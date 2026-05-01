from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab.cli import app


def test_inspect_json_exports_concrete_contract(minimal_source: Path) -> None:
    result = CliRunner().invoke(app, ["inspect", "--asset-root", str(minimal_source), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "inspect"
    assert payload["model_name"] == "AsimovFixture"
    assert payload["body_count"] == 3
    assert payload["joint_count"] == 3
    assert payload["actuator_count"] == 1
    assert payload["sensor_count"] == 2
    assert payload["camera_count"] == 1
    assert payload["site_count"] == 1
    assert payload["total_declared_mass_kg"] == 5.0

    joints = {joint["name"]: joint for joint in payload["joints"]}
    assert joints["floating_base"]["joint_type"] == "free"
    assert joints["floating_base"]["passive"] is True
    assert joints["left_hip_pitch_joint"]["passive"] is False
    assert joints["right_elbow_joint"]["passive"] is True


def test_inspect_markdown_is_deterministic(minimal_source: Path) -> None:
    runner = CliRunner()

    first = runner.invoke(app, ["inspect", "--asset-root", str(minimal_source), "--markdown"])
    second = runner.invoke(app, ["inspect", "--asset-root", str(minimal_source), "--markdown"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stdout == second.stdout
    assert "# AsimovFixture Model Contract" in first.stdout
    assert (
        "| left_hip_pitch_joint | left_hip_pitch_link | hinge | -1.0..1.0 | False |" in first.stdout
    )


def test_inspect_malformed_xml_fails_without_partial_contract(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "malformed_xml"

    result = CliRunner().invoke(app, ["inspect", "--asset-root", str(source), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["issues"][0]["code"] == "XML_PARSE_FAILED"


def test_inspect_rejects_conflicting_format_flags(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["inspect", "--asset-root", str(minimal_source), "--json", "--markdown"],
    )

    assert result.exit_code == 2
    assert "Use only one of --json or --markdown" in result.stderr
