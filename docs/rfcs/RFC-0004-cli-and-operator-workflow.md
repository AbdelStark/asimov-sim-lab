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
- `open` preflight
- `evidence`
- `export`

Deferred commands such as `capture` or preset management require their own contracts, tests, and schemas before they appear in the CLI.

`open` is implemented only as the preflight slice defined by `RFC-0008-viewer-open-contract.md`. Interactive GUI launch remains deferred until lifecycle, shutdown, and failure semantics are specified and tested.
