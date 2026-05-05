"""Deterministic evidence export package generation."""

from __future__ import annotations

import gzip
import re
import tarfile
from pathlib import Path
from tempfile import NamedTemporaryFile

from asimov_sim_lab.artifacts import sha256_file, write_text_atomic
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.evidence import (
    ASSET_MANIFEST_FILE,
    EVIDENCE_BUNDLE_FILE,
    INSPECT_REPORT_FILE,
    INSPECT_RESULT_FILE,
    RUNTIME_SMOKE_RESULT_FILE,
    VALIDATION_RESULT_FILE,
    generate_evidence_bundle,
)
from asimov_sim_lab.models import (
    ExportPackageFile,
    ExportPackageManifest,
    ExportPackageResult,
    Status,
)
from asimov_sim_lab.paths import AssetRootResolution

DEFAULT_PACKAGE_NAME = "asimov-sim-lab-evidence"
DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"
EXPORT_PACKAGE_MANIFEST_FILE = "export-package-manifest.json"
EXPORT_PACKAGE_RESULT_FILE = "export-package-result.json"
EVIDENCE_DIR = "evidence"

_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_EVIDENCE_FILES = (
    ASSET_MANIFEST_FILE,
    EVIDENCE_BUNDLE_FILE,
    INSPECT_REPORT_FILE,
    INSPECT_RESULT_FILE,
    RUNTIME_SMOKE_RESULT_FILE,
    VALIDATION_RESULT_FILE,
)


def generate_export_package(
    resolution: AssetRootResolution,
    *,
    output_dir: Path,
    preset_dir: Path | None = None,
    strict: bool = False,
    overwrite: bool = False,
    package_name: str = DEFAULT_PACKAGE_NAME,
    deterministic: bool = True,
) -> ExportPackageResult:
    """Generate a deterministic tarball from a portable evidence bundle."""
    _validate_package_name(package_name)
    package_dir = output_dir.expanduser().resolve()
    _prepare_package_dir(package_dir, overwrite=overwrite)

    generated_at_utc = DETERMINISTIC_TIMESTAMP if deterministic else None
    evidence_result = generate_evidence_bundle(
        resolution,
        output_dir=package_dir / EVIDENCE_DIR,
        preset_dir=preset_dir,
        strict=strict,
        overwrite=True,
        generated_at_utc=generated_at_utc,
        bundle_dir_label=EVIDENCE_DIR,
        include_runtime_elapsed=not deterministic,
    )

    evidence_bundle_relative = f"{EVIDENCE_DIR}/{EVIDENCE_BUNDLE_FILE}"
    evidence_bundle_path = package_dir / evidence_bundle_relative
    evidence_bundle_sha256 = sha256_file(evidence_bundle_path)
    package_files = [
        _package_file(package_dir, f"{EVIDENCE_DIR}/{relative_path}")
        for relative_path in _EVIDENCE_FILES
    ]
    manifest = ExportPackageManifest(
        evidence_bundle_path=evidence_bundle_relative,
        evidence_bundle_sha256=evidence_bundle_sha256,
        evidence_artifacts=evidence_result.artifacts,
        package_files=package_files,
        deterministic=deterministic,
    )
    if generated_at_utc is not None:
        manifest.generated_at_utc = generated_at_utc

    manifest_path = package_dir / EXPORT_PACKAGE_MANIFEST_FILE
    _write_json(manifest_path, manifest.model_dump_json(indent=2))

    archive_path = package_dir / f"{package_name}.tar.gz"
    _write_deterministic_archive(
        archive_path,
        package_dir,
        [
            EXPORT_PACKAGE_MANIFEST_FILE,
            *(f"{EVIDENCE_DIR}/{relative_path}" for relative_path in _EVIDENCE_FILES),
        ],
    )

    status: Status = evidence_result.status
    result = ExportPackageResult(
        status=status,
        warnings=evidence_result.warnings,
        source_manifest_path=f"{EVIDENCE_DIR}/{ASSET_MANIFEST_FILE}",
        package_dir=str(package_dir),
        archive_path=str(archive_path),
        archive_sha256=sha256_file(archive_path),
        archive_size_bytes=archive_path.stat().st_size,
        evidence_bundle_path=evidence_bundle_relative,
        evidence_bundle_sha256=evidence_bundle_sha256,
        package_manifest_path=EXPORT_PACKAGE_MANIFEST_FILE,
        package_manifest_sha256=sha256_file(manifest_path),
        deterministic=deterministic,
        validation_passed=evidence_result.validation_passed,
        validation_issue_count=evidence_result.validation_issue_count,
        runtime_smoke_status=evidence_result.runtime_smoke_status,
        runtime_smoke_skipped=evidence_result.runtime_smoke_skipped,
    )
    if generated_at_utc is not None:
        result.generated_at_utc = generated_at_utc
    _write_json(package_dir / EXPORT_PACKAGE_RESULT_FILE, result.model_dump_json(indent=2))
    return result


def _validate_package_name(package_name: str) -> None:
    if not _PACKAGE_NAME_RE.fullmatch(package_name):
        raise LabError(
            "EXPORT_PACKAGE_NAME_INVALID",
            f"Export package name is not safe for a file name: {package_name!r}",
            "Use only letters, numbers, dots, underscores, and hyphens.",
            exit_code=2,
        )


def _prepare_package_dir(package_dir: Path, *, overwrite: bool) -> None:
    if package_dir.exists() and not package_dir.is_dir():
        raise LabError(
            "EXPORT_OUTPUT_NOT_DIRECTORY",
            f"Export output path exists and is not a directory: {package_dir}",
            "Pass a directory path for --output-dir.",
            exit_code=2,
        )
    if package_dir.exists() and any(package_dir.iterdir()) and not overwrite:
        raise LabError(
            "EXPORT_OUTPUT_NOT_EMPTY",
            f"Export output directory is not empty: {package_dir}",
            "Pass an empty directory or use --overwrite to replace generated package artifacts.",
            exit_code=2,
        )
    package_dir.mkdir(parents=True, exist_ok=True)


def _package_file(package_dir: Path, relative_path: str) -> ExportPackageFile:
    path = package_dir / relative_path
    return ExportPackageFile(
        relative_path=relative_path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
    )


def _write_json(path: Path, content: str) -> None:
    write_text_atomic(path, content.rstrip() + "\n")


def _write_deterministic_archive(
    archive_path: Path,
    package_dir: Path,
    relative_paths: list[str],
) -> None:
    temporary: Path | None = None
    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("wb", delete=False, dir=archive_path.parent) as raw_handle:
            temporary = Path(raw_handle.name)
            with (
                gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
                tarfile.open(
                    fileobj=gzip_handle,
                    mode="w",
                    format=tarfile.USTAR_FORMAT,
                ) as tar,
            ):
                for relative_path in sorted(relative_paths):
                    _add_archive_file(tar, package_dir, relative_path)
        temporary.replace(archive_path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise LabError(
            "EXPORT_ARCHIVE_WRITE_FAILED",
            f"Could not write export archive: {archive_path}: {exc}",
            "Check directory permissions and available disk space.",
            exit_code=2,
        ) from exc


def _add_archive_file(tar: tarfile.TarFile, package_dir: Path, relative_path: str) -> None:
    path = package_dir / relative_path
    try:
        info = tar.gettarinfo(str(path), arcname=relative_path)
        info.mtime = 0
        info.uid = 0
        info.gid = 0
        info.uname = ""
        info.gname = ""
        info.mode = 0o644
        with path.open("rb") as handle:
            tar.addfile(info, handle)
    except OSError as exc:
        raise LabError(
            "EXPORT_ARCHIVE_INPUT_FAILED",
            f"Could not add export package file {relative_path}: {exc}",
            "Regenerate the evidence bundle and retry the export.",
            exit_code=3,
        ) from exc
