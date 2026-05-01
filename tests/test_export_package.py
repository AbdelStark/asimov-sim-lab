from __future__ import annotations

import json
import tarfile
from pathlib import Path

from typer.testing import CliRunner

from asimov_sim_lab import runtime
from asimov_sim_lab.artifacts import sha256_file
from asimov_sim_lab.cli import app


def test_export_package_writes_deterministic_archive(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = _run_export(minimal_source, first_dir)
    second = _run_export(minimal_source, second_dir)

    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)

    assert first_payload["command"] == "export"
    assert first_payload["deterministic"] is True
    assert first_payload["validation_passed"] is True
    assert first_payload["runtime_smoke_status"] == "warning"
    assert first_payload["archive_sha256"] == second_payload["archive_sha256"]

    archive_path = Path(first_payload["archive_path"])
    assert first_payload["archive_sha256"] == sha256_file(archive_path)
    assert first_payload["evidence_bundle_path"] == "evidence/evidence-bundle.json"
    assert first_payload["package_manifest_path"] == "export-package-manifest.json"

    with tarfile.open(archive_path, mode="r:gz") as archive:
        assert archive.getnames() == [
            "evidence/asset-manifest.json",
            "evidence/evidence-bundle.json",
            "evidence/inspect-report.md",
            "evidence/inspect-result.json",
            "evidence/runtime-smoke-result.json",
            "evidence/validation-result.json",
            "export-package-manifest.json",
        ]
        for member in archive.getmembers():
            assert member.mtime == 0
            assert member.uid == 0
            assert member.gid == 0

    evidence_bundle = json.loads(
        (first_dir / "evidence" / "evidence-bundle.json").read_text(encoding="utf-8")
    )
    assert evidence_bundle["bundle_dir"] == "evidence"
    assert evidence_bundle["generated_at_utc"] == "1970-01-01T00:00:00Z"
    assert "runtime-smoke-result.json" in {
        artifact["relative_path"] for artifact in evidence_bundle["artifacts"]
    }


def test_export_refuses_non_empty_output_without_overwrite(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    output_dir = tmp_path / "export"
    output_dir.mkdir()
    (output_dir / "leftover.txt").write_text("stale", encoding="utf-8")

    result = _run_export(minimal_source, output_dir)

    assert result.exit_code == 2
    assert json.loads(result.stdout)["issues"][0]["code"] == "EXPORT_OUTPUT_NOT_EMPTY"


def test_export_overwrite_replaces_archive(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    output_dir = tmp_path / "export"

    first = _run_export(minimal_source, output_dir)
    assert first.exit_code == 0
    archive_path = output_dir / "asimov-sim-lab-evidence.tar.gz"
    archive_path.write_bytes(b"stale")

    second = _run_export(minimal_source, output_dir, "--overwrite")

    assert second.exit_code == 0
    assert sha256_file(archive_path) == json.loads(second.stdout)["archive_sha256"]


def test_export_rejects_unsafe_package_name(minimal_source: Path, tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "export",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(tmp_path / "export"),
            "--package-name",
            "../bad",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 2
    assert json.loads(result.stdout)["issues"][0]["code"] == "EXPORT_PACKAGE_NAME_INVALID"


def _run_export(minimal_source: Path, output_dir: Path, *extra: str):
    return CliRunner().invoke(
        app,
        [
            "export",
            "--asset-root",
            str(minimal_source),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
            *extra,
        ],
    )
