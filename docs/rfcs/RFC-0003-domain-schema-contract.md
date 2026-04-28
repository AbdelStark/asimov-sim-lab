# RFC-0003: Domain Schema Contract

## Abstract
Define the machine-readable internal data model for the repo's core objects before implementation begins.

## Scope
This RFC covers the primary internal schema for Asimov Sim Lab and the serialized outputs that downstream tools, reports, and UI layers will consume.

## Requirements
- explicit version field
- pydantic-backed validation
- stable JSON export shape
- room for provenance fields without breaking old consumers
