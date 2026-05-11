"""Shared MJCF XML helpers.

Internal module: not part of the public API surface. Centralizes the XML parse
entry point so `inspect` and `validation` cannot drift on error codes or
remediation strings.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from asimov_sim_lab.errors import LabError


def parse_mjcf(xml_path: Path) -> ET.Element:
    """Parse a primary MJCF XML file into its root element."""
    try:
        return ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise LabError(
            "XML_PARSE_FAILED",
            f"Could not parse MJCF XML: {xml_path}: {exc}",
            "Fix the XML before parsing the model contract.",
            exit_code=1,
        ) from exc
    except OSError as exc:
        raise LabError(
            "PRIMARY_XML_NOT_FOUND",
            f"Could not read primary XML: {xml_path}: {exc}",
            "Pass the upstream Asimov checkout root that contains sim-model/xmls/asimov.xml.",
            exit_code=3,
        ) from exc
