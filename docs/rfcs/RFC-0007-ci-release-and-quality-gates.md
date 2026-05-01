# RFC-0007: CI, Release, and Quality Gates

## Abstract
Even in a private incubation repo, quality gates should be explicit from day one.

## Required checks
- `uv lock --check`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy`
- `uv run pytest`
- `uv run python scripts/generate_schemas.py --check`
- `uv build`
- lightweight dependency audit
- fixture-backed evidence and export package generation
- CI upload of `.asimov-sim-lab/ci-evidence/` and `.asimov-sim-lab/ci-export/` as retained artifacts
- optional real-upstream smoke only when `ASIMOV_SIM_LAB_ASSET_ROOT` is set

## Release posture
No public release until the README, contracts, and actual implementation reality match.

Release candidates should attach the deterministic export archive and `export-package-result.json` produced from the same source checkout used for validation.
