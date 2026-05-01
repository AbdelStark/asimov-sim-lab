# RFC Index — Asimov Sim Lab

## Purpose
These RFCs define the durable architecture and product-contract boundaries for the repo.

## RFCs
- `RFC-0001-repo-architecture.md`
- `RFC-0002-source-sync-and-provenance.md`
- `RFC-0003-domain-schema-contract.md`
- `RFC-0004-cli-and-operator-workflow.md`
- `RFC-0005-validation-and-error-taxonomy.md`
- `RFC-0006-evidence-and-export-contract.md`
- `RFC-0007-ci-release-and-quality-gates.md`

## Phase-2 lock files
The RFCs are now complemented by phase-2 implementation contracts in `docs/spec/`:
- `MANIFEST-CONTRACT.md`
- `RESULT-SCHEMA-CONTRACT.md`
- `CLI-COMMAND-SPEC.md`
- `PROFILE-CONTRACT.md`
- `FIRST-THREE-SCENARIOS-BUILD-PACK.md`

Read those before changing implementation behavior. The MVP core has shipped; the goal now is to keep RFC language, executable contracts, schemas, and README status aligned.

## MVP decision log
`docs/spec/MVP-DECISION-LOG.md` is the accepted decision record for the current MVP implementation. If an older RFC phrase conflicts with that file, the decision log and executable schema/tests win until the RFC is revised.
