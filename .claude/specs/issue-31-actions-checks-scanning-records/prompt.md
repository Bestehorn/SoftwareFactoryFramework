# Prompt — issue #31: GitHub wrapper rewrite, part 2 slice: actions, checks, code-scanning, dependabot, secret-scanning families

Tier: S — data records in five family modules and their fake-host tests on the merged part-2a design (#28); re-tier to M only if a record needs a field or a request form part 1 and #28 do not build.

Kind: FEATURE.

## Goal

Cover `actions`, `checks`, `code-scanning`, `dependabot`, `secret-scanning`: 281 index rows, 6 mapped, 275 pending (measured at 7f2a1a9). Each pending id gets a `RestOperation` transcribed from its `docs/api-reference/github/rest/<category>.md` section, callable through `call <operation-id>` (#28), passing `test/test_github_wrapper_contract.py` and the coverage test, with the five modules' `PENDING` emptied.

## Scope

The issue's ACs and UBs (issue body). Out of scope: other families; the real-forge run (#10). The issue's open questions are settled by DL-002.
