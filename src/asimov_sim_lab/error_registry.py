"""Public diagnostic code registry.

Every code emitted by the CLI or Python API is registered here. The registry
is part of the operator contract: tests, runbooks, release evidence, and
external tooling may branch on these codes.

Adding, removing, or renaming a code requires updating this module in the same
commit as the producer change. Coverage is enforced by
``scripts/check_error_registry.py``.

Severity semantics:

* ``error`` — the command cannot complete the requested contract.
* ``warning`` — the command completed but the evidence is lower quality.
* ``strict_warning`` — promoted to ``error`` under ``--strict`` or profile
  ``strict_validation = true``.
* ``conditional`` — surface chooses error or warning at emission time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

Severity = Literal["error", "warning", "strict_warning", "conditional"]


@dataclass(frozen=True, slots=True)
class ErrorCodeEntry:
    code: str
    severity: Severity
    owner: str
    surface: str
    meaning: str
    remediation: str


_ENTRIES: tuple[ErrorCodeEntry, ...] = (
    ErrorCodeEntry(
        "ACTUATOR_JOINT_REFERENCE_MISSING",
        "error",
        "validation.py",
        "validate",
        "An actuator targets a joint that is not present in the inspect contract.",
        "Fix the actuator `joint` attribute or add the referenced joint.",
    ),
    ErrorCodeEntry(
        "ACTUATOR_TARGET_MISSING",
        "warning",
        "validation.py",
        "validate",
        "An actuator has no target reference understood by the MVP validator.",
        "Extend validator support or use a supported actuator target shape.",
    ),
    ErrorCodeEntry(
        "ASSET_ROOT_NOT_FOUND",
        "error",
        "paths.py",
        "all source commands",
        "No asset root was provided, the path does not exist, or the path is not a directory.",
        "Pass `--asset-root`, set `ASIMOV_SIM_LAB_ASSET_ROOT`, or configure a profile"
        " with an absolute checkout root.",
    ),
    ErrorCodeEntry(
        "BODY_MASS_NOT_DECLARED",
        "warning",
        "inspect.py",
        "inspect, validate, evidence, export",
        "No inertial mass declarations were found in the MJCF.",
        "Add MJCF inertial mass declarations if mass summaries are expected.",
    ),
    ErrorCodeEntry(
        "CHECKSUM_COMPUTE_FAILED",
        "error",
        "artifacts.py",
        "artifact generation",
        "A file could not be read while computing SHA-256.",
        "Check file permissions and regenerate the artifact.",
    ),
    ErrorCodeEntry(
        "EVIDENCE_OUTPUT_NOT_DIRECTORY",
        "error",
        "evidence.py",
        "evidence",
        "Evidence output path exists but is not a directory.",
        "Pass a directory path for `--output-dir`.",
    ),
    ErrorCodeEntry(
        "EVIDENCE_OUTPUT_NOT_EMPTY",
        "error",
        "evidence.py",
        "evidence",
        "Evidence output directory is non-empty without explicit overwrite.",
        "Use an empty directory or pass `--overwrite`.",
    ),
    ErrorCodeEntry(
        "EXPORT_ARCHIVE_INPUT_FAILED",
        "error",
        "export.py",
        "export",
        "A generated package file could not be read while building the archive.",
        "Regenerate evidence and retry export.",
    ),
    ErrorCodeEntry(
        "EXPORT_ARCHIVE_WRITE_FAILED",
        "error",
        "export.py",
        "export",
        "The deterministic export archive could not be written atomically.",
        "Check output directory permissions and disk space.",
    ),
    ErrorCodeEntry(
        "EXPORT_OUTPUT_NOT_DIRECTORY",
        "error",
        "export.py",
        "export",
        "Export output path exists but is not a directory.",
        "Pass a directory path for `--output-dir`.",
    ),
    ErrorCodeEntry(
        "EXPORT_OUTPUT_NOT_EMPTY",
        "error",
        "export.py",
        "export",
        "Export output directory is non-empty without explicit overwrite.",
        "Use an empty directory or pass `--overwrite`.",
    ),
    ErrorCodeEntry(
        "EXPORT_PACKAGE_NAME_INVALID",
        "error",
        "export.py",
        "export",
        "Export package name is not safe as a file-name stem.",
        "Use only letters, numbers, dots, underscores, and hyphens.",
    ),
    ErrorCodeEntry(
        "JOINT_RANGE_INVALID",
        "error",
        "validation.py",
        "validate",
        "A limited joint has an invalid or incomplete range declaration.",
        "Fix the MJCF joint `range` declaration.",
    ),
    ErrorCodeEntry(
        "JOINT_RANGE_MISSING",
        "warning",
        "validation.py",
        "validate",
        "A hinge or slide joint has no finite range.",
        "Add a finite range when the joint should be preset-targetable or bounded.",
    ),
    ErrorCodeEntry(
        "MANIFEST_WARNING",
        "warning",
        "doctor.py",
        "doctor",
        "Defensive fallback for manifest warnings without code prefixes.",
        "Preserve code-prefixed warnings in manifest producers.",
    ),
    ErrorCodeEntry(
        "MESHDIR_MISSING",
        "strict_warning",
        "inspect.py",
        "inspect, validate, evidence, export",
        "`compiler@meshdir` is missing and the supported default mesh directory was used.",
        'Add `compiler meshdir="../assets/meshes"` or run with `--strict` to reject it.',
    ),
    ErrorCodeEntry(
        "MESH_ASSET_REFERENCE_UNKNOWN",
        "error",
        "validation.py",
        "validate",
        "A geom references a mesh asset that is not declared in MJCF `<asset>`.",
        "Declare the mesh in `<asset>` or fix the geom reference.",
    ),
    ErrorCodeEntry(
        "MESH_DIRECTORY_NOT_FOUND",
        "error",
        "paths.py",
        "doctor, manifest generation",
        "The supported mesh directory is missing.",
        "Restore `sim-model/assets/meshes`.",
    ),
    ErrorCodeEntry(
        "MESH_REFERENCE_MISSING",
        "conditional",
        "inspect.py, validation.py",
        "inspect, validate",
        "MJCF references a mesh file that does not exist.",
        "Add the missing STL or fix the mesh file reference.",
    ),
    ErrorCodeEntry(
        "MUJOCO_MODEL_LOAD_FAILED",
        "error",
        "runtime.py",
        "runtime-smoke, evidence, export",
        "MuJoCo was available but could not compile the canonical MJCF.",
        "Fix MJCF, compiler paths, or referenced assets.",
    ),
    ErrorCodeEntry(
        "MUJOCO_NOT_INSTALLED",
        "conditional",
        "runtime.py",
        "runtime-smoke, evidence, export",
        "Optional MuJoCo runtime is unavailable.",
        "Install the `viewer` extra, or omit `--require-mujoco` when runtime"
        " compilation is optional.",
    ),
    ErrorCodeEntry(
        "OUTPUT_PATH_IS_DIRECTORY",
        "error",
        "artifacts.py",
        "file outputs",
        "A file output path points at a directory.",
        "Pass a file path for `--output` or `--manifest-output`.",
    ),
    ErrorCodeEntry(
        "OUTPUT_WRITE_FAILED",
        "error",
        "artifacts.py",
        "file outputs",
        "The command could not create, write, or atomically replace an output file.",
        "Check permissions and disk space.",
    ),
    ErrorCodeEntry(
        "PRESET_DIRECTORY_NOT_FOUND",
        "error",
        "presets.py",
        "validate --preset-dir",
        "Preset directory does not exist or is not a directory.",
        "Pass an existing preset directory.",
    ),
    ErrorCodeEntry(
        "PRESET_FILENAME_MISMATCH",
        "warning",
        "presets.py",
        "validate --preset-dir",
        "Preset TOML file name does not match the slugified preset name.",
        "Rename the file to match the preset name.",
    ),
    ErrorCodeEntry(
        "PRESET_JOINT_RANGE_MISSING",
        "error",
        "presets.py",
        "validate --preset-dir",
        "A preset targets a joint without a finite range.",
        "Add a finite joint range or remove the preset entry.",
    ),
    ErrorCodeEntry(
        "PRESET_JOINT_UNKNOWN",
        "error",
        "presets.py",
        "validate --preset-dir",
        "A preset references an unknown joint.",
        "Fix the joint name or remove the entry.",
    ),
    ErrorCodeEntry(
        "PRESET_NEUTRAL_VALUE_OMITTED",
        "warning",
        "presets.py",
        "validate",
        "Built-in neutral preset could not infer a safe value for a finite-range joint.",
        "Add/refine joint refs or inspect the omission.",
    ),
    ErrorCodeEntry(
        "PRESET_PARSE_FAILED",
        "error",
        "presets.py",
        "validate --preset-dir",
        "A preset TOML file could not be read, parsed, or validated.",
        "Fix TOML syntax and preset schema fields.",
    ),
    ErrorCodeEntry(
        "PRESET_VALUE_NOT_FINITE",
        "error",
        "presets.py",
        "validate --preset-dir",
        "A preset value is NaN or infinite.",
        "Replace it with a finite numeric value.",
    ),
    ErrorCodeEntry(
        "PRESET_VALUE_OUT_OF_RANGE",
        "error",
        "presets.py",
        "validate --preset-dir",
        "A preset value lies outside the joint range.",
        "Clamp or correct the preset value.",
    ),
    ErrorCodeEntry(
        "PRIMARY_XML_NOT_FOUND",
        "error",
        "paths.py, inspect.py, validation.py",
        "source commands",
        "The canonical MJCF entrypoint is missing or unreadable.",
        "Restore `sim-model/xmls/asimov.xml` or pass the correct checkout root.",
    ),
    ErrorCodeEntry(
        "PROFILE_INVALID_PATH",
        "error",
        "config.py",
        "profile loading",
        "Profile field validation failed, usually because a configured path is not absolute.",
        "Fix profile path values.",
    ),
    ErrorCodeEntry(
        "PROFILE_NOT_FOUND",
        "error",
        "config.py",
        "profile loading",
        "Explicit `--profile` path does not exist.",
        "Pass an existing profile path or omit `--profile`.",
    ),
    ErrorCodeEntry(
        "PROFILE_PARSE_FAILED",
        "error",
        "config.py",
        "profile loading",
        "Profile TOML could not be parsed or read.",
        "Fix TOML syntax or file permissions.",
    ),
    ErrorCodeEntry(
        "PROFILE_UNKNOWN_FIELD",
        "strict_warning",
        "config.py",
        "profile loading",
        "Profile contains unknown top-level fields.",
        "Remove unknown profile fields.",
    ),
    ErrorCodeEntry(
        "PROFILE_WARNING",
        "warning",
        "doctor.py",
        "doctor",
        "Defensive fallback for profile warnings without code prefixes.",
        "Preserve code-prefixed warnings in profile loading.",
    ),
    ErrorCodeEntry(
        "SENSOR_REFERENCE_MISSING",
        "error",
        "validation.py",
        "validate",
        "A sensor references an unknown body, joint, site, camera, or geom.",
        "Fix the sensor reference or add the target object.",
    ),
    ErrorCodeEntry(
        "SENSOR_TARGET_TYPE_UNSUPPORTED",
        "warning",
        "validation.py",
        "validate",
        "A sensor uses an unsupported `objtype`; target validation was skipped.",
        "Extend validator support or use a supported object type.",
    ),
    ErrorCodeEntry(
        "SIM_MODEL_README_NOT_FOUND",
        "strict_warning",
        "paths.py",
        "doctor, manifest generation",
        "Optional `sim-model/README.md` is missing.",
        "Restore upstream source documentation when publishing evidence.",
    ),
    ErrorCodeEntry(
        "SOURCE_DIRTY",
        "strict_warning",
        "paths.py",
        "provenance",
        "Source checkout has uncommitted or untracked files.",
        "Commit, stash, or explicitly accept dirty-source evidence.",
    ),
    ErrorCodeEntry(
        "SOURCE_GIT_QUERY_FAILED",
        "strict_warning",
        "paths.py",
        "provenance",
        "A Git provenance sub-query (dirty state or untracked count) returned no"
        " result, so the corresponding field is null.",
        "Investigate the Git environment (timeout, permissions, locked index) and rerun.",
    ),
    ErrorCodeEntry(
        "SOURCE_NOT_GIT",
        "strict_warning",
        "paths.py",
        "provenance",
        "Source root is not a Git checkout.",
        "Use a Git checkout when provenance matters.",
    ),
    ErrorCodeEntry(
        "SOURCE_NOT_GIT_ROOT",
        "strict_warning",
        "paths.py",
        "provenance",
        "Asset root is inside a Git worktree but is not the worktree root.",
        "Pass the checkout root that contains `sim-model/`.",
    ),
    ErrorCodeEntry(
        "SOURCE_WARNING",
        "warning",
        "doctor.py",
        "doctor",
        "Defensive fallback for provenance warnings without code prefixes.",
        "Preserve code-prefixed warnings in provenance readers.",
    ),
    ErrorCodeEntry(
        "UNSUPPORTED_SOURCE_LAYOUT",
        "error",
        "inspect.py, manifest.py",
        "inspect, manifest generation",
        "Source layout does not match the MVP contract, including unsupported `compiler@meshdir`.",
        "Keep MJCF assets under `sim-model/assets/meshes`.",
    ),
    ErrorCodeEntry(
        "UPSTREAM_LICENSE_NOT_FOUND",
        "strict_warning",
        "paths.py",
        "doctor, manifest generation",
        "No recognized license file exists at the upstream checkout root.",
        "Add or point at a checkout with a license file before public evidence release.",
    ),
    ErrorCodeEntry(
        "VIEWER_EXTRA_NOT_INSTALLED",
        "error",
        "viewer.py",
        "open",
        "Viewer preflight requires MuJoCo but the optional viewer runtime is not installed.",
        "Run `uv sync --extra viewer` before using viewer preflight/open workflows.",
    ),
    ErrorCodeEntry(
        "VIEWER_LAUNCH_FAILED",
        "error",
        "viewer.py",
        "open",
        "Viewer preflight reached MuJoCo but runtime model loading failed.",
        "Fix MJCF/runtime errors before opening the viewer.",
    ),
    ErrorCodeEntry(
        "VIEWER_LICENSE_MISSING",
        "error",
        "viewer.py",
        "open --require-license",
        "Viewer preflight requires an upstream root license but none was found.",
        "Add a license file or rerun with `--allow-missing-license`.",
    ),
    ErrorCodeEntry(
        "VIEWER_PRESET_NOT_FOUND",
        "error",
        "viewer.py",
        "open --preset",
        "Requested viewer preset is not built in and was not found in the local preset directory.",
        "Use `--preset neutral` or pass a preset directory containing the requested preset.",
    ),
    ErrorCodeEntry(
        "VIEWER_SOURCE_DIRTY",
        "error",
        "viewer.py",
        "open --require-clean-source",
        "Viewer preflight requires clean source provenance but the checkout is dirty.",
        "Commit, stash, or rerun with `--allow-dirty-source`.",
    ),
    ErrorCodeEntry(
        "VIEWER_VALIDATION_FAILED",
        "error",
        "viewer.py",
        "open",
        "Source validation failed before the viewer could be opened.",
        "Fix validation errors before opening the viewer.",
    ),
    ErrorCodeEntry(
        "WARNING",
        "warning",
        "validation.py",
        "validate",
        "Defensive fallback for warning strings without code prefixes.",
        "Preserve code-prefixed warning messages in producers.",
    ),
    ErrorCodeEntry(
        "XML_BOOLEAN_PARSE_FAILED",
        "error",
        "inspect.py",
        "inspect, validate",
        "A boolean MJCF attribute is not one of `true`, `false`, `1`, or `0`.",
        "Fix the MJCF boolean value.",
    ),
    ErrorCodeEntry(
        "XML_NUMERIC_PARSE_FAILED",
        "error",
        "inspect.py",
        "inspect, validate",
        "A numeric MJCF attribute cannot be parsed or has the wrong arity.",
        "Fix numeric MJCF attributes.",
    ),
    ErrorCodeEntry(
        "XML_PARSE_FAILED",
        "conditional",
        "inspect.py, manifest.py, validation.py",
        "inspect, manifest, validate",
        "Primary XML is malformed, or manifest could not derive mesh-reference provenance.",
        "Fix XML syntax before trusting generated contracts.",
    ),
)


def _build_registry() -> dict[str, ErrorCodeEntry]:
    registry: dict[str, ErrorCodeEntry] = {}
    for entry in _ENTRIES:
        if entry.code in registry:
            raise RuntimeError(f"duplicate error code entry: {entry.code}")
        registry[entry.code] = entry
    return registry


ERROR_CODES: Final[dict[str, ErrorCodeEntry]] = _build_registry()

HELP_URL: Final[str] = (
    "https://github.com/AbdelStark/asimov-sim-lab"
    "/blob/main/src/asimov_sim_lab/error_registry.py"
)
