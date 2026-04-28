# RFC-0001: Repo Architecture

## Abstract
Define a clean uv-managed Python repo layout that keeps core contracts, tests, fixtures, and future secondary surfaces separated.

## Decisions
- `src/asimov_sim_lab` is the canonical runtime package.
- `docs/spec/` holds product/spec contracts.
- `docs/rfcs/` holds implementation RFCs.
- `tests/` holds automated validation.
- secondary UX surfaces, if added later, must consume the Python core contracts instead of inventing their own schema.

## Acceptance
- package imports cleanly
- tests run under uv
- repo structure is stable before feature code lands
