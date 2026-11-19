# Target review, round 6: revision 6 of the factory state model against the keynote and the gap analysis (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `8df28db`, read from a detached worktree. I read the full diff
from revision 5 (`1fce726`) for design.md, traceability.md, decisions.md (R92–R103, O16) and review-response.md
(Part 0), and the unchanged design sections that a touched traceability row depends on.

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`.

Finding ids R1, … are this report's. They are not decisions.md's R entries, which this report always calls "decision
Rn".

## Summary

OPEN ITEMS: 1

**Verdicts on my 4 round-5 items** (tQ1–tQ4): 4 verified, 0 partly, 0 not fixed, 0 disputed.

**New findings:** 0 A, 0 B, 0 C, 1 D (R1). Open = 0 items not verified + 1 new finding = 1.

**Overall verdict: alignment and coverage hold. Revision 6 adds no difference from the vision, and every traceability
row its changes touch is honest.**

- The dispatcher's AWS role, the tip-only deploy (H15) and the per-tier statement of the production guard are each
  reflected where the traceability rows cite them.
- The new open decision O16 (whether the detected tier may deploy to production) is named in A19, the bank caveat's
  row.
- The one remaining point is wording: two phrases lag the revision's own per-tier statement (R1).

## Part 1: verdicts on my round-5 items

| Item | Verdict | Evidence in revision 6 |
|---|---|---|
| tQ1 | verified | §4.5 Dispatcher row: "a read-only AWS role for alarm states and Security Agent findings (§14)". §14 adds that the role can read only those "in the project's accounts, held by the dispatcher's host alone". §15.2 and §18 Setup list it too. §3.2: "The record is confirmed once, when triage sets the label; a later return of the alarm to OK does not revert it". Decision R102 |
| tQ2 | verified | §12.10: "The recommended set includes the privileged automation of §3.5 (`.github/workflows/**`, the steward's and the deploy pipeline's scripts and local actions, `templates/ci/**`)". A19's rest names §19 item 14 and the approval setting's sensitive paths. Decision R103 |
| tQ3 | verified | §7.2 CLOSE-READY row: "its AWS role may delete only the issue's own temporary resources, bounded per action by tag or by name prefix (§11)"; decision R101 |
| tQ4 | verified | traceability A14 now reads "per-host tokens without the deployment-approval and administration permissions (§15.2); the deploy role's OIDC trust in trunk only (§15.1 rule 5)", which matches §15.2. A later change in the same revision makes it need one qualifier: R1 |

## Part 2: traceability rows the changed sections touch

Revision 6 changed §2, §3.2, §3.5, §4.2, §4.5, §5.1, §5.3, §7.2, §8.3, §10.4, §10.8 (H13, H14, H15), §12.3, §12.6,
§12.9, §12.10, §14, §15.1 rule 5, §15.2, §18 and §19. These are the traceability rows that cite them:

| Rows | Verdict |
|---|---|
| A14 (changed) | honest in status (partly aligned, rest named); one qualifier missing: R1 |
| A19 (changed) | honest. Its rest now names three things: the approval setting's privileged-automation paths (§12.10, §19 item 14); that on the detected tier nothing guards the production deploy against a worker's trunk push (§15.2 item 5); and O16. Each matches design.md |
| A5, A15, C4, B.1 row 1 | honest. "The gate is the post-deploy smoke" still holds: the deploy after a landing is now the trunk push run that the steward's push starts, and only trunk's tip is deployed (§4.2, §10.4 steps 3 and 4, H15) |
| A7, B.2 3.4 | honest. The guidance issue is now locked to collaborators and corrected by a new block, never edited (§12.9). The rows' claims (standing answers; the same on both clients) are unchanged |
| A10, C10, B.1 rows 3 and 8 | honest. The source-record expedite now has its credential (tQ1) |
| A9, A11, A16, A17, A21, C1 | honest. Verify claims may call only the exits §4.5 assigns (§5.3), which A16 already implies. C1's "no human-only gates" still holds: O16 is a pending operator choice, not a gate |
| B.1 rows 2, 4, 5, 13, 15; B.2 3.2, 3.5; B.4 | honest. Row 15 and 3.5 ("sensitive PR paths") now include the recommended privileged-automation set. B.4's kept items are unaffected by the deploy's new trigger |

Ideas of the vision or gap-analysis items newly without a row: none. Revision 6 introduces no difference from the
vision that lacks a reason in section C. O16 and the detected tier concern forge plans, which the keynote does not
address, and A19 names them where the bank caveat is traced.

## Part 3: new findings

### R1 — Two phrases lag revision 6's per-tier statement of the production guard
Severity: D
Location:
- traceability.md A14, design element: "the deploy role's OIDC trust in trunk only (§15.1 rule 5)";
- design.md §15.2: "The dispatcher's token: contents write (claim refs) and issues write (repairs), nothing more; plus
  a read-only AWS role for alarm states and Security Agent findings (§14)".
Defect:
- Revision 6 states that the OIDC trust confines the production deploy to reviewed trunk code only on the protected
  tier. §15.1 rule 5 says "on the detected tier it does not, because a worker can push trunk itself", and §12.3 item 3
  and §15.2 item 5 say the same. A14 lists the trust as a control without that qualifier. A19 carries the residual, and
  A14's status ("partly aligned") is unaffected.
- §15.2 says "nothing more; plus", which contradicts itself in one sentence.
Proposed-edit:
- A14: "the deploy role's OIDC trust in trunk's tip only, which confines the production deploy on the protected tier
  (§15.1 rule 5)".
- §15.2: "The dispatcher's token: contents write (claim refs) and issues write (repairs), and a read-only AWS role for
  alarm states and Security Agent findings (§14); nothing more."
