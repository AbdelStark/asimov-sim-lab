from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab import runtime
from asimov_sim_lab.cli import app
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.runtime import run_runtime_smoke


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


class _FailingMjModel:
    @staticmethod
    def from_xml_path(path: str) -> _FakeModel:
        raise ValueError(f"bad xml: {path}")


class _FailingMujoco:
    __version__ = "test-runtime"
    MjModel = _FailingMjModel


def test_runtime_smoke_skips_when_mujoco_missing(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_runtime_smoke(resolution)

    assert result.status == "warning"
    assert result.runtime_available is False
    assert result.skipped is True
    assert result.loaded is False
    assert result.failure_code is None


def test_runtime_smoke_can_require_mujoco(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_runtime_smoke(resolution, require_mujoco=True)

    assert result.status == "error"
    assert result.failure_code == "MUJOCO_NOT_INSTALLED"


def test_runtime_smoke_records_compiled_counts(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_runtime_smoke(resolution, mujoco_module=_FakeMujoco())

    assert result.status == "warning"
    assert result.runtime_available is True
    assert result.loaded is True
    assert result.model_counts is not None
    assert result.model_counts.nbody == 3
    assert result.runtime_version == "test-runtime"


def test_runtime_smoke_can_omit_elapsed_for_reproducible_exports(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_runtime_smoke(
        resolution,
        mujoco_module=_FakeMujoco(),
        include_elapsed=False,
    )

    assert result.loaded is True
    assert result.elapsed_ms is None


def test_runtime_smoke_reports_load_failure(minimal_source: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    result = run_runtime_smoke(resolution, mujoco_module=_FailingMujoco())

    assert result.status == "error"
    assert result.loaded is False
    assert result.failure_code == "MUJOCO_MODEL_LOAD_FAILED"


def test_runtime_smoke_cli_json_missing_dependency(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)

    result = CliRunner().invoke(
        app,
        [
            "runtime-smoke",
            "--asset-root",
            str(minimal_source),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "runtime-smoke"
    assert payload["skipped"] is True


def test_runtime_smoke_cli_require_mujoco_exits_nonzero(minimal_source: Path, monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)

    result = CliRunner().invoke(
        app,
        [
            "runtime-smoke",
            "--asset-root",
            str(minimal_source),
            "--require-mujoco",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    assert json.loads(result.stdout)["failure_code"] == "MUJOCO_NOT_INSTALLED"
