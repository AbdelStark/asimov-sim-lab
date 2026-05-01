"""CLI entrypoint for Asimov Sim Lab."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal

import typer

from asimov_sim_lab.doctor import run_doctor
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.inspect import inspect_model, render_inspect_markdown
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    DoctorResult,
    ErrorResult,
    InspectResult,
    Status,
    ValidationIssue,
    ValidationResult,
)
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.validation import validate_model

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
    if path.exists() and path.is_dir():
        raise LabError(
            "OUTPUT_PATH_IS_DIRECTORY",
            f"Output path is a directory: {path}",
            "Pass a file path for --output or --manifest-output.",
            exit_code=2,
        )
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise LabError(
            "OUTPUT_WRITE_FAILED",
            f"Could not write output path: {path}: {exc}",
            "Check directory permissions and available disk space.",
            exit_code=2,
        ) from exc


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
    for warning in result.warnings:
        lines.append(f"warning: {warning}")
    return "\n".join(lines) + "\n"


def _validation_text(result: ValidationResult) -> str:
    lines = [
        f"status: {result.status}",
        f"passed: {result.passed}",
        f"issue_count: {result.issue_count}",
    ]
    for issue in result.issues:
        lines.append(f"{issue.severity}: {issue.code}: {issue.message}")
    return "\n".join(lines) + "\n"


def _doctor_exit_code(status: Status) -> int:
    return 3 if status == "error" else 0
