from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from typer.testing import CliRunner

import asimov_sim_lab.cli as cli
from asimov_sim_lab import runtime
from asimov_sim_lab.cli import app
from asimov_sim_lab.models import ViewerOpenResult
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.viewer import run_viewer_open_preflight


class _FakeModel:
    nbody = 3
    njnt = 2
    nu = 1
    nsensor = 2
    ngeom = 2
    nmesh = 2
    nq = 9
    nv = 8


class _FakeMjModel:
    @staticmethod
    def from_xml_path(path: str) -> _FakeModel:
        assert path.endswith("sim-model/xmls/asimov.xml")
        return _FakeModel()


class _FakeMujoco:
    __version__ = "test-runtime"
    MjModel = _FakeMjModel


class _BrokenMjModel:
    @staticmethod
    def from_xml_path(path: str) -> _FakeModel:
        raise ValueError(f"bad model: {path}")


class _BrokenMujoco:
    __version__ = "broken-runtime"
    MjModel = _BrokenMjModel


def test_viewer_open_preflight_passes_with_fake_mujoco(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(resolution, mujoco_module=_FakeMujoco())

    assert result.command == "open"
    assert result.status == "warning"
    assert result.opened is False
    assert result.launch_mode == "preflight_only"
    assert result.validation_passed is True
    assert result.runtime_smoke_status == "warning"
    assert result.runtime_version == "test-runtime"
    assert result.failure_code is None


def test_viewer_open_preflight_accepts_named_preset(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(
        resolution,
        preset_name="custom-neutral",
        preset_dir=Path(__file__).resolve().parents[1] / "docs" / "examples" / "presets",
        mujoco_module=_FakeMujoco(),
    )

    assert result.status == "warning"
    assert result.failure_code is None
    assert result.preset_name == "custom-neutral"


def test_viewer_open_preflight_requires_mujoco(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(resolution)

    assert result.status == "error"
    assert result.opened is False
    assert result.failure_code == "VIEWER_EXTRA_NOT_INSTALLED"
    assert result.failure_help_url == "docs/spec/ERROR-CODE-REGISTRY.md"


def test_viewer_open_preflight_maps_runtime_load_failure(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(resolution, mujoco_module=_BrokenMujoco())

    assert result.status == "error"
    assert result.failure_code == "VIEWER_LAUNCH_FAILED"
    assert result.failure_message is not None
    assert "bad model" in result.failure_message
    assert result.runtime_smoke_status == "error"


def test_viewer_open_preflight_blocks_validation_errors(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "broken_mesh_ref"
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = run_viewer_open_preflight(resolution, mujoco_module=_FakeMujoco())

    assert result.status == "error"
    assert result.failure_code == "VIEWER_VALIDATION_FAILED"
    assert result.validation_passed is False
    assert result.runtime_smoke_status == "warning"


def test_viewer_open_preflight_blocks_unknown_preset(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(
        resolution,
        preset_name="missing",
        mujoco_module=_FakeMujoco(),
    )

    assert result.status == "error"
    assert result.failure_code == "VIEWER_PRESET_NOT_FOUND"


def test_viewer_open_preflight_can_require_clean_source(
    minimal_source: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    shutil.copytree(minimal_source, source)
    _git(source, "init")
    _git(source, "config", "user.email", "test@example.com")
    _git(source, "config", "user.name", "Test User")
    _git(source, "add", "sim-model")
    _git(source, "commit", "-m", "fixture")
    (source / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = run_viewer_open_preflight(
        resolution,
        require_clean_source=True,
        mujoco_module=_FakeMujoco(),
    )

    assert result.status == "error"
    assert result.failure_code == "VIEWER_SOURCE_DIRTY"


def test_viewer_open_preflight_can_require_upstream_license(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_viewer_open_preflight(
        resolution,
        require_license=True,
        mujoco_module=_FakeMujoco(),
    )

    assert result.status == "error"
    assert result.failure_code == "VIEWER_LICENSE_MISSING"


def test_open_cli_json_is_preflight_only_without_mujoco(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)

    result = CliRunner().invoke(
        app,
        [
            "open",
            "--asset-root",
            str(minimal_source),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["command"] == "open"
    assert payload["opened"] is False
    assert payload["launch_mode"] == "preflight_only"
    assert payload["failure_code"] == "VIEWER_EXTRA_NOT_INSTALLED"


def test_open_cli_text_includes_preflight_failure_details(
    minimal_source: Path, monkeypatch
) -> None:
    def fake_preflight(*args, **kwargs) -> ViewerOpenResult:
        return ViewerOpenResult(
            status="error",
            warnings=["SOURCE_DIRTY: upstream checkout has uncommitted files"],
            runtime_version="fake-runtime",
            xml_path="sim-model/xmls/asimov.xml",
            preset_name="neutral",
            validation_passed=True,
            validation_issue_count=0,
            runtime_smoke_status="error",
            opened=False,
            launch_mode="preflight_only",
            failure_code="VIEWER_LAUNCH_FAILED",
            failure_message="could not load model",
            failure_remediation="Fix MJCF/runtime errors before opening the viewer.",
            failure_help_url="docs/spec/ERROR-CODE-REGISTRY.md",
        )

    monkeypatch.setattr(cli, "run_viewer_open_preflight", fake_preflight)

    result = CliRunner().invoke(
        app,
        [
            "open",
            "--asset-root",
            str(minimal_source),
        ],
    )

    assert result.exit_code == 1
    assert "launch_mode: preflight_only" in result.stdout
    assert "runtime_version: fake-runtime" in result.stdout
    assert "failure: VIEWER_LAUNCH_FAILED: could not load model" in result.stdout
    assert "help: docs/spec/ERROR-CODE-REGISTRY.md" in result.stdout
    assert "warning: SOURCE_DIRTY" in result.stdout


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
