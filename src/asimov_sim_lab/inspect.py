"""MJCF inspection contract extraction."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from asimov_sim_lab._xml import parse_mjcf as _parse_xml
from asimov_sim_lab.errors import LabError
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    ActuatorContract,
    AssetManifest,
    CameraContract,
    GeomContract,
    InspectResult,
    JointContract,
    MeshAssetContract,
    SensorContract,
    SiteContract,
    Status,
)
from asimov_sim_lab.paths import MESH_DIR, PRIMARY_XML, AssetRootResolution

if TYPE_CHECKING:
    from asimov_sim_lab._pipeline import PipelineContext


def inspect_model(
    resolution: AssetRootResolution,
    *,
    context: PipelineContext | None = None,
) -> InspectResult:
    """Parse the supported MJCF entrypoint into a stable contract.

    When ``context`` is provided, returns the already-computed inspect result
    so the same checkout is not re-parsed during a chained command.
    """
    if context is not None:
        return context.inspect_result
    manifest = generate_asset_manifest(resolution)
    xml_path = resolution.asset_root / PRIMARY_XML
    root = _parse_xml(xml_path)
    return _inspect_from_root(root, manifest, resolution)


def _inspect_from_root(
    root: ET.Element,
    manifest: AssetManifest,
    resolution: AssetRootResolution,
) -> InspectResult:
    """Build the inspect contract from an already-parsed MJCF root + manifest."""
    xml_path = resolution.asset_root / PRIMARY_XML
    warnings = list(manifest.warnings)
    compiler_meshdir = _compiler_meshdir(root, xml_path, resolution.asset_root)
    if compiler_meshdir.warning is not None:
        warnings.append(compiler_meshdir.warning)

    meshes = _mesh_assets(root)
    missing_meshes = _missing_mesh_files(meshes, compiler_meshdir.mesh_dir)
    warnings.extend(
        f"MESH_REFERENCE_MISSING: mesh file referenced by MJCF is missing: {missing}"
        for missing in missing_meshes
    )

    bodies: list[str] = []
    geoms: list[GeomContract] = []
    joints: list[JointContract] = []
    cameras: list[CameraContract] = []
    sites: list[SiteContract] = []
    total_mass = 0.0
    mass_count = 0

    worldbody = root.find("worldbody")
    if worldbody is not None:
        for body in worldbody.findall("body"):
            body_mass, body_mass_count = _walk_body(body, bodies, geoms, joints, cameras, sites)
            total_mass += body_mass
            mass_count += body_mass_count

    actuators = _actuators(root)
    actuator_joint_names = {
        actuator.joint_name for actuator in actuators if actuator.joint_name is not None
    }
    joints = [
        joint.model_copy(update={"passive": joint.name not in actuator_joint_names})
        for joint in joints
    ]

    sensors = _sensors(root)
    if mass_count == 0:
        warnings.append("BODY_MASS_NOT_DECLARED: no inertial mass declarations found")

    status: Status = "warning" if warnings else "ok"
    return InspectResult(
        status=status,
        warnings=sorted(set(warnings)),
        source_manifest_path=None,
        model_name=root.attrib.get("model", "unknown"),
        body_count=len(bodies),
        joint_count=len(joints),
        actuator_count=len(actuators),
        sensor_count=len(sensors),
        mesh_count=len(meshes),
        geom_count=len(geoms),
        camera_count=len(cameras),
        site_count=len(sites),
        total_declared_mass_kg=round(total_mass, 12) if mass_count else None,
        bodies=bodies,
        meshes=meshes,
        geoms=geoms,
        joints=joints,
        actuators=actuators,
        sensors=sensors,
        cameras=cameras,
        sites=sites,
    )


def render_inspect_markdown(result: InspectResult) -> str:
    """Render a deterministic Markdown model report from the JSON contract."""
    lines = [
        f"# {result.model_name} Model Contract",
        "",
        f"- status: `{result.status}`",
        f"- bodies: `{result.body_count}`",
        f"- joints: `{result.joint_count}`",
        f"- actuators: `{result.actuator_count}`",
        f"- sensors: `{result.sensor_count}`",
        f"- meshes: `{result.mesh_count}`",
        f"- geoms: `{result.geom_count}`",
        f"- cameras: `{result.camera_count}`",
        f"- sites: `{result.site_count}`",
    ]
    if result.total_declared_mass_kg is not None:
        lines.append(f"- total declared mass kg: `{result.total_declared_mass_kg}`")
    if result.warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in result.warnings)

    lines.extend(
        [
            "",
            "## Joints",
            "",
            "| name | body | type | range | passive |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for joint in result.joints:
        range_text = (
            f"{joint.range_min}..{joint.range_max}"
            if joint.range_min is not None and joint.range_max is not None
            else ""
        )
        lines.append(
            f"| {joint.name} | {joint.body} | {joint.joint_type} | {range_text} | {joint.passive} |"
        )

    lines.extend(
        ["", "## Actuators", "", "| name | type | joint | ctrlrange |", "| --- | --- | --- | --- |"]
    )
    for actuator in result.actuators:
        ctrlrange = (
            f"{actuator.ctrl_min}..{actuator.ctrl_max}"
            if actuator.ctrl_min is not None and actuator.ctrl_max is not None
            else ""
        )
        lines.append(
            f"| {actuator.name} | {actuator.actuator_type} | "
            f"{actuator.joint_name or ''} | {ctrlrange} |"
        )

    lines.extend(
        ["", "## Cameras", "", "| name | body | mode | fovy |", "| --- | --- | --- | --- |"]
    )
    lines.extend(
        f"| {camera.name} | {camera.body} | {camera.mode or ''} | {camera.fovy or ''} |"
        for camera in result.cameras
    )
    return "\n".join(lines) + "\n"


class _MeshdirResolution:
    def __init__(self, mesh_dir: Path, warning: str | None = None) -> None:
        self.mesh_dir = mesh_dir
        self.warning = warning


def _compiler_meshdir(root: ET.Element, xml_path: Path, asset_root: Path) -> _MeshdirResolution:
    supported = (asset_root / MESH_DIR).resolve()
    compiler = root.find("compiler")
    if compiler is None or compiler.attrib.get("meshdir") is None:
        return _MeshdirResolution(
            supported,
            warning=(
                "MESHDIR_MISSING: compiler@meshdir missing; using supported default mesh directory"
            ),
        )
    resolved = (xml_path.parent / compiler.attrib["meshdir"]).resolve()
    if resolved != supported:
        raise LabError(
            "UNSUPPORTED_SOURCE_LAYOUT",
            (f"compiler@meshdir resolves outside the supported MVP mesh directory: {resolved}"),
            "Keep MJCF mesh assets under sim-model/assets/meshes for the MVP contract.",
            exit_code=3,
        )
    return _MeshdirResolution(resolved)


def _mesh_assets(root: ET.Element) -> list[MeshAssetContract]:
    asset = root.find("asset")
    if asset is None:
        return []
    meshes: list[MeshAssetContract] = []
    for mesh in asset.findall("mesh"):
        file_name = mesh.attrib.get("file")
        if file_name is None:
            continue
        # MuJoCo defaults the mesh name to the file stem when no `name` is given.
        # Match that convention so contract names line up with geom `mesh=...` refs.
        name = mesh.attrib.get("name") or Path(file_name).stem
        meshes.append(MeshAssetContract(name=name, file=file_name))
    return meshes


def _missing_mesh_files(meshes: list[MeshAssetContract], mesh_dir: Path) -> list[str]:
    return [mesh.file for mesh in meshes if not (mesh_dir / mesh.file).is_file()]


def _walk_body(
    body: ET.Element,
    bodies: list[str],
    geoms: list[GeomContract],
    joints: list[JointContract],
    cameras: list[CameraContract],
    sites: list[SiteContract],
) -> tuple[float, int]:
    body_name = body.attrib.get("name", "")
    if body_name:
        bodies.append(body_name)

    mass_sum = 0.0
    mass_count = 0
    inertial = body.find("inertial")
    if inertial is not None and inertial.attrib.get("mass") is not None:
        mass_sum += _parse_float(inertial.attrib["mass"], "inertial@mass")
        mass_count += 1

    for geom in body.findall("geom"):
        geom_name = geom.attrib.get("name")
        if geom_name is None:
            continue
        geoms.append(
            GeomContract(
                name=geom_name,
                body=body_name,
                geom_type=geom.attrib.get("type"),
                mesh=geom.attrib.get("mesh"),
            )
        )
    for freejoint in body.findall("freejoint"):
        name = freejoint.attrib.get("name", "floating_base")
        joints.append(
            JointContract(
                name=name,
                body=body_name,
                joint_type="free",
                passive=True,
            )
        )
    for joint in body.findall("joint"):
        range_min, range_max = _parse_pair(joint.attrib.get("range"), "joint@range")
        joints.append(
            JointContract(
                name=joint.attrib.get("name", ""),
                body=body_name,
                joint_type=joint.attrib.get("type", "hinge"),
                axis=_parse_triplet(joint.attrib.get("axis"), "joint@axis"),
                range_min=range_min,
                range_max=range_max,
                ref=_parse_optional_float(joint.attrib.get("ref"), "joint@ref"),
                limited=_parse_optional_bool(joint.attrib.get("limited"), "joint@limited"),
                passive=True,
            )
        )
    for camera in body.findall("camera"):
        camera_name = camera.attrib.get("name")
        if camera_name is None:
            continue
        cameras.append(
            CameraContract(
                name=camera_name,
                body=body_name,
                mode=camera.attrib.get("mode"),
                pos=_parse_triplet(camera.attrib.get("pos"), "camera@pos"),
                quat=_parse_quad(camera.attrib.get("quat"), "camera@quat"),
                fovy=_parse_optional_float(camera.attrib.get("fovy"), "camera@fovy"),
            )
        )
    for site in body.findall("site"):
        site_name = site.attrib.get("name")
        if site_name is None:
            continue
        sites.append(
            SiteContract(
                name=site_name,
                body=body_name,
                pos=_parse_triplet(site.attrib.get("pos"), "site@pos"),
            )
        )
    for child in body.findall("body"):
        child_mass, child_count = _walk_body(child, bodies, geoms, joints, cameras, sites)
        mass_sum += child_mass
        mass_count += child_count
    return mass_sum, mass_count


def _actuators(root: ET.Element) -> list[ActuatorContract]:
    actuator_root = root.find("actuator")
    if actuator_root is None:
        return []
    actuators: list[ActuatorContract] = []
    for index, actuator in enumerate(list(actuator_root)):
        ctrl_min, ctrl_max = _parse_pair(actuator.attrib.get("ctrlrange"), "actuator@ctrlrange")
        actuators.append(
            ActuatorContract(
                name=actuator.attrib.get("name", f"{actuator.tag}_{index}"),
                actuator_type=actuator.tag,
                joint_name=actuator.attrib.get("joint"),
                ctrl_min=ctrl_min,
                ctrl_max=ctrl_max,
            )
        )
    return actuators


def _sensors(root: ET.Element) -> list[SensorContract]:
    sensor_root = root.find("sensor")
    if sensor_root is None:
        return []
    sensors: list[SensorContract] = []
    for index, sensor in enumerate(list(sensor_root)):
        sensors.append(
            SensorContract(
                name=sensor.attrib.get("name", f"{sensor.tag}_{index}"),
                sensor_type=sensor.tag,
                site=sensor.attrib.get("site"),
                body=sensor.attrib.get("body"),
                objtype=sensor.attrib.get("objtype"),
                objname=sensor.attrib.get("objname"),
            )
        )
    return sensors


def _parse_pair(value: str | None, field_name: str) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    parsed = _parse_float_sequence(value, field_name, expected_count=2)
    return parsed[0], parsed[1]


def _parse_triplet(value: str | None, field_name: str) -> tuple[float, float, float] | None:
    if value is None:
        return None
    parsed = _parse_float_sequence(value, field_name, expected_count=3)
    return parsed[0], parsed[1], parsed[2]


def _parse_quad(value: str | None, field_name: str) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parsed = _parse_float_sequence(value, field_name, expected_count=4)
    return parsed[0], parsed[1], parsed[2], parsed[3]


def _parse_float_sequence(value: str, field_name: str, *, expected_count: int) -> tuple[float, ...]:
    parts = value.split()
    if len(parts) != expected_count:
        _raise_numeric_parse_failed(field_name, value, f"{expected_count} numeric values")
    try:
        return tuple(float(part) for part in parts)
    except ValueError as exc:
        raise LabError(
            "XML_NUMERIC_PARSE_FAILED",
            f"Could not parse numeric value for {field_name}: {value!r}",
            "Fix numeric MJCF attributes before generating a contract.",
            exit_code=1,
        ) from exc


def _parse_optional_float(value: str | None, field_name: str) -> float | None:
    if value is None:
        return None
    return _parse_float(value, field_name)


def _parse_float(value: str, field_name: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise LabError(
            "XML_NUMERIC_PARSE_FAILED",
            f"Could not parse numeric value for {field_name}: {value!r}",
            "Fix numeric MJCF attributes before generating a contract.",
            exit_code=1,
        ) from exc


def _parse_optional_bool(value: str | None, field_name: str) -> bool | None:
    if value is None:
        return None
    normalized = value.lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise LabError(
        "XML_BOOLEAN_PARSE_FAILED",
        f"Could not parse boolean value for {field_name}: {value!r}",
        "Use true, false, 1, or 0 for MJCF boolean attributes.",
        exit_code=1,
    )


def _raise_numeric_parse_failed(field_name: str, value: str, expected: str) -> NoReturn:
    raise LabError(
        "XML_NUMERIC_PARSE_FAILED",
        f"Could not parse numeric value for {field_name}: expected {expected}, got {value!r}",
        "Fix numeric MJCF attributes before generating a contract.",
        exit_code=1,
    )
