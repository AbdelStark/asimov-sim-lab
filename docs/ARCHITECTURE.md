# ARCHITECTURE — Asimov Sim Lab

## System Shape

Asimov Sim Lab is a local CLI and Python library. It does not run a server, open network connections, download upstream assets, or manage long-lived state. Every command reads a local Asimov v1 checkout, derives fresh contracts, and writes optional file artifacts.

```text
operator
  |
  v
cli.py
  |
  +-- paths.py -------- local asset-root resolution and Git provenance
  |
  +-- manifest.py ----- checksummed asset manifest
  |
  +-- inspect.py ------ MJCF parse and model contract extraction
  |
  +-- validation.py --- reference, range, sensor, actuator, and preset checks
  |
  +-- presets.py ------ built-in neutral preset and optional local TOML presets
  |
  +-- evidence.py ----- checksummed evidence bundle directory
  |
  v
models.py ------------ Pydantic public contracts and JSON Schemas
```

## Data Flow

1. The CLI resolves the source checkout from `--asset-root`, profile, or `ASIMOV_SIM_LAB_ASSET_ROOT`.
2. `paths.py` verifies the supported source layout and records local Git provenance.
3. `manifest.py` hashes the primary XML and STL files and records mesh reference provenance.
4. `inspect.py` parses `sim-model/xmls/asimov.xml` into an `InspectResult`.
5. `validation.py` derives validation issues from the current XML and inspect contract.
6. `evidence.py` can write the manifest, inspect result, validation result, Markdown report, and bundle index into one checksummed evidence directory.
7. The CLI emits text, Markdown, or JSON and optionally writes artifacts atomically.

## Public Contracts

The public contracts are Pydantic models in `src/asimov_sim_lab/models.py` and generated JSON Schemas in `docs/schemas/`. JSON output is the source of truth. Text and Markdown are views.

Current contract families:

- `AssetManifest`
- `DoctorResult`
- `InspectResult`
- `ValidationResult`
- `EvidenceBundleResult`
- `ErrorResult`

Generated schemas must be updated with:

```bash
uv run python scripts/generate_schemas.py
uv run python scripts/generate_schemas.py --check
```

## Design Decisions

- Source assets are local-checkout-only for the MVP. The tool never downloads or vendors upstream files.
- The supported source layout is intentionally narrow: `<asset-root>/sim-model/xmls/asimov.xml` and `<asset-root>/sim-model/assets/meshes/*.STL`.
- `compiler@meshdir` must resolve to `sim-model/assets/meshes`; other layouts fail with `UNSUPPORTED_SOURCE_LAYOUT`.
- The inspect contract exports concrete MJCF elements only. Defaults/templates are not counted as robot bodies or joints.
- Validation errors are typed `ValidationIssue` objects, not free-form log strings.
- Markdown reports are derived from `InspectResult`; they are not independent truth.
- Evidence bundles list artifact checksums in `evidence-bundle.json`; the bundle index is the review handle, not a replacement for the JSON contracts it references.

## Invariants

- Unknown fields are forbidden on public result contracts.
- Every machine-readable result has `schema_version`, `generated_at_utc`, `tool_version`, `command`, `status`, and `warnings`.
- Output files are written through a temporary file and atomic replace.
- Evidence bundle directories must be empty unless `--overwrite` is used.
- Invalid XML cannot produce a partial inspect contract.
- Malformed numeric or boolean MJCF attributes fail contract extraction rather than becoming `null`.
- Sensor object references are validated against the correct MJCF namespace: bodies, joints, sites, cameras, and concrete geoms.
- Generated schemas must match the committed model definitions.
- Local profile paths and asset roots are operator-local inputs, not portable public evidence by themselves.

## Failure Modes

- `ASSET_ROOT_NOT_FOUND`: no source root was provided or it does not exist.
- `PRIMARY_XML_NOT_FOUND`: the supported MJCF entrypoint is missing.
- `MESH_DIRECTORY_NOT_FOUND`: the supported mesh directory is missing.
- `UNSUPPORTED_SOURCE_LAYOUT`: the source layout does not match the MVP contract.
- `XML_PARSE_FAILED`: the primary XML is malformed.
- `XML_NUMERIC_PARSE_FAILED`: a numeric MJCF attribute cannot be parsed.
- `XML_BOOLEAN_PARSE_FAILED`: a boolean MJCF attribute is not one of `true`, `false`, `1`, or `0`.
- `OUTPUT_PATH_IS_DIRECTORY`: `--output` or `--manifest-output` points at a directory.
- `OUTPUT_WRITE_FAILED`: the command could not create, write, or atomically replace an output file.
- `EVIDENCE_OUTPUT_NOT_DIRECTORY`: `--output-dir` points at a non-directory path.
- `EVIDENCE_OUTPUT_NOT_EMPTY`: `--output-dir` is non-empty and `--overwrite` was not passed.

## Operational Runbook

This is not a deployed service. Operation means local command execution in CI, development, or a release-prep script.

### Fresh Setup

```bash
uv sync --extra dev
uv run asimov-sim-lab doctor --asset-root /absolute/path/to/asimov-v1 --format json
```

### Debug A Failing Source Checkout

```bash
uv run asimov-sim-lab doctor --asset-root /absolute/path/to/asimov-v1 --format json
uv run asimov-sim-lab inspect --asset-root /absolute/path/to/asimov-v1 --json
uv run asimov-sim-lab validate --asset-root /absolute/path/to/asimov-v1 --format json
uv run asimov-sim-lab evidence --asset-root /absolute/path/to/asimov-v1 --output-dir .asimov-sim-lab/evidence --overwrite --format json
```

Read `issues[].code`, `issues[].message`, and `issues[].remediation` before inspecting code. Most failures should be actionable from JSON alone.

### Refresh Schemas

```bash
uv run python scripts/generate_schemas.py
uv run python scripts/generate_schemas.py --check
```

Commit schema changes only when the public contract intentionally changed.

### Release Gate

```bash
make check
```

`make check` runs lockfile, format, lint, mypy, pytest with coverage, schema drift, build, and dependency audit gates.

### Optional Real-Upstream Smoke

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make smoke-real
```

The real-upstream smoke is intentionally optional because CI cannot assume access to a private or sibling checkout.

The smoke target also writes `.asimov-sim-lab/smoke-real-evidence/`, which is ignored local state and can be reviewed before sharing.

## Security And Privacy

- No secrets are required.
- `.env` and `.asimov-sim-lab/` are ignored local state.
- JSON artifacts and evidence bundle indexes may include absolute local paths in provenance fields. Treat generated artifacts as local diagnostics unless paths have been reviewed for publication.
- The tool does not execute XML content, shell out to MuJoCo, or open network connections.

## Current Boundaries

Deferred until separate contracts exist:

- MuJoCo viewer command
- screenshot, video, or capture artifacts
- local web UI or report viewer
- controller or policy-training workflows
- compiled-physics validation beyond XML contract extraction
