# Decision Log

## DL-001 — 2026-11-11T06:46:21Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's tier line): one module and its tests, with a design choice (record granularity, a multipart GraphQL request, the refusal class); #30's approved design is the model.
**Driver:** issue #44 Tier line and Open questions; .claude/specs/issue-30-github-graphql-capabilities/design.md (on branch issue-30-github-graphql-capabilities).
**Alternatives considered:** tier S (rejected: the multipart request form and the record shape are undecided).
**Evidence:** issue #44 body; #41 design D2 (`GraphQLOperation.capability`, `call` reaching GraphQL records).
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T07:06:10Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Refuse only the mutations that create an issue or work item (`workItemCreate`, `workItemsCsvImport`); the branch-rule mutations stay callable with a residual, as #30 keeps GitHub's `createBranchProtectionRule` callable and #41 D8's gated class (commits to or merges into a branch, or creates an issue) does not cover protection rules; `PENDING_CAPABILITIES` SHALL be empty; the design restates requirements AC-4.1 accordingly.
**Driver:** requirements.md author report (choice 2); #30 design Residuals; #41 design D8 exceptions row.
**Alternatives considered:** refuse every `branchRule…` mutation (rejected: diverges from the GitHub twin and #41's class; branch protection writes no ref).
**Evidence:** issue-30 design.md Residuals; issue-41 design.md D8.
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md

## DL-003 — 2026-11-11T07:28:47Z — issue-work-orchestrator — phase:DESIGN

**Decision:** One record per mutation and one per field member, under GitLab's existing `graphql#<member>` id scheme; several records may serve one capability, so `capability_problems` stays as is.
**Driver:** design author report; a mutation document runs every root field in order (GraphQL spec §6.2.2), so one record per capability would update and delete in one call; a record pages one connection.
**Alternatives considered:** one record per capability (rejected: the reason above).
**Evidence:** design.md D1, D2; src/payload/scripts/gitlab_api/registry.py `lookup`, `call`.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-004 — 2026-11-11T07:28:47Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Upload mutations take `--file NAME=PATH` on a declared `Upload` variable and go out as the multipart request of `conventions.md` "File uploads" through `Transport.graphql(files=...)` and the existing `multipart_body`; the two refused ids map to `None` in a `Mapping[str, Optional[str]]` `GATED_OPERATIONS` with `refuse_gated` testing membership, as GitHub's does.
**Driver:** requirements AC-3.1, AC-4.1, AC-4.2; `issue create` sends REST `plan#create-an-issue`, never `workItemCreate`.
**Alternatives considered:** `--file files.0=...` naming, a record field, a separate transport upload method (each rejected in design D4); a subcommand name for the refusal (rejected: none sends it).
**Evidence:** design.md D4, D6; docs/api-reference/gitlab/conventions.md "File uploads"; src/payload/scripts/github_api/commands/call.py `refuse_gated`.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-005 — 2026-11-11T07:28:47Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Restate requirements' Introduction, Requirement 4 story and Out of scope to match AC-4.1 as DL-002 restated it (no branch-rule refusal); the design edits `commands/call.py` beyond `GATED_OPERATIONS` and the entry docstring as D9 records.
**Driver:** design author report: three passages still named branch-rule refusals after DL-002.
**Alternatives considered:** none
**Evidence:** requirements.md Introduction, Requirement 4, Out of scope; design.md D9.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-006 — 2026-11-11T07:58:10Z — issue-work-orchestrator — phase:DESIGN

**Decision:** With files, `Transport.graphql` takes its body and Content-Type from the existing `transport.request_body` (the multipart branch REST `--file` uses) instead of calling `multipart_body` itself; iteration 01's 3 B and 14 C/D are applied (design.md 47,629 B).
**Driver:** review/standards-reviewer/iteration-01.md B1 (`design-principles.md` §2); review/review-latest.md B1-B3.
**Alternatives considered:** building the multipart body inside `Transport.graphql` (rejected: repeats `request_body`).
**Evidence:** src/payload/scripts/gitlab_api/transport.py `request_body`; review/review-latest.md.
**Supersedes:** DL-004 (its body-construction clause only)
**Artifacts touched:** design.md

## DL-007 — 2026-11-11T08:16:20Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Approve design.md after iteration 02 (every lane READY; the remaining C1/D1/D2 restated, 47,606 B); tasks.md keeps the `commands/call.py` and `registry.call` wiring in wave 2, beside the records, because G's tests for them need the records.
**Driver:** review/{spec-review-agent,test-architect,standards-reviewer}/iteration-02.md READY; devops, security, best-practice iteration-01 READY; tasks author report.
**Alternatives considered:** call.py in wave 1 (rejected: an IMPL before its TEST, or a new test outside the design).
**Evidence:** review/*/iteration-02.md; tasks.md Waves 1-2.
**Supersedes:** none
**Artifacts touched:** design.md, tasks.md

## DL-008 — 2026-11-11T08:30:52Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 01: both lanes READY (0 A, 0 B); the spec lane's D1 (the legend names H's source, design § Testing Strategy) applied by the conductor as the reviewer's sentence.
**Driver:** review/test-architect/tasks-iteration-01.md; review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** none
**Evidence:** both tasks-iteration-01.md Verdict lines.
**Supersedes:** none
**Artifacts touched:** tasks.md
