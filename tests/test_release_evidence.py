from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from asimov_sim_lab import runtime
from asimov_sim_lab.export import generate_export_package
from asimov_sim_lab.paths import resolve_asset_root


def test_release_evidence_checker_accepts_generated_export(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    export_dir = tmp_path / "export"
    generate_export_package(resolution, output_dir=export_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_release_evidence.py",
            "--export-dir",
            str(export_dir),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "release evidence ok" in result.stdout


def test_release_evidence_checker_rejects_checksum_mismatch(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    export_dir = tmp_path / "export"
    generate_export_package(resolution, output_dir=export_dir)
    result_path = export_dir / "export-package-result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["archive_sha256"] = "0" * 64
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_release_evidence.py",
            "--export-dir",
            str(export_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "checksum mismatch" in result.stderr


def test_release_candidate_report_records_verified_archive(
    minimal_source: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime, "_import_mujoco", lambda: None)
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    export_dir = tmp_path / "export"
    export_result = generate_export_package(resolution, output_dir=export_dir)
    output = tmp_path / "release-report.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/write_release_candidate_report.py",
            "--export-dir",
            str(export_dir),
            "--output",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    report = output.read_text(encoding="utf-8")
    assert f"archive_sha256: `{export_result.archive_sha256}`" in report
    assert "MUJOCO_NOT_INSTALLED" in report
    assert str(export_dir) not in report
