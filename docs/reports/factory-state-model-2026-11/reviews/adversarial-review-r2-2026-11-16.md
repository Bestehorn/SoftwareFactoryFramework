# Adversarial review of the factory state-model design, revision 2 (2026-11-16)

**Subject.** Revision 2 of the factory state-model design, branch `docs-factory-state-model-design` at commit `cec3492`:
`docs/design/factory-state-model/design.md`, `decisions.md` and `review-response.md`. `traceability.md` was not
reviewed. The review was done in a session independent of the designer's, from a detached worktree, read-only.

**Product code read to check the design's claims:**

- `src/payload/scripts/merge_steward.py`: `eligibility`, `reject`, `plan`, the train merge message and `TRAILER_RE`;
- `src/payload/scripts/github_api/commands/issues.py` (`cmd_comment_issue`, `cmd_update_issue`);
- `src/payload/scripts/github_api/commands/call.py` (`GATED_OPERATIONS`);
- `templates/ci/github-merge-steward.yml.template`, `templates/ci/github-deploy.yml.template` and
  `templates/ci/gitlab-delivery.gitlab-ci.yml.template`.

Platform facts come from the forge documentation, named where each is used, and from `docs/api-reference/`.

**Operator decisions respected:**

- **U21:** equal scrutiny. Authorship matters only for reserved decisions (§12.3).
- **U24:** the agents keep posting as the operator's account. This review does not argue for another identity. Where it
  touches U24, it tests only the claim of §15.2 that the residual is limited by P12, the forge-bound gates and the
  wrapper's marking.

---

## Summary

**Verdicts on the 53 findings of the revision-1 review:**

| Verdict | Count |
|---|---|
| verified | 36 |
| partly | 17 |
| not-fixed | 0 |
| disputed | 0 |

**New findings on revision 2's additions (N1–N16):**

| Grade | Count | Ids |
|---|---|---|
| A | 0 | — |
| B | 9 | N1, N2, N3, N4, N5, N7, N8, N9, N10 |
| C | 6 | N6, N11, N12, N13, N14, N15 |
| D | 1 | N16 |

Revision 2 is a substantial improvement. Every grade-A finding of revision 1 now has a mechanism:

- the role table;
- `actor.agent`;
- one claim per issue;
- the authorised-human rule.

What remains is that these mechanisms cover the worker path well and the other paths unevenly. Callers that are not
workers run unfenced. Several roles that write records have no row in the table. The facts the design calls
unforgeable have side doors. Several U24 limits do not hold as stated.

### The five most important open items

1. **Only workers are fenced, and several writers have no row (N1, N2).**
   - Unfenced callers that can move a stage under another holder or race a live verb:
     - the answer recorder and `/get-guidance`;
     - the reconciler;
     - the steward and the watcher on TEST-READY.
   - Roles that write with no row of their own in §4.5:
     - the conductor, who posts every lane's records (§8.2);
     - the arbiter;
     - the question checker.
   - By §4.5's own rule ("a role outside its row, is data"), every in-session round envelope is data.
2. **The U24 residual is reachable without a compromised agent (N5, with A4 and C16).**
   - §15.2's limit "the wrapper marks every agent write" is false in the code and in the design: §8.2 marks only
     `factory:` and `merge-steward:` lines.
   - So an ordinary, unmarked agent note counts as the authorised human. The phase notes and verbatim Q&A of
     `issue-tracking.md` are examples.
   - An agent's direct label write is recorded as a human override, which moves the stage without its predicate.
   - The forge-bound gates are a permission difference between tokens of ONE account. Self-review prevention cannot be
     used under that account.
3. **The claim ref's lifecycle contradicts itself (N4, with B1, C4 and C17).**
   - Expiry "replaces the token by compare-and-swap", but acquiring needs the ref to be absent.
   - Release deletes the ref, and with it the cursor that is supposed to spare every new holder a full scan.
   - Renewal "every N minutes during long steps" names no process to do it.
   - Fencing a branch push is a check followed by a write, unless the claim ref and the branch go in one atomic push.
4. **Issues can still strand (N3).**
   - A TEST-READY issue whose PR leaves the queue for any reason other than culprit, conflict or red CI has no exit.
     `merge_steward.eligibility` rejects for four such reasons.
   - A `ci-pending` issue whose PR gets no CI run is invisible to every queue.
   - `env-incident` issues sit at START and are pulled by triage once `needs-input` clears.
   - The recorder queue re-fires on every poll while any blocking question remains.
5. **The "unforgeable" facts have side doors (N7, N10).**
   - `Reverts-PR` lives on the revert commit, which sits on the second-parent side, where any PR can write a trailer.
   - GitHub trunk protection is not specified, though the workers' tokens can write contents.
   - The deploy verdict's source run is not pinned to a workflow, an event and an environment.
   - On GitHub the steward and the watcher post as `github-actions[bot]`, which any PR workflow can also do.

Close behind: N8 and N9.

- **N8:** on a default personal GitHub repository, GitHub Actions may not create pull requests. Revert-first therefore
  never opens its revert PR, and the deploy guard then skips every later deploy.
- **N9:** the maker's own session posts the checkers' records, so B6 stays open for in-session lanes.

---

## 1. Verdicts on the revision-1 findings

Section references are to revision 2's design.md unless noted.

| Id | Verdict | Evidence in revision 2 | What is left |
|---|---|---|---|
| A1 | partly | §4.5 role table; §4.2 names a caller per edge; §3.4 items 3–4; TEST-READY's two exits have callers | Gaps listed in N2 and N3. TEST-READY has no exit for rejects other than culprit, conflict or red CI, or for a PR closed by a human. Roles with no row: conductor, arbiter, question checker. The steward's env-incident and `blocked-by` writes are not in its row. The `split` close has no writer. The reconciler's "no forward edge" contradicts §4.4's roll-forward |
| A2 | verified | §8.1 `actor.agent` and `role`; maker ≠ checker checked on `agent` and `role` | `agent` is self-declared in bytes the conductor writes (N9) |
| A3 | verified | §5.1 one claim per issue, the stage informational; §3.4 item 1 | — |
| A4 | partly | §8.3 authorised-human filter; §12.3 reserved decisions; §6.3 lock option; U24 residual in §15.2 | Under U24 the filter separates nothing for agent writes that are not marked, and the design marks only machine lines (N5) |
| B1 | partly | §5.1 claim ref with `--force-with-lease`; fencing token = ref SHA; §5.2 reaper's own clock | The lease binds only cooperating clients: any token with contents write can `--force` or delete the ref. Fencing a branch push is check-then-act without `--atomic`. Renewal between wrapper calls has no mechanism. Expiry-replace conflicts with acquire-must-not-exist. Writes of a stale holder through REST are unfenced (N4) |
| B2 | partly | §4.4 intent first, done last; the reconciler rolls forward or back; the guard is named a read followed by writes | The reconciler cannot tell a crashed verb from a live one for callers that hold no claim (N1) |
| B3 | verified | §14 one queue per checker lane; §5.3 verify claims | The lane queues do not exclude `hold`, `blocked-by` or `needs-input` (N3) |
| B4 | partly | §12.7 answer recorder; §14 recorder queue | The queue's condition stays true after a partial answer or a comment that is not an answer, so the recorder restarts every poll (N3). Its interpretation of free text has no checker (N13) |
| B5 | partly | §4.3 ask hash (title + body without tick states), `/amend`, SPEC and IMPLEMENTATION only; §8.2 machine-comment definition | An agent's body edit that is not a tick is an ask change under the shared login. `issue-tracking.md` tells agents to add discovered checklist items, which is such an edit (N6) |
| B6 | partly | §8.5 downgrades need the lane's `accept`; §8.6 the steward re-runs the fold; the status is a projection | The conductor in the maker's session posts every lane's records (§8.2), including the `accept`, so the fold re-runs over bytes the maker side wrote (N9) |
| B7 | partly | §10.8 H7 landings from first-parent `Steward-PR` trailers; comments are projections; author filtering is a second layer | `Reverts-PR` is read from a commit any PR can author. Trunk is not protected on GitHub by anything in the design or the templates (N7) |
| B8 | verified | §6.3 admission by author; provenance lines never admit | — |
| B9 | partly | §15.2 one fine-grained token per host, without the permissions for irreversible operations; the GitHub App alternative was declined (U24) | Workers need contents write (branches, claim refs), and so can write trunk unless a ruleset stops them (N7). The token split is a permission difference within one account (N5). The dispatcher's write scope is not listed: claim expiry needs contents write, repairs need issues write |
| B10 | partly | §8.2 one envelope per round; §5 claims over git; PR projections off; token bucket; §15.2 "this is not measured" | New per-issue comment sources are not in the estimate: two audit lines per edge (§4.4), `factory: spend` at each checkpoint (§13), one ledger line per temporary resource (§11), answer and override lines. The reduction is unquantified in both directions |
| B11 | verified | §10.5 a red verdict marks no issue; H8 | — |
| B12 | verified | §10.8 H9 `verify_issue` transitions to CLOSE-READY and never closes | — |
| B13 | verified | §12.5 one `env-incident` issue per root cause, open, a `blocked-by` target | Those issues have no stage and are pullable at START (N3) |
| B14 | partly | §10.4 step 3: `workflow_dispatch` of the revert PR's CI or the exemption; `plan()` orders `revert` first; H10 | On a default personal GitHub repository the steward's `GITHUB_TOKEN` may not create the revert PR at all. The exemption and the ordering are keyed on a label any worker can set (N8) |
| B15 | verified | §10.8 H1 per PR, from trunk trailers; §4.2 TEST-READY → CLOSE-READY for EVERY PR | The `Reverts-PR` source (N7) |
| B16 | verified | §10.4 step 2.2 exactly one step and the dependency closure; signature; refunds (§13) | — |
| B17 | partly | §10.3 step 4 the restore guard and the SHA-256 digest check; §10.6 only the deploy role writes the cache | The REQUIRED Minimum tier of §10.6 does not list the stateful replacement/deletion detector the guard runs. "Old code on a migrated schema" cannot be seen in a CloudFormation change set (N14) |
| B18 | verified | §6.4 deterministic floor, raise only, re-derived at SPEC exit | — |
| B19 | verified | §4.2 S's tests, fixtures and configuration run over H's code | — |
| B20 | verified | §11 the `factory-issue` tag and the ledger; both must be empty | — |
| B21 | verified | §3.5 delivery modes | — |
| B22 | verified | §4.2 readiness is `do-not-merge` removed; drafts only where the forge has them | — |
| C1 | verified | §4.2 `--allow-pending` only when pending CI is the sole unmet clause | — |
| C2 | verified | §4.2 and §14: the worker sets `ci-pending` and releases; the verifier lane completes | Contradicts the tier-S "no hand-offs" row (N12). No timeout, and no path when no CI run exists (N3) |
| C3 | verified | §10.4 step 2.2 synthesizes the first-parent steward merges | — |
| C4 | partly | §8.2 paging with a client-side id filter; cursor in the claim ref; continuation issue at 2,000 | The release verb deletes the ref, and with it the cursor, so every hand-off makes the next holder scan in full (N4) |
| C5 | verified | §8.2 fold by comment or note id on both forges | — |
| C6 | verified | §13 report-only for the first 20 issues per tier | — |
| C7 | verified | §7.3 tier S keeps one combined pass | — |
| C8 | verified | §11 item 3 rotation, outside the empty backlog, no learning capture of its own | — |
| C9 | partly | §3.2 `split` flag, `blocked-by` every child, "closed administratively when the last child closes" | No role in §4.5 writes that close. When the block releases, the parent is a START issue pulled by triage again (N3) |
| C10 | verified | §3.2 `blocked-by`: cycles, closed targets, GitLab tier | — |
| C11 | verified | §5.1 ONE release verb, called by the steward and the watcher | — |
| C12 | verified | §12.4 deterministic always-ask list | — |
| C13 | verified | §6.3 the verbatim body, fenced, beside the paraphrase | — |
| C14 | verified | §4.2 `spec-approved` is a side effect written by the verb | — |
| C15 | verified | §10.4 step 2.4 the attributor ranks only inside the suspect set; logs are data | — |
| C16 | partly | §4.4 the reconciler compares a single label with the last `done` line | Under U24 an agent's direct label write is indistinguishable from an authorised human's. It becomes an `override` and moves the stage with no predicate (N5) |
| C17 | partly | §5.1 renewal in the wrapper on every verb call; §16 | "At least every N minutes during long steps" needs a process alive between wrapper calls. None is designed, and one that is designed renews for a hung worker forever (N4) |
| C18 | verified | §10.4 step 4 deploy guard | The guard freezes deploys when the revert PR cannot be created (N8) |
| C19 | verified | §10.7 assumptions listed | — |
| C20 | verified | §5.3 ascending order, random back-off | One `git push --atomic` of every claim ref would make the group claim a single compare-and-swap with no back-off (N4) |
| C21 | partly | §8.2 the fold rejects edited records; §5.1 no comment deletion; §19 item 4 deletion is a residual | Rejecting an edited record fails open for findings of earlier rounds. §13 says counters never come from editable comments, but the audit lines it uses are editable comments (N15) |
| C22 | verified | §8.7 step 4 deterministic re-check; an OVERRULING decision becomes a `needs-input` approval | Whether a decision overrules a finding should be computed from the records (the chosen option leaves a legal or security finding open), not judged by the arbiter |
| C23 | verified | Both target files are listed in the main checkout's local `.git/info/exclude` (read during this review) | — |
| D1 | verified | §2 label list | — |
| D2 | verified | §2; §18 small defects | — |
| D3 | verified | §10.5 uses TEST-READY; the dated appendix is kept as written | — |
| D4 | verified | §4.2 CLOSE-READY → closed defines the laundry list | — |

The four findings answered with a different mechanism, judged on whether the mechanism meets the need:

- **B1, claims via `--force-with-lease`:** the server-side compare-and-swap is the right primitive, and it spends no
  REST write budget. Lifecycle and fencing gaps remain (N4).
- **B7, landings from trunk trailers:** right for landings. Wrong for reverts as specified (N7).
- **C2, `ci-pending` plus the verifier lane:** meets the need. It needs a timeout and a no-run path (N3), and the tier-S
  table must say so (N12).
- **C22, escalate only an overruling decision:** meets the need, if "overrules" is computed (row above).

---

## 2. New findings

Each B finding uses the review-contract shape. The C and D findings are shorter.

### N1 (B): only workers are fenced; the other callers of the verb race the holder and each other

- **Location:** §4.4 Guard, third bullet; §4.4 "The reconciler"; §4.5 Steward, Watcher, Reconciler and Answer recorder
  rows; §5.1 "Acquire"; §12.7; §12.9 step 5.
- **Target quote:** "for a worker, the caller's fencing token is not the claim ref's current value".
- **Defect.** The fence applies to workers only. Four other callers write stages and records with no exclusion:
  1. **The answer recorder and `/get-guidance` move the stage under a worker's claim.** They may call "the transition
     an answer explicitly implies" (§4.5).
     - The recorder clears `needs-input` (§12.7). The issue is then pullable, and a worker claims it.
     - A human running `/get-guidance` on the same issue then transitions it (§12.9 step 5) while the worker holds the
       claim.
     - The recorder and `/get-guidance` can also run on one issue at once: the dispatcher starts the recorder on a
       fresh human comment while the human answers through `/get-guidance`.
     - Either way §3.4 item 2, "One writer per issue at a time", fails by design.
  2. **The reconciler races a live verb.** "An intent without `done` is rolled FORWARD when its side effects are present
     and back when they are absent."
     - A verb between its intent (step 2) and its side effects (step 3) looks exactly like a crashed one.
     - The reconciler rolls it back, then the live verb adds its labels and its `done` line.
     - For workers the claim's liveness could separate the two cases. For the steward, the watcher and the recorder
       there is no claim to consult.
  3. **The steward and the watcher both write TEST-READY's exits.** Nothing excludes them from each other.
     - The deploy job and the steward tick run in different workflows with different concurrency groups:
       `group: merge-steward` and `group: deploy-{{ENVIRONMENT}}`.
     - Each exit is a read followed by writes (§4.4 step 1).
     - If they interleave on one issue, the issue gets two stage labels. The reconciler then "repairs" from whichever
       `done` line came last, so the order of two network calls decides between CLOSE-READY and REWORK-REQUIRED.
- **Not defined anywhere:** the claim kind `record`. It is named once, in §5.1 "Acquire", and no section says who takes
  it or when.
- **Material-because:** P13 (check-then-act named) and §3.4 item 2. An issue closed whose PR the steward has just
  returned, or a transition lost to a roll-back, is a wrong-terminal-state failure.
- **Evidence:**
  - design.md §4.4, §4.5, §5.1, §12.7, §12.9;
  - the two workflow templates' `concurrency` blocks: `group: merge-steward` in `github-merge-steward.yml.template`,
    and `group: deploy-{{ENVIRONMENT}}` in `github-deploy.yml.template`;
  - a search of design.md for "`record`" finds only the definition of the claim kinds in §5.1.
- **Proposed edit (recommended first):**
  1. **Every caller takes the claim for the length of its verb call.** Extend the fence clause of §4.4 to every caller.
     - The steward, the recorder and `/get-guidance` take a claim of kind `record` for one verb call, and wait or back
       off while a worker holds the claim.
     - The reconciler repairs only an issue whose claim ref is absent or expired, and whose open intent is older than L.
       A live verb then always holds the ref.
     - Make the steward the ONLY caller of TEST-READY's exits:
       - the watcher posts its verification record, which is a fact;
       - the steward's next tick applies TEST-READY → CLOSE-READY.
     - That keeps the deploy job at `contents: read`. The verdict job of `github-deploy.yml.template` has
       `contents: read` and `issues: write`, so it could not take a claim ref anyway.
  2. Keep the watcher as a caller, and give the deploy job's verdict step `contents: write` so it can take a `record`
     claim. This widens the permissions of the job that holds deploy credentials.

### N2 (B): the authority table leaves writers without a row, and one row contradicts §4.4

- **Location:** §4.5 table and its closing rule; §8.1 `role` values; §8.2 "One envelope per ROUND"; §8.7 step 3;
  §12.4; §3.2 `blocked-by`, `split` and `env-incident` rows; §12.5; §10.4 step 6; §14 "the dispatcher when #N gets
  there".
- **Target quote:** "A write by any other identity, or by a role outside its row, is data: it is never counted by a
  predicate."
- **Defect.** The rule is strict, and the table does not cover the writers the rest of the design relies on:
  - **Conductor.** §8.2 has the conductor post "every lane's records of a round together".
    - §8.1 lists `conductor` as a role, but §4.5 has no Conductor row.
    - The Checker-lane row writes "finding, verification and verdict records"; the Worker row writes "its team's
      records".
    - Read literally, every in-session round envelope is written by a role outside its row, so it is data and the
      checker clause of §4.1 never holds.
  - **Arbiter.** It writes `decision` records (§8.1, §8.7) and has no row.
  - **Question checker.** It decides which questions reach the human (§12.4) and has no row.
  - **Steward.** Its row lacks:
    - `env-incident` issues (§10.4 step 6 has the steward open them);
    - `blocked-by` on the affected issues (§12.5);
    - the release verb (§5.1);
    - culprit, `red-since` and refund records (§10.4, §10.5, §13).
  - **Watcher.** Its row lacks setting `blocked-by` on the affected issues when it opens an `env-incident`.
  - **Reconciler and reaper.** Their row says "no forward edge", but §4.4 has the reconciler roll an intent FORWARD.
    Clearing `blocked-by` (§3.2) is not listed in their row either.
  - **The `split` close.** "Closed administratively when the last child closes" (§3.2) names no caller.
- **Material-because:** P11 (authority explicit). It is the A1 failure class: an edge or a record with no permitted
  writer is either never written, or written by a role whose writes are, by §4.5, data.
- **Evidence:** design.md §4.5 (the seven rows), §8.1 (`role`: lane, `maker`, `conductor`, `arbiter`, `recorder`),
  §8.2, §8.7, §12.4, §12.5, §3.2, §10.4 step 6.
- **Proposed edit:**
  1. Add Conductor, Arbiter and Question-checker rows.
     - The conductor's "May write" is "the round envelope, assembled verbatim from the lanes' parts".
     - The arbiter's is `decision` records.
     - The question checker's is a question verdict.
  2. Complete the Steward and Watcher rows from §10.4, §10.5, §12.5 and §5.1.
  3. Restate the reconciler's edge as "completes or undoes another role's recorded intent; starts no edge".
  4. Name the dispatcher as the caller of the `split` close, with the predicate "every child is closed".

### N3 (B): flag and queue combinations still strand issues or make them churn

- **Location:** §14 queue table; §4.2 TEST-READY → REWORK-REQUIRED; §3.2 `ci-pending`, `split` and `env-incident`;
  §12.5; §12.7.
- **Target quote:** "Hand-offs between stages are safe only if something guarantees a worker for every non-empty
  queue."
- **Defect.** Concrete combinations:
  1. **TEST-READY with a PR the steward rejects for a reason that is not an edge.**
     - `merge_steward.eligibility` rejects when:
       - the base is not trunk;
       - the PR is a draft;
       - the description carries closing text under the watcher;
       - a dependency was closed without landing.
     - `reject()` then returns the issue.
     - The design's only exits from TEST-READY are culprit, conflict, red PR CI, Track T's culprit record and a blocking
       finding. So the verb refuses these returns ("the refusal names the unmet clause").
     - A PR closed unmerged by a human has no exit either.
     - In each case the issue stays in TEST-READY. No queue holds TEST-READY, and the watcher waits for a landing that
       will never come. This is the stranding A2 (2026-11-02) was taken to stop.
  2. **`ci-pending` with no CI run.**
     - The verifier queue needs "the PR's CI run has ended", and every worker queue excludes `ci-pending`.
     - A PR with no run ends in neither queue:
       - path filters that skip every workflow;
       - a run queued with no runner;
       - a workflow file that fails to parse.
     - No timeout is defined.
  3. **`env-incident` issues are START issues.**
     - They carry no stage label and no audit line, which is §3.1's definition of START, and they are labelled
       `needs-input` (§12.5).
     - When the owner comments, the recorder clears `needs-input`, and the triage worker pulls an incident issue.
     - If the owner is not on the human allow-list, their comments are data (§8.3), and the incident's `needs-input`
       never clears.
  4. **The recorder restarts on every poll.** Its queue condition, "an authorised human comment newer than the last
     open question", stays true:
     - after a comment that answers one of two blocking questions;
     - after a human comment that is not an answer at all.
     The dispatcher starts the recorder again on every poll, each time a headless session.
  5. **Held, blocked or waiting issues are offered to checker lanes and the verifier.**
     - The lane and verifier queues do not exclude `hold`, `blocked-by` or `needs-input`.
     - A lane started on a held issue stops "at its next verb call" (§3.2), releases, and is started again on the next
       poll.
  6. **The `split` parent is re-triaged.**
     - It never leaves START: `split` is a flag.
     - When its `blocked-by` releases, it is a START issue for triage, because no caller closes it (N2).
- **Material-because:**
  - §14's own premise, and the 0-of-10 hand-off record that motivates the dispatcher;
  - for item 4, the write budget §15.2 calls binding and the model spend §13 reports.
- **Evidence:**
  - design.md §14 queue table, §4.2, §3.1, §3.2, §12.5, §12.7;
  - `src/payload/scripts/merge_steward.py` `eligibility` (four `reject` reasons) and `reject` (`_return_issue` for
    every issue of the PR).
- **Proposed edit:**
  1. Add a TEST-READY → REWORK-REQUIRED clause, "the steward rejected the PR, or the PR was closed unmerged", whose
     record carries the reason.
  2. Give `ci-pending` a timeout. After it, the verifier refuses with "no CI result", which returns the issue to the
     implementation queue.
  3. Exclude `env-incident` from every worker queue. Require the incident's owner to be on the human allow-list, or
     name a fallback owner.
  4. Make the recorder's condition "a human comment newer than the recorder's last run on this issue".
  5. Add `hold`, `blocked-by` and `needs-input` to the exclusions of the lane and verifier queues.
  6. Close the `split` parent as in N2.

### N4 (B): the claim ref's lifecycle contradicts itself, and fencing a push is check-then-act

- **Location:** §5.1 Acquire, Fencing token, Renew and Release; §5.2 Expiry; §8.2 Reading and Comment cap; §14 worker
  queue condition "no claim".
- **Target quote:** "Expiry replaces the token by compare-and-swap. The old holder's next call fails on the fence."
- **Defect:**
  1. **Expiry vs acquire.**
     - Expiry writes a new commit to the ref, so the ref still exists.
     - Acquire pushes with an empty lease, "the ref must not exist", so nobody can acquire an expired claim.
     - The worker queues require "no claim", so the issue drops out of every queue.
     - If expiry instead deletes the ref, the old holder's next renewal, which expects its own token, fails correctly.
       But the cursor is lost (item 2).
  2. **Release deletes the cursor.**
     - "The last folded id is recorded in the claim ref's commit message, so a new holder resumes from it and never
       full-scans."
     - The release verb deletes the ref, and every stage hand-off, `needs-input` and `ci-pending` releases.
     - So the cursor survives only expiry, and the common case is a full scan.
     - The continuation issue "inherits the stage, the claim and the cursor". But the claim ref is keyed by issue
       number, so inheriting it needs a second ref and a delete, which is unspecified.
  3. **Renewal between wrapper calls.**
     - "At least every N minutes during long steps" needs a process running between wrapper invocations, and the
       wrapper is a per-call CLI.
     - With no such process, a long test run or a long model turn outlives L.
     - With one, a hung but living worker renews forever, and expiry never fires.
  4. **Fencing a branch push.** "Every push for the issue checks that the caller's token is the ref's current value".
     A check followed by a separate push is check-then-act: the claim can expire between the two.
  5. **The lease binds only cooperating clients.**
     - Any token with contents write can `git push --force` or delete `refs/factory/claims/<n>`.
     - Every worker token has contents write (B9).
     - This belongs in §19 next to item 2.
  6. **The branch fallback `factory-claim/<n>`.**
     - Under the operator's token, every renewal is a branch push.
     - Every `on: push` workflow without a branch filter then starts a run.
     - Branch rulesets on `**` apply to it as well.
- **Material-because:**
  - §3.4 item 2 (one writer per issue);
  - §15.2's binding write budget: a full scan at every hand-off spends read budget and time, and a CI run per renewal
    spends runner minutes;
  - C4 and C17, which this mechanism was meant to close.
- **Evidence:**
  - design.md §5.1, §5.2, §8.2, §14;
  - git-push documentation: an empty `<expect>` in `--force-with-lease=<ref>:<expect>` requires the ref not to exist.
    `--atomic` updates all refs or none, and fails when the server does not support atomic pushes.
- **Proposed edit (recommended first):**
  1. **Make the ref permanent, and model the claim states as commits.**
     - After the first claim the ref always exists. Its tip is a `held` commit (kind, holder, cursor) or a `free`
       commit (cursor).
     - Acquire = compare-and-swap from the observed `free` tip, or from absence, to a `held` child.
     - Release = held → free.
     - Expiry = held → free, by the reaper.
     - The queues read "no claim" as "absent or `free`".
     - The cursor then survives every hand-off.
     - Push the issue branch and a renewal of the claim ref in ONE `git push --atomic`, so a branch push lands only
       while the caller holds the claim.
     - Acquire a group claim the same way, as one atomic push (it replaces C20's back-off).
     - Define renewal as "on every wrapper call only", and set L above the longest step measured in §13. Do not add a
       heartbeat.
     - Add "atomic push support on both forges" to O14.
  2. Keep delete-on-release, and move the cursor to a separate `refs/factory/cursor/<n>` updated by compare-and-swap.
     This fixes item 2 only.

### N5 (B): the U24 residual is not limited as §15.2 claims; an ordinary agent reaches it

- **Location:** §15.2 "The accepted residual" (the three limits); §8.2 "A machine comment"; §8.3; §4.4 the reconciler's
  override line; §12.3 item 3; §12.7.
- **Target quote:** "the wrapper: it marks every agent write, so an unmarked comment from the shared login can only
  come from outside it."
- **Defect.** The three limits do not hold as stated:
  1. **Marking.**
     - §8.2 says the wrapper marks "every `factory:` and `merge-steward:` line it writes", not every write.
     - In the code, `cmd_comment_issue` posts `{body: <text>}` unchanged, and `cmd_update_issue` writes the body
       unchanged.
     - `call.py`'s `GATED_OPERATIONS` does not gate `issues/create-comment`, `issues/update-comment` or `issues/update`.
     - Agents post free-text notes by rule. `issue-tracking.md` asks for a note at each phase transition, and for every
       question and answer "as a comment, verbatim".
     - Every such note is an unmarked comment from the operator's login. To §8.3, §12.7 and the recorder queue it is an
       authorised human's comment.
     - No compromised agent is needed: an agent that posts "Recommended: option 1" as a note gives the recorder an
       "answer".
  2. **Labels.**
     - §4.4 records a single hand-set stage label, "when an authorised human set it", as an override, and the stage
       moves with no predicate.
     - The label event's actor is the operator's login whether the human or an agent wrote it.
     - `call` can add labels, so any agent's direct label write is an override that skips every gate.
     - That also contradicts U21: "An answer from the operator does not skip a checker" (§12.3).
  3. **Forge-bound gates.**
     - Under U24, "the human's own credentials" and the agents' tokens belong to ONE account. The gate is only the
       permission set each token was created with.
     - The token copied today to every machine (§15.2) predates that split.
     - GitHub's protected-environment option to prevent self-reviews blocks users who started a deployment from
       approving it (GitHub Docs, "Deployments and environments"). The agents start deploys as the operator, so the
       option would also block the operator. It cannot be on, so the gate rests on the token permissions alone.
     - On GitHub Free, Pro and Team, required reviewers exist only for public repositories (same page). For a private
       repository on those plans, §12.3's example gate does not exist.
     - On GitLab, deployment approvals are Premium or Ultimate. By default the user who triggers a deployment pipeline
       may not approve it (GitLab Docs, "Deployment approvals"), the same conflict.
     - GitLab fine-grained personal access tokens became generally available only in GitLab 19.2 (GitLab Docs,
       "Fine-grained personal access tokens"). With only the legacy scopes, `api` grants complete read and write access.
  4. **Trunk** is a fourth door (N7).
- **Material-because:**
  - U24 itself: the operator accepted a residual limited by these three mechanisms, and the operator asked the reviewer
    to test whether they limit it;
  - P12 / U21 for the override path;
  - §12.3's reserved decisions.
- **Evidence:**
  - `src/payload/scripts/github_api/commands/issues.py`: `cmd_comment_issue`, `cmd_update_issue`;
  - `src/payload/scripts/github_api/commands/call.py`: `GATED_OPERATIONS`;
  - design.md §8.2, §4.4, §12.3, §15.2;
  - the GitHub and GitLab documentation named above.
- **Proposed edit (recommended first):**
  1. **Make the claim true, and stop treating an unmarked comment as an answer.**
     - The wrapper marks EVERY comment and body write: `comment-issue`, `update-issue`, `checklist`, and `call` on
       `issues/create-comment`, `issues/update-comment` and `issues/update`.
     - A gate refuses an unmarked write from an agent path, and denies forge MCP write tools to agents.
     - The recorder accepts only an explicit answer form (`/answer Q-3 = 1`) by an authorised login.
     - The reconciler never accepts a hand-set stage label as an override. A human changes a stage with an explicit
       `/stage <to> because …` comment, which the verb then evaluates like any call.
     - §15.2 states plainly that the forge-bound gates are a permission difference between tokens of one account, and
       which plans offer them.
  2. Keep the design, and restate §15.2 and §19 item 3: an ordinary agent's unmarked note, and any agent's label write,
     can act as the authorised human. This records the true size of the residual U24 accepted.

### N7 (B): `Reverts-PR` is read from PR-authored commits, and trunk is not protected on GitHub

- **Location:** §4.2 TEST-READY → CLOSE-READY; §4.5 "Facts are taken from where they cannot be forged"; §10.4 step 3;
  §10.8 H1, H7.
- **Target quote:** "landings and reverts from trunk's first-parent history, whose commits only the steward writes".
- **Defect:**
  1. **Revert facts.**
     - The `Reverts-PR: #<n>` trailer is on the revert PR's commit (§10.4 step 3).
     - When the steward lands that PR, its first-parent commit is the steward merge. That merge's trailers name the
       revert PR (`Steward-PR: #<revert PR>`), not the reverted one: see `merge_steward.py`'s train merge message.
     - So the revert fact is read from the second-parent side, which any PR author writes.
     - A worker's commit carrying `Reverts-PR: #k`, landing in an ordinary PR, makes PR k's landing look superseded.
       PR k's issue then never reaches CLOSE-READY, and no reland is scheduled, because nothing was reverted.
  2. **Trunk.**
     - "Only the steward writes" trunk is asserted, not enforced on GitHub.
     - No GitHub template or delivery document configures a ruleset. `gitlab-delivery.gitlab-ci.yml.template` does
       cover GitLab ("allow that token's bot user to push to the protected trunk").
     - The workers' per-host tokens need contents write for issue branches and claim refs. On GitHub that permission is
       repository-wide unless a ruleset restricts the trunk.
     - So a fast-forward push of a commit carrying `Steward-PR: #k` forges a landing on the history the design treats
       as unforgeable.
- **Material-because:** B7 and H1, the closing path of the model. A forged landing ends in a closed issue whose code
  never landed. A forged revert strands an issue (N3's failure class).
- **Evidence:**
  - design.md §4.2, §4.5, §10.4 step 3, §10.8;
  - `merge_steward.py`: the train merge message (`Steward-PR`, `Steward-PRs`, `Steward-Issues`, `Steward-Batch`,
    `Steward-Base`) and `TRAILER_RE`;
  - the trunk instructions in the GitLab template;
  - no counterpart in the GitHub templates.
- **Proposed edit (recommended first):**
  1. **Have the steward write the revert fact into its own first-parent merge.**
     - It writes `Steward-Reverts: #<n> <merge sha>` when the landed PR is a steward-opened revert (see N8).
     - The predicate reads only first-parent trailers.
     - Require a trunk ruleset that blocks updates by anyone but the steward, and verify it on `sff-test-*` (add to O14:
       which actor a GitHub ruleset can exempt for a `GITHUB_TOKEN` push).
     - As a check independent of the ruleset, the watcher confirms each first-parent landing against
       `GET /repos/{owner}/{repo}/activity` (operation `repos/list-activities`, filters `ref`, `actor`,
       `activity_type=push|force_push`; `docs/api-reference/github/rest/repos.md`). The push to trunk must be by the
       steward's actor.
  2. Keep the trailer on the revert commit, and accept it only when that commit's diff is the exact inverse of the named
     merge's first-parent diff. This is mechanical, but it does not cover trunk.

### N8 (B): on a default GitHub repository the steward cannot open the revert PR, and the deploy guard then freezes deploys

- **Location:** §10.4 steps 3–4; §10.8 H10; §4.5 Steward row.
- **Target quote:** "The steward opens `git revert -m 1 <merge>` as a PR labelled `revert`".
- **Defect:**
  1. **Creation.**
     - GitHub's "Managing GitHub Actions settings for a repository" page says that in a new personal-account
       repository, workflows may not create or approve pull requests by default. The switch is the setting "Allow
       GitHub Actions to create and approve pull requests".
     - The steward runs on `GITHUB_TOKEN` (`github-merge-steward.yml.template`), so on such a repository the revert PR
       is refused. H10 fixed the revert PR's CI, not its creation.
  2. **No owner for the failure.**
     - §10.4 step 4 skips trunk commits "that contain an attributed culprit without its revert". With no revert PR,
       every later deploy is skipped while landings continue.
     - The only escalation is the red-streak clock of step 6 (suggested 4 h), which reports an environment incident.
       The cause it would need to report is a repository setting.
  3. **Label keying.**
     - The CI exemption and `plan()`'s revert-first ordering key on the label `revert`.
     - Any worker can set that label on its own PR under the shared login, and jump the queue without PR CI. Train CI
       still runs.
- **Material-because:** revert-first is the design's central delivery mechanism (§10, decision U20). On the forge's
  default setting it does not start, and the guard written to protect it stops all deploys.
- **Evidence:**
  - the GitHub documentation page named above;
  - `GET /repos/{owner}/{repo}/actions/permissions/workflow` returns `can_approve_pull_request_reviews`, the API name of
    that setting (`docs/api-reference/github/rest/actions.md`);
  - the tick job's permissions in `github-merge-steward.yml.template`;
  - design.md §10.4.
- **Proposed edit:**
  1. Setup enables the setting.
  2. The steward checks `can_approve_pull_request_reviews` at the start of every tick and opens an `env-incident` when it
     is false.
  3. A failed revert-PR creation is itself an immediate `env-incident`, not a red streak.
  4. Key the exemption and the ordering on "opened by the steward's identity AND the head is `git revert -m 1` of a
     first-parent steward merge", never on the label.

### N9 (B): the maker's session posts the checkers' records, so maker ≠ checker for in-session lanes rests on the conductor

- **Location:** §8.2 "One envelope per ROUND"; §8.4 steps 2–3; §8.5; §8.6; §4.5 Checker-lane row.
- **Target quote:** "The conductor runs in the maker's session, so it cannot downgrade a blocking finding alone."
- **Defect.**
  - The same conductor:
    - receives each lane's part;
    - "dedupes";
    - posts the envelope, including any lane's `accept` that §8.5 requires for a downgrade.
  - The lane subagents return their output to the conductor, so there is no channel the conductor does not control.
  - The steward re-runs the fold (§8.6) over those same bytes.
  - So for in-session lanes:
    - the A2 fix (`actor.agent`) and the B6 fix (`accept` needed) are claims written by the maker side;
    - dropping a finding, or rewriting a verdict to CLEAN, leaves no trace.
  - This is not the U24 login question: it would hold under any identity model, because one process writes all the
    bytes.
- **Material-because:** §4.1's checker clause, and P12. The gate is only as independent as its writer.
- **Evidence:** design.md §8.2, §8.4, §8.5, §8.6. In §4.2 the adversarial verifier on `ci-pending` runs headless, as a
  separately started lane (§14), and is therefore the one checker whose bytes the maker does not post.
- **Proposed edit (recommended first):**
  1. **State the boundary, and lean on the independent lane.**
     - §8.5 and §19 say that in-session lane records are as trustworthy as the conductor.
     - The predicates that close a stage require at least one verdict from a separately started lane. The verifier of
       IMPLEMENTATION-READY → TEST-READY already is one. Add the same for SPEC-REQUIRED → IMPLEMENTATION-READY on tier
       M and L (a headless spec checker).
  2. Each lane posts its own part. This costs the write budget that one envelope per round saves (B10).

### N10 (B): the watcher's deploy fact is not pinned, and on GitHub the steward and the watcher share an identity any PR workflow has

- **Location:** §4.2 TEST-READY → CLOSE-READY ("a deploy + smoke green on a commit D"); §4.5 "CI results from the
  forge's run API"; §4.5 Steward and Watcher rows; §10.8 H7.
- **Target quote:** "CI results from the forge's run API."
- **Defect:**
  - The predicate does not say WHICH run counts. It names neither the workflow file path, nor the event (a push to
    trunk, or the steward's dispatch), nor the ref, nor the `environment`.
  - A PR branch based on the trunk contains every earlier landing. A workflow on that branch that is named or shaped
    like the deploy is "green on a commit containing every such landing".
  - Today `merge_steward.py verdict` takes `--conclusion` as an argument from the calling workflow. It reads no run.
  - On GitHub both §4.5 rows name `github-actions[bot]`. H7 says a PR workflow can post as that identity. So the
    steward's and the watcher's records are forgeable by the same route. Revision 2 moved only landings off that route,
    not culprit records, `red-since` or verification lines.
- **Material-because:**
  - TEST-READY → CLOSE-READY is the edge that leads to closing;
  - P11.
  A false CLOSE-READY leads the close-out to close an issue that was never deployed. Unlike N5, this needs no unmarked
  comment from the operator's login, so U24's limits do not apply.
- **Evidence:**
  - design.md §4.2, §4.5, §10.8 H7;
  - `merge_steward.py` `verdict` (`--conclusion` is an input);
  - `github-deploy.yml.template` (the verdict job's permissions, and `environment: {{ENVIRONMENT}}`).
- **Proposed edit:** the predicate reads the run from the run API, pinned to all of these:
  - the deploy workflow's path on the trunk;
  - event `push` or `workflow_dispatch` on the trunk ref;
  - the named environment;
  - conclusion `success`.
  The watcher's and the steward's issue records count only when they name a run that matches this pin.

### C and D findings

- **N6 (C): body edits under the shared login change the ask hash (§4.3).**
  - `issue-tracking.md` has agents add discovered checklist items, and adding an item is more than a tick-state change.
  - Under U24 that edit is "an authorised human" editing the body, which sends the issue back to SPEC-REQUIRED.
  - Edit: hash only the text above a machine-owned marker, and have the wrapper refuse agent edits above it.
- **N11 (C): `hold` does not stop landing.**
  - §3.2 says "every actor stops at its next verb call", but a landing is a trunk push, not a verb call.
  - The steward's own hold is `do-not-merge` on the PR (`STEWARD_DEFAULTS` `hold_label`; `eligibility` returns "wait"
    for it). It ignores the factory `hold` on the issue.
  - Edit: `eligibility` also waits while any issue the PR references carries `hold`.
- **N12 (C): the tier-S table contradicts `ci-pending`.**
  - §7.3 says "Hand-offs | none, unless the worker is interrupted: one claim from START to TEST-READY".
  - §4.2 makes every worker release at `ci-pending`, so every tier-S issue hands off once.
  - Edit the row, and count the cold start of the verifier in the tier-S cost.
- **N13 (C): the recorder interprets prose with no checker (§12.7).**
  - Turning "go with the second, but keep the flag" into `Q-<n> = <option or text>` is a judgement, even though the
    recorder "makes no decision".
  - Edit: the explicit answer form of N5, with free text recorded verbatim and left for the next worker's question
    checker.
- **N14 (C): the restore guard rests on detectors that are not required.**
  1. §10.3 step 4.2 runs "the stateful replacement/deletion check". §10.6's REQUIRED Minimum tier does not list that
     detector; §10.7 lists it as prevention.
  2. "Put old code on a migrated schema" cannot be seen in a CloudFormation change set. It needs a record of which
     migrations ran since the last green commit, which the Minimum tier does not require.
  3. The trunk verdict "records" each assembly's digest without saying where. If it is a `github-actions[bot]` comment,
     N10 applies. A forged digest only makes the restore refuse, so the failure is a denial of service, not a
     corruption.
  - Edit: add the detector and a migration ledger to the Minimum tier, and name the digest's storage, for example in
    the S3 object's own metadata, written by the deploy role.
- **N15 (C): rejecting edited records fails open, and audit lines are editable (§8.2, §13).**
  - The fold rejects an edited record. So editing an earlier round's envelope silently drops its findings, and the
    later verdict counts from the fold.
  - §13 says "Every counter is derived from the verb's audit lines … never from editable comments", but §4.4's audit
    lines are comments and are "not immutable".
  - Edit: an edited record puts the issue on `hold` with a tamper record instead of being skipped. §13 says "from audit
    lines, which are editable; see §19 item 4".
- **N16 (D): the flag line of §3.3's diagram omits `env-incident`.**

---

## 3. Checked and not settled here

- **O14 (custom refs, lease refusal).** Not tested; it needs a push to a forge. GitHub refuses pushes to the hidden
  `refs/pull/*`; whether it accepts `refs/factory/claims/*` is unverified. Add to O14:
  - atomic-push support on both forges (N4);
  - the actor a GitHub ruleset can exempt for a `GITHUB_TOKEN` trunk push (N7);
  - whether a push to a custom ref starts `on: push` workflows. The branch fallback starts them (N4 item 6).
- **U21 and §12.3 consistency** (review-response item 4):
  - Consistent: `needs-input`, approvals (§12.10) and admission (§6.3) all route reserved decisions to the authorised
    human.
  - Inconsistent: the label override of §4.4, a human act that skips the predicate (N5 item 2), and the recorder's
    interpretation (N13).
- **Write budget (B10).** Not measurable from the design. The new comment sources listed in the B10 row should enter
  the estimate before the reduction is claimed.
