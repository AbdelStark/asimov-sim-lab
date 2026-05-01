# Contributing

Asimov Sim Lab is contract-first. Do not add product surface that outruns the executable contracts.

## Setup

Read `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/spec/PRODUCT-SPEC.md` before changing behavior.

```bash
uv sync --extra dev
```

Use a local upstream checkout only:

```bash
export ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1
```

Do not commit `.asimov-sim-lab/`, generated local reports, absolute machine paths, or upstream Asimov assets.

## Required Checks

```bash
make check
```

The authoritative gates are:
- lockfile check
- Ruff format/check
- mypy strict typing
- pytest with 90% package coverage
- generated schema drift check
- package build
- lightweight dependency audit

## Fixture Rules

- CI fixtures must be tiny and synthetic.
- Mimic the supported `sim-model/` layout and Asimov-like names.
- Do not copy upstream XML or mesh assets into this repo.
- Mesh fixtures should be valid minimal ASCII STL files.
- Broken fixtures should prove typed failure codes, not incidental exceptions.

## Schema Rules

Pydantic models are the implementation source. Committed JSON Schemas are generated artifacts:

```bash
make schemas-update
make schemas
```

If a public JSON field changes, update docs and schema files in the same change.

## Documentation Rules

- Update `CHANGELOG.md` for user-visible changes.
- Update `README.md` when commands, status, limitations, or setup change.
- Update `docs/ARCHITECTURE.md` when module boundaries, data flow, or invariants change.
- Keep deferred commands out of command help, quickstarts, and examples until they are implemented.

## Claim Rules

- Do not claim official upstream affiliation.
- Do not claim hardware fidelity, manufacturing readiness, electrical safety, or policy performance.
- Do not present presets as validated physical motions.
- Keep README quickstart commands limited to behavior that actually works.
