from __future__ import annotations

import os
from pathlib import Path

import pytest

from asimov_sim_lab.inspect import inspect_model
from asimov_sim_lab.paths import ENV_ASSET_ROOT, resolve_asset_root
from asimov_sim_lab.runtime import run_runtime_smoke
from asimov_sim_lab.validation import validate_model


@pytest.mark.skipif(ENV_ASSET_ROOT not in os.environ, reason=f"{ENV_ASSET_ROOT} is not set")
def test_optional_real_upstream_smoke() -> None:
    resolution = resolve_asset_root(asset_root=Path(os.environ[ENV_ASSET_ROOT]), profile_path=None)

    inspect_result = inspect_model(resolution)
    validation_result = validate_model(resolution)
    runtime_result = run_runtime_smoke(resolution)

    assert inspect_result.joint_count > 0
    assert inspect_result.mesh_count > 0
    assert validation_result.passed
    assert runtime_result.status in {"ok", "warning"}
