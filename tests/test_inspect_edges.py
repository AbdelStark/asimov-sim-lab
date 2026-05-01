from __future__ import annotations

from pathlib import Path

import pytest

from asimov_sim_lab.errors import LabError
from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.paths import resolve_asset_root


def _write_source(root: Path, xml: str, *, mesh_name: str = "LEFT_HIP_PITCH.STL") -> Path:
    (root / "sim-model" / "xmls").mkdir(parents=True)
    (root / "sim-model" / "assets" / "meshes").mkdir(parents=True)
    (root / "sim-model" / "xmls" / "asimov.xml").write_text(xml, encoding="utf-8")
    (root / "sim-model" / "assets" / "meshes" / mesh_name).write_text(
        f"solid {mesh_name}\nendsolid {mesh_name}\n",
        encoding="utf-8",
    )
    return root


def test_inspect_missing_meshdir_warns(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        """
        <mujoco model="NoMeshdir">
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody><body name="pelvis_link"><freejoint name="floating_base"/></body></worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = inspect_model(resolution)

    assert any(warning.startswith("MESHDIR_MISSING") for warning in result.warnings)


def test_inspect_unsupported_meshdir_warns(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        """
        <mujoco model="BadMeshdir">
          <compiler meshdir="../../outside"/>
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody><body name="pelvis_link"><freejoint name="floating_base"/></body></worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = inspect_model(resolution)

    assert any(warning.startswith("UNSUPPORTED_SOURCE_LAYOUT") for warning in result.warnings)


def test_inspect_invalid_numeric_fails(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        """
        <mujoco model="BadNumber">
          <compiler meshdir="../assets/meshes"/>
          <worldbody>
            <body name="pelvis_link">
              <inertial mass="not-a-number"/>
            </body>
          </worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    with pytest.raises(LabError) as exc:
        inspect_model(resolution)

    assert exc.value.code == "XML_NUMERIC_PARSE_FAILED"


def test_inspect_no_asset_or_masses_is_allowed_with_warning(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        """
        <mujoco model="Sparse">
          <compiler meshdir="../assets/meshes"/>
          <worldbody><body name="pelvis_link"><freejoint name="floating_base"/></body></worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = inspect_model(resolution)

    assert result.mesh_count == 0
    assert result.total_declared_mass_kg is None
    assert any(warning.startswith("BODY_MASS_NOT_DECLARED") for warning in result.warnings)
