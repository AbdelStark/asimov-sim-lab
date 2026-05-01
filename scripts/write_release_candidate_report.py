"""Write a sanitized release-candidate dry-run report from an export package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from check_release_evidence import validate_export_dir


def build_report(export_dir: Path) -> str:
    errors = validate_export_dir(export_dir)
    if errors:
        raise SystemExit("\n".join(f"release evidence error: {error}" for error in errors))

    root = export_dir.expanduser().resolve()
    result = _read_json(root / "export-package-result.json")
    evidence = _read_json(root / result["evidence_bundle_path"])

    warnings = sorted(str(warning) for warning in result.get("warnings", []))
    blocker_lines = _blockers(result, warnings)
    verdict = "not tag-ready" if blocker_lines else "tag-ready"

    lines = [
        "# RELEASE-CANDIDATE-DRY-RUN - Asimov Sim Lab",
        "",
        "This report is generated from a locally verified export package. It records the",
        "release evidence state without committing upstream XML, meshes, or local output paths.",
        "",
        "## Evidence",
        "",
        f"- verdict: `{verdict}`",
        f"- archive: `{Path(result['archive_path']).name}`",
        f"- archive_sha256: `{result['archive_sha256']}`",
        f"- archive_size_bytes: `{result['archive_size_bytes']}`",
        f"- evidence_bundle_path: `{result['evidence_bundle_path']}`",
        f"- evidence_bundle_sha256: `{result['evidence_bundle_sha256']}`",
        f"- package_manifest_path: `{result['package_manifest_path']}`",
        f"- deterministic: `{_literal(result['deterministic'])}`",
        f"- validation_passed: `{_literal(result['validation_passed'])}`",
        f"- validation_issue_count: `{result['validation_issue_count']}`",
        f"- runtime_smoke_status: `{result['runtime_smoke_status']}`",
        f"- runtime_smoke_skipped: `{_literal(result['runtime_smoke_skipped'])}`",
        f"- evidence_generated_at_utc: `{evidence['generated_at_utc']}`",
        "",
        "## Warnings",
        "",
    ]
    if warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- none")

    lines.extend(["", "## Blockers", ""])
    if blocker_lines:
        lines.extend(f"- {line}" for line in blocker_lines)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Verification",
            "",
            "The export package passed:",
            "",
            "```bash",
            "uv run python scripts/check_release_evidence.py --export-dir <export-dir>",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _blockers(result: dict[str, Any], warnings: list[str]) -> list[str]:
    blockers: list[str] = []
    if result.get("validation_passed") is not True:
        blockers.append("validation did not pass")
    if result.get("runtime_smoke_status") == "error":
        blockers.append("runtime smoke status is error")
    if any(warning.startswith("SOURCE_DIRTY") for warning in warnings):
        blockers.append("source checkout is dirty; disclose or clean before tagging")
    if any(warning.startswith("UPSTREAM_LICENSE_NOT_FOUND") for warning in warnings):
        blockers.append("upstream root license is missing; disclose or resolve before tagging")
    if any(warning.startswith("MUJOCO_NOT_INSTALLED") for warning in warnings):
        blockers.append("MuJoCo runtime smoke was skipped; disclose for source-contract alpha")
    return blockers


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"JSON file is not an object: {path}")
    return raw


def _literal(value: Any) -> str:
    return json.dumps(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    content = build_report(args.export_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"release candidate report written: {args.output}")


if __name__ == "__main__":
    main()
