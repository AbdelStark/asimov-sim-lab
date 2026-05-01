# RFC-0002: Source Sync and Provenance

## Abstract
Define how the repo discovers, pins, mirrors, or validates upstream Asimov source assets.

## Core questions
- what is the minimum supported upstream asset set?
- how do generated artifacts record commit/source provenance?

## Accepted MVP answers
- minimum supported upstream asset set is `sim-model/xmls/asimov.xml`, `sim-model/assets/meshes/*.STL`, and optional `sim-model/README.md`
- MVP uses explicit local checkout roots only
- no vendored upstream assets and no fetch-on-demand behavior

## Contract
- every derived artifact must record upstream source path(s)
- every sync/refresh command must expose the source revision or snapshot identifier
- failures must distinguish missing files, schema drift, and unsupported formats
