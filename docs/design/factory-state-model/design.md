# Factory state model: design (revision 2, 2026-11-16)

Status: design only. Nothing described here is implemented unless §2 says it exists today.

Revision 2 answers the two reviews of revision 1 (11073fe):

- the adversarial review: 53 findings, 4 A;
- the review against the keynote and the gap analysis: 23 findings.

Both are in [`docs/reports/factory-state-model-2026-11/reviews/`](../../reports/factory-state-model-2026-11/reviews/).
[review-response.md](review-response.md) maps every finding to what changed. Finding ids appear in brackets, e.g.
[A1], [T-05].

Companion documents:

- [decisions.md](decisions.md): the decisions and their sources.
- [traceability.md](traceability.md): how the design aligns with the keynote, which is a vision and not a
  specification, and how it covers the gap analysis.
- [`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/): the research behind each
  section, cited as *(R: file)*.

Words used throughout:

- **stage**: the one state an open issue is in (§3).
- **flag**: an orthogonal marker, such as `needs-input`.
- **claim**: the server-enforced lease a worker holds on an issue (§5).
- **maker / checker**: the agent that produces an artefact, and an agent or tool that judges it.
- **team**: the makers and checkers working one stage of one issue.
- **role**: what an actor may write (§4.5).
- **identity**: the forge login a write comes from.
- **reserved decision**: a decision the design leaves to an authorised human (§12.3).

---

## 1. Goal and principles

The goal: the operator talks to the projects only through the backlog. Every issue, once created, is picked up by
workers (Claude Code, Kiro, Kiro Crew) on any machine and moved to a verified, closed state without waiting for
anyone, with the human as the rare exception.

| # | Principle | Consequence in this design |
|---|---|---|
| P1 | The backlog is the only interface | The tracker and git hold everything another worker needs; machine-local run state is a cache, never the source of truth |
| P2 | Workers never wait | Every wait has an owner that is not a worker: a human answer (`needs-input`), the PR's own CI (`ci-pending`, picked up by the verifier lane), merge (the steward), deploy and smoke (the deploy pipeline and the watcher). The worker releases and pulls other work |
| P3 | Any number of workers, any machine, any client | Exclusion comes from a server-enforced claim (a git ref compare-and-swap), not from the account or from re-reading comments (§5) |
| P4 | Maker ≠ checker | Enforced per agent context and role, not per session (§8.1); the steward re-evaluates the checkers' verdicts itself before landing (§8.6) |
| P5 | Every stage has a deterministically checkable finish line; the team loops until it holds | A script, the transition verb, evaluates it from tracker + git + CI state (§4) |
| P6 | The human is the last-resort conflict resolver | No human-only stage or gate. Questions only when no agent can answer them, in ONE batch, never drip-fed (§12). An optional per-project approval setting exists, off by default |
| P7 | Shared environments; batched delivery; revert first | One CI or deploy run covers many issues. A failed deploy or smoke is restored first, then attributed (§10) |
| P8 | Effort proportional to the ask | Tiers S/M/L decide artefacts, panels and budgets (`clients/claude/rules/proportionality.md`); tier S has a minimum path (§7.3); one claim may carry an issue through several stages |
| P9 | Enforcement is client-neutral | The state machine lives in the wrapper scripts and CI, which Claude Code and Kiro both run, not only in one client's hooks |
| P10 | File-based distribution per project | The framework stays copied into each project by the setup and update prompts; a plugin is a future option (§16) |
| P11 | Authority is explicit | Every edge and every record type names the role that may write it (§4.5); a write by any other role is data [A1] |
| P12 | Equal scrutiny (decision U21) | Every input, from the operator, an agent or an outsider, is judged on its content. A human answer never skips a checker. Authorship decides only who may make a reserved decision (§12.3), never how hard the content is checked |
| P13 | Check-then-act is named and made safe | Where the tracker offers no conditional write, exclusion comes from a server-side guard (a ref create or fast-forward), and recovery rolls forward (§4.4, §5) |

---

## 2. Starting point: what exists, what is reused, what must change

| Capability | Today | Where | In this design |
|---|---|---|---|
| Merge queue with cumulative trains: land the longest green prefix; blame only the newest PR of the first red train; one retry for a first failure | yes | `src/payload/scripts/merge_steward.py` (docstring "ONE TICK") | reused |
| Train merges carry `Steward-PR:` and `Steward-Issues:` trailers on trunk's first-parent history | yes | `merge_steward.py` (`TRAILER_RE`, the train commit message) | becomes the source of truth for landings (§10.8 H1, H7) |
| Post-deploy verification by git ancestry; the `delivery-status` issue | yes; the status issue is kept CLOSED and only its body is written (`_status_issue`, `_write_status`) | `merge_steward.py` `verdict`; `clients/common/docs/delivery.md` §4 (which says "open", a doc/code deviation) [D2] | reused as a machine status record only (§12.5) [B13] |
| Delivery labels `queue`, `queue-failed`, `queue-conflict`, `queue-retried`, `do-not-merge`, `awaiting-verification`, `verified`, `verification-failed`, `needs-rework`, `needs-closeout`, `reverify`, `delivery-status` | yes | `clients/common/docs/delivery.md` §6 [D1] | reused below the stage labels |
| Tiers, byte caps, review panel with caps (S one combined pass, max 2; M 4/2; L 6/3), materiality A–D | yes | `clients/claude/rules/proportionality.md`, `clients/common/docs/review-contract.md`, `clients/common/phases/spec-phase-review.md` | reused |
| Test-first waves, red for the right reason, the adversarial verifier, evidence reports | yes | `src/hooks/red_for_right_reason.py`, `clients/common/phases/spec-phase-implement.md` | reused |
| Filing discipline, findings ledger | yes | `clients/claude/rules/issue-filing-discipline.md` | reused |
| Claim: label + assignee + re-read | yes, but unsafe across machines (§5.5) | `src/payload/scripts/github_api/commands/claim.py` | replaced by the claim ref (§5) |
| Triage, spec and questions as tracker states | **no**: they happen inside one session; the spec lives in its worktree until the PR | `clients/claude/agents/issue-work-orchestrator.md` (FIX) | new |
| Something that starts workers | **no** | — | the dispatcher (§14) |
| Revert after a failed deploy | **no** | `docs/reports/red-pipeline-analysis-2026-11-02.md` | new (§10) |

**Delivery behaviours of today's code that this design changes** (revision 1 treated them as reused):

| Today | Where | Change |
|---|---|---|
| A red verdict returns every issue landed since the last green deploy (`verification-failed` + `needs-rework`) | `verify_issue`, `verdict` | the red verdict marks no issue; only Track T's culprit record returns one (§10.5, H8) [B11] |
| A green verdict closes the issue when its checklist is complete | `verify_issue` (`issue_close`) | the watcher transitions to CLOSE-READY; the close-out team closes (§11, H9) [B12] |
| Every PR of a batch is recorded with the batch tip as its landing, and `last_landing` takes the last match regardless of PR | `land()` → `after_landing`; `last_landing` | landings and reverts per PR, derived from trunk trailers (H1) [B15] |
| `merge-steward:` lines are matched from any comment author | `GitHubHost.issue()` keeps only `body` | landings are derived from trunk history; comments are projections (H7) [B7] |
| A PR the steward opens with `GITHUB_TOKEN` gets no PR CI, so `eligibility` waits for ever; `plan()` orders by enqueue time | `github-merge-steward.yml.template`; `eligibility`, `plan` | the steward dispatches the revert's CI and orders reverts first (H10) [B14] |
| Train branches are deleted after landing | `land()` → `delete_trains` | attribution uses the first-parent merge commits on trunk (§10.4) [C3] |
| GitLab notes are listed by `created_at` | the GitLab host in `merge_steward.py` | the fold orders by note id on both forges (§8.2) [C5] |
| `release-issue` writes the whole label set minus `in-progress` | `cmd_release_issue` in `claim.py` | one release verb, additive (§5.4) |

---

## 3. The state model

### 3.1 Stages (exactly one per open issue)

Each stage is a **queue** named for the next kind of work the issue needs. Being worked on is the claim, not a stage.

| Stage | Meaning | Pulled by | Leaves to |
|---|---|---|---|
| **START** | New; no work done yet. An issue with no stage label AND no transition audit line is in START (§4.4) | triage worker | SPEC-REQUIRED; closed administratively; split into child issues |
| **SPEC-REQUIRED** | Triaged; it needs a spec and acceptance tests | spec team | IMPLEMENTATION-READY |
| **IMPLEMENTATION-READY** | A reviewed spec at a pinned commit, failing acceptance tests that define "done", no blocking question | implementation team | TEST-READY |
| **TEST-READY** | The PR is in the merge queue, then landed, then deployed and smoke-tested. Never claimed by a worker; its exits are written by the steward and the watcher roles (§4.5) | merge steward, deploy pipeline, watcher | CLOSE-READY; REWORK-REQUIRED |
| **REWORK-REQUIRED** | Returned from TEST-READY with a machine-readable cause | implementation team, pulled first | TEST-READY; IMPLEMENTATION-READY; SPEC-REQUIRED |
| **CLOSE-READY** | Every PR landed and not reverted; deploy and smoke green on a commit containing all of them | close-out team | closed (done) |

TEST-READY spans queue → merge → CI → deploy → smoke (decision U7). Its internal milestones (queued, landed,
verified) are machine lines and trunk trailers, not stages.

### 3.2 Flags (orthogonal to the stage)

| Flag | Meaning | Set by | Cleared by |
|---|---|---|---|
| `needs-input` | at least one BLOCKING question or approval is open (decision U1). The stage does not change; the claim is released | any team, after the question checker (§12.4) | the answer recorder or `/get-guidance`, when an authorised answer exists for every blocking question (§12.7) [B4] |
| `blocked-by #N` | cannot proceed until #N reaches a named stage. Native dependency where the forge offers it free (GitHub issue dependencies); otherwise a machine line `factory: blocked-by #N until <stage>` (GitLab blocking links are Premium) [C10] | triage, spec | the dispatcher when #N gets there; a target closed administratively releases the block with a comment; a cycle is a triage error, reported on the issue |
| `hold` | the human paused it; every actor stops at its next verb call | an authorised human | an authorised human |
| `claimed` | a query filter projected from the claim ref (§5); never authoritative | the claim verb | the release verb |
| `ci-pending` | the PR's own CI is running on head H; the worker has released | implementation worker | the verifier lane, when the run ends (§4.2) |
| `review-open` / `review-verify` | blocking findings wait for the maker / resolutions wait for a checker lane; `review-verify` also queues the issue for that lane (§14) | the record writer | the claim holder, after the fold shows nothing pending |
| `split` | a parent whose work moved to child issues; `blocked-by` every child [C9] | triage | closed administratively when the last child closes |
| tier `S`/`M`/`L` + risk tags (`auth`, `money`, `data-migration`, `iam-iac`) | select the team, the checkers and the budgets | triage, at or above a deterministic floor (§6.4) | raise only; lowering needs a checker's verdict [B18] |
| `priority:<level>`; `priority:critical` expedites (§14) | product priority | an authorised human; triage for production incidents | an authorised human |
| `admitted` | admission of an issue whose author is not on the allow-list (§6.3) | an authorised human | — |
| `env-incident` | marks an issue that IS an environment incident (§12.5) | the steward, the watcher, any team | the environment owner, by closing it |

### 3.3 Diagram

```
           (every issue, including the operator's own, goes through triage)
START ──triage──► SPEC-REQUIRED ──spec gate──► IMPLEMENTATION-READY ──CI green + verified──► TEST-READY ──deploy+smoke green──► CLOSE-READY ──► closed
  │                                                                                              │   (watcher)
  └──► closed (duplicate / invalid / won't do; split → children at START)                        └──► REWORK-REQUIRED (steward: culprit only; after a landing: revert first)
                                                                                                        │
                                                                    rework analysis, then: TEST-READY | IMPLEMENTATION-READY | SPEC-REQUIRED

Flags on any open stage: needs-input · blocked-by · hold · claimed · ci-pending · review-open/verify · split · tier + risk · priority · admitted
```

### 3.4 Properties

1. **States are durable checkpoints, not compulsory hand-offs.** One claim covers the issue, whatever stage the holder
   carries it through, and every transition is recorded with its evidence [A3]. Tier S may run START → TEST-READY in
   one claim. A crash leaves a checkpoint another worker resumes from.
2. **One writer per issue at a time:** the claim ref (§5).
3. **A stage changes only through the transition verb (§4.4).** Workers, the steward, the watcher and the reconciler all
   call the same code; nobody writes a stage label directly.
4. **Who may call which edge is fixed by role (§4.5).** A worker never changes the stage of an issue whose claim it does
   not hold.

### 3.5 Delivery modes [B21, T-15]

The model assumes the merge steward. Per `config/delivery.json`:

| Mode | TEST-READY → CLOSE-READY when |
|---|---|
| `merge: steward` + `verification: watcher` | the full predicate of §4.2: every PR landed and not reverted, deploy + smoke green on a commit containing them |
| `merge: steward` + `verification: none` | every PR landed and not reverted, and the trunk CI of a commit containing them is green |
| `merge: direct` (this repository today) | not a factory project. It keeps the session workflow of `clients/common/docs/delivery.md` until it switches (gap-analysis rank 9) |

### 3.6 Other trackers [T-21]

The stages map onto a Jira workflow, whose statuses are exclusive natively, and the flags map onto labels. The claim
(§5) and the records (§8) use git refs and forge comments, so a Jira backend needs its own equivalents. The Jira wrapper
itself is out of scope here.

---

## 4. Transitions and their finish lines

### 4.1 The rule that makes predicates deterministic

> A transition's predicate is evaluated by a script from tracker + git + CI state only. Its checker part is always the
> same sentence: **every checker the stage requires (by tier and risk tags) has posted a verdict on the artefact's
> CURRENT commit, from a context with that checker's role other than the maker's (§8.1), and no blocking finding is
> open.**

Judgement happens inside the checkers. The predicate only counts their structured verdicts (§8). A verdict on an older
commit does not count, so a new commit by the maker re-opens the check as a delta review. Before landing, the steward
re-evaluates the fold itself and ignores any status a maker could have set (§8.6) [B6].

### 4.2 The predicates

| Transition (caller role, §4.5) | Predicate (all must hold) |
|---|---|
| START → SPEC-REQUIRED (worker) | a triage record for the current ask hash, containing: the duplicate search (candidates and verdict), a scope verdict, tier and risk tags at or above the deterministic floor (§6.4), the estimated footprint, and the **decision inventory** (§12.2). For M and L, a triage checker's verdict on the record [T-19]. No open blocking question |
| START → closed (worker) | the triage record's outcome (duplicate, invalid, won't do) + a SECOND agent's confirming verdict (the duplicate-confirmer). Closing destroys work, so it always gets a checker |
| START → split (worker) | every child exists at START and references the parent; the parent carries `split` and is `blocked-by` every child |
| SPEC-REQUIRED → IMPLEMENTATION-READY (worker) | spec + acceptance tests committed at SHA S on the pushed issue branch; the acceptance tests fail for the right reason at S; every acceptance criterion is referenced by ≥ 1 test (traceability script); all required spec checkers report on S with 0 open blocking findings; no open blocking question; the approval setting, if on, is satisfied for the spec (§12.10); tier and tags re-derived from the spec's declared footprint, raise only (§6.4). **Side effect** written by the verb, not a precondition: `spec-approved {sha: S, ask_hash}` [C14] |
| IMPLEMENTATION-READY → TEST-READY (worker, or the verifier lane completing a `ci-pending` issue) | a PR from the branch with `Refs #N`, base = trunk, `do-not-merge` removed (and not a draft where the forge has drafts) [B22]; **S's acceptance tests, run with S's fixtures and test configuration over H's code, pass** [B19]; any change since S to the acceptance tests, the fixtures or configuration they depend on (`conftest.py`, helpers, pytest settings) needs a newer `spec-approved`; PR CI green on head H; the adversarial verifier and every required implementation checker report on H with 0 open blocking findings; the approval setting, if on, is satisfied for the PR's changed paths [T-07]; the evidence report is present; `check-pr` exits 0. **While PR CI runs**, the worker sets `ci-pending` and releases; the verifier lane completes the transition when the run ends [C2, T-10]. `enqueue --allow-pending` remains only for a re-enqueue after a rebase that changes no file, and only when pending CI is the sole unmet clause [C1] |
| TEST-READY → CLOSE-READY (watcher) | for EVERY PR the issue queued: a landing on trunk's first-parent history (a steward merge whose `Steward-PR` trailer names it) that no later revert of that PR supersedes (`Reverts-PR` trailer) [B15, B7]; a deploy + smoke green on a commit D that contains every such landing; every `(post-deploy)` item ticked. Per mode: §3.5 |
| TEST-READY → REWORK-REQUIRED (steward) | a steward record names this PR the culprit, a conflict or PR-CI red; OR Track T's culprit record after a failed deploy or smoke (§10.4); OR a blocking finding on the queued PR (`review-open` dequeues it) |
| REWORK-REQUIRED → any exit (worker) | a **rework-analysis record** classifies the cause as code, requirement or environment, with evidence, and the test-architect lane confirms a "code" classification (the acceptance tests still express the ask) [T-01]. Then: **→ TEST-READY**: the IMPLEMENTATION-READY → TEST-READY predicate on the new head, plus a resolution record answering the cause (e.g. the job that failed is green on the new head); **→ IMPLEMENTATION-READY / SPEC-REQUIRED**: a requirement cause amends the acceptance criteria before code is touched, and the target stage's predicates apply from scratch; an environment cause is an `env-incident` (§12.5), not rework |
| CLOSE-READY → closed (worker) | the close-out record (§11): the temporary-resource ledger AND a query by the `factory-issue` tag are both empty [B20]; every item of the **laundry list** has a disposition. The laundry list is the spec's residuals, the findings-ledger rows written during the issue, the lanes' `notVerified` entries and the close-out's own observations [D4, T-06]. The structured summary is posted; the checklist is complete; no open PR references the issue; the remote branch is gone |

### 4.3 Pickup preconditions (checked when a claim is taken)

- **The ask is unchanged since approval**, checked in SPEC-REQUIRED and IMPLEMENTATION-READY only [B5]:
  - The verb compares the ask hash (title + body WITHOUT checklist tick states) with `spec-approved`.
  - Answers and machine comments do not change the ask.
  - An authorised human changes it by editing the title or the body, or with an explicit `/amend` comment. Either sends
    the issue back to SPEC-REQUIRED, where the spec checkers re-approve quickly if the change is immaterial.
  - From TEST-READY on, a change of mind is a new issue.
- **The spec base is current enough.** If the spec's declared footprint changed on trunk since S, the spec checkers do a
  delta review against the new trunk first. This replaces a WIP cap (decision U8).
- **No `hold`, no open `blocked-by`, no `needs-input`.**
- **For a checker role:** the issue is in that lane's queue (§14).

### 4.4 The transition verb, its recovery, and where the stage is stored [B2, C16]

One wrapper verb for both forges, for example `transition <issue> --from <stage> --to <stage> --evidence <link>`:

1. **Guard.** This is a read followed by writes, not a compare-and-set: exclusion comes from the claim ref (§5). It
   refuses when:
   - the issue is not in `--from`;
   - the caller's role may not call this edge (§4.5);
   - for a worker, the caller's fencing token is not the claim ref's current value;
   - or the predicate fails. The refusal names the unmet clause.
2. **Intent.** Append `factory: stage <A> -> <B> intent <id> by <role>/<agent>`.
3. **Side effects** of the edge: the enqueue, the `spec-approved` record, the release.
4. **Labels.** Add the new stage label, then remove the old one, with the additive primitives only.
5. **Done.** Append `factory: stage <A> -> <B> done <id>`.

**The reconciler** (dispatcher, §14) repairs before any worker may pull an issue:

- An intent without `done` is rolled FORWARD when its side effects are present and back when they are absent.
- An issue with zero or two stage labels is repaired from its last `done` line.
- A single stage label that disagrees with the last `done` line was set by hand. It is corrected, or, when an authorised
  human set it, recorded as `factory: stage <A> -> <B> by <login> (override)`.

These audit lines are the trail an auditor reads and the metrics source (§17). They are not immutable (§19).

**Storage.** The portable path is plain prefixed labels (`stage:spec-required`), which work on every tier of both
forges, with exclusivity enforced by the verb. Native single-select storage is a later option: GitLab scoped labels
(`stage::…`, Premium/Ultimate) and GitHub issue fields (organisation-level single-select, generally available since
2026-07 per GitHub; not for user-owned repositories).

### 4.5 Authority: which role may write what [A1, P11]

| Role | Identity under the current shared account | May call | May write |
|---|---|---|---|
| **Worker** (maker team) | the operator's login, on a per-host token (§15.2) | the worker edges of the issue whose claim it holds (§4.2) | its team's records; the claim ref of that issue |
| **Checker lane** | the same login; distinguished by a fresh agent context with the lane's role (§8.1) | IMPLEMENTATION-READY → TEST-READY, as the verifier lane completing a `ci-pending` issue; nothing else | finding, verification and verdict records; a verify-kind claim (§5.3) |
| **Steward** | the steward's CI identity (GitHub: the workflow's `GITHUB_TOKEN`, posting as `github-actions[bot]`; GitLab: the `STEWARD_TOKEN` user) | TEST-READY → REWORK-REQUIRED; reland moves within TEST-READY | trunk (fast-forward to a train), train refs, revert PRs, `merge-steward:` lines |
| **Watcher** | the deploy pipeline's CI identity | TEST-READY → CLOSE-READY | verification lines, `delivery-status`, `env-incident` issues |
| **Reconciler, reaper** | the dispatcher's token | repairs (§4.4) and claim expiry (§5.2); no forward edge | `override` and repair lines |
| **Answer recorder** (headless) and **`/get-guidance`** (interactive) | acting for an authorised human, whose login and comment id the record names | the transition an answer explicitly implies | `factory: answer` records; clearing `needs-input` |
| **Authorised human** | a login on the project's human allow-list (the operator; named collaborators) | anything | reserved decisions (§12.3) are valid only from this role |

A write by any other identity, or by a role outside its row, is data: it is never counted by a predicate.

**Facts are taken from where they cannot be forged by a comment:**

- landings and reverts from trunk's first-parent history, whose commits only the steward writes (§10.8 H1, H7);
- claims from the claim ref (§5);
- CI results from the forge's run API.

**Under the shared account** (decision U24), worker, checker and answer-recorder writes all come from one login. Their
roles are then told apart by the marker and the `actor` fields, which proves nothing against a compromised agent. That
residual is accepted; what limits it is in §15.2.

---

## 5. Claims [A3, B1, C11, C17, C20, C21]

### 5.1 The claim is a git ref per issue

A claim is the ref `refs/factory/claims/<issue>` in the project's repository. Where a forge refuses a custom ref
namespace, it is a branch with the prefix `factory-claim/`. Both forms are to be verified on `sff-test-*` repositories
(O14).

- **Acquire.** Create a commit whose message names the worker, the kind (`make`, `verify` or `record`) and the stage,
  and push it with `git push --force-with-lease=<ref>: <commit>:<ref>`. The empty expectation means "the ref must not
  exist". The receiving side checks the ref's old value atomically, so a second acquirer is refused by the server. There
  is ONE claim per issue, whatever stage the commit names; the stage is informational.
- **Fencing token** = the ref's current commit SHA. Every verb call and every push for the issue checks that the
  caller's token is the ref's current value. A holder whose token is stale stops at that call.
- **Renew** by pushing a child commit with `--force-with-lease=<ref>:<token>` (an exact compare-and-swap). The wrapper
  renews on every verb call and at least every N minutes during long steps, never by a prompt instruction [C17]. Renewal
  uses the git protocol, not a REST content write (§15.2).
- **Release** with the ONE release verb: delete the ref (compare-and-swap on the token), remove the `claimed`
  projection, and remove the legacy in-progress label and assignee if present. The steward and the watcher call the same
  verb when they return or verify an issue [C11].
- **Projection.** A short claim comment may mirror the ref for humans. The protocol never edits or deletes a comment
  [C21].

### 5.2 Expiry and the reaper

- The lease duration L is configurable. The default is 45 minutes, longer than the longest step without a wrapper call.
- The reaper (dispatcher, §14) declares a claim expired when the same token has stood unchanged for L by the reaper's
  own clock, across two of its own observations. No worker clock is compared, so clock skew does not matter.
- Expiry replaces the token by compare-and-swap. The old holder's next call fails on the fence.
- **Residual:** writes the old holder makes between expiry and its next verb call. That window is at most one step
  (§19).
- This replaces the session watchdog for crashed turns: a worker killed by an API error simply stops renewing.

### 5.3 Verify claims and group claims

- **A checker lane** that verifies resolutions takes the issue's claim with kind `verify`. It may write only its own
  records (§4.5) and the `ci-pending` completion.
- **A decision that moves several issues** takes all their claims, all or nothing. Example: "this batch goes back to
  SPEC-REQUIRED". Claims are acquired in ascending issue number; after a failure, all are released and retried after a
  random back-off [C20]. The alternative is ONE coordinating issue that the others are `blocked-by`. Workers never
  negotiate in free text; §8 is the only exchange format.

### 5.4 One release verb

The release verb replaces `release-issue`'s whole-set label write with additive removes. A label added by someone else
between a read and a write is then never lost.

### 5.5 Why today's claim is not enough (code read on 2026-11-11)

- `start-issue` refuses a claim only when a DIFFERENT login holds it (`_claim_is_held_by_another` in
  `src/payload/scripts/github_api/commands/claim.py`). Every worker posts as the same login, so a second machine's
  claim on the same issue succeeds.
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
3. production signals: an alarm or an AWS DevOps Agent investigation produces ONE issue through `issue-intake-agent`
   with `Origin: production`, under the same filing gate (gap-analysis 2.6). Triage gives it `priority:critical` when
   it describes a live incident, which the dispatcher pulls before everything else (§14) [T-09];
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
  in a **read-only mode** and waits for an `admitted` label set by an authorised human:
  - no write tools, no AWS credentials, no forge write except the triage record;
  - the issue text is data;
  - the admission view shows the verbatim body, fenced, next to the triage paraphrase, because a paraphrase of injected
    text can read harmless.
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
| START | triage worker | duplicate retrieval (forge search + lexical or embedding similarity over open and recently closed issues); the tier and risk floor (§6.4); template lint | **duplicate-confirmer** (mandatory before any close); **triage checker** (M, L) |
| SPEC-REQUIRED | spec-author (+ spec-researcher); acceptance-test author; threat-model maker (L or risk tags: the awslabs threat-modeling MCP server, pinned to a commit) | AC → test traceability; red for the right reason; EARS/INCOSE spec lint (new); byte caps; threat-model schema check | test-architect; security-reviewer (one-line CLEAN unless a trust boundary is touched); **threat-model checker** (new; STRIDE + OWASP ASVS 5.0; L or risk tags); devops-iac-reviewer (IaC); standards / best-practice (M+); optional AWS Security Agent design review (L + `auth`/`money`, budget-capped) |
| IMPLEMENTATION-READY | spec-implementer (waves), ci-workflow-agent, code-merge-reviewer | ruff, mypy, bandit, secret scan, tests; **diff coverage on changed lines** (new); **OSV-Scanner** (new); **IaC gate: cdk-nag + cfn-lint + Checkov or cfn-guard + `cdk diff --security-only`** (new); import/architecture contracts; mutation testing on changed functions (L or risk tags); **dead and unnecessary code on the diff** (vulture or Skylos `--diff`, knip); IAM Policy Autopilot (actions the code needs vs the CDK grants) | adversarial-verifier; **logic-bug reviewer** (new, M+: find → verify-to-disprove → rank); standards (M+); security and devops lanes by risk tag; unnecessary-code reviewer (M+); optional **external security review of the PR** (AWS Security Agent diff scan; project setting `external_security_review`: `risk` by default, `all` for every PR, or `off`) [T-04] |
| TEST-READY | merge steward, deploy pipeline | train CI; pre-flight (§10.3); **stateful replacement/deletion detector** on the change set (new); smoke/E2E | failure attributor for smoke failures. It uses CloudWatch and CloudTrail MCP read-only, ranks only inside the suspect set, and treats logs as data [C15]. Optional batch release readiness (AWS DevOps Agent) for batches with `iam-iac`. Optional **penetration test** of the shared stage environment (AWS Security Agent): budget-capped, batched per project setting (e.g. weekly, or per batch containing `auth`/`money`); its findings enter START as issues [T-04] |
| REWORK-REQUIRED | any implementer | the same deterministic set on the new SHA; SARIF baselines show which findings are fixed, new or unchanged | the test-architect confirms the rework classification (§4.2); then only the lanes with open findings, plus lanes whose files the fix touched (delta) |
| CLOSE-READY | close-out worker | leftover checks on the diff (TODO, debug flags); the temporary-resource ledger and tag query (§11); a log scan of the deploy window for errors, where the project provides a read-only log query [T-13] | **retro checker**: every learning is backed by evidence, is not already a rule or memory, and nothing is filed without an observed defect |

Two existing agents break maker ≠ checker and are split when implemented: `issue-housekeeping-agent` and
`doc-reviewer-agent` both make and check.

### 7.3 Cost proportionality, and the tier-S minimum path [C7, T-16]

| Selection | Checkers |
|---|---|
| Every issue | the deterministic baseline, AC traceability, red for the right reason, diff coverage, the adversarial verifier |
| Tier S | as `proportionality.md` says today: ONE combined spec-review pass (all lenses, incl. test coverage; max 2 iterations) instead of the panel |
| Tier M and L | the full panel (test-architect, standards, best-practice, security, devops as tagged), the logic-bug reviewer, the triage checker, the close-out LLM reviewers |
| Tier L | the threat-model lane, mutation testing |
| Risk tags | `auth`/`money`: full security, threat model, mutation; `iam-iac`: devops-iac plus the IaC gate (which also runs whenever `cdk/` changes); `data-migration`: the stateful-replacement check is blocking |
| Paid external agents (AWS Security Agent, AWS DevOps Agent) | per project setting, budget-capped, never the only checker for a gate |

**The tier-S minimum path:** a one-line fix stays a one-line fix.

| Step | What tier S does | Why it stays |
|---|---|---|
| Triage | the deterministic floor, duplicate retrieval, a one-line decision inventory; the duplicate-confirmer only if a candidate is found | every issue is triaged (U16); a wrong close destroys work |
| Spec | `change.md` with its acceptance criteria and the tests that pin them, on the issue branch | the finish line must exist before the code |
| Review | ONE combined pass | today's rule |
| Implementation | one wave; the deterministic baseline; one adversarial-verifier pass | maker ≠ checker on the code |
| Close-out | the deterministic clean-up and the summary; the retro checker only when a learning is proposed | U18 |
| Hand-offs | none, unless the worker is interrupted: one claim from START to TEST-READY | context stays warm |

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
- `role`: the lane, or `maker`, `conductor`, `arbiter`, `recorder`.

**Maker ≠ checker is checked on `agent` and `role`, not on `worker`.** A verification is valid only from an agent
context with the finding's lane role that did not write the resolution. In-session lanes therefore count when they run
as separate subagent contexts, which is how the conductor dispatches them today.

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

### 8.2 Transport: the same bytes, three ways [B10, C4, C5, C21]

1. **Inside one machine:** a file per lane per iteration.
2. **Between machines and issues:** an issue comment.
   - Layout: a hidden marker line, a one-line Conventional-Comments rendering for humans, and the JSON in a fenced block
     inside `<details>`.
   - **One envelope per ROUND:** the conductor posts every lane's records of a round together, not one comment per lane.
   - At most 60,000 characters per comment, because GitHub refuses more than 65,536. Deterministic ids. Read before
     write. Never edit.
   - **Fold order** is by comment or note id on BOTH forges, not by creation time. **Edited record comments**
     (`updated_at` ≠ `created_at`) are rejected by the fold.
   - **Reading:** pages are fetched and filtered client-side by id, because GitHub's list endpoint takes only `since`
     (an updated time). The last folded id is recorded in the claim ref's commit message, so a new holder resumes from it
     and never full-scans.
   - **Placement:** records go on the issue whose holder must act. Cross-issue feedback from #A about #B's work is posted
     on #B, with a pointer on #A.
   - **Comment cap:** GitHub disables comments on an issue past 2,500. At 2,000 comments the verb continues the issue in
     a linked continuation issue that inherits the stage, the claim and the cursor.
   - **Index:** the labels `review-open` and `review-verify`.
3. **On the PR/MR, as projections**, off by default: review threads, and a `factory/review` commit status for humans.
   The status is not the gate (§8.6).

**A machine comment** is a comment carrying the marker, written through the wrapper. The wrapper adds the marker to
every `factory:` and `merge-steward:` line it writes [B5].

### 8.3 Human input in comments [A4, P12]

A comment counts as an answer, an approval or a change of the ask only if its author is an **authorised human** (§4.5).
Any other unmarked comment, from an outsider or from any login not on the human allow-list, is data. It is read and
judged on its content like any input, and may well be a valid bug report or argument, but it never decides a reserved
question, never approves, and never moves the ask.

The same filter applies to PR/MR threads. Why authorship matters at exactly these points, and nowhere else: §12.3.

### 8.4 The normal round

1. The conductor pins the SHA and dispatches every lane, each in its own subagent context, in one message.
2. Each lane writes its envelope part, which must validate.
3. The conductor folds the records: it dedupes, flags conflict candidates (overlapping anchors with different fixes)
   and posts the round's envelope.
4. The maker answers every open blocking finding in one pass.
5. Each lane verifies ONLY its own findings at the new SHA, in a fresh context, with fresh re-run evidence. A "verified"
   without fresh evidence is invalid.

### 8.5 Downgrades [B6]

The conductor runs in the maker's session, so it cannot downgrade a blocking finding alone. A downgrade to
non-blocking needs the raising lane's `accept` or an arbiter decision.

### 8.6 The gate [B6]

The predicate's checker clause is evaluated by the verb from the folded records. Before landing, the steward re-runs
the same fold (`review_records.py fold`) on the head SHA. The `factory/review` status, which anything with push access
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
   option. A decision that OVERRULES a legal or security finding becomes a `needs-input` approval; one that upholds it
   does not.
5. Only a genuine product decision, an irreversible or sensitive choice, or an exhausted budget reaches the human: as
   ONE five-line question, through `needs-input`.

The literature behind the low round cap: most of the gain of multi-agent debate comes from the first independent
answers (NeurIPS 2025), and reviewer–critic loops drift into false agreement unless disagreement is made explicit (2026)
(*R: review-protocol.md §6.3*).

---

## 9. The spec between workers

- **Where it lives:** the spec and the acceptance tests are committed on the pushed issue branch, with a PR that
  carries `do-not-merge`, and is also a draft where the forge supports drafts [B22]. GitHub offers drafts in private
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
- **A short AC list on the issue**, so the human can follow the work in the tracker without opening the branch.
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

### 10.3 Track E: the environment restore (the deploy job; needs no attribution) [B17]

1. **Pre-flight**, seconds, before anything changes: IAM simulation of the actions the new templates need,
   export-in-use check, change-set validation.
2. **Deploy** with a result per stack. Independent stacks keep deploying after one fails, so a deploy shows more than
   one defect.
3. **Smoke**, retried once.
4. **On a failure**, the job restores INSIDE THE SAME RUN, in the same concurrency slot (a separately dispatched restore
   could be superseded by a pending deploy):
   1. it takes the last green commit's cloud assembly from the cache, and verifies the assembly's SHA-256 against the
      digest the trunk verdict recorded for it;
   2. it computes the restore's change set and runs the **stateful replacement/deletion check on it**. A restore that
      would delete or replace a stateful or retained resource, or put old code on a migrated schema, STOPS and becomes an
      `env-incident` for the owner (§12.5);
   3. otherwise it redeploys only the stacks whose template changed, consumers before producers, with
      `cdk deploy --app <cached assembly> <stack> --exclusively`;
   4. it runs the smoke again.
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
   window newly uses, a red restore without stateful change, a failed rollback. None of these blames an issue.
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
3. **Revert** [B14]:
   - The steward opens `git revert -m 1 <merge>` as a PR labelled `revert`, whose commit carries a `Reverts-PR: #<n>`
     trailer.
   - On GitHub a PR created with `GITHUB_TOKEN` starts no workflow, so the steward dispatches the revert PR's CI itself
     with `workflow_dispatch`, the one event that token may start. Alternatively a `revert` PR is exempt from
     `require_pr_ci`, because its train CI is its CI.
   - `plan()` orders `revert` PRs first, so the revert is train 1 of the next batch.
   - Landings never pause; while red, a batch is capped small (the revert plus at most k PRs).
4. **Deploy guard while the revert is pending** [C18]: the deploy job skips trunk commits that contain an attributed
   culprit without its revert. The environment stays on the restored version instead of being broken and restored again
   by every deploy.
5. **The next green deploy** confirms the attribution and verifies the innocent landings by ancestry. A red one with the
   same signature means the attribution was wrong: revert the next suspect, and **refund** the counters the wrong
   attribution charged to the innocent issue (§13) [B16].
6. **Escalate** after two wrong attributions in a row, or after a red streak longer than the configured clock (suggested
   4 h), by opening an `env-incident` issue (§12.5) [B13].

### 10.5 How issues react [B11]

**A red deploy or smoke verdict marks no issue by itself.** It records `red-since` and hands the window to Track T. Only
Track T's culprit record returns an issue; today's blame-all return is removed (H8).

| Role in the red window | Effect |
|---|---|
| Culprit | → REWORK-REQUIRED (steward). The revert's trailer and the `reverted PR #<n> <merge> in <revert>` line name the PR. The rework branch starts with a revert of the revert: git brings nothing back when a reverted merge is merged again |
| Culprit whose fix needs a grant (e.g. an IAM action) | as above, plus `needs-input` of kind approval: the human is asked only for the grant |
| Innocent in the window | stays in TEST-READY, untouched; the next green deploy containing it verifies it; no rework, no re-landing |
| Reverted as an ambiguous suspect | stays in TEST-READY. The steward relands it itself, in bisection order; no worker involved |
| Landed after the red began | unchanged (the existing red-streak rule) |
| Infra red | no issue changes; an `env-incident` issue with its owner |

### 10.6 What each AWS project provides

| Tier | The project provides | NFT after a smoke failure |
|---|---|---|
| **Minimum (REQUIRED, decision U20)** | cached cloud assemblies per deployed SHA; a deploy script that redeploys named stacks from a given assembly; a per-stack result file; CloudFormation rollback on; ECS deployment circuit breaker; custom-resource timeouts; an IAM action manifest; a smoke check that runs standalone | est. 5–30 min (against 1.5–3 h today) |
| Better | stateful stacks split out with stack policies; the smoke for user-facing entry points as pre-traffic hooks (traffic never reaches a broken version); expand–contract migrations | ≈ 0 for hooked components |
| Best | blue/green with bake time for all compute; feature flags | seconds |

**The cache** [B17]:

- It lives in an S3 bucket in the dev account, with retention at least the `cdk gc` rollback buffer (decision M1).
  Chess already hit the GitHub artifact storage limit.
- **Only the deploy job's role may write it.** The trunk verdict records each cached assembly's SHA-256, and the
  restore verifies it before use.

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

### 10.8 Hazards in today's code that revert-first triggers (fix together with it)

- **H1. A reverted culprit gets closed** [B15].
  - **Today:** the verdict verifies an issue when its last landing line names an ancestor of the deployed commit. A
    reverted landing stays an ancestor, and `last_landing` takes the newest line of ANY PR.
  - **Fix:** landings and reverts are recorded per PR and derived from trunk's first-parent history (`Steward-PR` /
    `Reverts-PR` trailers). The predicate holds only when EVERY PR of the issue has a landing no later revert of THAT PR
    supersedes. A revert counts from the moment it lands.
- **H2. Re-merging a reverted merge brings nothing back** unless the revert is reverted first.
- **H3. A restore must not count as a trunk verdict:** record `<env> serving <sha> (restored)`.
- **H4. A separately dispatched restore can be superseded** by a pending trunk deploy, so it runs inside the failing run.
- **H5. A revert can itself be undeployable:** a later landing imports the export it removes, or it undoes a migration.
  The prevention checks also run on reverts.
- **H6. Serial stack masking hides later defects:** a result per stack, and independent stacks keep deploying.
- **H7. Forged machine lines** [B7].
  - **Today:** any commenter can post `merge-steward: landed <sha>`, and the code ignores the author.
  - **Fix:** landings come from trunk history (H1); comments are projections. Parsing machine lines only from the
    steward's identity is a second layer: a workflow on a worker's own PR branch can also post as
    `github-actions[bot]`.
- **H8. Blame-all red verdict:** removed (§10.5) [B11].
- **H9. The watcher closes issues itself** [B12]: `verify_issue` never closes. On success it transitions TEST-READY →
  CLOSE-READY, and the close-out team closes.
- **H10. Steward-opened PRs get no PR CI on GitHub** [B14]: the dispatch, the CI exemption and the ordering of §10.4 step
  3.

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

   Every temporary resource is **tagged** `factory-issue=<repo>#<n>`, or named with that prefix where the resource
   type has no tags. Each team also records it in a temporary-resource ledger on the issue (one machine line per
   resource: kind, id, environment, created-by). CLOSE-READY removes what the ledger names AND what a query by the tag
   finds. The exit predicate requires both to be empty.

   Chess #1130 is the motivating case: it left 1,000 staged uploads, which nobody recorded, and they later blocked other
   issues' deploy checks.
2. **New issues uncovered by the deployment, even a successful one,** under the filing discipline (observed defects
   only; zero is a valid result). The sources:
   - the close-out's scan of the deploy window's logs, where the project provides a read-only log query [T-13];
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

## 12. Human input (decisions U1, U12, U14, U17, U21)

### 12.1 The `needs-input` lifecycle

- **Blocking question:** set `needs-input`, release the claim, pull other work. No unattended worker ever blocks on an
  interactive question. Asking interactively stays only in a session the human is actively driving.
- **Reversible decision:** proceed with the recommended option and record it as an assumption the human may override
  (decision U12). An override after the spec stage becomes REWORK-REQUIRED or SPEC-REQUIRED; after the landing, a new
  issue.
- **Format:** every question is a record in the five-line shape of `clients/claude/rules/continuous-work.md` (one line
  of context, two to four options with consequences, the recommended option first), with an id and
  blocking/non-blocking.

### 12.2 Decision inventory, up front

At START and at SPEC entry, the maker lists EVERY decision and human input the issue will need through to CLOSE-READY:

- product choices;
- inputs (accounts, data, folders);
- permissions;
- sign-offs.

All of them go out in ONE batch. A question raised later must state why it was not foreseeable. A foreseeable late
question is a defect of the spec stage, recorded in the retro.

### 12.3 Equal scrutiny, and why authorship still matters for reserved decisions [A4, P12]

Every input is judged on its content: the operator's, an agent's, an outsider's (decision U21). An answer from the
operator does not skip a checker. When it leads to an artefact, that artefact faces every lane like any other. An
outsider's comment can be a valid bug report and is read as one.

Authorship decides only WHO may make a **reserved decision**. A reserved decision is a question the question checker
(§12.4) found no agent may answer:

- irreversible;
- sensitive;
- a genuine product decision;
- a grant or an approval.

It matters there for a reason that has nothing to do with trusting the operator more:

1. **Maker ≠ checker for decisions.** A decision is reserved because no agent may make it. If an agent's comment could
   answer it, the agent that escalated the question would answer its own escalation. The design's own rule says it may
   not.
2. **Outsiders.** On a public repository any signed-in user can comment. Their text is data, never a decision on the
   project's behalf (§8.3).
3. **Irreversible operations** (a production deploy, a deletion, an IAM grant) are additionally gated by forge
   mechanisms bound to the human's own credentials. Example: a protected environment with a required reviewer. The
   agents' tokens lack that permission (§15.2).

Everything else, including answers to non-blocking questions, findings and comments, is judged on content alone,
whoever wrote it.

### 12.4 The question checker (maker ≠ checker for questions) [C12]

Before anything reaches the human, a separate agent tries to answer it from the spec, the issue, the codebase, the
docs, the decision records and the steering. Only these pass, the four Proven Exceptions of `continuous-work.md`:

- irreversible;
- sensitive;
- a genuine product decision;
- a hard blocker.

A deterministic **always-ask list** passes regardless of the checker's view: IAM grants, deletions of data or
resources, anything touching production, credentials. A false "answerable" on those would let an agent decide what is
reserved.

### 12.5 Routing by kind; environment incidents [B13]

Environment health, credentials and dependency or contention never become an issue's question.

| Kind | Goes to |
|---|---|
| Environment health, credentials | ONE open issue per root cause, labelled `env-incident` and `needs-input` for its owner, deduped across issues. The affected issues are `blocked-by` it, and released when it closes |
| Dependency, contention | `blocked-by #N`, or the merge steward |

The `delivery-status` issue stays what it is today: a closed issue whose body is the steward's machine status record. It
never carries escalations, because `/get-guidance` lists only open `needs-input` issues.

Example from the data: the same Security Hub finding (SSM.1) was asked about from four different issues.

### 12.6 Standing permissions are policy

Examples:

- "agents may dispatch the prod deploy after a green stage";
- "agents may change IAM in the shared dev account".

They are asked once per project and recorded as a decision record or steering line, never per issue again.

### 12.7 Recording answers [B4]

An answer can arrive two ways; both end the same.

- **Directly on the issue:** the dispatcher lists `needs-input` issues that have an authorised human's comment newer
  than the last open question. It starts the **answer recorder**, a headless role that makes no decision. The recorder
  turns the comment into a `factory: answer Q-<n> = <option or text> (by <login>, comment <id>)` record, and clears
  `needs-input` when no blocking question is left.
- **Through `/get-guidance`**, interactively (§12.9).

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
4. **Record** each answer verbatim on every affected issue, as the recorder does (§12.7).
5. **Transition** only when the answer clearly sends the issue to another stage; otherwise the next worker in the stage
   reads the answer.
6. **Generalise:** offer to turn a general answer into a decision record or steering line, so it is not asked again.
7. **End** with a fixed summary. The command can be stopped at any point, because all state is on the issues.

### 12.10 Optional approval setting (decision U17) [T-07]

Off by default; no stage requires a human. A project that needs one (e.g. a bank, or AI-DLC's "implements after a human
validates") switches it on for:

- **specs** of tier M/L or with chosen risk tags: a clause of SPEC-REQUIRED → IMPLEMENTATION-READY;
- **sensitive paths** of a PR, e.g. `iam/**`, `auth/**`: a clause of IMPLEMENTATION-READY → TEST-READY and of
  REWORK-REQUIRED → TEST-READY. It covers paths the spec did not declare.

The approval arrives as one batched `needs-input` of kind approval through `/get-guidance`, while independent work
continues. It is a reserved decision (§12.3).

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

**Where the counts come from** [C21, T-02]:

- Every counter is derived from the verb's audit lines and the steward's records, never from editable comments.
- **Cost:** every worker appends `factory: spend tokens=<n> usd=<x> by <worker>/<agent>` at each checkpoint and at
  release, from its harness's usage report. The verb sums these lines per issue, so the cost budget can trip across
  machines and sessions.

**Calibration** [C6]:

- The thresholds come from single-session flows with about 97 % cache reads. Each hand-off and each cross-session lane
  starts cold, so the new flow will cost more.
- For the first 20 issues per tier, all budgets are **report-only**. Then they are recalibrated from the spend lines.

**Resets:**

- per stage visit: review, verifier and question counters. Re-entering SPEC gets half the cap, so REWORK ↔ SPEC
  ping-pong gets no fresh budget.
- per PR: CI rounds.
- never by a worker: queue returns, culprit failures, rework, claims and cost. Only an authorised human's answer raises
  the limit of the counter that tripped.
- **Refunds:** a wrong attribution (§10.4) refunds the counters it charged [B16].

**What does not count as a bounce:** infra failures, flakes fixed by a re-run of the same SHA, landing into an
already-red environment, and conflicts an automatic rebase resolves.

**Expected escalation rate from budgets:** about 2–3 %, falling towards 1 % with culprit-only attribution (measured for
the tracker counters alone: 1.3 % pooled). Today's time tripwires do not fit elapsed time (89 % of S issues take more
than 3 h from claim to merge, mostly waiting), so any time budget counts active time only.

---

## 14. Scheduling: the dispatcher

Hand-offs between stages are safe only if something guarantees a worker for every non-empty queue. Decision A2 of
2026-11-02 ("the session owns its PR until it lands") was taken because hand-offs stranded: 0 of 10 closed, since no one
picked returned work up. The dispatcher is what lets this design reverse A2.

- **Polling, not webhooks:** a workstation cannot receive forge webhooks (*R: webhook-triggers-analysis-2026-11-06*, in
  `docs/reports/`). The dispatcher polls the tracker every few minutes. It runs the reconciler (§4.4) and the reaper
  (§5.2), and counts pullable work in these **queues** [B3, B4]:

| Queue | Pullable when | Role started |
|---|---|---|
| one per worker stage (START, SPEC-REQUIRED, IMPLEMENTATION-READY, REWORK-REQUIRED, CLOSE-READY) | no claim, no `hold`, no `needs-input`, no open `blocked-by`, no `ci-pending`, no `review-verify` | the stage's maker team |
| one per checker lane | `review-verify` with a resolution waiting for that lane | that lane, with a verify claim (§5.3) |
| verifier | `ci-pending` and the PR's CI run has ended | the adversarial verifier, which completes or refuses IMPLEMENTATION-READY → TEST-READY |
| answer recorder | `needs-input` with an authorised human comment newer than the last open question | the answer recorder (§12.7) |

- **Pull order:**
  1. anything with `priority:critical`, whatever its stage [T-09];
  2. then right to left: REWORK-REQUIRED, the lane and verifier queues, CLOSE-READY, IMPLEMENTATION-READY,
     SPEC-REQUIRED, START;
  3. then priority within a queue.

  The human sets priority with labels. While trunk is red or nothing is ready for implementation, workers write specs
  rather than idle (decision U8).
- **Footprint-aware selection:** between equals, prefer an issue whose declared footprint does not overlap work in
  flight. The steward already does this inside a batch.
- **Capacity** per role and per host is configured.
- **Host and worker start are open** (O12) [T-03]. The candidates:
  - Kiro Crew (cron, a heartbeat crew);
  - headless CLI runs on CI runners;
  - a scheduled task on a workstation.

  For each client, the design still needs the command that starts a worker with a role and an issue, and the
  governance it inherits: the same rules, hooks and tool allow-lists as an interactive session [T-17]. The dispatcher
  makes no code changes. It needs tracker read access, the reconciler's and reaper's write scope, and the ability to
  start a worker.

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
5. No deploy credentials in a session that reads untrusted content: logs, issue text, web pages.
6. An "untrusted input" line in every checker prompt.

### 15.2 Identity, credentials and the write budget [B9, B10, A4, B6]

**Decision U24 (2026-11-16): the agents keep posting as the operator's account.** Today one token is copied to every
machine; the design changes the tokens, not the account.

**What that requires:**

- **One fine-grained token per host**: scoped to the project repositories, expiring, revocable alone. A leaked laptop
  is then revoked without touching the others.
- The dispatcher gets a token limited to what it writes.
- The worker tokens LACK the permissions behind irreversible operations, such as approving a protected deployment or
  administering the repository. Those stay with the human's own credentials (§12.3).
- **The write budget:** GitHub limits content-creating requests to 80 per minute and 500 per hour per account, shared by
  every worker, every project and the operator's own UI. GitLab's note limit is higher, 300 per minute per user. The
  design spends less of it:
  - one envelope per review round (§8.2);
  - claims and lease renewals over the git protocol, not REST (§5);
  - PR projections off by default;
  - a host-wide token bucket in the wrapper that honours `retry-after`.

  Revision 1's estimate of about 160 content writes per tier-M issue drops by roughly the number of lanes per round;
  this is not measured.

**The accepted residual.** Under the shared account, a compromised agent could post an unmarked comment and pose as the
authorised human for a reserved decision (§12.3). What limits it:

- **P12:** the artefact that follows still faces every checker;
- **forge-bound gates:** irreversible operations stay with the human's own credentials, which the per-host tokens lack;
- **the wrapper:** it marks every agent write, so an unmarked comment from the shared login can only come from outside
  it.

The decision itself could still be forged. That is recorded, not designed away.

**A second, separate consequence:** the agents and the operator's own UI share one write budget, so the reductions above
are binding, not optional.

**If this is revisited**, the two alternatives considered were:

- a separate machine account for all agents: the human's comments become provable by author, and the agents get their
  own write budget;
- a GitHub App plus GitLab bot tokens: the strongest separation, with check runs and its own rate budget, but more
  setup.

---

## 16. Client parity and distribution

- **What lives where.** The state machine (transition verb, claim refs, records, budgets) lives in the wrappers and CI,
  so Claude Code and Kiro enforce it the same way. Lease renewal happens in the wrapper on every verb call, not in a
  prompt, which matters on Kiro [C17]. Client hooks add the in-session guardrails each harness supports.
- **Kiro's missing pieces** are covered by the cross-machine machinery: no session watchdog (the lease reaper replaces
  it), no StopFailure event (the lease expires), no session cron (the dispatcher).
- **The stop gates must change** [T-11]. Today the issue-loop brake refuses a loop's DONE while a queued PR has not
  landed, and `Phase: HANDED_OFF` needs `check-handoff`. Under this design a worker's turn ends correctly when its claim
  ends in a valid transition, a `needs-input`, a `ci-pending` or a release. The release vocabulary of
  `clients/claude/docs/run-identity.md` and the gates must accept that. Headless workers end with a machine-readable
  verdict line in place of the interactive SESSION verdict.
- **The phase-2 renderer is a precondition** [T-14]. The design adds about 14 agent roles that do not exist yet:
  - triage worker, triage checker, duplicate-confirmer;
  - acceptance-test author;
  - threat-model maker and checker;
  - logic-bug reviewer, unnecessary-code reviewer;
  - failure attributor;
  - close-out worker, retro checker;
  - question checker, answer recorder, arbiter.

  There is also the split of two agents into maker and checker. Kept by hand as Claude and Kiro twins, that grows the
  twin set by about 70 %. The renderer (`docs/reports/directory-restructure-proposal-2026-11-07.md`) generates both
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
- cost per issue, per tier and per model.

A digest (the `/delivery-status` option D2 of `docs/reports/session-endings-analysis-2026-11-01.md`) prints them per
project. It is also where close-out summaries (§11) and elapsed-time alarms (§13) reach the human.

---

## 18. What would change in the framework (for planning, not now)

| Area | New | Changed | Reused |
|---|---|---|---|
| Tracker state | stage labels, the transition verb with intent/done lines, the reconciler | — | the additive label primitives |
| Claims | the claim ref with fencing token and lease; the reaper; ONE release verb | `start-issue`/`release-issue` become the ref protocol; the `mkdir` lock stays a same-clone optimisation | — |
| Authority | the role table (§4.5); human and machine allow-lists per project | every writer calls the verb instead of writing labels | — |
| Spec hand-off | `spec-approved` record, ask hash, `/amend`, acceptance tests at spec time, the test-freeze run | the orchestrator's FIX splits into SPEC and IMPLEMENTATION teams | the spec phases, the review panel, the tiers |
| Review exchange | `factory-review/v1` records with `actor.agent` and `notVerified`; a validation and fold script; one envelope per round; the arbiter | the review lanes emit records instead of prose files | the review contract's materiality rules |
| Checkers | IaC gate, OSV-Scanner, diff coverage, spec lint, logic-bug reviewer, threat-model lane, triage checker, duplicate-confirmer, retro checker, answer recorder; optional external security review and pen test | housekeeping and doc-reviewer split into maker and checker | the existing lanes |
| Delivery (`merge_steward.py`, templates) | Track E restore with the restore guard and the cache digest; Track T attribution and revert PRs with `Reverts-PR` trailers; the deploy guard for pending reverts | the red verdict marks no issue (H8); `verify_issue` transitions instead of closing (H9); landings and reverts per PR from trunk trailers (H1, H7); revert PR CI dispatch and revert-first ordering (H10); attribution from first-parent merges | trains, ancestry verification, `delivery-status` as a status record |
| Wrapper | comment paging with an id filter; the cursor in the claim ref; the continuation issue; the write token bucket | the GitLab fold orders by note id | the forge API packages |
| Human input | `/get-guidance`, the answer recorder, the question checker with its always-ask list, the decision inventory, standing-permission records, `env-incident` issues | `continuous-work.md` escalation text | the five-line question shape |
| Gates and harness | a headless verdict line | the stop gates and the release vocabulary accept a transition, `needs-input`, `ci-pending` or a release as a valid end [T-11]; `proportionality.md`'s tier-S path is unchanged [C7] | the remaining gates |
| Scheduling | the dispatcher with its queues | decision A2 reversed | — |
| Clients | the phase-2 renderer first [T-14] | — | — |
| Setup | the Minimum revert tier required for AWS projects; pinned MCP servers; strict MCP config for checkers; per-host fine-grained tokens | both setup prompts and the update prompt | — |

**Small defects found on the way**, to fix when the framework is changed:

- `clients/claude/agents/spec-review-agent.md` repeats one paragraph.
- `clients/claude/docs/dead-code-language-matrix.md` lists `ts-prune` as required, although it is in maintenance mode
  and knip covers it.
- `clients/common/docs/delivery.md` §4 calls the `delivery-status` issue open, while the code keeps it closed [D2].
- The two maker-checker agents named in §7.2.

---

## 19. Known weaknesses: where a reviewer should push

1. **Custom ref namespaces** (§5.1). Whether GitHub and GitLab accept pushes to `refs/factory/claims/*`, and their
   exact refusal on a lease mismatch, is unverified. There is a branch-prefix fallback. To verify on `sff-test-*`
   repositories (O14).
2. **The fencing window** (§5.2). An expired holder can still write until its next verb call, so a step must stay short
   enough that L covers it.
3. **Identity** (§15.2, U24). Under the shared account, which the operator chose to keep, a compromised agent can forge
   a reserved decision. P12, the forge-bound gates and the wrapper's marking limit, but do not remove, that accepted
   risk.
4. **Immutability** [T-08]. Audit lines and records are comments the shared account can delete. The fold rejects
   edited records, but nothing stops a deletion. The option is a digest of the folded records written to a protected
   audit ref at close-out (O15).
5. **The write budget** (§15.2). The reduced write volume is estimated, not measured.
6. **Hand-off cost** [C6]. Cold starts make the decoupled flow costlier than the data the budgets were set from.
   Budgets are report-only until recalibrated.
7. **Smoke attribution is heuristic** (§10.4, step 2.4). A wrong guess costs one deploy, one reland and a refund, never
   a broken trunk, but repeated wrong guesses lengthen VBT.
8. **The arbiter's authority** (§8.7). Its decision is re-checked by the lanes' deterministic checks and escalated when
   it overrules security. Whether it simply sides with the more confident lane on judgement calls is still open.
9. **The learning-batch issue** (§11) is the designer's proposal (M5).
10. **Not designed here:**
    - automated capture of corrections and recurrence counting (gap-analysis 2.5);
    - backlog drift measurement (gap-analysis row 11);
    - the Jira wrapper (gap-analysis 3.8);
    - the details of the production intake (gap-analysis 2.6);
    - the contract-drift check per project (gap-analysis 3.7);
    - per-agent deny rules and Kiro's central allow-lists (gap-analysis 3.2);
    - a living system spec (gap-analysis 2.8);
    - the dispatcher's host and worker start (O12).

    [traceability.md](traceability.md) lists them.
