"""Typer-based CLI entrypoint.

Wires every subcommand (``doctor``, ``inspect``, ``validate``, ``runtime-smoke``,
``open``, ``evidence``, ``export``) onto the typed library functions in this
package, formats results as text/JSON/Markdown, writes artifacts atomically,
and maps :class:`asimov_sim_lab.errors.LabError` instances to stable exit codes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer

from asimov_sim_lab.artifacts import write_text_atomic
from asimov_sim_lab.doctor import run_doctor
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.evidence import generate_evidence_bundle
from asimov_sim_lab.export import DEFAULT_PACKAGE_NAME, generate_export_package
from asimov_sim_lab.inspect import inspect_model, render_inspect_markdown
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    DoctorResult,
    ErrorResult,
    EvidenceBundleResult,
    ExportPackageResult,
    InspectResult,
    RuntimeSmokeResult,
    Status,
    ValidationIssue,
    ValidationResult,
    ViewerOpenResult,
)
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.runtime import run_runtime_smoke
from asimov_sim_lab.validation import validate_model
from asimov_sim_lab.viewer import DEFAULT_VIEWER_PRESET, run_viewer_open_preflight

app = typer.Typer(
    no_args_is_help=True, help="Inspect and validate a local Asimov v1 MuJoCo checkout."
)

OutputFormat = Literal["text", "json", "markdown"]


@app.callback()
def main() -> None:
    """Asimov Sim Lab command group."""


@app.command()
def doctor(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write primary result artifact.")
    ] = None,
    manifest_output: Annotated[
        Path | None, typer.Option("--manifest-output", help="Write generated asset manifest.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate evidence warnings.")
    ] = False,
) -> None:
    """Verify local source layout and provenance."""
    if output_format not in {"text", "json"}:
        _usage_error("doctor supports --format text|json")
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        effective_strict = strict or bool(
            resolution.profile and resolution.profile.strict_validation
        )
        result, manifest = run_doctor(resolution, strict=effective_strict)
        if manifest_output is not None and manifest is not None:
            _write_text(manifest_output, manifest.model_dump_json(indent=2) + "\n")
            result.source_manifest_path = str(manifest_output)
        payload = result.model_dump_json(indent=2) + "\n"
        if output_format == "json":
            _emit(payload, output)
        else:
            _emit(_doctor_text(result), output)
        raise typer.Exit(_doctor_exit_code(result.status))
    except LabError as exc:
        _handle_error(exc, command="doctor", output_format=output_format, output=output)


@app.command("inspect")
def inspect_command(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write primary result artifact.")
    ] = None,
    manifest_output: Annotated[
        Path | None, typer.Option("--manifest-output", help="Write generated asset manifest.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text, json, or markdown.")
    ] = "text",
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit JSON inspect contract.")
    ] = False,
    markdown: Annotated[
        bool, typer.Option("--markdown", help="Emit Markdown inspect report.")
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate evidence warnings.")
    ] = False,
) -> None:
    """Export the MJCF model contract."""
    resolved_format = _resolve_inspect_format(
        output_format, json_output=json_output, markdown=markdown
    )
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        result = inspect_model(resolution)
        manifest = generate_asset_manifest(resolution)
        if manifest_output is not None:
            _write_text(manifest_output, manifest.model_dump_json(indent=2) + "\n")
            result.source_manifest_path = str(manifest_output)
        if resolved_format == "json":
            payload = result.model_dump_json(indent=2) + "\n"
        elif resolved_format == "markdown":
            payload = render_inspect_markdown(result)
        else:
            payload = _inspect_text(result)
        _emit(payload, output)
        raise typer.Exit(0)
    except LabError as exc:
        _handle_error(exc, command="inspect", output_format=resolved_format, output=output)


@app.command()
def validate(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write primary result artifact.")
    ] = None,
    manifest_output: Annotated[
        Path | None, typer.Option("--manifest-output", help="Write generated asset manifest.")
    ] = None,
    preset_dir: Annotated[
        Path | None, typer.Option("--preset-dir", help="Optional local preset directory.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate evidence warnings.")
    ] = False,
) -> None:
    """Validate source references, joint ranges, sensors, actuators, and presets."""
    if output_format not in {"text", "json"}:
        _usage_error("validate supports --format text|json")
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        effective_strict = strict or bool(
            resolution.profile and resolution.profile.strict_validation
        )
        result = validate_model(resolution, preset_dir=preset_dir, strict=effective_strict)
        manifest = generate_asset_manifest(resolution)
        if manifest_output is not None:
            _write_text(manifest_output, manifest.model_dump_json(indent=2) + "\n")
            result.source_manifest_path = str(manifest_output)
        payload = (
            result.model_dump_json(indent=2) + "\n"
            if output_format == "json"
            else _validation_text(result)
        )
        _emit(payload, output)
        raise typer.Exit(0 if result.passed else 1)
    except LabError as exc:
        _handle_error(exc, command="validate", output_format=output_format, output=output)


@app.command()
def evidence(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help="Directory for evidence artifacts.")
    ] = None,
    preset_dir: Annotated[
        Path | None, typer.Option("--preset-dir", help="Optional local preset directory.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate evidence warnings.")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite/--no-overwrite", help="Replace known bundle artifacts.")
    ] = False,
) -> None:
    """Generate a checksummed evidence bundle directory."""
    if output_format not in {"text", "json"}:
        _usage_error("evidence supports --format text|json")
    if output_dir is None:
        _usage_error("evidence requires --output-dir")
    assert output_dir is not None
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        effective_strict = strict or bool(
            resolution.profile and resolution.profile.strict_validation
        )
        result = generate_evidence_bundle(
            resolution,
            output_dir=output_dir,
            preset_dir=preset_dir,
            strict=effective_strict,
            overwrite=overwrite,
        )
        payload = (
            result.model_dump_json(indent=2) + "\n"
            if output_format == "json"
            else _evidence_text(result)
        )
        _emit(payload, None)
        raise typer.Exit(0 if result.validation_passed else 1)
    except LabError as exc:
        _handle_error(exc, command="evidence", output_format=output_format, output=None)


@app.command("runtime-smoke")
def runtime_smoke(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write primary result artifact.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    require_mujoco: Annotated[
        bool,
        typer.Option(
            "--require-mujoco/--allow-missing-mujoco",
            help="Fail when the optional MuJoCo runtime is not installed.",
        ),
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate source warnings.")
    ] = False,
) -> None:
    """Load the canonical MJCF through the optional MuJoCo runtime."""
    if output_format not in {"text", "json"}:
        _usage_error("runtime-smoke supports --format text|json")
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        result = run_runtime_smoke(resolution, require_mujoco=require_mujoco)
        payload = (
            result.model_dump_json(indent=2) + "\n"
            if output_format == "json"
            else _runtime_smoke_text(result)
        )
        _emit(payload, output)
        raise typer.Exit(0 if result.status != "error" else 1)
    except LabError as exc:
        _handle_error(exc, command="runtime-smoke", output_format=output_format, output=output)


@app.command("open")
def open_command(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write preflight result artifact.")
    ] = None,
    preset_name: Annotated[
        str | None, typer.Option("--preset", help="Viewer preset name.")
    ] = DEFAULT_VIEWER_PRESET,
    preset_dir: Annotated[
        Path | None, typer.Option("--preset-dir", help="Optional local preset directory.")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    require_clean_source: Annotated[
        bool,
        typer.Option(
            "--require-clean-source/--allow-dirty-source",
            help="Fail preflight when the source checkout is dirty.",
        ),
    ] = False,
    require_license: Annotated[
        bool,
        typer.Option(
            "--require-license/--allow-missing-license",
            help="Fail preflight when no upstream root license is found.",
        ),
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate validation warnings.")
    ] = False,
) -> None:
    """Run schema-backed viewer preflight without launching a GUI."""
    if output_format not in {"text", "json"}:
        _usage_error("open supports --format text|json")
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        effective_strict = strict or bool(
            resolution.profile and resolution.profile.strict_validation
        )
        result = run_viewer_open_preflight(
            resolution,
            preset_name=preset_name,
            preset_dir=preset_dir,
            strict=effective_strict,
            require_clean_source=require_clean_source,
            require_license=require_license,
        )
        payload = (
            result.model_dump_json(indent=2) + "\n"
            if output_format == "json"
            else _viewer_open_text(result)
        )
        _emit(payload, output)
        raise typer.Exit(0 if result.status != "error" else 1)
    except LabError as exc:
        _handle_error(exc, command="open", output_format=output_format, output=output)


@app.command("export")
def export_command(
    asset_root: Annotated[
        Path | None, typer.Option("--asset-root", help="Upstream Asimov repo root.")
    ] = None,
    profile: Annotated[
        Path | None, typer.Option("--profile", help="Optional local profile TOML.")
    ] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help="Directory for export package artifacts.")
    ] = None,
    preset_dir: Annotated[
        Path | None, typer.Option("--preset-dir", help="Optional local preset directory.")
    ] = None,
    package_name: Annotated[
        str, typer.Option("--package-name", help="Base file name for the export archive.")
    ] = DEFAULT_PACKAGE_NAME,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
    strict: Annotated[
        bool, typer.Option("--strict/--no-strict", help="Escalate evidence warnings.")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite/--no-overwrite", help="Replace generated artifacts.")
    ] = False,
    deterministic: Annotated[
        bool,
        typer.Option(
            "--deterministic/--no-deterministic",
            help="Normalize timestamps and archive metadata for reproducible package bytes.",
        ),
    ] = True,
) -> None:
    """Generate a deterministic evidence export archive."""
    if output_format not in {"text", "json"}:
        _usage_error("export supports --format text|json")
    if output_dir is None:
        _usage_error("export requires --output-dir")
    assert output_dir is not None
    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=profile, strict=strict)
        effective_strict = strict or bool(
            resolution.profile and resolution.profile.strict_validation
        )
        result = generate_export_package(
            resolution,
            output_dir=output_dir,
            preset_dir=preset_dir,
            strict=effective_strict,
            overwrite=overwrite,
            package_name=package_name,
            deterministic=deterministic,
        )
        payload = (
            result.model_dump_json(indent=2) + "\n"
            if output_format == "json"
            else _export_text(result)
        )
        _emit(payload, None)
        raise typer.Exit(
            0 if result.validation_passed and result.runtime_smoke_status != "error" else 1
        )
    except LabError as exc:
        _handle_error(exc, command="export", output_format=output_format, output=None)


def _resolve_inspect_format(
    output_format: str, *, json_output: bool, markdown: bool
) -> OutputFormat:
    if output_format not in {"text", "json", "markdown"}:
        _usage_error("inspect supports --format text|json|markdown")
    explicit_flags = [json_output, markdown]
    if sum(explicit_flags) > 1:
        _usage_error("Use only one of --json or --markdown.")
    if json_output and output_format != "text":
        _usage_error("Use either --json or --format, not both.")
    if markdown and output_format != "text":
        _usage_error("Use either --markdown or --format, not both.")
    if json_output:
        return "json"
    if markdown:
        return "markdown"
    if output_format == "json":
        return "json"
    if output_format == "markdown":
        return "markdown"
    return "text"


def _usage_error(message: str) -> None:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(2)


def _handle_error(
    error: LabError,
    *,
    command: str,
    output_format: str,
    output: Path | None,
) -> None:
    if output_format == "json":
        issue = ValidationIssue(
            code=error.code,
            severity="error",
            message=error.message,
            remediation=error.remediation,
        )
        payload = (
            ErrorResult(command=command, status="error", issues=[issue]).model_dump_json(indent=2)
            + "\n"
        )
        try:
            _emit(payload, output)
        except LabError as output_error:
            typer.echo(str(error), err=True)
            typer.echo(str(output_error), err=True)
            raise typer.Exit(output_error.exit_code) from output_error
    else:
        typer.echo(str(error), err=True)
    raise typer.Exit(error.exit_code)


def _emit(payload: str, output: Path | None) -> None:
    if output is None:
        typer.echo(payload, nl=False)
    else:
        _write_text(output, payload)


def _write_text(path: Path, content: str) -> None:
    write_text_atomic(path, content)


def _doctor_text(result: DoctorResult) -> str:
    lines = [f"status: {result.status}", f"asset_root: {result.resolved_asset_root or ''}"]
    for check in result.checks:
        code = f" [{check.code}]" if check.code else ""
        lines.append(f"{check.status}: {check.name}{code}: {check.detail}")
    return "\n".join(lines) + "\n"


def _inspect_text(result: InspectResult) -> str:
    lines = [
        f"model: {result.model_name}",
        f"status: {result.status}",
        (
            f"bodies={result.body_count} joints={result.joint_count} "
            f"actuators={result.actuator_count} sensors={result.sensor_count} "
            f"meshes={result.mesh_count} geoms={result.geom_count}"
        ),
        f"cameras={result.camera_count} sites={result.site_count}",
    ]
    if result.total_declared_mass_kg is not None:
        lines.append(f"total_declared_mass_kg={result.total_declared_mass_kg}")
    lines.extend(f"warning: {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _validation_text(result: ValidationResult) -> str:
    lines = [
        f"status: {result.status}",
        f"passed: {result.passed}",
        f"issue_count: {result.issue_count}",
    ]
    lines.extend(f"{issue.severity}: {issue.code}: {issue.message}" for issue in result.issues)
    return "\n".join(lines) + "\n"


def _evidence_text(result: EvidenceBundleResult) -> str:
    lines = [
        f"status: {result.status}",
        f"validation_passed: {result.validation_passed}",
        f"validation_issue_count: {result.validation_issue_count}",
        f"runtime_smoke_status: {result.runtime_smoke_status}",
        f"runtime_smoke_skipped: {result.runtime_smoke_skipped}",
        f"bundle_dir: {result.bundle_dir}",
    ]
    lines.extend(
        f"artifact: {artifact.artifact_type} {artifact.relative_path} sha256={artifact.sha256}"
        for artifact in result.artifacts
    )
    lines.extend(f"warning: {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _runtime_smoke_text(result: RuntimeSmokeResult) -> str:
    lines = [
        f"status: {result.status}",
        f"runtime_available: {result.runtime_available}",
        f"skipped: {result.skipped}",
        f"loaded: {result.loaded}",
        f"xml_path: {result.xml_path}",
    ]
    if result.runtime_version is not None:
        lines.append(f"runtime_version: {result.runtime_version}")
    if result.model_counts is not None:
        lines.append(
            "model_counts: "
            f"nbody={result.model_counts.nbody} "
            f"njnt={result.model_counts.njnt} "
            f"nu={result.model_counts.nu} "
            f"nsensor={result.model_counts.nsensor} "
            f"ngeom={result.model_counts.ngeom} "
            f"nmesh={result.model_counts.nmesh}"
        )
    if result.failure_code is not None:
        lines.append(f"failure: {result.failure_code}: {result.failure_message or ''}")
    lines.extend(f"warning: {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _export_text(result: ExportPackageResult) -> str:
    lines = [
        f"status: {result.status}",
        f"validation_passed: {result.validation_passed}",
        f"runtime_smoke_status: {result.runtime_smoke_status}",
        f"runtime_smoke_skipped: {result.runtime_smoke_skipped}",
        f"archive_path: {result.archive_path}",
        f"archive_sha256: {result.archive_sha256}",
        f"evidence_bundle_path: {result.evidence_bundle_path}",
    ]
    lines.extend(f"warning: {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _viewer_open_text(result: ViewerOpenResult) -> str:
    lines = [
        f"status: {result.status}",
        f"opened: {result.opened}",
        f"launch_mode: {result.launch_mode}",
        f"validation_passed: {result.validation_passed}",
        f"validation_issue_count: {result.validation_issue_count}",
        f"runtime_smoke_status: {result.runtime_smoke_status}",
        f"xml_path: {result.xml_path}",
        f"preset_name: {result.preset_name or ''}",
    ]
    if result.runtime_version is not None:
        lines.append(f"runtime_version: {result.runtime_version}")
    if result.failure_code is not None:
        lines.append(f"failure: {result.failure_code}: {result.failure_message or ''}")
    if result.failure_help_url is not None:
        lines.append(f"help: {result.failure_help_url}")
    lines.extend(f"warning: {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _doctor_exit_code(status: Status) -> int:
    return 3 if status == "error" else 0
