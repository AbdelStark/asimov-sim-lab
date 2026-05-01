from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab import runtime
from asimov_sim_lab.cli import app


def test_evidence_bundle_writes_complete_artifacts(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    output_dir = tmp_path / "evidence"

    result = CliRunner().invoke(
        app,
        [
            "evidence",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "evidence"
    assert payload["validation_passed"] is True
    assert payload["validation_issue_count"] >= 0
    assert payload["runtime_smoke_status"] == "warning"
    assert payload["runtime_smoke_skipped"] is True

    expected_files = {
        "asset-manifest.json",
        "inspect-result.json",
        "validation-result.json",
        "runtime-smoke-result.json",
        "inspect-report.md",
        "evidence-bundle.json",
    }
    assert {path.name for path in output_dir.iterdir()} == expected_files

    artifacts = {artifact["relative_path"]: artifact for artifact in payload["artifacts"]}
    assert set(artifacts) == expected_files - {"evidence-bundle.json"}
    for relative_path, artifact in artifacts.items():
        path = output_dir / relative_path
        assert artifact["sha256"] == _sha256(path)
        assert artifact["size_bytes"] == path.stat().st_size

    assert json.loads((output_dir / "evidence-bundle.json").read_text(encoding="utf-8")) == payload
    inspect_result = json.loads((output_dir / "inspect-result.json").read_text(encoding="utf-8"))
    validation_result = json.loads(
        (output_dir / "validation-result.json").read_text(encoding="utf-8")
    )
    runtime_result = json.loads(
        (output_dir / "runtime-smoke-result.json").read_text(encoding="utf-8")
    )
    assert inspect_result["source_manifest_path"] == "asset-manifest.json"
    assert validation_result["source_manifest_path"] == "asset-manifest.json"
    assert runtime_result["source_manifest_path"] == "asset-manifest.json"
    assert runtime_result["skipped"] is True
    assert "# AsimovFixture Model Contract" in (output_dir / "inspect-report.md").read_text(
        encoding="utf-8"
    )


def test_evidence_bundle_refuses_non_empty_output_without_overwrite(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    output_dir = tmp_path / "evidence"
    output_dir.mkdir()
    (output_dir / "leftover.txt").write_text("stale", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "evidence",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["issues"][0]["code"] == "EVIDENCE_OUTPUT_NOT_EMPTY"


def test_evidence_bundle_overwrite_replaces_known_artifacts(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    output_dir = tmp_path / "evidence"

    first = CliRunner().invoke(
        app,
        [
            "evidence",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
        ],
    )
    assert first.exit_code == 0
    (output_dir / "inspect-report.md").write_text("stale\n", encoding="utf-8")

    second = CliRunner().invoke(
        app,
        [
            "evidence",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(output_dir),
            "--overwrite",
            "--format",
            "json",
        ],
    )

    assert second.exit_code == 0
    assert "# AsimovFixture Model Contract" in (output_dir / "inspect-report.md").read_text(
        encoding="utf-8"
    )


def test_evidence_requires_output_dir(minimal_source: Path) -> None:
    result = CliRunner().invoke(app, ["evidence", "--asset-root", str(minimal_source)])

    assert result.exit_code == 2
    assert "evidence requires --output-dir" in result.stderr


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()
