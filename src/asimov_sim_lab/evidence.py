"""Evidence bundle generation for reviewable local artifacts."""

from __future__ import annotations

from pathlib import Path

from asimov_sim_lab.artifacts import sha256_file, write_text_atomic
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.inspect import inspect_model, render_inspect_markdown
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    EvidenceArtifact,
    EvidenceBundleResult,
    Status,
)
from asimov_sim_lab.paths import AssetRootResolution
from asimov_sim_lab.validation import validate_model

ASSET_MANIFEST_FILE = "asset-manifest.json"
INSPECT_RESULT_FILE = "inspect-result.json"
VALIDATION_RESULT_FILE = "validation-result.json"
INSPECT_REPORT_FILE = "inspect-report.md"
EVIDENCE_BUNDLE_FILE = "evidence-bundle.json"


def generate_evidence_bundle(
    resolution: AssetRootResolution,
    *,
    output_dir: Path,
    preset_dir: Path | None = None,
    strict: bool = False,
    overwrite: bool = False,
) -> EvidenceBundleResult:
    """Generate a complete evidence directory for one source checkout."""
    bundle_dir = output_dir.expanduser().resolve()
    _prepare_bundle_dir(bundle_dir, overwrite=overwrite)

    manifest = generate_asset_manifest(resolution)
    inspect_result = inspect_model(resolution)
    validation_result = validate_model(resolution, preset_dir=preset_dir, strict=strict)

    inspect_result.source_manifest_path = ASSET_MANIFEST_FILE
    validation_result.source_manifest_path = ASSET_MANIFEST_FILE

    _write_bundle_artifact(bundle_dir / ASSET_MANIFEST_FILE, manifest.model_dump_json(indent=2))
    _write_bundle_artifact(
        bundle_dir / INSPECT_RESULT_FILE, inspect_result.model_dump_json(indent=2)
    )
    _write_bundle_artifact(
        bundle_dir / VALIDATION_RESULT_FILE, validation_result.model_dump_json(indent=2)
    )
    _write_bundle_artifact(
        bundle_dir / INSPECT_REPORT_FILE, render_inspect_markdown(inspect_result)
    )

    artifacts = [
        _artifact(bundle_dir, ASSET_MANIFEST_FILE, "asset_manifest"),
        _artifact(bundle_dir, INSPECT_RESULT_FILE, "inspect_result"),
        _artifact(bundle_dir, VALIDATION_RESULT_FILE, "validation_result"),
        _artifact(bundle_dir, INSPECT_REPORT_FILE, "inspect_report"),
    ]

    warnings = sorted(
        {
            *manifest.warnings,
            *inspect_result.warnings,
            *validation_result.warnings,
        }
    )
    status: Status = "ok"
    if warnings:
        status = "warning"
    if not validation_result.passed:
        status = "error"

    result = EvidenceBundleResult(
        status=status,
        warnings=warnings,
        source_manifest_path=ASSET_MANIFEST_FILE,
        bundle_dir=str(bundle_dir),
        artifacts=artifacts,
        validation_passed=validation_result.passed,
        validation_issue_count=validation_result.issue_count,
    )
    _write_bundle_artifact(bundle_dir / EVIDENCE_BUNDLE_FILE, result.model_dump_json(indent=2))
    return result


def _prepare_bundle_dir(bundle_dir: Path, *, overwrite: bool) -> None:
    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise LabError(
            "EVIDENCE_OUTPUT_NOT_DIRECTORY",
            f"Evidence output path exists and is not a directory: {bundle_dir}",
            "Pass a directory path for --output-dir.",
            exit_code=2,
        )
    if bundle_dir.exists() and any(bundle_dir.iterdir()) and not overwrite:
        raise LabError(
            "EVIDENCE_OUTPUT_NOT_EMPTY",
            f"Evidence output directory is not empty: {bundle_dir}",
            "Pass an empty directory or use --overwrite to replace known bundle artifacts.",
            exit_code=2,
        )
    bundle_dir.mkdir(parents=True, exist_ok=True)


def _write_bundle_artifact(path: Path, content: str) -> None:
    write_text_atomic(path, content.rstrip() + "\n")


def _artifact(bundle_dir: Path, relative_path: str, artifact_type: str) -> EvidenceArtifact:
    path = bundle_dir / relative_path
    return EvidenceArtifact(
        artifact_type=artifact_type,
        relative_path=relative_path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
    )
