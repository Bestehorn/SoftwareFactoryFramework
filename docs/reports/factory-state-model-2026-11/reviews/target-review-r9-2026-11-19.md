# Target review, round 9 (confirmation pass): revision 9 of the factory state model (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `775d436`, read from a detached worktree. I read the full diff
from revision 8 (`66c8a50`) for design.md, decisions.md (R113, R114; R109 and R111 revised) and traceability.md
(header only).

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be U1, …; there are none.

## Summary

OPEN ITEMS: 0

**Earlier items:** none were open after round 8.

**New findings:** none (0 A, 0 B, 0 C, 0 D).

**Verdict: every traceability row that revision 9's changes touch is still honest against design.md, the keynote and
the gap analysis.**

- Revision 9 changes two things:
  - the dispatcher's check that the steward is alive: it now reads the run API, with "Actions: read" added to the
    dispatcher's token (§3.5, §4.5 Dispatcher row, §14, §15.2);
  - how the rollout carries the production environment's secrets (H15).
- No idea of the vision or gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## The rows the changed sections touch

| Change in revision 9 | Rows that cite it | Verdict |
|---|---|---|
| §3.5, §14: the dispatcher checks the steward's liveness through the run API (the workflow's `state` is `active`, and its latest run started within three schedule intervals); the status record stays the watcher's (decision R113) | A9 and B.1 row 5 (the dispatcher's duties, host open, O12); B.2 3.3 | honest. The check is a dispatcher duty and inherits those rows' named rest (O12). The interim `enqueue` report is unchanged |
| §4.5 Dispatcher row, §14, §15.2: "Actions: read" added to the dispatcher's token | A14 (authority table, per-host tokens); B.1 row 13 and B.2 3.2 (control) | honest. A read permission for one role adds no write path; the rows' statuses and rests (O11, O12, sandboxing) are unaffected. §15.2 still ends the dispatcher's credentials with "nothing more", matching tR1's restatement |
| H15: the rollout copies the old environment's policy and variables, and the operator re-enters each secret from its source (decision R114) | C1 ("no human-only gates") | honest. Re-entering secrets is a step of the rollout the operator already runs through the update prompt, not a gate in the issue flow |
| H15: unchanged otherwise (old-file runs on the detected tier; the protected tier's new environment) | A14, A19 | honest; their per-tier statements are unchanged and still match §15.1 rule 5 and §15.2 item 5 |

Rows not touched by revision 9 keep the verdicts of rounds 7 and 8.

## New findings

None.
