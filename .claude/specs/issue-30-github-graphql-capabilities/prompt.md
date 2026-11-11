# Prompt — issue #30: GitHub wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M — 13 capability records in `graphql_only.py` with fake-host tests, and a design choice the issue names (record granularity, the mutation shape, where a node-ID lookup lives, which capabilities `call` refuses).

Kind: FEATURE.

## Goal

#14 AC-2: every capability of the "Only in GraphQL" table of `docs/api-reference/github/graphql/conventions.md` gets a documented wrapper call over GraphQL — a `GraphQLOperation` reachable through `call <operation-id>` (#28) — with fake-host tests, and `graphql_only.PENDING_CAPABILITIES` emptied.

## Scope

The issue's ACs and UBs (issue body). Out of scope: REST families; the real-forge run (#10); the GitLab twin (#44). The issue's open questions are design questions, answered in `design.md`.
