# Target review, round 11 (confirmation pass): revision 11 of the factory state model (2026-11-20)

Reviewed: branch `docs-factory-state-model-design` at `b440fb7`, read from a detached worktree. I read the full diff
from revision 10 (`88bce8a`) for design.md, decisions.md (R116; R115 revised) and traceability.md (header only).

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be W1, …; there are none.

## Summary

OPEN ITEMS: 0

**Earlier items:** none were open after round 10.

**New findings:** none (0 A, 0 B, 0 C, 0 D).

**Verdict: every traceability row that revision 11's changes touch is still honest against design.md, the keynote and
the gap analysis.**

- Revision 11 changes only the wording of the steward-liveness check in §3.5 and §18 (decision R116):
  - the bound is now the 99th percentile of the scheduled-run gaps over 14 days, leaving out gaps inside this check's
    own incidents, and capped at 4 × the schedule interval;
  - the dispatcher recomputes the bound on every poll;
  - cancelled runs, and on GitLab skipped pipelines, are left out of the failing-ticks count.
- No idea of the vision or gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## The rows the changed sections touch

| Change in revision 11 | Rows that cite it | Verdict |
|---|---|---|
| §3.5: the bound's new definition; the dispatcher recomputes it on every poll from the run listing it already reads | A9 and B.1 row 5 (the dispatcher's duties, host open, O12); B.2 3.3 | honest. The check stays a dispatcher duty and inherits those rows' named rest (O12); it needs no new credential |
| §3.5: cancelled runs (GitLab: `canceled` or `skipped` pipelines) skipped in the failing-ticks count | the same rows | honest; this refines the check's condition, not its owner or reach |
| §18 Delivery row: "ran within its bound (computed on every poll from its run history)" | B.3 rank 9 and B.2 3.7 (the forge setup as a precondition); C1 | honest. The bound is no longer a setup step, so nothing about it remains for the operator. C1's "no human-only gates" is unaffected |

Rows not touched by revision 11 keep the verdicts of rounds 7 to 10.

## New findings

None.
