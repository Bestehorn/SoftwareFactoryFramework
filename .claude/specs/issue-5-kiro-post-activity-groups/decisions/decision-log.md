# Decision Log

## DL-001 — 2026-11-10T16:52:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; step 2 names `--group lint --group types --group security` explicitly; no new `run_checks.py` selection.
**Driver:** Issue #5 open question; the installed `.claude/rules/post-activity.md` step 2 already uses the explicit groups, so naming them keeps both clients identical with no new interface.
**Alternatives considered:** a named non-test selection in `run_checks.py` (a new CLI interface in shipped code, beyond the ask).
**Evidence:** `.claude/rules/post-activity.md` step 2; `src/payload/scripts/run_checks.py` `GROUP_ORDER`.
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-5-kiro-post-activity-groups/prompt.md

## DL-002 — 2026-11-10T16:06:01Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md after combined review iteration 01 (A+B = 0); C1-C3 and D1 applied in one author pass (C3 restates the stale setup-kiro 8.23 Integration line as an I1 edit, no new criterion).
**Driver:** review/spec-review-agent/iteration-01.md verdict CLEAN (READY).
**Alternatives considered:** C3 as a residual (would leave the same contradiction one section away).
**Evidence:** review/spec-review-agent/iteration-01.md#C1..#D1
**Supersedes:** none
**Artifacts touched:** change.md
