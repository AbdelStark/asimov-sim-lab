# Asimov Sim Lab

Asimov Sim Lab is a Python CLI and library that inspects and validates a local Asimov v1 MuJoCo checkout, then emits schema-backed evidence artifacts.

## Status

As of May 1, 2026, this project is an alpha MVP. It is suitable for local source inspection, contract export, validation, optional MuJoCo runtime smoke checks, preflight-only viewer/open checks, deterministic evidence packaging, and CI-backed development against synthetic fixtures. It is not yet suitable for production robotics operation, hardware claims, controller evaluation, policy training, video capture, interactive viewer launch, or public release automation. Known limitations: local-checkout-only source assets, no interactive MuJoCo viewer launch, no screenshot/capture flow, no UI, no automatic upstream download, and runtime smoke checks only verify that MuJoCo can compile the MJCF. Breaking changes before `1.0` are possible.

## Why It Exists

The upstream Asimov v1 release contains useful MuJoCo assets, but raw XML and mesh files are hard to audit, diff, validate, and reuse safely. This repo turns that local source checkout into explicit contracts: asset manifests, model inspection JSON, validation results, optional runtime-smoke results, preflight-only viewer/open results, Markdown reports, checksummed evidence bundles, deterministic export archives, and JSON Schemas that future UI/report layers can trust.

## Who It Is For

- Robotics developers inspecting the Asimov v1 simulation model.
- Contributors validating MJCF, mesh, preset, and provenance changes.
- Reviewers who need reproducible evidence tied to source files and checksums.
- Future tools that need stable machine-readable model contracts.

## Install

Requirements:

- Python `>=3.12`
- `uv`
- A local Asimov v1 checkout containing `sim-model/xmls/asimov.xml`

```bash
uv sync --extra dev
```

Set the upstream asset root in one of three ways:

```bash
uv run asimov-sim-lab doctor --asset-root /absolute/path/to/asimov-v1
```

```bash
export ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1
uv run asimov-sim-lab doctor
```

```toml
# .asimov-sim-lab/profile.toml
schema_version = "0.1.0"
default_asset_root = "/absolute/path/to/asimov-v1"
strict_validation = true
```

`.asimov-sim-lab/` is local ignored state. Do not commit machine-specific paths or generated local reports unless they are intentional evidence artifacts.

## Use

Check layout and provenance:

```bash
uv run asimov-sim-lab doctor --asset-root /absolute/path/to/asimov-v1 --format json
```

Write an asset manifest:

```bash
uv run asimov-sim-lab doctor \
  --asset-root /absolute/path/to/asimov-v1 \
  --format json \
  --manifest-output .asimov-sim-lab/asset-manifest.json
```

Export the model contract:

```bash
uv run asimov-sim-lab inspect --asset-root /absolute/path/to/asimov-v1 --json
uv run asimov-sim-lab inspect --asset-root /absolute/path/to/asimov-v1 --markdown
```

Validate references, ranges, sensors, actuators, and presets:

```bash
uv run asimov-sim-lab validate --asset-root /absolute/path/to/asimov-v1 --format json
uv run asimov-sim-lab validate --asset-root /absolute/path/to/asimov-v1 --preset-dir docs/examples/presets --format json
```

Run the optional MuJoCo compiled-runtime smoke:

```bash
uv sync --extra viewer
uv run asimov-sim-lab runtime-smoke --asset-root /absolute/path/to/asimov-v1 --require-mujoco --format json
```

Without the `viewer` extra, `runtime-smoke` exits `0` by default with a warning and `skipped: true`. Use `--require-mujoco` when the runtime is expected to be installed.

Run the viewer/open preflight contract:

```bash
uv sync --extra viewer
uv run asimov-sim-lab open --asset-root /absolute/path/to/asimov-v1 --format json
```

`open` is preflight-only in this alpha. It validates the source checkout, requested preset, and MuJoCo compile path, then emits `ViewerOpenResult` with `opened=false` and `launch_mode=preflight_only`. It never opens an interactive window, steps simulation, captures media, or evaluates controllers.

Generate a complete evidence bundle:

```bash
uv run asimov-sim-lab evidence \
  --asset-root /absolute/path/to/asimov-v1 \
  --output-dir .asimov-sim-lab/evidence \
  --overwrite \
  --format json
```

The bundle directory contains `asset-manifest.json`, `inspect-result.json`, `validation-result.json`, `runtime-smoke-result.json`, `inspect-report.md`, and `evidence-bundle.json`.

Generate a deterministic export package:

```bash
uv run asimov-sim-lab export \
  --asset-root /absolute/path/to/asimov-v1 \
  --output-dir .asimov-sim-lab/export \
  --overwrite \
  --format json
```

The export directory contains a portable evidence bundle, `export-package-manifest.json`, `export-package-result.json`, and `asimov-sim-lab-evidence.tar.gz`. The archive normalizes timestamps and tar metadata by default, so identical inputs produce identical archive hashes.

Verify an export package before attaching it to a release candidate:

```bash
uv run python scripts/check_release_evidence.py --export-dir .asimov-sim-lab/export
```

Generate a sanitized release-candidate dry-run report from a real-upstream export:

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make release-dry-run
```

Exit codes:

- `0`: command succeeded, including warnings-only validation
- `1`: validation failed or XML contract parsing failed
- `2`: invalid CLI usage or invalid output path
- `3`: missing or unsupported source layout

## Contracts

JSON artifacts are the source of truth. Text and Markdown are renderings.

- `docs/schemas/asset-manifest.schema.json`
- `docs/schemas/doctor-result.schema.json`
- `docs/schemas/evidence-bundle-result.schema.json`
- `docs/schemas/error-result.schema.json`
- `docs/schemas/export-package-manifest.schema.json`
- `docs/schemas/export-package-result.schema.json`
- `docs/schemas/inspect-result.schema.json`
- `docs/schemas/runtime-smoke-result.schema.json`
- `docs/schemas/validation-result.schema.json`
- `docs/schemas/viewer-open-result.schema.json`

The inspect contract currently exports model name, bodies, joints, actuators, sensors, mesh assets, concrete geoms, cameras, sites, declared XML mass totals, passive-joint inference, and typed warnings. The validator checks supported source layout, mesh files, geom mesh references, actuator targets, sensor targets, joint ranges, and built-in or local TOML presets. Runtime smoke checks verify optional MuJoCo import and model compilation only; they do not simulate, control, or score robot behavior. `open` adds viewer-specific preflight gating and result shape without launching an interactive viewer.

## Architecture

Core modules live in `src/asimov_sim_lab/`:

- `paths.py`: asset-root resolution, supported-layout checks, Git provenance
- `manifest.py`: checksummed source manifest generation
- `inspect.py`: MJCF parsing and inspect-contract extraction
- `validation.py`: reference, range, sensor, actuator, and preset validation
- `presets.py`: built-in neutral preset and local TOML preset validation
- `runtime.py`: optional MuJoCo compiled-runtime smoke validation
- `viewer.py`: preflight-only viewer/open contract
- `evidence.py`: checksummed evidence bundle generation
- `export.py`: deterministic export archive generation
- `models.py`: Pydantic public contracts and schema versions
- `cli.py`: Typer command surface and output handling

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for invariants, data flow, failure modes, and the runbook.

## Develop

```bash
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run python scripts/generate_schemas.py --check
uv run python scripts/check_error_registry.py --check
uv build
uv run pip-audit --skip-editable
```

Or run the full gate:

```bash
make check
```

Optional real-upstream smoke:

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make smoke-real
```

Release-candidate dry run:

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make release-dry-run
```

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md), [docs/spec/PRODUCT-SPEC.md](docs/spec/PRODUCT-SPEC.md), and [AGENTS.md](AGENTS.md). Keep changes contract-first: update code, tests, generated schemas, and docs together. Diagnostic-code changes must update [docs/spec/ERROR-CODE-REGISTRY.md](docs/spec/ERROR-CODE-REGISTRY.md). JSON-mode domain errors include a `help_url` back to that registry. Release candidates must follow [docs/spec/RELEASE-CANDIDATE-EVIDENCE-POLICY.md](docs/spec/RELEASE-CANDIDATE-EVIDENCE-POLICY.md). Do not add interactive viewer launch, capture, controller, policy, or UI surfaces without a contract and tests.

## Roadmap

Next three milestones:

- **M1: Publication-safe evidence review.** Exit criteria: a redaction/review guide covers absolute paths, upstream license disclosure, dirty-source warnings, and release attachments.
- **M2: Schema compatibility policy.** Exit criteria: public schemas declare compatibility expectations for alpha changes, and tests catch accidental version drift.
- **M3: Interactive viewer design gate.** Exit criteria: preflight telemetry from `open` is reviewed, and any GUI launch proposal includes shutdown/error behavior before implementation.

## Help

Use GitHub issues for bugs, feature proposals, and documentation gaps. Include the command, exit code, JSON output when available, asset-root layout, and whether the source checkout was dirty.
