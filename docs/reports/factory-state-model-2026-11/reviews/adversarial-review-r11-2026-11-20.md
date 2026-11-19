# Adversarial review of the factory state-model design, revision 11 (2026-11-20)

**Verdicts on the 2 open round-10 items (review-response.md Part 0):** 2 verified, 0 partly, 0 not-fixed,
0 disputed.

**New findings on revision 11's changes (W1):** A 0, B 0, C 0, D 1 (W1).

OPEN ITEMS: 1

(Open = every round-10 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 11 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`b440fb7`. Read:

- the full diff of `design.md` and `decisions.md` against revision 10 (`88bce8a`);
- `review-response.md` Part 0;
- the steward template's `schedule` trigger, to size the run history.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Platform facts** come from `docs/api-reference/github/`: the run-listing parameters, and the rate-limit table in
`conventions.md`.

**Ids.** Round-10 findings are cited as `aV<n>`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

---

## Summary

Revision 11 applies both round-10 edits to the §3.5 liveness bullet:

- **the bound** is the 99th percentile of scheduled-run gaps over 14 days, without the check's own incidents, and
  capped at 4 × the interval;
- **before 14 days** of history exist, the cap applies;
- **every poll** recomputes the bound;
- **cancelled runs** are skipped, not counted.

Both hold. Sizing the bound against the steward's schedule (`7,37 * * * *`, every 30 minutes) gives a cap of two
hours. With two consecutive polls, a false incident needs a scheduled-run gap of more than two hours, which at that
schedule means four or more consecutive drops, or delays of the same length. One wording item
remains: the bound does not come "from the run listing it already reads", and recomputing it on every poll has a
cost under the shared account (W1).

### Answers to what revision 11 changed

| Change | Answer |
|---|---|
| §3.5: the bound (percentile, 14 days, cap, recomputed every poll) | holds. Where its data comes from, and how often it is recomputed: W1 |
| §3.5: cancelled runs skipped (GitLab `canceled`, `skipped`) | holds; one reading only |
| §18 Delivery row | consistent |

---

## 1. Verdicts on the round-10 items

| Id | Verdict | Where revision 11 fixes it | Note |
|---|---|---|---|
| aV1 | verified | §3.5: the 99th percentile of scheduled-run gaps over 14 days, leaving out gaps inside this check's incidents, capped at 4 × the interval, the cap until 14 days exist, recomputed on every poll; §18; R116 | W1 |
| aV2 | verified | §3.5: "of its last three completed runs that did not conclude `cancelled`"; GitLab skips `canceled` and `skipped`; R116 | — |

---

## 2. New findings

### W1 (D): the bound needs its own run listing, and recomputing it every poll draws on the shared account's limit

- **Location:** §3.5, liveness bullet ("The dispatcher recomputes it on every poll from the run listing it already
  reads").
- **Defect:**
  - **It is a different listing.** The liveness check reads the latest run and the last three completed runs, which
    is one short listing of runs of any event. The bound needs the scheduled runs of the last 14 days:
    `GET /repos/{owner}/{repo}/actions/workflows/{id}/runs` with `event=schedule` and `created` set to the last 14
    days (`docs/api-reference/github/rest/actions.md`, `actions/list-workflow-runs`).
  - **It is about seven requests.** At the steward's schedule of every 30 minutes, 14 days are about 672 scheduled
    runs, or seven pages of 100.
  - **The requests share the operator's limit.** Under U24 the dispatcher's token is one of the operator's tokens.
    A user's requests share 5,000 per hour "across all of that user's tokens and apps"
    (`docs/api-reference/github/conventions.md`, rate-limit table). That limit is shared with every worker.
  - **At an assumed one-minute poll** (no rate is set; O12), that is about 420 extra requests an hour, for a figure
    that changes slowly.
- **Proposed edit:** "The dispatcher keeps the gap history from the scheduled runs it has seen (a cache, rebuilt from
  `GET …/runs?event=schedule&created=>=<14 days ago>` after a restart) and recomputes the bound when a new scheduled run
  appears". The behaviour is the same, with one short request per poll.
