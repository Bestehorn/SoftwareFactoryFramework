# Decision Log

## DL-001 — 2026-11-11T06:03:50Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #41's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #39 Tier line (S — data records in one family module and their fake-host tests on part 1's record t…); #41 design D8 (a slice edits its family modules and test modules).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #39 body; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T06:18:47Z — issue-work-orchestrator — phase:SPEC

**Decision:** The deprecated epic APIs get records like every other row; N's two tests are each record's fake-host proof and F adds one two-page case per paged record; a GET section headed "List" or "Get all" is `Paging.OFFSET`; `Kind.FILE` follows an `In` `form` row, not the Type column; member rows such as `not[labels]` are their own query `Param`; the emoji combined path row is declared as written.
**Driver:** #41 design D6 (no exclusion), D8; conventions.md "Pagination"; README "GitLab REST specifics"; N `record_problems`.
**Alternatives considered:** KEYSET for some lists (rejected: the reference names none).
**Evidence:** docs/api-reference/gitlab/conventions.md; test/test_gitlab_wrapper_contract.py.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T06:18:47Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep `plan#clone-an-issue` (creates an issue) and `plan#create-a-merge-request-note` (`/merge` quick action) pending, with a ledger row: the GitLab `GATED_OPERATIONS` is `Mapping[str, str]` and `refuse_gated` lets a `None` entry through, so no no-subcommand refusal exists yet; also pending, the keys a second endpoint of one Reference needs (one record per id).
**Driver:** src/payload/scripts/gitlab_api/commands/call.py `GATED_OPERATIONS`, `refuse_gated`; #41 design Residuals (one record per id).
**Alternatives considered:** add the `None` mapping to the GitLab gate here, as #27 did for GitHub (rejected: a mechanism outside this slice's ask; a ledger row routes it).
**Evidence:** change.md AC-2, Residuals.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T06:18:47Z — issue-work-orchestrator — phase:SPEC

**Decision:** Restate K's pending-only case `OP_PENDING_ONLY` from `plan#create-an-upload` (declared here) to `plan#clone-an-issue` (stays pending).
**Driver:** K `src/payload/test/test_gitlab_api_call.py` uses a pending id this slice declares.
**Alternatives considered:** none (the case's meaning is "an id only on a pending list").
**Evidence:** src/payload/test/test_gitlab_api_call.py `OP_PENDING_ONLY`.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T06:38:29Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 01 READY (0 A, 0 B); C1-C3 and D1-D2 applied.
**Driver:** review/spec-review-agent/iteration-01.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md Verdict line.
**Supersedes:** none
**Artifacts touched:** change.md
