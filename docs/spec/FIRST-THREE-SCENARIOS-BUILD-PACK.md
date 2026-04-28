# FIRST-THREE-SCENARIOS-BUILD-PACK — Asimov Sim Lab

## Intent
Turn the first implementation phase into three narrow, testable work packs instead of one fuzzy "build the tool" sprint.

These are not marketing milestones. They are the first truthful value loops.

## Work pack 1 — Asset discovery + doctor
### Goal
Prove the repo can locate a supported Asimov checkout and emit a manifest-backed health report.

### Required files
- `src/asimov_sim_lab/config.py`
- `src/asimov_sim_lab/paths.py`
- `src/asimov_sim_lab/manifest.py`
- `tests/test_doctor.py`
- `tests/fixtures/source_roots/minimal_valid/`
- `tests/fixtures/source_roots/missing_xml/`

### Must ship
- asset-root resolution from CLI flag or profile
- supported-layout checks for XML, mesh dir, README
- manifest JSON generation in memory plus optional persisted manifest output
- `doctor --format json`

### Verification
- valid fixture returns exit `0`
- missing-xml fixture returns non-zero and typed error code
- doctor JSON contains `resolved_asset_root` and `checks`

## Work pack 2 — MJCF inspection contract export
### Goal
Parse the canonical MJCF entrypoint and emit the first real model contract artifact.

### Required files
- `src/asimov_sim_lab/models.py`
- `src/asimov_sim_lab/inspect.py`
- `tests/test_inspect.py`
- `tests/fixtures/xml/minimal_asimov.xml`

### Must ship
- extract model name
- extract body / joint / actuator / sensor counts
- emit stable JSON contract
- emit deterministic markdown rendering from the same contract

### Verification
- `inspect --json` returns schema-valid output
- markdown export is deterministic for the same fixture
- parser fails loudly on malformed XML

## Work pack 3 — Validation engine for references + presets
### Goal
Make validation a real product surface rather than a TODO comment.

### Required files
- `src/asimov_sim_lab/validation.py`
- `src/asimov_sim_lab/presets.py`
- `tests/test_validation.py`
- `tests/fixtures/source_roots/broken_mesh_ref/`
- `tests/fixtures/source_roots/broken_actuator_ref/`
- `tests/fixtures/presets/`

### Must ship
- typed `ValidationIssue` model
- mesh-reference validation
- actuator-reference validation
- preset joint existence and range validation
- JSON result export with pass/fail semantics

### Verification
- broken mesh fixture emits `MESH_REFERENCE_MISSING`
- broken actuator fixture emits `ACTUATOR_JOINT_REFERENCE_MISSING`
- out-of-range preset emits a preset-specific validation code
- warnings do not masquerade as errors

## Sequence rule
Do not start work pack 2 until work pack 1 produces a usable manifest or equivalent in-memory source contract.

Do not start work pack 3 until work pack 2 exports a stable inspect contract.

## Strong recommendation on fixtures
Keep the first fixtures tiny and synthetic.

The early goal is contract correctness, not proving full upstream compatibility on day one. Real upstream smoke fixtures can be added immediately after the synthetic contract path is stable.

## Exit condition for phase 3 start
When these three work packs are locked, coding can begin without re-arguing repo shape, result schemas, or CLI semantics.
