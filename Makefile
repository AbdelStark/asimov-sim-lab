.PHONY: build check lint schemas schemas-update security smoke-real test type

check: lint type schemas test build security

lint:
	uv run ruff format --check .
	uv run ruff check .

type:
	uv run mypy

test:
	uv run pytest

schemas:
	uv run python scripts/generate_schemas.py --check

schemas-update:
	uv run python scripts/generate_schemas.py

build:
	uv build

security:
	uv run pip-audit --skip-editable

smoke-real:
	@test -n "$(ASIMOV_SIM_LAB_ASSET_ROOT)" || (echo "Set ASIMOV_SIM_LAB_ASSET_ROOT=/path/to/asimov-v1" && exit 2)
	uv run asimov-sim-lab doctor --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --format json
	uv run asimov-sim-lab inspect --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --json
	uv run asimov-sim-lab validate --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --format json
	uv run asimov-sim-lab evidence --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --output-dir .asimov-sim-lab/smoke-real-evidence --overwrite --format json
