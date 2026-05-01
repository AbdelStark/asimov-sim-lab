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
