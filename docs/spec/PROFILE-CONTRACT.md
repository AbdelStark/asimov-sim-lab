# PROFILE-CONTRACT — Asimov Sim Lab

## Why profiles exist
The repo needs a clean way to separate operator-specific local paths from stable repo logic.

A profile is not a source of product truth. It is a local execution/config shim.

## Default profile path
- `.asimov-sim-lab/profile.toml`

## Profile scope
Profiles may define:
- default upstream asset root
- default output directory
- viewer preferences
- capture defaults
- validation strictness defaults

Profiles may not redefine:
- result schema versions
- supported upstream layout contract
- built-in error codes

## Profile model
```toml
schema_version = "0.1.0"
name = "local-dev"
default_asset_root = "/absolute/path/to/asimov-v1"
default_output_dir = "reports"
strict_validation = true

[viewer]
autostart = false
camera = "front"
width = 1600
height = 900

[capture]
default_pose = "neutral"
image_format = "png"
```

## Validation rules
- profile files must be explicit TOML
- `default_asset_root` must be an absolute path
- `default_output_dir` may be relative to the repo root
- unknown top-level keys should fail validation in strict mode
- profile parsing errors must point to the exact field when possible

## Precedence order
1. explicit CLI flags
2. explicit profile values
3. `ASIMOV_SIM_LAB_ASSET_ROOT`
4. typed error with remediation

When `--profile` is omitted, `.asimov-sim-lab/profile.toml` is loaded if it exists. The live `.asimov-sim-lab/` directory is ignored local state and must not be committed.

## First-cut implementation posture
The initial runnable slice only needs to support:
- loading a profile if present
- reading `default_asset_root`
- reading `strict_validation`
- ignoring viewer/capture sections unless the command needs them
- no profile writing
- stdlib `tomllib` only

## Failure codes tied to profiles
- `PROFILE_NOT_FOUND`
- `PROFILE_PARSE_FAILED`
- `PROFILE_SCHEMA_MISMATCH`
- `PROFILE_INVALID_PATH`
- `PROFILE_UNKNOWN_FIELD`

## Non-goals
- per-user cloud sync
- environment inheritance magic that makes runs non-reproducible
- hidden auto-generated profiles at install time
