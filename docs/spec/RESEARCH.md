# RESEARCH — Asimov Sim Lab

## Research posture
This repo is grounded in a real external source artifact rather than a synthetic idea prompt. The product opportunity comes from making an upstream technical release easier to inspect, validate, and use.

## Strategic reason this lane matters
- high signal for robotics / embodied-AI credibility
- obvious link to real builder and developer pain
- concrete enough to demo without pretending to solve all of robotics
- supports a portfolio story around tools, validation, and technical product sense

## Recommended implementation principle
Build the narrowest truthful core first. Secondary UX layers must consume stable machine-readable contracts rather than becoming the source of truth.

## Open research questions
- exact upstream version pinning strategy
- redistribution boundaries for mirrored/generated assets
- how much browser/UI surface belongs in v1 versus a later phase

## Locked MVP research decisions
- MVP source assets are local-checkout-only.
- CI uses synthetic fixtures only.
- Upstream assets are not vendored or downloaded by core commands.

## Quality bar
World-class software here means:
- explicit contracts
- provenance on generated artifacts
- reproducible commands
- clean error taxonomies
- no hand-wavy demo claims
