# Adversarial review of the factory state-model design, revision 8 (2026-11-19)

**Verdicts on the 4 open round-7 items (review-response.md Part 0):** 4 verified, 0 partly, 0 not-fixed, 0 disputed.

**New findings on revision 8's changes (T1, T2):** A 0, B 0, C 1 (T1), D 1 (T2).

OPEN ITEMS: 2

(Open = every round-7 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 8 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`66c8a50`. Read:

- the full diff of `design.md` and `decisions.md` against revision 7 (`b236e58`);
- `review-response.md` Part 0;
- §4.5 (the Steward and Watcher rows) and §12.5, for who writes `delivery-status`.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Code read to check the design's claims:** `src/payload/scripts/merge_steward.py`:

- `verdict`, which writes the status record;
- `_status_issue`;
- `_write_status`, which writes only when the body changes.

**Platform facts** come from `docs/api-reference/`, named where used.

**Ids.** Round-7 findings are cited as `aS<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

---

## Summary

Revision 8 applies all four round-7 edits:

- the detected tier's deploy job names no environment, and its trust names only the ref subject;
- the rollout replaces the production environment rather than renaming it;
- the environment check runs at setup;
- the dispatcher watches the steward.

One new mechanism has a gap, and one has a wording problem:

- **The steward's "last tick" is not recorded (C).** The dispatcher reads the time of the `delivery-status` record.
  That record is written by the deploy's verdict job, only after a deploy and only when its body changes. In any
  period without deploys, the check reports a dead steward (T1).
- **Secrets cannot be copied (D).** The rollout "copies the old one's … secrets", but GitHub's API never returns a
  secret's value (T2).

### Answers to what revision 8 changed

| Change | Answer |
|---|---|
| §3.5: the steward checks the deploy workflow; the dispatcher checks the steward's last tick | the deploy-workflow check holds. The last-tick check reads a time nothing writes per tick (T1) |
| §3.5: the environment check also runs at setup | holds |
| §15.1 rule 5: no environment on the detected tier's deploy job | holds, and the reason is stated (a job that names an environment carries the environment subject) |
| H15: the rollout replaces the production environment | holds for the trust. Copying secrets (T2) |
| §15.2 item 5: the detected tier's 30-day re-run window | holds |
| §18 | consistent with the above |

---

## 1. Verdicts on the round-7 items

| Id | Verdict | Where revision 8 fixes it | Note |
|---|---|---|---|
| aS1 | verified | §3.5: the steward checks every tick that the deploy workflow is enabled; the dispatcher checks the steward's last tick; until the dispatcher runs, `enqueue` reports a refused tick dispatch; §18 | what "last tick" reads: T1 |
| aS2 | verified | §15.1 rule 5: on the detected tier the deploy job names no environment, the role trusts only the ref subject, and setup refuses an environment subject; §18 | — |
| aS3 | verified | H15: the rollout creates a new environment with the old one's policy, points the trust at it, deletes the old one, and states that only the protected tier gains; §15.2 item 5: the detected tier's 30-day window | copying secrets: T2 |
| aS4 | verified | §3.5 and §18: setup and update run the environment-name check and list each hit first | — |

---

## 2. New findings

### T1 (C): the dispatcher's check reads a "last tick" that the steward does not record

- **Location:** §3.5, the bullet on disabled workflows ("the steward's last tick, the time of its `delivery-status`
  record, is within three schedule intervals"); §18 Delivery row.
- **Defect:**
  - **The steward does not write that record.**
    - §4.5 lists `delivery-status` among the Watcher's writes, the deploy pipeline's verdict job, not the Steward's.
    - In today's code the record is written only by `verdict`, through `_write_status`, and only when the body
      changes (`if body.strip() != (issue.body or "").strip()`). A tick writes nothing to it.
  - **So a quiet period looks like a dead steward.** In any period without deploys (no landings, a quiet weekend),
    the record's time is older than three schedule intervals while the steward is healthy. The dispatcher then opens
    an `env-incident` that blames a disabled workflow or failing ticks. The same happens again after each close, until
    the next deploy.
  - **A standing false alarm hides the real one.** The operator "rarely returns to sessions" (§11), and an incident
    that is always open trains the owner to ignore it.
- **Proposed edit (recommended first):**
  1. **Make the steward record its tick.**
     - Every tick writes its time into a line of its own in the status record, for example
       `merge-steward: tick <iso time> <run id>`.
     - The dispatcher compares that line, not the issue's `updated_at`, which any comment or label changes.
     - §4.5 adds the tick line to the Steward row.
     - The write uses the steward's `GITHUB_TOKEN`, so it costs none of the operator's write budget (§15.2).
  2. Have the dispatcher read the steward workflow's latest run from the run API instead
     (`GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs`). That needs "Actions: read" on the dispatcher's
     token, one more permission than §15.2 lists.

### T2 (D): environment secrets cannot be copied

- **Location:** H15 rollout bullet ("creates a new production environment with the old one's deployment-branch policy,
  secrets and variables"); decisions.md R111.
- **Defect:**
  - The secrets API returns a secret's name and dates, never its value: `actions/list-environment-secrets` and
    `actions/get-environment-secret` (`docs/api-reference/github/rest/actions.md`).
  - The policy and the variables can be copied. Each secret must be written again from its source, which is the
    operator's step at rollout.
- **Proposed edit:** "copies the old one's deployment-branch policy and variables, and the operator re-enters each
  secret from its source (the API returns no secret values)".
