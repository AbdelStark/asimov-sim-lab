# RELEASE-CANDIDATE-EVIDENCE-POLICY — Asimov Sim Lab

## Purpose

A release candidate is not ready because the tests passed once. It is ready when the exact code, schemas, source checkout, generated evidence, and export archive form a reviewable chain.

This policy defines the minimum evidence package required before tagging or publishing an alpha release.

## Release Candidate Inputs

Required local inputs:

- clean tracked working tree in `asimov-sim-lab`
- generated schemas committed and current
- no committed `.env`, `.asimov-sim-lab/`, upstream XML, upstream meshes, or local evidence outputs
- explicit upstream source root for real-upstream evidence, provided through `ASIMOV_SIM_LAB_ASSET_ROOT`
- operator decision on whether missing MuJoCo is acceptable for the candidate

The project still supports local checkout only. Do not download or vendor upstream assets during release prep.

## Required Local Gates

Run from the repository root:

```bash
make check
```

Run real-upstream evidence generation:

```bash
ASIMOV_SIM_LAB_ASSET_ROOT=/absolute/path/to/asimov-v1 make smoke-real
```

`make smoke-real` writes:

- `.asimov-sim-lab/smoke-real-evidence/`
- `.asimov-sim-lab/smoke-real-export/`

Both directories are ignored local state. Review them before publishing or attaching them.

## Export Package Verification

Every release-candidate export directory must pass:

```bash
uv run python scripts/check_release_evidence.py \
  --export-dir .asimov-sim-lab/smoke-real-export
```

The checker verifies:

- `export-package-result.json` exists and is readable
- archive, manifest, and evidence-bundle checksums match the recorded values
- every package file listed in `export-package-manifest.json` exists and matches its size and SHA-256
- archive members match the package manifest
- archive members use deterministic metadata: regular files, `mtime=0`, `uid=0`, `gid=0`
- evidence bundle validation passed and runtime smoke did not produce `status=error`

## What To Attach To A Release Candidate

Attach or preserve:

- `export-package-result.json`
- `export-package-manifest.json`
- `asimov-sim-lab-evidence.tar.gz`
- command transcript or CI link showing `make check`
- command transcript or CI/local log showing `check_release_evidence.py` passed

Do not attach raw `.asimov-sim-lab/smoke-real-evidence/` without reviewing local absolute paths in provenance fields.

## Runtime Smoke Policy

`runtime-smoke` has three release meanings:

- `status=ok`: MuJoCo is installed and compiled the MJCF without warnings.
- `status=warning`, `skipped=true`, `MUJOCO_NOT_INSTALLED`: acceptable for source-contract-only alpha candidates when documented in the release notes.
- `status=error`: blocks a release candidate until fixed or explicitly scoped out with maintainer approval.

Runtime smoke does not simulate, step, score, or validate controller behavior.

## Blocking Conditions

Do not tag or publish if any of these are true:

- `make check` fails
- generated schemas are out of date
- `scripts/check_error_registry.py --check` fails
- `scripts/check_release_evidence.py --export-dir ...` fails
- export evidence has `validation_passed=false`
- export evidence has `runtime_smoke_status=error`
- source checkout provenance is dirty or unlicensed and the release notes do not explicitly disclose it
- release notes claim viewer, capture, controller, policy, hardware, safety, or manufacturing readiness

## Review Checklist

- [ ] `git status --short --branch` reviewed
- [ ] `make check` passed
- [ ] real-upstream `make smoke-real` passed
- [ ] export package checker passed
- [ ] `export-package-result.json` archive SHA-256 recorded in release notes
- [ ] runtime smoke status documented
- [ ] known warnings documented
- [ ] `CHANGELOG.md` reflects user-visible changes
- [ ] README status still matches shipped behavior

## CI Retention

CI generates fixture-backed `.asimov-sim-lab/ci-evidence/` and `.asimov-sim-lab/ci-export/` artifacts on supported Python versions. Those artifacts prove the package contract against synthetic fixtures. They do not replace real-upstream evidence from a local Asimov checkout.
