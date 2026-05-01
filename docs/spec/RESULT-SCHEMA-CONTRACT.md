# RESULT-SCHEMA-CONTRACT — Asimov Sim Lab

## Why this exists
The CLI, tests, CI, and any later UI layer need one stable output surface. This repo should not let pretty terminal rendering become the source of truth.

## Core principle
Human-readable output is a view. JSON artifacts are the contract.

## Result families
The MVP needs four result families:
1. asset discovery / doctor
2. inspection / model contract export
3. validation
4. evidence bundle summaries
5. structured domain errors for JSON-mode failures

## Shared envelope
Every machine-readable result must include this top-level envelope:
```python
from pydantic import BaseModel, Field
from typing import Literal

class ResultEnvelope(BaseModel):
    schema_version: str = '0.1.0'
    generated_at_utc: str
    tool_version: str
    command: str
    source_manifest_path: str | None = None
    status: Literal['ok', 'warning', 'error']
    warnings: list[str] = Field(default_factory=list)
```

## Inspect result contract
```python
class JointContract(BaseModel):
    name: str
    body: str
    joint_type: str
    axis: tuple[float, float, float] | None = None
    range_min: float | None = None
    range_max: float | None = None
    ref: float | None = None
    limited: bool | None = None
    passive: bool

class ActuatorContract(BaseModel):
    name: str
    actuator_type: str
    joint_name: str | None = None
    ctrl_min: float | None = None
    ctrl_max: float | None = None

class MeshAssetContract(BaseModel):
    name: str
    file: str

class GeomContract(BaseModel):
    name: str
    body: str
    geom_type: str | None = None
    mesh: str | None = None

class SensorContract(BaseModel):
    name: str
    sensor_type: str
    site: str | None = None
    body: str | None = None
    objtype: str | None = None
    objname: str | None = None

class CameraContract(BaseModel):
    name: str
    body: str
    mode: str | None = None
    pos: tuple[float, float, float] | None = None
    quat: tuple[float, float, float, float] | None = None
    fovy: float | None = None

class SiteContract(BaseModel):
    name: str
    body: str
    pos: tuple[float, float, float] | None = None

class InspectResult(ResultEnvelope):
    command: Literal['inspect'] = 'inspect'
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
```

## Validation result contract
```python
class ValidationIssue(BaseModel):
    code: str
    severity: Literal['error', 'warning']
    message: str
    remediation: str | None = None
    relative_path: str | None = None
    object_name: str | None = None

class ValidationResult(ResultEnvelope):
    command: Literal['validate'] = 'validate'
    passed: bool
    issue_count: int
    issues: list[ValidationIssue]
    checked_paths: list[str]
```

## Evidence bundle result contract
```python
class EvidenceArtifact(BaseModel):
    artifact_type: str
    relative_path: str
    sha256: str
    size_bytes: int

class EvidenceBundleResult(ResultEnvelope):
    command: Literal['evidence'] = 'evidence'
    bundle_dir: str
    artifacts: list[EvidenceArtifact]
    validation_passed: bool
    validation_issue_count: int
```

## Doctor result contract
```python
class DoctorCheck(BaseModel):
    name: str
    status: Literal['ok', 'warning', 'error']
    detail: str

class DoctorResult(ResultEnvelope):
    command: Literal['doctor'] = 'doctor'
    checks: list[DoctorCheck]
    resolved_asset_root: str | None = None
```

## Error result contract
```python
class ErrorResult(ResultEnvelope):
    issues: list[ValidationIssue]
```

## Serialization rules
- JSON must be UTF-8 encoded.
- Key order does not matter semantically.
- Numeric units must remain explicit in field names where ambiguity exists.
- `None` should serialize as `null`, not synthetic zero values.
- Unknown extra fields must be rejected in tests for the canonical export path.

## Markdown export posture
Markdown is allowed for `inspect`, but it is a derived rendering of `InspectResult`, not an independent schema.

## Provenance requirements
Every result must preserve enough provenance to answer:
- which command emitted it?
- which manifest or asset root did it use?
- which package version emitted it?
- when was it generated?

## Exit-code semantics
- `ok` + no errors -> exit code `0`
- warnings only -> exit code `0`
- validation or contract errors -> non-zero exit code
- evidence bundle exits non-zero when bundled validation did not pass

## Non-goals
- multi-version backward compatibility at v0 beyond explicit schema checks
- browser UI wire format design
- video capture metadata contract in this phase
- partial inspect contracts for malformed XML
