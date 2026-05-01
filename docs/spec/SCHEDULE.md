# SCHEDULE — Asimov Sim Lab

## Phase 1 — Spec package

Status: complete.

- repo creation
- uv scaffold
- product spec
- implementation plan
- RFC set

## Phase 2 — Contract deepening

Status: complete.

- manifest contract
- result schema contract
- CLI/export contracts
- fixture strategy
- validation taxonomy
- profile contract

## Phase 3 — Runnable core

Status: complete for alpha MVP.

- asset-root resolution
- manifest generation
- inspect contract extraction
- validation commands
- generated JSON Schemas
- synthetic fixture coverage
- CI and local quality gates
- optional real-upstream smoke
- checksummed evidence bundle command
- optional MuJoCo runtime-smoke command
- deterministic export package command
- CI fixture evidence/export artifact retention

## Phase 4 — Alpha hardening

Status: next.

- public field and error-code documentation
- publication-safe evidence review guidance
- release-candidate evidence policy for retained CI artifacts and real-upstream export packages
- stronger schema-version compatibility checks
- dependency and release-readiness review

## Phase 5 — Product surface

Status: deferred until Phase 4 exits.

- MuJoCo viewer/open contract behind the `viewer` extra
- richer exports or graph rendering
- screenshot/capture contract
- report viewer or local UI

## Sequencing note

Do not add Phase 5 surfaces until Phase 4 can prove the core contracts with local and optional real-upstream evidence.
