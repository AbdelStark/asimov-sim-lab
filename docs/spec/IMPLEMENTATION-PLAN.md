# IMPLEMENTATION-PLAN — Asimov Sim Lab

## Implementation posture

Contract-first. The MVP core is now implemented, so future work should harden contracts, evidence, and operator workflows before adding product surface.

## Completed MVP work packages

1. Asset-root resolution and manifest generation.
2. MJCF inspection export.
3. Validation engine and preset checks.
4. Generated and committed JSON Schemas from the Pydantic contracts.
5. CI, Makefile, pre-commit, coverage, schema drift, build, and dependency audit gates.
6. Optional real-upstream smoke gated by `ASIMOV_SIM_LAB_ASSET_ROOT`.
7. Evidence bundle generation with checksummed manifest, inspect, validation, runtime-smoke, and Markdown artifacts.
8. Optional MuJoCo runtime-smoke command with explicit skipped/missing dependency semantics.
9. Deterministic export package generation with portable bundle paths and archive checksums.
10. CI fixture evidence/export generation with retained workflow artifacts.

## Current module ownership

- `config.py`: local profile loading and profile warnings.
- `paths.py`: source-root resolution, supported-layout checks, Git metadata.
- `manifest.py`: asset manifest checksums and mesh reference provenance.
- `models.py`: public contracts and schema version.
- `inspect.py`: XML parsing and model contract extraction.
- `validation.py`: validation issue generation.
- `presets.py`: built-in neutral preset and local preset validation.
- `runtime.py`: optional MuJoCo runtime smoke checks.
- `artifacts.py`: atomic writes and checksum helpers.
- `evidence.py`: evidence bundle generation.
- `export.py`: deterministic export package generation.
- `doctor.py`: layout/provenance/manifest health checks.
- `cli.py`: command surface, output formats, atomic writes.
- `scripts/generate_schemas.py`: schema generation.

## Must-have repo invariants

- all generated outputs carry source provenance
- validation failures are actionable and typed
- tests cover broken fixtures as well as happy paths
- README never outruns shipped reality
- JSON contracts remain the source of truth for future UI layers
- schema changes are committed only with the code and tests that justify them
- evidence bundles must list checksums for every generated review artifact
- deterministic export archives must not embed local output-directory paths
- runtime smoke must stay dependency-gated and must not become a viewer, simulation, or controller claim

## Next implementation sequence

1. Complete alpha contract hardening: public field docs, error-code registry, and stricter schema-version checks.
2. Add a publication-safe evidence review guide and error-code registry.
3. Add a release-candidate evidence policy that says which bundle/export artifacts must be attached before tagging.
4. Design the viewer/open contract as an RFC before adding interactive MuJoCo surfaces.

## Implementation decisions

The detailed decision log lives in `docs/spec/MVP-DECISION-LOG.md`. That file is part of the implementation contract, not background reading.
