# RFC-0006: Evidence and Export Contract

## Abstract
Every serious run should produce inspectable artifacts that future users and reviewers can trust.

## Requirements
- outputs include timestamps and source provenance
- outputs are file-based first
- exported data is diffable and testable
- demo artifacts should be reproducible from documented commands
- evidence bundles list SHA-256 digests for every generated review artifact
- evidence bundles include optional runtime smoke results, including explicit skipped state when MuJoCo is not installed
- non-empty evidence directories require explicit overwrite intent
- export packages include a portable evidence directory, package manifest, and deterministic `tar.gz` archive
- deterministic export packages normalize generated timestamps, tar metadata, gzip metadata, owner IDs, and evidence bundle output paths
- export package results record archive SHA-256 and link back to `evidence/evidence-bundle.json`

## Non-goals
- archive upstream meshes or XML outside the generated evidence artifacts
- remove source provenance from JSON contracts
- claim simulation correctness, controller behavior, or hardware fidelity from runtime smoke
