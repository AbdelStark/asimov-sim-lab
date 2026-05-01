# RFC-0006: Evidence and Export Contract

## Abstract
Every serious run should produce inspectable artifacts that future users and reviewers can trust.

## Requirements
- outputs include timestamps and source provenance
- outputs are file-based first
- exported data is diffable and testable
- demo artifacts should be reproducible from documented commands
- evidence bundles list SHA-256 digests for every generated review artifact
- non-empty evidence directories require explicit overwrite intent
