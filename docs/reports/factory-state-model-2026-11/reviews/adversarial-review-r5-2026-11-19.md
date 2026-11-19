# Adversarial review of the factory state-model design, revision 5 (2026-11-19)

**Verdicts on the 16 open round-4 items (review-response.md Part 0):** 16 verified, 0 partly, 0 not-fixed,
0 disputed.

**New findings on revision 5's changes (Q1–Q11):** A 1 (Q1), B 3 (Q2–Q4), C 5 (Q5–Q9), D 2 (Q10, Q11).

OPEN ITEMS: 11

(Open = every round-4 item not verified, plus every new finding of any grade, D included, as in round 4.)

---

## Scope

**Subject.** Revision 5 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`1fce726`. Read:

- the full diff of `design.md` and `decisions.md` against revision 4 (`049a047`);
- `review-response.md` Part 0 and "What the next review should check (revision 5)";
- the sections around the changes: §2, §3.5, §4.2–§4.5, §5.1–§5.4, §7.2, §8.2–§8.5, §10.4, §10.5, §10.8, §11,
  §12.3–§12.9, §15.1, §15.2, §18, §19.

`traceability.md` was not reviewed. The review ran in a session independent of the designer's, from a detached
worktree, read-only.

**Product code read to check the design's claims:**

- `src/payload/scripts/merge_steward.py`:
  - `Steward.deploy_guard`;
  - `Git.merge` (`merge --no-ff` of the PR head) and `Git.is_ancestor`;
  - `trigger_deploy`, `after_batch_landed`, `reverify`;
  - `trigger_ci` and `ci_state`;
- `templates/ci/github-deploy.yml.template`, in full.

**Platform facts** come from vendor documentation, the vendors' issue trackers, community sources and
`docs/api-reference/`, each named where it is used.

**Ids.** Round-4 findings are cited as `aP<n>`, the designer's naming in Part 0 (they were `P<n>` in the round-4
report).

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account. Only whether the design states the residual truthfully
  is tested here.

**A disclosure.** Revision 5 resolves two of my round-4 findings in ways I did not propose, and several new findings
follow from those choices:

- P4 showed that removing "Actions: write" cuts the steward's wake-ups. My recommended option was
  `repository_dispatch` with the permission kept off. Revision 5 keeps the permission on worker tokens instead. Q1
  and Q7 are reachable only because of that.
- P5 proposed a write deploy key held by the operator for workflow-file landings. Revision 5 gives the deploy key to
  the steward for every push. Q3, Q5, Q6 and Q8 are about that key.

Q1's other half, a deploy guard that admits any ancestor of trunk, is in today's code and was already in revision 4.
Round 4 did not check it.

---

## Summary

Revision 5 applies every round-4 item. The protection tiers, the printed guidance forms, the reland fact and the
checkers that call their own exits all hold as written. What the simplifications leave open lies where they meet the
deploy workflow and the forge's actual behaviour:

- **The OIDC trust binds the run, not the commit it deploys (A).** A worker dispatches the trunk deploy with any
  commit reachable from trunk. That includes unreviewed intermediate commits of landed PRs, run with the production
  role on the protected tier (Q1).
- **The detected tier has no production guard (B).** There a worker pushes trunk, and the push starts the deploy with
  the worker's code. §12.3, §15.1 and §15.2 say otherwise (Q2).
- **A deploy-key push starts workflows (B).** After H14, every landing deploys twice, and trains run their CI twice.
  The deploy template's first rule assumes the opposite (Q3).
- **The fold does not bind a cited form to its issue (B).** Guidance-issue comments carry lines for many issues, and
  the fold accepts any authorised form for any issue's record (Q4).

The C items:

- the "one credential" depends on two invariants setup does not check (Q5);
- the detection's attribution may show the operator for both kinds of push (Q6);
- "Actions: write" also cancels, re-runs and deletes pinned runs (Q7);
- a refusal that no PR caused drops every PR (Q8);
- tool renewal acts as a heartbeat (Q9).

### Answers to "what the next review should check (revision 5)"

| Item | Answer |
|---|---|
| the round-4 items | all 16 verified (§1) |
| the deploy key as the one bypass, and its environment | the bypass is the category "deploy keys", not one key, and the environment admits every default-branch workflow, including those started by `pull_request_target` (Q5). A deploy-key push starts workflows (Q3). The activity record may name the operator (Q6) |
| the GitLab tier | holds as stated: fine-grained tokens from 19.2, a protected, masked and hidden variable, and the pre-19.2 residual in §15.2 item 5 |
| the per-tick detection | holds on GitLab, where the steward is a bot user. On GitHub it depends on Q6 |
| §15.2 and the detected tier's true size | trunk: yes. The production deploy: no (Q2) |
| workflow-file changes through the queue | the landing path holds: a deploy key is not subject to the `workflows` restriction. A refusal that no PR caused drops every PR (Q8) |
| privileged automation as `iam-iac` | holds for the net diff. Q1 bypasses it with an intermediate commit |
| `/get-guidance`, the guidance issue, the recorder | printing the forms closes aM5. Missing: the fold's binding of a cited form to its issue and value (Q4); edits to the block (Q11) |
| the reland fact, declared reverts, the CLOSE-READY and closed returns | hold |
| the checkers calling their own exits; the re-fold | hold. §5.3 still has the pre-revision wording (Q10) |
| the deploy role's OIDC trust; the per-action AWS bound | the trust holds for the run's ref, not for the commit deployed (Q1), and not on the detected tier (Q2). The AWS bound holds. §7.2 has the old wording (Q10) |

---

## 1. Verdicts on the round-4 items

| Id | Verdict | Where revision 5 fixes it | Note |
|---|---|---|---|
| aM5 (rest) | verified | §12.9 step 4: `/get-guidance` prints one block of form lines, the human posts them on the guidance issue, and no mark, hook or gate remains; §8.3; §15.2 "What limits it" without "or otherwise"; §12.9 "still not provable" | binding a cited form to its issue: Q4 |
| aP1 | verified | §4.2: the PR state is the last of `Steward-PR`, `Steward-Reverts` and `Steward-Relands`; the CLOSE-READY → REWORK-REQUIRED and closed → REWORK-REQUIRED edges; CLOSE-READY → closed re-checks; §10.4 step 3 "a merge that inverts a revert is therefore a reland"; §4.5 Steward row | — |
| aP2 | verified | §4.2 preamble; §8.5 "That checker calls the exit itself"; §4.5 Checker-lane row lists each exit | §5.3 wording: Q10 |
| aP3 | verified | §8.2 "never trusted for a decision", with the three re-fold cases; §4.2 preamble | — |
| aP4 | verified | §3.5 "What this does not need" and §15.2: worker tokens keep "Actions: write", so both wake-ups work | consequences of the permission: Q1, Q7 |
| aP5 | verified | §3.5 and H14: workflow-file changes land through the queue, and the steward pushes with its deploy key; a refused train push drops that PR | a deploy key may push workflow files (community source in Q3). Neighbours: Q3, Q5, Q8 |
| aP6 | verified | §3.5: on the protected tier, fine-grained worker tokens from GitLab 19.2 and a protected, masked and hidden variable; §15.2 item 5: before 19.2 GitLab is on the detected tier | — |
| aP7 | verified | §10.4 step 3: a revert must be declared and confirmed by its content; otherwise it is a candidate that changes no stage | — |
| aP8 | verified | §4.2 re-spec side effects; the `/stage` request dequeues first; §4.3 header names REWORK-REQUIRED | — |
| aP9 | verified | §4.3: the ask includes every executed `/amend`, in comment order | — |
| aP10 | verified | §4.2: four outcomes, and only `green` counts; §10.4 step 5 "a skipped one is neither" | re-runs and cancels: Q7 |
| aP11 | verified | §3.2: payload label lists; `priority:critical` from a source record the dispatcher re-reads; §8.2; §15.2 | — |
| aP12 | verified, differently from the proposal | §3.5: privileged automation is tagged `iam-iac`, and §19 item 14 states the residual. On the protected tier no `GITHUB_TOKEN` can push trunk, so other write workflows no longer reach it. §4.5 corrects the `github-actions[bot]` text | the environment is the new shared exemption: Q5 |
| aP13 | verified | §5.1: commit-hook renewal is best-effort and in the background; `run_tests.py` and `suite_semaphore.py run` renew | Q9 |
| aP14 | verified | §5.4: the claim ref is pushed first, then the label and the `continued from` line, then the old issue is closed | — |
| aP15 | verified | §4.2 and §10.4 step 3: `return_run_details` stated per API version | — |

---

## 2. New findings

### Q1 (A): a worker token deploys any commit reachable from trunk, with the production role

- **Location:**
  - §15.1 rule 5;
  - §12.3 item 3;
  - §15.2, "What that requires" (worker tokens keep "Actions: write") and "What limits it";
  - §3.5 "What this does not need";
  - §10.4 step 3, "Deploys the steward starts".
- **Target quote:** "**Deploys run only in CI, from trunk**: the deploy role's trust policy names only the trunk's OIDC
  subject" (§15.1 rule 5).
- **Defect:**
  1. **The trust checks the run's ref, not the deployed commit.**
     - The deploy template's `workflow_dispatch` takes an input `sha`.
     - The `deploy` job names the environment and checks out `inputs.sha || github.sha`. It then runs the project's
       deploy steps from that checkout.
  2. **The guard admits every ancestor of trunk.** `deploy_guard` accepts
     `sha == trunk or self.git.is_ancestor(sha, self.trunk_ref)`.
  3. **Every commit of every landed PR is such an ancestor.**
     - The steward lands with `git merge --no-ff <PR head>` (`Git.merge`). Intermediate commits are part of trunk's
       history, and no checker reviewed them on their own.
     - The lanes review the PR's net diff, and the `iam-iac` floor fires on the paths that net diff touches.
  4. **The path.**
     - Worker tokens keep "Actions: write" (§15.2).
     - A worker dispatches the deploy workflow on ref trunk, with `sha` set to an intermediate commit of its own landed
       PR.
     - The run's ref is trunk, and its environment is the production environment limited to trunk. So its OIDC
       subject matches the role's trust on both tiers.
     - The deploy steps that run are the intermediate commit's.
  5. **An example.**
     - A session that read untrusted content may hold a worker token.
     - It commits a changed deploy script and reverts that change in its next commit. The PR lands with no net change
       to the script.
     - Its dispatch then runs the first commit's script with the production role.
     - §15.1 rule 5 says this cannot happen: "A session that reads untrusted content … never holds deploy
       credentials".
  6. **Older trunk commits as well.** The same dispatch deploys any older trunk commit: the one before a security
     fix, or a culprit before its revert. §12.3 item 3 names only WHEN a deploy runs as the standing permission, not
     WHICH commit.
- **Material-because:**
  - §15.1 rule 5 and R90: the production deploy needs credentials no agent session holds;
  - §12.3 item 3: irreversible operations;
  - the protected tier's prevention claim in §15.2.
- **Evidence:**
  - `templates/ci/github-deploy.yml.template`: `on.workflow_dispatch.inputs.sha`, job `deploy`;
  - `merge_steward.py`: `Steward.deploy_guard`, `Git.merge`, `Git.is_ancestor`;
  - design.md §3.5, §12.3, §15.1, §15.2;
  - GitHub Docs, "OpenID Connect reference": a job that names an environment gets the subject
    `repo:ORG/REPO:environment:NAME`.
- **Proposed edit (recommended first):**
  1. **Deploy only trunk's tip.**
     - Remove the `sha` input. The deploy checks out `github.sha` of a run whose ref is trunk.
     - Every deploy the steward starts today is already trunk's tip: `after_batch_landed` right after a landing, and
       `reverify` with `trunk`.
     - Under H14 the landing push starts the `push` run (Q3). The steward pins that run by `head_sha`, as §4.2
       already allows, and stops dispatching.
     - A worker's dispatch can then only redeploy the current tip, which is the WHEN residual §12.3 already states.
     - §15.1 rule 5 adds: "and the commit it deploys is trunk's tip; the deploy takes no commit input".
  2. Keep the input, and let `deploy-guard` accept only a first-parent steward merge no older than the last deployed
     commit. §15.1 rule 5 then names that guard as part of the boundary.

### Q2 (B): on the detected tier any worker runs its own code with the production role, and four places say otherwise

- **Location:**
  - §12.3 item 3;
  - §15.1 rule 5, last sentence;
  - §15.2, "What that requires" (the bullet on worker tokens keeping "Workflows" and "Actions: write");
  - §15.2, residual item 5;
  - §19 item 4.
- **Target quotes:**
  - "What guards these operations is credentials no agent session holds" (§12.3);
  - "A workflow a worker writes on its branch cannot assume it, on either tier." (§15.1);
  - "Trunk and the production deploy are guarded instead by credentials no worker holds" (§15.2).
- **Defect:**
  - **A trunk push runs the worker's code with the deploy role.**
    - On the detected tier "any worker token can push trunk" (§3.5).
    - A trunk push starts the deploy workflow's `push` trigger.
    - Any workflow the push adds to trunk runs with the subject `repo:<owner>/<repo>:ref:refs/heads/<trunk>`, which
      the deploy role trusts.
    - Environments are not available on this tier (§3.5 table), so the environment subject is not an option.
  - **Detection comes too late.** On this tier the deploy role guards nothing against a worker: the worker chooses
    the code, and the trigger runs it with production credentials. The detection stops the steward landing, but the
    deploy starts with the push.
  - **The texts disagree.**
    - §15.2 item 5 says "the push, and any trunk workflow it starts, has already happened". That is true, but it does
      not say this includes the production deploy with the worker's code.
    - §12.3 item 3, §15.1 rule 5 ("on either tier"), §15.2's bullet and §19 item 4 state the opposite, with no tier
      qualifier.
  - **This is a real case.** The design places the operator's main project on this tier (§3.5 table, Detected row).
- **Material-because:**
  - U24's residual "stated at its true size" (§15.2);
  - whether §15.2 states the detected tier truthfully;
  - §12.3 item 3.
- **Evidence:**
  - design.md §3.5 (Detected row), §12.3 item 3, §15.1 rule 5, §15.2, §19 item 4;
  - `github-deploy.yml.template` `on.push.branches`;
  - GitHub Docs, "OpenID Connect reference" (the subject without an environment).
- **Proposed edit (recommended first):**
  1. **State the tier in each place.**
     - §12.3 item 3 and §15.1 rule 5: "on the protected tier".
     - §15.2 item 5 adds: "including the production deploy, which then runs the worker's code with the deploy role".
     - §19 item 4 says the same.
  2. In addition, as the operator's decision: setup refuses a production environment on the detected tier. Factory
     mode there deploys only to non-production environments.

### Q3 (B): a deploy-key push starts workflows, so every landing deploys twice and every train runs its CI twice

- **Location:**
  - §3.5 "What this does not need", second bullet;
  - §10.8 H14;
  - §4.5 Steward row;
  - `templates/ci/github-deploy.yml.template`, header rule 1;
  - §18 Delivery row.
- **Target quote:** "The steward pushes its trains and trunk with its deploy key, on both tiers" (§3.5).
- **Defect:**
  - **The template assumes the opposite of what the forge does.**
    - A push made with `GITHUB_TOKEN` starts no workflow; a push made with a deploy key does. The check-spelling
      wiki, "Feature: Update with deploy key", says: "Deploy keys allow repository workflows to make pushes that
      trigger workflows, unlike the GITHUB_TOKEN".
    - The deploy template's header says: "Under the steward the trunk only moves by the steward's GITHUB_TOKEN push,
      so the two triggers never both fire for one landing."
  - **Every landing deploys twice.**
    - After H14 both triggers fire: the landing push starts a `push` run, and `after_batch_landed` dispatches a second
      run for the same commit.
    - With one concurrency group and `cancel-in-progress: false`, an idle environment runs the first and then the
      second.
    - So every landing that arrives at an idle environment deploys its commit twice. That doubles the deploy time
      TEST-READY waits on. The template header itself cites a 90-minute deploy.
  - **Every train runs its CI twice.**
    - A project CI workflow whose `push` trigger matches `steward/train-*` runs once from the push and again from
      `trigger_ci`'s dispatch.
    - `ci_state` takes the newest run, so the verdict is still right, at twice the runner cost.
  - **Not stated.** The design mentions neither effect, and §18 lists no change to the deploy template.
- **Material-because:**
  - template rule 1 is existing behaviour that this change breaks (unchanged behaviour);
  - TEST-READY latency (§10.2) and the deploy throughput that the template's supersession exists to protect.
- **Evidence:**
  - design.md §3.5, H14, §4.5;
  - `github-deploy.yml.template`: header and `on:`;
  - `merge_steward.py`: `after_batch_landed`, `trigger_ci`, `ci_state`;
  - the check-spelling wiki page named above.
- **Proposed edit (recommended first):**
  1. **Let the push start the deploy.**
     - The steward stops dispatching a deploy after a landing. The pinned verdict reads the push run by `head_sha`,
       as §4.2 already allows. This is the same change as Q1's first option.
     - Template rule 1 becomes "the steward's deploy-key push starts the deploy".
     - Setup checks that the project's CI `push` triggers exclude `steward/train-*`. Where they do not, the steward
       stops dispatching train CI.
  2. Keep the dispatch. Under `merge: steward` remove the deploy's `push` trigger; it stays for `merge: direct`.
     Exclude train refs from the CI `push` triggers.

### Q4 (B): the fold does not check that a cited form names this issue, or that the record matches it

- **Location:** §8.3 "The fold checks every form a record cites"; §12.7; §12.9 step 4.
- **Target quote:** "It accepts a recorder record only when the cited comment exists, is unedited, is unmarked, is an
  explicit form, and has an author on the allow-list."
- **Defect:**
  - **Forms now come from other issues.** Revision 5 makes a comment on another issue the normal source of a form.
    One guidance-issue comment carries lines for many issues, for example `/answer #12 Q-3 = 1` and
    `/answer #15 Q-3 = 2`.
  - **The five conditions do not bind.**
    - They hold for that comment whichever issue's record cites it, and whichever of its lines the record applies.
    - Question ids are per issue (`Q-<n>`), so `Q-3` exists on many issues.
  - **So wrong records pass.** These records on #12 all pass the fold:
    - one that applies #15's line;
    - one that cites a form posted on #15 itself;
    - one whose value differs from the cited line.
  - **The fold must check the recorder.** The fold is the check on the recorder, which wrote the record. If it does
    not bind the record to the form, it proves only that some authorised form exists somewhere.
- **Material-because:**
  - §12.3 item 1: only an authorised human answers a reserved decision;
  - §8.3's premise that the fold, not the recorder, decides what counts.
- **Evidence:** design.md §8.3, §12.7 (the record `factory: answer Q-<n> = <option or text> (by <login>, comment
  <id>)`), §12.9.
- **Proposed edit:** add three conditions to the fold's list:
  - the cited comment is on this issue or on the guidance issue;
  - the line applied is a form for this issue (on the guidance issue, naming this issue first);
  - the record's form and value equal that line's.

### Q5 (C): "exactly ONE credential" rests on two invariants that nothing checks

- **Location:** §3.5 Protected row; §15.2 "What limits it" (protected tier); §19 item 1 (O14).
- **Defect:**
  1. **The bypass covers every deploy key.**
     - A ruleset's deploy-key bypass applies to all of the repository's deploy keys, not to one. In the REST API,
       for `actor_type` `DeployKey`, `actor_id` "should be null": GitHub's REST documentation, quoted in
       github/rest-api-description #4406.
     - Any other write deploy key, such as a CD tool's or an old one, can also push trunk.
     - This also answers O14's first question.
  2. **The environment's limit is on the run's ref.**
     - Every default-branch workflow that names the steward's environment can read the key. That includes workflows
       started by events a worker causes:
       - `pull_request_target`, whose ref has always been the default branch since 2025-12-08 (GitHub changelog
         2025-11-07, "Actions pull_request_target and environment branch protections changes");
       - `issue_comment`;
       - `workflow_run`.
     - A default-branch workflow that names the environment and checks out PR code hands the key to the PR. §19
       item 14's checkers are then the only guard.
- **Proposed edit:**
  - Setup and update check that the steward's key is the repository's only write deploy key. Listing deploy keys
    needs the operator's token, so the tick cannot check this.
  - The tick checks that no workflow file on trunk except the steward's names the steward environment.
  - §3.5 says "every deploy key".
  - §19 item 1 drops the answered part of O14.

### Q6 (C): the detection's attribution may show the operator for the steward's push and for a worker's push alike

- **Location:** §3.5 "Detection, on every tier"; §10.8 H7; §15.2 item 5; O14.
- **Defect:**
  - **GitHub shows a deploy-key push as made by the key's adder.** Stack Overflow 30251147 shows a deploy-key tag
    push displayed as the team member who added the key.
  - **Every push could show the operator.** Setup adds the steward's key with the operator's token, and under U24
    every worker token is the operator's account. If the activity record's `actor` follows the same rule, the
    steward's push and a worker's push both show the operator.
  - **Other payloads say which credential pushed.** Webhook payloads carry a `pusher_type`, "user or a deploy key"
    (GitHub Docs, "Webhook events and payloads"). O14 asks what the activity record carries.
  - **What is left is a shape check.** Without attribution, detection only checks that each first-parent commit is a
    steward merge with trailers. A worker passes it by writing those trailers. §15.2 item 5 ("stops the steward
    landing after the fact") then holds only for pushes that do not forge them.
  - **GitLab is not affected.** There the steward is a bot user.
- **Proposed edit:**
  - O14 asks the exact question: does the activity record distinguish a deploy-key push from a push made with its
    adder's token?
  - §3.5 states the answer either way.
  - If it does not, §15.2 item 5 says that on GitHub's detected tier a push carrying forged steward trailers goes
    undetected.

### Q7 (C): "Actions: write" also cancels, re-runs and deletes the pinned deploy run

- **Location:** §4.2 TEST-READY → CLOSE-READY (the pinned verdict and its four outcomes); §10.4 step 5; §15.2.
- **Defect:**
  - **The permission covers more than dispatch.** It also grants `POST …/runs/{run_id}/cancel`,
    `POST …/jobs/{job_id}/rerun` and `DELETE …/runs/{run_id}` (`docs/api-reference/github/rest/actions.md`).
    Re-running failed jobs is routine for a CI agent.
  - **The design does not say how the pinned verdict reads three cases:**
    - **A re-run.** The jobs API returns the latest attempt by default (`filter=latest`). A green re-run of a red
      deploy turns a red that Track T has already acted on into a green of the culprit's own commit.
    - **A deleted run,** which then returns 404.
    - **A run a worker cancelled.**
- **Proposed edit:**
  - The pinned verdict reads attempt 1 (`/attempts/1/jobs`) and records later attempts as data.
  - A cancelled or missing pinned run counts as `skipped or refused`, and the steward starts a new deploy.
  - §12.6 lists re-running and cancelling deploys next to dispatching.

### Q8 (C): a push refusal that no PR caused drops every queued PR

- **Location:** §10.8 H14, second bullet; §4.2 TEST-READY → REWORK-REQUIRED.
- **Defect:**
  - **Most refusals now have no culprit PR.** After H14 the deploy key may push workflow files. A train push is then
    refused mostly for reasons no PR causes: the key revoked, its secret missing, or a transport failure.
  - **One lapsed key empties the queue.** Each refused train drops "that PR" with `queue-failed`. So one lapsed key
    sends every queued issue to REWORK-REQUIRED.
  - **"That PR" is undefined for cumulative trains.** A refusal of train k also refuses every later train, so "that
    PR" has no single meaning.
- **Proposed edit:**
  - Only a refusal that names the PR's own content (a file over GitHub's size limit, a push-ruleset path rule) drops
    the newest PR of the first refused train.
  - An authentication, permission or transport refusal, or a refusal of every train, is an `env-incident`, and that
    tick lands nothing.

### Q9 (C): renewal from `run_tests.py` and `suite_semaphore.py run` is a heartbeat

- **Location:** §5.1, "Renew", third bullet, against §5.1's "There is no heartbeat process, so a hung worker stops
  renewing and expires."
- **Defect:**
  - These tools renew "while they run or wait for a slot". So a hung suite (a deadlocked test), or a slot wait that
    never ends, keeps the claim held for as long as the process lives.
  - `ci-owns-the-test-suite.md` sets no bound on the slot wait ("WAITS for a free one").
  - The reaper's expiry (§5.2) never fires for that worker.
- **Proposed edit:**
  - Tool renewal stops at a ceiling, for example 2 × L, and only while the calling session is alive.
  - Past the ceiling the tool exits non-zero, and the claim expires as §5.2 describes.

### Q10 (D): wording left from earlier revisions

- §2, second table, the Actions-may-create-PRs row: "the steward checks it every tick (H11, §3.5)". H11 and §3.5 now
  say it detects a refusal at revert time.
- §7.2 CLOSE-READY row: "may delete only resources tagged … (tag-conditioned IAM)". §11 now bounds S3 objects by name
  prefix (R89).
- §5.3 "Verify claims": "It may write only its own records (§4.5) and, as the verifier, the `ci-pending`
  completion". Under R81 every separately started checker calls its exit (§4.5 Checker-lane row).

### Q11 (D): the guidance issue's own handling

- **Edits.** An edited guidance comment fails "is unedited" for every line in its block. §12.9 step 7's summary should
  tell the human to post a corrected block, never to edit one.
- **Locking.** On a public repository, setup locks the guidance issue so that only collaborators can comment (GitHub
  Docs, "Locking conversations"). Outsiders' lines are ignored anyway, so this only removes noise from the
  dispatcher's scan.
