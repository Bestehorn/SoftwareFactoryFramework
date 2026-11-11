# Decision Log

## DL-001 — 2026-11-11T04:15:51Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S, one cycle, re-tiered down from the issue's M: the M trigger (the raw-text request body of `markdown/render-raw`, which `Transport.request` cannot send) stays pending and is routed to #46, leaving data records on #28's design; the 31 families run as one wave of disjoint files.
**Driver:** issue #33 Tier line and Open question 1; #46 (non-JSON request bodies); #27 DL-002 (the same routing of `repos/upload-release-asset`); proportionality.md ("when in doubt, choose the smaller tier").
**Alternatives considered:** tier M building the text body here (rejected: #46 owns that request form for every family); split along the work items (rejected: no design choice differs between them, and one wave of disjoint modules runs in parallel).
**Evidence:** issue #33 body; issue #46 body; src/payload/scripts/github_api/transport.py `Transport.request`.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T04:15:51Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** `meta/get-zen` and `meta/get-octocat` are declared: #28 D3 writes a body that is not JSON to standard output unchanged, so their text answers need no new mechanism.
**Driver:** issue #33 Open question 2; #28 design D3 (print forms).
**Alternatives considered:** keep them pending for #46 (rejected: #28 already prints a non-JSON response).
**Evidence:** .claude/specs/issue-28-generic-operation-command/design.md D3; src/payload/scripts/github_api/commands/call.py.
**Supersedes:** none
**Artifacts touched:** prompt.md, change.md

## DL-003 — 2026-11-11T04:36:51Z — issue-work-orchestrator — phase:SPEC

**Decision:** Declare the seven records whose call writes a branch or creates issues (`agent-tasks/create-task-in-repo`, `agent-merge/put-agent-merge-enrollment`, `agent-automations/create-repo-automation`, `agent-automations/edit-repo-automation`, `agent-automations/create-repo-automation-task`, `codespaces/export-for-authenticated-user`, `campaigns/create-campaign`) and gate each in `commands/call.py` `GATED_OPERATIONS` mapped to `None`, as #27 AC-7 does; this adds a `commands/call.py` task.
**Driver:** #27 merged as f374b3d, so the `None` mapping is on origin/main (the change author's pending alternative assumed it was not); #28 design Security "Destructive operations".
**Alternatives considered:** keep them pending with a ledger row (rejected: the mechanism now exists, and a gated record is documented and covered).
**Evidence:** origin/main f374b3d `src/payload/scripts/github_api/commands/call.py` `GATED_OPERATIONS`, `refuse_gated`.
**Supersedes:** none
**Artifacts touched:** change.md, commands/call.py

## DL-004 — 2026-11-11T04:36:51Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep `copilot/set-copilot-content-exclusion-for-organization` pending: its body is a map of any key, and `call` refuses a body name the record does not document; recorded as a ledger row (#46 owns only request forms).
**Driver:** #28 Residuals (the record is this slice's to route); #46 prompt.md scope.
**Alternatives considered:** a record with no body names (rejected: the call could send no member).
**Evidence:** docs/api-reference/github/rest/copilot.md section of that id.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T04:36:51Z — issue-work-orchestrator — phase:SPEC

**Decision:** Edit N `test/test_github_wrapper_contract.py` `test_an_unreachable_call_matches_its_reference_section` minimally (outside #28 D8's slice table): its step 3 drops the declared `billing/update-budget-org` before adding its own record, else the id is declared twice and `registry.lookup` refuses it.
**Driver:** change author's finding; `registry.lookup` refuses an id declared twice.
**Alternatives considered:** leave `billing/update-budget-org` pending (rejected: AC-1).
**Evidence:** test/test_github_wrapper_contract.py `test_an_unreachable_call_matches_its_reference_section`.
**Supersedes:** none
**Artifacts touched:** test/test_github_wrapper_contract.py

## DL-006 — 2026-11-11T04:36:51Z — issue-work-orchestrator — phase:SPEC

**Decision:** `dependency-graph/diff-range` is `Paging.LINK` (an array `200` with a `Link` header, #27's rule); a `Link` header on a one-object answer stays `Paging.NONE` (#31); the retired source-import records are declared as their sections document them; a family with no `Paging.LINK` record has no per-page test (an empty parametrization would run as a skip).
**Driver:** #27 change.md AC-4; #31 change.md AC-4; tests-must-not-fail.md (no skip).
**Alternatives considered:** none
**Evidence:** docs/api-reference/github/rest/dependency-graph.md, rest/migrations.md.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-007 — 2026-11-11T05:11:27Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 01 READY (0 A, 0 B); C2, D1, D2 applied; C1 (the decisions on the issue) posted as an issue comment.
**Driver:** review/spec-review-agent/iteration-01.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md Verdict line; issue #33 comment 6787571024.
**Supersedes:** none
**Artifacts touched:** change.md
