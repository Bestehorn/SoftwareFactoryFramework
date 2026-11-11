# Prompt — issue #44: GitLab wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M — the capabilities of the "Only in GraphQL" table of `docs/api-reference/gitlab/graphql/conventions.md` in `gitlab_api/graphql_only.py` with fake-host tests, and a design choice the issue names (record granularity, a multipart GraphQL request for two capabilities).

Kind: FEATURE.

## Goal

Every capability of that table gets a documented call over GraphQL reachable through `call <operation-id>` (#41), with fake-host tests, and `graphql_only.PENDING_CAPABILITIES` emptied but for capabilities a missing request form keeps pending (routed as the design records).

## Scope

The issue's ACs and UBs (issue body). Out of scope: REST families; the real-instance run (#11); the GitHub twin (#30, whose approved design is the model). The issue's open questions are design questions, answered in `design.md`.
