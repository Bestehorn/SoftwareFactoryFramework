# Target review, round 7: revision 7 of the factory state model against the keynote and the gap analysis (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `b236e58`, read from a detached worktree. I read the full diff
from revision 6 (`8df28db`) for design.md, traceability.md, decisions.md (R104–R108, O16 extended) and
review-response.md (Part 0), and the unchanged design sections that a touched traceability row depends on.

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be S1, …; there are none.

## Summary

OPEN ITEMS: 0

**Verdicts on my 1 round-6 item** (tR1): 1 verified, 0 partly, 0 not fixed, 0 disputed.

**New findings:** none (0 A, 0 B, 0 C, 0 D). Open = 0 items not verified + 0 new findings = 0.

**Overall verdict: alignment and coverage hold, and every traceability status is honest against revision 7.**

- Revision 7 changes only delivery and deploy mechanics. They touch traceability A14 (changed), A19, A5, A15, C4, C1,
  B.1 rows 1 and 13, and B.4, and each still matches design.md and both targets.
- No idea of the vision and no gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## Part 1: verdict on my round-6 item

| Item | Verdict | Evidence in revision 7 |
|---|---|---|
| tR1 | verified | traceability A14: "the deploy role's OIDC trust in trunk's tip only, which confines the production deploy on the protected tier (§15.1 rule 5)". design.md §15.2: "The dispatcher's credentials: a token with contents write (claim refs) and issues write (repairs), and a read-only AWS role for alarm states and Security Agent findings (§14) [tQ1]; nothing more". Decision R108 |

## Part 2: traceability rows the changed sections touch

Revision 7 changed §3.5, §4.2 (TEST-READY → CLOSE-READY), §8.3, §10.8 H13 and H15, §12.6, §15.1 rule 5, §15.2 and §18,
and extended O16.

| Rows | Verdict |
|---|---|
| A14 (changed) | honest. §15.1 rule 5 now names, on the protected tier, only the production environment's subject in the trust, and on the detected tier the ref subject. Together with H15's tip check as the deploy job's first step, that is "trunk's tip only … on the protected tier", as A14 says |
| A19 | honest. Its "On the detected tier nothing guards the production deploy against a worker's trunk push (§15.2 item 5, O16)" still matches §15.1 rule 5 and §15.2 item 5. O16's new third option (a plan with the protected tier) is a choice inside O16, which A19 cites |
| A5, A15, C4, B.1 row 1 | honest. The post-deploy smoke stays the gate. The re-verify rule against supersession and the grace-period re-verify (§4.2, decision R104) change when a pinned run is dispatched, not what verifies an issue |
| C1 | honest. Setup and update listing every workflow a landing starts, for the operator to confirm at setup (§3.5, decision R107), is a setup step the operator already runs, not a gate in the issue flow; "no human-only gates" holds |
| A7, B.2 3.4 | honest. The §8.3 change (on issue N a form line counts only when it names no issue or `#N`) narrows which lines count and changes neither row's claim |
| B.1 rows 13 and 15; B.2 3.2 and 3.5 | honest. The environment check now covers expression-valued names and outside reusable workflows (§3.5), and §12.6 names disabling and enabling workflows as a standing permission; neither affects these rows' statuses or rests |
| B.4 | honest. Trains, ancestry verification and the SESSION verdict are kept; the deploy mechanics changed below them |

Ideas of the vision or gap-analysis items newly without a row: none. Revision 7 introduces no difference from the
vision; its changes concern forge mechanics the keynote does not address.

## Part 3: new findings

None.
