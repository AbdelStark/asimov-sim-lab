from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab.cli import app


def _codes(payload: dict[str, object]) -> set[str]:
    issues = payload["issues"]
    assert isinstance(issues, list)
    return {str(issue["code"]) for issue in issues}


def test_validate_minimal_fixture_passes_with_warnings(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app, ["validate", "--asset-root", str(minimal_source), "--format", "json"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["status"] in {"ok", "warning"}
    assert "PRESET_VALUE_OUT_OF_RANGE" not in _codes(payload)


def test_validate_broken_mesh_reference_fails(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "broken_mesh_ref"

    result = CliRunner().invoke(app, ["validate", "--asset-root", str(source), "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert "MESH_REFERENCE_MISSING" in _codes(payload)


def test_validate_broken_actuator_reference_fails(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "broken_actuator_ref"

    result = CliRunner().invoke(app, ["validate", "--asset-root", str(source), "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert "ACTUATOR_JOINT_REFERENCE_MISSING" in _codes(payload)


def test_validate_local_preset_out_of_range_fails(minimal_source: Path, fixtures_dir: Path) -> None:
    preset_dir = fixtures_dir / "presets"

    result = CliRunner().invoke(
        app,
        [
            "validate",
            "--asset-root",
            str(minimal_source),
            "--preset-dir",
            str(preset_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert "PRESET_VALUE_OUT_OF_RANGE" in _codes(payload)


def test_validate_strict_escalates_provenance_warning(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["validate", "--asset-root", str(minimal_source), "--format", "json", "--strict"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert "SOURCE_NOT_GIT_ROOT" in _codes(payload) or "SOURCE_NOT_GIT" in _codes(payload)
