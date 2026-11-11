# Decision Log

## DL-001 — 2026-11-11T02:56:16Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #28's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #32 Tier line; #28 design D8 (a slice edits its family module and test module).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #32 body; .claude/specs/issue-28-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T03:25:58Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Keep `pulls/update-branch` pending (it writes the PR's head branch and no gated subcommand sends it); once #27 lands its `None`-mapped gating, gating it is one entry (residual).
**Driver:** review/spec-review-agent/iteration-01.md B2, C1; a pending id sends nothing.
**Alternatives considered:** gate it now with a `None` mapping (rejected: that mapping type is #27's change; avoids a semantic conflict).
**Evidence:** review/spec-review-agent/iteration-01.md.
**Supersedes:** none
**Artifacts touched:** change.md Residuals

## DL-003 — 2026-11-11T03:25:58Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Gate `pulls/merge-async` to `merge-pr` in `commands/call.py` `GATED_OPERATIONS`; the refusal names the subcommand to use.
**Driver:** review/spec-review-agent/iteration-01.md B2; its body carries `merge_action: direct_merge` and `bypass_rules` — a trunk write the merge-steward gate guards.
**Alternatives considered:** leave it callable (rejected: bypasses gate_merge_steward).
**Evidence:** review/spec-review-agent/iteration-01.md.
**Supersedes:** none
**Artifacts touched:** commands/call.py, K

## DL-004 — 2026-11-11T03:25:58Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Edit K (`src/payload/test/test_github_api_call.py`, outside #28 D8's slice table) minimally: the AC-2.1 pending-id case moves off `pulls/list` (declared here) to `pulls/update-branch`, plus the `pulls/merge-async` gated case; declare `issues/get-issue-artifact` as `Paging.NONE` (its `page`/`per_page` are documented query names).
**Driver:** review/spec-review-agent/iteration-01.md B1, B2.
**Alternatives considered:** leave get-issue-artifact pending (rejected: #27 declares the same shape as NONE).
**Evidence:** review/spec-review-agent/iteration-01.md.
**Supersedes:** none
**Artifacts touched:** K, families/issues.py

## DL-005 — 2026-11-11T03:25:58Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Absorb a small fix of `src/hooks/gate_filing.py` `CREATE_RE`: match `create-issue` / `issue create` as a subcommand token, not a substring, so a command naming `issues/create-issue-artifact` is not refused.
**Driver:** review/spec-review-agent/iteration-01.md C2 — the reviewer's own Bash call naming that id was refused by the installed issue-filing gate (observed, quoted in the review).
**Alternatives considered:** a residual (rejected: small, clear, and it blocks this slice's record in every session).
**Evidence:** review/spec-review-agent/iteration-01.md.
**Supersedes:** none
**Artifacts touched:** src/hooks/gate_filing.py, src/hooks/tests/test_gate_filing.py

## DL-006 — 2026-11-11T03:53:24Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md as reviewed after combined review iteration 02 (the tier-S cap); its one B (the `CREATE_RE` matching rule was ambiguous) fixed by the reviewer's exact restatement (skip a match with a word character, `/`, `.` or `-` directly before or after) and a quoted-spelling block case.
**Driver:** review/spec-review-agent/iteration-02.md B1, D1.
**Alternatives considered:** a residual (rejected: the fix is the reviewer's own wording, applied in the pass).
**Evidence:** change.md (7,993 bytes).
**Supersedes:** none
**Artifacts touched:** change.md

## DL-007 — 2026-11-11T04:12:08Z — issue-work-orchestrator — phase:FIX

**Decision:** Accept IMPL-7's `GATED_NOT_SENT`: the `pulls/merge-async` refusal names `merge-pr` without ", which sends it", because `merge-pr` sends `pulls/merge`, not the async operation.
**Driver:** AC-6 (name the subcommand to use); `commands/pulls.py` `OP_PULLS_MERGE` is the only id `merge-pr` sends.
**Alternatives considered:** reuse the existing message (rejected: it would state a falsehood).
**Evidence:** src/payload/scripts/github_api/commands/call.py `refuse_gated`, `GATED_NOT_SENT`; evidence/green/wave-1.txt.
**Supersedes:** none
**Artifacts touched:** src/payload/scripts/github_api/commands/call.py

## DL-008 — 2026-11-11T04:39:47Z — issue-work-orchestrator — phase:PR

**Decision:** Resolve the rebase conflict onto #27's merge (f374b3d) in `commands/call.py` by keeping both: #27's `Mapping[str, Optional[str]]`, membership test and `None` branch, plus #32's `pulls/merge-async` entry and `GATED_NOT_SENT` ending on the non-`None` branch.
**Driver:** rebase conflict; code-merge-reviewer report (both intents kept line by line).
**Alternatives considered:** none (taking one side would drop the other's refusals).
**Evidence:** code-merge-reviewer run: 789 passed over the 15 affected test files; commit eb63d18.
**Supersedes:** none
**Artifacts touched:** src/payload/scripts/github_api/commands/call.py

## DL-009 — 2026-11-11T05:17:36Z — issue-work-orchestrator — phase:VERIFY

**Decision:** Rework after the verifier REFUTED AC-6's wording: K's gated cases now assert `which sends it` on the `pulls/merge` and `issues/create` refusals and its absence on `pulls/merge-async`; mutants M06 and M06b now fail K (3 and 1 failures); one push, then a delta re-verification.
**Driver:** evidence/verify/refutation-report.md (M06, M06b survived).
**Alternatives considered:** drop `GATED_NOT_SENT` (rejected: the message would state a falsehood, DL-007).
**Evidence:** evidence/green/rework-1.txt; rework implementer's mutant runs.
**Supersedes:** none
**Artifacts touched:** src/payload/test/test_github_api_call.py
