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
11. Enforced diagnostic-code registry and release-candidate evidence verifier.
12. Viewer/open RFC defining the required preflight contract before implementation.
13. Preflight-only `open` command with `ViewerOpenResult`, viewer-specific errors, tests, and schema.
14. Release-candidate dry-run report generation from a verified real-upstream export package.
15. JSON-mode domain errors linking back to the public diagnostic-code registry.

## Current module ownership

- `config.py`: local profile loading and profile warnings.
- `paths.py`: source-root resolution, supported-layout checks, Git metadata.
- `manifest.py`: asset manifest checksums and mesh reference provenance.
- `models.py`: public contracts and schema version.
- `inspect.py`: XML parsing and model contract extraction.
- `validation.py`: validation issue generation.
- `presets.py`: built-in neutral preset and local preset validation.
- `runtime.py`: optional MuJoCo runtime smoke checks.
- `viewer.py`: preflight-only viewer/open readiness checks.
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
- `open` must remain preflight-only until interactive GUI lifecycle, shutdown, and failure behavior are specified and tested
- emitted diagnostic codes must be registered and mechanically checked
- release-candidate export packages must pass `scripts/check_release_evidence.py`

## Next implementation sequence

1. Add a publication-safe evidence review guide for release attachments and absolute-path provenance.
2. Add alpha schema compatibility policy and tests that make accidental schema-version drift visible.
3. Design the interactive viewer launch extension using current `open` preflight telemetry; do not implement GUI launch until lifecycle semantics are accepted.

## Implementation decisions

The detailed decision log lives in `docs/spec/MVP-DECISION-LOG.md`. That file is part of the implementation contract, not background reading.
