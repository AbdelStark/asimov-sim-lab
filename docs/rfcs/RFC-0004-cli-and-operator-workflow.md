# RFC-0004: CLI and Operator Workflow

## Abstract
The first operator surface should be a direct, scriptable CLI rather than a GUI-first workflow.

## Required properties
- discoverable commands
- deterministic stdout/stderr for CI use
- file-based outputs where relevant
- clear non-zero exit codes for validation failures

## Initial commands
- `doctor`
- `inspect`
- `validate`
- `runtime-smoke`
- `evidence`
- `export`

Deferred commands such as `open`, `capture`, or preset management require their own contracts, tests, and schemas before they appear in the CLI.

`open` now has a draft contract in `RFC-0008-viewer-open-contract.md`; it remains deferred until its schema, failure codes, tests, and optional-runtime behavior are implemented.
