# CLI-COMMAND-SPEC — Asimov Sim Lab

## CLI posture
The CLI is the first serious operator surface. It must be scriptable, predictable, and boring in the best way.

## Supported command set for the first real slice
```bash
asimov-sim-lab doctor
asimov-sim-lab inspect
asimov-sim-lab inspect --json
asimov-sim-lab inspect --markdown
asimov-sim-lab validate
asimov-sim-lab runtime-smoke
asimov-sim-lab open
asimov-sim-lab evidence
asimov-sim-lab export
```

## Global rules
- stdout is reserved for primary command output.
- stderr is reserved for operator-facing errors and progress notices.
- JSON mode writes machine-readable payloads only.
- non-zero exit codes indicate command failure or failed validation.
- path arguments must be explicit; no hidden cwd magic beyond documented defaults.

## Shared options
```text
--asset-root PATH         Explicit upstream asset root
--profile PATH            Optional lab profile file
--output PATH             File output path for JSON/Markdown artifacts
--manifest-output PATH    Optional persisted asset-manifest path
--output-dir PATH         Artifact directory for `evidence` or `export`
--format [text|json]      When supported by the command
--strict / --no-strict    Escalate warnings into failures where applicable
--preset NAME             Viewer or validation preset where supported
--preset-dir PATH         Directory of local TOML presets where supported
--overwrite / --no-overwrite
```

Asset-root precedence:
1. explicit `--asset-root`
2. explicit or default profile `default_asset_root`
3. `ASIMOV_SIM_LAB_ASSET_ROOT`
4. typed error

There is no sibling auto-discovery in MVP.

## `doctor`
Purpose:
- verify package wiring
- verify asset-root discovery
- verify that the supported upstream layout exists
- emit a concise health summary

Expected behavior:
- succeeds even if optional future features are absent
- fails if the primary XML cannot be located
- supports `--format json`
- `--output` writes the `DoctorResult`
- `--manifest-output` writes the persisted asset manifest when requested

Example:
```bash
asimov-sim-lab doctor --asset-root /path/to/asimov-v1 --format json --manifest-output .asimov-sim-lab/asset-manifest.json
```

## `inspect`
Purpose:
- parse the canonical MJCF entrypoint
- produce a stable model contract summary
- optionally export JSON or Markdown report artifacts

Expected behavior:
- text mode prints a concise summary table
- `--json` emits `InspectResult`
- `--markdown` emits a deterministic markdown report derived from the JSON contract
- if `--output` is absent in JSON/Markdown mode, write to stdout

Examples:
```bash
asimov-sim-lab inspect --asset-root /path/to/asimov-v1
asimov-sim-lab inspect --json --output reports/model-contract.json
asimov-sim-lab inspect --markdown --output reports/model-contract.md
```

## `validate`
Purpose:
- verify references and contract integrity before a viewer is opened or a report is trusted

Validation scope for the first cut:
- primary XML exists
- mesh references resolve
- geom mesh references resolve
- actuator joint references resolve
- sensor references resolve when applicable
- malformed numeric/boolean MJCF attributes fail contract extraction
- preset pose files, when present, only reference known joints and legal ranges

Expected behavior:
- exit `0` on pass or warnings-only
- exit non-zero if any error-severity issues exist
- `--format json` emits `ValidationResult`

Example:
```bash
asimov-sim-lab validate --asset-root /path/to/asimov-v1 --format json
asimov-sim-lab validate --asset-root /path/to/asimov-v1 --preset-dir ./presets --format json
```

## `evidence`
Purpose:
- produce one reviewable artifact directory for source provenance, model inspection, validation, runtime smoke, and Markdown summary
- make every artifact checksum explicit
- keep local generated evidence under an operator-chosen directory

Expected behavior:
- requires `--output-dir`
- refuses non-empty output directories unless `--overwrite` is passed
- writes `asset-manifest.json`, `inspect-result.json`, `validation-result.json`, `runtime-smoke-result.json`, `inspect-report.md`, and `evidence-bundle.json`
- exits `0` when validation passes, including warnings-only validation
- exits non-zero when validation produces error-severity issues
- `--format json` emits `EvidenceBundleResult`

Example:
```bash
asimov-sim-lab evidence --asset-root /path/to/asimov-v1 --output-dir .asimov-sim-lab/evidence --overwrite --format json
```

## `runtime-smoke`
Purpose:
- verify that the optional MuJoCo Python runtime can compile the canonical MJCF
- expose runtime availability as a typed result instead of an implicit import failure

Expected behavior:
- exits `0` with `status=warning` and `skipped=true` when MuJoCo is missing by default
- exits non-zero with `MUJOCO_NOT_INSTALLED` when `--require-mujoco` is passed and MuJoCo is missing
- exits non-zero with `MUJOCO_MODEL_LOAD_FAILED` when MuJoCo is installed but cannot compile the XML
- `--format json` emits `RuntimeSmokeResult`
- does not open a viewer, step simulation, evaluate controllers, or make hardware-fidelity claims

Example:
```bash
asimov-sim-lab runtime-smoke --asset-root /path/to/asimov-v1 --allow-missing-mujoco --format json
asimov-sim-lab runtime-smoke --asset-root /path/to/asimov-v1 --require-mujoco --format json
```

## `open`
Purpose:
- run the viewer/open preflight contract before any interactive launch exists
- verify source validation, requested preset availability, optional provenance gates, and MuJoCo compile readiness
- expose viewer readiness as `ViewerOpenResult` instead of an ad hoc demo script

Expected behavior:
- never opens an interactive viewer in the alpha implementation
- always emits `opened=false` and `launch_mode=preflight_only`
- exits non-zero when validation has error-severity issues
- exits non-zero with `VIEWER_EXTRA_NOT_INSTALLED` when MuJoCo is missing
- exits non-zero with `VIEWER_LAUNCH_FAILED` when MuJoCo is installed but cannot compile the XML
- exits non-zero with viewer-specific errors for missing presets, dirty source when required, or missing upstream license when required
- `--format json` emits `ViewerOpenResult`
- does not step simulation, capture media, evaluate controllers, or make hardware-fidelity claims

Example:
```bash
asimov-sim-lab open --asset-root /path/to/asimov-v1 --format json
asimov-sim-lab open --asset-root /path/to/asimov-v1 --preset neutral --require-clean-source --format json
```

## `export`
Purpose:
- generate a portable evidence directory and deterministic `tar.gz` archive for review or CI retention
- link archive checksums to the generated evidence bundle
- avoid embedding local output-directory paths inside archive contents

Expected behavior:
- requires `--output-dir`
- refuses non-empty output directories unless `--overwrite` is passed
- writes `evidence/`, `export-package-manifest.json`, `export-package-result.json`, and `<package-name>.tar.gz`
- normalizes generated timestamps and archive metadata by default
- validates `--package-name` as a safe file-name stem
- `--format json` emits `ExportPackageResult`

Example:
```bash
asimov-sim-lab export --asset-root /path/to/asimov-v1 --output-dir .asimov-sim-lab/export --overwrite --format json
```

## Deferred commands
These are intentionally named now but not promised in this phase:
- `capture`
- `preset validate`
- `preset list`

The CLI should omit deferred commands until they have real behavior, tests, and contracts.

Interactive viewer launch remains deferred. `open` is currently limited to the schema-backed preflight slice defined by `docs/rfcs/RFC-0008-viewer-open-contract.md`.

## Exit codes
- `0`: success, including warnings-only validation
- `1`: validation failed or XML contract extraction failed
- `2`: command misuse / invalid CLI arguments
- `3`: unsupported upstream layout or missing required source assets
- `4`: internal unhandled tool failure

## Test obligations
The first implementation must cover:
- `doctor` smoke success
- `inspect --json` shape
- `validate --format json` pass/fail semantics
- one broken fixture path per major validation error family
- viewer/open preflight success with a fake MuJoCo module
- viewer/open missing MuJoCo, validation failure, unknown preset, and provenance-gate failures
- generated `ViewerOpenResult` schema validation
- conflicting format flags exit `2`
- JSON-mode domain failures emit structured error results
