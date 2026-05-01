from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import validate as validate_json_schema

from asimov_sim_lab.evidence import generate_evidence_bundle
from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.manifest import generate_asset_manifest
from asimov_sim_lab.paths import resolve_asset_root
from asimov_sim_lab.validation import validate_model


def test_committed_json_schemas_are_current() -> None:
    subprocess.run(
        [sys.executable, "scripts/generate_schemas.py", "--check"],
        check=True,
    )


def test_outputs_validate_against_committed_schemas(minimal_source: Path, tmp_path: Path) -> None:
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    manifest = json.loads(generate_asset_manifest(resolution).model_dump_json())
    inspect_result = json.loads(inspect_model(resolution).model_dump_json())
    validation_result = json.loads(validate_model(resolution).model_dump_json())
    evidence_result = json.loads(
        generate_evidence_bundle(resolution, output_dir=tmp_path / "evidence").model_dump_json()
    )

    schema_dir = Path("docs/schemas")
    validate_json_schema(
        manifest, json.loads((schema_dir / "asset-manifest.schema.json").read_text())
    )
    validate_json_schema(
        inspect_result, json.loads((schema_dir / "inspect-result.schema.json").read_text())
    )
    validate_json_schema(
        validation_result,
        json.loads((schema_dir / "validation-result.schema.json").read_text()),
    )
    validate_json_schema(
        evidence_result,
        json.loads((schema_dir / "evidence-bundle-result.schema.json").read_text()),
    )
