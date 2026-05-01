"""Preset pose loading and validation."""

from __future__ import annotations

import math
import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from asimov_sim_lab.models import InspectResult, JointContract, ValidationIssue


class Preset(BaseModel):
    """A named joint pose preset."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    name: str
    description: str | None = None
    joints: dict[str, float] = Field(default_factory=dict)


def build_neutral_preset(inspect_result: InspectResult) -> tuple[Preset, list[ValidationIssue]]:
    """Infer a conservative neutral preset from current joint refs/ranges."""
    joints: dict[str, float] = {}
    issues: list[ValidationIssue] = []
    for joint in inspect_result.joints:
        if joint.joint_type == "free":
            continue
        if not _has_finite_range(joint):
            continue
        value = _safe_neutral_value(joint)
        if value is None:
            issues.append(
                ValidationIssue(
                    code="PRESET_NEUTRAL_VALUE_OMITTED",
                    severity="warning",
                    message=f"No safe neutral value could be inferred for {joint.name}.",
                    object_name=joint.name,
                )
            )
            continue
        joints[joint.name] = value
    return Preset(
        name="neutral", description="Generated neutral inspection pose.", joints=joints
    ), issues


def load_preset_dir(preset_dir: Path) -> tuple[list[Preset], list[ValidationIssue]]:
    """Load TOML preset files from a directory."""
    issues: list[ValidationIssue] = []
    presets: list[Preset] = []
    if not preset_dir.exists() or not preset_dir.is_dir():
        return [], [
            ValidationIssue(
                code="PRESET_DIRECTORY_NOT_FOUND",
                severity="error",
                message=f"Preset directory does not exist: {preset_dir}",
                remediation="Pass an existing --preset-dir path.",
            )
        ]

    for path in sorted(preset_dir.glob("*.toml")):
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
            preset = Preset.model_validate(raw)
        except (OSError, tomllib.TOMLDecodeError, ValidationError) as exc:
            issues.append(
                ValidationIssue(
                    code="PRESET_PARSE_FAILED",
                    severity="error",
                    message=f"Could not load preset {path}: {exc}",
                    relative_path=path.name,
                )
            )
            continue
        expected_slug = _slugify(preset.name)
        if path.stem != expected_slug:
            issues.append(
                ValidationIssue(
                    code="PRESET_FILENAME_MISMATCH",
                    severity="warning",
                    message=(
                        f"Preset filename {path.name!r} does not match preset name {preset.name!r}."
                    ),
                    remediation=f"Rename the file to {expected_slug}.toml.",
                    relative_path=path.name,
                    object_name=preset.name,
                )
            )
        presets.append(preset)
    return presets, issues


def validate_presets(
    inspect_result: InspectResult,
    *,
    preset_dir: Path | None = None,
) -> list[ValidationIssue]:
    """Validate built-in neutral and optional local presets."""
    issues: list[ValidationIssue] = []
    neutral, neutral_issues = build_neutral_preset(inspect_result)
    issues.extend(neutral_issues)
    issues.extend(_validate_preset(neutral, inspect_result, built_in=True))

    if preset_dir is not None:
        presets, load_issues = load_preset_dir(preset_dir)
        issues.extend(load_issues)
        for preset in presets:
            issues.extend(_validate_preset(preset, inspect_result, built_in=False))
    return issues


def _validate_preset(
    preset: Preset, inspect_result: InspectResult, *, built_in: bool
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    joints = {joint.name: joint for joint in inspect_result.joints}
    source = "built-in preset" if built_in else "preset"
    for joint_name, value in preset.joints.items():
        joint = joints.get(joint_name)
        if joint is None:
            issues.append(
                ValidationIssue(
                    code="PRESET_JOINT_UNKNOWN",
                    severity="error",
                    message=f"{source} {preset.name!r} references unknown joint {joint_name!r}.",
                    object_name=joint_name,
                )
            )
            continue
        if not math.isfinite(value):
            issues.append(
                ValidationIssue(
                    code="PRESET_VALUE_NOT_FINITE",
                    severity="error",
                    message=(
                        f"{source} {preset.name!r} has non-finite value for joint {joint_name!r}."
                    ),
                    object_name=joint_name,
                )
            )
            continue
        if not _has_finite_range(joint):
            issues.append(
                ValidationIssue(
                    code="PRESET_JOINT_RANGE_MISSING",
                    severity="error",
                    message=(
                        f"{source} {preset.name!r} targets joint without "
                        f"a finite range: {joint_name!r}."
                    ),
                    object_name=joint_name,
                )
            )
            continue
        assert joint.range_min is not None
        assert joint.range_max is not None
        if value < joint.range_min or value > joint.range_max:
            issues.append(
                ValidationIssue(
                    code="PRESET_VALUE_OUT_OF_RANGE",
                    severity="error",
                    message=(
                        f"{source} {preset.name!r} value {value} is outside range "
                        f"{joint.range_min}..{joint.range_max} for {joint_name!r}."
                    ),
                    object_name=joint_name,
                )
            )
    return issues


def _safe_neutral_value(joint: JointContract) -> float | None:
    assert joint.range_min is not None
    assert joint.range_max is not None
    if joint.ref is not None and joint.range_min <= joint.ref <= joint.range_max:
        return joint.ref
    if joint.range_min <= 0.0 <= joint.range_max:
        return 0.0
    return None


def _has_finite_range(joint: JointContract) -> bool:
    return joint.range_min is not None and joint.range_max is not None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "preset"
