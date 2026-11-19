# Adversarial review of the factory state-model design, revision 13 (2026-11-20)

**Verdict on the 1 open round-12 item (review-response.md Part 0):** 1 verified, 0 partly, 0 not-fixed, 0 disputed.

**New findings on revision 13's change:** none (A 0, B 0, C 0, D 0).

OPEN ITEMS: 0

(Open = every round-12 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 13 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`ecdeb68`. Read:

- the diff of `design.md` and `decisions.md` against `8dee636`, which is revision 12 plus its review reports;
- `review-response.md` Part 0.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Platform facts:** `docs/api-reference/gitlab/rest/verify.md`, "List all pipelines triggered by a pipeline
schedule".

**Ids.** The round-12 finding is cited as `aX1`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

---

## Summary

Revision 13 makes one design change. The bound sub-bullet in §3.5 now names GitLab's listing for rebuilding the gap
history after a restart (`GET /projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines`), next to GitHub's
`event=schedule` listing; decisions.md R118 records it.

The endpoint lists only the pipelines that the schedule triggered, and it takes `created_after`. So a rebuild over the
last 14 days is one paged listing on GitLab too, as on GitHub. Nothing else in the design changed, and the change opens
no neighbouring path.

---

## 1. Verdict on the round-12 item

| Id | Verdict | Where revision 13 fixes it | Note |
|---|---|---|---|
| aX1 | verified | §3.5, the bound sub-bullet: "GitLab: `GET /projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines`"; R118 | the endpoint filters by `created_after`, so the 14-day rebuild needs no further parameter |

---

## 2. New findings

None.
