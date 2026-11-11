# Prompt — issue #14: GitHub wrapper rewrite, part 2 — the last pending operations

Tier: S — three records on the existing record type and gate, so that part 1's pending list is empty (#14 "Done", #12 AC-1): `pulls/update-branch` and `code-scanning/commit-autofix`, which write a branch and are now refused through #27's "no subcommand sends it" gate, and `copilot/set-copilot-content-exclusion-for-organization`, whose body is a map of arbitrary keys.

Kind: FEATURE.

## Goal

The coverage test runs with every GitHub family's `PENDING` empty. Every family slice (#27, #29, #31, #32, #33, #46) and the GraphQL slice (#30) are closed, and these three keys are what remains (the ledger rows of #31 DL-003, #32 DL-002, #33 DL-004).

## Scope

The three keys and their tests. Then #14's checklist is reconciled against its closed children. Out of scope: the real-forge run (#10).
