"""Internal pipeline context for sharing upstream results across one command run.

Private. Never exported from :mod:`asimov_sim_lab`. The dataclass carries the
results that every command derives from the same source checkout — the asset
manifest, the parsed MJCF root, and the inspect contract — so downstream
functions can reuse them instead of recomputing.

Constructing a context reads the on-disk checkout once. Mutating those files
while a context is in flight is undefined behaviour: the cached results will
not reflect the change until a new context is built.

See ``docs/rfcs/RFC-0009-pipeline-context.md`` for the contract.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from asimov_sim_lab.models import AssetManifest, InspectResult
from asimov_sim_lab.paths import PRIMARY_XML, AssetRootResolution


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Already-computed upstream results, scoped to one command invocation."""

    resolution: AssetRootResolution
    manifest: AssetManifest
    inspect_result: InspectResult
    xml_root: ET.Element

    @classmethod
    def build(cls, resolution: AssetRootResolution) -> PipelineContext:
        """Read the checkout once and assemble all reusable upstream results."""
        # Imports are local to avoid a module-load-time cycle:
        # inspect -> manifest -> paths is fine, but pipeline -> inspect -> pipeline isn't.
        from asimov_sim_lab._xml import parse_mjcf
        from asimov_sim_lab.inspect import _inspect_from_root
        from asimov_sim_lab.manifest import generate_asset_manifest

        manifest = generate_asset_manifest(resolution)
        xml_root = parse_mjcf(resolution.asset_root / PRIMARY_XML)
        inspect_result = _inspect_from_root(xml_root, manifest, resolution)
        return cls(
            resolution=resolution,
            manifest=manifest,
            inspect_result=inspect_result,
            xml_root=xml_root,
        )
