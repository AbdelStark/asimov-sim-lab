"""Asset-root resolution and supported-layout checks."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from asimov_sim_lab.config import Profile, load_profile
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.models import DoctorCheck, SourceLocator

ENV_ASSET_ROOT = "ASIMOV_SIM_LAB_ASSET_ROOT"
PRIMARY_XML = Path("sim-model/xmls/asimov.xml")
MESH_DIR = Path("sim-model/assets/meshes")
SIM_MODEL_README = Path("sim-model/README.md")

STRICT_WARNING_CODES = {
    "SOURCE_DIRTY",
    "SOURCE_GIT_QUERY_FAILED",
    "SOURCE_NOT_GIT_ROOT",
    "SOURCE_NOT_GIT",
    "SIM_MODEL_README_NOT_FOUND",
    "UPSTREAM_LICENSE_NOT_FOUND",
    "MESHDIR_MISSING",
    "XML_PARSE_FAILED",
    "PROFILE_UNKNOWN_FIELD",
}


@dataclass(slots=True)
class AssetRootResolution:
    asset_root: Path
    locator: str
    profile: Profile | None = None
    profile_locator: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GitMetadata:
    repo_url: str | None
    commit: str | None
    branch: str | None
    dirty: bool | None
    untracked_count: int | None
    warnings: list[str]


def resolve_asset_root(
    *,
    asset_root: Path | None,
    profile_path: Path | None,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    strict: bool = False,
) -> AssetRootResolution:
    """Resolve the local upstream checkout root by explicit precedence."""
    env_values = env or os.environ
    profile, profile_locator = load_profile(profile_path, repo_root=repo_root, strict=strict)
    warnings = list(profile.warnings) if profile is not None else []

    if asset_root is not None:
        root = asset_root
        locator = "cli"
    elif profile is not None and profile.default_asset_root is not None:
        root = profile.default_asset_root
        locator = profile_locator or "profile"
    elif env_values.get(ENV_ASSET_ROOT):
        root = Path(env_values[ENV_ASSET_ROOT])
        locator = f"env:{ENV_ASSET_ROOT}"
    else:
        raise LabError(
            "ASSET_ROOT_NOT_FOUND",
            "No Asimov asset root was provided.",
            (
                f"Pass --asset-root, configure {ENV_ASSET_ROOT}, "
                "or create .asimov-sim-lab/profile.toml."
            ),
            exit_code=3,
        )

    root = root.expanduser().resolve()
    if not root.exists():
        raise LabError(
            "ASSET_ROOT_NOT_FOUND",
            f"Asset root does not exist: {root}",
            "Pass the upstream Asimov checkout root that contains sim-model/.",
            exit_code=3,
        )
    if not root.is_dir():
        raise LabError(
            "ASSET_ROOT_NOT_FOUND",
            f"Asset root is not a directory: {root}",
            "Pass the upstream Asimov checkout root that contains sim-model/.",
            exit_code=3,
        )

    return AssetRootResolution(
        asset_root=root,
        locator=locator,
        profile=profile,
        profile_locator=profile_locator,
        warnings=warnings,
    )


def layout_checks(asset_root: Path) -> list[DoctorCheck]:
    """Return supported-layout checks for the MVP source tree."""
    checks = [
        _path_check("asset_root", asset_root, "ASSET_ROOT_NOT_FOUND", required_dir=True),
        _path_check("primary_xml", asset_root / PRIMARY_XML, "PRIMARY_XML_NOT_FOUND"),
        _path_check(
            "mesh_directory", asset_root / MESH_DIR, "MESH_DIRECTORY_NOT_FOUND", required_dir=True
        ),
    ]
    readme = asset_root / SIM_MODEL_README
    if readme.exists():
        checks.append(
            DoctorCheck(name="sim_model_readme", status="ok", detail=str(SIM_MODEL_README))
        )
    else:
        checks.append(
            DoctorCheck(
                name="sim_model_readme",
                status="warning",
                detail=f"Optional sim-model README not found: {SIM_MODEL_README}",
                code="SIM_MODEL_README_NOT_FOUND",
            )
        )

    if _has_license_file(asset_root):
        checks.append(
            DoctorCheck(name="upstream_license", status="ok", detail="license file detected")
        )
    else:
        checks.append(
            DoctorCheck(
                name="upstream_license",
                status="warning",
                detail="No recognized upstream license file found at checkout root.",
                code="UPSTREAM_LICENSE_NOT_FOUND",
            )
        )
    return checks


def source_locator(resolution: AssetRootResolution) -> tuple[SourceLocator, list[str]]:
    """Build provenance metadata for a local checkout."""
    git = read_git_metadata(resolution.asset_root)
    warnings = [*resolution.warnings, *git.warnings]
    locator = SourceLocator(
        mode="local_checkout",
        root_path=str(resolution.asset_root),
        locator=resolution.locator,
        upstream_repo_url=git.repo_url,
        upstream_commit=git.commit,
        upstream_branch=git.branch,
        git_dirty=git.dirty,
        git_untracked_count=git.untracked_count,
    )
    return locator, warnings


def strict_status(status: str, code: str | None, *, strict: bool) -> str:
    if strict and status == "warning" and code in STRICT_WARNING_CODES:
        return "error"
    return status


def read_git_metadata(asset_root: Path) -> GitMetadata:
    """Read Git provenance without treating parent worktrees as source checkouts."""
    top_level = _git(asset_root, "rev-parse", "--show-toplevel")
    if top_level is None:
        return GitMetadata(
            None, None, None, None, None, ["SOURCE_NOT_GIT: asset root is not a Git checkout"]
        )
    if Path(top_level).resolve() != asset_root.resolve():
        return GitMetadata(
            None,
            None,
            None,
            None,
            None,
            [
                "SOURCE_NOT_GIT_ROOT: asset root is inside a Git worktree "
                "but is not the worktree root"
            ],
        )

    commit = _git(asset_root, "rev-parse", "HEAD")
    branch = _git(asset_root, "branch", "--show-current")
    repo_url = _git(asset_root, "config", "--get", "remote.origin.url")

    # Split dirty detection from the untracked-file count so neither pays the cost
    # of walking the whole worktree. `--untracked-files=no` skips the walk; the
    # untracked count uses the index-aware `git ls-files`. After confirming this is
    # a Git checkout via `rev-parse --show-toplevel`, a None response from either
    # sub-query means the call genuinely failed (timeout or git error) — surface
    # that as `SOURCE_GIT_QUERY_FAILED` with nullable dirty/untracked rather than
    # silently reporting a clean tree.
    warnings: list[str] = []
    dirty_status = _git(asset_root, "status", "--porcelain=v1", "--untracked-files=no")
    if dirty_status is None:
        warnings.append("SOURCE_GIT_QUERY_FAILED: could not determine working-tree dirty state")
        dirty: bool | None = None
    else:
        dirty = any(line.strip() for line in dirty_status.splitlines())

    untracked_raw = _git(asset_root, "ls-files", "--others", "--exclude-standard")
    if untracked_raw is None:
        warnings.append("SOURCE_GIT_QUERY_FAILED: could not enumerate untracked files")
        untracked_count: int | None = None
    else:
        untracked_count = sum(1 for line in untracked_raw.splitlines() if line.strip())

    # `dirty` covers staged/unstaged changes; untracked files also count as dirty.
    has_untracked = untracked_count is not None and untracked_count > 0
    if dirty is None and not has_untracked:
        # Both signals are unknown (dirty query failed) AND no untracked files were
        # found (or that query failed too) — we genuinely can't say.
        final_dirty: bool | None = None
    else:
        final_dirty = bool(dirty) or has_untracked

    if final_dirty:
        warnings.append("SOURCE_DIRTY: upstream checkout has uncommitted or untracked files")
    return GitMetadata(repo_url, commit, branch or None, final_dirty, untracked_count, warnings)


def _path_check(
    name: str,
    path: Path,
    code: str,
    *,
    required_dir: bool = False,
) -> DoctorCheck:
    exists = path.is_dir() if required_dir else path.is_file()
    if exists:
        return DoctorCheck(name=name, status="ok", detail=str(path))
    expected = "directory" if required_dir else "file"
    return DoctorCheck(
        name=name,
        status="error",
        detail=f"Required {expected} not found: {path}",
        code=code,
    )


def _has_license_file(asset_root: Path) -> bool:
    candidates = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md", "NOTICE")
    return any((asset_root / candidate).is_file() for candidate in candidates)


def _git(asset_root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(asset_root), *args],
            check=False,
            text=True,
            capture_output=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()
