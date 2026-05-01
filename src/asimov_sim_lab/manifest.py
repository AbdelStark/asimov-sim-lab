"""Asset manifest generation."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from asimov_sim_lab.errors import LabError
from asimov_sim_lab.models import AssetManifest, MeshEntry, XmlEntry
from asimov_sim_lab.paths import (
    MESH_DIR,
    PRIMARY_XML,
    SIM_MODEL_README,
    AssetRootResolution,
    layout_checks,
    source_locator,
)


def generate_asset_manifest(resolution: AssetRootResolution) -> AssetManifest:
    """Generate a fresh manifest for a supported local checkout."""
    asset_root = resolution.asset_root
    checks = layout_checks(asset_root)
    errors = [check for check in checks if check.status == "error"]
    if errors:
        first = errors[0]
        raise LabError(
            first.code or "UNSUPPORTED_SOURCE_LAYOUT",
            first.detail,
            "Pass the upstream Asimov checkout root that contains sim-model/.",
            exit_code=3,
        )

    source, warnings = source_locator(resolution)
    for check in checks:
        if check.status == "warning":
            warning = check.code or check.detail
            warnings.append(f"{warning}: {check.detail}")

    primary_xml_path = asset_root / PRIMARY_XML
    mesh_dir = asset_root / MESH_DIR
    referenced = _mesh_file_references(primary_xml_path)
    meshes = [
        MeshEntry(
            relative_path=_relative(asset_root, path),
            sha256=_sha256(path),
            size_bytes=path.stat().st_size,
            referenced_by=sorted(referenced.get(path.name, [])),
        )
        for path in _mesh_files(mesh_dir)
    ]

    return AssetManifest(
        source=source,
        primary_xml=XmlEntry(
            relative_path=str(PRIMARY_XML),
            sha256=_sha256(primary_xml_path),
            size_bytes=primary_xml_path.stat().st_size,
        ),
        meshes=meshes,
        readme_path=str(SIM_MODEL_README) if (asset_root / SIM_MODEL_README).is_file() else None,
        warnings=sorted(set(warnings)),
    )


def _mesh_files(mesh_dir: Path) -> list[Path]:
    return sorted(
        path for path in mesh_dir.iterdir() if path.is_file() and path.suffix.lower() == ".stl"
    )


def _mesh_file_references(primary_xml_path: Path) -> dict[str, list[str]]:
    try:
        root = ET.parse(primary_xml_path).getroot()
    except ET.ParseError:
        return {}
    references: dict[str, list[str]] = {}
    asset = root.find("asset")
    if asset is None:
        return references
    for mesh in asset.findall("mesh"):
        file_name = mesh.attrib.get("file")
        mesh_name = mesh.attrib.get("name", file_name)
        if file_name is None or mesh_name is None:
            continue
        references.setdefault(file_name, []).append(mesh_name)
    return references


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise LabError(
            "CHECKSUM_COMPUTE_FAILED",
            f"Could not compute checksum for {path}: {exc}",
            "Check file permissions and rerun the command.",
            exit_code=3,
        ) from exc
    return hasher.hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
