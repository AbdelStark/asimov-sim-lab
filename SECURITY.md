# Security Policy

## Supported Versions

Asimov Sim Lab is in alpha (`0.x`). Only the latest published `0.x` release receives security updates. Pre-release commits on `main` are best-effort.

| Version | Supported          |
| ------- | ------------------ |
| `0.1.x` | :white_check_mark: |
| `< 0.1` | :x:                |

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security reports.

Use GitHub's private vulnerability reporting:

- <https://github.com/AbdelStark/asimov-sim-lab/security/advisories/new>

Include:

- The affected command, version, and Python version.
- A minimal reproducer (sanitized — do not include third-party assets or absolute machine paths).
- Observed behavior, expected behavior, and impact assessment.
- Whether the issue is reachable through the public CLI surface, the Python API, or only via specifically crafted local source roots.

## Scope

In scope:

- Code execution, path traversal, archive-extraction, or checksum-bypass issues in `inspect`, `validate`, `runtime-smoke`, `evidence`, `export`, `open`, or `doctor`.
- Issues that let a crafted local source root or preset cause unsafe file writes outside the requested output directory.
- Schema or evidence-bundle integrity issues (e.g. tampered archive validates as clean).

Out of scope:

- Vulnerabilities in upstream MuJoCo, in user-provided assets, or in third-party Python dependencies — please report those upstream. We will track and update affected dependencies once an upstream advisory exists.
- Hardware, manufacturing, or controller safety claims. The project explicitly does not make such claims (see `README.md`).

## Disclosure Timeline

- Acknowledgement: within 7 days of report.
- Initial assessment: within 14 days.
- Fix or mitigation in a tagged release: target 30 days, longer if coordination with upstream is required.

## Hardening Notes for Operators

- Pin a known release of `asimov-sim-lab` and verify wheel checksums.
- Run CLI commands against trusted local checkouts only. The project does not download or execute upstream code.
- Treat generated evidence and export bundles as untrusted input until checksums are reverified with `scripts/check_release_evidence.py`.
- Run `uv run pip-audit --skip-editable` (or `make security`) before publishing builds.
