"""Public Pydantic contracts for Asimov Sim Lab."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from asimov_sim_lab import __version__

SCHEMA_VERSION = "0.1.0"

Status = Literal["ok", "warning", "error"]
Severity = Literal["error", "warning"]


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for result artifacts."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class StrictBaseModel(BaseModel):
    """Base model that rejects accidental public-contract drift."""

    model_config = ConfigDict(extra="forbid")


class SourceLocator(StrictBaseModel):
    mode: Literal["local_checkout", "release_snapshot"]
    root_path: str
    locator: str
    snapshot_id: str | None = None
    upstream_repo_url: str | None = None
    upstream_commit: str | None = None
    upstream_branch: str | None = None
    git_dirty: bool | None = None
    git_untracked_count: int | None = None


class XmlEntry(StrictBaseModel):
    relative_path: str
    sha256: str
    size_bytes: int


class MeshEntry(StrictBaseModel):
    relative_path: str
    sha256: str
    size_bytes: int
    referenced_by: list[str] = Field(default_factory=list)


class AssetManifest(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    generated_at_utc: str = Field(default_factory=utc_now)
    generator_version: str = __version__
    source: SourceLocator
    primary_xml: XmlEntry
    meshes: list[MeshEntry]
    readme_path: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ResultEnvelope(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    generated_at_utc: str = Field(default_factory=utc_now)
    tool_version: str = __version__
    command: str
    source_manifest_path: str | None = None
    status: Status
    warnings: list[str] = Field(default_factory=list)


class DoctorCheck(StrictBaseModel):
    name: str
    status: Status
    detail: str
    code: str | None = None


class DoctorResult(ResultEnvelope):
    command: Literal["doctor"] = "doctor"
    checks: list[DoctorCheck]
    resolved_asset_root: str | None = None


class EvidenceArtifact(StrictBaseModel):
    artifact_type: str
    relative_path: str
    sha256: str
    size_bytes: int


class EvidenceBundleResult(ResultEnvelope):
    command: Literal["evidence"] = "evidence"
    bundle_dir: str
    artifacts: list[EvidenceArtifact]
    validation_passed: bool
    validation_issue_count: int


class MeshAssetContract(StrictBaseModel):
    name: str
    file: str


class GeomContract(StrictBaseModel):
    name: str
    body: str
    geom_type: str | None = None
    mesh: str | None = None


class JointContract(StrictBaseModel):
    name: str
    body: str
    joint_type: str
    axis: tuple[float, float, float] | None = None
    range_min: float | None = None
    range_max: float | None = None
    ref: float | None = None
    limited: bool | None = None
    passive: bool


class ActuatorContract(StrictBaseModel):
    name: str
    actuator_type: str
    joint_name: str | None = None
    ctrl_min: float | None = None
    ctrl_max: float | None = None


class SensorContract(StrictBaseModel):
    name: str
    sensor_type: str
    site: str | None = None
    body: str | None = None
    objtype: str | None = None
    objname: str | None = None


class CameraContract(StrictBaseModel):
    name: str
    body: str
    mode: str | None = None
    pos: tuple[float, float, float] | None = None
    quat: tuple[float, float, float, float] | None = None
    fovy: float | None = None


class SiteContract(StrictBaseModel):
    name: str
    body: str
    pos: tuple[float, float, float] | None = None


class InspectResult(ResultEnvelope):
    command: Literal["inspect"] = "inspect"
    model_name: str
    body_count: int
    joint_count: int
    actuator_count: int
    sensor_count: int
    mesh_count: int
    geom_count: int
    camera_count: int
    site_count: int
    total_declared_mass_kg: float | None = None
    bodies: list[str]
    meshes: list[MeshAssetContract]
    geoms: list[GeomContract]
    joints: list[JointContract]
    actuators: list[ActuatorContract]
    sensors: list[SensorContract]
    cameras: list[CameraContract]
    sites: list[SiteContract]


class ValidationIssue(StrictBaseModel):
    code: str
    severity: Severity
    message: str
    remediation: str | None = None
    relative_path: str | None = None
    object_name: str | None = None


class ValidationResult(ResultEnvelope):
    command: Literal["validate"] = "validate"
    passed: bool
    issue_count: int
    issues: list[ValidationIssue]
    checked_paths: list[str]


class ErrorResult(ResultEnvelope):
    issues: list[ValidationIssue]
