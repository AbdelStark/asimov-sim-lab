"""Validation engine for source references and presets."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from asimov_sim_lab.errors import LabError
from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.models import InspectResult, Severity, Status, ValidationIssue, ValidationResult
from asimov_sim_lab.paths import MESH_DIR, PRIMARY_XML, STRICT_WARNING_CODES, AssetRootResolution
from asimov_sim_lab.presets import validate_presets


def validate_model(
    resolution: AssetRootResolution,
    *,
    preset_dir: Path | None = None,
    strict: bool = False,
) -> ValidationResult:
    """Validate the current source checkout against the MVP contracts."""
    inspect_result = inspect_model(resolution)
    issues = _warnings_to_issues(inspect_result.warnings, strict=strict)
    xml_path = resolution.asset_root / PRIMARY_XML
    root = _parse_xml(xml_path)

    issues.extend(_validate_mesh_references(root, resolution.asset_root))
    issues.extend(_validate_actuator_references(inspect_result))
    issues.extend(_validate_sensor_references(inspect_result))
    issues.extend(_validate_joint_ranges(inspect_result))
    issues.extend(validate_presets(inspect_result, preset_dir=preset_dir))

    passed = not any(issue.severity == "error" for issue in issues)
    status: Status = "ok" if not issues else "warning"
    if not passed:
        status = "error"
    return ValidationResult(
        status=status,
        warnings=[issue.message for issue in issues if issue.severity == "warning"],
        source_manifest_path=None,
        passed=passed,
        issue_count=len(issues),
        issues=issues,
        checked_paths=[
            PRIMARY_XML.as_posix(),
            MESH_DIR.as_posix(),
            "built-in:neutral",
            *(["preset-dir"] if preset_dir is not None else []),
        ],
    )


def _parse_xml(xml_path: Path) -> ET.Element:
    try:
        return ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise LabError(
            "XML_PARSE_FAILED",
            f"Could not parse MJCF XML: {xml_path}: {exc}",
            "Fix the XML before validation.",
            exit_code=1,
        ) from exc
    except OSError as exc:
        raise LabError(
            "PRIMARY_XML_NOT_FOUND",
            f"Could not read primary XML: {xml_path}: {exc}",
            "Pass the upstream Asimov checkout root that contains sim-model/xmls/asimov.xml.",
            exit_code=3,
        ) from exc


def _warnings_to_issues(warnings: list[str], *, strict: bool) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for warning in warnings:
        code = warning.split(":", maxsplit=1)[0] if ":" in warning else "WARNING"
        severity: Severity = "error" if strict and code in STRICT_WARNING_CODES else "warning"
        issues.append(ValidationIssue(code=code, severity=severity, message=warning))
    return issues


def _validate_mesh_references(root: ET.Element, asset_root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    asset = root.find("asset")
    mesh_assets: dict[str, str] = {}
    if asset is not None:
        for mesh in asset.findall("mesh"):
            name = mesh.attrib.get("name")
            file_name = mesh.attrib.get("file")
            if name is not None and file_name is not None:
                mesh_assets[name] = file_name
                if not (asset_root / MESH_DIR / file_name).is_file():
                    issues.append(
                        ValidationIssue(
                            code="MESH_REFERENCE_MISSING",
                            severity="error",
                            message=f"MJCF mesh file reference does not exist: {file_name}",
                            remediation=(
                                "Add the missing STL file or update the mesh file reference."
                            ),
                            relative_path=(MESH_DIR / file_name).as_posix(),
                            object_name=name,
                        )
                    )

    for geom in root.findall(".//geom"):
        mesh_name = geom.attrib.get("mesh")
        if mesh_name is not None and mesh_name not in mesh_assets:
            issues.append(
                ValidationIssue(
                    code="MESH_ASSET_REFERENCE_UNKNOWN",
                    severity="error",
                    message=f"Geom references unknown mesh asset: {mesh_name}",
                    remediation=(
                        "Declare the mesh in the MJCF asset section or fix the geom mesh reference."
                    ),
                    object_name=mesh_name,
                )
            )
    return issues


def _validate_actuator_references(inspect_result: InspectResult) -> list[ValidationIssue]:
    joint_names = {joint.name for joint in inspect_result.joints}
    issues: list[ValidationIssue] = []
    for actuator in inspect_result.actuators:
        if actuator.joint_name is None:
            issues.append(
                ValidationIssue(
                    code="ACTUATOR_TARGET_MISSING",
                    severity="warning",
                    message=f"Actuator {actuator.name!r} has no understood target reference.",
                    object_name=actuator.name,
                )
            )
        elif actuator.joint_name not in joint_names:
            issues.append(
                ValidationIssue(
                    code="ACTUATOR_JOINT_REFERENCE_MISSING",
                    severity="error",
                    message=(
                        f"Actuator {actuator.name!r} references unknown joint "
                        f"{actuator.joint_name!r}."
                    ),
                    remediation="Fix the actuator joint attribute or add the referenced joint.",
                    object_name=actuator.name,
                )
            )
    return issues


def _validate_sensor_references(inspect_result: InspectResult) -> list[ValidationIssue]:
    body_names = set(inspect_result.bodies)
    joint_names = {joint.name for joint in inspect_result.joints}
    site_names = {site.name for site in inspect_result.sites}
    camera_names = {camera.name for camera in inspect_result.cameras}
    mesh_names = {mesh.name for mesh in inspect_result.meshes}
    known_by_type = {
        "body": body_names,
        "joint": joint_names,
        "site": site_names,
        "camera": camera_names,
        "geom": mesh_names,
    }
    issues: list[ValidationIssue] = []
    for sensor in inspect_result.sensors:
        if sensor.site is not None and sensor.site not in site_names:
            issues.append(_sensor_missing(sensor.name, sensor.site, "site"))
        if sensor.body is not None and sensor.body not in body_names:
            issues.append(_sensor_missing(sensor.name, sensor.body, "body"))
        if sensor.objtype is not None and sensor.objname is not None:
            known = known_by_type.get(sensor.objtype)
            if known is not None and sensor.objname not in known:
                issues.append(_sensor_missing(sensor.name, sensor.objname, sensor.objtype))
    return issues


def _validate_joint_ranges(inspect_result: InspectResult) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for joint in inspect_result.joints:
        if joint.joint_type == "free":
            continue
        range_missing = joint.range_min is None or joint.range_max is None
        if joint.limited is True or not range_missing:
            if range_missing:
                issues.append(
                    ValidationIssue(
                        code="JOINT_RANGE_INVALID",
                        severity="error",
                        message=f"Joint {joint.name!r} has an invalid range declaration.",
                        object_name=joint.name,
                    )
                )
        elif joint.joint_type in {"hinge", "slide"}:
            issues.append(
                ValidationIssue(
                    code="JOINT_RANGE_MISSING",
                    severity="warning",
                    message=f"Joint {joint.name!r} has no declared finite range.",
                    object_name=joint.name,
                )
            )
    return issues


def _sensor_missing(sensor_name: str, target_name: str, target_type: str) -> ValidationIssue:
    return ValidationIssue(
        code="SENSOR_REFERENCE_MISSING",
        severity="error",
        message=f"Sensor {sensor_name!r} references unknown {target_type} {target_name!r}.",
        remediation="Fix the sensor reference or add the referenced MJCF object.",
        object_name=sensor_name,
    )
