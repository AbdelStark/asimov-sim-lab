# RFC-0007: CI, Release, and Quality Gates

## Abstract
Even in a private incubation repo, quality gates should be explicit from day one.

## Required checks
- `uv run pytest`
- `uv run ruff check .`
- import/package smoke path
- schema/fixture validation where available

## Release posture
No public release until the README, contracts, and actual implementation reality match.
