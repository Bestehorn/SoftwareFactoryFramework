# Prompt — issue #32: GitHub wrapper rewrite, part 2 slice: issues, pulls, reactions, search, activity, gists families

Tier: S — data records in family modules and their fake-host tests on the merged part-2a design (#28); re-tier to M only if a record needs a field or a request form part 1 and #28 do not build.

Kind: FEATURE.

## Goal

Cover `issues`, `pulls`, `reactions`, `search`, `activity`, `gists`: 173 index rows, 14 mapped, 159 pending (measured at 7f2a1a9). Each pending id gets a `RestOperation` transcribed from its `docs/api-reference/github/rest/<category>.md` section, callable through `call <operation-id>` (#28), passing `test/test_github_wrapper_contract.py` and the coverage test, with the family modules' `PENDING` emptied.

## Scope

The issue's ACs and UBs (issue body). Out of scope: other families; the real-forge run (#10).
