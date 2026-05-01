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
--format [text|json]      When supported by the command
--strict / --no-strict    Escalate warnings into failures where applicable
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
- actuator joint references resolve
- sensor references resolve when applicable
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

## Deferred commands
These are intentionally named now but not promised in this phase:
- `open`
- `capture`
- `preset validate`
- `preset list`

The CLI should omit deferred commands until they have real behavior, tests, and contracts.

## Exit codes
- `0`: success, including warnings-only validation
- `1`: validation failed
- `2`: command misuse / invalid CLI arguments
- `3`: unsupported upstream layout or missing required source assets
- `4`: internal unhandled tool failure

## Test obligations
The first implementation must cover:
- `doctor` smoke success
- `inspect --json` shape
- `validate --format json` pass/fail semantics
- one broken fixture path per major validation error family
- conflicting format flags exit `2`
- JSON-mode domain failures emit structured error results
