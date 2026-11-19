# Target review, round 8 (confirmation pass): revision 8 of the factory state model (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `66c8a50`, read from a detached worktree. I read the full diff
from revision 7 (`b236e58`) for design.md, decisions.md (R109–R112) and traceability.md (header only).

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be T1, …; there are none.

## Summary

OPEN ITEMS: 0

**Earlier items:** none were open after round 7.

**New findings:** none (0 A, 0 B, 0 C, 0 D).

**Verdict: every traceability row that revision 8's changes touch is still honest against design.md, the keynote and
the gap analysis.**

- Revision 8 changes only delivery and deploy mechanics: §3.5, §10.8 H15, §15.1 rule 5, §15.2 item 5 and §18.
- No idea of the vision or gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## The rows the changed sections touch

| Change in revision 8 | Rows that cite it | Verdict |
|---|---|---|
| §15.1 rule 5: on the detected tier the deploy job names no environment, the role trusts only the trunk's ref subject, and setup refuses an environment subject there (decision R110) | A14 ("the deploy role's OIDC trust in trunk's tip only, which confines the production deploy on the protected tier") | honest. The rule still says that on the detected tier the trust does not confine the deploy, because a worker can push trunk itself; A14's qualifier matches |
| §15.2 item 5 and H15: on the detected tier, old-file deploy runs stay re-runnable for 30 days after the rollout; the protected tier's rollout creates a new environment and deletes the old one (decision R111) | A19 ("On the detected tier nothing guards the production deploy against a worker's trunk push (§15.2 item 5, O16)") | honest. The added 30-day residual falls under A19's existing statement of that tier, and O16 still covers whether that tier may deploy to production |
| §3.5: setup and update run the environment-name check and list each hit before factory mode starts (decision R112); setup lists the workflows a landing starts (unchanged) | C1 ("no human-only gates") | honest. Both are steps of the setup the operator already runs, not gates in the issue flow |
| §3.5: the steward checks that the deploy workflow is enabled; the dispatcher checks that the steward's last tick is recent; until the dispatcher runs, `enqueue` reports a refused tick dispatch (decision R109) | A9 and B.1 row 5 (the dispatcher's host open, O12); B.1 row 13 and B.2 3.2 (control) | honest. The new liveness check is a dispatcher duty and inherits A9's and row 5's named rest (O12); the interim `enqueue` report keeps today's session path working. Control rows are unaffected |
| §18 Setup row: the per-tier deploy-job and trust settings, the setup-time environment check | B.3 rank 9 and B.2 3.7 (the switch to `merge: steward` and its forge setup) | honest. Both name the forge setup of §3.5 as a precondition, which this extends |

Rows not touched by revision 8 keep the verdicts of round 7.

## New findings

None.
