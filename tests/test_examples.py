from __future__ import annotations

import tomllib
from pathlib import Path

from asimov_sim_lab.config import Profile
from asimov_sim_lab.presets import Preset, load_preset_dir


def test_profile_example_parses(fixtures_dir: Path) -> None:
    profile_path = fixtures_dir.parent.parent / "docs" / "examples" / "profile.toml"
    raw = profile_path.read_text(encoding="utf-8")

    profile = Profile.model_validate(tomllib.loads(raw))

    assert profile.default_asset_root == Path("/absolute/path/to/asimov-v1")


def test_preset_example_parses() -> None:
    preset_path = Path("docs/examples/presets/custom-neutral.toml")
    raw = preset_path.read_text(encoding="utf-8")

    preset = Preset.model_validate(tomllib.loads(raw))

    assert preset.name == "custom-neutral"
    assert preset.joints["left_hip_pitch_joint"] == 0.25


def test_preset_example_directory_loads() -> None:
    presets, issues = load_preset_dir(Path("docs/examples/presets"))

    assert not [issue for issue in issues if issue.severity == "error"]
    assert {preset.name for preset in presets} == {"custom-neutral"}
