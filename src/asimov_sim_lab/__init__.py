"""Asimov Sim Lab — schema-backed inspection and validation for MuJoCo robot models.

This package exposes a stable, typed Python API mirroring the CLI surface:

- :func:`resolve_asset_root` — locate the upstream checkout (CLI / profile / env).
- :func:`generate_asset_manifest` — checksummed manifest of XML and mesh assets.
- :func:`inspect_model` — parse the MJCF into an :class:`InspectResult` contract.
- :func:`validate_model` — static validation of references, ranges, and presets.
- :func:`run_runtime_smoke` — optional MuJoCo compile smoke check.
- :func:`run_viewer_open_preflight` — schema-backed viewer preflight.
- :func:`generate_evidence_bundle` — checksummed artifact directory.
- :func:`generate_export_package` — deterministic ``.tar.gz`` archive.

All result types are Pydantic v2 models with corresponding JSON Schemas under
``docs/schemas/``. JSON is the source of truth; text and Markdown renderings are
derived from it.
"""

__version__ = "0.1.0"

from asimov_sim_lab.evidence import generate_evidence_bundle
from asimov_sim_lab.export import generate_export_package
from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.models import (
    AssetManifest,
    DoctorResult,
    EvidenceBundleResult,
    ExportPackageResult,
    InspectResult,
    RuntimeSmokeResult,
    ValidationResult,
    ViewerOpenResult,
)
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.runtime import run_runtime_smoke
from asimov_sim_lab.validation import validate_model
from asimov_sim_lab.viewer import run_viewer_open_preflight

__all__ = [
    "AssetManifest",
    "DoctorResult",
    "EvidenceBundleResult",
    "ExportPackageResult",
    "InspectResult",
    "RuntimeSmokeResult",
    "ValidationResult",
    "ViewerOpenResult",
    "__version__",
    "generate_asset_manifest",
    "generate_evidence_bundle",
    "generate_export_package",
    "inspect_model",
    "resolve_asset_root",
    "run_runtime_smoke",
    "run_viewer_open_preflight",
    "validate_model",
]
