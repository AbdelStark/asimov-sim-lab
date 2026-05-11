# RFC-0009: Pipeline Context

## Status

Proposed. Not yet implemented. Targets the next minor release after `0.1.0`.

## Abstract

Every top-level command in Asimov Sim Lab walks the same upstream chain — asset-root resolution, manifest generation, MJCF parse, inspect contract, validation, optional runtime smoke — and the orchestrating commands (`evidence`, `export`, `open`) chain several of those together. The current implementation re-derives every intermediate result from scratch at every layer, so a single `evidence` invocation parses the primary XML 4–5 times and recomputes the SHA-256 of every mesh file 4 times. This RFC proposes a typed, internal `PipelineContext` that carries already-computed upstream results so downstream functions can reuse them.

## Motivation

### Observed redundancy

A single `evidence` run currently executes the following call graph (simplified, showing only the expensive operations):

```
generate_evidence_bundle(resolution)
  ├── generate_asset_manifest(resolution)          # XML parse + N mesh SHA-256
  ├── inspect_model(resolution)
  │     └── generate_asset_manifest(resolution)    # XML parse + N mesh SHA-256  ← duplicate
  ├── validate_model(resolution)
  │     └── inspect_model(resolution)
  │           └── generate_asset_manifest(resolution)  # XML parse + N mesh SHA-256  ← duplicate
  │     └── parse_mjcf(xml_path)                   # 4th XML parse on the same file
  └── run_runtime_smoke(resolution)
        └── generate_asset_manifest(resolution)    # XML parse + N mesh SHA-256  ← duplicate
```

For the real Asimov-v1 humanoid (≈50 STL files, ~1 MB each):

- XML parsed 4 times per invocation.
- ~200 MB of redundant mesh SHA-256 computation per invocation.
- `git status` + `git ls-files` re-run several times via `paths.source_locator` → `read_git_metadata`.

The hottest gain is on `export` (which also calls `generate_evidence_bundle` and then re-runs the pipeline a second time with deterministic timestamps). One `export` invocation can produce 6–8 redundant manifest builds.

### Why it stayed unfixed

The current shape is contract-clean: every public function is callable on its own from the Python API, takes a single `AssetRootResolution`, and returns its full schema-backed result. That property must not regress. Memoization on a global cache breaks process isolation and creates invalidation traps. The right shape is an explicit, optional context object threaded through the call chain.

## Non-Goals

- No cross-process or on-disk cache. The context is scoped to a single command invocation.
- No change to any published Pydantic model or JSON Schema.
- No new public CLI flags. The CLI builds the context once internally and passes it down.
- No new error codes. The context's builder reuses the existing codes from the underlying functions.
- No async, concurrency, or parallelism. Out of scope.
- No public export of `PipelineContext` from `asimov_sim_lab.__init__`. It is an internal optimization surface, not a public contract.

## Proposed Shape

### The context object

```python
# src/asimov_sim_lab/_pipeline.py  (private)

from dataclasses import dataclass
from asimov_sim_lab.models import AssetManifest, InspectResult
from asimov_sim_lab.paths import AssetRootResolution

@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Already-computed upstream results, threaded through one command run.

    Internal. Never exported from `asimov_sim_lab.__init__`. Callers that
    construct one MUST treat its source assets as frozen for the duration of
    the call chain — mutating the on-disk checkout while a context is in flight
    is undefined behavior.
    """

    resolution: AssetRootResolution
    manifest: AssetManifest
    inspect_result: InspectResult

    @classmethod
    def build(cls, resolution: AssetRootResolution) -> "PipelineContext":
        from asimov_sim_lab.inspect import inspect_model
        from asimov_sim_lab.manifest import generate_asset_manifest

        manifest = generate_asset_manifest(resolution)
        # inspect_model currently recomputes the manifest internally; the
        # implementation phase will refactor it to accept a precomputed one.
        inspect_result = inspect_model(resolution, _manifest=manifest)
        return cls(resolution=resolution, manifest=manifest, inspect_result=inspect_result)
```

### Public function signatures

Every function that today recomputes upstream results gains an optional `context: PipelineContext | None = None` keyword-only parameter. When `None`, behavior is unchanged. When provided, the function reuses the cached fields instead of recomputing.

```python
def inspect_model(
    resolution: AssetRootResolution,
    *,
    context: PipelineContext | None = None,
) -> InspectResult: ...

def validate_model(
    resolution: AssetRootResolution,
    *,
    preset_dir: Path | None = None,
    strict: bool = False,
    context: PipelineContext | None = None,
) -> ValidationResult: ...

def run_runtime_smoke(
    resolution: AssetRootResolution,
    *,
    require_mujoco: bool = False,
    generated_at_utc: str | None = None,
    include_elapsed: bool = True,
    mujoco_module: MujocoModuleLike | None = None,
    context: PipelineContext | None = None,
) -> RuntimeSmokeResult: ...

def run_viewer_open_preflight(
    resolution: AssetRootResolution,
    *,
    preset_name: str | None = DEFAULT_VIEWER_PRESET,
    preset_dir: Path | None = None,
    strict: bool = False,
    require_clean_source: bool = False,
    require_license: bool = False,
    mujoco_module: MujocoModuleLike | None = None,
    context: PipelineContext | None = None,
) -> ViewerOpenResult: ...

def generate_evidence_bundle(
    resolution: AssetRootResolution,
    *,
    output_dir: Path,
    preset_dir: Path | None = None,
    strict: bool = False,
    overwrite: bool = False,
    bundle_dir_label: str | None = None,
    generated_at_utc: str | None = None,
    include_runtime_elapsed: bool = True,
    context: PipelineContext | None = None,
) -> EvidenceBundleResult: ...

def generate_export_package(
    resolution: AssetRootResolution,
    *,
    output_dir: Path,
    preset_dir: Path | None = None,
    strict: bool = False,
    overwrite: bool = False,
    package_name: str = DEFAULT_PACKAGE_NAME,
    deterministic: bool = True,
    context: PipelineContext | None = None,
) -> ExportPackageResult: ...
```

### CLI integration

Every CLI subcommand that runs more than one stage builds the context once at the top and passes it down. Single-stage subcommands (e.g., `doctor`) need no change.

```python
# cli.py:evidence_command
resolution = resolve_asset_root(...)
context = PipelineContext.build(resolution)
result = generate_evidence_bundle(resolution, ..., context=context)
```

### Internal contract

When `context is not None`:

- `generate_asset_manifest` is **not** called again; the function uses `context.manifest`.
- `inspect_model` is **not** called again; the function uses `context.inspect_result`.
- The XML is **not** re-parsed for the duration of the chain. Validation's internal `parse_mjcf` call can reuse `context.inspect_result` indirectly (validation derives most of its checks from `inspect_result`) and re-parse only for the geom-level checks that need raw `ET.Element` access. Future work may add a `context.xml_root` for full reuse.

When `context is None`, every function computes its own manifest/inspect locally, exactly as today. **No call site outside this package needs to change**.

## Invariants

- `PipelineContext` is frozen. Mutating it is a type error (slots + frozen).
- A function that accepts `context` must not also accept ad hoc precomputed-result kwargs (e.g., no `inspect_result=` parameter alongside `context=`). The context is the only handoff surface.
- The CLI builds exactly one context per command invocation.
- The context never crosses process boundaries. It is never serialized, pickled, or written to disk.
- Building a context still raises the same typed `LabError` codes that the underlying functions raise (`ASSET_ROOT_NOT_FOUND`, `XML_PARSE_FAILED`, `UNSUPPORTED_SOURCE_LAYOUT`, etc.) — there are no new error codes.
- A function called *with* a context produces a result with the same `schema_version`, `command`, and field-set as one called *without*. Output bytes must be identical for deterministic-mode runs.

## Determinism

The export pipeline's deterministic-byte guarantee is the most sensitive invariant in the project. The implementation phase must:

1. Run `make smoke-real` (or `make demo`) twice — once on `main`, once on the implementation branch — and `diff` the resulting evidence and export bundle artifacts. The diff must be empty on every JSON file, every Markdown file, and the tarball SHA-256.
2. Add a regression test in `tests/test_export_package.py` that builds a context, generates two export packages from the same resolution (one via context, one without), and asserts `archive_sha256` and `evidence_bundle_sha256` are byte-identical.

## Performance Target

Wall-clock improvement on the real Asimov-v1 humanoid (~50 STL files), measured via `time make smoke-real`:

| Run | Today | Target |
|---|---|---|
| `evidence` | baseline | **≥ 3× faster** |
| `export` | baseline | **≥ 4× faster** (export wraps evidence) |
| `inspect` | baseline | no change (single-stage) |
| `validate` | baseline | ~2× faster (skips one extra inspect) |

The implementation phase must record the actual before/after numbers in its commit message and CHANGELOG.

## Test Requirements

Implementation cannot merge without:

- A regression test that counts manifest builds via a `monkeypatch` on `generate_asset_manifest`: with a context, the orchestrator (`generate_evidence_bundle`) must call it exactly once.
- A regression test that counts XML parses via a `monkeypatch` on `_xml.parse_mjcf`: with a context, the orchestrator must call it exactly once.
- A determinism test as described above (byte-identical export bytes with and without context).
- Coverage of the no-context path for every public function (existing tests already cover this; new context-aware tests must not delete or weaken them).
- A test that proves `PipelineContext` is not exported from `asimov_sim_lab.__init__` (`assert "PipelineContext" not in asimov_sim_lab.__all__`).

## Documentation Requirements

Before shipping:

- `AGENTS.md` gains a single line under "Conventions": *"Use `PipelineContext` when chaining inspect → validate → runtime-smoke in one process; do not call upstream functions twice in the same command."*
- `docs/ARCHITECTURE.md` updates the "Data Flow" section to show the context object threading through the pipeline.
- `CHANGELOG.md` records the perf win under "Changed" (not "Added" — no new public surface) and explicitly notes that JSON output is byte-identical.
- This RFC moves from `Proposed` to `Accepted` in the same PR that lands the implementation.

## Out of Scope (Follow-Ups)

The following are deliberately deferred to a future RFC if the need arises:

- A `context.xml_root: ET.Element` field for validation's geom-level checks (would eliminate the last duplicate parse, currently in `validation._validate_*_references`).
- Public export of `PipelineContext` for external Python-API consumers (would commit to a stable contract; not worth doing until external callers actually exist).
- Cross-invocation caching keyed on `(asset_root, mtime)` (invalidation footgun; explicit per-invocation context is enough).
- Parallel execution of `validate_model` and `run_runtime_smoke` (different problem class; would need its own thread-safety review).

## Exit Criteria

The pipeline-context slice is ready when:

- Every orchestrator (`generate_evidence_bundle`, `generate_export_package`, `run_viewer_open_preflight`, CLI subcommands `evidence`, `export`, `open`) builds the context once and passes it down.
- A single `evidence` invocation calls `generate_asset_manifest` and `parse_mjcf` exactly once each (verified by tests).
- Export bytes are byte-identical to today's output on the same input.
- All existing tests pass with no flag, no skip, no quarantine.
- Performance targets are met and recorded.
- Docs are aligned per the section above.
- This RFC is marked `Accepted`.
