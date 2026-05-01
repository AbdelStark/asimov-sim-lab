# Asimov Sim Lab

A spec-first MuJoCo inspection and validation workbench for the Asimov v1 simulation model.

## Status

Private incubation repo. The MVP core is CLI-first and contract-first: local asset discovery, manifest generation, MJCF inspection, validation, generated JSON Schemas, and synthetic fixture tests.

## Thesis

Turn the public Asimov v1 MuJoCo release into a serious developer-facing inspection, validation, and capture tool before any controller or policy work begins.

## Why this repo exists

The upstream Asimov release already contains technically valuable source material, but the raw release is still too awkward for fast inspection, validation, and reuse. This repo turns that source material into a more legible builder/developer artifact without pretending to replace the upstream repository.

## Current build posture

- modern `uv`-managed Python project
- spec-first / RFC-first execution with executable contracts
- local-checkout-only source asset strategy
- generated JSON Schemas for public result artifacts
- emphasis on reproducibility, provenance, and validation
- no inflated claims about hardware fidelity, manufacturing completeness, or electrical safety
- no controller, policy-training, UI, viewer, screenshot, or capture implementation in the MVP

## MVP architecture

- Python core package in `src/asimov_sim_lab`
- contracts and RFCs in `docs/spec/` and `docs/rfcs/`
- generated JSON Schemas in `docs/schemas/`
- tests in `tests/`
- optional secondary UI surfaces only after the core data contracts are stable

## Source of truth

Read these first:

1. `docs/spec/PRODUCT-SPEC.md`
2. `docs/spec/IMPLEMENTATION-PLAN.md`
3. `docs/spec/MVP-STATUS.md`
4. `docs/spec/MVP-DECISION-LOG.md`
5. `docs/spec/MANIFEST-CONTRACT.md`
6. `docs/spec/RESULT-SCHEMA-CONTRACT.md`
7. `docs/spec/CLI-COMMAND-SPEC.md`
8. `docs/spec/PROFILE-CONTRACT.md`
9. `docs/spec/FIRST-THREE-SCENARIOS-BUILD-PACK.md`
10. `docs/rfcs/README.md`

## Initial commands

```bash
uv sync --extra dev
uv run asimov-sim-lab doctor --asset-root /path/to/asimov-v1 --format json
uv run asimov-sim-lab inspect --asset-root /path/to/asimov-v1 --json
uv run asimov-sim-lab validate --asset-root /path/to/asimov-v1 --format json
uv run ruff check .
uv run mypy
uv run pytest
```

## Local profile

The MVP never downloads or vendors upstream assets. Pass `--asset-root`, set
`ASIMOV_SIM_LAB_ASSET_ROOT`, or create an ignored local profile at
`.asimov-sim-lab/profile.toml`.

## Deferred

- `open`
- `capture`
- local UI or web report viewer
- controller examples
- policy training
- hardware fidelity or manufacturing claims
