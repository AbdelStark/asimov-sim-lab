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
- one feature-specific export or demo command
