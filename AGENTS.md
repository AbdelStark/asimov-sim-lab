# AGENTS — Asimov Sim Lab

This file is the short operational context for AI agents and new contributors working in this repository.

## Project Identity

Asimov Sim Lab is a Python CLI and library that inspects and validates a local Asimov v1 MuJoCo checkout and emits schema-backed evidence artifacts.

## Current State

- Stage: alpha MVP.
- Shipped commands: `doctor`, `inspect`, `validate`, `runtime-smoke`, `evidence`, `export`.
- Source strategy: local checkout only. No automatic download and no vendored upstream assets.
- Public contracts: Pydantic models in `src/asimov_sim_lab/models.py` and generated JSON Schemas in `docs/schemas/`.
- Deferred: viewer/open, capture/screenshot/video, UI, controllers, policy training, hardware or manufacturing claims.

## Architecture Map

- `src/asimov_sim_lab/cli.py`: Typer CLI, output modes, atomic file writes.
- `src/asimov_sim_lab/config.py`: local TOML profile loading.
- `src/asimov_sim_lab/paths.py`: asset-root resolution, source-layout checks, Git provenance.
- `src/asimov_sim_lab/manifest.py`: source manifest and checksum generation.
- `src/asimov_sim_lab/inspect.py`: MJCF parsing and inspect-contract extraction.
- `src/asimov_sim_lab/validation.py`: validation issue generation.
- `src/asimov_sim_lab/presets.py`: built-in neutral preset and local preset validation.
- `src/asimov_sim_lab/runtime.py`: optional MuJoCo compiled-runtime smoke checks.
- `src/asimov_sim_lab/evidence.py`: checksummed evidence bundle generation.
- `src/asimov_sim_lab/export.py`: deterministic export package generation.
- `src/asimov_sim_lab/artifacts.py`: atomic artifact writes and SHA-256 helpers.
- `src/asimov_sim_lab/models.py`: public result contracts.
- `scripts/generate_schemas.py`: schema generation from public contracts.
- `tests/fixtures/`: hermetic synthetic source roots.

## Tech Stack

- Python `>=3.12`
- `uv`
- Typer CLI
- Pydantic v2 contracts
- Ruff lint/format
- mypy strict mode
- pytest with branch coverage
- pip-audit for dependency vulnerability checks

## Commands

Install:

```bash
uv sync --extra dev
```

Quality gate:

```bash
make check
```

Expanded gate:

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

Manual CLI smoke:

```bash
uv run asimov-sim-lab doctor --asset-root /absolute/path/to/asimov-v1 --format json
uv run asimov-sim-lab inspect --asset-root /absolute/path/to/asimov-v1 --json
uv run asimov-sim-lab validate --asset-root /absolute/path/to/asimov-v1 --format json
uv run asimov-sim-lab runtime-smoke --asset-root /absolute/path/to/asimov-v1 --allow-missing-mujoco --format json
uv run asimov-sim-lab evidence --asset-root /absolute/path/to/asimov-v1 --output-dir .asimov-sim-lab/evidence --overwrite --format json
uv run asimov-sim-lab export --asset-root /absolute/path/to/asimov-v1 --output-dir .asimov-sim-lab/export --overwrite --format json
```

Optional real-upstream smoke:

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make smoke-real
```

## Conventions

- Keep JSON contracts as source of truth. Text and Markdown are renderings.
- Add or update tests for every behavior change.
- Regenerate and commit `docs/schemas/*.schema.json` after public contract changes.
- Use typed `LabError` or `ValidationIssue` codes for recoverable failures.
- Make validation issues actionable with a clear message and remediation when possible.
- Keep local paths and generated evidence out of public docs unless intentionally documented.
- Evidence bundles are review artifacts; inspect `evidence-bundle.json` and local paths before publishing.
- Export packages normalize evidence bundle paths and archive metadata by default; do not add local absolute output paths to archive contents.
- `runtime-smoke` only proves optional MuJoCo model compilation, not simulation correctness, control quality, or hardware fidelity.
- Keep docs aligned with shipped behavior. Do not describe deferred commands as implemented.

## Critical Constraints

- Do not vendor upstream Asimov XML, meshes, or generated reports into this repo.
- Do not add hidden sibling checkout discovery.
- Do not make hardware fidelity, manufacturing, safety, control, or policy-performance claims.
- Do not add viewer, capture, controller, or policy-training surfaces without a spec, tests, and schema-backed contract.
- Do not relax schema drift, mypy, coverage, or lint gates to make a change pass.
- Do not commit `.env` or `.asimov-sim-lab/`.

## Gotchas

- `--asset-root` must point at the upstream checkout root that contains `sim-model/`; passing `sim-model/` itself is unsupported.
- `compiler@meshdir` must resolve to `sim-model/assets/meshes`.
- XML parse failures may still allow `doctor` to report layout/provenance, but `inspect` and `validate` must not emit partial model contracts.
- Sensor `objtype="geom"` references concrete geom names, not mesh asset names.
- `source.root_path` in JSON output is an absolute local diagnostic path. Review generated artifacts before publishing them.
- Fixture source roots are inside this repository and may intentionally produce Git provenance warnings.
