"""Optional MuJoCo runtime smoke checks."""

from __future__ import annotations

import importlib
from pathlib import Path
from time import perf_counter
from typing import Protocol, cast

from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import RuntimeModelCounts, RuntimeSmokeResult, Status
from asimov_sim_lab.paths import PRIMARY_XML, AssetRootResolution


class MjModelLike(Protocol):
    nbody: int
    njnt: int
    nu: int
    nsensor: int
    ngeom: int
    nmesh: int
    nq: int
    nv: int


class MjModelFactoryLike(Protocol):
    @staticmethod
    def from_xml_path(path: str) -> MjModelLike: ...


class MujocoModuleLike(Protocol):
    __version__: str
    MjModel: type[MjModelFactoryLike]


def run_runtime_smoke(
    resolution: AssetRootResolution,
    *,
    require_mujoco: bool = False,
    generated_at_utc: str | None = None,
    include_elapsed: bool = True,
    mujoco_module: MujocoModuleLike | None = None,
) -> RuntimeSmokeResult:
    """Load the canonical MJCF with MuJoCo when the optional runtime is installed."""
    manifest = generate_asset_manifest(resolution)
    warnings = list(manifest.warnings)
    xml_path = resolution.asset_root / PRIMARY_XML
    runtime = mujoco_module if mujoco_module is not None else _import_mujoco()

    if runtime is None:
        warning = "MUJOCO_NOT_INSTALLED: install the viewer extra to enable compiled-runtime smoke"
        warnings.append(warning)
        status: Status = "error" if require_mujoco else "warning"
        result = RuntimeSmokeResult(
            status=status,
            warnings=sorted(set(warnings)),
            runtime_available=False,
            skipped=True,
            loaded=False,
            xml_path=_portable_xml_path(xml_path, resolution.asset_root),
            failure_code="MUJOCO_NOT_INSTALLED" if require_mujoco else None,
            failure_message=warning if require_mujoco else None,
            failure_remediation="Run `uv sync --extra viewer` or omit `--require-mujoco`."
            if require_mujoco
            else None,
        )
        _stamp(result, generated_at_utc)
        return result

    started = perf_counter()
    try:
        model = runtime.MjModel.from_xml_path(str(xml_path))
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        result = RuntimeSmokeResult(
            status="error",
            warnings=sorted(set(warnings)),
            runtime_available=True,
            runtime_version=getattr(runtime, "__version__", None),
            skipped=False,
            loaded=False,
            xml_path=_portable_xml_path(xml_path, resolution.asset_root),
            elapsed_ms=round(elapsed_ms, 3) if include_elapsed else None,
            failure_code="MUJOCO_MODEL_LOAD_FAILED",
            failure_message=f"MuJoCo could not load {PRIMARY_XML.as_posix()}: {exc}",
            failure_remediation="Fix the MJCF, compiler paths, or referenced assets.",
        )
        _stamp(result, generated_at_utc)
        return result

    elapsed_ms = (perf_counter() - started) * 1000
    result = RuntimeSmokeResult(
        status="warning" if warnings else "ok",
        warnings=sorted(set(warnings)),
        runtime_available=True,
        runtime_version=getattr(runtime, "__version__", None),
        skipped=False,
        loaded=True,
        xml_path=_portable_xml_path(xml_path, resolution.asset_root),
        model_counts=RuntimeModelCounts(
            nbody=model.nbody,
            njnt=model.njnt,
            nu=model.nu,
            nsensor=model.nsensor,
            ngeom=model.ngeom,
            nmesh=model.nmesh,
            nq=model.nq,
            nv=model.nv,
        ),
        elapsed_ms=round(elapsed_ms, 3) if include_elapsed else None,
    )
    _stamp(result, generated_at_utc)
    return result


def _import_mujoco() -> MujocoModuleLike | None:
    try:
        return cast(MujocoModuleLike, importlib.import_module("mujoco"))
    except ImportError:
        return None


def _portable_xml_path(xml_path: Path, asset_root: Path) -> str:
    try:
        return xml_path.relative_to(asset_root).as_posix()
    except ValueError:
        return str(xml_path)


def _stamp(result: RuntimeSmokeResult, generated_at_utc: str | None) -> None:
    if generated_at_utc is not None:
        result.generated_at_utc = generated_at_utc
