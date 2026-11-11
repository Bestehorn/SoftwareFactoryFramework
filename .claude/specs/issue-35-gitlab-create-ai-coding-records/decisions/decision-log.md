# Decision Log

## DL-001 — 2026-11-11T06:44:49Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #41's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #35 Tier line (S — data records in two family modules and their tests on part 1's record type; M if…); #41 design D8.
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #35 body; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T07:17:38Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep 16 keys pending: the 13 branch-writing ids, the `archive[.format]` path, the two-`:id` group SSH certificate path, and `changelog.txt`, the second endpoint of its Reference; every other key gets a record.
**Driver:** issue #35 open questions; gitlab `GATED_OPERATIONS` is `Mapping[str, str]`, so there is no no-subcommand refusal; part 1 builds one record per Reference.
**Alternatives considered:** declaring the branch-writing ids (rejected: callable, with nothing gating them); tier M for the three forms (rejected: the ask is records).
**Evidence:** src/payload/scripts/gitlab_api/commands/call.py `GATED_OPERATIONS`, `refuse_gated`; registry.py `expand`; #39 DL-003; issue #35 comment 6789639385.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T07:17:38Z — issue-work-orchestrator — phase:SPEC

**Decision:** A record is `Paging.OFFSET` when it is a GET whose heading begins with "List" or whose table has a `page` row, else NONE; never KEYSET. Kinds: `array of hashes` (and the blobs `files`) → ARRAY_OF_HASHES, other array → ARRAY, hash/object → HASH, else SCALAR.
**Driver:** #39 DL-002 (OFFSET on "List"/"Get all"); `conventions.md` "Keyset-based" (opt-in); create.md `files` row of the multiple-blobs section.
**Alternatives considered:** paging only by heading (rejected: some create sections that are not headed "List" carry a `page` row).
**Evidence:** docs/api-reference/gitlab/rest/create.md; docs/api-reference/gitlab/conventions.md; .claude/specs/issue-39-gitlab-plan-records/decisions/decision-log.md DL-002.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T07:17:38Z — issue-work-orchestrator — phase:SPEC

**Decision:** The `/clone`, `/rebase` and `/merge` quick-action paths in saved notes and descriptions, and the command-line `auth_password` of the pull-mirroring settings record, are routed as ledger rows, not handled in this change.
**Driver:** issue-filing-discipline.md branch 4 (no observed defect); #36 DL-003 (a credential on the command line); #41 Security.
**Alternatives considered:** gating the note records (rejected: a new mechanism, outside the ask).
**Evidence:** change.md Residuals; .claude/specs/issue-36-gitlab-no-stage-records/decisions/decision-log.md DL-003.
**Supersedes:** none
**Artifacts touched:** change.md, docs/findings-ledger.md (at IMPL-1)

## DL-005 — 2026-11-11T07:45:30Z — issue-work-orchestrator — phase:SPEC

**Decision:** AC-4 also pages the four ai-coding "Retrieve" lists (merge request participants, reviewers, dependencies, blocked merge requests) as `Paging.OFFSET`; the rest of DL-003 stands.
**Driver:** review/iteration-01.md B1: GitLab's handlers call `paginate` (lib/api/merge_requests.rb; ee/lib/api/merge_request_dependencies.rb); conventions.md "Pagination" (offset paging on every list endpoint).
**Alternatives considered:** paging by heading and `page` row only (rejected: prints the first page as the whole answer and refuses `--query page=`).
**Evidence:** review/iteration-01.md B1; docs/api-reference/gitlab/conventions.md "Pagination".
**Supersedes:** DL-003
**Artifacts touched:** change.md

## DL-006 — 2026-11-11T07:58:40Z — issue-work-orchestrator — phase:SPEC

**Decision:** Approve change.md after combined review iteration 02 READY (B1, C1, D1 closed; 7,965 B).
**Driver:** review/iteration-02.md verdict.
**Alternatives considered:** none
**Evidence:** review/iteration-01.md; review/iteration-02.md.
**Supersedes:** none
**Artifacts touched:** change.md
