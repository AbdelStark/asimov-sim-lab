"""Public Pydantic contracts and schema versions.

All result, manifest, and contract types live here so that the published JSON
Schemas under ``docs/schemas/`` stay in lockstep with the runtime models. Every
model forbids extra fields (``extra="forbid"``) to prevent silent contract
drift between releases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from asimov_sim_lab import __version__
from asimov_sim_lab.error_registry import HELP_URL as ERROR_REGISTRY_HELP_URL

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


class RuntimeModelCounts(StrictBaseModel):
    nbody: int
    njnt: int
    nu: int
    nsensor: int
    ngeom: int
    nmesh: int
    nq: int
    nv: int


class RuntimeSmokeResult(ResultEnvelope):
    command: Literal["runtime-smoke"] = "runtime-smoke"
    runtime: Literal["mujoco"] = "mujoco"
    runtime_available: bool
    runtime_version: str | None = None
    skipped: bool
    loaded: bool
    xml_path: str
    model_counts: RuntimeModelCounts | None = None
    elapsed_ms: float | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    failure_remediation: str | None = None


class EvidenceBundleResult(ResultEnvelope):
    command: Literal["evidence"] = "evidence"
    bundle_dir: str
    artifacts: list[EvidenceArtifact]
    validation_passed: bool
    validation_issue_count: int
    runtime_smoke_status: Status
    runtime_smoke_skipped: bool


class ExportPackageFile(StrictBaseModel):
    relative_path: str
    sha256: str
    size_bytes: int


class ExportPackageManifest(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    generated_at_utc: str = Field(default_factory=utc_now)
    generator_version: str = __version__
    evidence_bundle_path: str
    evidence_bundle_sha256: str
    evidence_artifacts: list[EvidenceArtifact]
    package_files: list[ExportPackageFile]
    deterministic: bool


class ExportPackageResult(ResultEnvelope):
    command: Literal["export"] = "export"
    package_dir: str
    archive_path: str
    archive_sha256: str
    archive_size_bytes: int
    evidence_bundle_path: str
    evidence_bundle_sha256: str
    package_manifest_path: str
    package_manifest_sha256: str
    deterministic: bool
    validation_passed: bool
    validation_issue_count: int
    runtime_smoke_status: Status
    runtime_smoke_skipped: bool


class ViewerOpenResult(ResultEnvelope):
    command: Literal["open"] = "open"
    runtime: Literal["mujoco"] = "mujoco"
    runtime_version: str | None = None
    xml_path: str
    preset_name: str | None = None
    validation_passed: bool
    validation_issue_count: int
    runtime_smoke_status: Status
    opened: bool
    launch_mode: Literal["interactive", "preflight_only"] = "preflight_only"
    failure_code: str | None = None
    failure_message: str | None = None
    failure_remediation: str | None = None
    failure_help_url: str | None = None


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
    help_url: str = ERROR_REGISTRY_HELP_URL
