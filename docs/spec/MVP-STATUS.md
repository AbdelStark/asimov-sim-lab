# MVP-STATUS — Asimov Sim Lab

## Current state
- phase: phase 3 runnable core implementation
- repo: created
- remote: configured
- local clone: present
- uv scaffold: present
- contracts: locked for the first implementation pass
- implementation: core MVP in progress

## What is already real
- private GitHub repo exists
- README and spec package exist
- RFC backlog exists
- package/test scaffold exists
- deeper contracts now exist for manifest, result schemas, CLI semantics, profile handling, and first work packs
- core modules now map those contracts to executable Python surfaces
- synthetic source-root fixtures cover happy and broken paths
- JSON Schema generation is part of the local/CI contract

## What is intentionally not real yet
- no real upstream sync implementation
- no polished demo UI
- no public release posture
- no MuJoCo viewer/open command
- no screenshot/capture command
- no controller or policy-training path

## Exit criteria for implementation start
- all critical contracts reviewed
- source asset strategy pinned
- first fixture pack selected
- first smoke workflow defined

## Next implementation target
Finish the MVP core:
- validate schema generation and drift checks
- run full local quality gates
- run optional real-upstream smoke when `ASIMOV_SIM_LAB_ASSET_ROOT` is available
- keep README and docs aligned with shipped behavior
