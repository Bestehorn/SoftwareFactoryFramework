# Adversarial review of the factory state-model design, revision 10 (2026-11-19)

**Verdicts on the 3 open round-9 items (review-response.md Part 0):** 3 verified, 0 partly, 0 not-fixed, 0 disputed.

**New findings on revision 10's changes (V1, V2):** A 0, B 0, C 1 (V1), D 1 (V2).

OPEN ITEMS: 2

(Open = every round-9 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 10 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`88bce8a`. Read:

- the full diff of `design.md` and `decisions.md` against revision 9 (`775d436`);
- `review-response.md` Part 0.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Platform facts:** GitLab Docs, "Scheduled pipelines". It confirms the design's new statement that a schedule turns
inactive when its owner is blocked or removed from the project.

**Ids.** Round-9 findings are cited as `aU<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

**A disclosure.** Both new findings are about wording that revision 10 took from my own round-9 proposals:

- V1: the bound as "the longest gap" in the run history;
- V2: "cancelled does not count".

---

## Summary

Revision 10 applies all three round-9 edits to the liveness bullet of §3.5:

- the failing-ticks rule;
- GitLab's pipeline schedule;
- the measured bound, with two consecutive polls.

It also carries the GitLab read scope into §4.5, §14 and §15.2. All three items hold.

What is left concerns the bound and one phrase:

- **The bound has no value at first setup, and an old outage inflates it (C).** The longest gap in the history
  includes the steward's own earlier outages. One two-day outage makes every later outage shorter than two days
  invisible until the next update (V1).
- **"Does not count" has two readings (D)** (V2).

### Answers to what revision 10 changed

| Change | Answer |
|---|---|
| §3.5: failing ticks | holds. Wording: V2 |
| §3.5: GitLab's pipeline schedule | holds. The owner statement is confirmed by GitLab Docs |
| §3.5: the measured bound and two consecutive polls | the two polls hold. The bound: V1 |
| §4.5, §14, §15.2, §18 | consistent |

---

## 1. Verdicts on the round-9 items

| Id | Verdict | Where revision 10 fixes it | Note |
|---|---|---|---|
| aU1 | verified | §3.5: of the last three completed runs, not all `failure` or `timed_out`; superseded `cancelled` ticks do not count; GitLab: the last three finished pipelines | V2 |
| aU2 | verified | §3.5: GitLab `GET /projects/:id/pipeline_schedules/:pipeline_schedule_id`; a read scope in §4.5, §14 and §15.2 | — |
| aU3 | verified | §3.5: the bound from the steward's own run history, recorded by setup and refreshed by update; two consecutive polls | V1 |

---

## 2. New findings

### V1 (C): the bound is undefined at first setup, and the steward's own outages inflate it

- **Location:** §3.5, liveness bullet ("the bound is the longest gap between scheduled runs in the steward's own run
  history, recorded by setup and refreshed by update").
- **Defect:**
  1. **First setup has no history.** At the first setup the steward workflow has not run yet, so the bound has no
     value. Read as zero, it opens an incident on the second poll. Read as unbounded, it detects nothing.
  2. **The longest gap includes outages.** The history the bound comes from includes the steward's own outages, the
     events the check exists to find. One two-day outage, for example a disabled workflow found late, sets the bound to
     two days. Every later outage shorter than that then goes unreported until an update refreshes the bound, and
     updates follow framework releases, not the steward's health.
- **Proposed edit:**
  - The bound is a high percentile of the gaps, for example the 99th, of scheduled runs over the last 14 days, capped
    at a fixed ceiling (for example 4 × the schedule interval). Gaps that fall inside an `env-incident` of this check
    are left out.
  - Until 14 days of history exist, the bound is the ceiling.
  - The dispatcher recomputes the bound on its own poll, from the same run listing it already reads, so it needs no
    update to refresh.

### V2 (D): "does not count" has two readings

- **Location:** §3.5, liveness bullet ("of its last three completed runs, not all concluded `failure` or `timed_out`
  (a superseded tick concludes `cancelled` and does not count)").
- **Defect:**
  - **Reading 1:** a `cancelled` run is one of the three and is not a failure. One cancelled run among the three then
    passes the check. Busy periods supersede ticks often, so a steward that fails every tick passes the check exactly
    when ticks are frequent.
  - **Reading 2:** the intended one, where cancelled runs are skipped.
- **Proposed edit:** "of its last three completed runs that did not conclude `cancelled`, not all concluded `failure`
  or `timed_out`" (GitLab: `canceled` and `skipped` are skipped the same way).
