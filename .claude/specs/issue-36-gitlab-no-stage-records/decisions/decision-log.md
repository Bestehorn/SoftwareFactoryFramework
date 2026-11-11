# Decision Log

## DL-001 — 2026-11-11T06:03:50Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #41's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #36 Tier line (S — data records in one family module and its test module on part 1's record type; M…); #41 design D8 (a slice edits its family modules and test modules).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #36 body; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T06:18:14Z — issue-work-orchestrator — phase:SPEC

**Decision:** Rows marked "in OpenAPI only" and deprecated rows become `Param`s (the issue's first open question).
**Driver:** N's `table_rows` reads every row whatever its Notes cell; `record_problems` reports a query or body row the record lacks.
**Alternatives considered:** docs-page rows only (rejected: fails N).
**Evidence:** test/test_gitlab_wrapper_contract.py `table_rows`, `record_problems`.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T06:18:14Z — issue-work-orchestrator — phase:SPEC

**Decision:** A secret value is passed as `-f` text (the issue's second open question); its command-line exposure is a ledger row.
**Driver:** #41 D2 (`--file` only for a `FILE` attribute; `KIND_ACCEPTS` refuses a path for a `SCALAR`); #41 D4 logs names, never values; #41 design Residuals "Secrets in arguments".
**Alternatives considered:** a file or stdin option for text values (rejected: a new mechanism, scope freeze).
**Evidence:** src/payload/scripts/gitlab_api/registry.py `KIND_ACCEPTS`; issue-41 design D2, D4.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T06:18:14Z — issue-work-orchestrator — phase:SPEC

**Decision:** The two list records are `Paging.OFFSET`; no record of the group writes a branch, merges or creates an issue, so `GATED_OPERATIONS` is unchanged.
**Driver:** docs/api-reference/gitlab/conventions.md "Pagination" (offset is the default for every list endpoint); precedent `ai-coding#list-merge-request-pipelines`; #41 D8 exceptions row.
**Alternatives considered:** `Paging.NONE` (rejected: would print one page if GitLab pages the list).
**Evidence:** conventions.md "Pagination"; rest/no-stage-assigned.md section headings.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T06:38:29Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 02 READY (the tier-S cap); iteration 01's B1, C1 and D1 applied.
**Driver:** review/spec-review-agent/iteration-0{1,2}.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-0{1,2}.md Verdict line.
**Supersedes:** none
**Artifacts touched:** change.md
