"""Doctor command domain logic."""

from __future__ import annotations

from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import AssetManifest, DoctorCheck, DoctorResult, Status
from asimov_sim_lab.paths import (
    AssetRootResolution,
    layout_checks,
    read_git_metadata,
    strict_status,
)


def run_doctor(
    resolution: AssetRootResolution, *, strict: bool = False
) -> tuple[DoctorResult, AssetManifest | None]:
    """Run layout/provenance checks and generate a manifest when possible."""
    checks = layout_checks(resolution.asset_root)
    profile_warnings = [
        DoctorCheck(
            name="profile",
            status="warning",
            detail=warning,
            code=warning.split(":", maxsplit=1)[0] if ":" in warning else "PROFILE_WARNING",
        )
        for warning in resolution.warnings
    ]
    checks.extend(profile_warnings)

    git = read_git_metadata(resolution.asset_root)
    for warning in git.warnings:
        checks.append(
            DoctorCheck(
                name="provenance",
                status="warning",
                detail=warning,
                code=warning.split(":", maxsplit=1)[0] if ":" in warning else "SOURCE_WARNING",
            )
        )

    normalized_checks = [
        check.model_copy(update={"status": strict_status(check.status, check.code, strict=strict)})
        for check in checks
    ]
    manifest = None
    if not any(check.status == "error" for check in normalized_checks):
        manifest = generate_asset_manifest(resolution)

    status: Status = "ok"
    if any(check.status == "error" for check in normalized_checks):
        status = "error"
    elif any(check.status == "warning" for check in normalized_checks):
        status = "warning"

    result = DoctorResult(
        status=status,
        warnings=[check.detail for check in normalized_checks if check.status == "warning"],
        source_manifest_path=None,
        checks=normalized_checks,
        resolved_asset_root=str(resolution.asset_root),
    )
    return result, manifest
