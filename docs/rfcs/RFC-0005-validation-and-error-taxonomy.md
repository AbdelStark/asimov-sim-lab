# RFC-0005: Validation and Error Taxonomy

## Abstract
Validation is a first-class product feature, not a side effect.

## Requirements
- typed validation codes
- human-readable remediation guidance
- support for broken fixtures in tests
- machine-readable JSON output for CI and future UIs

## Non-goal
Validation should not silently coerce bad upstream data into seemingly-correct output.
