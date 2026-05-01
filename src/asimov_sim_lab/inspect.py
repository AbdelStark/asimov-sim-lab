"""MJCF inspection contract extraction."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from asimov_sim_lab.errors import LabError
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    ActuatorContract,
    CameraContract,
    InspectResult,
    JointContract,
    MeshAssetContract,
    SensorContract,
    SiteContract,
    Status,
)
from asimov_sim_lab.paths import MESH_DIR, PRIMARY_XML, AssetRootResolution


def inspect_model(resolution: AssetRootResolution) -> InspectResult:
    """Parse the supported MJCF entrypoint into a stable contract."""
    manifest = generate_asset_manifest(resolution)
    xml_path = resolution.asset_root / PRIMARY_XML
    root = _parse_xml(xml_path)

    warnings = list(manifest.warnings)
    compiler_meshdir = _compiler_meshdir(root, xml_path, resolution.asset_root)
    if compiler_meshdir.warning is not None:
        warnings.append(compiler_meshdir.warning)
    if compiler_meshdir.error is not None:
        warnings.append(compiler_meshdir.error)

    meshes = _mesh_assets(root)
    missing_meshes = _missing_mesh_files(meshes, compiler_meshdir.mesh_dir)
    for missing in missing_meshes:
        warnings.append(
            f"MESH_REFERENCE_MISSING: mesh file referenced by MJCF is missing: {missing}"
        )

    bodies: list[str] = []
    joints: list[JointContract] = []
    cameras: list[CameraContract] = []
    sites: list[SiteContract] = []
    total_mass = 0.0
    mass_count = 0

    worldbody = root.find("worldbody")
    if worldbody is not None:
        for body in worldbody.findall("body"):
            body_mass, body_mass_count = _walk_body(body, bodies, joints, cameras, sites)
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
        camera_count=len(cameras),
        site_count=len(sites),
        total_declared_mass_kg=round(total_mass, 12) if mass_count else None,
        bodies=bodies,
        meshes=meshes,
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
    for camera in result.cameras:
        lines.append(
            f"| {camera.name} | {camera.body} | {camera.mode or ''} | {camera.fovy or ''} |"
        )
    return "\n".join(lines) + "\n"


class _MeshdirResolution:
    def __init__(
        self, mesh_dir: Path, warning: str | None = None, error: str | None = None
    ) -> None:
        self.mesh_dir = mesh_dir
        self.warning = warning
        self.error = error


def _parse_xml(xml_path: Path) -> ET.Element:
    try:
        return ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise LabError(
            "XML_PARSE_FAILED",
            f"Could not parse MJCF XML: {xml_path}: {exc}",
            "Fix the XML before generating an inspect contract.",
            exit_code=1,
        ) from exc
    except OSError as exc:
        raise LabError(
            "PRIMARY_XML_NOT_FOUND",
            f"Could not read primary XML: {xml_path}: {exc}",
            "Pass the upstream Asimov checkout root that contains sim-model/xmls/asimov.xml.",
            exit_code=3,
        ) from exc


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
        return _MeshdirResolution(
            supported,
            error=(
                "UNSUPPORTED_SOURCE_LAYOUT: compiler@meshdir resolves outside the supported "
                f"MVP mesh directory: {resolved}"
            ),
        )
    return _MeshdirResolution(resolved)


def _mesh_assets(root: ET.Element) -> list[MeshAssetContract]:
    asset = root.find("asset")
    if asset is None:
        return []
    meshes: list[MeshAssetContract] = []
    for index, mesh in enumerate(asset.findall("mesh")):
        file_name = mesh.attrib.get("file")
        if file_name is None:
            continue
        name = mesh.attrib.get("name", f"mesh_{index}")
        meshes.append(MeshAssetContract(name=name, file=file_name))
    return meshes


def _missing_mesh_files(meshes: list[MeshAssetContract], mesh_dir: Path) -> list[str]:
    missing: list[str] = []
    for mesh in meshes:
        if not (mesh_dir / mesh.file).is_file():
            missing.append(mesh.file)
    return missing


def _walk_body(
    body: ET.Element,
    bodies: list[str],
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
        mass_sum += _parse_float(inertial.attrib["mass"])
        mass_count += 1

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
        range_min, range_max = _parse_pair(joint.attrib.get("range"))
        joints.append(
            JointContract(
                name=joint.attrib.get("name", ""),
                body=body_name,
                joint_type=joint.attrib.get("type", "hinge"),
                axis=_parse_triplet(joint.attrib.get("axis")),
                range_min=range_min,
                range_max=range_max,
                ref=_parse_optional_float(joint.attrib.get("ref")),
                limited=_parse_optional_bool(joint.attrib.get("limited")),
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
                pos=_parse_triplet(camera.attrib.get("pos")),
                quat=_parse_quad(camera.attrib.get("quat")),
                fovy=_parse_optional_float(camera.attrib.get("fovy")),
            )
        )
    for site in body.findall("site"):
        site_name = site.attrib.get("name")
        if site_name is None:
            continue
        sites.append(
            SiteContract(name=site_name, body=body_name, pos=_parse_triplet(site.attrib.get("pos")))
        )
    for child in body.findall("body"):
        child_mass, child_count = _walk_body(child, bodies, joints, cameras, sites)
        mass_sum += child_mass
        mass_count += child_count
    return mass_sum, mass_count


def _actuators(root: ET.Element) -> list[ActuatorContract]:
    actuator_root = root.find("actuator")
    if actuator_root is None:
        return []
    actuators: list[ActuatorContract] = []
    for index, actuator in enumerate(list(actuator_root)):
        ctrl_min, ctrl_max = _parse_pair(actuator.attrib.get("ctrlrange"))
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


def _parse_pair(value: str | None) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    parts = value.split()
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def _parse_triplet(value: str | None) -> tuple[float, float, float] | None:
    if value is None:
        return None
    parts = value.split()
    if len(parts) != 3:
        return None
    try:
        return float(parts[0]), float(parts[1]), float(parts[2])
    except ValueError:
        return None


def _parse_quad(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parts = value.split()
    if len(parts) != 4:
        return None
    try:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except ValueError:
        return None


def _parse_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    return _parse_float(value)


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise LabError(
            "XML_NUMERIC_PARSE_FAILED",
            f"Could not parse numeric value {value!r}",
            "Fix numeric MJCF attributes before generating a contract.",
            exit_code=1,
        ) from exc


def _parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    return None
