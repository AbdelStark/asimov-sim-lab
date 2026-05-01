"""Generate committed JSON Schemas from public Pydantic contracts."""

from __future__ import annotations

import json
from pathlib import Path

from asimov_sim_lab.models import (
    AssetManifest,
    DoctorResult,
    ErrorResult,
    InspectResult,
    ValidationResult,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "docs" / "schemas"
SCHEMAS = {
    "asset-manifest.schema.json": AssetManifest,
    "doctor-result.schema.json": DoctorResult,
    "error-result.schema.json": ErrorResult,
    "inspect-result.schema.json": InspectResult,
    "validation-result.schema.json": ValidationResult,
}


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS.items():
        schema = model.model_json_schema()
        path = SCHEMA_DIR / filename
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
