# Changelog

All notable user-facing changes are recorded here.

## 0.1.0 - Unreleased

### Added

- CLI commands: `doctor`, `inspect`, `validate`, `runtime-smoke`, preflight-only `open`, `evidence`, and `export`.
- Local asset-root resolution through `--asset-root`, profile, or `ASIMOV_SIM_LAB_ASSET_ROOT`.
- Checksummed asset manifest with XML and STL provenance.
- MJCF inspect contract with bodies, joints, actuators, sensors, mesh assets, concrete geoms, cameras, sites, declared XML mass totals, and passive-joint inference.
- Validation for supported layout, mesh file references, geom mesh references, actuator joint references, sensor targets, joint ranges, and presets.
- Generated JSON Schemas for manifest, doctor, inspect, validation, runtime smoke, viewer open preflight, evidence, export, and error results.
- Deterministic Markdown inspect report derived from the JSON contract.
- `runtime-smoke` command that records optional MuJoCo import, MJCF compile success/failure, or explicit skipped state.
- `open` command that emits schema-backed viewer preflight results without launching a GUI.
- `evidence` command that writes a checksummed review bundle with manifest, inspect JSON, validation JSON, runtime-smoke JSON, Markdown report, and bundle index.
- `export` command that writes a deterministic evidence archive, package manifest, and package result with archive checksums.
- CI fixture evidence/export artifact retention for release-review workflows.
- Enforced diagnostic-code registry covering emitted errors and warnings.
- JSON-mode domain errors now include a help URL pointing to the diagnostic-code registry.
- Release-candidate evidence policy, export-package verifier, and sanitized release dry-run report generator.
- Viewer/open RFC implemented for the preflight-only slice.
- Synthetic fixture test suite, coverage gate, schema drift check, build gate, and dependency audit gate.

### Fixed

- Unsupported `compiler@meshdir` layouts now fail with `UNSUPPORTED_SOURCE_LAYOUT` instead of passing validation as a warning.
- Sensor `objtype="geom"` references are validated against concrete geom names instead of mesh asset names.
- Malformed numeric and boolean MJCF attributes now fail contract extraction instead of silently serializing as `null`.
- Manifest generation surfaces XML parse warnings when it cannot derive mesh reference provenance.
- JSON error output no longer recurses when `--output` points at a directory.

### Known Limitations

- Only local upstream checkouts are supported.
- No interactive MuJoCo viewer launch, capture, screenshot, video, or UI surface is implemented.
- No controller, policy-training, hardware-fidelity, manufacturing, or electrical-safety claims are made.
- Optional real-upstream smoke requires `ASIMOV_SIM_LAB_ASSET_ROOT`; CI uses synthetic fixtures only.
- Runtime smoke compiles the MJCF when MuJoCo is installed, but it does not step simulation or validate controller behavior.
