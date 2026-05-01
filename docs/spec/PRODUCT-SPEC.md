# PRODUCT-SPEC — Asimov Sim Lab

## One-line thesis

Turn a local Asimov v1 MuJoCo checkout into a serious developer-facing inspection, validation, and evidence tool before any viewer, controller, policy, or demo surface is built.

## Product shape

CLI-first Python package with a narrow public Python API, schema-backed JSON outputs, deterministic Markdown inspection reports, and optional future MuJoCo viewer support behind a `viewer` extra.

## Users

- robotics developers inspecting the public Asimov v1 simulation model
- contributors validating MJCF and mesh-facing changes
- technical reviewers who need reproducible evidence that reports came from real source assets
- future UI/reporting layers that need stable machine-readable contracts

## MVP promise

- locate an explicit local upstream checkout
- generate a fresh asset manifest with checksums and provenance
- export a concrete MJCF model contract
- validate mesh, actuator, sensor, joint-range, and preset references
- publish committed JSON Schemas for result artifacts
- prove happy and broken paths with tiny synthetic fixtures
- keep public docs aligned with shipped behavior

## Non-goals

- no controller, policy-training, RL, imitation-learning, or ML benchmark work
- no `open`, `capture`, screenshot, video, local UI, or web report viewer
- no automatic upstream download or hidden sibling discovery
- no vendored upstream XML or mesh assets
- no claims about hardware fidelity, manufacturing readiness, electrical safety, or policy performance

## Source Assets

The MVP supports this upstream layout only:

```text
<asset-root>/
  sim-model/
    xmls/asimov.xml
    assets/meshes/*.STL
    README.md
```

`--asset-root` means the upstream checkout root that contains `sim-model/`. Passing `sim-model/` directly is unsupported.

## Commands

```bash
asimov-sim-lab doctor --asset-root /path/to/asimov-v1 --format json
asimov-sim-lab inspect --asset-root /path/to/asimov-v1 --json
asimov-sim-lab inspect --asset-root /path/to/asimov-v1 --markdown
asimov-sim-lab validate --asset-root /path/to/asimov-v1 --format json
```

Asset-root precedence:

1. `--asset-root`
2. profile `default_asset_root`
3. `ASIMOV_SIM_LAB_ASSET_ROOT`
4. typed error with remediation

## Data Contracts

JSON artifacts are the source of truth. Text and Markdown are renderings.

Committed schemas:

- `docs/schemas/asset-manifest.schema.json`
- `docs/schemas/doctor-result.schema.json`
- `docs/schemas/error-result.schema.json`
- `docs/schemas/inspect-result.schema.json`
- `docs/schemas/validation-result.schema.json`

Every result includes schema version, tool version, generated timestamp, command, status, warnings, and enough provenance to identify the local source checkout.

## Inspection Contract

`inspect` uses standard XML parsing and exports concrete model elements only. MJCF defaults/templates do not count as robot joints or bodies.

MVP fields include:

- model name
- body, joint, actuator, sensor, mesh, camera, and site counts
- concrete body names
- mesh asset names and files
- joint names, bodies, types, axes, ranges, refs, limited flags, and passive flags
- generic actuator type, name, joint target, and control range
- minimal sensor target metadata
- minimal camera and site metadata
- optional `total_declared_mass_kg`, clearly scoped to declared XML mass values

`passive` means no actuator targets the joint. `floating_base` is passive and distinguished with `joint_type="free"`.

## Validation Contract

`validate` derives references from the current XML on every run. It validates:

- supported source layout
- mesh files referenced by MJCF asset declarations
- geom mesh references to declared mesh assets
- actuator joint references
- sensor site/body/object references
- limited or preset-targetable hinge/slide ranges
- built-in neutral preset
- optional local TOML presets via `--preset-dir`

Warnings do not fail by default. `--strict` escalates defined evidence-quality warnings such as dirty/unpinned provenance or missing optional upstream evidence.

## Presets

MVP presets are TOML only. The package ships an inferred built-in `neutral` preset:

- use `joint@ref` when present and inside range
- otherwise use `0.0` when inside range
- otherwise omit the joint and warn

Additional local presets can be validated from a directory, one preset per TOML file.

## Architecture

```text
asimov-sim-lab/
├── docs/
│   ├── examples/
│   ├── rfcs/
│   ├── schemas/
│   └── spec/
├── scripts/
│   └── generate_schemas.py
├── src/asimov_sim_lab/
│   ├── cli.py
│   ├── config.py
│   ├── doctor.py
│   ├── errors.py
│   ├── inspect.py
│   ├── manifest.py
│   ├── models.py
│   ├── paths.py
│   ├── presets.py
│   └── validation.py
└── tests/
    └── fixtures/
```

## Quality Gates

- `uv lock --check`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy`
- `uv run pytest`
- `uv run python scripts/generate_schemas.py`
- `git diff --exit-code -- docs/schemas`
- `uv build`
- `uv run pip-audit --skip-editable`

CI uses synthetic fixtures only. Real upstream smoke is optional and gated by `ASIMOV_SIM_LAB_ASSET_ROOT`.

## Deferred V1 Surface

- local MuJoCo `open` command
- capture/screenshot/video contracts
- report viewer or UI
- richer physical summaries from compiled MuJoCo state
- issue bundle generation
