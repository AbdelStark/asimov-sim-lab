# RELEASE-CANDIDATE-DRY-RUN - Asimov Sim Lab

This report is generated from a locally verified export package. It records the
release evidence state without committing upstream XML, meshes, or local output paths.

## Evidence

- verdict: `not tag-ready`
- archive: `asimov-sim-lab-evidence.tar.gz`
- archive_sha256: `5e477a5e523ad238927b45ced428dbda26d4d1c41cb24a65734aecdb27b20109`
- archive_size_bytes: `7159`
- evidence_bundle_path: `evidence/evidence-bundle.json`
- evidence_bundle_sha256: `e606990b8122047c35467f2e53c38fd01aa72ec1a8184543a8699c2a11db11c4`
- package_manifest_path: `export-package-manifest.json`
- deterministic: `true`
- validation_passed: `true`
- validation_issue_count: `2`
- runtime_smoke_status: `warning`
- runtime_smoke_skipped: `true`
- evidence_generated_at_utc: `1970-01-01T00:00:00Z`

## Warnings

- `MUJOCO_NOT_INSTALLED: install the viewer extra to enable compiled-runtime smoke`
- `SOURCE_DIRTY: upstream checkout has uncommitted or untracked files`
- `UPSTREAM_LICENSE_NOT_FOUND: No recognized upstream license file found at checkout root.`

## Blockers

- source checkout is dirty; disclose or clean before tagging
- upstream root license is missing; disclose or resolve before tagging
- MuJoCo runtime smoke was skipped; disclose for source-contract alpha

## Verification

The export package passed:

```bash
uv run python scripts/check_release_evidence.py --export-dir <export-dir>
```
