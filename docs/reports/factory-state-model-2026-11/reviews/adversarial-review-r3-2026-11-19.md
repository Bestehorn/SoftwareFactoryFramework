# Adversarial review of the factory state-model design, revision 3 (2026-11-19)

**Verdicts on the 44 items of review-response.md Part 1 that came from the round-2 adversarial report:**
43 verified, 1 partly (aN7), 0 not-fixed, 0 disputed.

**New findings on revision 3's additions (M1–M15):** A 0, B 7 (M1–M7), C 7 (M8–M14), D 1 (M15).

OPEN ITEMS: 16

---

## Scope

**Subject.** Revision 3 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`5dcc08f`. Read in full: `docs/design/factory-state-model/design.md` and `review-response.md`. Read in part:
`decisions.md` (R34–R56, O12, O14, O15). `traceability.md` was not reviewed. The review ran in a session independent of
the designer's, from a detached worktree, read-only.

**Product code read to check the design's claims:**

- `src/payload/scripts/merge_steward.py`: `eligibility`, `plan`, `reject`, the train merge message (`Steward-PR`,
  `Steward-PRs` and the other trailers);
- `src/payload/scripts/github_api/commands/call.py`: `GATED_OPERATIONS`;
- `templates/ci/github-deploy.yml.template`, in full;
- `templates/ci/github-merge-steward.yml.template`: the tick job's `permissions`.

**Platform facts** come from GitHub's documentation, named where each is used, and from `docs/api-reference/`.

**Ids.** Round-2 findings are cited as `aN<n>`, the designer's naming in review-response.md (they were `N<n>` in the
round-2 report). Revision-1 findings keep their ids (A1, B7, …).

**Operator decisions respected:**

- **U21:** equal scrutiny. Authorship matters only for reserved decisions.
- **U24:** the agents keep posting as the operator's account. This review does not argue for another identity. It tests
  only whether §15.2 states the residual at its true size.

**A disclosure.** Four of the mechanisms faulted below were proposed in my own round-2 report:

- M2: the revert fact written only for steward-opened reverts (round-2 N7, edit 1);
- M3: the pin on the run-level conclusion (round-2 N10);
- aN7's remainder: the activity check keyed on the steward's actor (round-2 N7, edit 1);
- M14: the per-tick check of the Actions setting (round-2 N8, edit 2).

The designer applied them as proposed. The defects are in the proposals.

---

## Summary

Revision 3 closes almost everything round 2 raised:

- every caller of the verb holds the claim ref, and the steward alone calls TEST-READY's exits;
- the claim ref is permanent, with `held` and `free` commits;
- branch pushes go out atomically with the claim renewal;
- every agent comment and body write is marked;
- human input counts only through explicit forms;
- the revert fact sits on the steward's own first-parent merge;
- the deploy fact is pinned to a run read from the run API.

What remains is at the edges of those mechanisms. Each one covers the path it was designed for, and a neighbouring
path is left open:

- the separately started checkers have no queue to start them;
- the explicit forms other than `/answer` have no executor;
- human-owned flags are still plain label writes;
- the run-level conclusion is not the deploy verdict.

### Answers to "what the next review should check (revision 3)"

| Item | Answer |
|---|---|
| 1. Every caller holds the claim; the steward is the sole caller of TEST-READY's exits | Holds as designed. Open: a steward that backs off on a held ref can lose a return (M8); a `/stage` on a TEST-READY issue has no path that keeps the steward the only writer (M6) |
| 2. Permanent claim ref, `held`/`free` commits, atomic pushes | Holds for the wrapper's path. Open: the cursor alone cannot resume a fold (M9); renewal cadence (M10); a plain `git push` is unfenced (M11); the continuation issue (M12) |
| 3. Marking, explicit forms, and §15.2's residual at its true size | Marking and forms hold for comments. §15.2 still understates, in three ways: human-owned flags are label writes (M4); `/get-guidance` posts a marked form that counts (M5); trunk is reachable through a workflow a worker writes (aN7). Also `/amend` and `/stage` have no executor (M6), and an outsider can rewrite an admitted issue (M7) |
| 4. The queue table | Nothing starts the separately started spec checker or the log-scan lane (M1); the lane rows churn, and `tamper` has no re-fold queue (M13) |
| 5. `Steward-Reverts`, the pinned run, the ruleset and activity check, the Actions-may-create-PRs check | A revert landed through any other PR is invisible (M2); the run conclusion and `head_sha` are not the deploy verdict (M3); the ruleset cannot single out the steward's `GITHUB_TOKEN` (aN7); the steward's token cannot read the Actions setting (M14) |
| 6. The in-session boundary of §8.5 | Stated truthfully. Open: §4.1's universal clause names exits §8.5 gives no checker (M1) |

---

## 1. Verdicts on the round-2 items (review-response.md Part 1)

### Revision-1 findings judged "partly" in round 2

| Id | Verdict | Where revision 3 fixes it | Note |
|---|---|---|---|
| A1 | verified | §4.2 TEST-READY → REWORK-REQUIRED (every reject, closed PR); §4.5 conductor, arbiter, question checker and dispatcher rows; the `split` close; §4.4 the reconciler completes or undoes only | — |
| A4 | verified | §8.2 marking of every comment and body write; §8.3 explicit forms only | Label writes are not covered by marking (M4) |
| B1 | verified | §5.1 atomic branch + claim push; renewal on writing calls; expiry by a `free` child; §19 items 2 and 3 | The atomic push is not enforced (M11) |
| B2 | verified | §4.4 every caller holds the claim; the reconciler touches only free-claim issues with intents older than L | — |
| B4 | verified | §12.7 started only on an explicit form newer than the last run; free text verbatim | — |
| B5 | verified | §4.3 the ask is above the machine-owned marker; the wrapper refuses an agent edit above it | Author edits of an admitted issue (M7) |
| B6 | verified | §8.5 boundary stated; a separately started checker per stage exit | Nothing starts it (M1) |
| B7 | verified | §10.8 H7 landings from first-parent history; `Steward-Reverts` | Trunk protection: aN7 |
| B9 | verified | §3.5 trunk ruleset; dispatcher scope in §4.5, §14, §15.2 | The direct push is closed; the workflow path is aN7's remainder |
| B10 | verified | §15.2 lists the sources; `writes=` measures them; no estimate claimed | — |
| B14 | verified | §10.4 step 3: dispatch of the revert PR's CI; exemption keyed on identity + exact revert content | The setting check: M14 |
| B17 | verified | §10.3 step 4 and §10.6: detector and migration ledger in the Minimum tier; digest in S3 object metadata | — |
| C4 | verified | §5.1 the cursor lives in `held` and `free` commits | The cursor is not enough to resume a fold (M9) |
| C9 | verified | §3.2 and §4.2 the dispatcher closes `split` parents; `split` excluded from worker queues | — |
| C16 | verified | §4.4 hand-set stage labels are reverted; `/stage` | `/stage` has no executor (M6) |
| C17 | verified | §5.1 renewal in the wrapper; L from `step-seconds` | Cadence (M10) |
| C21 | verified | §8.2 `tamper`; §13 restated; deletion stays §19 item 6 | Clearing `tamper` (M4, M13) |

### Remarks on verified findings

| Id | Verdict | Note |
|---|---|---|
| A2 | verified | §8.1 bounds `actor.agent` by §8.5 |
| B3 | verified | §14 lane exclusions. The rows lack "no claim" (M13) |
| B13 | verified | §12.5 `env-incident` issues have no stage and are in no worker queue |
| B15 | verified | §10.8 H1 per PR from first-parent trailers. Reverts outside Track T: M2 |
| C2 | verified | §4.2 the `ci-pending` timeout; §7.3 the hand-offs row |
| C18 | verified | §10.4 step 4: a revert PR that cannot be created is an immediate `env-incident` |
| C20 | verified | §5.3 group claims in one atomic push |
| C22 | verified | §8.7 the overrule is computed |

### Round-2 findings aN1–aN16

| Id | Verdict | Note |
|---|---|---|
| aN1 | verified | §4.4, §4.5, §5.3: every caller holds a claim; §3.1 TEST-READY's exits are the steward's. The back-off: M8 |
| aN2 | verified | §4.5 rows complete |
| aN3 | verified | reject and closed-PR returns, the `ci-pending` timeout, `env-incident` outside worker queues, the recorder condition, lane exclusions and the `split` close are all present. New strands from revision 3's own additions: M1, M6 |
| aN4 | verified | §5.1–§5.4 permanent ref, CAS on the observed tip, atomic pushes. Notes: M9–M12 |
| aN5 | verified | the three items of the round-2 finding are fixed: marking, no label override, the forge-gate limits stated in §12.3 item 3. Paths revision 3 does not cover: M4, M5 |
| aN6 | verified | §4.3 marker |
| **aN7** | **partly** | `Steward-Reverts` and the PAT path are fixed; trunk is still reachable through a worker-authored workflow, and the activity check cannot tell. See §2 |
| aN8 | verified | setup enables the setting; a refused creation is an immediate `env-incident`; the exemption is keyed on content. The per-tick check cannot be made as written (M14) |
| aN9 | verified | §8.5 boundary and separately started checkers. Nothing starts them (M1) |
| aN10 | verified | §4.2 the pin. The pinned field is not the deploy verdict (M3) |
| aN11 | verified | §3.2 `hold`; R44 `eligibility` waits on a held issue |
| aN12 | verified | §7.3 hand-offs row |
| aN13 | verified | §8.3, §12.7 |
| aN14 | verified | §10.6 Minimum tier |
| aN15 | verified | §8.2 `tamper`; §13 |
| aN16 | verified | §3.3 "Not a stage: env-incident issues" |

### Section 3 of the round-2 report

| Item | Verdict | Note |
|---|---|---|
| O14 extended | verified | §5.5 and §19 item 1 list atomic multi-ref pushes, workflow triggers on custom refs, and the ruleset actor |
| U21 consistency | verified | the label override (§4.4) and the recorder's interpretation (§12.7) are removed |
| Write budget | verified | §15.2 and §19 item 7: measured, not estimated |

---

## 2. The remainder of aN7 (B): trunk is reachable through a worker-authored workflow

- **Location:** §3.5 "Forge setup required in factory mode"; §4.5 "Facts are taken from where they cannot be forged";
  §10.8 H7 "Fix, second part"; §15.2 "What limits it".
- **Target quote:** "The trunk ruleset and the pinned run facts (§3.5, §4.5) close the delivery side, which does not
  rely on comment authorship."
- **Defect.** The steward pushes trunk with the workflow's `GITHUB_TOKEN` (§4.5 Steward row). The tick job declares
  `contents: write` (`github-merge-steward.yml.template`). That gives a dilemma:
  1. **The ruleset cannot exempt the steward's push.** The steward cannot land anything.
  2. **It exempts the GitHub Actions identity.** Every workflow run in the repository gets a `GITHUB_TOKEN` of that same
     identity. A workflow file a worker adds on its issue branch, triggered by `on: push`, runs from that branch. It can
     declare the same `permissions: contents: write` block the steward's template declares, and push trunk as the
     steward would.

  In both cases "a trunk ruleset that blocks updates by anyone but the steward" is not something a ruleset can express.
  Nothing in §15.2 takes the Workflows permission away from the worker tokens. The independent check does not separate
  the cases either:
  - H7 has the steward confirm that "the push was made by the steward's actor", from the activity record;
  - that actor is the same GitHub Actions bot;
  - H7's own next bullet says a workflow on a worker's PR branch "can also post as `github-actions[bot]`".

  §19 item 1 and §3.5 leave "which actor a GitHub ruleset can exempt" to O14. The dilemma above holds whatever O14
  finds.
- **Material-because:**
  - B7 and H1: forged first-parent history carries `Steward-PR` and `Steward-Reverts` trailers, which are the landing
    and revert facts of TEST-READY → CLOSE-READY;
  - §15.2's claim to state the residual at its true size.
- **Evidence:**
  - design.md §3.5, §4.5 (Steward row and the `github-actions[bot]` sentence), §10.8 H7, §15.2;
  - `templates/ci/github-merge-steward.yml.template`, the tick job's `permissions` (`contents: write`);
  - GitHub Docs, "Use GITHUB_TOKEN for authentication in workflows": the token's access is set per workflow and per job
    with the `permissions` key.
- **Proposed edit (recommended first):**
  1. **Take away the means of adding a workflow.**
     - The worker tokens lack the fine-grained "Workflows" permission, so no worker push can add or change a file under
       `.github/workflows/`.
     - A change to a workflow file is landed with the operator's own token, as a reserved decision.
     - Every factory-installed workflow that runs branch code declares `contents: read`.
     - §10.8 H7 restates the activity check as "pushed by GitHub Actions", and §15.2 says what closes the delivery
       side: no worker-writable workflow can obtain a write token.
  2. **Give the steward a trunk credential no other workflow can read.** A deploy key or GitHub App key is stored as a
     secret of an environment whose deployment branches are limited to the default branch, and the ruleset bypass names
     only that credential.
     - Environments in private repositories need GitHub Pro, Team or Enterprise.
     - Whether a ruleset can name a deploy key as bypass actor goes into O14.
  3. Keep the design and restate §15.2: the delivery side is closed against a worker token's direct push, not against
     an agent that writes a workflow.

---

## 3. New findings

### M1 (B): the separately started checkers have no queue that starts them, and §4.1 requires one at exits §8.5 does not cover

- **Location:** §4.1 the checker sentence; §8.5 table; §14 queue table; §7.3 tier-S table, Close-out row; §11 item 2.
- **Target quote:** "At least one of those verdicts comes from a separately started checker (§8.5)."
- **Defect:**
  1. **Nothing starts them.**
     - §8.5 defines a separately started checker as "a session the dispatcher starts, which holds a `verify` claim and
       posts its own records".
     - The dispatcher starts roles only from the §14 queues. The checker-lane row needs "`review-verify` with a
       resolution waiting for that lane". A first review of a spec, or a log scan at CLOSE-READY, has no resolution
       waiting. The verifier row covers only `ci-pending`.
     - So nothing starts the M/L spec checker of SPEC-REQUIRED → IMPLEMENTATION-READY, or the log-scan lane of
       CLOSE-READY → closed. The predicate cannot hold, and both stages strand, the failure class behind decision A2
       (0 of 10 hand-offs closed).
  2. **§4.1 is stated for every predicate, but §8.5 names checkers for four exits only.**
     - START → SPEC-REQUIRED, START → closed and START → split have no separately started checker.
     - CLOSE-READY → closed has none for tier S: the §7.3 Close-out row lists no log-scan lane.
     - It also has none for a project without a read-only log query: §11 runs the lane only "where the project provides"
       one.
     - Read literally, those exits can never be taken. Read loosely, P4's "every stage exit that closes a stage" and
       §19 item 5's "every stage exit has a separately started checker" overstate.
- **Material-because:**
  - liveness of SPEC-REQUIRED (M/L) and CLOSE-READY;
  - P4 and §4.1, the rule that makes predicates deterministic.
- **Evidence:** design.md §4.1, §4.2 (START rows), §7.3, §8.5, §11 item 2, §14, §19 item 5.
- **Proposed edit (recommended first):**
  1. **A request flag and a queue row.**
     - The maker's verb call that ends its in-session work sets `checker-requested:<lane>` and releases.
     - §14 gains the row: `checker-requested:<lane>`, no claim, none of `hold`, `needs-input`, open `blocked-by` or
       `tamper`; it starts that lane with a `verify` claim, and the lane clears the flag with its verdict.
     - §8.5's table gains the START exits (the triage checker for M/L, the duplicate-confirmer for a close) and states
       the CLOSE-READY cases without a lane as recorded trade-offs, like tier S's spec.
     - §4.1 reads "where §8.5 names one".
  2. Narrow §4.1, P4 and §19 item 5 to IMPLEMENTATION-READY → TEST-READY and the REWORK exits to TEST-READY, the
     exits whose separately started checker (the verifier) has a queue. The M/L spec checker and the log-scan lane then
     run in-session, and §19 item 5 records that as a trade-off.

### M2 (B): a revert that the steward did not open is never a revert fact, so the reverted PR's issue closes

- **Location:** §10.4 step 3; §10.8 H1 "Fix"; §4.2 TEST-READY → CLOSE-READY and TEST-READY → REWORK-REQUIRED.
- **Target quote:** "When the steward lands a revert PR, it writes `Steward-Reverts: PR #<n> <merge sha>` into its own
  first-parent merge commit."
- **Defect:**
  - The only rule the design gives for recognising a revert PR is the steward-opened one: "a PR that the steward's
    identity opened AND whose head is exactly `git revert -m 1` of a first-parent steward merge".
  - A revert opened any other way lands as an ordinary PR, with `Steward-PR: #<revert PR>` only. Examples: the
    operator's revert button on a bad PR, or a worker's `git revert -m 1` on its rework branch.
  - The reverted PR's landing is then never superseded. The next green deploy contains both commits, so the TEST-READY
    → CLOSE-READY predicate holds, and the issue closes with its code gone. That is H1's failure, reached by a path
    revision 3 opened when it narrowed the fact to steward-opened reverts.
  - §4.2 has no TEST-READY → REWORK-REQUIRED cause "reverted outside Track T" either.
- **Material-because:** H1, B15, and TEST-READY → CLOSE-READY, the edge that leads to closing.
- **Evidence:** design.md §4.2, §10.4 step 3, §10.8 H1; `merge_steward.py`, the train merge message (`Steward-PR`,
  `Steward-PRs`).
- **Proposed edit (recommended first):**
  1. **Key the fact on content, and the privileges on identity.**
     - At landing, the steward writes `Steward-Reverts: PR #<n> <merge sha>` for ANY landed PR whose net diff is exactly
       the inverse of a first-parent steward merge's first-parent diff.
     - The opener check keeps only the CI exemption and the revert-first ordering.
     - §4.2 gains the cause "a revert of this PR landed outside Track T" on TEST-READY → REWORK-REQUIRED (steward).
     - A partial revert is an ordinary change. Say so in §19.
  2. `eligibility` rejects an exact revert of a steward merge that the steward did not open, with "reverts go through
     Track T". This is simpler, but it takes the revert button away from the operator.

### M3 (B): the pinned run's conclusion and commit are not the deploy-and-smoke verdict

- **Location:** §4.2 TEST-READY → CLOSE-READY (the pin); §10.3 step 4; §10.4 step 4; §10.8 H3, H13.
- **Target quote:** "conclusion `success`, read from the run API) and ran on a commit D that contains every such
  landing".
- **Defect:**
  1. **A skipped deploy concludes green.**
     - §10.4 step 4: "the deploy job skips trunk commits that contain an attributed culprit without its revert".
     - GitHub Docs, "Using conditions to control job execution": "A job that is skipped will report its status as
       'Success'."
     - So a run that deployed nothing can conclude `success`, and every innocent landing it contains passes the
       predicate without a deploy.
  2. **A restored run can conclude green.**
     - Track E restores "INSIDE THE SAME RUN" (§10.3 step 4). Nothing says the run must then conclude failure.
     - H3's `<env> serving <sha> (restored)` record is not part of the pin.
  3. **The commit is the wrong field.**
     - For `workflow_dispatch` the run's `head_sha` is the dispatched ref's tip. The template deploys
       `ref: ${{ inputs.sha || github.sha }}`.
     - The run object carries no inputs. A dispatch for an earlier commit (a re-deploy, or a dispatch after a later
       landing) makes "ran on a commit D" read the wrong commit.
  4. The template's own verdict job already computes the verdict from job results
     (`needs.deploy.result == 'success' && needs.e2e.result == 'success'`). Revision 3 replaced that with the run-level
     field.
- **Material-because:** TEST-READY → CLOSE-READY; P11. A false CLOSE-READY closes an issue that was never deployed.
- **Evidence:**
  - `templates/ci/github-deploy.yml.template`: the `deploy` and `e2e` checkouts and the verdict expression;
  - `docs/api-reference/github/rest/actions.md`: `actions/create-workflow-dispatch` takes `return_run_details`;
  - GitHub Docs, "Workflow syntax": `run-name` may reference the `inputs` context;
  - design.md §10.3, §10.4, §10.8 H3, H13.
- **Proposed edit (recommended first):**
  1. **Pin the run the steward dispatched, and the jobs.**
     - The steward dispatches with `return_run_details` and records `dispatched run <id> for <sha>`.
     - The pin reads that run id and that sha. For a `push` run, `head_sha` is the deployed commit.
     - From the jobs API, it requires the deploy job and the smoke job to conclude `success`, and no restore step to
       have run.
     - A restored or skipped deploy makes the run conclude `failure` explicitly.
  2. Put the sha in `run-name` (returned as `display_title`), and pin the job conclusions as in option 1.

### M4 (B): human-owned flags are plain label writes, which any agent inside the wrapper can make

- **Location:** §3.2 rows `hold`, `priority`, `admitted`, `tamper`; §6.3; §8.2 "Marking"; §15.2 residual item 1 and
  "What limits it".
- **Target quote:** "The marking gate means a cooperating agent can no longer impersonate the operator by accident: an
  ordinary note never counts."
- **Defect:**
  - §3.2 says these flags are set or cleared by "an authorised human":
    - `admitted` (the admission gate for text that "may direct agents that can push code and deploy to AWS", §6.3);
    - `hold` (set and cleared);
    - `priority:*`;
    - clearing `tamper`.
  - Marking covers "every comment and body write". Labels are neither, and `call.py`'s `GATED_OPERATIONS` gates no
    label operation.
  - Under U24 a label event's actor is the operator's login whoever wrote it.
  - §4.4 reverts a hand-set STAGE label, but nothing reverts these flags.
  - So an ordinary agent working through the wrapper's additive label commands can, by mistake, admit an outsider's
    issue, lift a hold or clear `tamper`. An agent tidying labels or a housekeeping pass is enough; no compromised
    agent is needed.
  - §15.2 item 1 names only "an agent that bypasses the wrapper".
- **Material-because:**
  - §6.3 admission;
  - §3.2 `hold`;
  - §8.2 `tamper`;
  - U24: the residual must be stated at its true size.
- **Evidence:** design.md §3.2, §4.4, §6.3, §8.2, §15.2; `src/payload/scripts/github_api/commands/call.py`
  `GATED_OPERATIONS` (no label operation).
- **Proposed edit (recommended first):**
  1. **Forms for the human flags.**
     - These flags change only through explicit forms (`/admit`, `/hold`, `/unhold`, `/priority <level>`,
       `/clear-tamper`), which the recorder applies.
     - The wrapper refuses an agent's add or remove of these labels.
     - The dispatcher reverts such a label that no form backs, as §4.4 does for stage labels.
  2. Keep the labels, and restate §15.2 item 1 and the "by accident" limit: any agent using the wrapper's label
     commands can admit, unhold, reprioritise or clear `tamper` as the operator.

### M5 (B): an agent inside the wrapper can post a counted answer through the `/get-guidance` mark

- **Location:** §12.9 step 4; §8.3; §12.3 item 1; §12.7; §4.5 Answer recorder row; §15.2 residual item 1.
- **Target quote:** "It posts the answer as an explicit form quoting the human's words, marked as posted through
  `/get-guidance` by the human's login."
- **Defect:**
  - §8.3 accepts explicit forms "in an unmarked comment". §12.9 makes a MARKED comment count as an explicit form.
  - The mark is written by the wrapper for whatever agent context calls it with that mark. So any agent that runs
    through the wrapper with the `/get-guidance` mark answers a question, including a reserved one: an IAM grant, a
    deletion, production.
  - That contradicts §12.3 item 1 ("an ordinary agent note can never pass as an answer"). §12.9 itself says "as provable
    as any agent write", but §15.2 item 1 says forging an answer needs "an agent that bypasses the wrapper".
  - Separately, the recorder's `factory: answer … (by <login>, comment <id>)` records count by role. The role is one
    the writer declares, and the design does not say the fold re-checks the cited comment.
- **Material-because:**
  - §12.3 reserved decisions and the always-ask list (§12.4);
  - U24: the residual must be stated at its true size.
- **Evidence:** design.md §4.5, §8.3, §12.3, §12.7, §12.9, §15.2.
- **Proposed edit (recommended first):**
  1. **Only unmarked forms count, and the fold checks them.**
     - `/get-guidance` prints the exact form lines for the human to post in the forge, one comment per batch with one
       form per line. §8.3 must then allow several form lines in one comment.
     - The fold accepts a recorder record only when the cited comment exists, is unedited, is unmarked, is an explicit
       form, and its author is on the allow-list.
  2. Keep `/get-guidance` posting.
     - The wrapper accepts that mark only from the command's own entry point, a gate keyed on the command like the
       marking gate.
     - The digest lists every answer posted that way.
     - §15.2 item 1 adds "or uses the `/get-guidance` path".

### M6 (B): `/amend`, `/stage` and an edit above the marker have no executor, and their backward edges do not exist

- **Location:** §8.3 table; §4.3 first bullet; §4.2 table; §4.5 Authorised-human and Answer-recorder rows; §14
  recorder row.
- **Target quote:** "An authorised human changes the ask by editing above the marker, or with `/amend <text>`. Either
  sends the issue back to SPEC-REQUIRED".
- **Defect:**
  1. **No edge.** §4.2 has no IMPLEMENTATION-READY → SPEC-REQUIRED edge and no predicate for a human-requested move. A
     verb asked for one refuses ("the caller's role may not call this edge").
  2. **No caller.**
     - The authorised human acts "through explicit forms only" and holds no claim.
     - The recorder queue needs `needs-input` (§14), so an `/amend` or a `/stage` on an issue without `needs-input`
       starts nothing.
  3. **Strand.** After an ask change in IMPLEMENTATION-READY, every pickup fails §4.3's "The ask is unchanged since
     approval", and no edge leads out. The issue strands.
  4. **TEST-READY.** A `/stage` there has no path that keeps "its exits written by the steward alone" (§3.1).
- **Material-because:**
  - liveness of IMPLEMENTATION-READY after an ask change;
  - C16, whose fix replaced the label override with `/stage`;
  - P12.
- **Evidence:** design.md §3.1, §4.2, §4.3, §4.5, §8.3, §14.
- **Proposed edit (recommended first):**
  1. **The recorder executes every form, and the edges exist.**
     - The recorder row counts any explicit form newer than its last run, with or without `needs-input`.
     - §4.2 gains IMPLEMENTATION-READY → SPEC-REQUIRED (recorder), whose predicate is that the ask hash differs from
       `spec-approved`'s or an `/amend`/`/stage` form names it.
     - A `/stage` whose target is not an edge of §4.2 is refused with a record.
     - On TEST-READY the recorder posts a steward request record, which the steward applies or refuses at its next
       tick.
  2. Drop `/stage`, and accept `/amend` only in START and SPEC-REQUIRED. Elsewhere it is refused with "file a new
     issue". An edit above the marker still needs the IMPLEMENTATION-READY → SPEC-REQUIRED edge.

### M7 (B): an admitted outsider can rewrite the issue after admission

- **Location:** §6.3; §3.2 `admitted`; §4.3 first bullet.
- **Target quote:** "Everything else … waits for an `admitted` label set by an authorised human".
- **Defect:**
  - GitHub Docs, "Editing an issue": issue authors can change their own issue's title and description.
  - `admitted` names no ask hash, and §4.3's hash check runs only in SPEC-REQUIRED and IMPLEMENTATION-READY, against
    `spec-approved`, not against what was admitted.
  - An outsider can therefore get a harmless ask admitted, then rewrite it:
    - before triage, which reads the new text;
    - or after spec approval, which sends the issue back to SPEC-REQUIRED (M6), where the spec team works from the new
      text.
  - In both cases the admission label stays.
- **Material-because:** §6.3's purpose, B8 and C13: text from outside the allow-list must not direct agents that push
  code and deploy.
- **Evidence:** design.md §3.2, §4.3, §6.3; GitHub Docs, "Editing an issue".
- **Proposed edit (recommended first):**
  1. **Admission names the ask.**
     - Admission is a record, `admitted {ask_hash}`, with the label as its projection.
     - Every pickup of an issue whose author is not on the allow-list compares the current ask hash with the admitted
       one. On a mismatch the issue drops to read-only mode, with a new admission view.
  2. On admission, triage copies the admitted ask verbatim into a new issue authored by the factory login and closes the
     outsider's issue administratively, linking the two.

### M8 (C): a steward that backs off on a held ref can lose a TEST-READY return

- **Location:** §5.3 "Record claims"; §4.2 TEST-READY → REWORK-REQUIRED; §14 "the steward drives it on every tick".
- **Target quote:** "When the ref is held, they back off and retry on their next tick or poll."
- **Defect:** `reject()` removes the queue label and comments before it returns the issue, and `plan()` iterates only
  queued PRs. If the record claim is refused at the return, the PR is no longer queued at the next tick, and TEST-READY
  has no worker queue. The design does not say that a tick re-derives TEST-READY's exits for every TEST-READY issue.
- **Evidence:** `merge_steward.py` `reject`, `plan`; design.md §5.3, §14.
- **Proposed edit:** state that every tick evaluates both TEST-READY exits for every TEST-READY issue from durable
  facts (the `merge-steward:` reject line, PR state, trunk trailers, the pinned run), so a backed-off return is retried.

### M9 (C): the cursor alone cannot resume a fold

- **Location:** §8.2 "Reading"; §5.1 `held`/`free` commits.
- **Target quote:** "The last folded id is the cursor in the claim ref's commits … so a new holder never full-scans."
- **Defect:** a fold's state (open findings, verdicts per SHA, pending questions) is not in the cursor. A new holder
  that knows only the last folded id must re-fold from the first record to know what is open. Also, edited earlier
  records are found only by `updated_at`.
- **Proposed edit:** the `held`/`free` commit carries a tree with the folded state at the cursor, written by the release
  verb. A new holder reads it and fetches comments with `since` = the last fold's time, which returns both new and
  edited comments, so `tamper` detection needs no full scan either.

### M10 (C): renewal depends on REST-writing calls whose cadence is undefined

- **Location:** §5.1 "Renew"; §13 spend line; `ci-owns-the-test-suite.md` ("push once").
- **Target quote:** "The wrapper renews on every wrapper call that writes, and only then".
- **Defect:**
  - Between one branch push per batch and notes only at phase transitions, the renewing calls during implementation are
    the spend lines "at each checkpoint", and the design does not define a checkpoint.
  - Each renewal is triggered by a content-creating REST write from the shared budget (§15.2).
  - L is set from the step durations it bounds, so a long step lengthens the expiry of every crashed holder.
- **Proposed edit:**
  - renew on every wrapper call and from the commit hook, as a ref-only `git push --force-with-lease`, which costs no
    REST write;
  - define the checkpoint as at least every commit;
  - cap L, and refuse a step that would exceed it.

### M11 (C): branch-push fencing covers only the wrapper's atomic push

- **Location:** §5.1 "Branch pushes are fenced atomically"; §19 item 2.
- **Target quote:** "The worker pushes the issue branch and a renewal commit of its claim ref together, in ONE
  `git push --atomic`".
- **Defect:** nothing refuses a plain `git push` of the issue branch, the shape the framework's `git-push` skill uses
  today. An expired holder's plain push lands whenever it is a fast-forward.
- **Proposed edit:**
  - the `pre-push` hook refuses a push of an issue branch unless it is the atomic push carrying the claim renewal with
    the lease;
  - §19 item 2 names the hook.

### M12 (C): the continuation leaves the old issue pullable, and a failed push orphans the new one

- **Location:** §5.4 "Continuation issue"; §3.1 START row.
- **Target quote:** "moves the old ref to `free` with the line `continued in #<m>`".
- **Defect:**
  1. The old issue stays open in its stage with a free claim, so §14's worker queue pulls it again: two issues for one
     ask.
  2. If the atomic push fails after the create, the new issue has no stage label and no audit line, which §3.1 defines
     as START. Triage then takes it for a new issue.
- **Proposed edit:**
  - the same verb closes the old issue administratively ("continued in #m"), or sets a `continued` flag excluded from
    every queue;
  - it writes the new issue's stage label and a `factory: continued from #<n>` line before the push;
  - the reconciler finishes or undoes a half-done continuation from those lines.

### M13 (C): queue-table gaps: lanes without "no claim", `env-incident` wording, no re-fold queue for `tamper`

- **Location:** §14 queue table and the sentence after it; §12.5; §3.2 `tamper`; §8.2.
- **Target quote:** "`env-incident` issues are in no queue".
- **Defect:**
  1. The lane rows do not require "no claim". `review-verify` is set while the maker still holds its `make` claim, so
     the dispatcher starts a lane whose `verify` acquire is refused, on every poll.
  2. §14 says `env-incident` issues are "in no queue", but §12.5 gives them `needs-input` for their owner, and a direct
     `/answer` on one needs the recorder. §12.5 says "no worker queue".
  3. "A checker re-folds the issue" for `tamper`, but no row starts that checker, and no form clears the flag (see M4).
- **Proposed edit:**
  - add "no claim" to the lane and verifier rows;
  - §14 says "in no worker queue";
  - add a row "`tamper`, no claim: the re-fold checker";
  - clear the flag by an explicit form.

### M14 (C): the steward's token cannot read the Actions setting it checks every tick

- **Location:** §3.5 "Forge setup required in factory mode"; §10.8 H11.
- **Target quote:** "checked by the steward on every tick. A failed check opens an `env-incident`".
- **Defect:**
  - GitHub Docs, "REST API endpoints for GitHub Actions permissions": `GET /repos/{owner}/{repo}/actions/permissions/workflow`
    requires the "Administration" repository permission (read).
  - The `GITHUB_TOKEN` `permissions` key offers no administration scope.
  - Implemented as written, the check fails on every tick and keeps an `env-incident` open permanently.
- **Proposed edit:**
  - the setup and update prompts check the setting with the operator's token;
  - the steward keeps only the detection at revert time, which §10.4 step 3 already turns into an immediate
    `env-incident`;
  - §3.5 lists what the steward checks per tick separately from what setup checks.

### M15 (D): wording

- §4.5 Watcher row: the identity column says `contents: read`, but the row writes verification facts, `env-incident`
  issues and `blocked-by`. That needs issues write, which the template's verdict job declares. The `blocked-by` write is
  also made without a claim, while §3.4 item 2 says one writer per issue.
- §8.5 "REWORK-REQUIRED exits | the verifier on the new head": that is true only of the → TEST-READY exit.
