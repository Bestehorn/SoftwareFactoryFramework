# Adversarial review of the factory state-model design, revision 12 (2026-11-20)

**Verdict on the 1 open round-11 item (review-response.md Part 0):** 1 verified, 0 partly, 0 not-fixed, 0 disputed.

**New findings on revision 12's change (X1):** A 0, B 0, C 0, D 1 (X1).

OPEN ITEMS: 1

(Open = every round-11 item not verified, plus every new finding of any grade.)

---

## Scope

**Subject.** Revision 12 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`50cec91`. Read:

- the full diff of `design.md` and `decisions.md` against revision 11 (`b440fb7`);
- `review-response.md` Part 0.

The review ran in a session independent of the designer's, from a detached worktree, read-only.

**Platform facts** come from `docs/api-reference/`, named where used.

**Ids.** The round-11 finding is cited as `aW1`, the designer's naming in Part 0.

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account.
- **O16:** open, and the operator's to decide.

---

## Summary

Revision 12 applies aW1 as proposed. The dispatcher keeps a cached gap history of the scheduled runs it has seen, and
after a restart rebuilds it from one paged listing of 14 days filtered to `event=schedule`. It recomputes the bound
when a new scheduled run appears, so each poll costs one short request.

That holds, and it fits P1: the cache can be rebuilt from the forge, so it is never the source of truth.

The one item left is a wording gap the change introduced. The rebuild listing is given only in GitHub's form, inside a
bullet that both forges share (X1). It is a D and does not affect the design's behaviour on GitHub.

### Answers to what revision 12 changed

| Change | Answer |
|---|---|
| §3.5: the cached gap history, its rebuild, and the recompute on a new scheduled run | holds on GitHub. The GitLab form of the rebuild is missing (X1) |
| §18 Delivery row | consistent |

---

## 1. Verdict on the round-11 item

| Id | Verdict | Where revision 12 fixes it | Note |
|---|---|---|---|
| aW1 | verified | §3.5: the cache of scheduled-run gaps, rebuilt after a restart from `GET …/actions/workflows/{id}/runs?event=schedule` with `created` over 14 days, the bound recomputed when a new scheduled run appears, one short request per poll; §18; R117 | X1 |

---

## 2. New findings

### X1 (D): the rebuild listing is given only for GitHub

- **Location:** §3.5, liveness bullet, the bound sub-bullet ("a cache rebuilt after a restart from one listing
  (`GET …/actions/workflows/{id}/runs?event=schedule` …)").
- **Defect:**
  - The bound sub-bullet applies to both forges, but it names only GitHub's listing.
  - On GitLab the scheduled pipelines come from
    `GET /projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines`
    (`docs/api-reference/gitlab/rest/verify.md`, "List all pipelines triggered by a pipeline schedule").
- **Proposed edit:** add "(GitLab: `GET /projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines`)" after the
  GitHub listing.
