"""Generate committed JSON Schemas from public Pydantic contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel

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


def _schema_content(model: type[BaseModel]) -> str:
    schema = model.model_json_schema()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify committed schemas match generated content without writing files.",
    )
    args = parser.parse_args()

    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    mismatches: list[Path] = []
    for filename, model in SCHEMAS.items():
        path = SCHEMA_DIR / filename
        content = _schema_content(model)
        if args.check:
            try:
                existing = path.read_text(encoding="utf-8")
            except OSError:
                mismatches.append(path)
                continue
            if existing != content:
                mismatches.append(path)
        else:
            path.write_text(content, encoding="utf-8")

    if mismatches:
        for path in mismatches:
            print(f"schema out of date: {path.relative_to(ROOT)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
