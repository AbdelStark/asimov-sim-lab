from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab.cli import app


def test_doctor_json_success(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app, ["doctor", "--asset-root", str(minimal_source), "--format", "json"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "doctor"
    assert payload["resolved_asset_root"] == str(minimal_source.resolve())
    assert any(
        check["name"] == "primary_xml" and check["status"] == "ok" for check in payload["checks"]
    )


def test_doctor_missing_xml_returns_typed_layout_error(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "missing_xml"

    result = CliRunner().invoke(app, ["doctor", "--asset-root", str(source), "--format", "json"])

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert any(check["code"] == "PRIMARY_XML_NOT_FOUND" for check in payload["checks"])


def test_doctor_surfaces_manifest_parse_warning(fixtures_dir: Path) -> None:
    source = fixtures_dir / "source_roots" / "malformed_xml"

    result = CliRunner().invoke(app, ["doctor", "--asset-root", str(source), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "warning"
    assert any(check["code"] == "XML_PARSE_FAILED" for check in payload["checks"])


def test_doctor_writes_manifest_atomically(minimal_source: Path, tmp_path: Path) -> None:
    manifest_path = tmp_path / "nested" / "asset-manifest.json"

    result = CliRunner().invoke(
        app,
        [
            "doctor",
            "--asset-root",
            str(minimal_source),
            "--format",
            "json",
            "--manifest-output",
            str(manifest_path),
        ],
    )

    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["primary_xml"]["relative_path"] == "sim-model/xmls/asimov.xml"
    assert sorted(mesh["relative_path"] for mesh in manifest["meshes"]) == [
        "sim-model/assets/meshes/LEFT_HIP_PITCH.STL",
        "sim-model/assets/meshes/RIGHT_ELBOW.STL",
    ]


def test_doctor_rejects_sim_model_as_asset_root(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["doctor", "--asset-root", str(minimal_source / "sim-model"), "--format", "json"],
    )

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert any(check["code"] == "PRIMARY_XML_NOT_FOUND" for check in payload["checks"])
