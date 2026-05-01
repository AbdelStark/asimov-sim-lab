# RFC-0008: Viewer/Open Contract

## Status

Draft. This RFC defines the gate for adding an interactive MuJoCo viewer/open surface. It does not authorize implementation yet.

## Abstract

`runtime-smoke` proves that the optional MuJoCo Python package can compile the canonical MJCF. The next tempting feature is an `open` command that launches an interactive viewer. That command must not ship as an ad hoc demo. It needs a contract that protects source provenance, avoids false robotics claims, and keeps optional runtime dependencies out of the default install.

## Motivation

Users will eventually want a quick way to inspect the robot visually. A viewer command is useful only if it is clearly bounded:

- it opens a validated local checkout
- it does not mutate source assets
- it does not imply controller quality, simulation fidelity, policy performance, or hardware readiness
- it reports runtime failures as typed diagnostics
- it remains optional behind the `viewer` extra

## Proposed Command Shape

```bash
asimov-sim-lab open \
  --asset-root /absolute/path/to/asimov-v1 \
  --require-clean-source \
  --preset neutral
```

Initial options:

- `--asset-root PATH`: same precedence and semantics as existing commands
- `--profile PATH`: same local profile support as existing commands
- `--preset NAME`: optional pose preset name; default `neutral`
- `--preset-dir PATH`: optional local preset directory
- `--require-clean-source / --allow-dirty-source`: fail if provenance warnings include `SOURCE_DIRTY`
- `--require-license / --allow-missing-license`: fail if `UPSTREAM_LICENSE_NOT_FOUND`
- `--format text|json`: emit a typed preflight/open result before launching, or skip launch in JSON-only mode if needed

The command name is intentionally `open`, not `simulate`, `run`, or `play`.

## Preconditions

Before a viewer window opens, the command must complete:

1. asset-root resolution
2. layout checks
3. manifest generation
4. inspect contract extraction
5. validation
6. runtime smoke with MuJoCo required
7. preset validation when a preset is requested

Any error-severity issue blocks opening.

## Result Contract

The implementation must introduce a schema-backed result before shipping:

```python
class ViewerOpenResult(ResultEnvelope):
    command: Literal["open"] = "open"
    runtime: Literal["mujoco"] = "mujoco"
    runtime_version: str
    xml_path: str
    preset_name: str | None
    validation_passed: bool
    runtime_smoke_status: Status
    opened: bool
    launch_mode: Literal["interactive", "preflight_only"]
```

The result must be generated before any interactive viewer launch. If JSON mode cannot safely launch a viewer without corrupting stdout, JSON mode should be preflight-only.

## New Failure Codes To Reserve

These codes are reserved for implementation, but must not be added to the enforced registry until source emits them:

- `VIEWER_EXTRA_NOT_INSTALLED`
- `VIEWER_VALIDATION_FAILED`
- `VIEWER_PRESET_NOT_FOUND`
- `VIEWER_SOURCE_DIRTY`
- `VIEWER_LICENSE_MISSING`
- `VIEWER_LAUNCH_FAILED`

## Non-Goals

- no screenshot or video capture
- no simulation stepping contract beyond what MuJoCo viewer performs internally
- no controller loading
- no policy inference
- no benchmark scoring
- no hardware, safety, manufacturing, or physical-fidelity claims
- no automatic upstream download

## Dependency Policy

MuJoCo remains optional:

```bash
uv sync --extra viewer
```

The default package install must continue to support `doctor`, `inspect`, `validate`, `runtime-smoke` skipped mode, `evidence`, and `export` without MuJoCo installed.

## Test Requirements

Implementation cannot merge without:

- unit tests for preflight failure mapping
- CLI tests for `--format json` preflight output
- tests proving missing MuJoCo fails with a typed viewer/runtime error
- tests proving validation errors block launch
- tests proving dirty-source policy is enforced when required
- schema generation and schema validation tests for `ViewerOpenResult`

Interactive GUI launch may remain manually smoke-tested, but the preflight contract must be automated.

## Documentation Requirements

Before shipping `open`, update:

- README status and command examples
- `CLI-COMMAND-SPEC.md`
- `RESULT-SCHEMA-CONTRACT.md`
- `ERROR-CODE-REGISTRY.md`
- `AGENTS.md`
- `CHANGELOG.md`

Docs must say exactly what `open` proves: local viewer launch only.

## Exit Criteria

The viewer/open slice is ready when:

- the command is behind the `viewer` extra
- preflight is schema-backed and tested
- all failure modes are typed
- JSON mode is non-interactive or stdout-safe
- local source provenance remains visible
- no docs imply simulation, controller, policy, hardware, safety, or manufacturing readiness
