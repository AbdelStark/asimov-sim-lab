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
- `ViewerOpenResult.validation_passed` now reflects the actual `validate_model` outcome instead of being forced to `false` whenever any gate (`VIEWER_SOURCE_DIRTY`, `VIEWER_LICENSE_MISSING`, `VIEWER_PRESET_NOT_FOUND`) blocks preflight; consumers can now distinguish "model is invalid" from "model is valid but a non-validation gate failed".
- `<mesh file="X.STL"/>` elements without an explicit `name` attribute now default to the file stem (`"X"`) in both inspect and validation views, matching MuJoCo's own naming convention; previously the inspect contract used `mesh_0`/`mesh_1`/... while validation silently dropped the entry, so any geom that referenced the mesh by its MuJoCo-implied name would falsely trip `MESH_ASSET_REFERENCE_UNKNOWN`.
- `open` preflight no longer parses the MJCF twice; the orphaned `inspect_model` call before `validate_model` (which itself runs inspect) was removed.
- Git provenance no longer runs `git status --untracked-files=all` (which walks the entire worktree under a 2s subprocess timeout, silently returning a "clean" tree on timeout). Dirty detection uses `git status --untracked-files=no` and untracked count uses `git ls-files --others --exclude-standard`; both are index-aware and cheap. A new strict warning `SOURCE_GIT_QUERY_FAILED` surfaces partial failures (timeout, locked index) so callers can distinguish "clean" from "unknown" instead of getting a silent false negative.
- Non-UTF-8 profile TOML files now raise a typed `PROFILE_PARSE_FAILED` with a clear remediation instead of an uncaught `UnicodeDecodeError` traceback.

### Changed

- Internal: `_parse_xml` was duplicated verbatim across `inspect.py` and `validation.py`. Extracted to a private `asimov_sim_lab._xml.parse_mjcf` so the two modules cannot drift on error codes or remediation strings.
- Orchestrator commands (`evidence`, `export`, `open`) now share a single internal `PipelineContext` so the asset manifest and MJCF parse run exactly once per invocation instead of 4–5 times. On the real Asimov-v1 humanoid (28 STL files), `evidence` drops from ~566 ms to ~184 ms (**3.08× faster**); `export` benefits proportionally. Output bytes are byte-identical to the prior implementation (`archive_sha256`, `evidence_bundle_sha256`, and `package_manifest_sha256` are unchanged for the same input). The public function signatures gain an optional `context=` kwarg; existing callers that don't pass it keep working unchanged. See `docs/rfcs/RFC-0009-pipeline-context.md`.

### Known Limitations

- Only local upstream checkouts are supported.
- No interactive MuJoCo viewer launch, capture, screenshot, video, or UI surface is implemented.
- No controller, policy-training, hardware-fidelity, manufacturing, or electrical-safety claims are made.
- Optional real-upstream smoke requires `ASIMOV_SIM_LAB_ASSET_ROOT`; CI uses synthetic fixtures only.
- Runtime smoke compiles the MJCF when MuJoCo is installed, but it does not step simulation or validate controller behavior.
