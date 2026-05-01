.PHONY: build check lint registry release-evidence-check schemas schemas-update security smoke-real test type

check: lint type schemas registry test build security

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

registry:
	uv run python scripts/check_error_registry.py --check

release-evidence-check:
	@test -n "$(ASIMOV_SIM_LAB_EXPORT_DIR)" || (echo "Set ASIMOV_SIM_LAB_EXPORT_DIR=/path/to/export-dir" && exit 2)
	uv run python scripts/check_release_evidence.py --export-dir "$(ASIMOV_SIM_LAB_EXPORT_DIR)"

build:
	uv build

security:
	uv run pip-audit --skip-editable

smoke-real:
	@test -n "$(ASIMOV_SIM_LAB_ASSET_ROOT)" || (echo "Set ASIMOV_SIM_LAB_ASSET_ROOT=/path/to/asimov-v1" && exit 2)
	uv run asimov-sim-lab doctor --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --format json
	uv run asimov-sim-lab inspect --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --json
	uv run asimov-sim-lab validate --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --format json
	uv run asimov-sim-lab runtime-smoke --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --allow-missing-mujoco --format json
	uv run asimov-sim-lab evidence --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --output-dir .asimov-sim-lab/smoke-real-evidence --overwrite --format json
	uv run asimov-sim-lab export --asset-root "$(ASIMOV_SIM_LAB_ASSET_ROOT)" --output-dir .asimov-sim-lab/smoke-real-export --overwrite --format json
	uv run python scripts/check_release_evidence.py --export-dir .asimov-sim-lab/smoke-real-export
