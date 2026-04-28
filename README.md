# Asimov Sim Lab

A spec-first MuJoCo inspection and validation workbench for the Asimov v1 simulation model.

## Status

Spec-first private incubation repo. The current phase is contract hardening, not feature sprawl.

## Thesis

Turn the public Asimov v1 MuJoCo release into a serious developer-facing inspection, validation, and capture tool before any controller or policy work begins.

## Why this repo exists

The upstream Asimov release already contains technically valuable source material, but the raw release is still too awkward for fast inspection, validation, and reuse. This repo turns that source material into a more legible builder/developer artifact without pretending to replace the upstream repository.

## Current build posture

- modern `uv`-managed Python project
- spec-first / RFC-first execution
- clean package scaffold for future implementation
- emphasis on reproducibility, provenance, and validation
- no inflated claims about hardware fidelity, manufacturing completeness, or electrical safety

## Planned architecture

- Python core package in `src/asimov_sim_lab`
- contracts and RFCs in `docs/spec/` and `docs/rfcs/`
- tests in `tests/`
- optional secondary UI surfaces only after the core data contracts are stable

## Source of truth for phase 1

Read these first:

1. `docs/spec/PRODUCT-SPEC.md`
2. `docs/spec/IMPLEMENTATION-PLAN.md`
3. `docs/spec/MVP-STATUS.md`
4. `docs/rfcs/README.md`

## Initial commands

```bash
uv sync
uv run pytest
uv run ruff check .
```

## Immediate next milestone

Lock contracts and fixtures before writing real product logic.
