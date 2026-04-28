# Asimov Sim Lab

A spec-first MuJoCo inspection and validation workbench for the Asimov v1 simulation model.

## Status

Private incubation repo. Phase 2 contract hardening is now locked. The next pass should implement the first narrow real value loop rather than inventing more surface area.

## Thesis

Turn the public Asimov v1 MuJoCo release into a serious developer-facing inspection, validation, and capture tool before any controller or policy work begins.

## Why this repo exists

The upstream Asimov release already contains technically valuable source material, but the raw release is still too awkward for fast inspection, validation, and reuse. This repo turns that source material into a more legible builder/developer artifact without pretending to replace the upstream repository.

## Current build posture

- modern `uv`-managed Python project
- spec-first / RFC-first execution
- clean package scaffold for future implementation
- phase 2 contracts locked for manifest, result schemas, CLI semantics, profiles, and first work packs
- emphasis on reproducibility, provenance, and validation
- no inflated claims about hardware fidelity, manufacturing completeness, or electrical safety

## Planned architecture

- Python core package in `src/asimov_sim_lab`
- contracts and RFCs in `docs/spec/` and `docs/rfcs/`
- tests in `tests/`
- optional secondary UI surfaces only after the core data contracts are stable

## Source of truth before implementation

Read these first:

1. `docs/spec/PRODUCT-SPEC.md`
2. `docs/spec/IMPLEMENTATION-PLAN.md`
3. `docs/spec/MVP-STATUS.md`
4. `docs/spec/MANIFEST-CONTRACT.md`
5. `docs/spec/RESULT-SCHEMA-CONTRACT.md`
6. `docs/spec/CLI-COMMAND-SPEC.md`
7. `docs/spec/PROFILE-CONTRACT.md`
8. `docs/spec/FIRST-THREE-SCENARIOS-BUILD-PACK.md`
9. `docs/rfcs/README.md`

## Initial commands

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy
uv run asimov-sim-lab doctor
```

## Immediate next milestone

Implement work pack 1:
- asset-root resolution
- manifest generation
- `doctor --format json`
- tiny synthetic source-root fixtures
