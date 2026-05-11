from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from asimov_sim_lab.config import DEFAULT_PROFILE_PATH, load_profile
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.paths import (
    ENV_ASSET_ROOT,
    layout_checks,
    read_git_metadata,
    resolve_asset_root,
)


def test_load_profile_default_if_present(tmp_path: Path, minimal_source: Path) -> None:
    profile_path = tmp_path / DEFAULT_PROFILE_PATH
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        f'schema_version = "0.1.0"\ndefault_asset_root = "{minimal_source.resolve()}"\n',
        encoding="utf-8",
    )

    profile, locator = load_profile(None, repo_root=tmp_path)

    assert locator == "default_profile"
    assert profile is not None
    assert profile.default_asset_root == minimal_source.resolve()


def test_load_profile_missing_explicit_path_fails(tmp_path: Path) -> None:
    with pytest.raises(LabError) as exc:
        load_profile(tmp_path / "missing.toml")

    assert exc.value.code == "PROFILE_NOT_FOUND"


def test_load_profile_invalid_toml_fails(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.toml"
    profile_path.write_text("not = [valid", encoding="utf-8")

    with pytest.raises(LabError) as exc:
        load_profile(profile_path)

    assert exc.value.code == "PROFILE_PARSE_FAILED"


def test_load_profile_relative_asset_root_fails(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.toml"
    profile_path.write_text('default_asset_root = "relative/path"\n', encoding="utf-8")

    with pytest.raises(LabError) as exc:
        load_profile(profile_path)

    assert exc.value.code == "PROFILE_INVALID_PATH"


def test_load_profile_unknown_field_warns_or_fails_strict(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.toml"
    profile_path.write_text('default_asset_root = "/tmp"\nextra = true\n', encoding="utf-8")

    profile, _ = load_profile(profile_path, strict=False)
    assert profile is not None
    assert profile.warnings

    with pytest.raises(LabError) as exc:
        load_profile(profile_path, strict=True)
    assert exc.value.code == "PROFILE_UNKNOWN_FIELD"


def test_resolve_asset_root_env_fallback(minimal_source: Path) -> None:
    resolution = resolve_asset_root(
        asset_root=None,
        profile_path=None,
        env={ENV_ASSET_ROOT: str(minimal_source)},
    )

    assert resolution.asset_root == minimal_source.resolve()
    assert resolution.locator == f"env:{ENV_ASSET_ROOT}"


def test_resolve_asset_root_rejects_missing_and_file(tmp_path: Path) -> None:
    with pytest.raises(LabError) as missing:
        resolve_asset_root(asset_root=tmp_path / "missing", profile_path=None, env={})
    assert missing.value.code == "ASSET_ROOT_NOT_FOUND"

    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(LabError) as file_error:
        resolve_asset_root(asset_root=file_path, profile_path=None, env={})
    assert file_error.value.code == "ASSET_ROOT_NOT_FOUND"


def test_layout_checks_missing_readme_warns(tmp_path: Path) -> None:
    (tmp_path / "sim-model" / "xmls").mkdir(parents=True)
    (tmp_path / "sim-model" / "assets" / "meshes").mkdir(parents=True)
    (tmp_path / "sim-model" / "xmls" / "asimov.xml").write_text("<mujoco/>", encoding="utf-8")

    checks = layout_checks(tmp_path)

    assert any(check.code == "SIM_MODEL_README_NOT_FOUND" for check in checks)
    assert any(check.code == "UPSTREAM_LICENSE_NOT_FOUND" for check in checks)


def test_read_git_metadata_for_clean_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

    metadata = read_git_metadata(tmp_path)

    assert metadata.commit is not None
    assert metadata.dirty is False
    assert metadata.untracked_count == 0
    assert metadata.warnings == []


def test_read_git_metadata_counts_untracked_separately(tmp_path: Path) -> None:
    # Verifies the dirty-vs-untracked split landed in PF-04: the dirty signal comes
    # from `status --untracked-files=no`, untracked count from `ls-files --others`.
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "untracked.txt").write_text("y", encoding="utf-8")

    metadata = read_git_metadata(tmp_path)

    assert metadata.dirty is True
    assert metadata.untracked_count == 1
    assert any(w.startswith("SOURCE_DIRTY") for w in metadata.warnings)


def test_read_git_metadata_surfaces_query_failure_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulates a partial git failure (e.g., timeout): rev-parse confirms a checkout
    # but a downstream sub-query returns None. PF-04 must surface this as "unknown"
    # (null dirty), not the prior silent false negative of `dirty=False`.
    from asimov_sim_lab import paths as paths_module

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

    real_git = paths_module._git

    def flaky_git(asset_root: Path, *args: str) -> str | None:
        if args[:1] == ("status",) or args[:1] == ("ls-files",):
            return None
        return real_git(asset_root, *args)

    monkeypatch.setattr(paths_module, "_git", flaky_git)

    metadata = read_git_metadata(tmp_path)

    assert metadata.commit is not None
    assert metadata.dirty is None
    assert metadata.untracked_count is None
    assert any(w.startswith("SOURCE_GIT_QUERY_FAILED") for w in metadata.warnings)
