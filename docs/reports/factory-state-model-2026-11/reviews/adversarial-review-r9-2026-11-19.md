# Adversarial review of the factory state-model design, revision 9 (2026-11-19)

**Verdicts on the 2 open round-8 items (review-response.md Part 0):** 2 verified, 0 partly, 0 not-fixed, 0 disputed.

**New findings on revision 9's changes (U1–U3):** A 0, B 0, C 1 (U1), D 2 (U2, U3).

OPEN ITEMS: 3

(Open = every round-8 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 9 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`775d436`. Read:

- the full diff of `design.md` and `decisions.md` against revision 8 (`66c8a50`);
- `review-response.md` Part 0;
- the header of `templates/ci/github-merge-steward.yml.template`, which records measured schedule drops.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Platform facts** come from `docs/api-reference/`, named where used.

**Ids.** Round-8 findings are cited as `aT<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

---

## Summary

Revision 9 applies both round-8 items.

- The dispatcher now reads the steward's liveness from the run API with "Actions: read". It checks that the workflow
  is `active` and that its latest run started within three schedule intervals. The status record keeps one writer.
- The rollout has the operator re-enter each secret.

Both hold. The liveness check now covers a disabled steward and a missing one. Three neighbours are left:

- **A failing steward (C).** It passes the check, because its runs still start. Revision 8 named "ticks failing" as a
  cause; revision 9 dropped it (U1).
- **GitLab (D).** The check is stated for GitHub only (U2).
- **The fixed bound (D).** The schedule the check relies on drops runs, by the steward template's own measurement, so
  a fixed bound of three intervals will raise false incidents (U3).

### Answers to what revision 9 changed

| Change | Answer |
|---|---|
| §3.5: the dispatcher's liveness check through the run API | holds for a disabled workflow (by hand, or by GitHub for inactivity) and for a workflow that stopped running. Misses a workflow whose every run fails (U1). GitLab (U2). The bound (U3) |
| §4.5, §14, §15.2: "Actions: read" on the dispatcher's token | consistent across the three places, and it is a read permission only |
| §18 Delivery row | consistent |
| H15: secrets re-entered by the operator | holds |

---

## 1. Verdicts on the round-8 items

| Id | Verdict | Where revision 9 fixes it | Note |
|---|---|---|---|
| aT1 | verified | §3.5: the workflow's `state` and its latest run, from the run API, with "Actions: read"; the status record is not used, and it stays the watcher's; §4.5 Dispatcher row; §14; §15.2; §18; R113 | U1, U2, U3 |
| aT2 | verified | H15: the policy and variables are copied, and the operator re-enters each secret; R114 | — |

---

## 2. New findings

### U1 (C): a steward whose every tick fails passes the liveness check

- **Location:** §3.5, the bullet on disabled workflows ("the workflow's `state` is `active`, and its latest run started
  within three schedule intervals").
- **Defect:**
  - **The check looks at starts only.** It tests whether the steward's runs start, not whether they succeed.
  - **A crashing steward still starts.** A steward that fails on every tick keeps starting on schedule. For example:
    - an exception left by a landed change to `merge_steward.py` (privileged automation that workers may change, §19
      item 14);
    - a lapsed credential that the tick needs before H14's classification is reached.
  - **Nothing reports it.**
    - The steward cannot report its own crash when it fails before it reaches that code.
    - The dispatcher sees an `active` workflow with a recent run, and opens nothing.
    - Nothing lands, and TEST-READY issues wait with no visible cause. That is the gap aS1 exists to close.
  - **Revision 8 covered it; revision 9 does not.** Revision 8's incident named "ticks failing" as one cause.
    Revision 9's names only "the workflow disabled" and "no recent run".
- **Proposed edit:**
  - The same run API call returns each run's `conclusion` (`GET /repos/{owner}/{repo}/actions/workflows/{id}/runs`).
  - The dispatcher also opens the `env-incident` when the last three completed runs did not conclude `success`. A
    superseded tick concludes `cancelled`, so count only `failure` and `timed_out`.
  - The incident names the latest failed run.

### U2 (D): the liveness check is stated for GitHub only

- **Location:** §3.5, the bullet on disabled workflows; §4.5 Dispatcher row ("actions read").
- **Defect:**
  - On GitLab the steward ticks from a pipeline schedule. That schedule can be set inactive through
    `PUT /projects/:id/pipeline_schedules/:pipeline_schedule_id`.
  - Its state and last pipeline come from `GET /projects/:id/pipeline_schedules/:pipeline_schedule_id`
    (`docs/api-reference/gitlab/rest/verify.md`, "Retrieve a pipeline schedule").
  - The design names neither the endpoint nor the dispatcher token's scope for it.
- **Proposed edit:** "GitLab: the steward's pipeline schedule is active and its last pipeline started within three
  intervals (`GET /projects/:id/pipeline_schedules/:id`, with a read scope on the dispatcher's token)".

### U3 (D): a fixed bound of three intervals meets the schedule's measured drops

- **Location:** §3.5 ("its latest run started within three schedule intervals"; "The schedule runs whether or not
  anything lands, so a quiet period passes").
- **Defect:**
  - In a quiet period the schedule is the only source of runs.
  - The steward template's header records that "GitHub delays and drops scheduled runs (8 of about 86 in 43 hours,
    same project)". Its source names delays as well as drops, so gaps longer than one interval are routine.
  - With no further rule, a run of delays or drops opens a false `env-incident`, and incidents need the owner.
- **Proposed edit:**
  - Open the incident only when two consecutive dispatcher polls see the gap.
  - Take the bound from the longest gap measured in the steward's own run history (setup records it, and update
    refreshes it) rather than a fixed three intervals.
