# IMPLEMENTATION-PLAN — Asimov Sim Lab

## Implementation posture
Contract-first. Keep the first runnable slice narrow, deterministic where possible, and deeply tied to the real upstream source assets.

## Work packages
1. Lock source asset sync/provenance rules.
2. Define machine-readable internal schemas.
3. Implement parser/ingestion layer.
4. Implement validation layer and error taxonomy.
5. Implement one CLI or report path that proves the core value loop.
6. Add evidence artifacts and CI.
7. Only then add richer UI/viewer/product polish.

## Must-have repo invariants
- all generated outputs carry source provenance
- validation failures are actionable and typed
- tests cover broken fixtures as well as happy paths
- README never outruns shipped reality

## Likely first files to implement
- `src/asimov_sim_lab/cli.py`
- `src/asimov_sim_lab/models.py`
- `src/asimov_sim_lab/parser.py`
- `src/asimov_sim_lab/validation.py`
- `tests/test_smoke.py`
- feature-specific fixtures under `fixtures/`
