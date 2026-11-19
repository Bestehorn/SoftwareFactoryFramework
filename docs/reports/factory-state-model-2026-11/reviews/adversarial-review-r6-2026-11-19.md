# Adversarial review of the factory state-model design, revision 6 (2026-11-19)

**Verdicts on the 11 open round-5 items (review-response.md Part 0):** 11 verified, 0 partly, 0 not-fixed,
0 disputed.

**New findings on revision 6's changes (R1–R7):** A 0, B 2 (R1, R2), C 3 (R3–R5), D 2 (R6, R7).

OPEN ITEMS: 7

(Open = every round-5 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 6 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`8df28db`. Read:

- the full diff of `design.md` and `decisions.md` against revision 5 (`1fce726`);
- `review-response.md` Part 0 and "What the next review should check (revision 6)";
- the sections the changes touch: §3.5, §4.2, §8.3, §10.3, §10.4, §10.6, §10.8, §12.3, §12.6, §12.9, §15.1, §15.2, §18,
  §19.

`traceability.md` was not reviewed. The review ran in a session independent of the designer's, from a detached
worktree, read-only.

**Product code read to check the design's claims:**

- `templates/ci/github-deploy.yml.template`, the header (rules 1–3) and the `guard` → `deploy` job structure;
- `src/payload/scripts/merge_steward.py`:
  - `Steward.deploy_guard`;
  - the train merge message;
  - the GitLab host's `trigger_deploy` and `redeploy`.

**Platform facts** come from vendor documentation and `docs/api-reference/`, each named where it is used.

**Ids.** Round-5 findings are cited as `aQ<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide. It is reviewed only for whether the design states it truthfully.

---

## Summary

Revision 6 applies every round-5 edit, and the per-tier statements of the production guard are now true where they
stand. Two of the new rules fail against the deploy workflow's own mechanics:

- **The cancelled-pin rule fights the supersession (B).** A newer pending deploy cancels the older pending one by
  design; that is the template's batching. Revision 6 answers every cancelled pinned run with a new dispatch, and each
  dispatch cancels the next pending run. While one deploy runs, the steward dispatches on every tick, and at least one
  redundant deploy of the same tip follows (R1).
- **"A re-run of an older commit concludes skipped or refused" depends on where the check runs (B).** GitHub re-runs
  a single job with the earlier jobs' results. So a tip check in the template's separate `guard` job does not run
  again. Runs made under the old template stay re-runnable for 30 days (R2).

The C items:

- the production role and the steward's key reach jobs other than the deploy job through the trust's ref subject,
  expression-valued environment names and reusable workflows (R3);
- a landing whose push run never appears, for example because a worker disabled the deploy workflow, has no pinned run
  and no handling (R4);
- other workflows with a trunk `push` or `workflow_run` trigger now start on every landing, and only train CI is
  checked (R5).

### Answers to "what the next review should check (revision 6)"

| Item | Answer |
|---|---|
| the round-5 items | all 11 verified (§1) |
| the tip-only deploy (H15) | the input and the any-ancestor path are gone. The re-run claim holds only for a check inside the deploy job, run from trusted code; old-template runs stay re-runnable (R2) |
| the landing's push run as the pinned deploy | holds for pinning. The cancelled-pin rule loops against supersession (R1). A push run that never appears is not handled (R4). Other push-triggered workflows (R5) |
| the re-verify dispatches | hold |
| the classified train-push refusals (H14) | hold. The cumulative-train reasoning ("that PR is the one that added the refused content") is right |
| the fold's binding of a form to its issue (§8.3) | holds. One wording gap: a line naming another issue on issue N (R7) |
| the environment checks and the only-write-deploy-key check (§3.5) | the key check holds. The environment check is static, so it misses expression-valued names and reusable workflows, and the trust's ref subject bypasses it (R3) |
| the per-tier statements (§12.3, §15.1, §15.2, §19 item 4) | true per tier as written, given R2 and R3 |
| O16 | stated truthfully in §15.2 item 5 and decisions.md. The operator's options also include moving the repository to a plan that has the protected tier; O16 does not list that option, which is the operator's to add, not a defect |

---

## 1. Verdicts on the round-5 items

| Id | Verdict | Where revision 6 fixes it | Note |
|---|---|---|---|
| aQ1 | verified | H15: no `sha` input; the deploy deploys only trunk's tip, read at job start; §10.4 step 4; §15.1 rule 5; §12.3 item 3 | where the check runs: R2 |
| aQ2 | verified | §12.3 item 3, §15.1 rule 5, §15.2 bullet and items 3 and 5, §19 item 4, each per tier; O16 | — |
| aQ3 | verified | §3.5: a deploy-key push starts `push` workflows; §10.4 step 3: the landing's deploy is the push run and the steward dispatches only `reverify`; §4.2 pins the push run by `head_sha`; §18: template rule 1 rewritten, and setup checks train refs | R1, R4, R5 |
| aQ4 | verified | §8.3: the three binding conditions | R7 |
| aQ5 | verified | §3.5: the only write deploy key, checked by setup and update; the steward refuses and checks every tick for other workflows that name its environment or the production environment; §3.5 cites the bypass for all keys; O14 trimmed | the check's reach: R3 |
| aQ6 | verified | §3.5 states what detection catches on the detected tier either way; §15.2 item 5; O14 asks the exact question | — |
| aQ7 | verified | §4.2: the first attempt (`/attempts/1/jobs`); a cancelled or deleted pinned run counts as `skipped or refused`; H13; §12.6 | the cancel rule meets supersession: R1. GitLab: R6 |
| aQ8 | verified | H14: refusals classified; a content refusal drops the newest PR of the first refused train; other refusals are an `env-incident` | — |
| aQ9 | verified | §5.1: renewal only while the parent process lives, up to 2 × L, then exit non-zero | — |
| aQ10 | verified | §2 row, §5.3, §7.2 restated | — |
| aQ11 | verified | §12.9 step 4: the guidance issue is locked and corrected by a new block; step 7's summary repeats it | — |

---

## 2. New findings

### R1 (B): the cancelled-pin rule answers the deploy's own supersession with dispatches, which supersede again

- **Location:** §4.2 TEST-READY → CLOSE-READY ("a pinned run that was cancelled or deleted counts as `skipped or
  refused`, and the steward then dispatches a new deploy of trunk's tip"); §10.4 step 3; H13.
- **Target quote:** "a pinned run that was cancelled or deleted counts as `skipped or refused`, and the steward then
  dispatches a new deploy of trunk's tip" (§4.2).
- **Defect:**
  - **Supersession cancels pending runs as a matter of course.** The deploy template's rule 2 is one concurrency
    group with `cancel-in-progress: false`, so "a newer PENDING deploy replaces an older pending one". GitHub cancels
    the replaced pending run ("Control the concurrency of workflows and jobs"). Rule 3: that "loses no verdict, because
    verification is by ANCESTRY".
  - **Since revision 6, every landing's pin is such a run.** It is the landing's push run. So while one deploy runs,
    the push run of every landing but the newest is cancelled by the next landing.
  - **The rule then loops.** Take landings L2 and L3 arriving while L1's deploy runs:
    - L3's push run cancels L2's.
    - The steward sees L2's pin cancelled and dispatches D1 for the tip.
    - D1 cancels L3's pending push run. The next tick sees that pin cancelled and dispatches D2, which cancels D1, and
      so on.
    - That is one dispatch per tick for as long as L1's deploy runs.
  - **A redundant deploy follows.** When L1's deploy ends, the last pending dispatch runs. The next tick finds its
    predecessor cancelled and dispatches once more, and that run deploys the same tip again after the first finishes.
    So the rule brings back the double deploy that aQ3 removed, in exactly the busy periods the supersession exists
    for.
  - **The rule is also inconsistent.** A run "refused" because a newer landing exists gets no dispatch, while the
    same situation reached by supersession does.
- **Material-because:**
  - unchanged behaviour: template rules 2 and 3;
  - deploy throughput and TEST-READY latency (§10.2), which were aQ3's reasons.
- **Evidence:**
  - design.md §4.2, §10.4 step 3;
  - `github-deploy.yml.template` header rules 2 and 3, `concurrency:`;
  - GitHub Docs, "Control the concurrency of workflows and jobs": a newly queued run cancels the group's existing
    pending one.
- **Proposed edit (recommended first):**
  1. **Redeploy only when nothing newer covers the commit.** A cancelled or deleted pinned run needs a new deploy only
     when no other pinned run whose commit contains D is pending, running or done. That run is a newer landing's push
     run or an earlier re-verify dispatch. Supersession is then the normal case it was meant to be, and only a cancel
     with nothing behind it (a worker's cancel, a deletion) leads to a dispatch.
  2. Redeploy only for a cancel the steward did not cause and supersession did not cause. This needs the cancelling
     actor, which the run API does not report as a field, so option 1 is the one that can be checked.

### R2 (B): a single-job re-run skips a tip check that sits in another job, and old-template runs stay re-runnable

- **Location:** H15 ("its job deploys only when its commit is trunk's tip, read when the job starts … That also covers
  a re-run"); §15.1 rule 5; §12.3 item 3; §18 Delivery row (the template change).
- **Target quote:** "a re-run or queued run of an older commit concludes `skipped or refused` (H15)" (§15.1 rule 5).
- **Defect:**
  1. **Today's check is a separate job.** The template's guard is the `guard` job, and `deploy` has `needs: guard`.
     It deliberately runs the default branch's copy of `merge_steward.py` ("so a dispatch can never make the guard run
     the commit it guards").
     - GitHub re-runs a single chosen job together with its dependents, and reuses the results and outputs of the
       other jobs from the earlier attempt. Deployment protection rules that passed before pass again ("Re-running
       workflows and jobs").
     - So re-running only `deploy` of an older run skips the guard entirely.
     - The design says "its job deploys only when …", but §18 names only "no `sha` input" and the header rule as the
       template change, and nothing moves the check.
  2. **The code that runs the check matters.**
     - Inside the deploy job, the check must come from the default branch, checked out before the deployed commit.
     - A re-run uses the original run's commit and workflow file (same `GITHUB_SHA`, "Re-running workflows and
       jobs"). A check run from the checked-out commit is that older commit's code, which may predate the check.
  3. **Runs made under the old template.**
     - Runs can be re-run for 30 days after the initial run, with the original commit, and so with the old workflow
       file: the `sha` input, and the guard that accepts any ancestor.
     - For 30 days after rollout, a worker with "Actions: write" can re-run an old dispatched deploy and deploy that
       older trunk commit with the production role.
- **Material-because:** §15.1 rule 5 and §12.3 item 3, the protected tier's production guard (aQ1's second path, an
  older trunk commit, by another route).
- **Evidence:**
  - `github-deploy.yml.template`: jobs `guard` and `deploy`, the guard step's comment;
  - `merge_steward.py` `deploy_guard` (its docstring: it runs the default branch's copy);
  - design.md H15, §15.1, §18;
  - GitHub Docs, "Re-running workflows and jobs": the same commit and ref, other jobs' results reused, the 30-day
    window.
- **Proposed edit (recommended first):**
  1. **State where the check runs, and close the transition window.**
     - H15 and §18 say that the tip check is the deploy job's first step, run from a checkout of the default branch
       (the steward's copy), before the job checks out the commit and before any step that uses the role.
     - The rollout gives the production environment a new name, and the role's trust names only the new
       environment's subject, so runs of the old workflow file cannot assume the role.
  2. Keep the `guard` job, and add the same check, from the default branch, as the deploy job's first step. The
     rollout step of option 1 is still needed.

### R3 (C): three ways a job other than the deploy job still gets the production role or the steward's key on the protected tier

- **Location:** §15.1 rule 5 (the trust policy); §3.5 Protected row (the environment check); R96.
- **Defect:**
  1. **The trust's ref subject.**
     - §15.1 rule 5: the trust "names only the trunk's OIDC subject (…), or on the protected tier the subject of a
       production environment". It does not say that the protected tier drops the ref subject.
     - Every trunk job that names no environment carries `repo:<owner>/<repo>:ref:refs/heads/<trunk>` (GitHub Docs,
       "OpenID Connect reference"). If the trust keeps that subject, any trunk workflow that requests `id-token: write`
       can assume the role: one a worker dispatches on trunk, or a re-run of an older trunk run. The check that only
       the deploy workflow names the production environment then confines nothing.
  2. **Expression-valued environment names.**
     - A common pattern is a "deploy to an environment" workflow with `environment: ${{ inputs.environment }}`. A
       worker dispatches it with `production`, or with the steward's environment.
     - A static check of names sees only the expression.
  3. **Reusable workflows.**
     - A job that calls a reusable workflow (`jobs.<id>.uses`, local or in another repository) runs that workflow's
       jobs in the caller repository's context, including the environment it names.
     - A check of trunk's own workflow files does not see an environment named in another repository's file.
- **Proposed edit:**
  - §15.1 rule 5: "on the protected tier the trust names ONLY the production environment's subject, never the ref
    subject".
  - §3.5: the steward's check treats an expression-valued `environment` as naming every environment, and treats a
    call to a reusable workflow outside the repository as naming one, unless the setup record lists it as reviewed.

### R4 (C): a landing whose push run never appears has no pinned run, and nothing handles it

- **Location:** §4.2 (the pinned run is "the trunk `push` run that the steward's landing push started"); §10.4 step 3.
- **Defect:**
  - Before revision 6, the steward's dispatch returned a run id, or an error it could see.
  - Now the landing's deploy depends on a push event starting a run, and nothing in §4.2 covers a run that does not
    appear. Two concrete causes:
    - **A worker disables the deploy workflow.** "Actions: write" covers `PUT …/actions/workflows/{id}/disable`
      (`actions/disable-workflow`, `docs/api-reference/github/rest/actions.md`). After that, no landing deploys,
      silently.
    - **GitHub does not start the run** for the push.
  - Either way the landing's issues stay in TEST-READY with no red, no `skipped`, and no `env-incident`.
- **Proposed edit:**
  - When no push run for D exists after a grace period (the steward already has `dispatch_grace_minutes`), the
    steward dispatches a re-verify deploy of the tip.
  - A disabled deploy or steward workflow is an `env-incident`.
  - §12.6 lists disabling and enabling workflows with dispatching, re-running and cancelling them.

### R5 (C): other workflows with a trunk `push` or `workflow_run` trigger now start on every landing

- **Location:** §3.5 "A deploy-key push starts `push` workflows"; §18 Setup row ("CI `push` triggers that exclude
  `steward/train-*`").
- **Defect:**
  - Under a `GITHUB_TOKEN` push, no workflow ran on a steward landing. The template header says that a deploy chain
    admitted only by `workflow_run` of the CI or by a trunk `push` "never fires again", and setup prompt Part 7.1
    item 4 had projects adapt their chains to the dispatch.
  - Under H14 every workflow whose `push` trigger matches trunk now starts on each landing: a release or publish
    workflow, a docs deploy, a code scan.
  - So does every `workflow_run` chain on a CI that runs on trunk pushes, which can be a second deploy chain beside the
    template's push trigger.
  - Setup checks only the CI's train refs.
- **Proposed edit:** setup and update list every workflow whose `push` or `workflow_run` trigger matches trunk or
  `steward/train-*`, and the operator confirms each as intended. §3.5 says that a deploy-key landing starts them all.

### R6 (D): the first-attempt rule names only GitHub's endpoint

- §4.2 and H13 give `/attempts/1/jobs`. On GitLab, `GET /projects/:id/pipelines/:pipeline_id/jobs` returns only each
  job's latest attempt unless `include_retried=true` (`docs/api-reference/gitlab/rest/verify.md`, "List all jobs by
  pipeline").
- State the GitLab form: list with `include_retried=true` and take each job's earliest attempt.

### R7 (D): on issue N, "any form line" also admits a line that names another issue

- §8.3: "on issue N any form line, on the guidance issue a line that names `#N` first".
- A line `/answer #15 Q-3 = 1` posted on issue N is a form line on N. Applied to N, it answers N's `Q-3` with what the
  human wrote for #15.
- Restate: "on issue N a form line that names no issue, or names `#N`".
