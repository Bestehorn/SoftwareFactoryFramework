# Factory state model: design (revision 11, 2026-11-19)

Status: design only. Nothing described here is implemented unless §2 says it exists today.

History:

- **Revision 1** (11073fe) was reviewed twice (76 findings).
- **Revision 2** (cec3492) answered them. Its two re-reviews verified 55 of the 76, judged 21 only partly fixed, and
  raised 30 new findings, none of grade A.
- **Revision 3** (5dcc08f) answered those. Its round-3 reviews verified every item but one (aN7, partly) and raised 19
  new findings, none of grade A.
- **Revision 4** (049a047) answered those 20. Its round-4 reviews verified all but one (aM5, partly) and raised 20 new
  findings, none of grade A.
- **Revision 5** (1fce726) answered the 21 items left open. Where a round-4 finding showed that a mechanism rested on
  a forge feature the plan does not offer, it replaced the mechanism with a simpler one and stated the residual. Its
  round-5 reviews verified all 21 and raised 15 new findings, one of grade A (aQ1).
- **Revision 6** (8df28db) answered those 15. Its round-6 reviews verified all 15 and raised 8 new findings, none of
  grade A.
- **Revision 7** (b236e58) answered those 8. Its round-7 reviews verified all 8; the alignment review raised no new
  finding, the adversarial review 4, none of grade A or B.
- **Revision 8** (66c8a50) answered those 4. Its round-8 reviews verified all 4; the alignment review again raised
  nothing, the adversarial review 2 findings (1 C, 1 D).
- **Revision 9** (775d436) answered those 2. Its round-9 reviews verified both; the alignment review raised nothing,
  the adversarial review 3 findings (1 C, 2 D) on the steward's liveness check.
- **Revision 10** (88bce8a) answered those 3. Its round-10 adversarial review verified all 3 and raised 2 wording
  findings (1 C, 1 D) on the same check.
- **Revision 11** answers those 2.

All review reports are in
[`docs/reports/factory-state-model-2026-11/reviews/`](../../reports/factory-state-model-2026-11/reviews/), and
[review-response.md](review-response.md) maps every finding to its disposition. Finding ids appear in brackets:

- [A1] and [T-05] are first-round findings;
- [aN3] and [tN3] are round-2 findings;
- [aM3] and [tM1] are round-3 findings, of the adversarial and the alignment review;
- [aP3] and [tP1] are round-4 findings;
- [aQ3] and [tQ1] are round-5 findings;
- [aR3] and [tR1] are round-6 findings;
- [aS3] is a round-7 finding;
- [aT1] is a round-8 finding;
- [aU1] is a round-9 finding;
- [aV1] is a round-10 finding.

Companion documents:

- [decisions.md](decisions.md): the decisions and their sources.
- [traceability.md](traceability.md): how the design aligns with the keynote, which is a vision and not a
  specification, and how it covers the gap analysis.
- [`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/): the research behind each
  section, cited as *(R: file)*.

Words used throughout:

- **stage**: the one state an open issue is in (§3).
- **flag**: an orthogonal marker, such as `needs-input`.
- **claim**: the server-enforced lease on an issue (§5). EVERY caller of the transition verb holds it for the length
  of its call.
- **maker / checker**: the agent that produces an artefact, and an agent or tool that judges it.
- **team**: the makers and checkers working one stage of one issue.
- **role**: what an actor may write (§4.5).
- **identity**: the forge login a write comes from.
- **reserved decision**: a decision the design leaves to an authorised human (§12.3).
- **explicit form**: a one-line command in a comment (`/answer`, `/approve`, `/amend`, `/stage`, `/admit`, `/hold`,
  `/unhold`, `/priority`, `/clear-tamper`), the only way a human changes state (§8.3).

---

## 1. Goal and principles

The goal: the operator talks to the projects only through the backlog. Every issue, once created, is picked up by
workers (Claude Code, Kiro, Kiro Crew) on any machine and moved to a verified, closed state without waiting for
anyone, with the human as the rare exception.

| # | Principle | Consequence in this design |
|---|---|---|
| P1 | The backlog is the only interface | The tracker and git hold everything another worker needs; machine-local run state is a cache, never the source of truth |
| P2 | Workers never wait | Every wait has an owner that is not a worker: a human answer (`needs-input`), the PR's own CI (`ci-pending`, picked up by the verifier lane), merge (the steward), deploy and smoke (the deploy pipeline). The worker releases and pulls other work |
| P3 | Any number of workers, any machine, any client | Exclusion comes from a server-enforced claim, a git ref compare-and-swap, held by every caller of the verb (§5) |
| P4 | Maker ≠ checker | Enforced per agent context and role (§8.1). Every stage exit §8.5 names needs at least one verdict from a separately started checker, whose bytes the maker's session does not post; the exits without one are recorded trade-offs (§8.5, §19) [aN9, aM1] |
| P5 | Every stage has a deterministically checkable finish line; the team loops until it holds | A script, the transition verb, evaluates it from tracker + git + CI state (§4) |
| P6 | The human is the last-resort conflict resolver | No human-only stage or gate. Questions only when no agent can answer them, in ONE batch, never drip-fed (§12). An optional per-project approval setting exists, off by default |
| P7 | Shared environments; batched delivery; revert first | One CI or deploy run covers many issues. A failed deploy or smoke is restored first, then attributed (§10) |
| P8 | Effort proportional to the ask | Tiers S/M/L decide artefacts, panels and budgets (`clients/claude/rules/proportionality.md`); tier S has a minimum path (§7.3) |
| P9 | Enforcement is client-neutral | The state machine lives in the wrapper scripts and CI, which Claude Code and Kiro both run, not only in one client's hooks |
| P10 | File-based distribution per project | The framework stays copied into each project by the setup and update prompts; a plugin is a future option (§16) |
| P11 | Authority is explicit | Every edge and every record type names the role that may write it (§4.5); a write by any other role is data [A1] |
| P12 | Equal scrutiny (decision U21) | Every input, from the operator, an agent or an outsider, is judged on its content. A human's act, an answer or a `/stage` request alike, passes the same predicates as an agent's. Authorship decides only who may make a reserved decision (§12.3) |
| P13 | Check-then-act is named and made safe | Where the tracker offers no conditional write, exclusion comes from the claim ref, recovery rolls forward, and the remaining windows are named (§4.4, §5, §19) |

---

## 2. Starting point: what exists, what is reused, what must change

| Capability | Today | Where | In this design |
|---|---|---|---|
| Merge queue with cumulative trains: land the longest green prefix; blame only the newest PR of the first red train; one retry for a first failure | yes | `src/payload/scripts/merge_steward.py` (docstring "ONE TICK") | reused |
| Train merges carry `Steward-PR:` and `Steward-Issues:` trailers on trunk's first-parent history | yes | `merge_steward.py` (`TRAILER_RE`, the train commit message) | the source of truth for landings, extended with `Steward-Reverts:` (§10.8 H1) |
| Post-deploy verification by git ancestry; the `delivery-status` issue | yes; the status issue is kept CLOSED and only its body is written (`_status_issue`, `_write_status`) | `merge_steward.py` `verdict`; `clients/common/docs/delivery.md` §4 (which says "open", a doc/code deviation) [D2] | reused as a machine status record only (§12.5) |
| Delivery labels `queue`, `queue-failed`, `queue-conflict`, `queue-retried`, `do-not-merge`, `awaiting-verification`, `verified`, `verification-failed`, `needs-rework`, `needs-closeout`, `reverify`, `delivery-status` | yes | `clients/common/docs/delivery.md` §6 [D1] | reused below the stage labels |
| Tiers, byte caps, review panel with caps (S one combined pass, max 2; M 4/2; L 6/3), materiality A–D | yes | `clients/claude/rules/proportionality.md`, `clients/common/docs/review-contract.md`, `clients/common/phases/spec-phase-review.md` | reused; the caps stay enforced throughout (§13) [tN4] |
| Test-first waves, red for the right reason, the adversarial verifier, evidence reports | yes | `src/hooks/red_for_right_reason.py`, `clients/common/phases/spec-phase-implement.md` | reused |
| Filing discipline, findings ledger | yes | `clients/claude/rules/issue-filing-discipline.md` | reused |
| Claim: label + assignee + re-read | yes, but unsafe across machines (§5.6) | `src/payload/scripts/github_api/commands/claim.py` | replaced by the claim ref (§5) |
| Triage, spec and questions as tracker states | **no**: they happen inside one session; the spec lives in its worktree until the PR | `clients/claude/agents/issue-work-orchestrator.md` (FIX) | new |
| Something that starts workers | **no** | — | the dispatcher (§14) |
| Revert after a failed deploy | **no** | `docs/reports/red-pipeline-analysis-2026-11-02.md` | new (§10) |

**Behaviours of today's code and templates that this design changes:**

| Today | Where | Change |
|---|---|---|
| A red verdict returns every issue landed since the last green deploy | `verify_issue`, `verdict` | the red verdict marks no issue; only Track T's culprit record returns one (H8) [B11] |
| A green verdict closes the issue when its checklist is complete | `verify_issue` (`issue_close`) | the watcher records a fact; the steward transitions to CLOSE-READY; the close-out team closes (H9) [B12, aN1] |
| Every PR of a batch is recorded with the batch tip, and `last_landing` takes the last match regardless of PR | `land()` → `after_landing`; `last_landing` | landings and reverts per PR, from first-parent trailers only (H1) [B15, aN7] |
| `merge-steward:` lines are matched from any comment author | `GitHubHost.issue()` keeps only `body` | landings come from trunk history; comments are projections (H7) [B7] |
| A PR the steward opens with `GITHUB_TOKEN` gets no PR CI, and `plan()` orders by enqueue time | `github-merge-steward.yml.template`; `eligibility`, `plan` | the steward dispatches the revert's CI and orders steward-made reverts first (H10) [B14] |
| On a new personal GitHub repository, Actions may not create PRs, so the steward cannot open a revert at all | GitHub repository settings | setup enables it, and setup and update check it with the operator's token; the steward detects a refusal at revert time (H11, §3.5) [aN8, aQ10] |
| Nothing protects GitHub trunk from a worker's token, which needs contents write. On a private repository on GitHub Free, rulesets are not enforced at all (the operator saw this on chess on 2026-10-26) | the GitHub templates (the GitLab template does protect trunk) | protection tiers by plan, with detection on every tier (H12, §3.5) [aN7, aP5] |
| `verdict` takes the deploy's conclusion as an argument | `merge_steward.py verdict --conclusion` | the steward reads the pinned deploy run from the run API (H13) [aN10] |
| `eligibility` rejects for reasons the old design had no edge for (base not trunk, draft, closing keyword, dependency closed unlanded), and a PR can be closed unmerged | `eligibility`, `reject` | each is a TEST-READY → REWORK-REQUIRED cause (§4.2) [aN3] |
| The steward's hold is `do-not-merge` on the PR; it ignores a hold on the issue | `STEWARD_DEFAULTS` `hold_label`, `eligibility` | `eligibility` also waits while an issue the PR references carries `hold` [aN11] |
| Train branches are deleted after landing | `land()` → `delete_trains` | attribution uses the first-parent merge commits on trunk (§10.4) [C3] |
| GitLab notes are listed by `created_at` | the GitLab host in `merge_steward.py` | the fold orders by note id on both forges (§8.2) [C5] |
| `release-issue` writes the whole label set minus `in-progress` | `cmd_release_issue` in `claim.py` | one release verb, additive (§5.4) |
| The wrapper posts comment and body text unchanged, and `call` does not gate comment or issue writes | `cmd_comment_issue`, `cmd_update_issue`; `GATED_OPERATIONS` in `call.py` | the wrapper marks EVERY agent comment and body write, and refuses unmarked ones from agent paths (§8.2) [aN5] |

---

## 3. The state model

### 3.1 Stages (exactly one per open factory issue)

Each stage is a **queue** named for the next kind of work the issue needs. Being worked on is the claim, not a stage.
Issues carrying `env-incident` are not factory work items and have no stage (§12.5).

| Stage | Meaning | Pulled by | Leaves to |
|---|---|---|---|
| **START** | New; no work done yet. An issue with no stage label AND no transition audit line is in START (§4.4) | triage worker | SPEC-REQUIRED; closed administratively; split into child issues |
| **SPEC-REQUIRED** | Triaged; it needs a spec and acceptance tests | spec team | IMPLEMENTATION-READY |
| **IMPLEMENTATION-READY** | A reviewed spec at a pinned commit, failing acceptance tests that define "done", no blocking question | implementation team | TEST-READY |
| **TEST-READY** | The PR is in the merge queue, then landed, then deployed and smoke-tested. Never claimed by a worker. Its exits are written by the steward alone (§4.5), from its own records and the watcher's facts | merge steward, deploy pipeline | CLOSE-READY; REWORK-REQUIRED |
| **REWORK-REQUIRED** | Returned from TEST-READY with a machine-readable cause | implementation team, pulled first | TEST-READY; IMPLEMENTATION-READY; SPEC-REQUIRED |
| **CLOSE-READY** | Every PR landed and not reverted; deploy and smoke green on a commit containing all of them | close-out team | closed (done) |

TEST-READY spans queue → merge → CI → deploy → smoke (decision U7). Its internal milestones (queued, landed,
verified) are machine lines and trunk trailers, not stages.

### 3.2 Flags (orthogonal to the stage)

| Flag | Meaning | Set by | Cleared by |
|---|---|---|---|
| `needs-input` | at least one BLOCKING question or approval is open (decision U1). The stage does not change; the claim is released | any team, after the question checker (§12.4) | the answer recorder, when an explicit `/answer` or `/approve` from an authorised human exists for every blocking question (§12.7) |
| `blocked-by #N` | cannot proceed until #N reaches a named stage or closes. Native dependency where the forge offers it free (GitHub issue dependencies); otherwise a machine line `factory: blocked-by #N until <stage>` (GitLab blocking links are Premium) [C10] | triage, spec, the steward, the watcher (§4.5) | the dispatcher, when #N gets there. A target closed administratively releases the block with a comment; a cycle is a triage error, reported on the issue |
| `hold` | the human paused it. Every actor stops at its next verb call, and the steward does not land a PR that references a held issue [aN11] | an authorised human's `/hold`, applied by the answer recorder [aM4] | an authorised human's `/unhold`, applied by the recorder |
| `claimed` | a query filter projected from the claim ref (§5); never authoritative | the claim verb | the release verb |
| `ci-pending` | the PR's own CI is running on head H; the worker has released | implementation worker | the verifier lane, when the run ends or its timeout passes (§4.2) |
| `review-open` / `review-verify` | blocking findings wait for the maker / resolutions wait for a checker lane; `review-verify` also queues the issue for that lane (§14) | the record writer | the claim holder, after the fold shows nothing pending |
| `checker-requested:<lane>` | the maker's in-session work for a stage exit is done, and the exit's separately started checker (§8.5) is due; queues the issue for that lane (§14) [aM1] | the maker, with its release | that lane: by calling the exit itself when the predicate holds, or by posting its blocking findings, which returns the issue to the maker's queue [aP2] |
| `split` | a parent whose work moved to child issues; `blocked-by` every child; excluded from every worker queue [C9] | triage | the dispatcher closes it administratively when every child is closed (§4.5) |
| tier `S`/`M`/`L` + risk tags (`auth`, `money`, `data-migration`, `iam-iac`) | select the team, the checkers and the budgets | triage, at or above a deterministic floor (§6.4) | raise only; lowering needs a checker's verdict [B18] |
| `priority:<level>`; `priority:critical` expedites (§14) | product priority | an authorised human's `/priority <level>`, applied by the recorder. Triage may set `priority:critical` only when the issue carries a **source record** that the dispatcher re-reads read-only and confirms: a CloudWatch alarm (ARN) in alarm state, or an exploitable AWS Security Agent finding (finding id). A typed provenance line is not enough [aM4, aP11, tP4]. The record is confirmed once, when triage sets the label; a later return of the alarm to OK does not revert it [tQ1] | an authorised human's `/priority` |
| `admitted` | admission of an issue whose author is not on the allow-list; the projection of an `admitted {ask_hash}` record (§6.3) [aM7] | an authorised human's `/admit`, applied by the recorder | — (a changed ask drops it, §6.3) |
| `env-incident` | marks an issue that IS an environment incident; such an issue has no stage and is in no worker queue (§12.5) | the steward, the watcher, any team | its owner, by closing it |
| `tamper` | a record comment of this issue was edited after posting; the issue is held until the re-fold checker re-folds it (§8.2, §14) [aN15, aM13] | the fold | an authorised human's `/clear-tamper` after the re-fold, applied by the recorder |

**Human-owned flags** (`hold`, `priority:*` except triage's source-record case, `admitted`, clearing `tamper`) change
only through explicit forms. The wrapper refuses an agent's write of those labels in any form: an add, a remove, or a
label list inside an issue create or update payload. The dispatcher reverts such a label that no form backs, as it
does for stage labels (§4.4) [aM4, aP11].

### 3.3 Diagram

```
           (every issue, including the operator's own, goes through triage)
START ──triage──► SPEC-REQUIRED ──spec gate──► IMPLEMENTATION-READY ──CI green + verified──► TEST-READY ──deploy+smoke green──► CLOSE-READY ──► closed
  │                                                                                              │   (steward, from the watcher's pinned fact)
  └──► closed (duplicate / invalid / won't do; split → children at START)                        └──► REWORK-REQUIRED (steward: culprit, reject, closed PR; after a landing: revert first)
                                                                                                        │
                                                                    rework analysis, then: TEST-READY | IMPLEMENTATION-READY | SPEC-REQUIRED

Flags on any open stage: needs-input · blocked-by · hold · claimed · ci-pending · review-open/verify · split · tier + risk · priority · admitted · tamper
Not a stage: env-incident issues (§12.5)
```

### 3.4 Properties

1. **States are durable checkpoints, not compulsory hand-offs.** One claim covers the issue, whatever stage the holder
   carries it through, and every transition is recorded with its evidence [A3]. Tier S runs START → IMPLEMENTATION-READY
   → `ci-pending` in one claim, with one hand-off to the verifier (§7.3). A crash leaves a checkpoint another worker
   resumes from.
2. **One writer per issue at a time:** every caller of the verb holds the claim ref for the length of its call (§5)
   [aN1].
3. **A stage changes only through the transition verb (§4.4).** Workers, the separately started checkers, the steward,
   the reconciler and the answer recorder all call the same code. Nobody writes a stage label directly, and a hand-set label is
   reverted, never taken as an override (§4.4) [C16, aN5].
4. **Who may call which edge is fixed by role (§4.5).**

### 3.5 Delivery modes and the forge setup factory mode needs [B21, T-15, aN7, aN8]

The model assumes the merge steward. Per `config/delivery.json`:

| Mode | TEST-READY → CLOSE-READY (always called by the steward) when |
|---|---|
| `merge: steward` + `verification: watcher` | the full predicate of §4.2: every PR landed and not reverted, and the pinned deploy + smoke run green on a commit containing them |
| `merge: steward` + `verification: none` | every PR landed and not reverted, and the trunk CI of a commit containing them is green. The steward applies it at its next tick after the landing [T-15] |
| `merge: direct` (this repository today) | not a factory project. It keeps the session workflow of `clients/common/docs/delivery.md` until it switches (gap-analysis rank 9) |

**Trunk protection depends on the forge plan, so it comes in two tiers** [aN7, aP4, aP5, aP6, aP12, tP1]. Setup and
update determine the tier with the operator's own token and record it in `config/delivery.json`.

| Tier | Where | What guards trunk |
|---|---|---|
| **Protected** | GitHub public repositories, or private ones on Pro, Team or Enterprise Cloud, which have rulesets, environments and deployment branches (GitHub Docs, "About rulesets" and "Managing environments for deployment", seen 2026-11-19); GitLab with fine-grained worker tokens (GitLab 19.2 or later) | **Prevention:** a trunk ruleset or protected branch lets exactly ONE credential push trunk: the steward's trunk credential. On GitHub that is a deploy key, held as a secret of an environment whose deployment branches are limited to the default branch, so no run on any other ref can read it. A ruleset's deploy-key bypass covers EVERY deploy key of the repository, so setup and update check that the steward's key is the only write deploy key; listing keys needs the operator's token [aQ5]. The environment admits every default-branch workflow that names it, including those started by `pull_request_target`, `issue_comment` or `workflow_run`. So the steward refuses to land, and checks trunk on every tick for, any workflow other than its own that names its environment, or other than the deploy workflow that names the production environment; a hit on trunk is an `env-incident` [aQ5]. The check treats an expression-valued `environment` as naming every environment, and a call to a reusable workflow outside the repository as naming one unless the setup record lists that workflow as reviewed [aR3]. Setup and update run the same check first and list each hit, so the operator restructures the workflow or records it as reviewed before factory mode starts [aS4]. On GitLab it is the steward bot's token, as a protected, masked and hidden CI variable, and the worker tokens hold no permission to read variables or change protection. **Plus detection**, below |
| **Detected** | everything else, notably private repositories on GitHub Free, personal or organisation, where rulesets and environments are not available (the chess organisation is on Free, and its ruleset settings say so, operator, 2026-10-26), and GitLab before 19.2, where a worker's `api` scope is full access | **Detection only**, below. Any worker token can push trunk. The steward's deploy key is a repository secret, which a branch workflow can read. The design says so (§15.2) |

**What this does not need.** Worker tokens keep the permissions ordinary work needs, including changing workflow files
and dispatching workflows:
- On the protected tier, a workflow a worker writes, a dispatch on a worker's branch, or the steward's own
  `GITHUB_TOKEN` cannot push trunk, because none of them holds the trunk credential.
- A workflow-file change therefore lands through the queue like any other change. The steward pushes its trains and
  trunk with its deploy key, on both tiers, because a `GITHUB_TOKEN` may not push workflow files (H14). There is no
  human-only step (P6).
- The event-driven steward wake-ups (`enqueue`'s dispatch, the `steward-wake` job) keep working.
- **A deploy-key push starts `push` workflows**, unlike a `GITHUB_TOKEN` push [aQ3]. On trunk, that push run is the
  landing's deploy, so the steward stops dispatching one (§10.4 step 3), and the deploy template's header rule "the two
  triggers never both fire" becomes "the steward's push starts the deploy" (§18). For trains, setup checks that the
  project's CI `push` triggers exclude `steward/train-*`, so the train CI the steward dispatches stays the only run.
  Every other workflow whose `push` or `workflow_run` trigger matches trunk or `steward/train-*` now starts on each
  landing too (a release, a docs deploy, a scan, a second deploy chain); setup and update list them all in the setup
  record, for the operator to confirm when running setup [aR5].
- A worker token can disable a workflow, and a disabled workflow is not triggered at all [aR4, aS1]:
  - the steward checks every tick that the deploy workflow is enabled; a disabled one is an `env-incident`;
  - the steward cannot notice its own workflow being disabled, or report a crash that happens before its own error
    handling, so the dispatcher (§14) checks it on every poll, with a read permission on its token [aS1, aT1, aU2]:
    - GitHub, through the run API ("Actions: read"): the workflow's `state` is `active`; its latest run started within
      the bound; and of its last three completed runs that did not conclude `cancelled` (a superseded tick), not all
      concluded `failure` or `timed_out` [aU1, aV2];
    - GitLab: the steward's pipeline schedule is active and its last pipeline started within the bound
      (`GET /projects/:id/pipeline_schedules/:pipeline_schedule_id`); and of its last three finished pipelines that
      were not `canceled` or `skipped`, not all failed [aU1, aU2, aV2];
    - the bound allows for the schedule being delayed and dropped routinely (8 of about 86 runs in 43 hours, by the
      steward template's own measurement). It is the 99th percentile of the gaps between scheduled runs over the last
      14 days, leaving out gaps inside an `env-incident` of this check, and capped at 4 × the schedule interval; until
      14 days of history exist it is the cap. The dispatcher recomputes it on every poll from the run listing it
      already reads [aU3, aV1]. The schedule runs whether or not anything lands, so a quiet period passes. The
      incident opens only when two consecutive polls see the same fault [aU3];
    - the `env-incident` names what it saw: the workflow or schedule disabled (by hand; by GitHub after 60 days without
      activity in a public repository, GitHub Docs, "Events that trigger workflows", `schedule`; by GitLab when the
      schedule's owner loses access), no run within the bound, or the latest failed run. The status record is not used for this: only the watcher
    writes it, and only after a deploy. Until the dispatcher runs (O12), `enqueue` reports a refused tick dispatch to
    the session that enqueued.

**Detection, on every tier, by the steward on every tick:** every first-parent commit on trunk must be a steward merge
whose push the activity record attributes to the steward's credential:
- GitHub: `GET /repos/{owner}/{repo}/activity`, filtered by the trunk ref and push activity. Whether the record tells
  a deploy-key push from a push made with the token of the account that added the key is to be verified (O14) [aQ6];
- GitLab: the push events of the protected trunk.

Any other push opens an `env-incident` and stops the steward landing until an authorised human resolves it. On the
protected tier detection is a second line behind prevention. On the detected tier it catches only a push that does not
imitate the steward: a branch workflow that pushes with the deploy key read from the repository secrets passes it, and
if the activity record cannot tell the key from the operator's token (O14), so does any push that writes the steward's
trailers. That is a stated residual (§15.2 item 5) [aQ6].

**Changes to privileged automation** are risk-tagged `iam-iac` by the tier floor (§6.4): the workflow files, the
steward's and the deploy pipeline's scripts and local actions, and `templates/ci/`. So they always get the full
security and devops lanes and a separately started checker. That they then run with privilege once landed is inherent
in automation that agents may change (§19).

**Other forge setup**, written by setup and update and checked by them with the operator's token [aM14]:

- GitHub: "Allow GitHub Actions to create and approve pull requests" switched on (`can_approve_pull_request_reviews`).
  The steward detects a refusal at revert time and opens an `env-incident` at once (§10.4 step 3).

Rulesets accept deploy keys as a bypass actor, for all of a repository's keys at once: the bypass list offers one
"Deploy keys" entry (GitHub Docs, "Creating rulesets for a repository"). Whether a deploy key can push workflow-file
changes, and how the activity record names its pushes, is to be verified (O14).

### 3.6 Other trackers [T-21, tN14]

The stages map onto a Jira workflow, whose statuses are exclusive natively, and the flags map onto labels. The claim
(§5) is a git ref and works unchanged. The records (§8), the answer forms and the audit lines use forge comments, so a
Jira backend needs equivalents for those. The Jira wrapper itself is out of scope here.

---

## 4. Transitions and their finish lines

### 4.1 The rule that makes predicates deterministic

> A transition's predicate is evaluated by a script from tracker + git + CI state only. Its checker part is always the
> same sentence: **every checker the stage requires (by tier and risk tags) has posted a verdict on the artefact's
> CURRENT commit, from a context with that checker's role other than the maker's (§8.1), and no blocking finding is
> open. Where §8.5 names a separately started checker for the exit, one of those verdicts comes from it.**

Judgement happens inside the checkers. The predicate only counts their structured verdicts (§8). A verdict on an older
commit does not count, so a new commit by the maker re-opens the check as a delta review. Before landing, the steward
re-evaluates the fold itself and ignores any status a maker could have set (§8.6) [B6].

### 4.2 The predicates

Where §8.5 names a separately started checker for an exit, THAT checker calls the exit, under its `verify` claim, once
the predicate holds; the maker only requests it (`checker-requested`). Its verdict is then bound to the caller, as the
verifier's always was [aP2]. Every predicate's checker clause is evaluated from a fold of ALL the issue's records, not
from a cached folded state (§8.2) [aP3].

| Transition (caller role, §4.5) | Predicate (all must hold) |
|---|---|
| START → SPEC-REQUIRED (worker; for M and L, the triage checker) | a triage record for the current ask hash, containing: the duplicate search (candidates and verdict), a scope verdict, tier and risk tags at or above the deterministic floor (§6.4), the estimated footprint, and the **decision inventory** (§12.2). For M and L, a triage checker's verdict on the record [T-19]. No open blocking question |
| START → closed (the duplicate-confirmer) | the triage record's outcome (duplicate, invalid, won't do) + a SECOND agent's confirming verdict (the duplicate-confirmer, which then calls the close). Closing destroys work, so it always gets a checker |
| START → split (worker) | every child exists at START and references the parent; the parent carries `split` and is `blocked-by` every child |
| SPEC-REQUIRED → IMPLEMENTATION-READY (worker for tier S; for M and L, the separately started spec checker) | spec + acceptance tests committed at SHA S on the pushed issue branch; the acceptance tests fail for the right reason at S; every acceptance criterion is referenced by ≥ 1 test (traceability script); all required spec checkers report on S with 0 open blocking findings; **for M and L, one of them is a separately started spec checker** (§8.5) [aN9]; no open blocking question; the approval setting, if on, is satisfied for the spec (§12.10); tier and tags re-derived from the spec's declared footprint, raise only (§6.4). **Side effect** written by the verb: `spec-approved {sha: S, ask_hash}` [C14] |
| IMPLEMENTATION-READY → TEST-READY (the verifier lane; for a re-enqueue, the worker) | a PR from the branch with `Refs #N`, base = trunk, `do-not-merge` removed (and not a draft where the forge has drafts) [B22]; **S's acceptance tests, run with S's fixtures and test configuration over H's code, pass** [B19]; any change since S to the acceptance tests, the fixtures or configuration they depend on needs a newer `spec-approved`; PR CI green on head H; **the adversarial verifier, started separately at `ci-pending`**, and every required implementation checker report on H with 0 open blocking findings; the approval setting, if on, is satisfied for the PR's changed paths [T-07]; the evidence report is present; `check-pr` exits 0. **The worker never transitions with CI pending:** it sets `ci-pending` and releases. The verifier lane completes the transition when the run ends. When no CI result exists after the `ci-pending` timeout (default 3 × the project's median PR CI duration, at least 1 h), the verifier refuses with "no CI result", clears `ci-pending`, and the issue is back in the implementation queue [aN3]. `enqueue --allow-pending` remains only for a re-enqueue after a rebase that changes no file, when pending CI is the sole unmet clause [C1] |
| IMPLEMENTATION-READY or REWORK-REQUIRED → SPEC-REQUIRED, the re-spec edge (worker at pickup; the answer recorder on a human form) [aM6] | the ask hash differs from `spec-approved`'s (an authorised human edited above the marker, or an `/amend` was executed), OR an authorised human's `/stage spec-required` names the issue. The record names which. (A REWORK-REQUIRED exit chosen by the team itself goes through the rework analysis below). **Side effects** [aP8]: clear `ci-pending`, `checker-requested`, `review-open` and `review-verify`; put `do-not-merge` on the issue's open PR, or close it; record what was done |
| TEST-READY → CLOSE-READY (steward) | **every PR of the issue is in state `landed` or `relanded`, or is named in a rework record as replaced by a later PR of the issue** [B15, aN7, aP1]. A PR's state is the last of its first-parent facts: `Steward-PR` (landed), `Steward-Reverts` (reverted), `Steward-Relands` (relanded) (§10.4 step 3). And a **pinned deploy verdict of outcome `green`** on a commit D that contains every landed or relanded merge [aN10, aM3, aP10]. The pinned verdict has four outcomes, read from the jobs API: `green` (the deploy and smoke jobs concluded `success` and no restore step ran); `red`; `restored`; `skipped or refused`. Only `green` counts here. The pinned run is either the trunk `push` run that the steward's landing push started, with D its `head_sha`, or a deploy the steward dispatched itself to re-verify, identified by the run id the dispatch returned (`return_run_details: true` under API version `2022-11-28`; always returned from `2026-03-10`) [aP15, aQ3]. Any other run, a worker's dispatch included, is data. The verdict reads the pinned run's FIRST attempt (GitHub: `/attempts/1/jobs`; GitLab: the pipeline's jobs listed with `include_retried=true`, each job's earliest attempt), and later attempts are data [aQ7, aR6]. A pinned run that was cancelled or deleted counts as `skipped or refused`. Supersession cancels pending deploys as a matter of course, so the steward dispatches a new deploy of trunk's tip only when no other pinned run whose commit contains D is pending, running or done; so does a landing whose push run has not appeared within the dispatch grace period [aR1, aR4]. Every `(post-deploy)` item ticked. Under `verification: none`: §3.5 |
| TEST-READY → REWORK-REQUIRED (steward) | one of: a train record naming this PR the culprit, a conflict, or PR-CI red; Track T's culprit record (§10.4); a blocking finding on the queued PR (`review-open` dequeues it); **the steward rejected the PR for any other reason** (base not trunk, draft, closing keyword, dependency closed unlanded); **the PR was closed unmerged** [aN3]; **a revert of this PR landed outside Track T** (a `Steward-Reverts` fact for a revert the steward did not open, §10.4 step 3) [aM2]; **or an authorised human's `/stage` request** for this issue, which the steward applies after dequeuing the issue's PRs (§8.3) [aM6, aP8]. The record names the cause. Every tick re-derives the exits of every TEST-READY and CLOSE-READY issue from these durable facts, so a return refused by a held claim is applied at the next tick [aM8] |
| CLOSE-READY → REWORK-REQUIRED (steward) | a `Steward-Reverts` fact landed for one of the issue's PRs after the issue entered CLOSE-READY [aP1] |
| closed → REWORK-REQUIRED (steward; reopens the issue) | a `Steward-Reverts` fact landed for one of the closed issue's PRs [aP1] |
| REWORK-REQUIRED → any exit (worker) | a **rework-analysis record** classifies the cause as code, requirement or environment, with evidence, and a checker other than the maker confirms it [T-01, tN10, tM3]: the test-architect confirms "code" (the acceptance tests still express the ask); the spec checkers confirm "requirement" when they re-approve the amended criteria (tier S: the combined pass, §8.5); the steward's infra classifier (§10.4 step 1) or the failure attributor confirms "environment". Then: **→ TEST-READY**: the IMPLEMENTATION-READY → TEST-READY predicate on the new head, plus a resolution record answering the cause; **→ IMPLEMENTATION-READY / SPEC-REQUIRED**: a requirement cause amends the acceptance criteria before code is touched, and the target stage's predicates apply from scratch. **An environment cause leaves no exit:** the issue stays in REWORK-REQUIRED, `blocked-by` the `env-incident` (§12.5). When the incident closes, the failing check is re-run; green returns the issue to TEST-READY through the resolution record, and §13's refund applies |
| CLOSE-READY → closed (worker; where §8.5 names the log-scan lane, that lane) | no `Steward-Reverts` fact for any of the issue's PRs has landed since CLOSE-READY was entered [aP1]; the close-out record (§11): the temporary-resource ledger AND a query by the `factory-issue` tag are both empty [B20]; every item of the **laundry list** has a disposition. The laundry list is the spec's residuals, the findings-ledger rows written during the issue, the lanes' `notVerified` entries, the log-scan lane's findings and the close-out's own observations [D4, T-06]. The structured summary is posted; the checklist is complete; no open PR references the issue; the remote branch is gone |
| `split` parent → closed (dispatcher) | every child is closed [aN2, C9] |

### 4.3 Pickup preconditions (checked when a claim is taken)

- **The ask is unchanged since approval**, checked in SPEC-REQUIRED, IMPLEMENTATION-READY and REWORK-REQUIRED [B5,
  aN6, aP8]:
  - The **ask** is the title, plus the body ABOVE a machine-owned marker line (`<!-- factory: below this line is
    maintained by agents -->`) without checklist tick states, plus the text of every executed `/amend`, in comment
    order [aP9]. The verb compares its hash with `spec-approved`, and the close-out's "what was asked" quotes it.
  - Agents write only below the marker: discovered checklist items, notes. The wrapper refuses an agent's edit above
    it.
  - An authorised human changes the ask by editing above the marker, or with `/amend <text>` [aM6]:
    - in START and SPEC-REQUIRED, the change simply becomes part of the ask;
    - in IMPLEMENTATION-READY and REWORK-REQUIRED, the re-spec edge of §4.2 takes the issue back to SPEC-REQUIRED,
      where the spec checkers re-approve quickly if the change is immaterial. A worker that finds the mismatch at
      pickup calls that edge itself; an `/amend` is applied by the answer recorder;
    - from TEST-READY on, `/amend` is refused with "file a new issue": the code is already in the queue or on trunk.
  - Answers, notes and machine comments never change the ask.
- **An outsider's issue still says what was admitted** [aM7]. For an issue whose author is not on the allow-list,
  every pickup compares the current ask hash with the `admitted {ask_hash}` record. A mismatch drops the issue back
  to read-only triage with a new admission view (§6.3).
- **The spec base is current enough.** If the spec's declared footprint changed on trunk since S, the spec checkers do a
  delta review against the new trunk first. This replaces a WIP cap (decision U8).
- **No `hold`, no open `blocked-by`, no `needs-input`, no `tamper`.**
- **For a checker role:** the issue is in that lane's queue (§14).

### 4.4 The transition verb, its recovery, and where the stage is stored [B2, C16, aN1, aN5]

One wrapper verb for both forges, for example `transition <issue> --from <stage> --to <stage> --evidence <link>`. Its
caller ALWAYS holds the issue's claim ref for the length of the call. Workers hold a `make` or `verify` claim; the
steward, the answer recorder and the dispatcher take a short `record` claim (§5.3).

1. **Guard.** This is a read followed by writes. Exclusion comes from the claim ref, which every caller holds. It
   refuses when:
   - the issue is not in `--from`;
   - the caller's role may not call this edge (§4.5);
   - the caller's fencing token is not the claim ref's current value;
   - or the predicate fails. The refusal names the unmet clause.
2. **Intent.** Append `factory: stage <A> -> <B> intent <id> by <role>/<agent>`.
3. **Side effects** of the edge: the enqueue, the `spec-approved` record, the release.
4. **Labels.** Add the new stage label, then remove the old one, with the additive primitives only.
5. **Done.** Append `factory: stage <A> -> <B> done <id>`.

**The reconciler** (dispatcher, §14) completes or undoes another role's recorded intent; it starts no edge.

- It touches an issue only when its claim ref is free or absent AND the open intent is older than the lease L, so a
  live verb, which always holds the ref, is never mistaken for a crashed one.
- An intent without `done` is rolled forward when its side effects are present and back when they are absent.
- An issue with zero or two stage labels is repaired from its last `done` line.
- **A stage label that disagrees with the last `done` line is reverted**, and the reversion is recorded. A hand-set
  label is never taken as an override, whoever set it: under the shared account an agent's label write and a human's
  look the same. A human changes a stage with `/stage <to> because <reason>` (§8.3), which the verb evaluates like any
  other call (P12). The same reversion applies to a human-owned flag that no explicit form backs (§3.2) [aM4].

These audit lines are the trail an auditor reads and the metrics source (§17). They are comments, so not immutable
(§19).

**Storage.** The portable path is plain prefixed labels (`stage:spec-required`), which work on every tier of both
forges, with exclusivity enforced by the verb. Native single-select storage is a later option: GitLab scoped labels
(`stage::…`, Premium/Ultimate) and GitHub issue fields (organisation-level single-select, generally available since
2026-07 per GitHub; not for user-owned repositories).

### 4.5 Authority: which role may write what [A1, P11, aN2]

| Role | Identity under the shared account (U24) | Claim it holds while writing | May call | May write |
|---|---|---|---|---|
| **Worker** (maker team) | the operator's login, on a per-host token (§15.2) | `make` | the worker edges of the issue it holds (§4.2) | its team's records; below-the-marker issue text; spend lines |
| **Checker lane** | the same login; distinguished by a fresh agent context with the lane's role (§8.1) | `verify` when started separately; none when dispatched by a conductor | when started separately: the exits §8.5 assigns to it (the verifier IMPLEMENTATION-READY → TEST-READY; the duplicate-confirmer START → closed; the triage checker START → SPEC-REQUIRED; the spec checker SPEC-REQUIRED → IMPLEMENTATION-READY; the log-scan lane CLOSE-READY → closed) [aP2] | finding, verification and verdict records; spend lines |
| **Conductor** (in the maker's session) | the same login | the maker's `make` claim | none | the round envelope, assembled verbatim from the lanes' parts (§8.4); trusted only as far as the maker's session (§8.5) |
| **Arbiter** | the same login; a fresh context | none (it writes through the claim holder) | none | `decision` records on a conflict set (§8.7) |
| **Question checker** | the same login; a fresh context | none (it writes through the claim holder) | none | a question verdict (pass / answered, with the answer) per question (§12.4) |
| **Steward** | the steward's CI identity (GitHub: the workflow's `GITHUB_TOKEN` for PRs and comments, and its deploy key for train refs and trunk (an environment secret on the protected tier, a repository secret on the detected tier); GitLab: the steward bot's token, a protected, masked and hidden variable) | `record`, per issue it writes | TEST-READY → CLOSE-READY (from the pinned deploy verdict, or at landing under `verification: none`); TEST-READY → REWORK-REQUIRED, incl. a human's `/stage` request; CLOSE-READY → REWORK-REQUIRED and closed → REWORK-REQUIRED on a revert fact [aP1]; reland moves within TEST-READY; the release verb | trunk (fast-forward to a train), train refs, revert and reland PRs, `Steward-*` trailers (incl. `Steward-Reverts` and `Steward-Relands`), `merge-steward:` lines, `dispatched run` records, culprit / `red-since` / refund records, `env-incident` issues, and the `blocked-by` on the issues an incident affects, including incidents the watcher opened [aM15] |
| **Watcher** (the deploy pipeline's verdict job) | the deploy pipeline's CI identity: `contents: read`, `issues: write` [aM15] | none | none | verification facts naming the pinned run; `delivery-status`; `env-incident` issues. It sets no flag on a factory issue: the steward applies the `blocked-by` an incident causes at its next tick, under a `record` claim |
| **Dispatcher** (reconciler, reaper, queue keeper) | the dispatcher's token: contents write (claim refs), issues write (repairs, the `split` close, `blocked-by` clearing), actions read (the steward's liveness, §3.5; GitLab: a read scope for the pipeline schedule) [aT1, aU2]; a read-only AWS role for alarm states and Security Agent findings (§14) [tQ1] | `record` | the `split` close; repairs of §4.4; claim expiry (§5.2); no forward edge of another role | repair, reversion and expiry lines; `blocked-by` releases |
| **Answer recorder** (headless) | acting for an authorised human, whose login and comment id the record names | `record` | the re-spec edge on an `/amend` or `/stage spec-required` (§4.2); nothing on TEST-READY, where it posts a steward request record instead [aM6] | `factory: answer` records; clearing `needs-input`; the human-owned flags a form sets (§3.2); `admitted {ask_hash}` |
| **`/get-guidance`** (interactive, in the human's session) | the operator's login | none | none | nothing on the tracker: it collects, asks, and prints the form lines for the human to post (§12.9) [aM5] |
| **Authorised human** | a login on the project's human allow-list (the operator; named collaborators) | — | through explicit forms only (§8.3) | reserved decisions (§12.3) are valid only from this role |

Every role that runs an agent context may append spend lines (§13) [tN3]. A write by any other identity, or by a role
outside its row, is data: it is never counted by a predicate.

**Facts are taken from where they cannot be forged by a comment:**

- landings, reverts and relands from trunk's first-parent history, whose commits only the steward writes. On the
  protected tier that is enforced; on every tier a per-tick check confirms each first-parent push was made with the
  steward's credential (§3.5, §10.8 H7) [aN7, aP5];
- claims from the claim ref (§5);
- CI and deploy results from the forge's run API, pinned to workflow path, event, ref and environment (§4.2) [aN10].

The watcher's and the steward's issue records count only when they name a run that matches the pin. On GitHub the
steward and the watcher both post as `github-actions[bot]`, which a workflow on a PR branch can also do. That is why
no predicate rests on such a comment alone: landings come from trunk, and deploy verdicts from the pinned run read
through the API [aP12].

**Under the shared account** (decision U24), worker, checker, conductor and recorder writes all come from one login.
Their roles are told apart by the marker and the `actor` fields, which proves nothing against a compromised agent. That
residual is accepted; its true size is stated in §15.2.

---

## 5. Claims [A3, B1, C11, C17, C20, C21, aN4]

### 5.1 The claim ref is permanent; its tip says whether the issue is held

Each issue has one ref, `refs/factory/claims/<issue>`, in the project's repository. Where a forge refuses a custom ref
namespace, it is a branch with the prefix `factory-claim/`. That fallback starts every `on: push` workflow without a
branch filter and falls under branch rulesets, so the custom namespace is preferred (O14).

- **Commits are states.** After the first claim, the ref always exists. Its tip is either:
  - a `held` commit, whose message records the kind (`make`, `verify` or `record`), the holder (role, host, session,
    agent), the stage (informational) and the fold cursor;
  - or a `free` commit, which records the fold cursor and the last holder.

  Both carry a tree with the **folded state at the cursor**: open findings, verdicts per SHA, pending questions, and
  the time of the last fold. The release verb writes it [aM9]. A new holder reads that state to orient itself at
  pickup, then fetches only the comments updated since the last fold's time (`since`), which returns new and edited
  comments alike. Decisions never rest on it: exit predicates, separately started checkers and the steward re-fold from
  the first record (§8.2) [aP3].

  "No claim" in a queue (§14) means: the ref is absent or its tip is `free`.
- **Acquire.** Push a `held` child of the observed tip with `git push --force-with-lease=<ref>:<observed tip>`, or with
  an empty expectation when the ref does not exist yet. The receiving side checks the ref's old value atomically, so a
  second acquirer is refused by the server. There is ONE claim per issue, whatever stage it names.
- **Fencing token** = the tip SHA of the caller's `held` commit. Every verb call checks it against the ref's current
  value.
- **Branch pushes are fenced atomically.** The worker pushes the issue branch and a renewal commit of its claim ref
  together, in ONE `git push --atomic`, with the lease on the claim ref. A branch update therefore lands only while the
  caller holds the claim.
  - The `pre-push` hook refuses any push of an issue branch that is not that atomic push with the lease, so a plain
    `git push` by an expired holder is refused locally too [aM11].
  - REST writes (comments, labels) are fenced only by the check before each call. That window is one call long (§19).
- **Renew** by pushing a child `held` commit with a lease on the current token, as a ref-only
  `git push --force-with-lease`, which spends no REST write [aM10]:
  - the wrapper renews on EVERY wrapper call, reading or writing;
  - the commit hook renews on every commit, best-effort and in the background, so a **checkpoint** is at least every
    commit. A failed renewal never fails the commit, and the next call retries [aP13];
  - `scripts/run_tests.py` and `scripts/suite_semaphore.py run` renew while they run or wait for a slot, so a long local
    run (mutation testing, a queued suite) does not lose a live claim [aP13]. They renew only while their parent
    process lives and only up to a ceiling of 2 × L; past it the tool exits non-zero and the claim expires as §5.2
    says, so a hung suite or an endless slot wait cannot hold a claim [aQ9].

  There is no heartbeat process, so a hung worker stops renewing and expires. The lease duration L is set from the step
  durations the spend lines record (§13): default 60 minutes, capped at 90. A measured step longer than L is reported in
  the digest as a defect of that step, to be split [C17, aN4, aM10].
- **Release** with the ONE release verb [C11]:
  - push a `free` child, keeping the cursor, with a lease on the token;
  - remove the `claimed` projection;
  - remove the legacy in-progress label and assignee if present.

  The steward and the dispatcher call the same verb.
- **Projection.** A short claim comment may mirror the ref for humans. The protocol never edits or deletes a comment
  [C21].
- **The lease binds cooperating clients only.** Any token with contents write can force-push or delete a claim ref, and
  worker tokens have contents write. This is a residual (§19).

### 5.2 Expiry and the reaper

- The reaper (dispatcher, §14) declares a claim expired when the same `held` tip has stood unchanged for L by the
  reaper's own clock, across two of its own observations. No worker clock is compared, so clock skew does not matter.
- Expiry pushes a `free` child (keeping the cursor) by compare-and-swap. The old holder's next call fails on the fence,
  and its next atomic branch push is refused with it.
- The issue is then pullable again, and the next holder resumes from the cursor.

### 5.3 Record, verify and group claims

- **Record claims:** the steward, the answer recorder and the dispatcher take a `record` claim for the
  length of one verb call, so they never write under a worker's claim or race each other [aN1]. When the ref is held,
  they back off and retry on their next tick or poll.
  - TEST-READY issues are never held by workers, so the steward contends only with the recorder and the dispatcher.
- **Verify claims:** a separately started checker lane takes a `verify` claim. It may write only its own records, and
  call only the exits §4.5 assigns to its lane (the verifier's is the `ci-pending` completion) [aP2, aQ10].
- **Group claims:** a decision that moves several issues acquires all their claim refs in ONE `git push --atomic`, all
  or nothing, with no back-off loop [C20, aN4]. Example: "this batch goes back to SPEC-REQUIRED". The alternative is ONE
  coordinating issue that the others are `blocked-by`.
  - Workers never negotiate in free text; §8 is the only exchange format.

### 5.4 One release verb, and the continuation issue

- The release verb replaces `release-issue`'s whole-set label write with additive removes. A label added by someone
  else between a read and a write is then never lost.
- **Continuation issue** (§8.2) [aM12, aP14]:
  1. when an issue reaches the comment cap, the verb creates the continuation issue;
  2. in one atomic push, it creates the new issue's claim ref (held, with the cursor and folded state) and moves the
     old ref to `free` with the line `continued in #<m>`. The new issue is now held, so no worker can acquire it;
  3. on the new issue, it writes the inherited stage label and the line `factory: continued from #<n>`;
  4. it closes the old issue administratively ("continued in #m"), so no queue pulls it again.

  The reconciler finishes or undoes a half-done continuation from those lines. A new issue that carries
  `continued from` is therefore never taken for a fresh START issue.

### 5.5 Atomic-push support

Atomic multi-ref pushes and lease refusals are git protocol features. Whether both forges honour them on custom refs
is to be verified on `sff-test-*` repositories (O14), as is whether a push to a custom ref starts any workflow.

### 5.6 Why today's claim is not enough (code read on 2026-11-11)

- `start-issue` refuses a claim only when a DIFFERENT login holds it (`_claim_is_held_by_another` in
  `src/payload/scripts/github_api/commands/claim.py`). Every worker posts as the same login, so a second machine's claim
  on the same issue succeeds.
- The orchestrator calls `issue start` without `--strict`. Even `--strict` reads and then writes, so two workers that
  read before either writes both succeed.
- The `mkdir` lock (`.locks/issue-<N>.lock`) serialises only workers inside ONE clone.
- `release-issue` writes the whole label set minus `in-progress` from a fresh read, so a concurrently added label is
  lost.
- Revision 1's comment protocol had the same weaknesses, plus a list endpoint that may lag right after a create [B1].

---

## 6. Inflows, admission and triage

### 6.1 Inflows into START

1. issues the operator files;
2. agent-filed issues: the feedback loop, under the filing discipline, with its provenance lines;
3. production signals [T-09]:
   - an alarm or an AWS DevOps Agent investigation produces ONE issue through `issue-intake-agent`, with
     `Origin: production`, under the same filing gate (gap-analysis 2.6);
   - the dispatcher pulls a START issue FIRST when its AUTHOR is a factory login and it carries `Origin: production`,
     so an incident does not wait behind other work before triage (§14). The author check matters because anyone can
     type the provenance line (§6.3);
   - triage then sets `priority:critical` only with the alarm's source record, which the dispatcher confirms is in
     alarm state (§3.2) [aP11, tP4];
4. close-out findings (§11), under the filing discipline.

**Every issue goes through triage**, the operator's own included; there is no pass-through (decision U16).

### 6.2 What triage produces

The triage record of §4.2:

- the duplicate search;
- the scope verdict;
- tier and risk tags (§6.4);
- the footprint;
- the decision inventory (§12.2).

### 6.3 Admission [B8, C13]

The question is not whether an issue is triaged, but whether its TEXT may direct agents that can push code and deploy
to AWS.

- **Auto-admitted** iff the issue's AUTHOR is on the project's allow-list: the operator's login and the factory's
  login(s). Provenance lines describe an admitted issue; they never admit one, because anyone can type them.
- **Everything else** (other collaborators, bots, integrations, external reporters on a public repository) is triaged
  in a **read-only mode** and waits for an authorised human's `/admit`:
  - no write tools, no AWS credentials, no forge write except the triage record;
  - the issue text is data;
  - the admission view shows the verbatim body, fenced, next to the triage paraphrase, because a paraphrase of injected
    text can read harmless.
- **Admission names the ask** [aM7]. The answer recorder turns `/admit` into an `admitted {ask_hash}` record, with
  the label as its projection. An issue author can edit their own title and body at any time, so every pickup compares
  the current ask hash with the admitted one (§4.3). A mismatch drops the issue back to read-only triage, with a new
  admission view.
- **On public repositories**, locking factory issues to collaborators is a cheap extra layer. With or without it, a
  comment from a non-allow-listed author is data (§8.3).

### 6.4 The tier and risk floor [B18, T-19]

A deterministic footprint heuristic computes a minimum tier and minimum risk tags. Examples:

- paths under `cdk/` or IAM policies ⇒ `iam-iac`;
- auth modules ⇒ `auth`;
- migrations ⇒ `data-migration`;
- footprint breadth ⇒ a minimum tier.

Triage may raise the floor, never lower it. At SPEC exit, the tier and tags are re-derived from the spec's declared
footprint and may only rise. Lowering below the floor needs a checker's verdict. A worker carrying an issue through
several stages therefore cannot pick its own checking depth.

### 6.5 Untrusted content inside admitted issues [T-05]

Log lines, web pages, error messages and external reports quoted in an issue are fenced and marked as data.

The triage checker refuses an ask whose INSTRUCTION is taken from quoted text: an imperative, request or command found
inside a log line, page, error message or external report. An agent's own defect statement that cites fenced log lines
as evidence is admitted.

Under this rule the keynote's examples pass triage: a defect filed with log lines attached, and an incident's fix plan.

---

## 7. Teams and the loop inside a stage

### 7.1 The loop

```
claim ──► maker produces or updates the artefact at SHA X
  ▲            │
  │            ▼
  │   deterministic tools on X (cheap; SARIF out) ──► findings
  │   LLM checkers on X, in parallel, in fresh contexts, given the tool output filtered to the diff ──► findings
  │   a separately started checker where §8.5 names one for the exit
  │            │
  │   predicate(X)? ── yes ──► transition verb ──► release, or continue to the next stage (§3.4)
  │            │ no
  │            ▼
  │   maker answers EVERY open finding: fixed@SHA / alternative / rejected-with-evidence / conflict
  │   conflict sets ──► joint resolution (§8.7)
  │            │
  └── budget left? ── no ──► needs-input with a "stuck because …" record (§13), the rare exception
```

### 7.2 The team per stage (*R: checker-landscape.md §3, mcp-and-powers.md §5, plugin-marketplaces.md §3*)

| Stage | Makers | Deterministic checkers (first) | LLM and external checkers (gated by tier and risk) |
|---|---|---|---|
| START | triage worker | duplicate retrieval (forge search + lexical or embedding similarity over open and recently closed issues); the tier and risk floor (§6.4); template lint | **duplicate-confirmer** (mandatory before any close); **triage checker** (M, L); both separately started through `checker-requested` (§8.5) |
| SPEC-REQUIRED | spec-author (+ spec-researcher); acceptance-test author; threat-model maker (L or risk tags: the awslabs threat-modeling MCP server, pinned to a commit) | AC → test traceability; red for the right reason; EARS/INCOSE spec lint (new); byte caps; threat-model schema check | test-architect; security-reviewer (one-line CLEAN unless a trust boundary is touched); **threat-model checker** (new; STRIDE + OWASP ASVS 5.0; L or risk tags); devops-iac-reviewer (IaC); standards / best-practice (M+); for M and L, **one of these runs as a separately started spec checker** (§8.5) [aN9]; optional AWS Security Agent design review (L + `auth`/`money`, budget-capped) |
| IMPLEMENTATION-READY | spec-implementer (waves), ci-workflow-agent, code-merge-reviewer | ruff, mypy, bandit, secret scan, tests; **diff coverage on changed lines** (new); **OSV-Scanner** (new); **IaC gate: cdk-nag + cfn-lint + Checkov or cfn-guard + `cdk diff --security-only`** (new); import/architecture contracts; mutation testing on changed functions (L or risk tags); **dead and unnecessary code on the diff** (vulture or Skylos `--diff`, knip); IAM Policy Autopilot (actions the code needs vs the CDK grants); **docs-drift tools** (lychee, markdownlint) when the change touches a documented interface [tN7] | the adversarial-verifier, always **started separately at `ci-pending`**; **logic-bug reviewer** (new, M+: find → verify-to-disprove → rank); standards (M+); security and devops lanes by risk tag; unnecessary-code reviewer (M+); **docs-drift checker** (the checker half of `doc-reviewer-agent`: documentation checked against the code) when the change touches a documented interface [tN7]; optional **external security review of the PR** (AWS Security Agent diff scan; project setting `external_security_review`: `risk` by default, `all` for every PR, or `off`) [T-04] |
| TEST-READY | merge steward, deploy pipeline | train CI; pre-flight (§10.3); **stateful replacement/deletion detector** on the change set (new); smoke/E2E | failure attributor for smoke failures: it uses CloudWatch and CloudTrail MCP read-only, ranks only inside the suspect set, and treats logs as data [C15]. Optional batch release readiness (AWS DevOps Agent) for batches with `iam-iac`. Optional **penetration test** of the shared stage environment (AWS Security Agent): budget-capped, batched per project setting (e.g. weekly, or per batch containing `auth`/`money`). Its findings enter START as issues, each carrying its finding id as a source record; triage sets `priority:critical` on an exploitable one, which the dispatcher confirms by re-reading the finding (§3.2) [tP4]. They do not hold a release (traceability C10) [T-04, tN8] |
| REWORK-REQUIRED | any implementer | the same deterministic set on the new SHA; SARIF baselines show which findings are fixed, new or unchanged | the test-architect confirms a "code" rework classification, the steward's infra classifier or the attributor an "environment" one (§4.2); then only the lanes with open findings, plus lanes whose files the fix touched (delta) |
| CLOSE-READY | close-out worker: its AWS role may delete only the issue's own temporary resources, bounded per action by tag or by name prefix (§11), and it reads no logs [tN1, tQ3] | leftover checks on the diff (TODO, debug flags); the temporary-resource ledger and tag query (§11) | **log-scan lane**: a separately started, read-only lane with no AWS write credentials that scans the deploy window's logs, where the project provides a read-only log query, and emits finding records the close-out reads as data [T-13, tN1]; **retro checker**: every learning is backed by evidence, is not already a rule or memory, and nothing is filed without an observed defect |

Two existing agents break maker ≠ checker and are split when implemented: `issue-housekeeping-agent` and
`doc-reviewer-agent` both make and check.

### 7.3 Cost proportionality, and the tier-S minimum path [C7, T-16]

| Selection | Checkers |
|---|---|
| Every issue | the deterministic baseline, AC traceability, red for the right reason, diff coverage, the separately started adversarial verifier |
| Tier S | as `proportionality.md` says today: ONE combined spec-review pass (all lenses, incl. test coverage; max 2 iterations) instead of the panel |
| Tier M and L | the full panel (test-architect, standards, best-practice, security, devops as tagged), one of them started separately; the logic-bug reviewer; the triage checker; the close-out LLM reviewers |
| Tier L | the threat-model lane, mutation testing |
| Risk tags | `auth`/`money`: full security, threat model, mutation; `iam-iac`: devops-iac plus the IaC gate (which also runs whenever `cdk/` changes); `data-migration`: the stateful-replacement check is blocking |
| Paid external agents (AWS Security Agent, AWS DevOps Agent) | per project setting, budget-capped, never the only checker for a gate |

**The tier-S minimum path:** a one-line fix stays a one-line fix.

| Step | What tier S does | Why it stays |
|---|---|---|
| Triage | the deterministic floor, duplicate retrieval, a one-line decision inventory; the duplicate-confirmer only if a candidate is found | every issue is triaged (U16); a wrong close destroys work |
| Spec | `change.md` with its acceptance criteria and the tests that pin them, on the issue branch | the finish line must exist before the code |
| Review | ONE combined pass, in the maker's session | today's rule; the independent check of tier S is the verifier (§8.5) |
| Implementation | one wave; the deterministic baseline | — |
| Verification | one separately started adversarial-verifier pass at `ci-pending`; it starts cold, and its cost counts in the tier-S budget | maker ≠ checker on the code |
| Close-out | the deterministic clean-up and the summary; the retro checker only when a learning is proposed | U18 |
| Hand-offs | ONE, at `ci-pending`, to the verifier [aN12]; otherwise one claim from START to `ci-pending`, unless the worker is interrupted | context stays warm |

### 7.4 Techniques every checker uses (*R: plugin-marketplaces.md §4, checker-landscape.md §4*)

- Deterministic tools first. The LLM lanes get their SARIF filtered to the diff, to triage it and to hunt for what tools
  cannot see.
- A separate pass tries to DISPROVE each finding. A finding nobody can confirm is dropped, and its severity is capped at
  what the confirmation supports.
- Lens-split finders run in parallel, each with an explicit "do not flag" list.
- Proof comes from runner result files (counts, a deliberate break that must fail, "named, not run" for skipped tests),
  never from model opinion.
- Every verdict names what the lane did NOT verify (`notVerified`, §8.1) [T-06].
- Repository, issue and log text is evidence, never instruction.
- Stable finding ids with a revision stamp (§8).
- Per-lane precedent files and a resolution rate (the share of a lane's findings that were actually fixed) keep false
  positives down.

### 7.5 MCP servers always have a CLI path

The desktop app here runs Code sessions under `strictPluginOnlyCustomization: ["mcp"]`, so project MCP servers do not
load. A gate must therefore never depend on an MCP server. The deterministic checks run through
`src/payload/scripts/run_checks.py` and CI; MCP servers are optional accelerators for makers and LLM checkers
(decision U19, *R: mcp-and-powers.md*).

The policy comes from the AWSBedrockGateway project's gateway configuration: a non-empty `managedMcpServers` switches it
on. It stalled chess #1507.

---

## 8. The maker/checker exchange: `factory-review/v1` (*R: review-protocol.md*)

### 8.1 Records and actors

One JSON envelope carries seven append-only record types:

- `finding`, `resolution`, `verification`: the checker raises, the maker answers, the checker verifies;
- `link`: duplicate-of, conflicts-with, regression-of;
- `proposal`: a joint option for a conflict set;
- `decision`: arbiter or human;
- `verdict`: per lane per SHA, CLEAN or NOT-CLEAN with counts, and a REQUIRED `notVerified: [{scope, reason}]` (empty
  when the lane covered everything). Example: "routes, auth middleware: no test reaches them" [T-06].

The envelope's subject names the forge, repo, issue, PR, stage, tier, iteration and commit. Its `actor` has three
fields [A2]:

- `worker`: the claim holder's host and session, as in the claim ref;
- `agent`: a fresh id for every agent context, i.e. every subagent dispatch and every new session;
- `role`: the lane, or `maker`, `conductor`, `arbiter`, `question-checker`, `recorder`.

**Maker ≠ checker is checked on `agent` and `role`, not on `worker`.** A verification is valid only from an agent
context with the finding's lane role that did not write the resolution. For in-session lanes these fields are written by
the conductor's session, so their independence is bounded as §8.5 says.

- **A finding IS a SARIF 2.1.0 result** (a subset), so it can be exported to SARIF unchanged. The framework's fields sit
  under `factory/…` property keys: severity A–D and the blocking flag (the review contract's materiality),
  material-because (an acceptance-criterion id or a failure class), the violated standard, reasoning, evidence (command,
  exit code, excerpt, commit), and one or more options with patches, the recommended one first.
- **The target.** The reviewer writes meaning; the tool computes coordinates.
  - The reviewer gives a quote, as a W3C Web Annotation `TextQuoteSelector` (the exact text with a prefix and a suffix),
    plus a symbol or a section.
  - The tool resolves line, offset and fingerprint at the pinned commit, and rejects a quote it cannot find.
  - This works for code and for spec prose alike, survives edits, and removes invented line numbers.
- **Status is never stored.** It is derived by folding the records:
  open → addressed → verified | disputed → escalated | withdrawn | wont-fix-accepted.

### 8.2 Transport and marking [B10, C4, C5, C21, aN5, aN15]

1. **Inside one machine:** a file per lane per iteration.
2. **Between machines and issues:** an issue comment.
   - Layout: a hidden marker line, a one-line Conventional-Comments rendering for humans, and the JSON in a fenced block
     inside `<details>`.
   - **One envelope per ROUND:** the conductor posts every in-session lane's records of a round together. A separately
     started lane posts its own part (§8.5).
   - At most 60,000 characters per comment, because GitHub refuses more than 65,536. Deterministic ids. Read before
     write. Never edit.
   - **Fold order** is by comment or note id on BOTH forges, not by creation time.
   - **An edited record comment** (`updated_at` ≠ `created_at`) is not skipped silently. The fold puts the issue on
     `tamper`, a hold, and writes a tamper record naming the comment. A checker re-folds the issue from the unedited
     records, and an authorised human clears the flag.
   - **Reading:** at pickup, a new holder orients itself from the folded state and the last fold's time in the claim
     ref's commits, which survive every release (§5.1). It fetches comments with `since` = that time, which returns new
     and edited comments alike [aM9].
   - **That cache is written by the releasing holder, usually the maker, so it is never trusted for a decision** [aP3].
     Re-folding from the first record is required for:
     - every exit predicate the verb evaluates;
     - every separately started checker;
     - the steward's fold before landing (§8.6).
   - **Placement:** records go on the issue whose holder must act. Cross-issue feedback from #A about #B's work is posted
     on #B, with a pointer on #A.
   - **Comment cap:** GitHub disables comments on an issue past 2,500. At 2,000 comments the verb continues the issue in
     a linked continuation issue (§5.4).
   - **Index:** the labels `review-open` and `review-verify`.
3. **On the PR/MR, as projections**, off by default: review threads, and a `factory/review` commit status for humans.
   The status is not the gate (§8.6).

**Marking.** The wrapper marks EVERY comment and body write an agent makes:

- the commands `comment-issue`, `update-issue` and `checklist`;
- `call` on the issue-comment and issue-update operations;
- every `factory:` and `merge-steward:` line.

A gate refuses an unmarked comment or body write from an agent path, and forge MCP write tools are denied to agents.
The wrapper also refuses an agent's write of a human-owned flag label in any form (§3.2) [aM4, aP11]. An unmarked
comment from the shared login can then only come from outside the wrapper: the operator's own UI, or a bypass (§15.2).

### 8.3 Human input: explicit forms only [A4, aN5, aN13, P12]

A human's comment changes state only through an **explicit form**, one per line, from an **authorised human** (§4.5), in
an unmarked comment. One comment may carry several form lines, e.g. a batch of answers. On the project's **guidance
issue** (§12.9) each line names its issue first, e.g. `/answer #12 Q-3 = 1` [aM5]. The answer recorder executes every
form, whether or not the issue has `needs-input` (§12.7, §14) [aM6]:

| Form | Effect |
|---|---|
| `/answer Q-<n> = <option>` or `/answer Q-<n>: <text>`, optionally ending in `standing` | answers a question; free text is recorded verbatim, and the next worker's question checker reads it like any input (§12.7). A standing answer is also copied to the learning-batch issue (§12.9 step 6) |
| `/approve <id>` | grants an approval of kind approval (§12.10) |
| `/amend <text>` | changes the ask, per stage as §4.3 says |
| `/stage spec-required because <reason>` | sends an IMPLEMENTATION-READY or REWORK-REQUIRED issue back through the re-spec edge (§4.2). On a TEST-READY issue the recorder posts a steward request: at its next tick the steward dequeues the issue's PRs and then applies TEST-READY → REWORK-REQUIRED. Any other target is refused with a record [aM6, aP8] |
| `/admit` | admits an outsider's issue for its current ask (§6.3) |
| `/hold`, `/unhold` | sets or clears `hold` |
| `/priority <level>` | sets the priority label |
| `/clear-tamper` | clears `tamper` after the re-fold (§8.2) |

**The fold checks every form a record cites** [aM5, aQ4]. It accepts a recorder record on issue N only when:

- the cited comment exists, is unedited, is unmarked, and has an author on the allow-list;
- the comment is on issue N itself or on the project's guidance issue;
- the line the record applies is an explicit form for issue N: on issue N a form line that names no issue or names
  `#N`, on the guidance issue a line that names `#N` first [aR7];
- the record's form and value equal that line's.

No agent path can produce such a comment through the wrapper: `/get-guidance` prints the lines, and the human posts
them (§12.9).

Every other comment, from any author including the operator, is data. It is read and judged on its content like any
input, and may well be a valid bug report or argument, but it never decides a reserved question, never approves, never
moves the ask and never changes a stage.

The same rule applies to PR/MR threads. Why authorship matters at exactly these points, and nowhere else: §12.3.

### 8.4 The normal round

1. The conductor pins the SHA and dispatches every in-session lane, each in its own subagent context, in one message.
2. Each lane writes its envelope part, which must validate.
3. The conductor folds the records: it dedupes, flags conflict candidates (overlapping anchors with different fixes)
   and posts the round's envelope, assembled verbatim from the lanes' parts.
4. The maker answers every open blocking finding in one pass.
5. Each lane verifies ONLY its own findings at the new SHA, in a fresh context, with fresh re-run evidence. A "verified"
   without fresh evidence is invalid.

### 8.5 The in-session boundary, separately started checkers, and downgrades [B6, aN9]

The conductor runs in the maker's session and posts the in-session lanes' bytes. Those records are therefore
**exactly as trustworthy as that session**:

- a conductor that drops a finding or rewrites a verdict leaves no trace;
- `actor.agent` and an in-session lane's `accept` are claims the maker's side writes.

This holds under any identity model, because one process writes all the bytes.

So **the stage exits in the table below need a verdict from a separately started checker**: a session the dispatcher
starts, which holds a `verify` claim and posts its own records. It is started by the queue row of its trigger (§14): the
verifier by `ci-pending`; every other one by `checker-requested:<lane>`, which the maker sets as it releases after its
in-session work [aM1].

**That checker calls the exit itself**, under its `verify` claim, when it re-folds all records and finds the
predicate true. Otherwise it posts its blocking findings, and the issue returns to the maker's queue [aP2]. Its verdict
is thus bound to the call, and no record has to prove which session wrote it. The exits marked "none" are recorded
trade-offs (§19 item 5).

| Stage exit | Separately started checker |
|---|---|
| START → closed | the duplicate-confirmer, every tier: closing destroys work |
| START → SPEC-REQUIRED, tiers M and L | the triage checker |
| START → SPEC-REQUIRED, tier S; START → split | none: the deterministic tier floor and duplicate retrieval check them |
| SPEC-REQUIRED → IMPLEMENTATION-READY, tiers M and L | one spec checker, by default the test-architect |
| SPEC-REQUIRED → IMPLEMENTATION-READY, tier S | none: the combined spec pass stays in-session. The code's independent check is the verifier |
| IMPLEMENTATION-READY → TEST-READY | the adversarial verifier at `ci-pending`, every tier |
| REWORK-REQUIRED → TEST-READY | the verifier on the new head, through IMPLEMENTATION-READY → TEST-READY's predicate [aM15]. The other REWORK exits lead to stages whose own exits have their checkers |
| CLOSE-READY → closed, where the project provides a read-only log query | the log-scan lane |
| CLOSE-READY → closed, otherwise, and for tier S | none: the close-out's deterministic checks (the ledger and the tag query) decide |

**Downgrades.** A downgrade of a blocking finding to non-blocking needs the raising lane's `accept` or an arbiter
decision. A finding raised by a separately started lane can be downgraded only by that lane's own record or by the
arbiter, never by the conductor.

### 8.6 The gate [B6]

The predicate's checker clause is evaluated by the verb from the folded records. Before landing, the steward re-runs
the same fold (`review_records.py fold`) on the head SHA, from the first record and never from the cached folded state
[aP3]. The `factory/review` status, which anything with push access
can set, is only a projection for humans.

### 8.7 Multi-way resolution [C22]

A **conflict set** is formed by overlapping anchors, a `regression-of` link, a maker's `conflict` answer, or an
oscillating fingerprint. Example: the Security and the DevOps reviewer flag the same code with incompatible fixes.

1. The maker posts a proposal: at most three options, each stating for EVERY finding in the set how its rule is met,
   where possible implemented on a commit.
2. Every affected lane votes:
   - accept, with evidence from its own check re-run against the option;
   - or reject, naming the unmet clause and offering a counter-option that satisfies the whole set (a constructive
     veto).
3. After two rounds without unanimity, a fresh **arbiter** agent decides, with no transcripts, only the records, the ask
   and the evidence. Its order of reasoning:
   1. facts: re-run the evidence;
   2. an option that satisfies every finding;
   3. the configured precedence of standards, by default: legal/security > data loss > the ask's criteria and
      correctness > operability > maintainability > style.
4. **The arbiter's decision is checked.** Every affected lane's deterministic checks are re-run against the chosen
   option. Whether the decision OVERRULES a legal or security finding is **computed from the records**, not judged by
   the arbiter. It does when the chosen option's `satisfies` entry for such a finding is missing, or when that lane's
   ballot rejected the option. An overruling decision becomes a `needs-input` approval; one that upholds the finding
   does not.
5. Only a genuine product decision, an irreversible or sensitive choice, or an exhausted budget reaches the human: as
   ONE five-line question, through `needs-input`.

The literature behind the low round cap: most of the gain of multi-agent debate comes from the first independent
answers (NeurIPS 2025), and reviewer–critic loops drift into false agreement unless disagreement is made explicit (2026)
(*R: review-protocol.md §6.3*).

---

## 9. The spec between workers

- **Where it lives:** the spec and the acceptance tests are committed on the pushed issue branch, with a PR that carries
  `do-not-merge`, and is also a draft where the forge supports drafts [B22]. GitHub offers drafts in private
  repositories only on Team and Enterprise Cloud; GitLab offers draft MRs on every tier. Readiness is the label, which
  the steward's hold rule already respects, not the draft flag. The implementer continues on the same branch, so one PR
  carries spec, tests and code.
- **`spec-approved` record** `{sha, ask_hash}`, written by the verb (§4.2). A later commit touching the spec, the
  acceptance tests, or the fixtures and test configuration they depend on invalidates readiness until the spec checkers
  re-approve [B19].
- **Acceptance tests at spec time.** The spec team writes the finish line as failing tests against public interfaces.
  The implementer makes them pass and may not change them, nor what they depend on, without SPEC re-entry. This is
  maker ≠ checker at the level of the issue.
  - Where tests cannot express a criterion (IaC, refactors), the spec carries a verification plan: an expected
    `cdk diff`, a smoke script, a pre-flight check.
- **A short AC list on the issue**, above the machine-owned marker (§4.3), so the human can follow the work in the
  tracker without opening the branch.
- **Optional local runtime check per project** (gap-analysis 2.1), where the project can run locally: for M/L changes
  that alter runtime behaviour, the implementation team starts the service locally and runs the same E2E group the
  deploy pipeline runs. Playwright MCP (pinned, headless, isolated, origins allow-listed) is the pilot for driving a UI
  locally [T-20]. There are no throwaway shared environments (decision U9); the gate stays the post-deploy smoke.

---

## 10. TEST-READY: batching, merge, deploy and revert first (*R: revert-and-batching.md*)

### 10.1 Batching

Two mechanisms batch changes, so there is never one wait per issue:

- **Merge:** the steward lands batches through cumulative trains and blames only the first red prefix's newest PR
  (decision U2).
- **Deploy:** the deploy pipeline deploys the latest green trunk, so one deploy carries every landing since the last
  one.

Fast-moving organisations (Slack, Amazon, Shopify's Shipit, GitHub's deploy trains, CodePipeline) handle a failed batch
deploy the same way: restore the whole batch first, then ship it again without the suspect. None of them routinely
bisects on a shared environment: every step of a bisection costs a full deploy (⌈log₂ n⌉ deploys).

### 10.2 Three clocks

| Clock | Meaning | Cure |
|---|---|---|
| Non-functional time (NFT) | the environment cannot serve | the environment restore (Track E) |
| Verification-blocked time (VBT) | no deploy containing the culprit goes green, so innocent issues cannot be verified | a fast, correct trunk revert (Track T) |
| Trunk-blocked time (TBT) | landings are paused | never pause; keep batches small while red |

Chess's 50 red hours (2026-10-31 to 11-02) were mostly VBT: CloudFormation had rolled the failing stack back.

### 10.3 Track E: the environment restore (the deploy job; needs no attribution) [B17, aN14]

1. **Pre-flight**, seconds, before anything changes: IAM simulation of the actions the new templates need,
   export-in-use check, change-set validation.
2. **Deploy** with a result per stack. Independent stacks keep deploying after one fails, so a deploy shows more than
   one defect. Every migration the deploy runs is appended to the **migration ledger** (the deployed SHA, the
   migration's id, and whether it is expand-only), stored beside the cache.
3. **Smoke**, retried once.
4. **On a failure**, the job restores INSIDE THE SAME RUN, in the same concurrency slot (a separately dispatched restore
   could be superseded by a pending deploy):
   1. it takes the last green commit's cloud assembly from the cache, and verifies the assembly's SHA-256 against the
      digest stored in the S3 object's own metadata, which only the deploy role writes;
   2. it computes the restore's change set and runs the **stateful replacement/deletion detector on it**. It also reads
      the migration ledger: a migration since the last green commit that is not expand-only means old code would run on
      a migrated schema. Either case STOPS the restore, which becomes an `env-incident` for the owner (§12.5);
   3. otherwise it redeploys only the stacks whose template changed, consumers before producers, with
      `cdk deploy --app <cached assembly> <stack> --exclusively`;
   4. it runs the smoke again.

   **The run's pinned verdict has four outcomes**, written to the job and step results and read through the jobs API
   (§4.2) [aM3, aP10]:

   | Outcome | When | Counts as |
   |---|---|---|
   | `green` | deploy and smoke succeeded, no restore step ran | the only verdict that verifies (TEST-READY → CLOSE-READY) |
   | `red` | the deploy or the smoke failed and no restore ran | a red deploy: `red-since`, Track T |
   | `restored` | the deploy or the smoke failed, and the restore ran, whatever its own outcome; records `<env> serving <sha> (restored)` (H3) | a red deploy: `red-since`, Track T |
   | `skipped or refused` | the deploy guard of §10.4 step 4 skipped the commit, or the dispatch was refused | neither green nor red: no `red-since`, no attribution, never a "same signature" red |

   The run concludes `failure` for every outcome but `green`, so a skipped or restored run can never look green.
5. **Last-good also red?**
   - If the restore's change set held no stateful change, the cause is infra, drift or a flake, and nobody is blamed
     (the "passes without" test, for free).
   - Otherwise it is an `env-incident`: a culprit with persistent side effects must not pass as infra.
   - An `UPDATE_ROLLBACK_FAILED` stack gets one automatic `continue-update-rollback`, never with skipped resources, and
     then becomes an `env-incident`.

A naive revert rebuilds everything: chess's deploy job took a median of 94 min. The restore needs neither a build nor
synthesis.

### 10.4 Track T: the trunk revert (the steward; needs attribution)

1. **Classify infra first:** credentials, throttling, quota, runner loss, an `AccessDenied` on an action no PR in the
   window newly uses, a red restore without stateful change, a failed rollback. None of these blames an issue. The
   same classifier confirms an "environment" rework classification (§4.2) [tN10].
2. **Attribute**, stopping at the first conclusive step [B16, C3]:
   1. one landing in the window: that is the culprit;
   2. **a deploy-stage failure:** the window's cumulative states are the steward merge commits on trunk's first-parent
      history (the train branches are deleted after landing). The attributor synthesizes each, on CI, bounded in time.
      - If EXACTLY ONE step changes the failing resource R, or removes the named export or permission, and no other step
        changes R's dependency closure (the roles, policies and imports it references), that step is the culprit, with
        high confidence.
      - If several do, they form a suspect set (step 5);
   3. a pre-flight failure names the step itself;
   4. **a smoke failure:** drop the PRs that produce an identical cloud assembly and touch no deploy footprint, then rank
      the rest by overlap with the failing checks. The log-reading attributor only ranks inside this set and never
      reverts outside it [C15];
   5. still ambiguous: revert every suspect.

   A failure's **signature** = (stack, logical id, status reason with ids masked). It decides whether a later red is
   "the same" failure.
3. **Revert** [B14, aN7, aN8]:
   - The steward opens `git revert -m 1 <merge>` as a PR that declares `Reverts: PR #<k>`. If GitHub refuses to let the workflow create the PR, that is
     an immediate `env-incident` naming the setting (§3.5, H11), not a red streak.
   - On GitHub a PR created with `GITHUB_TOKEN` starts no workflow, so the steward dispatches the revert PR's CI itself
     with `workflow_dispatch`, the one event that token may start.
   - The CI exemption and the revert-first ordering in `plan()` apply only to a PR that the steward's identity opened
     AND whose head is exactly `git revert -m 1` of a first-parent steward merge. A label alone never qualifies, so a
     worker cannot jump the queue by labelling its own PR.
   - **Revert and reland facts** [aM2, aP1, aP7]. When the steward lands a PR, it writes one of these into its own
     first-parent merge commit, and that trailer, never a trailer on a PR's commits, is the fact (H1):
     - `Steward-Reverts: PR #<k> <merge sha>` when the PR **declares** the revert and the content **confirms** it. The
       declaration is `Reverts: PR #<k>` in its body, or GitHub's revert-button body "Reverts <owner>/<repo>#<k>". The
       content check: the PR's net diff is exactly the inverse of PR k's steward merge. Who opened the PR does not
       matter, so the operator's revert button and a worker's revert count as well as the steward's own. A declared
       revert the content does not confirm, or an exact inverse nobody declared, is recorded as a candidate on PR k's
       issue and changes no stage. Small changes that merely toggle a line back are thus never mistaken for reverts.
     - `Steward-Relands: PR #<k> <revert merge sha>` when the landed PR contains a commit that exactly inverts a
       `Steward-Reverts` merge of PR k: the steward's own reland of a suspect, or the first commit of a culprit's
       rework branch. A merge that inverts a revert is therefore a reland, never a revert.
     - A PR's state is the last of its facts: landed, reverted, relanded (§4.2).
     - A revert fact returns PR k's issue from TEST-READY, CLOSE-READY, or closed by reopening it (§4.2).
     - A partial revert is an ordinary change, not a revert fact (§19 item 13).
   - Landings never pause; while red, a batch is capped small (the revert plus at most k PRs).
   - **The deploy after a landing is the trunk `push` run** that the steward's deploy-key push starts, pinned by its
     `head_sha` (§4.2). The steward no longer dispatches one, which would deploy every landing twice [aQ3]. It
     dispatches a deploy only to re-verify (`reverify`), and records the run id from the dispatch response
     (`return_run_details: true` under API version `2022-11-28`; always returned from `2026-03-10`) as
     `dispatched run <id> for <sha>`, which the pinned verdict reads (§4.2) [aM3, aP15].
4. **Deploy guard** [C18, aQ1]: the deploy job deploys only trunk's tip (H15). While a revert is pending it also skips a
   tip that contains an attributed culprit without its revert. The environment stays on the restored version instead
   of being broken and restored again by every deploy. If the revert PR cannot be created, the `env-incident` of step 3
   names the cause at once.
5. **The next green deploy** confirms the attribution and verifies the innocent landings by ancestry. A red or restored
   one with the same signature means the attribution was wrong (a skipped one is neither, §10.3) [aP10]: revert the next suspect, and **refund** the counters the wrong
   attribution charged to the innocent issue (§13) [B16].
6. **Escalate** after two wrong attributions in a row, or after a red streak longer than the configured clock (suggested
   4 h), by opening an `env-incident` issue (§12.5) [B13].

### 10.5 How issues react [B11]

**A red deploy or smoke verdict marks no issue by itself.** It records `red-since` and hands the window to Track T. Only
Track T's culprit record returns an issue; today's blame-all return is removed (H8).

| Role in the red window | Effect |
|---|---|
| Culprit | → REWORK-REQUIRED (steward). The `reverted PR #<n> <merge> in <revert>` line names the PR; the `Steward-Reverts` trailer is the fact. The rework branch starts with a revert of the revert, because git brings nothing back when a reverted merge is merged again. Landing it writes `Steward-Relands` for the culprit's PR, and the rework record names the new PR as its successor [aP1] |
| Culprit whose fix needs a grant (e.g. an IAM action) | as above, plus `needs-input` of kind approval: the human is asked only for the grant |
| Innocent in the window | stays in TEST-READY, untouched; the next green deploy containing it verifies it; no rework, no re-landing |
| Reverted as an ambiguous suspect | stays in TEST-READY. The steward relands it itself, in bisection order, and the reland writes `Steward-Relands` for the suspect's PR [aP1]; no worker involved |
| Landed after the red began | unchanged (the existing red-streak rule) |
| Infra red | no issue changes; an `env-incident` issue with its owner |

### 10.6 What each AWS project provides

| Tier | The project provides | NFT after a smoke failure |
|---|---|---|
| **Minimum (REQUIRED, decision U20)** | cached cloud assemblies per deployed SHA, each with its SHA-256 in the object's metadata; a deploy script that redeploys named stacks from a given assembly; a per-stack result file; the **stateful replacement/deletion detector** and the **migration ledger** (§10.3) [aN14]; CloudFormation rollback on; ECS deployment circuit breaker; custom-resource timeouts; an IAM action manifest; a smoke check that runs standalone | est. 5–30 min (against 1.5–3 h today) |
| Better | stateful stacks split out with stack policies; the smoke for user-facing entry points as pre-traffic hooks (traffic never reaches a broken version); expand–contract migrations | ≈ 0 for hooked components |
| Best | blue/green with bake time for all compute; feature flags | seconds |

**The cache** [B17]:

- It lives in an S3 bucket in the dev account, with retention at least the `cdk gc` rollback buffer (decision M1).
  Chess already hit the GitHub artifact storage limit.
- **Only the deploy job's role may write it.** The digest sits in each object's metadata, written by that role, so no
  issue comment is involved. A forged or missing digest makes the restore refuse, which is a denial of service, not a
  corruption.

### 10.7 Prevention in the train (before the shared deploy)

These checks keep deploy-breaking changes out of the shared deploy:

- export-in-use compatibility;
- IAM simulation for the deploy role;
- the stateful replacement/deletion detector;
- the expand–contract migration lint;
- a revert-safety check on revert PRs.

**Replay of chess #566.** The export check would have refused it in the train: 0 h red. Without the check, the design
gives about 2.5 h red, against about 44 h after the cause was known [C19]. That figure assumes:

- the revert lands on its train CI alone, using H10's dispatch;
- no steward tick is lost;
- one deploy of about 94 min plus the restore.

### 10.8 Hazards in today's code and setup that revert-first triggers (fix together with it)

- **H1. A reverted culprit gets closed** [B15, aN7].
  - **Today:** the verdict verifies an issue when its last landing line names an ancestor of the deployed commit. A
    reverted landing stays an ancestor, and `last_landing` takes the newest line of ANY PR.
  - **Fix:** landings, reverts and relands are recorded per PR and read ONLY from trunk's first-parent steward merges:
    `Steward-PR`, `Steward-Reverts`, `Steward-Relands`. A PR's state is the last of them. The predicate holds only when
    every PR of the issue is landed or relanded, or is replaced by a later PR of the issue. A revert counts from the
    moment it lands, and returns the issue from TEST-READY, CLOSE-READY, or closed [aP1].
- **H2. Re-merging a reverted merge brings nothing back** unless the revert is reverted first.
- **H3. A restore must not count as a trunk verdict:** record `<env> serving <sha> (restored)`.
- **H4. A separately dispatched restore can be superseded** by a pending trunk deploy, so it runs inside the failing run.
- **H5. A revert can itself be undeployable:** a later landing imports the export it removes, or it undoes a migration.
  The prevention checks also run on reverts.
- **H6. Serial stack masking hides later defects:** a result per stack, and independent stacks keep deploying.
- **H7. Forged machine lines and forged trunk history** [B7, aN7].
  - **Today:** any commenter can post `merge-steward: landed <sha>`, and the code ignores the author.
  - **Fix, first part:** landings come from trunk history; comments are projections.
  - **Fix, second part, trunk itself** [aN7, aP5, aP6]:
    - **on the protected tier (H12)**, only the steward's trunk credential can push trunk. That is a deploy key in an
      environment limited to the default branch, or GitLab's hidden, protected bot token;
    - **on every tier, an independent check** confirms each first-parent landing: the steward verifies, from the
      activity record (`GET /repos/{owner}/{repo}/activity`, filtered by the trunk ref and push activity; GitLab: the
      push events of the protected trunk), that the push was made with the steward's credential. Any other push is an
      `env-incident` that stops landing (§3.5). On the detected tier that is detection after the fact, and a branch
      workflow that reads the deploy key from the repository secrets looks like the steward (§15.2).
  - Parsing machine lines only from the steward's identity is a third layer: a workflow on a worker's own PR branch can
    also post as `github-actions[bot]`.
- **H8. Blame-all red verdict:** removed (§10.5) [B11].
- **H9. The watcher closes issues itself** [B12, aN1]. `verify_issue` never closes. The watcher records a verification
  fact naming the pinned run; the steward's next tick applies TEST-READY → CLOSE-READY; the close-out team closes.
- **H10. Steward-opened PRs get no PR CI on GitHub** [B14]: the dispatch, the CI exemption and the ordering of §10.4 step
  3.
- **H11. Actions may not create PRs on a new personal GitHub repository** [aN8, aM14]: setup and update enable and
  check the setting with the operator's token. The steward detects a refusal at revert time and opens an `env-incident`
  at once (§3.5).
- **H12. GitHub trunk is unprotected** [aN7, aP5]: the protection tiers of §3.5. Where the plan allows it, a ruleset
  lets only the steward's deploy key push trunk; elsewhere the per-tick check detects every other push.
- **H13. The verdict trusts an argument** [aN10, aM3]: `verdict --conclusion` is replaced by the steward reading the
  pinned deploy verdict: the pinned run's first attempt, and its deploy and smoke job conclusions from the jobs API
  (GitLab: `include_retried=true`) (§4.2) [aQ7, aR6].
- **H14. A queued PR that the steward cannot push stalls every train** [aP5]. `Git.run` raises on the train push. A
  `GITHUB_TOKEN` may not push a change to a workflow file, so a queued PR touching `.github/workflows/` would fail
  every tick. The fix has two parts:
  - The steward pushes its train refs as well as trunk with its deploy key, which can push workflow-file changes (to
    verify, O14).
  - A push refusal no longer fails the whole tick, and it is classified [aQ8]:
    - a refusal that names content (a file over the forge's size limit, a push-ruleset path rule) drops the newest PR
      of the first refused train with a named reason (`queue-failed`); the trains are cumulative, so that PR is the one
      that added the refused content;
    - an authentication, permission or transport refusal, or one whose cause the message does not name, is an
      `env-incident`, and that tick lands nothing. A lapsed key thus never empties the queue.
- **H15. The deploy deploys any commit reachable from trunk** [aQ1]. The deploy template's `workflow_dispatch` takes a
  `sha` input, and `deploy_guard` accepts any ancestor of trunk. Since worker tokens keep "Actions: write", a worker
  could dispatch the trunk deploy with an intermediate commit of a landed PR, which no checker reviewed alone, or with
  an older trunk commit, and run it with the production role. The fix:
  - the deploy takes no commit input;
  - its job deploys only when its commit is trunk's tip, read when the job starts; otherwise it concludes `skipped or
    refused` (§10.3). That also covers a queued run of an older commit;
  - the check is the deploy job's FIRST step, run from a checkout of the default branch (the steward's copy), before the
    job checks out the commit to deploy and before any step that uses the role. A re-run of only the deploy job
    therefore runs it again; a check in a separate job would be skipped, because a single-job re-run reuses the other
    jobs' results (GitHub Docs, "Re-running workflows and jobs") [aR2];
  - runs of the old workflow file stay re-runnable for 30 days. GitHub has no environment rename, so the rollout
    creates a new production environment, copies the old one's deployment-branch policy and variables, has the
    operator re-enter each secret from its source (the API returns no secret values), points the role's trust at the
    new environment's subject, and deletes the old environment [aT2]. On the protected tier no run
    of the old file can then assume the role [aR2, aS3]. On the detected tier, which has no environments, old-file runs
    stay re-runnable under the ref-subject trust for those 30 days, part of that tier's stated residual (§15.2 item 5);
  - the restore of §10.3 needs no input, because it takes the last green assembly from the cache.

Not fixable by a faster revert: a failed rollback, an irreversible migration, a replaced stateful resource. These need
the prevention checks, the restore guard and an owner.

---

## 11. CLOSE-READY (decision U18)

CLOSE-READY is NOT code clean-up. Anything that changes code or other repository assets needs a PR and the machinery of
TEST-READY. Dead-code and unnecessary-code checks therefore run in the implementation team, on the diff, before the PR
(§7.2).

**Scope:**

1. **Local and temporary clean-up** [B20]:
   - temp files the agents created;
   - local and remote branches no longer needed;
   - worktrees;
   - temporary test and verification infrastructure: test users, staged uploads, probe stacks.

   Every temporary resource is **tagged** `factory-issue=<repo>#<n>`. It is also named with the prefix
   `factory-issue-<repo>-<n>` where the resource type has no tags, or where an action on it cannot be conditioned on
   tags (S3 objects, below) [tP3]. Each team also records it in a temporary-resource ledger on the issue (one machine line per
   resource: kind, id, environment, created-by). CLOSE-READY removes what the ledger names AND what a query by the tag
   finds. The exit predicate requires both to be empty.

   **Every team that creates temporary AWS resources, and the close-out that removes them, holds credentials bounded to
   the issue's own resources, action by action** [tN1, tM1, tP3]:
   - **tag-conditioned where the action supports it:** create only with the issue's `factory-issue` tag
     (`aws:RequestTag`; S3 objects: `s3:RequestObjectTag`), delete only resources carrying it (`aws:ResourceTag`);
   - **otherwise scoped by resource name:** S3 objects cannot be deleted or overwritten on a condition of their existing
     tags (Amazon S3 User Guide, "Tagging and access control policies"), so their put and delete are granted only on
     the key prefix `factory-issue-<repo>-<n>/` in the policy's resource ARN, and so is any other action that cannot be
     conditioned on tags;
   - **otherwise not granted** to an agent session at all.

   The close-out reads no logs directly. It still reads issue text and the log-scan lane's finding excerpts, so
   untrusted text and AWS write credentials meet only under credentials scoped to the issue's own tagged resources
   (§15.1 rule 5).

   Chess #1130 is the motivating case: it left 1,000 staged uploads, which nobody recorded, and they later blocked other
   issues' deploy checks.
2. **New issues uncovered by the deployment, even a successful one,** under the filing discipline (observed defects
   only; zero is a valid result). The sources:
   - the **log-scan lane**: a separately started, read-only lane with no AWS write credentials. It scans the deploy
     window's logs, where the project provides a read-only log query, and emits finding records that the close-out
     reads as data [T-13, tN1];
   - the lanes' `notVerified` entries;
   - the verifier's observations.
3. **Learnings and documentation** [T-12, C8]:
   - **Every learning goes to ONE rolling learning-batch issue**, never to machine-local memory. A worker on another
     machine would never see that memory (P1).
   - The learning-batch issue covers docs, `docs/lessons-learned.md`, steering files and rule proposals, as records.
   - It is worked like any tier-S issue when it has collected enough items, or once a day. Many issues' learnings thus
     land in one PR, not one follow-up PR each: such follow-up PRs were 40 % of chess's PRs, and each cost a trunk run.
   - When its PR is enqueued, the batch issue rotates: the next items go to a new batch issue.
   - It does not count against the empty backlog, and its own close-out captures no learnings.
   - This mechanism is the designer's proposal (decision M5).
4. **A structured close-out summary on the issue:**
   - what was asked and built;
   - the evidence;
   - the landing and deploy;
   - the checkers' outcome, including every `notVerified` entry;
   - temporary resources removed;
   - issues filed;
   - learnings recorded;
   - residuals.

   The human reads it in the tracker or in the digest (§17), because the operator rarely returns to sessions.

Exit predicate: §4.2.

---

## 12. Human input (decisions U1, U12, U14, U17, U21, U24)

### 12.1 The `needs-input` lifecycle

- **Blocking question:** set `needs-input`, release the claim, pull other work. No unattended worker ever blocks on an
  interactive question. Asking interactively stays only in a session the human is actively driving.
- **Reversible decision:** proceed with the recommended option and record it as an assumption the human may override
  (decision U12). An override after the spec stage becomes REWORK-REQUIRED or SPEC-REQUIRED; after the landing, a new
  issue.
- **Format:** every question is a record in the five-line shape of `clients/claude/rules/continuous-work.md` (one line
  of context, two to four options with consequences, the recommended option first), with an id `Q-<n>` and
  blocking/non-blocking. Its text ends with the answer form to use, e.g. `/answer Q-3 = 1`.

### 12.2 Decision inventory, up front

At START and at SPEC entry, the maker lists EVERY decision and human input the issue will need through to CLOSE-READY:

- product choices;
- inputs (accounts, data, folders);
- permissions;
- sign-offs.

All of them go out in ONE batch. A question raised later must state why it was not foreseeable. A foreseeable late
question is a defect of the spec stage, recorded in the retro.

### 12.3 Equal scrutiny, and why authorship still matters for reserved decisions [A4, aN5, P12]

Every input is judged on its content: the operator's, an agent's, an outsider's (decision U21). An answer from the
operator does not skip a checker. When it leads to an artefact, that artefact faces every lane like any other, and a
`/stage` request passes the same predicate as an agent's call. An outsider's comment can be a valid bug report and is
read as one.

Authorship decides only WHO may make a **reserved decision**. A reserved decision is a question the question checker
(§12.4) found no agent may answer:

- irreversible;
- sensitive;
- a genuine product decision;
- a grant or an approval.

It matters there for a reason that has nothing to do with trusting the operator more:

1. **Maker ≠ checker for decisions.** A decision is reserved because no agent may make it. If an agent's comment could
   answer it, the agent that escalated the question would answer its own escalation. The design's own rule says it may
   not. This is why only explicit forms count (§8.3), and why the wrapper marks every agent write (§8.2): an ordinary
   agent note can never pass as an answer. A form counts only when an authorised human posted it, unmarked;
   `/get-guidance` only prints the lines the human then posts (§12.9) [aM5, tP2].
2. **Outsiders.** On a public repository any signed-in user can comment. Their text is data, never a decision on the
   project's behalf (§8.3).
3. **Irreversible operations** (a production deploy, a deletion, an IAM grant). Under U24 no forge-side check can tell
   the operator from an agent. What guards these operations is credentials no agent session holds:
   - **on the protected tier**, the production deploy runs only in CI and only trunk's tip, because its AWS role trusts
     only trunk's OIDC subject and the deploy job refuses any other commit (§15.1 rule 5, H15) [aQ1, aQ2]. A worker
     token can still dispatch, re-run or cancel a trunk workflow, so WHEN a deploy runs is a standing permission
     (§12.6). **On the detected tier** this guard does not hold: any worker token can push trunk, and the push runs
     the worker's code with the deploy role (§15.2 item 5);
   - deletions and IAM grants beyond the issue's own temporary resources need AWS credentials no agent session holds
     (§11, §15.1 rule 5);
   - approving a protected deployment and administering the repository need token permissions the worker tokens lack
     (§15.2).

   Beyond those, the operation is protected only by the reserved decision, whose authorship U24 cannot prove (§15.2).
   The forges' own approval features do not change this:
   - GitHub's "prevent self-review" cannot be used under one account, because the agents start deployments as the
     operator.
   - GitHub required reviewers on private repositories need GitHub Enterprise: on Free, Pro and Team they exist only for
     public repositories (GitHub Docs, "Managing environments for deployment").
   - GitLab deployment approvals need Premium or Ultimate, and by default the user who triggers a pipeline may not
     approve it.
   - GitLab fine-grained personal access tokens exist only from GitLab 19.2; before that the `api` scope is full
     access.

Everything else, including answers to non-blocking questions, findings and comments, is judged on content alone,
whoever wrote it.

### 12.4 The question checker (maker ≠ checker for questions) [C12]

Before anything reaches the human, a separate agent tries to answer it from the spec, the issue, the codebase, the
docs, the decision records and the steering. It writes one question verdict per question (§4.5). Only these pass, the
four Proven Exceptions of `continuous-work.md`:

- irreversible;
- sensitive;
- a genuine product decision;
- a hard blocker.

A deterministic **always-ask list** passes regardless of the checker's view: IAM grants, deletions of data or
resources, anything touching production, credentials. A false "answerable" on those would let an agent decide what is
reserved.

### 12.5 Routing by kind; environment incidents [B13, aN3]

Environment health, credentials and dependency or contention never become an issue's question.

| Kind | Goes to |
|---|---|
| Environment health, credentials | ONE open issue per root cause, labelled `env-incident` and `needs-input` for its owner, deduped across issues. The affected issues are `blocked-by` it, and released when it closes |
| Dependency, contention | `blocked-by #N`, or the merge steward |

**`env-incident` issues are not factory work items:**

- they have no stage and are in no worker queue (§14);
- their owner is on the human allow-list; the fallback owner is the operator;
- they reach the human through `/get-guidance` and the digest;
- the steward, the watcher or any team may open one (§4.5).

The `delivery-status` issue stays what it is today: a closed issue whose body is the steward's machine status record. It
never carries escalations.

Example from the data: the same Security Hub finding (SSM.1) was asked about from four different issues.

### 12.6 Standing permissions are policy

Examples:

- "the steward may dispatch the prod deploy after a green stage" [tP5];
- "agents may change IAM in the shared dev account".

They are asked once per project and recorded as a decision record or steering line, never per issue again. Worker
tokens can dispatch, re-run, cancel, disable and enable workflows and their runs, so who may do that to a deploy is such
a policy [aR4]; the pinned
verdict does not depend on it, because it reads the pinned run's first attempt (§4.2) [aQ7].

### 12.7 Recording answers [B4, aN3, aN13]

Only explicit forms count (§8.3), posted by an authorised human either on the issue itself or on the project's guidance
issue (§12.9), where each line names its issue. The recorder applies each guidance-issue line to the issue it names.

- **The recorder.** The dispatcher lists issues, with or without `needs-input`, that have an explicit form from an
  authorised human newer than the recorder's last run on that issue, counting the guidance-issue lines that name
  them, and starts the **answer recorder**, a headless role [aM6].
  - The recorder holds a `record` claim and executes each form as §8.3's table says:
    - an answer becomes a `factory: answer Q-<n> = <option or text> (by <login>, comment <id>)` record;
    - an `/amend` or `/stage` takes the re-spec edge, or becomes a steward request on TEST-READY;
    - a flag form sets or clears its flag.
  - It writes `factory: recorded through comment <id>`, and clears `needs-input` when no blocking question is left.
  - It interprets nothing: free text is recorded verbatim, and the next worker's question checker reads it like any
    input.
  - A comment that is not an explicit form never starts it, and a partial answer starts it once, not on every poll.
  - The fold re-checks every form a record cites (§8.3), so a recorder record counts only when its comment does.
- **`/get-guidance`** (§12.9) helps the human write those forms; it posts nothing itself.

### 12.8 A human review task is one sheet

When the human must judge many items (e.g. 107 sentences), the items form ONE artefact the human completes in one
sitting, not a stream of questions.

### 12.9 `/get-guidance`

Run by the human when there is time; the same prompt on Kiro.

1. **Collect** across issues (later across projects), in order:
   1. blocking questions and approvals;
   2. "stuck" reports from the budgets;
   3. open `env-incident` issues the human owns;
   4. non-blocking assumptions the human may override.
2. **Dedupe** the same decision across issues.
3. **Ask** one item, or a small batch, at a time.
4. **Print** the answers as ONE block of explicit form lines, each naming its issue (`/answer #12 Q-3 = 1`), quoting
   the human's words for free text [aM5, tP2]:
   - the human posts that block as one comment on the project's **guidance issue**: a closed issue kept for this, like
     `delivery-status`, which setup creates and locks, so that only collaborators can comment (GitHub Docs, "Locking
     conversations") [aQ11];
   - a mistake is corrected by posting a corrected block, never by editing one: an edited comment fails the fold for
     every line in it (§8.3) [aQ11];
   - the command posts nothing and holds no claim. The answer recorder applies the lines to their issues (§12.7);
   - it works the same on every client, so it needs no prompt-submit hook, no mark and no extra gate.

   Under U24 the human authorship of such a comment is still not provable by the forge (§15.2).
5. **Stage changes** go into the same block as explicit forms (`/stage #12 spec-required because …`), which the
   recorder executes like any other; otherwise the next worker in the stage reads the answer.
6. **Generalise:** offer to mark a general answer as standing (`/answer #12 Q-3 = 1 standing`). The recorder copies a
   standing answer to the learning-batch issue (§11), whose PR lands it as a decision record or steering line, so it
   is not asked again.
7. **End** with a fixed summary, which repeats that the block is posted once and corrected by a new block, never
   edited. The command can be stopped at any point, because all state is on the issues.

### 12.10 Optional approval setting (decision U17) [T-07, tN9]

Off by default; no stage requires a human. A project that needs one (e.g. a bank, or AI-DLC's "implements after a human
validates") switches it on for:

- **specs** of tier M/L or with chosen risk tags: a clause of SPEC-REQUIRED → IMPLEMENTATION-READY;
- **sensitive paths** of a PR, e.g. `iam/**`, `auth/**`: a clause of IMPLEMENTATION-READY → TEST-READY and of
  REWORK-REQUIRED → TEST-READY. It covers paths the spec did not declare. The recommended set includes the privileged
  automation of §3.5 (`.github/workflows/**`, the steward's and the deploy pipeline's scripts and local actions,
  `templates/ci/**`), so that a project that switches approval on puts a human on the automation that guards it
  (§19 item 14) [tQ2].

The approval is an explicit `/approve <id>` from an authorised human. It is asked as one batched `needs-input` of kind
approval, which `/get-guidance` collects, while independent work continues. It is a reserved decision (§12.3).

**Limit under U24:** the approval's human authorship is not provable, because the agents post as the same login
(§15.2, §19 item 4). A project whose auditors need provable approval must revisit U24 (a separate agent identity), or
bind the approval to a forge-native gate that its plan offers and that the operator alone can pass.

### 12.11 The data behind §12 (*R: questions-data.md, thresholds.md §M6*)

- 51 of 133 issues worked on one machine since 2026-10-01 asked the human. 55 % of those asked in more than one
  episode, with a median of 10.2 h between episodes.
- Waiting for answers: a median of 28 % of an asking issue's span, 58 % at p75.
- Of the 95 questions asked ≥ 8 h after an issue's first, only 3 were genuine late design decisions. The rest:

| Kind | Count |
|---|---|
| One review task asked item by item | 38 |
| Environment health | 23 |
| Dependency or contention | 8 |
| Credentials | 7 |
| Standing permissions | 6 |
| Release sign-off | 5 |
| Inputs that belonged in the first batch | 3 |
| Review cap | 2 |

---

## 13. Budgets and bounce counters (*R: thresholds.md*)

Several counters run per issue and their trip rates add up. Each therefore has two limits:

- a **soft** limit (about p90–p95) that triggers an automatic corrective step;
- a **hard** limit (about p99 or above the observed maximum) that sets `needs-input` with a "stuck because …" record
  naming the counter, its value, the last three causes and a recommended option. That record is the proof that the
  agents tried.

| Loop | Soft (automatic) | Hard (human) | Hard ≈ |
|---|---|---|---|
| S spec review | 2 → approve with residuals | 3rd pass still has an open A | > p99 |
| M / L design review | 4 / 6 → approve with residuals | open A at the cap, or no progress over 2 iterations | p90–p99 |
| SPEC ↔ needs-input | 2 → batch questions with defaults | 3rd blocking episode | p99 |
| Verifier (refute → fix) | 3 → fresh verifier and implementer; S re-tiers to M | 6th round still refuted | > p99 |
| PR CI red rounds (per PR) | 2 → classify infra vs change | 5th change-caused red | p99.75 |
| Merge-queue returns (issue lifetime) | 2 | 4th | p99 |
| Culprit deploy failures | 1 → revert first | 2nd | > p99 |
| Total rework rounds | 2 | 4th | p99 |
| Claims without progress | 3 → a different worker next | 5th | p99.2 |
| Cost per issue S / M / L | $300 / $1,000 / $2,500 → re-plan, consider a re-tier | $500 / $2,500 / $4,000 | soft ≈ p90; hard ≥ max (S, L), p98 (M) |
| Elapsed time | digest alarm at 48 / 96 / 168 h | none: an expired lease reclaims the issue | — |

**Where the counts come from** [C21, T-02, tN3, aN15]:

- Counters are derived from the verb's audit lines and the steward's records. Those are comments and so editable: an
  edit trips `tamper` (§8.2), and a deletion is the residual of §19.
- **Spend:** every role that runs an agent context appends
  `factory: spend model=<id> tokens=<n> usd=<x> writes=<n> step-seconds=<n> by <role>/<agent>` at each checkpoint and
  at release, from its harness's usage report and the wrapper's write counter. The verb sums these lines per issue, so
  the cost budget can trip across machines and sessions.
  - `model=` gives cost per model (§17).
  - `writes=` measures the REST write budget (§15.2).
  - `step-seconds=` sets the lease L (§5.1).

**Calibration** [C6, tN4]:

- The cost, bounce and claim thresholds come from single-session flows with about 97 % cache reads. Each hand-off and
  each cross-session lane starts cold, so the new flow will cost more.
- For the first 20 issues per tier, THOSE counters are **report-only**; then they are recalibrated from the spend lines.
- **The review caps of `proportionality.md`** (S 2, M 4/2, L 6/3) are today's enforced rules and stay enforced
  throughout.

**Resets:**

- per stage visit: review, verifier and question counters. Re-entering SPEC gets half the cap, so REWORK ↔ SPEC
  ping-pong gets no fresh budget.
- per PR: CI rounds.
- never by a worker: queue returns, culprit failures, rework, claims and cost. Only an authorised human's explicit
  answer raises the limit of the counter that tripped.
- **Refunds:** a wrong attribution (§10.4) refunds the counters it charged [B16].

**What does not count as a bounce:** infra failures, flakes fixed by a re-run of the same SHA, landing into an
already-red environment, and conflicts an automatic rebase resolves.

**Expected escalation rate from budgets:** about 2–3 %, falling towards 1 % with culprit-only attribution (measured for
the tracker counters alone: 1.3 % pooled). Today's time tripwires do not fit elapsed time (89 % of S issues take more
than 3 h from claim to merge, mostly waiting), so any time budget counts active time only.

---

## 14. Scheduling: the dispatcher

Hand-offs between stages are safe only if something guarantees a role for all pullable work. Decision A2 of 2026-11-02
("the session owns its PR until it lands") was taken because hand-offs stranded: 0 of 10 closed, since no one picked
returned work up.

**A2 is reversed, and `check-handoff` superseded, only once the dispatcher runs on a host (O12)** [tN11]. Until then, a
session keeps its PR until it lands, as today.

- **Polling, not webhooks:** a workstation cannot receive forge webhooks (*R: webhook-triggers-analysis-2026-11-06*, in
  `docs/reports/`). The dispatcher polls the tracker every few minutes. It runs the reconciler (§4.4) and the reaper
  (§5.2), closes `split` parents whose children are all closed, releases `blocked-by` whose target got there, and counts
  pullable work in these **queues** [B3, B4, aN3]:

| Queue | Pullable when | Role started |
|---|---|---|
| one per worker stage (START, SPEC-REQUIRED, IMPLEMENTATION-READY, REWORK-REQUIRED, CLOSE-READY) | no claim (absent or `free`, §5.1); none of `hold`, `needs-input`, open `blocked-by`, `ci-pending`, `review-verify`, `checker-requested`, `split`, `env-incident`, `tamper` | the stage's maker team |
| one per checker lane | no claim; `review-verify` with a resolution waiting for that lane, OR `checker-requested:<lane>` [aM1]; none of `hold`, `needs-input`, open `blocked-by`, `tamper` | that lane, with a verify claim (§5.3) |
| verifier | no claim; `ci-pending`, and the PR's CI run has ended OR the `ci-pending` timeout has passed; none of `hold`, `needs-input`, open `blocked-by`, `tamper` | the adversarial verifier, which completes or refuses IMPLEMENTATION-READY → TEST-READY (§4.2) |
| re-fold checker | no claim; `tamper` without a re-fold record since it was set [aM13] | a checker that re-folds the issue from its unedited records and posts the result, for the human's `/clear-tamper` |
| answer recorder | no claim; an explicit form from an authorised human newer than the recorder's last run on that issue, on any issue including `env-incident` ones [aM6, aM13] | the answer recorder (§12.7) |

Every row requires "no claim", so a lane or the recorder is never started while a worker still holds the issue [aM13]. TEST-READY has no worker queue: the steward re-derives both its exits for every TEST-READY issue on every
tick (§4.2) [aM8]. `env-incident` issues are in no worker queue; they reach their owner through `/get-guidance` and the
digest, and the recorder executes forms on them.

- **Pull order:**
  1. a START issue authored by a factory login with `Origin: production` (§6.1), and anything with
     `priority:critical`, whatever its stage [T-09];
  2. then right to left: REWORK-REQUIRED, the lane, verifier and re-fold queues, CLOSE-READY, IMPLEMENTATION-READY,
     SPEC-REQUIRED, START;
  3. then priority within a queue.

  The human sets priority with `/priority` (§3.2) [tP5]. While trunk is red or nothing is ready for implementation, workers write specs
  rather than idle (decision U8).
- **Footprint-aware selection:** between equals, prefer an issue whose declared footprint does not overlap work in
  flight. The steward already does this inside a batch.
- **Capacity** per role and per host is configured.
- **Host and worker start are open** (O12) [T-03]. The candidates:
  - Kiro Crew (cron, a heartbeat crew);
  - headless CLI runs on CI runners;
  - a scheduled task on a workstation.

  For each client, the design still needs the command that starts a worker with a role and an issue, and the
  governance it inherits: the same rules, hooks and tool allow-lists as an interactive session [T-17]. Its token scope:
  contents write (claim refs), issues write (repairs, the `split` close, `blocked-by` releases) [B9], and actions read
  for the steward's liveness check (§3.5; GitLab: a read scope for the pipeline schedule) [aT1, aU2]. For the
  source-record check of `priority:critical` (§3.2) it also holds a read-only AWS role that can read only alarm states
  and AWS Security Agent findings in the project's accounts, held by the dispatcher's host alone [tQ1].

---

## 15. Tools, trust and identity (*R: mcp-and-powers.md, plugin-marketplaces.md, checker-landscape.md*)

### 15.1 Tool sources and trust rules

**Sources checked:**

- the awslabs MCP catalogue (consolidated in 2026: the IaC server replaces the CDK and CloudFormation servers; several
  servers deprecated);
- the official MCP registry;
- vendor MCP servers;
- Kiro powers;
- Claude Code plugin marketplaces;
- the products and deterministic tools of each checker category.

**Rule: imitate by default, install by exception.** Plugins, hooks and MCP servers run with the user's full permissions.
2026 had real supply-chain incidents: compromised scanner GitHub Actions (Trivy, KICS), malicious skills in community
catalogues, a trojanised Claude Code extension on another IDE's marketplace.

**Trust rules:**

1. Checkers get read-only tools only; read-only is enforced in IAM first and by server flags second. A 2026 CVE showed
   the AWS API MCP server silently skipping its own policy check after a failed policy load.
2. Never give a checker a mutating tool; deny by tool name.
3. Pin every server, scanner, action, plugin and power, never `@latest`. Bump pins by reviewed PR.
4. Headless checkers run with `--strict-mcp-config` (Kiro: `includeMcpJson: false`), so a PR cannot add an MCP server to
   its own checker through `.mcp.json`. This deliberately gives up MCP auto-discovery (traceability C11).
5. **A session that reads untrusted content** (logs, issue text, web pages, finding excerpts) never holds deploy
   credentials. It holds AWS write credentials only when they are bounded to its own issue's temporary resources, action
   by action: tag-conditioned where the action supports it, scoped by the resource-name prefix otherwise, not granted
   at all where neither is possible (§11) [tM1, tP3].
   **Deploys run only in CI, from trunk**: on the protected tier the deploy role's trust policy names ONLY the
   subject of a production environment whose deployment branches are limited to trunk
   (`repo:<owner>/<repo>:environment:<name>`), never the ref subject, which every trunk job without an environment
   carries [aR3]. On the detected tier, which has no deployment branches, the deploy job names NO environment and
   the role trusts only the trunk's ref subject (`repo:<owner>/<repo>:ref:refs/heads/<trunk>`) (GitHub Docs, "OpenID
   Connect reference", seen 2026-11-19). A job that names an environment carries the environment subject instead, and
   on that tier any workflow can name any environment, so setup refuses a trust that names an environment subject
   there [aS2]. The commit it deploys is trunk's tip when the job starts: the deploy takes no
   commit input, and a re-run or queued run of an older commit concludes `skipped or refused` (H15) [aQ1]. A workflow a
   worker writes on its branch cannot assume the role, on either tier. On the protected tier that confines the
   production deploy to reviewed trunk code; on the detected tier it does not, because a worker can push trunk itself
   (§15.2 item 5) [aQ2].
6. An "untrusted input" line in every checker prompt.
7. Forge MCP write tools are denied to agents; all forge writes go through the wrapper, which marks them (§8.2).

### 15.2 Identity, credentials and the write budget [B9, B10, A4, B6, aN5]

**Decision U24 (2026-11-16): the agents keep posting as the operator's account.** Today one token is copied to every
machine; the design changes the tokens, not the account.

**What that requires:**

- **One fine-grained token per host**: scoped to the project repositories, expiring, revocable alone. A leaked laptop
  is then revoked without touching the others.
- The dispatcher's credentials: a token with contents write (claim refs), issues write (repairs) and actions read (the
  steward's liveness; GitLab: a read scope for the pipeline schedule) [aT1, aU2], and a read-only AWS role for alarm states and Security Agent findings (§14) [tQ1]; nothing
  more [tR1].
- The worker tokens LACK the permissions behind approving a protected deployment and administering the repository.
  Those stay with the operator's own token (§12.3 item 3).
- The worker tokens keep the permissions ordinary work needs, including "Workflows" and "Actions: write" [aP4, tP1].
  On the protected tier, trunk and the production deploy are guarded instead by credentials no worker holds: the
  steward's deploy key, and the deploy role's OIDC trust in trunk's tip only (§3.5, §15.1 rule 5). On the detected tier
  they are not (item 5 below) [aQ2].
- **The wrapper marks every agent write** (§8.2). A gate refuses unmarked writes from agent paths, and agents' writes
  of human-owned flag labels in any form: a label added or removed, or a label list in a create or update payload
  [aM4].
- **The write budget:** GitHub limits content-creating requests to 80 per minute and 500 per hour per account, shared by
  every worker, every project and the operator's own UI. GitLab's note limit is higher, 300 per minute per user. Under
  U24 the reductions are binding:
  - one envelope per review round (§8.2);
  - claims, renewals and the cursor over the git protocol, not REST (§5);
  - PR projections off by default;
  - a host-wide token bucket in the wrapper that honours `retry-after`.

  The comment sources still per issue: two audit lines per edge, spend lines per checkpoint, ledger lines per
  temporary resource, answer, reversion and tamper records. The `writes=` field of the spend lines measures the real
  number per issue (§13); no estimate is claimed until the first 20 issues per tier have been measured.

**The accepted residual, stated at its true size.** Under the shared account:

1. an agent that bypasses the wrapper (a direct API call, a browser session) can post an explicit form as the operator,
   or write a human-owned flag label. It can thereby answer a reserved question, approve, amend, admit, unhold or
   request a stage. Inside the wrapper this is refused [aM4, aM5];
2. any contents-write token can force-push or delete claim refs (§5.1);
3. on the protected tier, the forge-side gates for irreversible operations are credentials no agent session holds;
   beyond them, and on the detected tier (item 5), the reserved decision is the only gate, and on some plans no forge
   mechanism adds to it (§12.3) [aQ2];
4. no approval or reserved decision is provable by author (§12.10);
5. **on the detected tier** (§3.5), any worker token can push trunk, and any branch workflow can read the steward's
   deploy key. The per-tick detection stops the steward landing after the fact; the push, and any trunk workflow it
   starts, has already happened, **including the production deploy, which then runs the worker's code with the deploy
   role** [aQ2]. For 30 days after the rollout, runs of the old deploy workflow also stay re-runnable there (H15)
   [aS3]. Detection there catches only a push that does not imitate the steward (§3.5) [aQ6]. Whether factory
   mode on this tier may deploy to production at all is the operator's call (O16). GitLab before 19.2 is in this tier
   and is not closed by this design.

**What limits it:**

- P12: whatever the forged decision leads to still faces every checker and every predicate.
- The marking and label gates mean that an agent working through the wrapper cannot post an answer or write a
  human-owned flag: an ordinary note never counts.
- The delivery side does not rely on comment authorship:
  - on every tier: landings and reverts read from trunk trailers, the pinned deploy verdict, and the per-tick
    detection of non-steward trunk pushes (§3.5, §4.2, §4.5);
  - on the protected tier, in addition, prevention: the trunk ruleset with the deploy key as its one bypass, the key
    held by an environment limited to trunk (GitLab: the protected trunk, with the steward bot's token as a protected,
    masked and hidden variable), and the deploy role's OIDC trust in trunk's tip only (H15). Worker tokens and the
    workflows workers write hold neither credential.
- Per-host tokens make a leak revocable.

The decision itself can still be forged by an agent that leaves the wrapper. That is recorded, not designed away.

**If this is revisited**, the two alternatives considered were:

- a separate machine account for all agents: the human's comments become provable by author, and the agents get their
  own write budget;
- a GitHub App plus GitLab bot tokens: the strongest separation, with check runs and its own rate budget, but more
  setup.

---

## 16. Client parity and distribution

- **What lives where.** The state machine (transition verb, claim refs, records, budgets) lives in the wrappers and CI,
  so Claude Code and Kiro enforce it the same way. Lease renewal happens in the wrapper on every writing call, not in a
  prompt, which matters on Kiro [C17]. Client hooks add the in-session guardrails each harness supports.
- **Kiro's missing pieces** are covered by the cross-machine machinery, once the dispatcher runs (O12): no session
  watchdog (the lease reaper replaces it), no StopFailure event (the lease expires), no session cron (the dispatcher).
  `/get-guidance` posts nothing, so it is the same prompt on both clients and needs no prompt-submit hook (§12.9) [tP2].
- **The stop gates must change** [T-11]. Today the issue-loop brake refuses a loop's DONE while a queued PR has not
  landed, and `Phase: HANDED_OFF` needs `check-handoff`. Under this design, once the dispatcher runs (§14), a worker's
  turn ends correctly when its claim ends in one of:
  - a valid transition;
  - a `needs-input`;
  - a `ci-pending`;
  - a release.

  The release vocabulary of `clients/claude/docs/run-identity.md` and the gates must accept that. Headless workers end
  with a machine-readable verdict line in place of the interactive SESSION verdict.
- **The phase-2 renderer is a precondition** [T-14, tM4]. The design adds 16 agent roles that do not exist yet:
  - triage worker, triage checker, duplicate-confirmer;
  - acceptance-test author;
  - threat-model maker and checker;
  - logic-bug reviewer, unnecessary-code reviewer;
  - failure attributor, log-scan lane;
  - close-out worker, retro checker, re-fold checker;
  - question checker, answer recorder, arbiter.

  There is also the split of two agents into maker and checker; the docs-drift checker is the checker half of
  `doc-reviewer-agent`. Kept by hand as Claude and Kiro twins, the 16 new roles grow the 20-agent twin set by 80 %. The renderer (`docs/reports/directory-restructure-proposal-2026-11-07.md`) generates both
  clients from one source and comes first.
- **Distribution stays file-based** per project (decision U19). A plugin is a future option: it would be tied to the
  AWSBedrockGateway project, which hosts the `bedrock-gateway` plugin marketplace and the managed-MCP configuration of
  the desktop app, and it would need equivalents for Kiro (powers, a different format with no pinning) and other
  harnesses.

---

## 17. Measurement

These records give the factory's figures without hand-made analyses:

- the transition lines (§4.4);
- the claim refs (§5);
- the review records (§8);
- the question and answer records (§12);
- the revert records (§10);
- the spend lines (§13).

The figures:

- lead time and time per stage;
- queue age;
- bounce and rework rates;
- review rounds and each lane's resolution rate;
- question episodes per issue and the share of time waiting for answers;
- NFT, VBT and TBT per red event;
- cost per issue, per tier and per model (the spend lines' `model=`);
- REST writes per issue (the spend lines' `writes=`).

A digest (the `/delivery-status` option D2 of `docs/reports/session-endings-analysis-2026-11-01.md`) prints them per
project. It is also where close-out summaries (§11), open `env-incident` issues and elapsed-time alarms (§13) reach the
human.

---

## 18. What would change in the framework (for planning, not now)

| Area | New | Changed | Reused |
|---|---|---|---|
| Tracker state | stage labels, the transition verb with intent/done lines, the reconciler (free claim and L-old intents only), label reversion, `/stage` | — | the additive label primitives |
| Claims | the permanent claim ref with `held`/`free` commits, fencing token, cursor and lease; atomic branch + claim pushes; `record`, `verify` and group claims; the reaper; ONE release verb | `start-issue`/`release-issue` become the ref protocol; the `mkdir` lock stays a same-clone optimisation | — |
| Authority | the role table (§4.5) with conductor, arbiter, question checker and dispatcher rows; human and machine allow-lists per project | every writer calls the verb under a claim instead of writing labels | — |
| Spec hand-off | `spec-approved` record, the ask marker and hash, `/amend`, acceptance tests at spec time, the test-freeze run | the orchestrator's FIX splits into SPEC and IMPLEMENTATION teams | the spec phases, the review panel, the tiers |
| Review exchange | `factory-review/v1` records with `actor.agent` and `notVerified`; a validation and fold script; one envelope per round; separately started checkers for the exits §8.5 names; the arbiter with a computed overrule; `tamper` and the re-fold | the review lanes emit records instead of prose files | the review contract's materiality rules |
| Checkers | IaC gate, OSV-Scanner, diff coverage, spec lint, logic-bug reviewer, threat-model lane, triage checker, duplicate-confirmer, docs-drift checker, log-scan lane, retro checker, re-fold checker, answer recorder; the `checker-requested` queue that starts the separately started checkers; optional external security review and pen test | housekeeping and doc-reviewer split into maker and checker | the existing lanes |
| Delivery (`merge_steward.py`, templates) | Track E restore with the restore guard, the migration ledger and object-metadata digests; the four deploy outcomes, of which only `green` counts (§10.3); Track T attribution; steward-opened revert PRs that declare `Reverts: PR #<k>`; `Steward-Reverts` trailers for every revert confirmed by content, whoever opened it, and `Steward-Relands` for relands; re-verify deploys dispatched with `return_run_details`; the deploy guard, which deploys only trunk's tip, as the deploy job's first step from the default branch (H15); a re-verify deploy when a pinned run was cancelled with nothing newer behind it, or a landing's push run never appeared; the per-tick activity check of trunk pushes; the per-tick check that no other workflow names the steward's or the production environment, expression-valued names and outside reusable workflows included; the per-tick check that the deploy workflow is enabled, and the dispatcher's check, through the run API, that the steward workflow is active, ran within its bound (computed on every poll from its run history) and is not failing every tick (GitLab: its pipeline schedule) [aS1, aT1, aU1, aU2, aU3, aV1]; per-tick re-derivation of the TEST-READY and CLOSE-READY exits, with the CLOSE-READY/closed → REWORK-REQUIRED edges; classified train-push refusals (H14) | the red verdict marks no issue (H8); the watcher records facts and the steward transitions (H9); landings and reverts from first-parent trailers (H1, H7); revert PR CI dispatch and ordering (H10); the pinned deploy verdict from the landing's push run or a re-verify dispatch, first attempt only, through the jobs API (H13); the deploy template: no `sha` input, and its header rule "the steward's push starts the deploy" (§3.5); every `eligibility` reject, a closed PR, a revert outside Track T and a `/stage` request return the issue; `eligibility` waits on an issue `hold`; the steward pushes trains and trunk with its deploy key | trains, ancestry verification, `delivery-status` as a status record |
| Wrapper and git hooks | marking of every agent comment and body write, and a gate on unmarked ones; the gate on human-owned flag labels in any form, payload label lists included; the explicit-form parser (several forms per comment, and guidance-issue lines that name their issue); the fold's check of cited forms; the folded state with `since` for orientation only, re-folded for every decision; the cursor and folded state in the claim ref; renewal on every wrapper call, from the commit hook, and from `run_tests.py` and `suite_semaphore.py run` while they run; the `pre-push` fence on issue branches; the continuation issue; the write token bucket; the write counter | `call` gates the issue-comment, issue-update and label operations; the GitLab fold orders by note id | the forge API packages |
| Human input | `/get-guidance`, which prints one block of form lines; the project's guidance issue; the answer recorder executing every explicit form (answers, approvals, `/amend`, `/stage`, `/admit`, `/hold`, `/unhold`, `/priority`, `/clear-tamper`), the re-spec edge, `admitted {ask_hash}`, the question checker with its always-ask list, the decision inventory, standing-permission records, `env-incident` issues outside every worker queue | `continuous-work.md` escalation text | the five-line question shape |
| Gates and harness | a headless verdict line | the stop gates and the release vocabulary accept a transition, `needs-input`, `ci-pending` or a release as a valid end, once the dispatcher runs [T-11]; `proportionality.md`'s tier-S path and review caps are unchanged [C7, tN4] | the remaining gates |
| Scheduling | the dispatcher with its queues and exclusions | decision A2 reversed, and `check-handoff` superseded, only once the dispatcher runs on a host [tN11] | — |
| Clients | the phase-2 renderer first [T-14] | — | — |
| Setup | the Minimum revert tier required for AWS projects; the protection tier, determined and recorded in `config/delivery.json`; on the protected tier the GitHub trunk ruleset with the steward's deploy key as its one bypass, the key in an environment limited to the default branch and the repository's only write deploy key, or the GitLab steward token as a protected, masked and hidden variable; the Actions-may-create-PRs setting; CI `push` triggers that exclude `steward/train-*`, and the list of every workflow a landing starts, in the setup record; all checked with the operator's token; at rollout, a new production environment replacing the old one, so that on the protected tier no run of the old deploy workflow can assume the role (H15); on the detected tier, a deploy job without an environment and a trust that names only the ref subject [aS2]; the environment-name check run at setup [aS4]; the guidance issue, locked to collaborators; the deploy role's OIDC trust in trunk only; the dispatcher's read-only AWS role for alarm states and Security Agent findings [tQ1]; pinned MCP servers; strict MCP config for checkers; per-host fine-grained tokens without the deployment-approval and administration permissions; AWS permissions for temporary resources bounded per action, by tag or by name prefix [tM1, tP3] | both setup prompts and the update prompt | — |

**Small defects found on the way**, to fix when the framework is changed:

- `clients/claude/agents/spec-review-agent.md` repeats one paragraph.
- `clients/claude/docs/dead-code-language-matrix.md` lists `ts-prune` as required, although it is in maintenance mode
  and knip covers it.
- `clients/common/docs/delivery.md` §4 calls the `delivery-status` issue open, while the code keeps it closed [D2].
- The two maker-checker agents named in §7.2.

---

## 19. Known weaknesses: where a reviewer should push

1. **Forge support for the claim ref** (§5.5, O14). Unverified on both forges:
   - pushes to `refs/factory/claims/*`;
   - atomic multi-ref pushes with leases;
   - whether such a push starts any workflow;
   - whether a deploy key can push workflow-file changes, and whether the activity record tells a deploy-key push from
     a push made with the token of the account that added the key (§3.5, H14) [aQ5, aQ6].

   The branch-prefix fallback exists, but it starts `on: push` workflows.
2. **The fencing window** (§5.1). Branch pushes are fenced atomically, and the `pre-push` hook refuses any other push of
   an issue branch. REST writes (comments, labels) are fenced only by a check before each call, so an expired holder can
   make one more REST write. A step must stay short enough that L covers it, and L is capped at 90 minutes.
3. **The lease binds cooperating clients only** (§5.1). Any contents-write token can force-push or delete a claim ref.
4. **Identity** (§15.2, U24). The residual at its true size: an agent that leaves the wrapper can post an explicit form,
   or write a human-owned flag label, as the operator. Approvals and reserved decisions are not provable by author.
   The forge-side gates for irreversible operations are credentials no agent session holds, on the protected tier. On
   the detected tier trunk and the production deploy are guarded only by detection after the fact, which a push that
   imitates the steward passes (§3.5, §15.2 item 5) [aQ2, aQ6]. P12, the marking gate, the protection tier, the
   pinned facts and per-host tokens limit, but do not remove, that accepted risk.
5. **The in-session boundary** (§8.5). In-session lane records are as trustworthy as the maker's session. The exits
   without a separately started checker are recorded trade-offs:
   - tier S's START → SPEC-REQUIRED and START → split (the deterministic floor and duplicate retrieval decide);
   - tier S's spec (its combined pass stays in-session to keep a one-line fix small; its code is still checked by the
     separately started verifier);
   - CLOSE-READY → closed for tier S and where a project has no read-only log query (the deterministic close-out checks
     decide).
6. **Immutability** [T-08]. Audit lines and records are comments the shared account can edit or delete. An edit trips
   `tamper`; a deletion goes unnoticed. The option is a digest of the folded records written to a protected audit ref at
   close-out (O15).
7. **The write budget** (§15.2). It is measured by the spend lines, not estimated. Until the first issues have run,
   whether one account's budget carries the factory is unknown.
8. **Hand-off cost** [C6]. Cold starts make the decoupled flow costlier than the data the cost budgets were set from.
   Those budgets are report-only until recalibrated.
9. **Smoke attribution is heuristic** (§10.4, step 2.4). A wrong guess costs one deploy, one reland and a refund, never
   a broken trunk, but repeated wrong guesses lengthen VBT.
10. **The arbiter's authority** (§8.7). Whether it overrules security is computed; on other judgement calls, whether it
    simply sides with the more confident lane is still open.
11. **The learning-batch issue** (§11) is the designer's proposal (M5).
12. **Not designed here:**
    - automated capture of corrections and recurrence counting (gap-analysis 2.5);
    - backlog drift measurement (gap-analysis row 11);
    - a search that runs when the backlog is empty, including for drift in documentation no change touches;
    - the Jira wrapper (gap-analysis 3.8);
    - the details of the production intake (gap-analysis 2.6);
    - the contract-drift check per project (gap-analysis 3.7);
    - per-agent deny rules and Kiro's central allow-lists (gap-analysis 3.2);
    - a living system spec (gap-analysis 2.8);
    - the dispatcher's host and worker start (O12).

    [traceability.md](traceability.md) lists them.
13. **Partial reverts** (§10.4 step 3) [aM2]. Only a revert of a steward merge confirmed by its content is a revert
    fact. A change that undoes part of a landed PR is an ordinary change, so the reverted PR's issue stays closed or
    verified.
14. **Landed privileged automation runs with privilege** (§3.5). A change to a workflow file, the steward or the deploy
    pipeline gets the full security and devops lanes and a separately started checker, and is then trusted once it
    has landed. Workers may change the automation that guards them; the checkers, not the forge, stop a harmful
    change.
