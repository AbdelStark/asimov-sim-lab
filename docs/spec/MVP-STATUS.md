# MVP-STATUS — Asimov Sim Lab

## Current state

- date: May 1, 2026
- phase: alpha MVP core implemented
- repo: created and pushed
- remote: configured
- package scaffold: present
- contracts: implemented as Pydantic models and generated JSON Schemas
- implementation: `doctor`, `inspect`, and `validate` are runnable
- validation posture: synthetic fixtures in CI, optional real-upstream smoke by environment variable

## What is real

- local asset-root resolution by `--asset-root`, profile, or `ASIMOV_SIM_LAB_ASSET_ROOT`
- supported-layout checks for `sim-model/xmls/asimov.xml` and `sim-model/assets/meshes`
- checksummed asset manifest generation
- MJCF inspect contract export for bodies, joints, actuators, sensors, mesh assets, concrete geoms, cameras, sites, passive joints, and declared XML mass totals
- validation for mesh files, geom mesh references, actuator targets, sensor targets, joint ranges, built-in neutral preset, and local TOML presets
- checksummed evidence bundle generation with manifest, inspect JSON, validation JSON, Markdown report, and bundle index
- JSON-mode structured errors for recoverable domain failures
- generated JSON Schemas in `docs/schemas/`
- `make check` gate covering lockfile, format, lint, mypy, pytest, schema drift, build, and dependency audit
- optional `make smoke-real` now exercises the evidence bundle path against a local upstream checkout
- `AGENTS.md`, `CHANGELOG.md`, `LICENSE`, `.env.example`, and architecture/runbook documentation

## What is intentionally not real yet

- no automatic upstream sync or download
- no vendored upstream XML or meshes
- no polished demo UI or report viewer
- no MuJoCo viewer/open command
- no screenshot, video, or capture command
- no controller or policy-training path
- no hardware-fidelity, manufacturing, electrical-safety, or policy-performance claims

## Current limitations

- The MVP supports one source layout only.
- JSON artifacts and evidence bundles may contain absolute local paths and should be reviewed before publication.
- Real-upstream smoke is optional because CI cannot assume access to a local Asimov checkout.
- Validation is XML-contract validation, not compiled MuJoCo physics validation.

## Next target

Alpha contract hardening:

- document all public contract fields and warning/error codes
- add a publication-safe evidence redaction/review guide
- keep optional real-upstream smoke evidence as a reviewable artifact
- define the viewer contract before adding any MuJoCo runtime surface
