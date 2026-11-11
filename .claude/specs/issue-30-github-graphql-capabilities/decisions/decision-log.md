# Decision Log

## DL-001 — 2026-11-11T04:14:25Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's tier line): one module and its tests, but a design choice — record granularity, the mutation and node-ID shape, and which capabilities `call` refuses.
**Driver:** issue #30 Tier line and Open questions; #28 design D2 (`GraphQLOperation` reached by `call`).
**Alternatives considered:** tier S (rejected: the record shape for mutations is undecided in #17 and #28).
**Evidence:** issue #30 body; .claude/specs/issue-28-generic-operation-command/design.md.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T04:28:57Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Accept the requirements' refusal class: `createCommitOnBranch`, `revertPullRequest`, `transferIssue` refused naming no subcommand, `enablePullRequestAutoMerge` naming `merge-pr`; branch protection, `deleteProjectV2` and `createSponsorship` stay callable (residuals); keep AC-2.5 (an undeclared variable is refused, exit 2) as `call`'s existing refusal of an undocumented name applied to GraphQL.
**Driver:** #27 AC-7 (branch-writing class), #32 DL-003 (merge gating), #28 AC-2.2 and design Security "Destructive operations"; the draft's "each capability has a documented call" is met by a declared record.
**Alternatives considered:** leave every capability callable (rejected: bypasses the merge-steward and filing gates); keep the four pending (rejected: a refused record is still documented and covered).
**Evidence:** requirements.md Requirement 3, Residuals.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** One `GraphQLOperation` per mutation or connection query a row names, id `graphql/<member>`; `GraphQLOperation` gains `operation_id` (first) and `connection` defaults to `()`; the coverage test's duplicate-capability check moves to `operation_id` (minimal edit).
**Driver:** requirements.md AC-1.1, AC-1.4, AC-1.5; GraphQL spec 6.2.2 (a mutation document runs every root field it selects).
**Alternatives considered:** one record per capability (rejected: one document would run several mutations).
**Evidence:** design.md D1, D2.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-004 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** `call` dispatches a `graphql/` id to a new `registry.graphql_lookup` (REST `lookup` unchanged); a mutation takes one `$input` (`-F input=...`); node ids are supplied by the caller; `--path`, `--query` and a caller's `after` on a paged record are refused as undocumented names (exit 2), the existing rule applied to GraphQL as #41 D2 does.
**Driver:** design.md D3, D4; #28 AC-2.2; #41 design D2.
**Alternatives considered:** one lookup over both kinds (rejected: `send`, `pages` and the compatibility commands expect a REST record).
**Evidence:** design.md D3, D4.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-005 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Gate `graphql/enablePullRequestAutoMerge` to `merge-pr` and `graphql/createCommitOnBranch`, `graphql/revertPullRequest`, `graphql/transferIssue` to `None` (DL-002); the branch rebases onto the trunk (#27 landed) before the first wave; a new contract test `test/test_github_graphql_contract.py` and suite `test_github_api_graphql_only.py`; the fixtures stay untouched (the static `POST /graphql` route suffices).
**Driver:** design.md D5, D6; #27 merged f374b3d.
**Alternatives considered:** extend `test_github_wrapper_contract.py` (rejected: REST-only reader).
**Evidence:** design.md D5, D6.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-006 — 2026-11-11T05:31:50Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md and design.md after design review iteration 03: every lane CLEAN or READY (Y1-Y6 and every C/D applied in iteration 02; the AC-4.1 docstring line break fixed in iteration 03).
**Driver:** review/*/iteration-0{1,2,3}.md; review/review-latest.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-03.md Verdict line; review/test-architect/iteration-02.md (21/21 COVERED).
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md

## DL-007 — 2026-11-11T06:01:26Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 02 (the cap): test lane CLEAN, spec lane READY; the test lane's last C (task 2.4 calls the `graphql_call` that 2.5 writes in the same wave) applied by the conductor as the reviewer's exact sentence.
**Driver:** review/test-architect/tasks-iteration-02.md; review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** none
**Evidence:** review/test-architect/tasks-iteration-02.md Verdict line.
**Supersedes:** none
**Artifacts touched:** tasks.md, design.md
