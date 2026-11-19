# Target review, round 5: revision 5 of the factory state model against the keynote and the gap analysis (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `1fce726`, read from a detached worktree. I read the full diff
from revision 4 (`049a047`) for design.md, traceability.md, decisions.md (R75–R91; R57 and R62 replaced) and
review-response.md (Part 0), and the unchanged design sections that a touched traceability row depends on.

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`.

## Summary

OPEN ITEMS: 4

**Verdicts on my 5 round-4 items** (tP1–tP5): 5 verified, 0 partly, 0 not fixed, 0 disputed.

**New findings:** 0 A, 0 B, 2 C, 2 D (Q1–Q4). Per the corrected brief, open counts every item not verified plus every
new finding of any grade, D included: 0 + 4 = 4.

**Overall verdict: alignment and coverage hold, and revision 5's simplifications are sound on the vision's terms.**

- Workflow-file changes land through the queue, so principle P6 and C1 hold again.
- `/get-guidance` is the same on both clients, which closes the Kiro-parity point.
- The AWS bound is stated per action, as AWS permits.
- `priority:critical` rests on a source record.

Every traceability row the changed sections touch is honest, and every difference has its reason in section C. Two
small open points remain:

- **Q1 (C):** the dispatcher must re-read alarms and security findings in AWS, but its stated credentials cover only
  the forge.
- **Q2 (C):** the new residual that agents may change the automation that guards them (§19 item 14) is missing from
  the bank caveat's row A19, and §12.10 does not mention it.

## Part 1: verdicts on my round-4 items

| Item | Verdict | Evidence in revision 5 |
|---|---|---|
| tP1 | verified | R75 replaces R57. Worker tokens keep "Workflows" and "Actions: write" (§15.2). "A workflow-file change therefore lands through the queue like any other change … There is no human-only step (P6)" (§3.5). The steward pushes trains and trunk with its deploy key, and a refused train push drops that PR with `queue-failed` (H14, R77). C1 now states the case. Changes to privileged automation are tagged `iam-iac`, so they get the full lanes and a separately started checker (§3.5, R76). Whether a deploy key can push workflow files is listed for verification (O14). The residual is §19 item 14; see Q2 |
| tP2 | verified (moot) | R78 replaces R62: `/get-guidance` "posts nothing and holds no claim". It prints one block of form lines, each naming its issue, which the human posts on the project's guidance issue (§12.9 step 4). The answer recorder applies them (§12.7). §16 and traceability 3.4 say it is the same on both clients and needs no prompt-submit hook |
| tP3 | verified | §11 item 1, §15.1 rule 5, §18 Setup and R89 state the bound per action: tag-conditioned where the action supports it (`aws:RequestTag`; for S3 objects `s3:RequestObjectTag`); scoped by the key prefix `factory-issue-<repo>-<n>/` where it does not (S3 put and delete, citing the S3 User Guide); otherwise not granted. The naming fallback now also covers "an action on it cannot be conditioned on tags". One stale row elsewhere: Q3 |
| tP4 | verified | §3.2: triage may set `priority:critical` "only when the issue carries a source record that the dispatcher re-reads read-only and confirms" (an alarm ARN in alarm state, or an exploitable AWS Security Agent finding id). §6.1 inflow 3, §7.2 TEST-READY, R86, C10 and A10 agree. The credential that re-read needs: Q1 |
| tP5 | verified | §14: "The human sets priority with `/priority` (§3.2)"; §12.6's example names the steward; B16 names R61, R64 and `/admit` (R91) |

## Part 2: traceability rows the changed sections touch

Revision 5 changed §3.2, §3.4, §3.5, §4.2, §4.3, §4.5, §5.1, §5.3, §5.4, §6.1, §7.2, §8.2, §8.3, §8.5, §8.6, §10.3,
§10.4, §10.5, §10.8, §11, §12.3, §12.6, §12.7, §12.9, §12.10, §14, §15.1, §15.2, §16, §18 and §19. These are the
traceability rows that cite those sections:

| Rows | Verdict |
|---|---|
| A5, A6, A8, A9, A11, A12, A16, A18, A21, A22, A24 | honest. A16 still holds now that a separately started checker calls its exit itself (R81) and every decision re-folds from the first record (R82). A12's "ask hash" now includes executed `/amend` text (R84); the row's pointer to §4.3 stays accurate |
| A7 (changed) | honest: a standing answer reaches the learning-batch issue (§12.9 step 6, §8.3); the rest (gap analysis 2.5 a–d) is unchanged and still open |
| A10 (changed) | honest; the source-record expedite matches §3.2, §6.1 and §14. Q1 concerns its mechanism, not its status |
| A13, A14, A17, A19, A20, A25 | statuses honest. A19's rest is incomplete (Q2); A14's design element is slightly overstated (Q4) |
| B.1 rows 2, 3, 4, 5, 8, 9, 13, 15 | honest. Row 4 ("designed", with forge support to verify under O14) still fits: O14 now also lists the deploy-key questions, and the tier table states the detected tier's residual (§15.2 item 5) |
| B.2 3.2, 3.4 (changed), 3.5, 3.7 | honest |
| B.4 | honest: trains, ancestry and the SESSION verdict are kept; the steward's train push now uses a deploy key (H14), which changes no keep item |
| C1 (changed), C10 (changed) | honest; each reason still holds |
| C2–C9, C11, C12 | honest; no changed section touches their reasons |

Ideas of the vision or gap-analysis items newly without a row: none. Revision 5 adds no difference from the vision that
lacks a section C reason. The detected tier and the guidance issue are design choices the keynote does not address.

## Part 3: new findings

### Q1 — The dispatcher must re-read AWS alarms and Security Agent findings, but its credentials cover only the forge
Severity: C
Location: design.md §3.2 (`priority` row: "a source record that the dispatcher re-reads read-only and confirms: a
CloudWatch alarm (ARN) in alarm state, or an exploitable AWS Security Agent finding"); §4.5 Dispatcher row; §14 ("Its
token scope: contents write (claim refs) and issues write"); §15.2 ("The dispatcher's token: contents write (claim
refs) and issues write (repairs), nothing more (§14)"); traceability C10, A10
Target: keynote slide 9 (the DevOps Agent and the Security Agent feeding the backlog); gap analysis §2.6 and §2.7.
Defect:
- The source-record confirmation is the dispatcher's job, but every place that lists the dispatcher's credentials
  limits them to two forge permissions. Re-reading an alarm's state needs a read-only AWS credential, and re-reading a
  Security Agent finding needs read access to that service's API. Neither is named, and §15.2 says "nothing more".
- §3.2 also does not say whether the confirmation holds only when the label is set, or continues after it. The
  dispatcher reverts a human-owned flag that nothing backs. Once the alarm returns to OK, which mitigation or a Track E
  restore does, a continuing check would revert the expedite on an incident whose fix is still open.
Proposed-edit:
- (Recommended) In §4.5, §14 and §15.2, give the dispatcher a read-only AWS role limited to reading alarm states and
  Security Agent findings for the project's accounts, held by the dispatcher's host only.
- In §3.2, add: "confirmed when triage sets it; a later return of the alarm to OK does not revert it".
- Alternatively, let triage attach the confirmation through the read-only failure-attributor credentials (§7.2), and
  have the dispatcher check only that the record exists.

### Q2 — Agents may change the automation that guards them, and the bank caveat's row does not say so
Severity: C
Location: design.md §19 item 14 ("Workers may change the automation that guards them; the checkers, not the forge, stop
a harmful change"), §3.5 ("Changes to privileged automation"), §12.10 (sensitive-path examples `iam/**`, `auth/**`);
traceability A19
Target: keynote slide 18 (the bank caveat: autonomy is a security question first); gap analysis §3.5 (human validation
for regulated users).
Defect:
- Revision 5's fix for tP1 lets workflow files, the steward's script and the deploy pipeline change through the queue,
  checked only by agents. §19 item 14 states that as a residual.
- A19 is the row for the bank caveat. Its rest names only the default-off approval setting and U24, not this residual.
- §12.10's sensitive-path approval is how a bank would put a human on exactly these files, but it lists `iam/**` and
  `auth/**` only, and the privileged-automation paths of §3.5 are not offered.
Proposed-edit:
- (Recommended) Add to A19's rest: "agents may change the automation that guards them, checked by agents only (§19
  item 14)".
- In §12.10, add the privileged-automation paths of §3.5 (`.github/workflows/**`, the steward's and the deploy
  pipeline's scripts, `templates/ci/**`) as a recommended sensitive-path set for a project that switches approval on.

### Q3 — §7.2's CLOSE-READY row still states the tag-only bound
Severity: D
Location: design.md §7.2 CLOSE-READY row ("its AWS role may delete only resources tagged `factory-issue=<repo>#<n>`
(tag-conditioned IAM)")
Defect: Since tP3, §11 item 1 and §15.1 rule 5 bound deletion per action. S3 objects are deleted by key prefix, because
their deletion cannot be tag-conditioned. §7.2 still says tag-conditioned only.
Proposed-edit: "its AWS role may delete only the issue's own temporary resources, bounded per action by tag or by name
prefix (§11)".

### Q4 — A14's design element says worker tokens lack the permissions behind irreversible operations
Severity: D
Location: traceability.md A14 ("per-host tokens without the permissions behind irreversible operations (§15.2)");
design.md §12.3 item 3, §15.2
Defect: In revision 5 the worker tokens keep "Actions: write". §12.3 item 3 says "A worker token can still dispatch a
trunk workflow, so WHEN a deploy runs is a standing permission". What guards the production deploy is the deploy role's
OIDC trust in trunk (§15.1 rule 5), not the token. §15.2 now names only deployment approval and repository
administration as missing permissions. A14's status ("partly aligned") is unaffected.
Proposed-edit: A14's design element: "per-host tokens without the deployment-approval and administration permissions
(§15.2); the deploy role's OIDC trust in trunk only (§15.1 rule 5)".
