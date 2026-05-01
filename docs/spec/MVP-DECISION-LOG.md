# MVP-DECISION-LOG — Asimov Sim Lab

This file records the locked MVP decisions that turn the RFC package into an executable implementation contract.

## Scope

- The MVP contains no controller, policy, policy-training, RL, imitation-learning, or ML benchmark work.
- "SOTA ML open source" is the quality bar: typed contracts, reproducible artifacts, rigorous tests, schemas, CI, packaging, and honest documentation.
- The product is an external companion tool for a local Asimov v1 checkout, not an official replacement for upstream.
- No upstream XML or mesh assets are vendored.
- No hardware fidelity, manufacturing readiness, electrical safety, or policy performance claims are made.

## Source Assets

- `--asset-root` means the upstream checkout root that contains `sim-model/`.
- Passing `sim-model/` directly is unsupported and should fail with a typed layout error.
- The MVP supports local checkout mode only.
- No auto-download, hidden sibling search, or network-dependent CI path is allowed.
- Asset root precedence is:
  1. `--asset-root`
  2. `--profile default_asset_root`
  3. `ASIMOV_SIM_LAB_ASSET_ROOT`
  4. typed error with remediation
- `.asimov-sim-lab/profile.toml` loads by default if present; explicit `--profile` must exist.
- `.asimov-sim-lab/` is ignored local state.

## Provenance

- Git metadata is recorded opportunistically when the asset root is a Git worktree root.
- Dirty or unpinned sources warn by default and fail under `--strict`.
- Generated artifacts use source-root-relative paths for asset entries.
- Absolute asset roots are local diagnostics only and must not be committed in examples or snapshots.
- Upstream license discovery is warning-only by default and strict-escalatable.

## Manifest

- Commands generate a fresh in-memory manifest each run.
- Persisted manifests are evidence artifacts only; there is no `--manifest-input` in MVP.
- The manifest hashes the primary XML and every discovered STL mesh in the supported mesh directory.
- Unreferenced mesh files are valid inventory, not validation errors.
- Missing required layout files fail; missing `sim-model/README.md` warns by default.

## Inspection

- `inspect` uses standard XML parsing, not MuJoCo, for the core contract.
- Only concrete model elements count; MJCF defaults/templates are excluded from exported counts.
- `passive` means no actuator targets the joint.
- `floating_base` is passive but distinguished with `joint_type="free"`.
- Cameras and sites are included in JSON with minimal fields.
- Concrete geoms are included so sensor `objtype="geom"` references validate against geom names, not mesh asset names.
- Detailed inertia export is deferred; `total_declared_mass_kg` is allowed as a declared-XML summary.
- Actuators are parsed generically from direct children of `<actuator>`.
- Sensor entries include enough target metadata to validate references.
- Malformed XML fails loudly; no partial inspect contract is emitted.

## Validation

- Validation derives joint limits and references from the current XML every run.
- `validate` owns failure semantics for reference integrity.
- `inspect` may warn about missing mesh references but does not replace `validate`.
- Mesh resolution uses `compiler@meshdir` when present; unsupported mesh directories fail with `UNSUPPORTED_SOURCE_LAYOUT`.
- Malformed numeric and boolean MJCF attributes fail contract extraction rather than serializing as `null`.
- Hinge/slide ranges are required when limited or preset-targetable; missing non-limited ranges warn.
- Validation issue codes are flat uppercase strings with domain prefixes.
- `--strict` applies across commands and escalates defined evidence-quality warnings, not harmless inventory.

## Presets

- Presets are TOML only.
- Local presets are one file per preset under a preset directory.
- The package ships only an inferred built-in `neutral` preset in MVP.
- Neutral uses `joint@ref` when valid, then `0.0` when valid, otherwise omits the joint with a warning.
- Local presets are optional via `--preset-dir`.

## CLI

- Supported commands are `doctor`, `inspect`, and `validate`.
- `open` and `capture` are omitted until they have real behavior, tests, and contracts.
- JSON artifacts are the source of truth; text and Markdown are renderings.
- Markdown is supported for `inspect` only.
- `doctor` and `validate` support `--format text|json`.
- `inspect` supports `--json`, `--markdown`, and `--format text|json|markdown`; conflicting flags exit `2`.
- `--output` and `--manifest-output` create parent directories and write atomically.
- JSON mode emits structured domain failures when possible.
- CLI misuse and internal crashes remain stderr-first.

## Tests And Gates

- CI uses committed synthetic fixtures only.
- Real upstream smoke tests are optional and gated by `ASIMOV_SIM_LAB_ASSET_ROOT`.
- Fixtures mimic the supported Asimov layout and tiny Asimov-like names without copying upstream assets.
- Mesh fixtures use tiny valid synthetic ASCII STL files.
- MVP supports Python `>=3.12`; CI targets Python 3.12 and 3.13.
- Coverage applies to `src/asimov_sim_lab` with an initial 90% floor.
- Generated JSON Schemas are committed and checked for drift on every PR.
- Public Python API is narrow: Pydantic models plus pure core functions.
- `tomllib` is the only TOML dependency in MVP.
- MuJoCo is optional under the `viewer` extra and is not used by core commands.
