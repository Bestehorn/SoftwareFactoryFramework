# Target review, round 10 (confirmation pass): revision 10 of the factory state model (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `88bce8a`, read from a detached worktree. I read the full diff
from revision 9 (`775d436`) for design.md, decisions.md (R115) and traceability.md (header only).

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be V1, …; there are none.

## Summary

OPEN ITEMS: 0

**Earlier items:** none were open after round 9.

**New findings:** none (0 A, 0 B, 0 C, 0 D).

**Verdict: every traceability row that revision 10's changes touch is still honest against design.md, the keynote and
the gap analysis.**

- Revision 10 changes only the dispatcher's check that the steward is alive (§3.5, §4.5 Dispatcher row, §14, §15.2,
  §18; decision R115):
  - the check also fires when the steward's last three completed runs all failed or timed out;
  - on GitLab it reads the pipeline schedule, with a read scope;
  - its time bound is the longest gap in the steward's own run history, recorded by setup;
  - an incident opens only when two consecutive polls see the same fault.
- No idea of the vision or gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## The rows the changed sections touch

| Change in revision 10 | Rows that cite it | Verdict |
|---|---|---|
| §3.5, §14: the liveness check's new conditions (failing ticks, GitLab's pipeline schedule, the measured bound, two consecutive polls) | A9 and B.1 row 5 (the dispatcher's duties, host open, O12); B.2 3.3 | honest. The check stays a dispatcher duty, so it inherits those rows' named rest (O12). The interim `enqueue` report until the dispatcher runs is unchanged |
| §4.5 Dispatcher row, §14, §15.2: a read scope for GitLab's pipeline schedule added to the dispatcher's token | A14; B.1 row 13 and B.2 3.2 (control) | honest. A read scope for one role adds no write path; these rows' statuses and rests (O11, O12, sandboxing) are unaffected. §15.2 still ends the dispatcher's credentials with "nothing more" |
| §18 Setup and update: record and refresh the steward's measured bound | C1 ("no human-only gates"); B.3 rank 9 and B.2 3.7 (the forge setup as a precondition) | honest. Recording the bound is part of the setup the operator already runs, not a gate in the issue flow |

Rows not touched by revision 10 keep the verdicts of rounds 7 to 9.

## New findings

None.
