from __future__ import annotations

from pathlib import Path

from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.presets import build_neutral_preset, load_preset_dir, validate_presets


def test_load_preset_dir_missing_is_error(tmp_path: Path) -> None:
    presets, issues = load_preset_dir(tmp_path / "missing")

    assert presets == []
    assert issues[0].code == "PRESET_DIRECTORY_NOT_FOUND"


def test_load_preset_dir_parse_error(tmp_path: Path) -> None:
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    (preset_dir / "bad.toml").write_text("name = [", encoding="utf-8")

    presets, issues = load_preset_dir(preset_dir)

    assert presets == []
    assert issues[0].code == "PRESET_PARSE_FAILED"


def test_load_preset_dir_filename_mismatch(tmp_path: Path) -> None:
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    (preset_dir / "wrong.toml").write_text(
        'schema_version = "0.1.0"\nname = "custom neutral"\n[joints]\n',
        encoding="utf-8",
    )

    presets, issues = load_preset_dir(preset_dir)

    assert [preset.name for preset in presets] == ["custom neutral"]
    assert issues[0].code == "PRESET_FILENAME_MISMATCH"


def test_validate_presets_unknown_and_nan(minimal_source: Path, tmp_path: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    inspect_result = inspect_model(resolution)
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    (preset_dir / "invalid.toml").write_text(
        (
            'schema_version = "0.1.0"\nname = "invalid"\n[joints]\n'
            "missing_joint = 0.0\nleft_hip_pitch_joint = nan\n"
        ),
        encoding="utf-8",
    )

    issues = validate_presets(inspect_result, preset_dir=preset_dir)

    assert any(issue.code == "PRESET_JOINT_UNKNOWN" for issue in issues)
    assert any(issue.code == "PRESET_VALUE_NOT_FINITE" for issue in issues)


def test_build_neutral_omits_joint_with_no_safe_value(tmp_path: Path) -> None:
    source = tmp_path
    (source / "sim-model" / "xmls").mkdir(parents=True)
    (source / "sim-model" / "assets" / "meshes").mkdir(parents=True)
    (source / "sim-model" / "xmls" / "asimov.xml").write_text(
        """
        <mujoco model="NoSafeNeutral">
          <compiler meshdir="../assets/meshes"/>
          <worldbody>
            <body name="pelvis_link">
              <joint name="offset_joint" type="hinge" range="1 2" axis="0 1 0"/>
            </body>
          </worldbody>
        </mujoco>
        """,
        encoding="utf-8",
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})
    inspect_result = inspect_model(resolution)

    neutral, issues = build_neutral_preset(inspect_result)

    assert "offset_joint" not in neutral.joints
    assert issues[0].code == "PRESET_NEUTRAL_VALUE_OMITTED"
