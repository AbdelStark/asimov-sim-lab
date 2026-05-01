# ERROR-CODE-REGISTRY — Asimov Sim Lab

## Purpose

Every public diagnostic code emitted by the CLI or Python API is tracked here. Codes are part of the operator contract: tests, runbooks, release evidence, and future UI/report surfaces may branch on them.

JSON-mode recoverable domain errors include `help_url: "docs/spec/ERROR-CODE-REGISTRY.md"` so automation and future UI layers can link diagnostics back to this registry.

This registry is enforced by:

```bash
uv run python scripts/check_error_registry.py --check
```

## Semantics

- **Error** means the command cannot complete the requested contract or validation failed.
- **Warning** means the command completed but the evidence is lower quality, incomplete, or environment-dependent.
- **Strict** warnings are promoted to errors when `--strict` or profile `strict_validation = true` applies.
- Strict-warning codes currently include `MESHDIR_MISSING`, `PROFILE_UNKNOWN_FIELD`, `SIM_MODEL_README_NOT_FOUND`, `SOURCE_DIRTY`, `SOURCE_NOT_GIT`, `SOURCE_NOT_GIT_ROOT`, and `UPSTREAM_LICENSE_NOT_FOUND`.
- Fallback warning codes exist only for defensive normalization when a warning string lacks a code prefix.

## Registry

| Code | Severity | Owner | Surface | Meaning | Remediation |
| --- | --- | --- | --- | --- | --- |
| `ACTUATOR_JOINT_REFERENCE_MISSING` | Error | `validation.py` | `validate` | An actuator targets a joint that is not present in the inspect contract. | Fix the actuator `joint` attribute or add the referenced joint. |
| `ACTUATOR_TARGET_MISSING` | Warning | `validation.py` | `validate` | An actuator has no target reference understood by the MVP validator. | Extend validator support or use a supported actuator target shape. |
| `ASSET_ROOT_NOT_FOUND` | Error | `paths.py` | all source commands | No asset root was provided, the path does not exist, or the path is not a directory. | Pass `--asset-root`, set `ASIMOV_SIM_LAB_ASSET_ROOT`, or configure a profile with an absolute checkout root. |
| `BODY_MASS_NOT_DECLARED` | Warning | `inspect.py` | `inspect`, `validate`, `evidence`, `export` | No inertial mass declarations were found in the MJCF. | Add MJCF inertial mass declarations if mass summaries are expected. |
| `CHECKSUM_COMPUTE_FAILED` | Error | `artifacts.py` | artifact generation | A file could not be read while computing SHA-256. | Check file permissions and regenerate the artifact. |
| `EVIDENCE_OUTPUT_NOT_DIRECTORY` | Error | `evidence.py` | `evidence` | Evidence output path exists but is not a directory. | Pass a directory path for `--output-dir`. |
| `EVIDENCE_OUTPUT_NOT_EMPTY` | Error | `evidence.py` | `evidence` | Evidence output directory is non-empty without explicit overwrite. | Use an empty directory or pass `--overwrite`. |
| `EXPORT_ARCHIVE_INPUT_FAILED` | Error | `export.py` | `export` | A generated package file could not be read while building the archive. | Regenerate evidence and retry export. |
| `EXPORT_ARCHIVE_WRITE_FAILED` | Error | `export.py` | `export` | The deterministic export archive could not be written atomically. | Check output directory permissions and disk space. |
| `EXPORT_OUTPUT_NOT_DIRECTORY` | Error | `export.py` | `export` | Export output path exists but is not a directory. | Pass a directory path for `--output-dir`. |
| `EXPORT_OUTPUT_NOT_EMPTY` | Error | `export.py` | `export` | Export output directory is non-empty without explicit overwrite. | Use an empty directory or pass `--overwrite`. |
| `EXPORT_PACKAGE_NAME_INVALID` | Error | `export.py` | `export` | Export package name is not safe as a file-name stem. | Use only letters, numbers, dots, underscores, and hyphens. |
| `JOINT_RANGE_INVALID` | Error | `validation.py` | `validate` | A limited joint has an invalid or incomplete range declaration. | Fix the MJCF joint `range` declaration. |
| `JOINT_RANGE_MISSING` | Warning | `validation.py` | `validate` | A hinge or slide joint has no finite range. | Add a finite range when the joint should be preset-targetable or bounded. |
| `MANIFEST_WARNING` | Warning | `doctor.py` | `doctor` | Defensive fallback for manifest warnings without code prefixes. | Preserve code-prefixed warnings in manifest producers. |
| `MESHDIR_MISSING` | Strict warning | `inspect.py` | `inspect`, `validate`, `evidence`, `export` | `compiler@meshdir` is missing and the supported default mesh directory was used. | Add `compiler meshdir="../assets/meshes"` or run with `--strict` to reject it. |
| `MESH_ASSET_REFERENCE_UNKNOWN` | Error | `validation.py` | `validate` | A geom references a mesh asset that is not declared in MJCF `<asset>`. | Declare the mesh in `<asset>` or fix the geom reference. |
| `MESH_DIRECTORY_NOT_FOUND` | Error | `paths.py` | `doctor`, manifest generation | The supported mesh directory is missing. | Restore `sim-model/assets/meshes`. |
| `MESH_REFERENCE_MISSING` | Error or warning | `inspect.py`, `validation.py` | `inspect`, `validate` | MJCF references a mesh file that does not exist. | Add the missing STL or fix the mesh file reference. |
| `MUJOCO_MODEL_LOAD_FAILED` | Error | `runtime.py` | `runtime-smoke`, `evidence`, `export` | MuJoCo was available but could not compile the canonical MJCF. | Fix MJCF, compiler paths, or referenced assets. |
| `MUJOCO_NOT_INSTALLED` | Warning or error | `runtime.py` | `runtime-smoke`, `evidence`, `export` | Optional MuJoCo runtime is unavailable. | Install the `viewer` extra, or omit `--require-mujoco` when runtime compilation is optional. |
| `OUTPUT_PATH_IS_DIRECTORY` | Error | `artifacts.py` | file outputs | A file output path points at a directory. | Pass a file path for `--output` or `--manifest-output`. |
| `OUTPUT_WRITE_FAILED` | Error | `artifacts.py` | file outputs | The command could not create, write, or atomically replace an output file. | Check permissions and disk space. |
| `PRESET_DIRECTORY_NOT_FOUND` | Error | `presets.py` | `validate --preset-dir` | Preset directory does not exist or is not a directory. | Pass an existing preset directory. |
| `PRESET_FILENAME_MISMATCH` | Warning | `presets.py` | `validate --preset-dir` | Preset TOML file name does not match the slugified preset name. | Rename the file to match the preset name. |
| `PRESET_JOINT_RANGE_MISSING` | Error | `presets.py` | `validate --preset-dir` | A preset targets a joint without a finite range. | Add a finite joint range or remove the preset entry. |
| `PRESET_JOINT_UNKNOWN` | Error | `presets.py` | `validate --preset-dir` | A preset references an unknown joint. | Fix the joint name or remove the entry. |
| `PRESET_NEUTRAL_VALUE_OMITTED` | Warning | `presets.py` | `validate` | Built-in neutral preset could not infer a safe value for a finite-range joint. | Add/refine joint refs or inspect the omission. |
| `PRESET_PARSE_FAILED` | Error | `presets.py` | `validate --preset-dir` | A preset TOML file could not be read, parsed, or validated. | Fix TOML syntax and preset schema fields. |
| `PRESET_VALUE_NOT_FINITE` | Error | `presets.py` | `validate --preset-dir` | A preset value is NaN or infinite. | Replace it with a finite numeric value. |
| `PRESET_VALUE_OUT_OF_RANGE` | Error | `presets.py` | `validate --preset-dir` | A preset value lies outside the joint range. | Clamp or correct the preset value. |
| `PRIMARY_XML_NOT_FOUND` | Error | `paths.py`, `inspect.py`, `validation.py` | source commands | The canonical MJCF entrypoint is missing or unreadable. | Restore `sim-model/xmls/asimov.xml` or pass the correct checkout root. |
| `PROFILE_INVALID_PATH` | Error | `config.py` | profile loading | Profile field validation failed, usually because a configured path is not absolute. | Fix profile path values. |
| `PROFILE_NOT_FOUND` | Error | `config.py` | profile loading | Explicit `--profile` path does not exist. | Pass an existing profile path or omit `--profile`. |
| `PROFILE_PARSE_FAILED` | Error | `config.py` | profile loading | Profile TOML could not be parsed or read. | Fix TOML syntax or file permissions. |
| `PROFILE_UNKNOWN_FIELD` | Strict warning | `config.py` | profile loading | Profile contains unknown top-level fields. | Remove unknown profile fields. |
| `PROFILE_WARNING` | Warning | `doctor.py` | `doctor` | Defensive fallback for profile warnings without code prefixes. | Preserve code-prefixed warnings in profile loading. |
| `SENSOR_REFERENCE_MISSING` | Error | `validation.py` | `validate` | A sensor references an unknown body, joint, site, camera, or geom. | Fix the sensor reference or add the target object. |
| `SENSOR_TARGET_TYPE_UNSUPPORTED` | Warning | `validation.py` | `validate` | A sensor uses an unsupported `objtype`; target validation was skipped. | Extend validator support or use a supported object type. |
| `SIM_MODEL_README_NOT_FOUND` | Strict warning | `paths.py` | `doctor`, manifest generation | Optional `sim-model/README.md` is missing. | Restore upstream source documentation when publishing evidence. |
| `SOURCE_DIRTY` | Strict warning | `paths.py` | provenance | Source checkout has uncommitted or untracked files. | Commit, stash, or explicitly accept dirty-source evidence. |
| `SOURCE_NOT_GIT` | Strict warning | `paths.py` | provenance | Source root is not a Git checkout. | Use a Git checkout when provenance matters. |
| `SOURCE_NOT_GIT_ROOT` | Strict warning | `paths.py` | provenance | Asset root is inside a Git worktree but is not the worktree root. | Pass the checkout root that contains `sim-model/`. |
| `SOURCE_WARNING` | Warning | `doctor.py` | `doctor` | Defensive fallback for provenance warnings without code prefixes. | Preserve code-prefixed warnings in provenance readers. |
| `UNSUPPORTED_SOURCE_LAYOUT` | Error | `inspect.py`, `manifest.py` | inspect/manifest generation | Source layout does not match the MVP contract, including unsupported `compiler@meshdir`. | Keep MJCF assets under `sim-model/assets/meshes`. |
| `UPSTREAM_LICENSE_NOT_FOUND` | Strict warning | `paths.py` | `doctor`, manifest generation | No recognized license file exists at the upstream checkout root. | Add or point at a checkout with a license file before public evidence release. |
| `VIEWER_EXTRA_NOT_INSTALLED` | Error | `viewer.py` | `open` | Viewer preflight requires MuJoCo but the optional viewer runtime is not installed. | Run `uv sync --extra viewer` before using viewer preflight/open workflows. |
| `VIEWER_LAUNCH_FAILED` | Error | `viewer.py` | `open` | Viewer preflight reached MuJoCo but runtime model loading failed. | Fix MJCF/runtime errors before opening the viewer. |
| `VIEWER_LICENSE_MISSING` | Error | `viewer.py` | `open --require-license` | Viewer preflight requires an upstream root license but none was found. | Add a license file or rerun with `--allow-missing-license`. |
| `VIEWER_PRESET_NOT_FOUND` | Error | `viewer.py` | `open --preset` | Requested viewer preset is not built in and was not found in the local preset directory. | Use `--preset neutral` or pass a preset directory containing the requested preset. |
| `VIEWER_SOURCE_DIRTY` | Error | `viewer.py` | `open --require-clean-source` | Viewer preflight requires clean source provenance but the checkout is dirty. | Commit, stash, or rerun with `--allow-dirty-source`. |
| `VIEWER_VALIDATION_FAILED` | Error | `viewer.py` | `open` | Source validation failed before the viewer could be opened. | Fix validation errors before opening the viewer. |
| `WARNING` | Warning | `validation.py` | `validate` | Defensive fallback for warning strings without code prefixes. | Preserve code-prefixed warning messages in producers. |
| `XML_BOOLEAN_PARSE_FAILED` | Error | `inspect.py` | `inspect`, `validate` | A boolean MJCF attribute is not one of `true`, `false`, `1`, or `0`. | Fix the MJCF boolean value. |
| `XML_NUMERIC_PARSE_FAILED` | Error | `inspect.py` | `inspect`, `validate` | A numeric MJCF attribute cannot be parsed or has the wrong arity. | Fix numeric MJCF attributes. |
| `XML_PARSE_FAILED` | Error or strict warning | `inspect.py`, `manifest.py`, `validation.py` | inspect/manifest/validate | Primary XML is malformed, or manifest could not derive mesh-reference provenance. | Fix XML syntax before trusting generated contracts. |

## Change Control

Adding, removing, or renaming a code requires:

1. Update the producer and tests that exercise the behavior.
2. Update this registry in the same commit.
3. Run `uv run python scripts/check_error_registry.py --check`.
4. Update operator docs if exit behavior or remediation changed.
