# Asimov Sim Lab

Asimov Sim Lab is a Python CLI and library that inspects and validates a local Asimov v1 MuJoCo checkout, then emits schema-backed evidence artifacts.

## Status

As of May 1, 2026, this project is an alpha MVP. It is suitable for local source inspection, contract export, validation, and CI-backed development against synthetic fixtures. It is not yet suitable for production robotics operation, hardware claims, controller evaluation, policy training, video capture, or public release automation. Known limitations: local-checkout-only source assets, no MuJoCo viewer command, no screenshot/capture flow, no UI, no automatic upstream download, and no compiled-physics validation. Breaking changes before `1.0` are possible.

## Why It Exists

The upstream Asimov v1 release contains useful MuJoCo assets, but raw XML and mesh files are hard to audit, diff, validate, and reuse safely. This repo turns that local source checkout into explicit contracts: asset manifests, model inspection JSON, validation results, Markdown reports, and JSON Schemas that future UI/report layers can trust.

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

Exit codes:

- `0`: command succeeded, including warnings-only validation
- `1`: validation failed or XML contract parsing failed
- `2`: invalid CLI usage or invalid output path
- `3`: missing or unsupported source layout

## Contracts

JSON artifacts are the source of truth. Text and Markdown are renderings.

- `docs/schemas/asset-manifest.schema.json`
- `docs/schemas/doctor-result.schema.json`
- `docs/schemas/error-result.schema.json`
- `docs/schemas/inspect-result.schema.json`
- `docs/schemas/validation-result.schema.json`

The inspect contract currently exports model name, bodies, joints, actuators, sensors, mesh assets, concrete geoms, cameras, sites, declared XML mass totals, passive-joint inference, and typed warnings. The validator checks supported source layout, mesh files, geom mesh references, actuator targets, sensor targets, joint ranges, and built-in or local TOML presets.

## Architecture

Core modules live in `src/asimov_sim_lab/`:

- `paths.py`: asset-root resolution, supported-layout checks, Git provenance
- `manifest.py`: checksummed source manifest generation
- `inspect.py`: MJCF parsing and inspect-contract extraction
- `validation.py`: reference, range, sensor, actuator, and preset validation
- `presets.py`: built-in neutral preset and local TOML preset validation
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

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md), [docs/spec/PRODUCT-SPEC.md](docs/spec/PRODUCT-SPEC.md), and [AGENTS.md](AGENTS.md). Keep changes contract-first: update code, tests, generated schemas, and docs together. Do not add viewer, capture, controller, policy, or UI surfaces without a contract and tests.

## Roadmap

Next three milestones:

- **M1: Alpha contract hardening.** Exit criteria: all public contract fields documented, schema drift enforced in CI, strict warning policy complete, optional real-upstream smoke documented.
- **M2: Evidence bundle.** Exit criteria: one command emits a reproducible local evidence directory with manifest, inspect result, validation result, Markdown summary, and checksums.
- **M3: Viewer contract preview.** Exit criteria: MuJoCo viewer support lives behind the `viewer` extra, loads only validated local assets, and has a typed failure model before any screenshot/capture command ships.

## Help

Use GitHub issues for bugs, feature proposals, and documentation gaps. Include the command, exit code, JSON output when available, asset-root layout, and whether the source checkout was dirty.
