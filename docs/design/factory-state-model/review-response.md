# Responses to the reviews (revision 6, 2026-11-19)

Five rounds so far:

- **Round 5** (the reviews of revision 5): answered by revision 6, in Part 0.
- **Round 4** (the reviews of revision 4): answered by revision 5, in Part 1, kept as written.
- **Round 3** (the reviews of revision 3): answered by revision 4, in Part 2, kept as written.
- **Round 2** (the re-reviews of revision 2): answered by revision 3, in Part 3, kept as written.
- **Round 1** (the reviews of revision 1): answered by revision 2, in Part 4, kept as written.

A decision id (R, M, U, O) refers to [decisions.md](decisions.md); a section (§) to [design.md](design.md).

# Part 0: the round-5 reviews of revision 5, answered by revision 6

Both reviews read revision 5 (1fce726) on 2026-11-19, in the same independent sessions:

- [adversarial-review-r5-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-r5-2026-11-19.md):
  all 16 round-4 items verified; 11 new findings (1 A, 3 B, 5 C, 2 D), ids aQ1–aQ11;
- [target-review-r5-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/target-review-r5-2026-11-19.md):
  all 5 round-4 items verified; 4 new findings (2 C, 2 D), ids tQ1–tQ4.

**Outcome.** All 15 findings are accepted, none rejected; each follows the reviewer's recommended edit. The one A
(aQ1) is a defect of today's deploy template and steward that revision 5's choice to keep "Actions: write" on worker
tokens made reachable: the fix is that the deploy deploys only trunk's tip (H15). aQ2's second option, refusing a
production environment on the detected tier, is the operator's call and is recorded as O16; the first option, stating
the residual in every place, is applied.

| Id | Grade | Finding (short) | Revision 6 |
|---|---|---|---|
| aQ1 | A | A worker token deploys any commit reachable from trunk with the production role | option 1: no `sha` input; the deploy job deploys only trunk's tip, read at job start, and concludes `skipped or refused` otherwise, which also covers re-runs; the restore needs no input (§10.4 step 4, H15, §15.1 rule 5, R92) |
| aQ2 | B | On the detected tier a worker's trunk push runs its code with the production role | option 1: the tier stated in §12.3 item 3, §15.1 rule 5, §15.2 (bullet, items 3 and 5) and §19 item 4; option 2 recorded as O16 for the operator (R93) |
| aQ3 | B | A deploy-key push starts workflows: every landing deploys twice | option 1: the landing's deploy is the trunk push run, pinned by `head_sha`; the steward dispatches only re-verify deploys; setup checks CI push triggers exclude `steward/train-*` (§3.5, §4.2, §10.4 step 3, §18, R94) |
| aQ4 | B | The fold does not bind a cited form to its issue or value | as proposed: three more conditions (§8.3, R95) |
| aQ5 | C | "Exactly one credential" rests on two unchecked invariants | as proposed: the only write deploy key, checked by setup and update; the steward refuses and checks other workflows that name its environment, and the production one too (§3.5, §19 item 1, R96) |
| aQ6 | C | The activity record may show the operator for both kinds of push | as proposed: O14 asks the exact question; §3.5 and §15.2 item 5 state what detection catches on the detected tier either way (R97) |
| aQ7 | C | "Actions: write" cancels, re-runs and deletes the pinned run | as proposed: the first attempt; a cancelled or deleted pinned run is `skipped or refused` and the tip is redeployed; §12.6 names the permission (§4.2, H13, §12.6, R98) |
| aQ8 | C | A refusal no PR caused drops every queued PR | as proposed: refusals classified; only a content refusal drops a PR (H14, R99) |
| aQ9 | C | Tool renewal is a heartbeat | as proposed: only while the parent process lives, capped at 2 × L (§5.1, R100) |
| aQ10 | D | Wording left from earlier revisions | §2 row, §5.3, §7.2 restated (R101) |
| aQ11 | D | The guidance issue's own handling | locked to collaborators; corrected by a new block, never edited (§12.9, R101) |
| tQ1 | C | The dispatcher must re-read AWS records, but holds only forge credentials | as proposed: a read-only AWS role for alarm states and Security Agent findings; confirmed once, at labelling (§3.2, §4.5, §14, §15.2, §18, R102) |
| tQ2 | C | The bank caveat's row omits that agents may change the automation that guards them | as proposed: A19's rest; the privileged automation in §12.10's recommended sensitive paths (R103) |
| tQ3 | D | §7.2 CLOSE-READY row still states the tag-only bound | as proposed (§7.2, R101) |
| tQ4 | D | A14 says worker tokens lack the permissions behind irreversible operations | as proposed (traceability A14, R101) |

# Part 1: the round-4 reviews of revision 4, answered by revision 5

Both reviews read revision 4 (049a047) on 2026-11-19, in the same independent sessions:

- [adversarial-review-r4-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-r4-2026-11-19.md):
  15 of 16 round-3 items verified, aM5 partly; 15 new findings (6 B, 8 C, 1 D), ids aP1–aP15; 16 open;
- [target-review-r4-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/target-review-r4-2026-11-19.md):
  all 4 round-3 items verified; 5 new findings (1 B, 3 C, 1 D), ids tP1–tP5; 5 open.

**Outcome.** All 21 open items are accepted, none rejected. Several mechanisms of revision 4 rested on forge features
that some plans lack, and each patch had opened a neighbouring path. Revision 5 therefore simplifies where the reviews
offered or implied a simpler option, and states the residual instead of adding another layer:

- **R57 is replaced by protection tiers** (aP4, aP5, aP6, aP12, tP1; R75). Worker tokens keep "Workflows" and
  "Actions: write", so the steward's wake-ups work as today and a workflow-file change lands through the queue, with
  no human-only step. On the protected tier the trunk ruleset's one bypass is the steward's deploy key, held by an
  environment limited to the default branch. On the detected tier (GitHub Free private repositories, GitLab before
  19.2) only the per-tick detection guards trunk, and §15.2 says so.
- **`/get-guidance` posts nothing** (aM5, tP2; R78): it prints one block of form lines, which the human posts on the
  project's guidance issue. The mark, its hook and the Kiro difference are gone.

A fact corrected on the way: GitHub Pro private repositories do have rulesets and environments (GitHub Docs, "About
rulesets", "Managing environments for deployment"), so only GitHub Free is in the detected tier.

| Id | Grade | Finding (short) | Revision 5 |
|---|---|---|---|
| aM5 (rest) | B | The `/get-guidance` mark is session-scoped; §15.2 says "or otherwise" | option 2: `/get-guidance` prints the lines on every client, and the human posts them on the guidance issue; only unmarked forms count; "or otherwise" removed (§8.3, §12.3, §12.7, §12.9, §15.2, §16, R78) |
| aP1 | B | No reland fact; a revert of a revert reads as a revert; no CLOSE-READY return | option 1: a PR's state is the last of `Steward-PR`, `Steward-Reverts`, `Steward-Relands`; landed, relanded or replaced; CLOSE-READY → REWORK-REQUIRED and closed → REWORK-REQUIRED; CLOSE-READY → closed re-checks (§4.2, §4.5, §10.4, §10.5, H1, R79) |
| aP2 | B | A verdict carries no proof it came from the separately started checker | option 2: the lane calls its exit itself under its `verify` claim; §4.5 lists the exits (§4.2, §4.5, §8.5, R81) |
| aP3 | B | The folded state is maker-written and trusted by every reader | option 1: orientation only; predicates, separately started checkers and the steward re-fold from the first record (§5.1, §8.2, §8.5, §8.6, R82) |
| aP4 | B | R57 cuts both steward wake-ups | R57 replaced: worker tokens keep "Actions: write", so both wake-ups stay (§3.5, R75) |
| aP5 | B | A workflow-file change has no landing path; a queued one fails every tick | the steward pushes trains and trunk with its deploy key, the ruleset's one bypass; a refused train push drops that PR with `queue-failed` (§3.5, H14, R75, R77) |
| aP6 | B | On GitLab the worker tokens can read the steward's token | option 1: the variable masked and hidden; fine-grained worker tokens from 19.2 (protected tier); before 19.2 the detected tier, not closed (§3.5, §15.2, R75) |
| aP7 | C | The content key matches legitimate later changes | declared and confirmed: `Reverts: PR #<k>` or GitHub's revert body, confirmed by content; otherwise a candidate that reopens nothing (§10.4 step 3, R80) |
| aP8 | C | The re-spec edge and `/stage` leave flags and PRs behind | as proposed (§4.2, §4.3, §8.3, R83) |
| aP9 | C | `/amend` text is not part of the ask | as proposed (§4.3, R84) |
| aP10 | C | A skipped or refused deploy must not count as red | as proposed: four outcomes (§10.3, §10.4 step 5, R85) |
| aP11 | C | Gaps in the label gate | as proposed: every form of label write; a source record for `priority:critical` (§3.2, §6.1, §8.2, §15.2, R86) |
| aP12 | C | What a write-token workflow runs is worker-changeable | changes to privileged automation are risk-tagged `iam-iac`; on the protected tier no `GITHUB_TOKEN` workflow can push trunk, so other default-branch workflows are no exemption; the landed-privilege residual is §19 item 14 (§3.5, §4.5, R75, R76) |
| aP13 | C | Renewal from the commit hook and long local runs | as proposed (§5.1, R87) |
| aP14 | C | The continuation writes the stage before the claim exists | as proposed (§5.4, R88) |
| aP15 | D | `return_run_details` depends on the API version | as proposed (§4.2, §10.4, R85) |
| tP1 | B | Every workflow-file change needs the operator's token: a human-only step | the alternative, simplified: workflow-file changes land through the queue with the steward's deploy key; P6 and C1 hold again (§3.5, traceability C1, R75) |
| tP2 | C | Kiro has a prompt-submit hook | moot: `/get-guidance` posts nothing on any client, so neither client needs the hook (§12.9, §16, traceability 3.4, R78) |
| tP3 | C | S3 object deletion cannot be tag-conditioned | as proposed: the bound per action, name-prefix scope where tags cannot condition (§11, §15.1 rule 5, §18, R89) |
| tP4 | C | The label gate refuses the `priority:critical` C10 promises | a source record instead of a provenance line: the finding id, re-read by the dispatcher (§3.2, §7.2, traceability C10, R86) |
| tP5 | D | Three stale sentences | as proposed (§12.6, §14, decisions B16, R91) |

Revision 5 also states, as a consequence of R75, where the production deploy's credential lives: the deploy role
trusts only trunk's OIDC subject, or on the protected tier a production environment limited to trunk (§12.3 item 3,
§15.1 rule 5, R90).

# Part 2: the round-3 reviews of revision 3, answered by revision 4

Both reviews read revision 3 (5dcc08f) on 2026-11-19, in the same independent sessions:

- [adversarial-review-r3-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-r3-2026-11-19.md):
  43 of 44 round-2 items verified, aN7 partly; 15 new findings (7 B, 7 C, 1 D), ids aM1–aM15; 16 open;
- [target-review-r3-2026-11-19.md](../../reports/factory-state-model-2026-11/reviews/target-review-r3-2026-11-19.md):
  all 20 round-2 items verified; 4 new findings (1 B, 1 C, 2 D), ids tM1–tM4; 4 open.

**Outcome.** All 20 open items are accepted, none rejected. Each follows the reviewer's recommended edit, with one
variation: for aM5, both options are combined (see below).

| Id | Grade | Finding (short) | Revision 4 |
|---|---|---|---|
| aN7 (rest) | B | Trunk reachable through a workflow a worker writes | worker tokens lack Workflows and Actions-write; write-token workflows on the default branch only; branch code `contents: read`; GitLab protected variable; activity check "pushed by GitHub Actions" (§3.5, §10.8 H7, §15.2, R57) |
| aM1 | B | Nothing starts the separately started checkers; §4.1 names exits §8.5 does not cover | `checker-requested:<lane>` and its queue row; §8.5 table covers the START exits and records the trade-offs; §4.1 and P4 say "where §8.5 names one" (R58) |
| aM2 | B | A revert the steward did not open is never a revert fact | `Steward-Reverts` for every exact revert, keyed on content; the reverted PR's issue returns or is reopened; partial reverts in §19 item 13 (R59) |
| aM3 | B | The pinned run's conclusion and commit are not the deploy verdict | the dispatched run id and sha, or a push run's `head_sha`; deploy and smoke job conclusions from the jobs API; restored and skipped deploys conclude `failure` (§4.2, §10.3, §10.4, R60) |
| aM4 | B | Human-owned flags are plain label writes | forms `/admit`, `/hold`, `/unhold`, `/priority`, `/clear-tamper`; the wrapper refuses agents' label writes of them; the dispatcher reverts unbacked ones (§3.2, §4.4, §8.2, R61) |
| aM5 | B | An agent can post a counted answer through the `/get-guidance` mark | both options combined: the mark is accepted only in a session the human started `/get-guidance` in (a `UserPromptSubmit` hook); Kiro prints the form lines instead; the fold re-checks every cited form; several forms per comment allowed (§8.3, §12.9, R62) |
| aM6 | B | `/amend`, `/stage` and an edit above the marker have no executor or edge | the recorder executes every form; the re-spec edge; `/stage` on TEST-READY as a steward request; `/amend` refused from TEST-READY on (§4.2, §4.3, §8.3, §12.7, R63) |
| aM7 | B | An admitted outsider can rewrite the issue | `admitted {ask_hash}`; a mismatch drops the issue to read-only triage (§4.3, §6.3, R64) |
| aM8 | C | A backed-off steward can lose a TEST-READY return | every tick re-derives both exits from durable facts (§4.2, §14, R65) |
| aM9 | C | The cursor alone cannot resume a fold | the folded state in the claim commits; `since` the last fold (§5.1, §8.2, R66) |
| aM10 | C | Renewal cadence undefined | every wrapper call and the commit hook, ref-only; checkpoint = every commit; L capped (§5.1, R67) |
| aM11 | C | A plain push is unfenced | the `pre-push` fence (§5.1, §19 item 2, R68) |
| aM12 | C | The continuation leaves the old issue pullable or orphans the new one | stage and `continued from` first, then the push, then the old issue closed; reconciler recovery (§5.4, R69) |
| aM13 | C | Queue gaps: no "no claim", `env-incident` wording, no `tamper` re-fold queue | every row requires "no claim"; the re-fold checker row; `/clear-tamper`; "no worker queue" (§14, R70) |
| aM14 | C | The steward's token cannot read the Actions setting | checked by setup and update with the operator's token; the steward detects the refusal at revert time (§3.5, H11, R71) |
| aM15 | D | Watcher row wording; REWORK row wording | watcher `issues: write`, no flag writes; the steward applies `blocked-by`; §8.5 row restated (§4.5, §8.5, R72) |
| tM1 | B | Trust rule 5 is absolute, but sessions break it | rule 5 restated as a bound; tag-conditioned create and delete for every team; §11 wording (§11, §15.1, §18, R73) |
| tM2 | C | A28 overstates | A28 partly aligned, rest named; §19 item 12 |
| tM3 | D | The "requirement" rework class has no confirmer | the spec checkers confirm it when re-approving (§4.2, R74) |
| tM4 | D | The role count does not match | 16 roles listed, 80 % (§16); traceability 3.4 |

# Part 3: the re-reviews of revision 2, answered by revision 3

Both re-reviews read revision 2 (cec3492) on 2026-11-16, in the same independent sessions as round 1:

- [adversarial-review-r2-2026-11-16.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-r2-2026-11-16.md):
  36 of 53 verified, 17 partly; 16 new findings (9 B, 6 C, 1 D), ids aN1–aN16;
- [target-review-r2-2026-11-16.md](../../reports/factory-state-model-2026-11/reviews/target-review-r2-2026-11-16.md):
  19 of 23 verified, 4 partly; 14 new findings (1 B, 10 C, 3 D), ids tN1–tN14; 2 status rows partly.

**Outcome.** Every open item is accepted, none rejected:

- the 30 new findings;
- the 21 partly-fixed findings;
- the reviewers' remarks on verified ones.

Nearly all follow the reviewers' recommended edits. Three choose among their options:

- **aN1:** option 1. Every caller holds the claim; the steward is the only caller of TEST-READY's exits.
- **aN4:** option 1. A permanent claim ref with `held` and `free` commits.
- **aN5:** option 1. Mark every agent write, accept explicit forms only, and restate the residual. Under U24 the
  residual stays; §15.2 states its true size.

## Revision-1 findings judged "partly" in the re-review

| Id | What was left | Revision 3 |
|---|---|---|
| A1 | TEST-READY exits for other rejects and closed PRs; rows for conductor, arbiter, question checker; incomplete steward row; the `split` close; the reconciler's forward roll | §4.2 TEST-READY → REWORK-REQUIRED (every reject, closed PR); §4.5 new and completed rows; `split` close by the dispatcher; the reconciler completes or undoes only (R34, R35, R39) |
| A4 | Unmarked agent notes pass as the authorised human | §8.2 every agent write marked, unmarked ones refused; §8.3 explicit forms only (R37) |
| B1 | Lease binds cooperating clients only; branch push check-then-act; no renewal mechanism; expiry vs acquire; stale REST writes | §5.1 permanent ref, atomic branch + claim push, renewal on writing calls only; residuals named in §19 items 2 and 3 (R36) |
| B2 | The reconciler cannot tell a crashed verb from a live one for callers without a claim | every caller holds the claim; the reconciler touches only free-claim issues with intents older than L (§4.4, R34) |
| B4 | Recorder re-fires; interpretation unchecked | explicit forms only; started only on a form newer than its last run; free text verbatim (§12.7, R37, R39) |
| B5 | An agent's body edit changes the ask | the ask is above the machine-owned marker; agents write below it (§4.3, R38) |
| B6 | The conductor posts every lane's records | §8.5 the in-session boundary; a separately started checker per stage exit (R42) |
| B7 | `Reverts-PR` on a PR-authored commit; trunk unprotected | `Steward-Reverts` on the steward's own merge; trunk ruleset; activity check (§10.8 H1, H7, H12, R40) |
| B9 | Worker contents write reaches trunk; dispatcher scope not listed | trunk ruleset (§3.5); dispatcher scope in §4.5, §14, §15.2 |
| B10 | New comment sources missing from the estimate | §15.2 lists them; `writes=` in the spend lines measures them; no estimate is claimed (R49) |
| B14 | The revert PR cannot be created on a default repository; label keying | setup and per-tick check of the setting; refusal = `env-incident`; keyed on identity + exact revert content (§10.4, R41) |
| B17 | Detector not in the Minimum tier; migrations invisible to a change set | detector and migration ledger in the Minimum tier; digest in object metadata (§10.3, §10.6, R45) |
| C4 | Release deletes the cursor | the cursor lives in `held` and `free` commits and survives every release (§5.1, R36) |
| C9 | No writer for the `split` close; the parent re-triaged | the dispatcher closes it; `split` excluded from every worker queue (§3.2, §4.2, §14) |
| C16 | An agent's label write becomes an override | hand-set labels are reverted; `/stage` (§4.4, R37) |
| C17 | Renewal between wrapper calls | renewal only on writing calls; L from measured step times; no heartbeat (§5.1, R36) |
| C21 | Rejecting edited records fails open; audit lines editable | `tamper` hold (§8.2, R46); §13 says counters come from editable comments; deletion is §19 item 6 |
| T-09 | The expedite works only after triage | pre-triage pull of production issues filed by a factory login (§6.1, §14, R53) |
| T-13 | The log scan sits in the worker that deletes AWS resources | read-only log-scan lane; tag-conditioned deletes (§11, R48) |
| T-15 | No caller of TEST-READY → CLOSE-READY under `verification: none` | the steward calls it in every mode (§3.5, §4.5) |
| T-16 | "Checking ≠ proving" has no row | traceability A27 |

The reviewers' remarks on verified findings, applied:

- A2: `actor.agent` is self-declared; bounded by §8.5.
- B3: the lane queues gained exclusions (§14).
- B13: `env-incident` issues have no stage and are in no queue (§12.5).
- B15: per-PR reverts from first-parent trailers.
- C2: a `ci-pending` timeout, and the tier-S table counts the hand-off (§4.2, §7.3).
- C18: the deploy guard escalates at once (§10.4).
- C20: group claims are atomic (§5.3).
- C22: the overrule is computed (§8.7).

## New findings of the adversarial re-review

| Id | Grade | Finding (short) | Revision 3 |
|---|---|---|---|
| aN1 | B | Only workers are fenced | every caller holds the claim; the steward alone calls TEST-READY's exits (§4.4, §4.5, §5.3, R34) |
| aN2 | B | Writers without a row; the reconciler contradicts §4.4 | §4.5 rows completed (R35) |
| aN3 | B | Flag and queue combinations strand issues or churn | reject and closed-PR returns; `ci-pending` timeout; `env-incident` outside queues; recorder condition; lane exclusions; `split` close (§4.2, §12.5, §12.7, §14, R39) |
| aN4 | B | The claim ref's lifecycle contradicts itself | permanent ref with `held`/`free` commits; atomic push; renewal on writing calls (§5, R36) |
| aN5 | B | The U24 residual is reachable without a compromised agent | marking of every agent write; explicit forms; label reversion; §12.3 item 3 and §15.2 state the forge-gate limits and the true residual (R37) |
| aN7 | B | `Reverts-PR` from PR commits; GitHub trunk unprotected | `Steward-Reverts`; trunk ruleset; activity check (R40) |
| aN8 | B | Actions may not create PRs by default; deploy guard freezes | setting in setup, checked per tick; refusal = `env-incident`; content-keyed exemption (R41) |
| aN9 | B | The maker's session posts the checkers' records | §8.5 boundary; separately started checker per stage exit (R42) |
| aN10 | B | Deploy fact not pinned; shared bot identity | pinned run from the run API; records count only when they name it (R43) |
| aN6 | C | Body edits under the shared login change the ask | the machine-owned marker (R38) |
| aN11 | C | `hold` does not stop landing | `eligibility` waits on an issue `hold` (R44) |
| aN12 | C | Tier-S table contradicts `ci-pending` | §7.3 hand-offs row: one, to the verifier |
| aN13 | C | The recorder interprets prose | explicit forms; free text verbatim for the next question checker (§12.7) |
| aN14 | C | The restore guard rests on detectors that are not required | Minimum tier gains the detector and the migration ledger; digest in object metadata (R45) |
| aN15 | C | Rejecting edited records fails open; audit lines editable | `tamper` (R46); §13 restated |
| aN16 | D | The diagram omits `env-incident` | §3.3 names it as not a stage |

The re-review's section 3, "checked and not settled here", is applied:

- **O14 extended:** atomic pushes, custom-ref workflow triggers, and the ruleset actor.
- **The U21 consistency points:** the label override and the recorder's interpretation are both removed.
- **The write budget:** it is measured rather than estimated.

## New findings of the alignment re-review

| Id | Grade | Finding (short) | Revision 3 |
|---|---|---|---|
| tN1 | B | The close-out reads untrusted logs while holding delete credentials | read-only log-scan lane; tag-conditioned deletes; trust rule 5 extended (§11, §15.1, R48) |
| tN2 | C | Claims by git ref differ from the keynote's comment tip without a reason | traceability A8 and C12 |
| tN3 | C | The spend line has no model, and lanes may not write it | `model=`; every agent-running role writes spend lines (§4.5, §13, R49) |
| tN4 | C | "All budgets report-only" suspends the review caps | only cost, bounce and claim counters are report-only (§13, R50); A13 names it |
| tN5 | C | A4 and A14 still lean on the open dispatcher host | traceability A4, A14 |
| tN6 | C | "Nobody looked" has no row | traceability A9 rest; §19 item 12 |
| tN7 | C | No docs-drift check | docs-drift checker in IMPLEMENTATION (§7.2, R54); traceability A28 |
| tN8 | C | The pen test as a non-gate has no reason | traceability C10 extended (R55) |
| tN9 | C | Approvals not provable under U24 | §12.10 limit; rows 15, 3.5, A19 name it (R56) |
| tN10 | C | The "environment" rework class has no checker and no exit | confirmed by the infra classifier; stays `blocked-by` the incident (§4.2, R51) |
| tN11 | C | A2 reversed unconditionally | conditional on the dispatcher's host (§14, §16, §18, traceability B.4, R52) |
| tN12 | D | A23 understates | "aligned on reach; differs on the means" |
| tN13 | D | Slides 29/30 and messaging untraced | traceability A21, A25 |
| tN14 | D | The claim needs no Jira equivalent | §3.6 restated |

The two status rows judged partly (A10, row 8, both through T-09) follow the pre-triage expedite.

# Part 4: the reviews of revision 1, answered by revision 2

Both reviews read revision 1 (11073fe) on 2026-11-11, each in a session independent of the designer's:

- [adversarial-review-2026-11-11.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-2026-11-11.md):
  53 findings (4 A, 22 B, 23 C, 4 D);
- [target-review-2026-11-11.md](../../reports/factory-state-model-2026-11/reviews/target-review-2026-11-11.md): 23
  findings (8 B, 12 C, 3 D) and a corrected status table.

Every finding is answered below with its disposition and the place in revision 2 that carries the change. A decision
id (R, M, U, O) refers to [decisions.md](decisions.md).

**Outcome.** All 76 findings are accepted:

- 70 as proposed or with a small variation;
- 4 with a different mechanism that meets the same need: B1, B7, C2 and C22;
- 1 superseded by another fix: T-10;
- 1 outside the design set: C23.

None is rejected. A4's root cause, which identity the agents post as, went to the operator. They decided to keep their
own account (U24), so the residual is accepted and recorded in design §15.2.

**Three operator decisions taken while answering** change how some findings are read:

- **U21, equal scrutiny.** The operator's input gets neither more nor less scrutiny than an agent's. Revision 2 keeps
  authorship checks only where a decision is reserved to a human, and explains why in design §12.3.
- **U22, the keynote is a vision, not a specification.** Target-review findings phrased as "not met" were applied as
  corrections of accuracy and alignment, and traceability.md now records alignment rather than compliance.
- **U23, reviews are permanent records.** Both reports are committed beside the design.

## Adversarial review

| Id | Grade | Finding (short) | Disposition | Revision 2 |
|---|---|---|---|---|
| A1 | A | No actor may change the stage of an issue in TEST-READY | accepted (option 1) | §4.5 authority table; §3.1; §3.4 items 3–4; caller role per edge in §4.2; §18 Authority and Delivery rows (R1) |
| A2 | A | Maker ≠ checker keyed on the session, so in-session verification never counts | accepted (option 1) | §8.1 `actor.agent` + role; §4.1; §8.4 (R4) |
| A3 | A | Per-stage claims vs one claim carrying an issue across stages | accepted | §5.1: one claim per issue, the stage informational; §3.4 item 1 (R2) |
| A4 | A | Any commenter's unmarked comment counts as an answer, approval or ask change | accepted, reframed by U21 | §8.3; §12.3; §4.5 authorised-human role; lock option in §6.3. Residual under the shared account accepted: U24 (R5) |
| B1 | B | The claim protocol has a visibility race, no fencing, an unspecified lease | accepted, different mechanism | §5.1–§5.2: the claim ref is acquired and renewed with `git push --force-with-lease`. That is a server-side compare-and-swap over the git protocol, which also spends no REST write budget, rather than `git/create-ref`. The fencing token is the ref SHA; the lease is judged by the reaper's own clock. Verification on `sff-test-*`: O14 (R2) |
| B2 | B | The verb is check-then-act, and crash recovery rolls back transitions that took effect | accepted | §4.4: guard named as such; intent first, done last; the reconciler rolls forward; the START rule (R3) |
| B3 | B | No dispatcher queue for checker lanes | accepted | §14 queue table; §5.3 verify claims (R24) |
| B4 | B | A direct answer is never read, because `needs-input` issues are not pullable | accepted | §12.7 answer recorder; §14 recorder queue (R24) |
| B5 | B | The ask-change trigger fires on answers and on the steward's own comments | accepted | §4.3: ask hash only, `/amend`, SPEC and IMPLEMENTATION only; §8.2 machine-comment definition (R7) |
| B6 | B | The gate counts verdicts whose authorship cannot be proven; the maker side can satisfy it | accepted | §8.5 downgrades; §8.6 the steward re-runs the fold; the status is a projection; the authorship residual is accepted under U24 (R23) |
| B7 | B | `merge-steward:` lines accepted from any author, so a landing can be forged | accepted, different mechanism | §10.8 H7: landings come from trunk's first-parent trailers (`Steward-PR`), with comments as projections. Author filtering is only a second layer, because a workflow on a worker's own PR branch can also post as `github-actions[bot]` (R8) |
| B8 | B | Admission keyed on provenance lines anyone can type | accepted | §6.3 admission by author (R6) |
| B9 | B | One write-scoped token everywhere, no per-worker revocation | accepted (option 1 as baseline) | §15.2 per-host fine-grained tokens without irreversible-operation permissions; option 2 (a GitHub App) was declined in U24 (R33) |
| B10 | B | The shared account's content-creation limit caps the factory | accepted | §8.2 one envelope per round; claims over git (§5); PR projections off; host-wide token bucket (§15.2). With the shared account kept (U24) these reductions are binding (R22) |
| B11 | B | The red verdict blames every landing since the last green deploy | accepted | §10.5; §10.8 H8; §2; §18 Delivery (R9) |
| B12 | B | The watcher closes verified issues itself, so CLOSE-READY never runs | accepted | §10.8 H9; §2; §11; §18 (R10) |
| B13 | B | `delivery-status` is closed and body-only, so it cannot carry escalations or be a `blocked-by` target | accepted | §12.5 `env-incident` issues per root cause; §10.4 step 6; §3.2 (R14) |
| B14 | B | Steward-opened revert PRs never get PR CI on GitHub; the revert is not train 1 | accepted | §10.4 step 3; §10.8 H10 (R11) |
| B15 | B | The H1 fix supersedes a batch-tip landing not tied to a PR | accepted | §10.8 H1: per PR, from trunk trailers; §4.2 TEST-READY → CLOSE-READY (R8) |
| B16 | B | Attribution step A3 names the wrong culprit when several landings change the failing resource | accepted | §10.4 step 2.2 (exactly one step, dependency closure); signature; refunds in §13 (R12) |
| B17 | B | The auto-restore has no guard for stateful changes and trusts an unprotected cache | accepted | §10.3 step 4 restore guard and digest check; step 5; §10.6 cache (R13, M1) |
| B18 | B | Triage sets the tier and risk tags alone | accepted | §6.4 deterministic floor, raise-only (R19) |
| B19 | B | The acceptance-test freeze can be bypassed without touching the test files | accepted | §4.2: S's tests, fixtures and configuration run over H's code; §9 (R17) |
| B20 | B | CLOSE-READY removes only resources the agents chose to record | accepted | §11 `factory-issue` tag + ledger; §4.2 (R25) |
| B21 | B | The predicates assume the steward and the watcher; other modes are not mapped | accepted | §3.5 delivery modes (R26) |
| B22 | B | Draft PRs do not exist for private repositories on GitHub Free and Pro | accepted | §9; §4.2: readiness is the `do-not-merge` label (R18) |
| C1 | C | `--allow-pending` admits any "wait" verdict | accepted | §4.2: only when pending CI is the sole unmet clause (R16) |
| C2 | C | The verifier cannot report while CI is pending | accepted, different mechanism | §4.2, §14: the worker sets `ci-pending` and releases; the verifier lane completes the transition when CI has ended. Workers still never wait (P2), and "done when CI is green" holds (R16) |
| C3 | C | The train branches are deleted at landing | accepted | §10.4 step 2.2: first-parent merges, synthesized on CI; §2 |
| C4 | C | No `--after-id` on GitHub; a machine-local cursor; the 2,500-comment cap | accepted | §8.2 paging with an id filter, the cursor in the claim ref, a continuation issue at 2,000 (R22) |
| C5 | C | GitLab notes are folded by `created_at` | accepted | §8.2 fold by id on both forges; §2 |
| C6 | C | Budgets calibrated on warm-cache sessions undercount the new flow | accepted | §13 report-only for the first 20 issues per tier (R21) |
| C7 | C | The every-issue checker list conflicts with tier S's one combined pass | accepted | §7.3: tier S keeps one combined pass; the minimum path table (R31) |
| C8 | C | The rolling learning-batch issue keeps the backlog non-empty | accepted | §11 item 3: rotation per PR, exempt from the empty backlog and from its own learning capture; traceability A5 (M5) |
| C9 | C | The split parent has no writer or close rule | accepted | §3.2 `split`; §4.2 |
| C10 | C | `blocked-by`: cycles, closed targets, GitLab tier | accepted | §3.2 |
| C11 | C | Nobody removes the lease and `claimed` on steward and watcher returns | accepted | §5.1 ONE release verb, called by the steward and the watcher too (R2) |
| C12 | C | A false negative of the question checker | accepted | §12.4 always-ask list (R29) |
| C13 | C | A read-only triage paraphrase can hide an injected ask | accepted | §6.3 verbatim body in the admission view (R6) |
| C14 | C | `spec-approved` is an effect, not a precondition | accepted | §4.2 side effect written by the verb |
| C15 | C | Log text can steer attribution | accepted | §7.2; §10.4 step 2.4: the attributor ranks only inside the suspect set; logs are data (R12) |
| C16 | C | A hand-set single stage label is taken as truth | accepted | §4.4 reconciler compares with the last done line (R3) |
| C17 | C | On Kiro, renewal "at every checkpoint" is the model's action | accepted | §5.1 renewal in the wrapper; §16 (R2) |
| C18 | C | Every deploy before the revert lands re-breaks the environment | accepted | §10.4 step 4 deploy guard (R11) |
| C19 | C | The 2.5 h replay has unstated assumptions | accepted | §10.7 assumptions listed |
| C20 | C | Group claims can livelock | accepted | §5.3 ascending order, random back-off (R2) |
| C21 | C | Counters live in comments the shared account can edit or delete | accepted | §8.2 the fold rejects edited records; §5.1 no comment deletion; §13 counters from audit lines; deletion stays a residual (§19 item 4) |
| C22 | C | The arbiter's decision has no checker | accepted, narrowed | §8.7 step 4: deterministic re-check always; only a decision that OVERRULES a security or legal finding becomes an approval, so upholding security does not add a human round (R23) |
| C23 | C | Two untracked target files in the main checkout could be published by accident | accepted; outside the design set | both paths are excluded in the main checkout's local `.git/info/exclude`; nothing committed |
| D1 | D | The delivery label list is incomplete | accepted | §2 |
| D2 | D | `delivery.md` calls the status issue open; the code keeps it closed | accepted | §2; §18 small defects |
| D3 | D | The appendix uses "LANDED" | accepted in the design; the appendix is kept as written | §10.5 uses TEST-READY; `revert-and-batching.md` is a dated record and is not rewritten |
| D4 | D | "Laundry list" is undefined | accepted | §4.2 CLOSE-READY → closed defines it |

## Target review

| Id | Grade | Finding (short) | Disposition | Revision 2 |
|---|---|---|---|---|
| T-01 | B | The return path to the spec is skippable | accepted | §4.2 a rework analysis on every exit, confirmed by the test-architect; traceability A1, row 10 partial (R15) |
| T-02 | B | Cost budgets have no measurement source | accepted | §13 spend lines; §17; traceability A13, rows 12, 16, 3.1 (R21) |
| T-03 | B | "Who starts the loops" marked designed while the host is open | accepted | traceability A2, A9, rows 3, 5, 14, 3.3 partial; O12 extended with worker start and governance; §14 |
| T-04 | B | Security beyond the diff overstated; no pen test | accepted | §7.2 optional external PR review (setting) and batched pen test; traceability C10; row 9 partial (R27) |
| T-05 | B | The triage rule can refuse the keynote's own feedback-loop issues | accepted | §6.5 rule restated (R30) |
| T-06 | B | The verdict cannot carry what a lane did not verify | accepted | §8.1 required `notVerified`; §7.4; §11 summary (R20) |
| T-07 | B | Approval for sensitive paths has no PR-level predicate | accepted | §12.10; §4.2; traceability row 15 and 3.5 aligned (R28) |
| T-08 | B | "Single immutable record" marked designed, but records are editable comments | accepted | traceability row 2 partial; §19 item 4; O15 |
| T-09 | C | Incidents enter at START, which is pulled last | accepted | §6.1, §14 `priority:critical` first (R24) |
| T-10 | C | The implementer may hand over before CI is green | superseded | the C2 fix makes the transition wait for green CI and the verifier, without the worker waiting, so there is no deviation to record (R16) |
| T-11 | C | The keep-list is not traced; the stop gates must change | accepted | traceability B.4; §16; §18 Gates row (R32) |
| T-12 | C | The learning loop's remainder named inconsistently; machine-local writes | accepted | §11 item 3: no machine-local memory; traceability A7, row 7 name 2.5 (a)–(d) (M5) |
| T-13 | C | Close-out's deployment findings have no source | accepted | §11 item 2 and §7.2: the deploy-window log scan where the project provides a query; traceability A6, row 6 name the rest |
| T-14 | C | About 14 new roles need hand-kept Kiro twins | accepted | §16 renderer precondition; traceability 3.4 (R32) |
| T-15 | C | The design presupposes the steward | accepted | §3.5; traceability 3.7 (R26) |
| T-16 | C | No traced minimum path for a one-line fix | accepted | §7.3 tier-S table; traceability A22 (R31) |
| T-17 | C | Keynote ideas without a row; differences not recorded | accepted | traceability A23–A26, C8, C9, C11; §14 governance inheritance |
| T-18 | C | The caveat, do's-and-don'ts and AI-DLC rows claim too much | accepted | traceability A19, A20 partly aligned; C1 reason extended |
| T-19 | C | Under B2 a worker can choose its own checking depth | accepted | §6.4 (same fix as B18) (R19) |
| T-20 | D | Traceability cites elements design.md lacks | accepted | Playwright in §9; the pen test in §7.2; the stop gates in §16 |
| T-21 | C | Jira is out of scope, but storage was chosen for GitHub and GitLab only | accepted | §3.6; traceability 3.8 |
| T-22 | D | C3 and C4 give partial reasons | accepted | traceability C3, C4 |
| T-23 | D | C2 cites one slide | accepted | traceability C2 |

## What round 2 was asked to check (kept as written)

1. Whether the claim ref (§5) holds up: the custom ref namespace, the atomicity of `--force-with-lease` on both forges
   (O14), and the fencing window (§19 item 2).
2. Whether the authority table (§4.5) leaves any edge or record without a writer, or gives one to two roles.
3. Whether the queues of §14 make every flag combination pullable by someone, with no issue stranded.
4. Whether U21's equal scrutiny and §12.3's reserved decisions are consistent everywhere `needs-input`, approvals and
   admission appear.

# What the next review should check (revision 6)

1. The round-5 items in Part 0, each against revision 6's design.md.
2. Whether revision 6's changes leave a neighbouring path open:
   - the tip-only deploy (H15), the landing's push run as the pinned deploy, and re-verify dispatches;
   - the classified train-push refusals (H14);
   - the fold's binding of a form to its issue (§8.3);
   - the environment checks and the only-write-deploy-key check (§3.5);
   - the per-tier statements of the production guard (§12.3, §15.1, §15.2, §19 item 4).

# What round 5 was asked to check (revision 5, kept as written)

1. The round-4 items in Part 1, each against revision 5's design.md.
2. Whether revision 5's simplifications leave a neighbouring path open:
   - the protection tiers: the deploy key as the ruleset's one bypass and its environment, the GitLab tier, the
     per-tick detection, and whether §15.2 states the detected tier at its true size;
   - workflow-file changes through the queue, and privileged automation as `iam-iac` (§19 item 14);
   - `/get-guidance` printing, the guidance issue, and the recorder applying its lines;
   - the reland fact, declared reverts, and the CLOSE-READY and closed returns;
   - the checkers calling their own exits, and the re-fold for every decision;
   - the deploy role's OIDC trust (§15.1 rule 5) and the per-action AWS bound (§11).

# What round 4 was asked to check (revision 4, kept as written)

1. The round-3 items in Part 1, each against revision 4's design.md.
2. Whether the new paths revision 4 opened leave a neighbouring path open, as round 3 found for revision 3:
   - the `checker-requested` queue;
   - the forms the recorder now executes, and the re-spec edge;
   - the `/get-guidance` mark gate;
   - content-keyed revert facts;
   - the dispatched-run pin;
   - the label gate;
   - the no-write-token-path rule.

# What round 3 was asked to check (revision 3, kept as written)

1. **Every caller holds the claim.** Whether, for every edge and every role of §4.5, the claim kind and the fence of
   §4.4 and §5.3 hold. Pay particular attention to the steward as the only caller of TEST-READY's exits.
2. **The permanent claim ref** (§5.1–§5.4): `held` and `free` commits, the atomic branch + claim push, renewal on
   writing calls only, expiry, group claims, the continuation issue.
3. **Marking and explicit forms** (§8.2, §8.3): whether any path still lets an ordinary agent write count as a human's,
   and whether the residual in §15.2 is now stated at its true size.
4. **The queue table** (§14): whether every flag combination is pullable by exactly the right role, and nothing churns.
5. **The new facts:** `Steward-Reverts`, the pinned deploy run, the trunk ruleset with its activity check, and the
   Actions-may-create-PRs check (§3.5, §4.2, §10.4, §10.8).
6. **Traceability** after the alignment re-review's corrections: rows A4, A8–A10, A13, A14, A19, A21, A23, A25, A27,
   A28; rows 2, 8, 9, 12, 15; C10, C12.
