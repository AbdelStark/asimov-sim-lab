# RFC-0002: Source Sync and Provenance

## Abstract
Define how the repo discovers, pins, mirrors, or validates upstream Asimov source assets.

## Core questions
- what is the minimum supported upstream asset set?
- do we vendor a pinned fixture snapshot or fetch on demand?
- how do generated artifacts record commit/source provenance?

## Contract
- every derived artifact must record upstream source path(s)
- every sync/refresh command must expose the source revision or snapshot identifier
- failures must distinguish missing files, schema drift, and unsupported formats
