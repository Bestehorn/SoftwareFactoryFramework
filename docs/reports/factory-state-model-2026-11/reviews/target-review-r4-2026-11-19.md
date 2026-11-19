# Target review, round 4: revision 4 of the factory state model against the keynote and the gap analysis (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `049a047`, read from a detached worktree:

- the full diff from `5dcc08f` for design.md, traceability.md, decisions.md (R57–R74) and review-response.md (Part 0);
- the unchanged parts of design.md where a traceability row depends on them.

Targets: the keynote deck (30 slides, text and speaker notes, extracted again in presentation order) and the gap
analysis of 2026-11-09. Both are untracked and excluded in the main checkout; neither was copied. Framing: decision
U22 (the keynote is a vision). Finding shape: `clients/common/docs/review-contract.md`. External facts are cited with
their source.

## Summary

**Verdicts on my 4 round-3 items** (tM1–tM4): 4 verified, 0 partly, 0 not fixed, 0 disputed.

**New findings:** 1 B, 3 C, 1 D (P1–P5; these finding ids are not design.md's principles P1–P13, which this report
always calls "principle Pn").

**Overall verdict: alignment and coverage hold, but revision 4's new mechanisms opened five small contradictions.**

- Every row that revision 4 touched is honest: A11, A16, A28 and 3.4.
- The rows it did not touch still match the design and both targets.
- Every vision idea and every gap-analysis item still has a row.

The new findings come from revision 4's own mechanisms:

- **P1 (B):** workers can no longer push workflow files, so every CI-workflow change needs the operator's own token.
  That is a human-only step, with no path in the state model. C1, principle P6 and U6 still say there are no
  human-only gates.
- **P2 (C):** the design says Kiro has no prompt-submit hook. Kiro's documentation lists one, so the Kiro fallback for
  `/get-guidance`, where the human posts every answer by hand, is not needed.
- **P3 (C):** S3 object deletion cannot be tag-conditioned, which the tM1 bound relies on.
- **P4 (C):** the label gate now refuses the `priority:critical` that C10 promises for exploitable pen-test findings.
- **P5 (D):** three sentences went stale with the explicit forms and the token rules.

OPEN ITEMS: 5

## Part 1: verdicts on my round-3 items

| Item | Verdict | Evidence in revision 4 |
|---|---|---|
| tM1 | verified | §15.1 rule 5 is now a bound: "never holds deploy credentials … AWS write credentials only when they are tag-conditioned … Deploys run only in CI". §11 item 1 says every team that creates temporary AWS resources creates only with the tag (`aws:RequestTag`) and deletes only tagged resources (`aws:ResourceTag`). It also states that issue text and finding excerpts reach the close-out "only under credentials scoped to the issue's own tagged resources". §18 Setup: "tag-conditioned create and delete permissions for every team that makes temporary resources"; R73. One service limit of this bound: P3 |
| tM2 | verified | A28 is "partly aligned. Rest: drift in documentation that no change touches is found only when a change touches it (§19 item 12)"; §19 item 12 adds "including for drift in documentation no change touches" |
| tM3 | verified | §4.2 "REWORK-REQUIRED → any exit": "the spec checkers confirm 'requirement' when they re-approve the amended criteria (tier S: the combined pass, §8.5)"; R74 |
| tM4 | verified | §16 lists 16 roles (counted), with the docs-drift checker moved to the `doc-reviewer-agent` split and the re-fold checker added; "grow the 20-agent twin set by 80 %"; traceability 3.4: "16 new roles" |

## Part 2: traceability.md, row by row, against revision 4

Revision 4 changed §3.2, §3.5, §4.2, §4.3, §4.5, §5, §6.3, §8.3, §8.5, §10, §11, §12.7, §12.9, §14, §15 and §16. I
re-checked every row against these sections and both targets.

| Rows | Verdict |
|---|---|
| A1–A9, A11–A20, A22–A28 | honest as written. A11 and A16 now say "for the exits §8.5 names", which matches design principle P4 and §8.5's new table; §19 item 5 lists every exit that has no separately started checker |
| A10 | honest, apart from the `priority:critical` clause it shares with C10 (P4) |
| A21 | honest, apart from what it inherits from C1 (P1) |
| B.1 rows 1–16 | honest. Row 3's "priority labels" stays accurate as the projection of `/priority`; the stale sentence behind it is P5 |
| B.2 3.1–3.3, 3.5–3.8 | honest |
| B.2 3.4 | honest on the count (tM4); P2 changes its Kiro-parity text |
| B.3, B.4 | honest |
| C2–C9, C11, C12 | honest; each reason still holds against revision 4 |
| C1 | no longer accurate (P1) |
| C10 | contradicted by §3.2 (P4) |

Vision ideas without a row: none that is a loop or a control.

Gap-analysis items without a row: none.

Differences without a reason in section C: one, the human-only workflow-file change (P1).

## Part 3: new findings

### P1 — Every change to a workflow file now needs the operator's own token: a human-only step with no path
Severity: B
Location: design.md §3.5 "Both: no worker-writable path to a write token" (last bullet: "a change to a workflow file
is landed with the operator's own token, as a reserved decision"), §15.2, §10.8 H7, §7.2 (`ci-workflow-agent` is an
IMPLEMENTATION-READY maker), §1 principle P6; decisions.md U6, R57; traceability.md C1, A21
Target: keynote slides 3, 4 and 6 (loops that run without the engineer pushing every step); gap analysis row 15 and
§3.5 (human validation as a configurable point, not a fixed gate).
Defect: Revision 4 removes the "Workflows" permission from worker tokens, so GitHub refuses any worker push that adds
or changes a file under `.github/workflows/`. The design then makes every such change a reserved decision, landed with
the operator's own token. Three things follow, and none is recorded:
- **The design contradicts itself.** Principle P6 still reads "No human-only stage or gate", U6 "No stage or gate that only a
  human can pass", and C1 "no human-only gates". CI-workflow changes are ordinary work: `ci-workflow-agent` is a maker
  of IMPLEMENTATION-READY.
- **No path exists.** Nothing routes an issue whose fix needs a workflow change:
  - no stage, flag or queue row;
  - no entry on the always-ask list (§12.4);
  - no `needs-input` kind.

  The worker's push is simply refused. The IAM-grant case has a path (§10.5: "`needs-input` of kind approval: the
  human is asked only for the grant"); this case has none.
- **The difference has no section C row.** It is a difference from the vision of unattended loops, so under U22 it
  needs one.
Material-because: wrong-behaviour, since an issue needing a workflow change stalls with no owner. The section C record
and principle P6 are also contradicted. The underlying decision belongs to the operator (U6).
Proposed-edit:
- (Recommended) Give this case the IAM-grant path: add "a change under `.github/workflows/`" to the always-ask list
  (§12.4). The worker commits everything else and leaves the workflow change as a patch in its `needs-input` of kind
  grant; the operator lands that patch with their own token.
- Add the exception to principle P6 and to C1's "design says" column, with the reason from §3.5 (no worker-writable
  path to a write token). Record it as an operator decision amending U6.
- Note the limit on `ci-workflow-agent` in §7.2.
- Alternative: let only the steward land workflow-file changes from a default-branch job, after the full checker set,
  with a token that holds "Workflows". Then decide whether that re-opens the path aN7 closed.

### P2 — Kiro has a prompt-submit hook, so `/get-guidance` needs no hand-posting fallback there
Severity: C
Location: design.md §12.9 step 4 ("where no such hook exists (Kiro today), the command instead prints the form lines,
and the human posts them on each issue"); decisions.md R62; traceability.md 3.4
Target: gap analysis §3.4: Kiro parity is "the gap they would hit first".
Defect: Kiro's hook documentation lists a **Prompt Submit** trigger, available in the IDE, the CLI and Kiro Web, that
"Triggers when the user submits a prompt". A shell action can read the prompt through `USER_PROMPT` (kiro.dev/docs/hooks/types/, "Hook
triggers", seen 2026-11-19). That is the property §12.9 relies on in Claude Code: "an agent cannot type a user prompt".
The documentation notes that the CLI's Prompt Submit hooks "cannot block", but recording that the human typed
`/get-guidance` needs no blocking. So the stated reason for the Kiro fallback does not hold, and the fallback makes
Kiro humans post every answer by hand. No Kiro hook in `clients/kiro/` uses this trigger today (grep: no match).
Proposed-edit: In §12.9 and R62, use Kiro's Prompt Submit hook as the Kiro counterpart of `UserPromptSubmit`. Keep
"print the form lines" only for a surface that lacks the trigger. Verify the trigger in the phase-2 renderer's Kiro
output.

### P3 — S3 object deletion cannot be tag-conditioned, so the tM1 bound needs a name scope too
Severity: C
Location: design.md §11 item 1 ("create only with the issue's `factory-issue` tag (`aws:RequestTag`); delete only
resources carrying it (`aws:ResourceTag`)"), §15.1 rule 5, §18 Setup row
Target: gap analysis §2.4 (agents that read logs and act on them); the trust rule that makes that safe.
Defect: The bound is stated in two condition keys that some services do not offer for the actions that matter. The
Amazon S3 User Guide says, of `s3:ExistingObjectTag`: "When granting permissions for the PUT Object and DELETE Object
operations, this condition key is not supported. That is, you cannot create a policy to grant or deny a user
permissions to delete or overwrite an object based on its existing tags." (docs.aws.amazon.com, "Tagging and access
control policies"). S3 objects also use `s3:RequestObjectTag`, not `aws:RequestTag`. §11 lists "staged uploads" among
the resources, and its motivating case is 1,000 of them. §11's naming fallback ("named with that prefix where the
resource type has no tags") covers types without tags, not actions that cannot be tag-conditioned.
Proposed-edit:
- In §11 and §15.1 rule 5, state the bound per action: tag-conditioned where the action supports it; otherwise scoped
  by resource name, e.g. an S3 key prefix `factory-issue-<repo>-<n>/` in the policy's resource ARN; otherwise not
  granted to an agent session at all.
- Extend the naming fallback to "where the type has no tags, or the action cannot be conditioned on them".

### P4 — The label gate refuses the `priority:critical` that C10 promises for exploitable pen-test findings
Severity: C
Location: design.md §3.2 (`priority` row and "Human-owned flags"), §7.2 TEST-READY row ("exploitable ones as
`priority:critical`"); decisions.md R55, R61; traceability.md C10, A10
Target: keynote slide 9, notes (a pen test that reports what it could actually exploit); gap analysis §2.7 (b).
Defect: Revision 4 makes `priority:*` human-owned. Triage "may set `priority:critical` only on an `Origin: production`
issue a factory login filed". The wrapper refuses any other agent write of the label, and the dispatcher reverts one
no form backs. A pen-test finding enters START as an agent-filed issue, not `Origin: production`. So §7.2, R55 and C10
promise a label that §3.2 now forbids, and the expedite C10 gives as part of its reason does not happen.
Proposed-edit:
- (Recommended) Extend §3.2's triage exception: "or an exploitable pen-test finding a factory login filed (`Origin:
  pen-test`)", with the same author check as §6.1.
- Alternatively, delete "exploitable ones as `priority:critical`" from §7.2, R55 and C10, and let those findings wait
  for the human's `/priority`.

### P5 — Three sentences went stale with the explicit forms and the token rules
Severity: D
Location: design.md §14, §12.6; decisions.md B16
Defect:
- §14: "The human sets priority with labels". Since R61, priority changes only through `/priority`, and a hand-set
  label is reverted (§3.2).
- decisions.md B16: "an `admitted` label set by an authorised human (revised by R6)". It is now set by the recorder
  from `/admit`, as an `admitted {ask_hash}` record (R61, R64).
- §12.6 still gives the example "agents may dispatch the prod deploy after a green stage". Worker tokens now lack
  "Actions: write" (§3.5), and rule 5 says "Deploys run only in CI".
Proposed-edit:
- §14: "The human sets priority with `/priority` (§3.2)."
- B16: "(revised by R6, R61, R64: `/admit`, recorded with the ask hash)".
- §12.6: replace the example with one the tokens allow, e.g. "the steward may dispatch the prod deploy after a green
  stage".
