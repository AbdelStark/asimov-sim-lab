"""Validate a generated export package before release-candidate use."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path
from typing import Any

EXPORT_RESULT = "export-package-result.json"


def validate_export_dir(export_dir: Path) -> list[str]:
    """Return release-evidence validation errors for an export directory."""
    errors: list[str] = []
    root = export_dir.expanduser().resolve()
    result_path = root / EXPORT_RESULT
    result = _read_json(result_path, errors)
    if result is None:
        return errors

    manifest_relative = _string_field(result, "package_manifest_path", errors)
    manifest_path = (
        _safe_child(root, manifest_relative, "package_manifest_path", errors)
        if manifest_relative is not None
        else root / ""
    )
    manifest = _read_json(manifest_path, errors) if manifest_relative is not None else None

    archive_path_value = _string_field(result, "archive_path", errors)
    archive_path = root / Path(archive_path_value).name if archive_path_value is not None else None
    archive_sha256 = _string_field(result, "archive_sha256", errors)
    archive_size = _int_field(result, "archive_size_bytes", errors)
    if archive_path is not None and archive_sha256 is not None and archive_size is not None:
        _check_file_digest(archive_path, archive_sha256, archive_size, errors)

    evidence_relative = _string_field(result, "evidence_bundle_path", errors)
    evidence_sha256 = _string_field(result, "evidence_bundle_sha256", errors)
    if evidence_relative is not None and evidence_sha256 is not None:
        evidence_path = _safe_child(root, evidence_relative, "evidence_bundle_path", errors)
        _check_file_digest(evidence_path, evidence_sha256, None, errors)
    else:
        evidence_path = root / ""

    manifest_sha256 = _string_field(result, "package_manifest_sha256", errors)
    if manifest_sha256 is not None and manifest_relative is not None:
        _check_file_digest(manifest_path, manifest_sha256, None, errors)

    if manifest is not None:
        _validate_manifest(root, manifest, evidence_relative, evidence_sha256, errors)
    evidence = _read_json(evidence_path, errors) if evidence_relative is not None else None
    if evidence is not None:
        _validate_evidence_bundle(evidence, errors)
    if archive_path is not None and manifest is not None and manifest_relative is not None:
        _validate_archive(archive_path, manifest_relative, manifest, errors)
    return errors


def _validate_manifest(
    root: Path,
    manifest: dict[str, Any],
    evidence_relative: str | None,
    evidence_sha256: str | None,
    errors: list[str],
) -> None:
    if evidence_relative is not None and manifest.get("evidence_bundle_path") != evidence_relative:
        errors.append("package manifest evidence_bundle_path does not match export result")
    if evidence_sha256 is not None and manifest.get("evidence_bundle_sha256") != evidence_sha256:
        errors.append("package manifest evidence_bundle_sha256 does not match export result")
    for index, entry in enumerate(_list_field(manifest, "package_files", errors)):
        if not isinstance(entry, dict):
            errors.append(f"package_files[{index}] is not an object")
            continue
        relative = _string_field(entry, "relative_path", errors, prefix=f"package_files[{index}]")
        sha256 = _string_field(entry, "sha256", errors, prefix=f"package_files[{index}]")
        size = _int_field(entry, "size_bytes", errors, prefix=f"package_files[{index}]")
        if relative is not None and sha256 is not None and size is not None:
            _check_file_digest(
                _safe_child(root, relative, f"package_files[{index}].relative_path", errors),
                sha256,
                size,
                errors,
            )


def _validate_evidence_bundle(evidence: dict[str, Any], errors: list[str]) -> None:
    if evidence.get("command") != "evidence":
        errors.append("evidence bundle command is not 'evidence'")
    if evidence.get("validation_passed") is not True:
        errors.append("evidence bundle validation_passed is not true")
    if evidence.get("runtime_smoke_status") == "error":
        errors.append("evidence bundle runtime_smoke_status is error")
    artifact_paths = {
        entry.get("relative_path")
        for entry in _list_field(evidence, "artifacts", errors)
        if isinstance(entry, dict)
    }
    required = {
        "asset-manifest.json",
        "inspect-result.json",
        "validation-result.json",
        "runtime-smoke-result.json",
        "inspect-report.md",
    }
    missing = sorted(required - artifact_paths)
    errors.extend(f"evidence bundle is missing artifact entry: {relative}" for relative in missing)


def _validate_archive(
    archive_path: Path,
    manifest_relative: str,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if not archive_path.is_file():
        errors.append(f"archive not found: {archive_path}")
        return
    expected_members = sorted(
        [
            manifest_relative,
            *[
                entry["relative_path"]
                for entry in _list_field(manifest, "package_files", errors)
                if isinstance(entry, dict) and isinstance(entry.get("relative_path"), str)
            ],
        ]
    )
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError) as exc:
        errors.append(f"archive could not be read: {archive_path}: {exc}")
        return
    actual_members = [member.name for member in members]
    if actual_members != expected_members:
        errors.append(
            "archive members do not match package manifest: "
            f"expected {expected_members}, got {actual_members}"
        )
    for member in members:
        if not member.isfile():
            errors.append(f"archive member is not a regular file: {member.name}")
        if member.mtime != 0:
            errors.append(f"archive member has non-deterministic mtime: {member.name}")
        if member.uid != 0 or member.gid != 0:
            errors.append(f"archive member has nonzero owner ids: {member.name}")


def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"could not read JSON file: {path}: {exc}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"could not parse JSON file: {path}: {exc}")
        return None
    if not isinstance(raw, dict):
        errors.append(f"JSON file is not an object: {path}")
        return None
    return raw


def _safe_child(root: Path, relative: str, field: str, errors: list[str]) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{field} must be a relative path inside the export directory")
        return root / "__invalid__"
    return root / path


def _check_file_digest(
    path: Path,
    expected_sha256: str,
    expected_size: int | None,
    errors: list[str],
) -> None:
    if not path.is_file():
        errors.append(f"artifact not found: {path}")
        return
    actual_size = path.stat().st_size
    if expected_size is not None and actual_size != expected_size:
        errors.append(f"size mismatch for {path}: expected {expected_size}, got {actual_size}")
    actual_sha256 = _sha256(path)
    if actual_sha256 != expected_sha256:
        errors.append(
            f"checksum mismatch for {path}: expected {expected_sha256}, got {actual_sha256}"
        )


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _string_field(
    data: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> str | None:
    value = data.get(field)
    label = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, str):
        errors.append(f"{label} is missing or not a string")
        return None
    return value


def _int_field(
    data: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> int | None:
    value = data.get(field)
    label = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, int):
        errors.append(f"{label} is missing or not an integer")
        return None
    return value


def _list_field(data: dict[str, Any], field: str, errors: list[str]) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(f"{field} is missing or not a list")
        return []
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export-dir", required=True, type=Path, help="Generated export directory."
    )
    args = parser.parse_args()

    errors = validate_export_dir(args.export_dir)
    if errors:
        for error in errors:
            print(f"release evidence error: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"release evidence ok: {args.export_dir}")


if __name__ == "__main__":
    main()
