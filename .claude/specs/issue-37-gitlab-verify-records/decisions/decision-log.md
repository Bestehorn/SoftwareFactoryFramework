# Decision Log

## DL-001 — 2026-11-11T06:44:49Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #41's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #37 Tier line (S — records in one family module and its tests on part 1's record type; M if the `*a…); #41 design D8.
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #37 body; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T07:06:10Z — issue-work-orchestrator — phase:SPEC

**Decision:** The issue's open questions: the two `*artifact_path` glob routes stay pending (`registry.expand` fills only `:name`; a ledger row); downloads are plain records printed byte for byte (#41 D3); the job-token routes are records like every other row (#41 D6 excludes nothing).
**Driver:** src/payload/scripts/gitlab_api/registry.py `PLACEHOLDER`, `expand`; #41 design D3, D5, D6.
**Alternatives considered:** re-tier to M and build the `*name` form (rejected: a mechanism outside the slice).
**Evidence:** change.md AC-2, Residuals.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T07:06:10Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep pending: the two glob routes, `verify#add-a-merge-request-to-a-merge-train` (merges; no subcommand sends it and the GitLab gate has no no-subcommand form), and the later endpoints of multi-endpoint sections (one record per id); `verify#runners-api-1` gets no record (each of its endpoints has its own section). The item "`verify.PENDING` empty" is deferred on #37 with ledger rows; K's artifacts redirect case moves to the real record.
**Driver:** src/payload/scripts/gitlab_api/commands/call.py `GATED_OPERATIONS`, `refuse_gated`; #41 design Residuals; K `artifacts-after-a-redirect`.
**Alternatives considered:** add a no-subcommand gate here (rejected: a mechanism outside the slice's ask).
**Evidence:** change.md AC-2, Files, Residuals.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T07:06:10Z — issue-work-orchestrator — phase:SPEC

**Decision:** `ARRAY_OF_HASHES` for `array of hashes`/`array of hash`/`array of strategy JSON objects`; plain `array` stays `ARRAY`; `verify#list-pipelines` is `KEYSET` (keyset only per conventions.md); `verify#list-all-scopes-for-a-runner-controller` is `NONE` (one object); job lists `OFFSET`.
**Driver:** docs/api-reference/gitlab/conventions.md "Pagination", "Keyset-based".
**Alternatives considered:** none
**Evidence:** conventions.md; rest/verify.md sections.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T07:40:12Z — issue-work-orchestrator — phase:SPEC

**Decision:** Approve change.md after combined review iteration 01 READY (0 A, 0 B); C1-C4 and D1-D2 applied (7,976 B); DL-001's re-tier trigger stands, since no record needs a field part 1 lacks.
**Driver:** review/spec-review-agent/iteration-01.md verdict and its C3 question.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md; change.md.
**Supersedes:** none
**Artifacts touched:** change.md
