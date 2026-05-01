"""Local profile loading for Asimov Sim Lab."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from asimov_sim_lab.errors import LabError

DEFAULT_PROFILE_PATH = Path(".asimov-sim-lab/profile.toml")
ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "name",
    "default_asset_root",
    "default_output_dir",
    "strict_validation",
    "viewer",
    "capture",
}


class Profile(BaseModel):
    """Operator-local profile input."""

    model_config = ConfigDict(extra="ignore")

    schema_version: str = "0.1.0"
    name: str | None = None
    default_asset_root: Path | None = None
    default_output_dir: Path | None = None
    strict_validation: bool = False
    warnings: list[str] = Field(default_factory=list)

    @field_validator("default_asset_root")
    @classmethod
    def _asset_root_must_be_absolute(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("default_asset_root must be absolute")
        return value


def load_profile(
    profile_path: Path | None,
    *,
    repo_root: Path | None = None,
    strict: bool = False,
) -> tuple[Profile | None, str | None]:
    """Load an explicit or default profile.

    Returns the profile and a provenance label (`profile` or `default_profile`).
    """
    root = repo_root or Path.cwd()
    if profile_path is None:
        candidate = root / DEFAULT_PROFILE_PATH
        locator = "default_profile"
        if not candidate.exists():
            return None, None
    else:
        candidate = profile_path
        locator = "profile"
        if not candidate.exists():
            raise LabError(
                "PROFILE_NOT_FOUND",
                f"Profile does not exist: {candidate}",
                "Pass an existing --profile path or omit --profile.",
                exit_code=2,
            )

    try:
        raw = tomllib.loads(candidate.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise LabError(
            "PROFILE_PARSE_FAILED",
            f"Could not parse profile: {candidate}: {exc}",
            "Fix the TOML syntax in the profile file.",
            exit_code=2,
        ) from exc
    except OSError as exc:
        raise LabError(
            "PROFILE_PARSE_FAILED",
            f"Could not read profile: {candidate}: {exc}",
            "Check profile file permissions.",
            exit_code=2,
        ) from exc

    warnings = _profile_unknown_field_warnings(raw)
    raw_strict = bool(raw.get("strict_validation", False))
    if (strict or raw_strict) and warnings:
        raise LabError(
            "PROFILE_UNKNOWN_FIELD",
            "; ".join(warnings),
            "Remove unknown top-level profile fields.",
            exit_code=2,
        )

    try:
        profile = Profile.model_validate(raw)
    except ValidationError as exc:
        raise LabError(
            "PROFILE_INVALID_PATH",
            f"Profile validation failed: {exc}",
            "Check profile field values and paths.",
            exit_code=2,
        ) from exc

    profile.warnings.extend(warnings)
    return profile, locator


def _profile_unknown_field_warnings(raw: Mapping[str, object]) -> list[str]:
    warnings: list[str] = []
    for key in sorted(set(raw) - ALLOWED_TOP_LEVEL_KEYS):
        warnings.append(f"PROFILE_UNKNOWN_FIELD: unknown top-level profile key {key!r}")
    return warnings
