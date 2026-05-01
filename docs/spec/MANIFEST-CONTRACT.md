# MANIFEST-CONTRACT — Asimov Sim Lab

## Why this exists
Before any parser or viewer code lands, the repo needs one canonical description of what upstream asset set was inspected, where it came from, and whether the local checkout is complete enough to trust.

## Contract scope
This contract defines the machine-readable manifest that every serious command will depend on:
- `doctor`
- `inspect`
- `validate`
- future `open` and `capture`

The manifest is the repo's first trust boundary. If the manifest is incomplete or stale, downstream reports must say so loudly.

## Canonical file
Default persisted manifest path:
- `.asimov-sim-lab/asset-manifest.json`

Optional alternate persisted manifest path:
- user-provided `--manifest-output <path>` under an allowed writable directory

Important distinction:
- `--output` is reserved for the command's primary result artifact
- `--manifest-output` is reserved for persisted asset-manifest material

## Manifest model
```python
from pydantic import BaseModel, Field
from typing import Literal

class SourceLocator(BaseModel):
    mode: Literal['local_checkout', 'release_snapshot']
    root_path: str
    locator: str
    snapshot_id: str | None = None
    upstream_repo_url: str | None = None
    upstream_commit: str | None = None
    upstream_branch: str | None = None
    git_dirty: bool | None = None
    git_untracked_count: int | None = None

class XmlEntry(BaseModel):
    relative_path: str
    sha256: str
    size_bytes: int

class MeshEntry(BaseModel):
    relative_path: str
    sha256: str
    size_bytes: int
    referenced_by: list[str] = Field(default_factory=list)

class AssetManifest(BaseModel):
    schema_version: str = '0.1.0'
    generated_at_utc: str
    generator_version: str
    source: SourceLocator
    primary_xml: XmlEntry
    meshes: list[MeshEntry]
    readme_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
```

## Required fields
- `schema_version`: explicit manifest contract version
- `generated_at_utc`: ISO-8601 UTC timestamp
- `generator_version`: package version that emitted the manifest
- `source.mode`: how the repo found the upstream assets
- `source.root_path`: local resolved root used during the run; this is local diagnostic data and generated artifacts must not be committed
- `source.locator`: whether the root came from CLI, profile, default profile, or env fallback
- `primary_xml`: the exact MJCF entrypoint used for inspection
- `meshes`: every discovered mesh file under the supported mesh root

## Required behaviors
1. The manifest must be reproducible from the same upstream checkout.
2. Every path stored in the manifest must be repo-relative or source-root-relative, never shell-shortened with `~`.
3. The manifest must record checksums for the primary XML and every mesh file included in scope.
4. Missing optional files may produce warnings.
5. Missing required files must fail validation.
6. Commands consuming the manifest must reject unknown future-major schema versions.
7. Git metadata must be recorded when the asset root is itself a Git worktree root.
8. Dirty or unpinned source provenance warns by default and fails under `--strict`.

## Supported upstream layout for MVP
The MVP only promises support for this upstream shape:
- `sim-model/xmls/asimov.xml`
- `sim-model/assets/meshes/*.STL`
- `sim-model/README.md`

If the upstream repo changes layout materially, the tool must emit a schema/layout drift error rather than pretending success.

## Output guarantees
The manifest must let a later command answer:
- what XML file was inspected?
- what exact local asset root was used?
- how many mesh files were present?
- did the tool see a pinned snapshot or an unpinned working checkout?

## Failure codes tied to this contract
- `ASSET_ROOT_NOT_FOUND`
- `PRIMARY_XML_NOT_FOUND`
- `MESH_DIRECTORY_NOT_FOUND`
- `UNSUPPORTED_SOURCE_LAYOUT`
- `CHECKSUM_COMPUTE_FAILED`
- `MANIFEST_SCHEMA_MISMATCH`

## Non-goals
- auto-fixing the upstream layout
- silently downloading missing assets in the middle of validation
- claiming license/redistribution clearance beyond recorded provenance fields

## First implementation cut
The first implementation only needs to support local-checkout mode truthfully. Release-snapshot mode can remain declared but unimplemented if the CLI reports that clearly.

Persisted manifests are evidence artifacts only in MVP. Commands regenerate manifests from the current local checkout and do not accept `--manifest-input`.
