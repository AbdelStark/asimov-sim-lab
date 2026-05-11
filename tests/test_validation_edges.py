from __future__ import annotations

from pathlib import Path

import pytest

from asimov_sim_lab.errors import LabError
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.validation import validate_model


def _source(root: Path, xml: str) -> Path:
    (root / "sim-model" / "xmls").mkdir(parents=True)
    (root / "sim-model" / "assets" / "meshes").mkdir(parents=True)
    (root / "sim-model" / "xmls" / "asimov.xml").write_text(xml, encoding="utf-8")
    (root / "sim-model" / "assets" / "meshes" / "LEFT_HIP_PITCH.STL").write_text(
        "solid LEFT_HIP_PITCH\nendsolid LEFT_HIP_PITCH\n",
        encoding="utf-8",
    )
    return root


def test_validate_malformed_xml_raises_typed_error(fixtures_dir: Path) -> None:
    resolution = resolve_asset_root(
        asset_root=fixtures_dir / "source_roots" / "malformed_xml",
        profile_path=None,
        env={},
    )

    with pytest.raises(LabError) as exc:
        validate_model(resolution)

    assert exc.value.code == "XML_PARSE_FAILED"


def test_validate_sensor_missing_reference(tmp_path: Path) -> None:
    source = _source(
        tmp_path,
        """
        <mujoco model="BadSensor">
          <compiler meshdir="../assets/meshes"/>
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody><body name="pelvis_link"><freejoint name="floating_base"/></body></worldbody>
          <sensor><gyro name="bad_gyro" site="missing_site"/></sensor>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = validate_model(resolution)

    assert any(issue.code == "SENSOR_REFERENCE_MISSING" for issue in result.issues)
    assert not result.passed


def test_validate_sensor_geom_reference_uses_geom_namespace(tmp_path: Path) -> None:
    source = _source(
        tmp_path,
        """
        <mujoco model="GeomSensor">
          <compiler meshdir="../assets/meshes"/>
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody>
            <body name="pelvis_link">
              <freejoint name="floating_base"/>
              <geom name="pelvis_collision" type="sphere" size="0.1"/>
            </body>
          </worldbody>
          <sensor>
            <framepos name="good_geom_sensor" objtype="geom" objname="pelvis_collision"/>
            <framepos name="bad_geom_sensor" objtype="geom" objname="left"/>
          </sensor>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = validate_model(resolution)

    missing = [issue for issue in result.issues if issue.code == "SENSOR_REFERENCE_MISSING"]
    assert len(missing) == 1
    assert missing[0].object_name == "bad_geom_sensor"
    assert not result.passed


def test_validate_unsupported_meshdir_fails(tmp_path: Path) -> None:
    source = _source(
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

    with pytest.raises(LabError) as exc:
        validate_model(resolution)

    assert exc.value.code == "UNSUPPORTED_SOURCE_LAYOUT"


def test_validate_actuator_without_target_warns(tmp_path: Path) -> None:
    source = _source(
        tmp_path,
        """
        <mujoco model="TargetlessActuator">
          <compiler meshdir="../assets/meshes"/>
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody><body name="pelvis_link"><freejoint name="floating_base"/></body></worldbody>
          <actuator><general name="targetless"/></actuator>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = validate_model(resolution)

    assert any(issue.code == "ACTUATOR_TARGET_MISSING" for issue in result.issues)
    assert result.passed


def test_validate_missing_unlimited_hinge_range_warns(tmp_path: Path) -> None:
    source = _source(
        tmp_path,
        """
        <mujoco model="RangeWarning">
          <compiler meshdir="../assets/meshes"/>
          <asset><mesh name="left" file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody>
            <body name="pelvis_link">
              <joint name="loose_joint" type="hinge" axis="0 1 0"/>
            </body>
          </worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = validate_model(resolution)

    assert any(issue.code == "JOINT_RANGE_MISSING" for issue in result.issues)
    assert result.passed


def test_validate_geom_can_reference_mesh_by_file_stem(tmp_path: Path) -> None:
    # An unnamed <mesh file="X.STL"/> is named "X" in MuJoCo. The validation view
    # must agree, or geoms that reference the stem hit MESH_ASSET_REFERENCE_UNKNOWN.
    source = _source(
        tmp_path,
        """
        <mujoco model="StemRef">
          <compiler meshdir="../assets/meshes"/>
          <asset><mesh file="LEFT_HIP_PITCH.STL"/></asset>
          <worldbody>
            <body name="pelvis_link">
              <freejoint name="floating_base"/>
              <geom name="hip_visual" type="mesh" mesh="LEFT_HIP_PITCH"/>
            </body>
          </worldbody>
        </mujoco>
        """,
    )
    resolution = resolve_asset_root(asset_root=source, profile_path=None, env={})

    result = validate_model(resolution)

    assert not any(issue.code == "MESH_ASSET_REFERENCE_UNKNOWN" for issue in result.issues)
    assert result.passed
