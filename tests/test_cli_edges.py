from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab.cli import app


def test_doctor_text_mode_and_output_file(minimal_source: Path, tmp_path: Path) -> None:
    output = tmp_path / "reports" / "doctor.txt"

    result = CliRunner().invoke(
        app,
        ["doctor", "--asset-root", str(minimal_source), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert "status:" in output.read_text(encoding="utf-8")


def test_doctor_invalid_format_exits_2(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["doctor", "--asset-root", str(minimal_source), "--format", "markdown"],
    )

    assert result.exit_code == 2
    assert "doctor supports --format text|json" in result.stderr


def test_doctor_missing_asset_root_json_error() -> None:
    result = CliRunner().invoke(app, ["doctor", "--format", "json"], env={})

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["issues"][0]["code"] == "ASSET_ROOT_NOT_FOUND"
    assert payload["help_url"] == "docs/spec/ERROR-CODE-REGISTRY.md"


def test_doctor_output_directory_error_text(minimal_source: Path, tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["doctor", "--asset-root", str(minimal_source), "--output", str(tmp_path)],
    )

    assert result.exit_code == 2
    assert "OUTPUT_PATH_IS_DIRECTORY" in result.stderr


def test_doctor_output_directory_error_json_does_not_recurse(
    minimal_source: Path, tmp_path: Path
) -> None:
    result = CliRunner().invoke(
        app,
        [
            "doctor",
            "--asset-root",
            str(minimal_source),
            "--format",
            "json",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "OUTPUT_PATH_IS_DIRECTORY" in result.stderr


def test_doctor_output_write_failure_json_does_not_recurse(
    minimal_source: Path, tmp_path: Path
) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "doctor",
            "--asset-root",
            str(minimal_source),
            "--format",
            "json",
            "--output",
            str(blocker / "doctor.json"),
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "OUTPUT_WRITE_FAILED" in result.stderr


def test_inspect_text_and_manifest_output(minimal_source: Path, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"

    result = CliRunner().invoke(
        app,
        [
            "inspect",
            "--asset-root",
            str(minimal_source),
            "--manifest-output",
            str(manifest_path),
        ],
    )

    assert result.exit_code == 0
    assert "model: AsimovFixture" in result.stdout
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["schema_version"] == "0.1.0"


def test_inspect_rejects_json_and_format_combo(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["inspect", "--asset-root", str(minimal_source), "--json", "--format", "json"],
    )

    assert result.exit_code == 2
    assert "Use either --json or --format" in result.stderr


def test_validate_text_and_manifest_output(minimal_source: Path, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"

    result = CliRunner().invoke(
        app,
        [
            "validate",
            "--asset-root",
            str(minimal_source),
            "--manifest-output",
            str(manifest_path),
        ],
    )

    assert result.exit_code == 0
    assert "passed: True" in result.stdout
    assert manifest_path.exists()


def test_validate_invalid_format_exits_2(minimal_source: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["validate", "--asset-root", str(minimal_source), "--format", "markdown"],
    )

    assert result.exit_code == 2
    assert "validate supports --format text|json" in result.stderr
