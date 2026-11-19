# Adversarial review of the factory state-model design, revision 7 (2026-11-19)

**Verdicts on the 7 open round-6 items (review-response.md Part 0):** 7 verified, 0 partly, 0 not-fixed,
0 disputed.

**New findings on revision 7's changes (S1–S4):** A 0, B 0, C 2 (S1, S2), D 2 (S3, S4).

OPEN ITEMS: 4

(Open = every round-6 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 7 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`b236e58`. Read:

- the full diff of `design.md` and `decisions.md` against revision 6 (`8df28db`);
- `review-response.md` Part 0.

The review ran in a session independent of the designer's, from a detached worktree, read-only. `traceability.md`
was not reviewed.

**Code read to check the design's claims:** `templates/ci/github-deploy.yml.template`, in which the `deploy` job names
`environment: {{ENVIRONMENT}}`.

**Platform facts** come from GitHub Docs, each named where it is used.

**Ids.** Round-6 findings are cited as `aR<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide. It now lists a plan with the protected tier as an option, and it is
  stated truthfully.

---

## Summary

Revision 7 applies all seven round-6 edits as proposed:

- the re-verify dispatch fires only when nothing newer covers a cancelled pin, and supersession is the normal case
  again;
- the tip check is the deploy job's first step, run from the default branch, so a single-job re-run cannot skip it;
- the protected tier's deploy role trusts only the environment subject.

What is left are two clarifications that matter (C) and two wording items (D):

- the steward cannot notice that its own workflow is disabled (S1);
- the detected tier's trust names the ref subject, but the deploy job names an environment, and the design does not
  say which subject that job carries there (S2);
- GitHub has no environment rename (S3);
- setup should run the environment check before the first tick (S4).

### Answers to "what the next review should check (revision 7)"

| Item | Answer |
|---|---|
| the round-6 items | all 7 verified (§1) |
| the re-verify rule (§4.2) | holds. Supersession no longer causes dispatches, a deletion or a worker's cancel with nothing behind it does, and so does a missing push run |
| the first-step tip check and the rollout rename (H15, §18) | the check holds. The rename needs wording (S3), and it acts only on the protected tier (S3) |
| the environment-subject-only trust (§15.1 rule 5) | holds on the protected tier. On the detected tier, which subject the deploy job carries is unstated (S2) |
| the conservative environment-name checks (§3.5) | hold. Ordering at setup (S4) |
| the disabled-workflow check (§3.5) | holds for the deploy workflow. The steward cannot check its own workflow (S1) |
| the setup record of workflows a landing starts | holds |
| GitLab's `include_retried=true`; the form-line binding (§8.3) | hold |

---

## 1. Verdicts on the round-6 items

| Id | Verdict | Where revision 7 fixes it | Note |
|---|---|---|---|
| aR1 | verified | §4.2: a new deploy of the tip only when no other pinned run whose commit contains D is pending, running or done | — |
| aR2 | verified | H15: the check is the deploy job's first step, from a checkout of the default branch, before the deploy commit is checked out and before any step that uses the role; the rollout renames the production environment; §18 Setup row | S3 |
| aR3 | verified | §15.1 rule 5: on the protected tier, only the environment subject, never the ref subject; §3.5: expression-valued names count as every environment, and outside reusable workflows as naming one unless reviewed | detected tier: S2; setup order: S4 |
| aR4 | verified | §4.2: a re-verify deploy when a landing's push run has not appeared within the grace period; §3.5: a disabled deploy or steward workflow is an `env-incident`; §12.6 | S1 |
| aR5 | verified | §3.5 and §18: every workflow a landing starts is listed in the setup record, for the operator to confirm | — |
| aR6 | verified | §4.2 and H13: GitLab lists jobs with `include_retried=true` and takes each job's earliest attempt | — |
| aR7 | verified | §8.3: on issue N, a form line that names no issue or names `#N` | — |

---

## 2. New findings

### S1 (C): the steward cannot notice that its own workflow is disabled

- **Location:** §3.5 "A disabled deploy or steward workflow is an `env-incident`, which the steward checks every tick";
  §18 Delivery row ("the per-tick check that the deploy and steward workflows are enabled").
- **Defect:**
  - A disabled workflow is not triggered (GitHub Docs, "Disabling and enabling a workflow"). So a disabled steward
    workflow has no tick in which to check itself.
  - "Actions: write" lets a worker disable it (§12.6). From then on, nothing lands, nothing returns, and no
    `env-incident` opens.
  - TEST-READY issues wait with no visible cause. The only remaining signal is that `enqueue`'s tick dispatch is
    refused, and the design does not say that anyone reads that refusal.
- **Proposed edit:**
  - The dispatcher (§14), which runs on its own host, checks every poll that the steward workflow is enabled and that
    its last tick is recent (the `delivery-status` record's time, within a bound such as three schedule intervals).
    Otherwise it opens the `env-incident`.
  - `enqueue` reports a refused tick dispatch as that incident's cause.
  - §3.5 says that the steward checks the deploy workflow, and the dispatcher checks the steward's.

### S2 (C): on the detected tier the trust names the ref subject, but the deploy job names an environment

- **Location:** §15.1 rule 5 ("On the detected tier, which has no environments, it names the trunk's ref subject");
  `templates/ci/github-deploy.yml.template` job `deploy` (`environment: {{ENVIRONMENT}}`).
- **Defect:**
  - **Which subject?** GitHub's OIDC reference gives the subject `repo:<owner>/<repo>:environment:<name>` whenever
    the job references an environment, and the ref subject only when it does not. The template's deploy job
    references one. The design does not say that the detected tier's deploy job drops `environment:`, and does not
    say which subject such a job carries on a private Free repository.
    - If it carries the environment subject, the detected tier's ref-subject trust refuses the deploy's own token.
    - The obvious repair would then be to trust the environment subject on the detected tier as well. There that hands
      the role to any branch workflow that names the environment: deployment branches and protection rules are not
      available on Free private repositories, and "Anyone that can edit workflows in the repository can create
      environments via a workflow file" (GitHub Docs, "Managing environments for deployment").
  - **What the detected tier protects.** The detected tier is unguarded by design, but only against trunk pushes
    (§15.2 item 5). The ref-subject trust is what keeps a branch workflow that has not landed away from the role. That
    is the part §15.1 rule 5 says holds "on either tier".
- **Proposed edit:**
  - §15.1 rule 5 and §18: on the detected tier the deploy job names no environment, and the role trusts only the ref
    subject.
  - Setup refuses a trust that names an environment subject on that tier.

### S3 (D): GitHub has no environment rename, and the rename helps only on the protected tier

- **Location:** H15 rollout bullet; §18 Setup row ("a renamed production environment").
- **Defect:**
  - **There is no rename.** "Renaming" means creating a new environment, with its deployment-branch policy, secrets
    and variables, and deleting the old one.
    - Until the old one is deleted, a default-branch job that names it still reads its secrets.
    - The per-tick check of §3.5 watches only the new name.
  - **Only the protected tier gains.** On the detected tier, which has no environments, old-file runs remain
    re-runnable for 30 days under the ref-subject trust. H15's "no run of the old file can assume it" holds on the
    protected tier only.
- **Proposed edit:** "the rollout creates a new production environment with the old one's policy, secrets and
  variables, points the trust at it, and deletes the old one; on the protected tier no run of the old file can then
  assume the role".

### S4 (D): setup should run the environment check before the first tick

- **Location:** §3.5 (the conservative check; "a hit on trunk is an `env-incident`"); §18 Setup row.
- **Defect:**
  - A project that already has a workflow with an expression-valued `environment` (a common "deploy to
    `${{ inputs.environment }}`" pattern) or an outside reusable workflow meets the check for the first time as an
    `env-incident` on the steward's first tick.
  - Setup is where the operator can restructure that workflow, or list it as reviewed.
- **Proposed edit:** setup and update run the same check and list each hit, so the operator restructures the workflow
  or records it as reviewed before factory mode starts.
