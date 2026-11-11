# Prompt — issue #33: GitHub wrapper rewrite, part 2 slice: the remaining 31 families

Tier: S (re-tiered from the issue's M by DL-001) — data records in 31 family modules and their fake-host tests on the merged part-2a design (#28); the one M trigger, `markdown/render-raw`'s raw-text request body, stays pending and is routed to #46.

Kind: FEATURE.

## Goal

Cover the 31 families the issue lists: 379 index rows, 0 records, 379 pending (measured at 7f2a1a9). Each pending id gets a `RestOperation` transcribed from its `docs/api-reference/github/rest/<category>.md` section, callable through `call <operation-id>` (#28), passing `test/test_github_wrapper_contract.py` and the coverage test, with the modules' `PENDING` emptied but for the ids routed to #46.

## Scope

The issue's ACs and UBs (issue body). Out of scope: other families; the real-forge run (#10); non-JSON request bodies (#46). The issue's open questions are settled by DL-001 and DL-002.
