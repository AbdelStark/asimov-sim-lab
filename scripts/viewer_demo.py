"""Interactive MuJoCo viewer demo.

Runs the schema-backed ``open`` preflight against the configured asset root
and then launches the official MuJoCo passive viewer with the model posed
to the ``neutral`` preset and a framed camera, so the humanoid is visible
and stepping the moment the window appears.

Asset-root resolution order:

1. ``--asset-root`` CLI flag.
2. ``ASIMOV_SIM_LAB_ASSET_ROOT`` environment variable.
3. A sibling ``asimov-v1`` checkout next to this repository (auto-detected).
4. The bundled ``minimal_valid`` synthetic test fixture (last-resort fallback
   so the demo always runs offline; this fixture is a stub, not a showcase).

Usage::

    uv run python scripts/viewer_demo.py
    uv run python scripts/viewer_demo.py --asset-root /path/to/asimov-v1
    uv run python scripts/viewer_demo.py --preset neutral

The library itself remains preflight-only; this script is a thin operator
convenience that imports ``mujoco`` directly and is not part of the public
API contract.

Requires the optional viewer extra: ``uv sync --extra viewer``.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.paths import PRIMARY_XML, resolve_asset_root
from asimov_sim_lab.presets import build_neutral_preset, load_preset_dir
from asimov_sim_lab.viewer import DEFAULT_VIEWER_PRESET, run_viewer_open_preflight

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ASSET_ROOT = REPO_ROOT / "tests" / "fixtures" / "source_roots" / "minimal_valid"
SIBLING_ASSET_ROOT = REPO_ROOT.parent / "asimov-v1"


def main() -> int:
    args = _parse_args()
    console = Console()

    asset_root, source = _resolve_demo_asset_root(args.asset_root)
    preset_dir = Path(args.preset_dir).resolve() if args.preset_dir else None

    console.print(
        Panel.fit(
            f"[bold]asset root:[/bold] {asset_root}\n[bold]source:[/bold] {source}",
            title="viewer demo",
            border_style="magenta",
        )
    )
    if source == "fixture":
        console.print(
            "[yellow]⚠ Using the synthetic minimal_valid test fixture.[/yellow]\n"
            "[dim]This is a 2-link stub, not a showcase. To see the real humanoid, "
            "either:[/dim]\n"
            "  [dim]• place an asimov-v1 checkout next to this repo, or[/dim]\n"
            "  [dim]• set ASIMOV_SIM_LAB_ASSET_ROOT=/path/to/asimov-v1, or[/dim]\n"
            "  [dim]• pass --asset-root /path/to/asimov-v1[/dim]"
        )

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

    xml_path = resolution.asset_root / PRIMARY_XML
    console.print(f"\n[green]launching MuJoCo viewer:[/green] {xml_path}")
    console.print("[dim]close the window or press Esc to exit[/dim]\n")

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    preset_joints = _load_preset_joints(resolution, preset_name=args.preset, preset_dir=preset_dir)
    applied = _apply_joint_pose(mujoco, model, data, preset_joints)
    mujoco.mj_forward(model, data)
    if applied:
        console.print(f"[dim]applied {applied} joint(s) from preset {args.preset!r}[/dim]")

    _launch_viewer(mujoco, model, data, console)
    return 0


def _resolve_demo_asset_root(cli_asset_root: str | None) -> tuple[Path, str]:
    """Pick the asset root for the demo and label its provenance."""
    if cli_asset_root:
        return Path(cli_asset_root).resolve(), "--asset-root flag"
    env_root = os.environ.get("ASIMOV_SIM_LAB_ASSET_ROOT")
    if env_root:
        return Path(env_root).resolve(), "ASIMOV_SIM_LAB_ASSET_ROOT env var"
    if (SIBLING_ASSET_ROOT / "sim-model" / "xmls" / "asimov.xml").is_file():
        return SIBLING_ASSET_ROOT.resolve(), "auto-detected sibling asimov-v1 checkout"
    return FIXTURE_ASSET_ROOT.resolve(), "fixture"


def _load_preset_joints(
    resolution: object,
    *,
    preset_name: str,
    preset_dir: Path | None,
) -> dict[str, float]:
    """Resolve a preset to a joint-name → angle mapping."""
    if preset_name == DEFAULT_VIEWER_PRESET:
        inspect_result = inspect_model(resolution)  # type: ignore[arg-type]
        neutral, _issues = build_neutral_preset(inspect_result)
        return dict(neutral.joints)
    if preset_dir is None:
        return {}
    presets, _issues = load_preset_dir(preset_dir)
    for preset in presets:
        if preset.name == preset_name:
            return dict(preset.joints)
    return {}


def _apply_joint_pose(
    mujoco_mod: object,
    model: object,
    data: object,
    joints: dict[str, float],
) -> int:
    """Write preset joint angles into data.qpos. Returns count applied."""
    applied = 0
    for name, value in joints.items():
        try:
            joint = model.joint(name)  # type: ignore[attr-defined]
        except KeyError:
            continue
        qposadr = int(joint.qposadr[0])
        data.qpos[qposadr] = value  # type: ignore[attr-defined]
        applied += 1
    return applied


def _launch_viewer(mujoco_mod: object, model: object, data: object, console: Console) -> None:
    """Launch the MuJoCo viewer with a framed camera and an auto-step loop.

    Prefers ``launch_passive`` (which lets us drive the simulation, set the
    camera, and start unpaused), but falls back to the blocking ``launch`` on
    macOS, where ``launch_passive`` requires the ``mjpython`` shim. The
    fallback viewer still respects the pre-applied ``data.qpos`` pose; the
    user presses Space to unpause.
    """
    try:
        ctx = mujoco_mod.viewer.launch_passive(model, data)  # type: ignore[attr-defined]
    except RuntimeError as exc:
        console.print(
            f"[yellow]launch_passive unavailable ({exc}); falling back to blocking viewer.[/yellow]"
        )
        console.print("[dim]press Space inside the viewer to run physics.[/dim]")
        mujoco_mod.viewer.launch(model, data)  # type: ignore[attr-defined]
        return

    with ctx as viewer:
        viewer.cam.lookat[:] = [0.0, 0.0, 0.8]
        viewer.cam.distance = 3.5
        viewer.cam.azimuth = 135.0
        viewer.cam.elevation = -15.0
        viewer.sync()

        timestep = float(model.opt.timestep)  # type: ignore[attr-defined]
        while viewer.is_running():
            step_start = time.perf_counter()
            mujoco_mod.mj_step(model, data)  # type: ignore[attr-defined]
            viewer.sync()
            slack = timestep - (time.perf_counter() - step_start)
            if slack > 0:
                time.sleep(slack)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--asset-root",
        help=(
            "Override the asset root. Defaults to a sibling asimov-v1 checkout "
            "if present, otherwise the synthetic minimal_valid fixture."
        ),
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
