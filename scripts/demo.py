"""End-to-end showcase of the Asimov Sim Lab public surface.

The demo runs against the hermetic synthetic fixture in ``tests/fixtures`` so
it works on any machine without an upstream Asimov v1 checkout. It walks the
full operator workflow: ``doctor`` → ``inspect`` → ``validate`` →
``runtime-smoke`` → ``open`` preflight → ``evidence`` → ``export`` →
release-evidence verification, then re-runs the validator against a broken
fixture to demonstrate failure surfaces.

Usage::

    uv run python scripts/demo.py
    uv run python scripts/demo.py --asset-root /absolute/path/to/asimov-v1
    uv run python scripts/demo.py --keep-output  # keep the demo workdir

Exit codes mirror the CLI: ``0`` on success, ``1`` if validation of the
canonical fixture fails (which would indicate a regression, since the
broken-fixture step is expected to fail and is handled internally).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from asimov_sim_lab import __version__
from asimov_sim_lab.doctor import run_doctor
from asimov_sim_lab.evidence import generate_evidence_bundle
from asimov_sim_lab.export import generate_export_package
from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.paths import AssetRootResolution, resolve_asset_root
from asimov_sim_lab.runtime import run_runtime_smoke
from asimov_sim_lab.validation import validate_model
from asimov_sim_lab.viewer import run_viewer_open_preflight

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "source_roots" / "minimal_valid"
BROKEN_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "source_roots" / "broken_actuator_ref"
PRESET_DIR = REPO_ROOT / "docs" / "examples" / "presets"

STATUS_STYLES = {"ok": "bold green", "warning": "bold yellow", "error": "bold red"}


def main() -> int:
    args = _parse_args()
    console = Console()

    asset_root = Path(args.asset_root).resolve() if args.asset_root else DEFAULT_FIXTURE
    if args.output_dir:
        workdir = Path(args.output_dir).resolve()
    else:
        workdir = Path(tempfile.mkdtemp(prefix="asimov-sim-lab-demo-"))
    workdir.mkdir(parents=True, exist_ok=True)

    _print_header(console, asset_root, workdir)
    try:
        _run_doctor(console, asset_root)
        _run_inspect(console, asset_root)
        _run_validate(console, asset_root)
        _run_runtime_smoke(console, asset_root)
        _run_open_preflight(console, asset_root)
        _run_evidence(console, asset_root, workdir / "evidence")
        _run_export(console, asset_root, workdir / "export")
        _run_release_check(console, workdir / "export")
        _run_broken_fixture(console)
    finally:
        if args.keep_output:
            console.print(f"[dim]demo artifacts preserved at: {workdir}[/dim]")
        else:
            shutil.rmtree(workdir, ignore_errors=True)
            console.print(f"[dim]cleaned up demo workdir: {workdir}[/dim]")

    console.print()
    console.print(Panel.fit("[bold green]All showcase steps completed successfully.[/bold green]"))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--asset-root",
        help="Override the asset root. Defaults to the synthetic minimal_valid fixture.",
    )
    parser.add_argument(
        "--output-dir",
        help="Persist evidence/export artifacts in this directory (default: ephemeral tempdir).",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Do not delete the demo workdir on exit.",
    )
    return parser.parse_args()


def _relpath(path: Path) -> str:
    """Return ``path`` relative to the repo root when possible."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _print_header(console: Console, asset_root: Path, workdir: Path) -> None:
    title = Text.assemble(
        ("Asimov Sim Lab ", "bold"),
        (f"v{__version__}", "bold cyan"),
        (" — end-to-end showcase", "bold"),
    )
    body = Text.from_markup(
        f"[bold]asset root:[/bold] {_relpath(asset_root)}\n"
        f"[bold]workdir:[/bold]    {workdir}\n"
        f"[bold]preset dir:[/bold] {_relpath(PRESET_DIR)}",
    )
    console.print(Panel(body, title=title, border_style="cyan"))


def _section(console: Console, title: str, cli_equivalent: str) -> None:
    console.print()
    console.print(Rule(f"[bold]{title}[/bold]", style="cyan"))
    console.print(f"[dim]CLI:[/dim] [italic]{cli_equivalent}[/italic]")


def _status_text(status: str) -> Text:
    return Text(status, style=STATUS_STYLES.get(status, "white"))


def _resolve(asset_root: Path) -> AssetRootResolution:
    return resolve_asset_root(asset_root=asset_root, profile_path=None)


def _run_doctor(console: Console, asset_root: Path) -> None:
    _section(
        console,
        "1. doctor — layout and provenance",
        f"asimov-sim-lab doctor --asset-root {_relpath(asset_root)}",
    )
    resolution = _resolve(asset_root)
    result, manifest = run_doctor(resolution)

    table = Table(show_header=True, header_style="bold")
    table.add_column("check")
    table.add_column("status")
    table.add_column("detail", overflow="fold")
    for check in result.checks:
        table.add_row(check.name, _status_text(check.status), check.detail or "—")
    if not result.checks:
        table.add_row("layout", _status_text("ok"), "no warnings")

    console.print(table)
    summary = Text.assemble(("overall: ", "bold"), _status_text(result.status))
    if manifest is not None:
        summary.append(
            f"  •  manifest: 1 XML / {len(manifest.meshes)} mesh files",
            style="dim",
        )
    console.print(summary)


def _run_inspect(console: Console, asset_root: Path) -> None:
    _section(
        console,
        "2. inspect — MJCF model contract",
        f"asimov-sim-lab inspect --asset-root {_relpath(asset_root)} --json",
    )
    resolution = _resolve(asset_root)
    result = inspect_model(resolution)

    table = Table(show_header=True, header_style="bold")
    table.add_column("metric")
    table.add_column("count", justify="right")
    table.add_row("bodies", str(result.body_count))
    table.add_row("joints", str(result.joint_count))
    table.add_row("actuators", str(result.actuator_count))
    table.add_row("sensors", str(result.sensor_count))
    table.add_row("meshes", str(result.mesh_count))
    table.add_row("geoms", str(result.geom_count))
    table.add_row("cameras", str(result.camera_count))
    table.add_row("sites", str(result.site_count))
    if result.total_declared_mass_kg is not None:
        table.add_row("declared mass (kg)", f"{result.total_declared_mass_kg:.3f}")
    console.print(table)
    if result.warnings:
        console.print(f"[yellow]warnings:[/yellow] {len(result.warnings)}")


def _run_validate(console: Console, asset_root: Path) -> None:
    _section(
        console,
        "3. validate — references, ranges, presets",
        (
            f"asimov-sim-lab validate --asset-root {_relpath(asset_root)} "
            f"--preset-dir {_relpath(PRESET_DIR)} --format json"
        ),
    )
    resolution = _resolve(asset_root)
    result = validate_model(resolution, preset_dir=PRESET_DIR)

    summary = Text.assemble(
        ("status: ", "bold"),
        _status_text(result.status),
        f"  •  passed={result.passed}  •  issues={result.issue_count}",
    )
    console.print(summary)
    if result.issues:
        _print_issues(console, result.issues)
    if not result.passed:
        raise SystemExit("validation of canonical fixture failed (regression)")


def _run_runtime_smoke(console: Console, asset_root: Path) -> None:
    _section(
        console,
        "4. runtime-smoke — optional MuJoCo compile check",
        (
            f"asimov-sim-lab runtime-smoke --asset-root {_relpath(asset_root)} "
            "--allow-missing-mujoco --format json"
        ),
    )
    resolution = _resolve(asset_root)
    result = run_runtime_smoke(resolution, require_mujoco=False)

    table = Table(show_header=True, header_style="bold")
    table.add_column("field")
    table.add_column("value", overflow="fold")
    table.add_row("status", _status_text(result.status))
    table.add_row("runtime_available", str(result.runtime_available))
    table.add_row("skipped", str(result.skipped))
    table.add_row("loaded", str(result.loaded))
    if result.runtime_version is not None:
        table.add_row("runtime_version", result.runtime_version)
    if result.failure_code is not None:
        table.add_row("failure", f"{result.failure_code}: {result.failure_message or ''}")
    console.print(table)


def _run_open_preflight(console: Console, asset_root: Path) -> None:
    _section(
        console,
        "5. open — viewer preflight (no GUI)",
        (
            f"asimov-sim-lab open --asset-root {_relpath(asset_root)} "
            f"--preset-dir {_relpath(PRESET_DIR)} --format json"
        ),
    )
    resolution = _resolve(asset_root)
    result = run_viewer_open_preflight(resolution, preset_dir=PRESET_DIR)

    table = Table(show_header=True, header_style="bold")
    table.add_column("field")
    table.add_column("value", overflow="fold")
    table.add_row("status", _status_text(result.status))
    table.add_row("opened", str(result.opened))
    table.add_row("launch_mode", result.launch_mode)
    table.add_row("validation_passed", str(result.validation_passed))
    table.add_row("preset_name", result.preset_name or "—")
    if result.failure_code is not None:
        table.add_row("failure", f"{result.failure_code}: {result.failure_message or ''}")
        if result.failure_help_url is not None:
            table.add_row("help_url", result.failure_help_url)
    console.print(table)


def _run_evidence(console: Console, asset_root: Path, output_dir: Path) -> None:
    _section(
        console,
        "6. evidence — checksummed review bundle",
        (
            f"asimov-sim-lab evidence --asset-root {_relpath(asset_root)} "
            f"--output-dir {output_dir} --overwrite --format json"
        ),
    )
    resolution = _resolve(asset_root)
    result = generate_evidence_bundle(
        resolution,
        output_dir=output_dir,
        preset_dir=PRESET_DIR,
        overwrite=True,
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("artifact")
    table.add_column("type")
    table.add_column("sha256", overflow="fold")
    for artifact in result.artifacts:
        table.add_row(artifact.relative_path, artifact.artifact_type, artifact.sha256)
    console.print(table)

    summary = Text.assemble(
        ("bundle: ", "bold"),
        f"{result.bundle_dir}\n",
        ("status: ", "bold"),
        _status_text(result.status),
        f"  •  validation_passed={result.validation_passed}",
    )
    console.print(summary)


def _run_export(console: Console, asset_root: Path, output_dir: Path) -> None:
    _section(
        console,
        "7. export — deterministic release archive",
        (
            f"asimov-sim-lab export --asset-root {_relpath(asset_root)} "
            f"--output-dir {output_dir} --overwrite --format json"
        ),
    )
    resolution = _resolve(asset_root)
    result = generate_export_package(
        resolution,
        output_dir=output_dir,
        preset_dir=PRESET_DIR,
        overwrite=True,
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("field")
    table.add_column("value", overflow="fold")
    table.add_row("status", _status_text(result.status))
    table.add_row("archive_path", result.archive_path)
    table.add_row("archive_sha256", result.archive_sha256)
    table.add_row("evidence_bundle_path", result.evidence_bundle_path)
    console.print(table)


def _run_release_check(console: Console, export_dir: Path) -> None:
    _section(
        console,
        "8. release evidence — independent verifier",
        f"python scripts/check_release_evidence.py --export-dir {export_dir}",
    )
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from check_release_evidence import validate_export_dir
    finally:
        sys.path.pop(0)

    errors = validate_export_dir(export_dir)
    if errors:
        for error in errors:
            console.print(f"[red]✗[/red] {error}")
        raise SystemExit("release evidence verification failed (regression)")
    console.print("[green]✓ export package passes release-evidence policy[/green]")


def _run_broken_fixture(console: Console) -> None:
    _section(
        console,
        "9. broken fixture — failure surface",
        f"asimov-sim-lab validate --asset-root {_relpath(BROKEN_FIXTURE)} --format json",
    )
    if not BROKEN_FIXTURE.exists():
        console.print(f"[yellow]skipped:[/yellow] fixture not present at {BROKEN_FIXTURE}")
        return
    resolution = resolve_asset_root(asset_root=BROKEN_FIXTURE, profile_path=None)
    result = validate_model(resolution)

    summary = Text.assemble(
        ("status: ", "bold"),
        _status_text(result.status),
        f"  •  passed={result.passed}  •  issues={result.issue_count}",
    )
    console.print(summary)
    _print_issues(console, result.issues)
    console.print(
        "[dim]→ this failure is expected; the demo proves diagnostics surface cleanly.[/dim]",
    )


def _print_issues(console: Console, issues: object) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("severity")
    table.add_column("code")
    table.add_column("message", overflow="fold")
    for issue in issues:  # type: ignore[attr-defined]
        severity_style = "red" if issue.severity == "error" else "yellow"
        table.add_row(Text(issue.severity, style=severity_style), issue.code, issue.message)
    console.print(table)


if __name__ == "__main__":
    raise SystemExit(main())
