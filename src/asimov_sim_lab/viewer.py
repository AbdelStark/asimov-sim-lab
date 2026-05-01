"""Viewer/open preflight contract."""

from __future__ import annotations

from pathlib import Path

from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import ERROR_REGISTRY_HELP_URL, Status, ValidationIssue, ViewerOpenResult
from asimov_sim_lab.paths import PRIMARY_XML, AssetRootResolution
from asimov_sim_lab.presets import load_preset_dir
from asimov_sim_lab.runtime import MujocoModuleLike, run_runtime_smoke
from asimov_sim_lab.validation import validate_model

DEFAULT_VIEWER_PRESET = "neutral"


def run_viewer_open_preflight(
    resolution: AssetRootResolution,
    *,
    preset_name: str | None = DEFAULT_VIEWER_PRESET,
    preset_dir: Path | None = None,
    strict: bool = False,
    require_clean_source: bool = False,
    require_license: bool = False,
    mujoco_module: MujocoModuleLike | None = None,
) -> ViewerOpenResult:
    """Run the schema-backed `open` preflight without launching a GUI."""
    manifest = generate_asset_manifest(resolution)
    inspect_model(resolution)
    validation_result = validate_model(resolution, preset_dir=preset_dir, strict=strict)

    issues: list[ValidationIssue] = list(validation_result.issues)
    if preset_name is not None:
        issues.extend(_validate_requested_preset(preset_name, preset_dir=preset_dir))
    if require_clean_source and "SOURCE_DIRTY" in _warning_codes(manifest.warnings):
        issues.append(
            _viewer_issue(
                "VIEWER_SOURCE_DIRTY",
                "Viewer preflight requires a clean source checkout, but source is dirty.",
                "Commit, stash, or rerun with --allow-dirty-source.",
            )
        )
    if require_license and "UPSTREAM_LICENSE_NOT_FOUND" in _warning_codes(manifest.warnings):
        issues.append(
            _viewer_issue(
                "VIEWER_LICENSE_MISSING",
                "Viewer preflight requires an upstream root license, but none was found.",
                (
                    "Add a license file to the upstream checkout or rerun with "
                    "--allow-missing-license."
                ),
            )
        )

    blocking = [issue for issue in issues if issue.severity == "error"]
    if blocking:
        return _result(
            resolution,
            manifest_warnings=manifest.warnings,
            validation_passed=False,
            validation_issue_count=len(issues),
            runtime_smoke_status="warning",
            preset_name=preset_name,
            failure_code=blocking[0].code
            if blocking[0].code.startswith("VIEWER_")
            else "VIEWER_VALIDATION_FAILED",
            failure_message=blocking[0].message,
            failure_remediation=blocking[0].remediation
            or "Fix validation errors before opening the viewer.",
        )

    runtime_result = run_runtime_smoke(
        resolution,
        require_mujoco=True,
        mujoco_module=mujoco_module,
    )
    if runtime_result.status == "error":
        failure_code = (
            "VIEWER_EXTRA_NOT_INSTALLED"
            if runtime_result.failure_code == "MUJOCO_NOT_INSTALLED"
            else "VIEWER_LAUNCH_FAILED"
        )
        return _result(
            resolution,
            manifest_warnings=[*manifest.warnings, *runtime_result.warnings],
            validation_passed=validation_result.passed,
            validation_issue_count=len(issues),
            runtime_smoke_status=runtime_result.status,
            preset_name=preset_name,
            runtime_version=runtime_result.runtime_version,
            failure_code=failure_code,
            failure_message=runtime_result.failure_message,
            failure_remediation=runtime_result.failure_remediation,
        )

    status: Status = "warning" if manifest.warnings or runtime_result.warnings else "ok"
    return ViewerOpenResult(
        status=status,
        warnings=sorted({*manifest.warnings, *runtime_result.warnings}),
        source_manifest_path=None,
        runtime_version=runtime_result.runtime_version,
        xml_path=PRIMARY_XML.as_posix(),
        preset_name=preset_name,
        validation_passed=validation_result.passed,
        validation_issue_count=len(issues),
        runtime_smoke_status=runtime_result.status,
        opened=False,
        launch_mode="preflight_only",
    )


def _validate_requested_preset(
    preset_name: str,
    *,
    preset_dir: Path | None,
) -> list[ValidationIssue]:
    if preset_name == DEFAULT_VIEWER_PRESET:
        return []
    if preset_dir is None:
        return [
            _viewer_issue(
                "VIEWER_PRESET_NOT_FOUND",
                f"Viewer preset {preset_name!r} was requested, but no --preset-dir was provided.",
                "Pass --preset neutral or provide --preset-dir with a matching preset.",
            )
        ]
    presets, load_issues = load_preset_dir(preset_dir)
    if any(issue.severity == "error" for issue in load_issues):
        return load_issues
    if not any(preset.name == preset_name for preset in presets):
        return [
            _viewer_issue(
                "VIEWER_PRESET_NOT_FOUND",
                f"Viewer preset {preset_name!r} was not found in {preset_dir}.",
                "Use an existing preset name or pass --preset neutral.",
            )
        ]
    return load_issues


def _result(
    resolution: AssetRootResolution,
    *,
    manifest_warnings: list[str],
    validation_passed: bool,
    validation_issue_count: int,
    runtime_smoke_status: Status,
    preset_name: str | None,
    failure_code: str,
    failure_message: str | None,
    failure_remediation: str | None,
    runtime_version: str | None = None,
) -> ViewerOpenResult:
    return ViewerOpenResult(
        status="error",
        warnings=sorted(set(manifest_warnings)),
        source_manifest_path=None,
        runtime_version=runtime_version,
        xml_path=(resolution.asset_root / PRIMARY_XML)
        .relative_to(resolution.asset_root)
        .as_posix(),
        preset_name=preset_name,
        validation_passed=validation_passed,
        validation_issue_count=validation_issue_count,
        runtime_smoke_status=runtime_smoke_status,
        opened=False,
        launch_mode="preflight_only",
        failure_code=failure_code,
        failure_message=failure_message,
        failure_remediation=failure_remediation,
        failure_help_url=ERROR_REGISTRY_HELP_URL,
    )


def _warning_codes(warnings: list[str]) -> set[str]:
    return {warning.split(":", maxsplit=1)[0] for warning in warnings if ":" in warning}


def _viewer_issue(code: str, message: str, remediation: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity="error",
        message=message,
        remediation=remediation,
    )
