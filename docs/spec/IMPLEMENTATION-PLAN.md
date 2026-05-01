# IMPLEMENTATION-PLAN — Asimov Sim Lab

## Implementation posture
Contract-first. Keep the first runnable slice narrow, deterministic where possible, and deeply tied to the real upstream source assets.

## Current sequencing
Phase 1 established the repo, scaffold, and RFC package.

Phase 2 locked the pre-coding contracts that would otherwise drift:
1. manifest contract
2. result schema contract
3. CLI command spec
4. profile contract
5. first three implementation work packs

Phase 3 should now execute against those contracts rather than redesigning them mid-flight.

## Work packages
1. Implement asset-root resolution and manifest generation.
2. Implement MJCF inspection export.
3. Implement validation engine and preset checks.
4. Generate and commit JSON Schemas from the Pydantic contracts.
5. Add CI, Makefile, pre-commit, coverage, schema drift, build, and lightweight security gates.
6. Add optional real-upstream smoke gated by `ASIMOV_SIM_LAB_ASSET_ROOT`.
7. Only then consider viewer/open/capture or richer UI/product polish.

## Must-have repo invariants
- all generated outputs carry source provenance
- validation failures are actionable and typed
- tests cover broken fixtures as well as happy paths
- README never outruns shipped reality
- JSON contracts remain the source of truth for future UI layers

## Likely first files to implement
- `src/asimov_sim_lab/config.py`
- `src/asimov_sim_lab/paths.py`
- `src/asimov_sim_lab/manifest.py`
- `src/asimov_sim_lab/models.py`
- `src/asimov_sim_lab/inspect.py`
- `src/asimov_sim_lab/validation.py`
- `src/asimov_sim_lab/presets.py`
- `src/asimov_sim_lab/doctor.py`
- `scripts/generate_schemas.py`
- `tests/test_doctor.py`
- `tests/test_inspect.py`
- `tests/test_validation.py`
- `tests/test_schemas.py`
- feature-specific fixtures under `tests/fixtures/`

## Implementation decisions

The detailed decision log lives in `docs/spec/MVP-DECISION-LOG.md`. That file is part of the implementation contract, not background reading.
