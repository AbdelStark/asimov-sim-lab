"""Interactive MuJoCo viewer demo.

Runs the schema-backed ``open`` preflight against the configured asset root
(or the bundled synthetic fixture, by default) and then launches the official
MuJoCo passive viewer so the model can be inspected interactively. The library
itself remains preflight-only; this script is a thin operator convenience that
imports ``mujoco`` directly and is not part of the public API contract.

Usage::

    uv run python scripts/viewer_demo.py
    uv run python scripts/viewer_demo.py --asset-root /path/to/asimov-v1
    uv run python scripts/viewer_demo.py --preset neutral

Requires the optional viewer extra: ``uv sync --extra viewer``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.viewer import DEFAULT_VIEWER_PRESET, run_viewer_open_preflight

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "source_roots" / "minimal_valid"


def main() -> int:
    args = _parse_args()
    console = Console()

    asset_root = Path(args.asset_root).resolve() if args.asset_root else DEFAULT_FIXTURE
    preset_dir = Path(args.preset_dir).resolve() if args.preset_dir else None

    try:
        resolution = resolve_asset_root(asset_root=asset_root, profile_path=None)
    except Exception as exc:
        console.print(f"[red]asset-root resolution failed:[/red] {exc}")
        return 3

    preflight = run_viewer_open_preflight(
        resolution,
        preset_name=args.preset,
        preset_dir=preset_dir,
    )
    console.print(
        Panel.fit(
            f"[bold]preflight status:[/bold] {preflight.status}\n"
            f"[bold]validation passed:[/bold] {preflight.validation_passed}\n"
            f"[bold]runtime smoke:[/bold] {preflight.runtime_smoke_status}\n"
            f"[bold]xml:[/bold] {preflight.xml_path}\n"
            f"[bold]preset:[/bold] {preflight.preset_name or '-'}",
            title="open preflight",
            border_style="cyan",
        )
    )
    if preflight.failure_code is not None:
        console.print(
            f"[red]preflight failure:[/red] {preflight.failure_code}: {preflight.failure_message}"
        )
        return 1
    if not preflight.validation_passed:
        console.print("[red]validation failed; not launching the viewer[/red]")
        return 1

    try:
        import mujoco
        import mujoco.viewer
    except ImportError:
        console.print(
            "[red]mujoco is not installed.[/red] Run: [bold]uv sync --extra viewer[/bold]"
        )
        return 2

    xml_path = resolution.asset_root / preflight.xml_path
    console.print(f"\n[green]launching MuJoCo viewer:[/green] {xml_path}")
    console.print("[dim]close the window or press Esc to exit[/dim]\n")

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    mujoco.viewer.launch(model, data)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--asset-root",
        help="Override the asset root. Defaults to the synthetic minimal_valid fixture.",
    )
    parser.add_argument(
        "--preset",
        default=DEFAULT_VIEWER_PRESET,
        help="Viewer preset name (default: neutral).",
    )
    parser.add_argument(
        "--preset-dir",
        help="Optional directory of local preset TOML files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
