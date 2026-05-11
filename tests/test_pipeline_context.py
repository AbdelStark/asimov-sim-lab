"""Regression tests for RFC-0009 PipelineContext.

Asserts the perf invariants (manifest + XML parse called exactly once per
orchestrator invocation when a context is provided), the determinism
guarantee (output bytes identical with and without context), and the API
boundary (PipelineContext is not part of the public package surface).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import asimov_sim_lab
from asimov_sim_lab import evidence as evidence_module
from asimov_sim_lab import export as export_module
from asimov_sim_lab import inspect as inspect_module
from asimov_sim_lab import manifest as manifest_module
from asimov_sim_lab import runtime as runtime_module
from asimov_sim_lab import validation as validation_module
from asimov_sim_lab._pipeline import PipelineContext
from asimov_sim_lab.evidence import generate_evidence_bundle
from asimov_sim_lab.export import generate_export_package
from asimov_sim_lab.paths import resolve_asset_root

if TYPE_CHECKING:
    pass


def test_pipeline_context_is_not_public() -> None:
    # The internal optimization surface must not leak into the public package
    # contract; external callers should not depend on it.
    assert "PipelineContext" not in asimov_sim_lab.__all__
    assert not hasattr(asimov_sim_lab, "PipelineContext")


def test_evidence_with_context_builds_manifest_exactly_once(
    minimal_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # RFC-0009 exit criterion: one `evidence` invocation must call
    # generate_asset_manifest exactly once when a context is provided.
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    context = PipelineContext.build(resolution)

    real = manifest_module.generate_asset_manifest
    calls: list[None] = []

    def counting(*args: object, **kwargs: object) -> object:
        calls.append(None)
        return real(*args, **kwargs)

    # Patch every binding through which the orchestrator might reach the manifest.
    monkeypatch.setattr(manifest_module, "generate_asset_manifest", counting)
    monkeypatch.setattr(inspect_module, "generate_asset_manifest", counting)
    monkeypatch.setattr(runtime_module, "generate_asset_manifest", counting)

    generate_evidence_bundle(
        resolution, output_dir=tmp_path / "bundle", overwrite=True, context=context
    )

    assert len(calls) == 0, (
        f"manifest must not be rebuilt when a context is provided; saw {len(calls)} calls"
    )


def test_evidence_with_context_parses_xml_exactly_once(
    minimal_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Companion to the manifest test: parse_mjcf must be called zero extra
    # times when a context is provided (the context already holds xml_root).
    from asimov_sim_lab import _xml as xml_module

    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    context = PipelineContext.build(resolution)

    real = xml_module.parse_mjcf
    calls: list[Path] = []

    def counting(path: Path) -> object:
        calls.append(path)
        return real(path)

    # Patch every module that imported parse_mjcf as a local alias.
    monkeypatch.setattr(xml_module, "parse_mjcf", counting)
    monkeypatch.setattr(inspect_module, "_parse_xml", counting)
    monkeypatch.setattr(validation_module, "_parse_xml", counting)

    generate_evidence_bundle(
        resolution, output_dir=tmp_path / "bundle", overwrite=True, context=context
    )

    assert len(calls) == 0, (
        f"XML must not be re-parsed when a context is provided; saw {len(calls)} parses"
    )


def test_export_bytes_identical_with_and_without_context(
    minimal_source: Path, tmp_path: Path
) -> None:
    # RFC-0009 determinism guarantee: an export package built via a precomputed
    # context must produce byte-identical archive and bundle SHA-256 to one
    # built without a context. Any drift here breaks the deterministic-output
    # contract that downstream verification scripts rely on.
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})

    without_context = generate_export_package(
        resolution, output_dir=tmp_path / "no-ctx", overwrite=True, deterministic=True
    )
    with_context = generate_export_package(
        resolution,
        output_dir=tmp_path / "with-ctx",
        overwrite=True,
        deterministic=True,
        context=PipelineContext.build(resolution),
    )

    assert with_context.archive_sha256 == without_context.archive_sha256
    assert with_context.evidence_bundle_sha256 == without_context.evidence_bundle_sha256
    assert with_context.package_manifest_sha256 == without_context.package_manifest_sha256


def test_inspect_with_context_returns_cached_result(minimal_source: Path) -> None:
    # inspect_model with a context must return the exact same object reference
    # the context was built with — no re-parse, no copy.
    resolution = resolve_asset_root(asset_root=minimal_source, profile_path=None, env={})
    context = PipelineContext.build(resolution)

    from asimov_sim_lab.inspect import inspect_model

    result = inspect_model(resolution, context=context)

    assert result is context.inspect_result


# Anchor the unused-import noqa so the module's intentional re-exports stay
# explicit even though the tests use them only via getattr / patching.
_ = (evidence_module, export_module)
