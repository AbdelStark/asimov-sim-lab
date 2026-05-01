# MVP-STATUS — Asimov Sim Lab

## Current state

- date: May 1, 2026
- phase: alpha MVP core implemented
- repo: created and pushed
- remote: configured
- package scaffold: present
- contracts: implemented as Pydantic models and generated JSON Schemas
- implementation: `doctor`, `inspect`, `validate`, `runtime-smoke`, `open` preflight, `evidence`, and `export` are runnable
- validation posture: synthetic fixtures in CI, retained fixture evidence/export artifacts, optional real-upstream smoke by environment variable

## What is real

- local asset-root resolution by `--asset-root`, profile, or `ASIMOV_SIM_LAB_ASSET_ROOT`
- supported-layout checks for `sim-model/xmls/asimov.xml` and `sim-model/assets/meshes`
- checksummed asset manifest generation
- MJCF inspect contract export for bodies, joints, actuators, sensors, mesh assets, concrete geoms, cameras, sites, passive joints, and declared XML mass totals
- validation for mesh files, geom mesh references, actuator targets, sensor targets, joint ranges, built-in neutral preset, and local TOML presets
- optional MuJoCo runtime smoke that records compile success, compile failure, or explicit skipped state
- preflight-only viewer/open command that validates source, preset, optional provenance gates, and MuJoCo compile readiness without launching a GUI
- checksummed evidence bundle generation with manifest, inspect JSON, validation JSON, runtime-smoke JSON, Markdown report, and bundle index
- deterministic export package generation with portable evidence bundle, package manifest, and archive checksum
- JSON-mode structured errors for recoverable domain failures
- generated JSON Schemas in `docs/schemas/`
- `make check` gate covering lockfile, format, lint, mypy, pytest, schema drift, build, and dependency audit
- enforced diagnostic-code registry in `docs/spec/ERROR-CODE-REGISTRY.md`
- release-candidate evidence policy and export-package verifier
- viewer/open RFC implemented for preflight-only behavior
- optional `make smoke-real` now exercises runtime smoke, evidence bundle generation, and export packaging against a local upstream checkout
- optional `make release-dry-run` records a sanitized real-upstream archive SHA-256, warnings, blockers, and verification command
- `AGENTS.md`, `CHANGELOG.md`, `LICENSE`, `.env.example`, and architecture/runbook documentation

## What is intentionally not real yet

- no automatic upstream sync or download
- no vendored upstream XML or meshes
- no polished demo UI or report viewer
- no interactive MuJoCo viewer launch
- no screenshot, video, or capture command
- no controller or policy-training path
- no hardware-fidelity, manufacturing, electrical-safety, or policy-performance claims

## Current limitations

- The MVP supports one source layout only.
- JSON artifacts and evidence bundles may contain absolute local paths and should be reviewed before publication.
- Real-upstream smoke is optional because CI cannot assume access to a local Asimov checkout.
- Runtime smoke verifies optional MuJoCo model compilation only; it is not simulation stepping, controller validation, or physics-quality validation.

## Next target

Alpha contract hardening:

- add a publication-safe evidence redaction/review guide
- formalize schema compatibility and version-drift checks for alpha public contracts
- use `open` preflight telemetry to design an interactive viewer launch contract before any GUI is implemented
