# Factory state model: design (draft for review, 2026-11-11)

Status: design only. Nothing described here is implemented unless §2 says it exists today. Decisions are
listed with their source in [decisions.md](decisions.md); coverage of the keynote and of the gap analysis is in
[traceability.md](traceability.md). The research behind each section is in
[`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/), cited as *(R: file)*.

Words used throughout:

- **stage**: the one state an open issue is in (§3).
- **flag**: an orthogonal marker, such as `needs-input` or `blocked-by`.
- **claim**: the lease a worker holds on an issue.
- **maker / checker**: the agent that produces an artefact, and an agent or tool that judges it.
- **team**: the makers and checkers working one stage of one issue.

---

## 1. Goal and principles

The goal: the operator talks to the projects only through the backlog. Every issue, once created, is picked up by
workers (Claude Code, Kiro, Kiro Crew) on any machine and moved to a verified, closed state without waiting for
anyone, with the human as the rare exception.

| # | Principle | Consequence in this design |
|---|---|---|
| P1 | The backlog is the only interface | The issue and its comments hold everything another worker needs; machine-local run state is a cache, never the source of truth |
| P2 | Workers never wait | Every wait has one owner that is not a worker: a human answer (`needs-input`), CI and merge (the merge steward), deploy and smoke (the deploy pipeline and the verdict watcher). The worker releases and pulls other work |
| P3 | Any number of workers, any machine, any client, one shared tracker account | Claims are leases arbitrated by the server's comment order, not by the account (§5) |
| P4 | Maker ≠ checker | Every stage has dedicated checkers; a maker never grades its own artefact (§7, §8) |
| P5 | Every stage has a deterministically checkable finish line; the team loops until it holds | A script, the transition verb, evaluates it from tracker + git + CI state (§4) |
| P6 | The human is the last-resort conflict resolver | No human-only stage or gate. Questions only when no agent can answer them, in ONE batch, never drip-fed (§12). An optional per-project approval setting exists, off by default |
| P7 | Shared environments; batched delivery; revert first | One CI or deploy run covers many issues. A failed deploy or smoke is restored first, then attributed (§10) |
| P8 | Effort proportional to the ask | Tiers S/M/L decide artefacts, panels and budgets (`clients/claude/rules/proportionality.md`); one claim may carry a small issue through several stages |
| P9 | Enforcement is client-neutral | The state machine lives in the wrapper scripts and CI, which Claude Code and Kiro both run, not only in one client's hooks |
| P10 | File-based distribution per project | The framework stays copied into each project by the setup and update prompts (`prompts/setup-claude.txt`, `prompts/setup-kiro.txt`, `prompts/update.txt`); a plugin is a future option (§16) |

---

## 2. Starting point: what exists and is reused

| Capability | Exists today | Where |
|---|---|---|
| Merge queue with cumulative trains: train k = trunk + the first k PRs; land the longest green prefix; blame only the newest PR of the first red train; one retry for a first failure | yes | `src/payload/scripts/merge_steward.py` (docstring "ONE TICK") |
| Post-deploy verification by git ancestry, red-streak attribution, the `delivery-status` issue | yes | `merge_steward.py` `verdict`; `clients/common/docs/delivery.md` §4 |
| Delivery labels: `queue`, `queue-failed`, `queue-conflict`, `needs-rework`, `awaiting-verification`, `verification-failed`, `needs-closeout`, `reverify` | yes | `clients/common/docs/delivery.md` §6 |
| Tiers, byte caps, review panel with caps (S 2, M 4/2, L 6/3), materiality gating of findings A–D | yes | `clients/claude/rules/proportionality.md`, `clients/common/docs/review-contract.md`, `clients/common/phases/spec-phase-review.md` |
| Test-first waves, red for the right reason, the adversarial verifier, evidence reports | yes | `src/hooks/red_for_right_reason.py`, `clients/common/phases/spec-phase-implement.md` |
| Filing discipline (observed defects only, fix first, findings ledger) | yes | `clients/claude/rules/issue-filing-discipline.md` |
| Claim: label + assignee + re-read | yes, but unsafe across machines (§5.4) | `src/payload/scripts/github_api/commands/claim.py` |
| Triage, spec and questions as tracker states | **no**. They happen inside one session; the spec lives in that session's worktree until the PR | `clients/claude/agents/issue-work-orchestrator.md` (FIX) |
| A machine-readable "waiting for the human" on the issue | **no**. An ambiguous issue gets a comment and a released claim; `AWAITING_USER` lives in a machine-local file | same |
| Something that starts workers on its own | **no**. Sessions are opened by the operator | — |
| Revert after a failed deploy | **no** | `docs/reports/red-pipeline-analysis-2026-11-02.md` |

The design keeps the delivery half (steward, watcher, labels) and adds the front half and the cross-machine
machinery.

---

## 3. The state model

### 3.1 Stages (exactly one per open issue)

Each stage is a **queue** named for the next kind of work the issue needs. Being worked on is the claim, not a
stage.

| Stage | Meaning | Pulled by | Leaves to |
|---|---|---|---|
| **START** | New; no work done yet. An issue without a stage label is in START | triage worker | SPEC-REQUIRED; closed administratively (duplicate, invalid, won't do); split into child issues |
| **SPEC-REQUIRED** | Triaged; it needs a spec and acceptance tests | spec team | IMPLEMENTATION-READY |
| **IMPLEMENTATION-READY** | A reviewed spec at a pinned commit, failing acceptance tests that define "done", no blocking question | implementation team | TEST-READY |
| **TEST-READY** | The PR is in the merge queue, then landed, then deployed and smoke-tested. Owned by the steward and the deploy pipeline; never claimed by a worker | merge steward, deploy pipeline, verdict watcher | CLOSE-READY; REWORK-REQUIRED |
| **REWORK-REQUIRED** | Returned from TEST-READY with a machine-readable cause | implementation team, pulled first | TEST-READY; IMPLEMENTATION-READY; SPEC-REQUIRED |
| **CLOSE-READY** | Landed, deployed, smoke green on a commit containing the landing | close-out team | closed (done) |

TEST-READY spans queue → merge → CI → deploy → smoke (decision U7). Its internal hand-offs (queued, landed,
verified) are machine lines on the issue, not stages.

### 3.2 Flags (orthogonal to the stage)

| Flag | Meaning | Set by | Cleared by |
|---|---|---|---|
| `needs-input` | at least one BLOCKING question or approval is open (INPUT-REQUIRED of the original proposal, decision U1). The stage does not change, and the claim is released | any team, after its question checker (§12) | `/get-guidance` or an unmarked human answer, when no blocking question is left |
| `blocked-by #N` (native dependency where the forge has one) | cannot proceed until #N reaches a named stage | triage, spec | the dispatcher, when #N gets there |
| `hold` | the human paused it; every worker stops at its next checkpoint | the human | the human |
| `claimed` | a cheap filter for "a lease exists"; the lease itself is a comment (§5) | the claim protocol | release or reaper |
| `review-open` / `review-verify` | blocking findings wait for the maker / resolutions wait for a checker lane (§8) | the record writer | the claim holder, after the fold shows nothing pending |
| tier `S`/`M`/`L` + risk tags (`auth`, `money`, `data-migration`, `iam-iac`) | select the team, the checkers and the budgets | triage | re-tier, with a recorded reason |
| `admitted` | admission of an issue by an author outside the allow-list (§6) | the human | — |

### 3.3 Diagram

```
           (every issue, including the operator's own, goes through triage)
START ──triage──► SPEC-REQUIRED ──spec gate──► IMPLEMENTATION-READY ──PR enqueued──► TEST-READY ──deploy+smoke green──► CLOSE-READY ──► closed
  │                                                                                      │
  └──► closed (duplicate / invalid / won't do; split → children at START)                └──► REWORK-REQUIRED (culprit only; after a landing: revert first)
                                                                                                │
                                                                       back to TEST-READY | IMPLEMENTATION-READY | SPEC-REQUIRED

Flags on any open stage: needs-input · blocked-by · hold · claimed (lease) · review-open/verify · tier + risk tags
```

### 3.4 Properties

1. **States are durable checkpoints, not compulsory hand-offs.** A worker holding the claim may carry an issue
   through several stages, recording each transition with its evidence (tier S: START → TEST-READY in one claim).
   A crash leaves a checkpoint another worker resumes from. The worker that has the context in memory goes on
   when it is free; nobody ever waits for it.
2. **One writer per issue at a time:** the claim.
3. **A stage changes only through the transition verb (§4.4).** No agent sets a stage label by hand.
4. **A worker never changes the stage of an issue it does not hold.** Cross-issue moves need a group claim (§5.3).

---

## 4. Transitions and their finish lines

### 4.1 The rule that makes predicates deterministic

> A transition's predicate is evaluated by a script from tracker + git + CI state only. Its checker part is
> always the same sentence: **every checker the stage requires (by tier and risk tags) has posted a verdict on the
> artefact's CURRENT commit, and no blocking finding is open.**

Judgement happens inside the checkers. The predicate only counts their structured verdicts (§8). A verdict on an
older commit does not count, so a new commit by the maker re-opens the check, as a delta review.

### 4.2 The predicates

| Transition | Predicate (all must hold) |
|---|---|
| START → SPEC-REQUIRED | a triage record for the current hash of the ask, containing: the duplicate search (candidates and verdict), a scope verdict, tier, risk tags, estimated footprint, and the **decision inventory** (§12.2); no open blocking question |
| START → closed (duplicate / invalid / won't do) | the triage record's outcome + a SECOND agent's confirming verdict (the duplicate-confirmer). Closing destroys work, so it always gets a checker |
| START → split | every child exists at START and references the parent; the parent's stage is derived from its children |
| SPEC-REQUIRED → IMPLEMENTATION-READY | spec + acceptance tests committed at SHA S on the pushed issue branch; the acceptance tests fail for the right reason at S; every acceptance criterion is referenced by ≥ 1 test (traceability script); all required spec checkers report on S with 0 open blocking findings; no open blocking question; the approval setting, if switched on (§12.8), is satisfied; a `spec-approved` record `{sha: S, ask_hash, last_human_comment_id}` is written |
| IMPLEMENTATION-READY → TEST-READY | a PR from the branch with `Refs #N`, not draft, base = trunk; the acceptance tests unchanged since S (`git diff S..HEAD` over their paths is empty), or a newer `spec-approved` covers them; PR CI green on head H, including every acceptance test (or pending, see below); all required implementation checkers report on H with 0 open blocking findings; the evidence report present; the steward accepts the PR (`check-pr` exit 0; `enqueue --allow-pending` admits a PR whose own CI is still running) |
| TEST-READY → CLOSE-READY | the steward's landing line exists and is not superseded by a `reverted` line (§10.8 H1); a deploy + smoke run concluded green on a commit D that contains the landing (ancestry); every `(post-deploy)` checklist item ticked |
| TEST-READY → REWORK-REQUIRED | a steward record names this PR the culprit, a conflict or a PR-CI red; OR a `reverted` record after a failed deploy or smoke names this issue the culprit; OR a blocking finding was raised on the queued PR (`review-open` dequeues it) |
| REWORK-REQUIRED → TEST-READY | the IMPLEMENTATION-READY → TEST-READY predicate on the new head, plus a resolution record answering the rework cause (e.g. the job that failed is green on the new head) |
| REWORK-REQUIRED → IMPLEMENTATION-READY / SPEC-REQUIRED | a rework-analysis record that classifies the root cause as **code** or **requirement** and says what must change; the target stage's own predicates then apply from scratch. A requirement cause amends the acceptance criteria before code is touched (closes gap-analysis 2.8) |
| CLOSE-READY → closed | the close-out record (§11): every temporary resource the issue recorded is removed or handed over; every laundry-list item has a disposition; the structured summary is posted; checklist complete; no open PR references the issue; the remote branch is gone |

### 4.3 Pickup preconditions (checked when a worker claims)

- **The ask is unchanged since approval.** At an IMPLEMENTATION-READY pickup and at every later checkpoint, the
  verb compares `ask_hash` and `last_human_comment_id` with the issue as it is now.
  - The hash covers the title and the body WITHOUT checklist tick states, because ticking edits the body.
  - A mismatch sends the issue back to SPEC-REQUIRED, where the spec checkers re-approve quickly if the change is
    immaterial.
  - After TEST-READY the code is in the queue or on trunk, so a change of mind becomes a new issue.
- **The spec base is current enough.** If the spec's declared footprint changed on trunk since S, the spec
  checkers do a delta review against the new trunk before implementation starts. This replaces a WIP cap, which
  was rejected (decision U8).
- **No `hold`, no open `blocked-by`, no `needs-input`.**

### 4.4 The transition verb and where the stage is stored

One wrapper verb for both forges, for example `transition <issue> --from <stage> --to <stage> --evidence <link>`:

1. **Compare-and-set:** it refuses if the issue is not in `--from`, or if the caller does not hold the claim.
2. It evaluates the edge's predicate (§4.2) and refuses with the unmet clause.
3. It swaps the stage label additively: it adds the new label, then removes the old one. It never writes the
   whole label set (§5.4).
4. It appends one machine line: `factory: stage <A> -> <B> by <worker> evidence <link>`.

That line is the audit trail an auditor can read (keynote caveat 1), the metrics source (§17), and the recovery
source if labels are damaged.

**Storage.** The portable code path is plain prefixed labels (`stage:spec-required`). They work on every tier of
both forges. Exclusivity is enforced by the verb, and a reconciler repairs an issue with zero or two stage labels
from the last audit line. Native single-select storage is a later option:

- GitLab scoped labels (`stage::…`): mutually exclusive by the forge, but Premium/Ultimate only.
- GitHub issue fields: organisation-level single-select, generally available since 2026-07 per GitHub; not
  available for user-owned repositories.

---

## 5. Claims

### 5.1 Protocol (works with one shared account, on the Free tier of both forges)

1. Post a claim comment: `factory: claim <stage> worker=<host>/<session> lease-until=<ISO>`.
2. Re-read the comments. The EARLIEST unexpired claim comment for that stage wins, because comment ids are
   assigned by the server.
3. The loser deletes its comment and pulls the next issue. The winner adds the `claimed` label as a query filter.
4. The lease is extended at every checkpoint by editing the comment.
5. A worker whose lease has gone, or whose issue changed stage under it (a human closed it or set `hold`), stops
   at its next checkpoint. The same reconciliation is used by OpenAI's Symphony orchestrator.

### 5.2 Expiry

A reaper (part of the dispatcher, §14) releases expired leases and returns the issue to its queue. This replaces
the session watchdog for crashed turns: a worker killed by an API error simply stops renewing.

### 5.3 Group claims

A decision that moves several issues takes all their claims, all or nothing, releasing everything if one fails.
Example: "this batch goes back to SPEC-REQUIRED". The alternative is ONE coordinating issue that the others are
`blocked-by`. Workers never negotiate in free text (§8 is the only exchange format).

### 5.4 Why today's claim is not enough (code read on 2026-11-11)

- `start-issue` refuses a claim only when a DIFFERENT login holds it (`_claim_is_held_by_another` in
  `src/payload/scripts/github_api/commands/claim.py`). Every worker posts as the same login, so a second
  machine's claim on the same issue succeeds.
- The orchestrator calls `issue start` without `--strict`. Even `--strict` reads and then writes, so two workers
  that read before either writes both succeed.
- The `mkdir` lock (`.locks/issue-<N>.lock`) serialises only workers inside ONE clone.
- `release-issue` writes the whole label set minus `in-progress`, from a fresh read. A label added by someone else
  between that read and the write is lost. With stages stored as labels this becomes a lost stage.

---

## 6. Inflows and admission

**Inflows into START:**

1. issues the operator files;
2. agent-filed issues: the feedback loop, under the filing discipline, with its provenance lines (`Origin:`,
   `Subject:`, `Spawned-from:`, `Filing-rationale:`);
3. production signals: an alarm or an AWS DevOps Agent investigation produces ONE issue through
   `issue-intake-agent` with `Origin: production`, under the same filing gate (gap-analysis 2.6);
4. close-out and retro findings (§11), under the filing discipline.

**Every issue goes through triage**, including the operator's own; there is no pass-through (decision U16). Triage
produces the triage record of §4.2.

**Admission.** The question is not whether an issue is triaged, but whether its TEXT may direct agents that can
push code and deploy to AWS.

- **Auto-admitted:** issues authored by the operator, and agent-filed issues carrying the filing gate's
  provenance lines.
- **Everything else** (other collaborators, bots, integrations, external reporters on a public repository) is
  triaged in a **read-only mode** and then waits for an `admitted` label set by the human:
  - no write tools, no AWS credentials, no forge write except the triage record itself;
  - the issue text is treated as data;
  - the triage record says what the issue asks, so the human admits it in seconds.
- **Untrusted content inside admitted issues:** log lines, web pages and error messages quoted by an agent are
  fenced and marked as data. The triage checker refuses an ask that originates in quoted untrusted text, because
  the keynote's feedback loop of filing issues from logs is exactly such a path.

---

## 7. Teams and the loop inside a stage

### 7.1 The loop

```
claim ──► maker produces or updates the artefact at SHA X
  ▲            │
  │            ▼
  │   deterministic tools on X (cheap; SARIF out) ──► findings
  │   LLM checkers on X, in parallel, given the tool output filtered to the diff ──► findings
  │            │
  │   predicate(X)? ── yes ──► transition verb ──► release, or continue to the next stage (§3.4)
  │            │ no
  │            ▼
  │   maker answers EVERY open finding: fixed@SHA / alternative / rejected-with-evidence / conflict
  │   conflict sets ──► joint resolution (§8.4)
  │            │
  └── budget left? ── no ──► needs-input with a "stuck because …" record (§13), the rare exception
```

### 7.2 The team per stage (*R: checker-landscape.md §3, mcp-and-powers.md §5, plugin-marketplaces.md §3*)

| Stage | Makers | Deterministic checkers (first) | LLM checkers (gated by tier and risk) |
|---|---|---|---|
| START | triage worker | duplicate retrieval (forge search + lexical or embedding similarity over open and recently closed issues); risk-tag and footprint heuristics; template lint | **duplicate-confirmer** (mandatory before any close); scope/sanity checker (L) |
| SPEC-REQUIRED | spec-author (+ spec-researcher); acceptance-test author; threat-model maker (L or risk tags: the awslabs threat-modeling MCP server, pinned to a commit) | AC → test traceability; red for the right reason; EARS/INCOSE spec lint (new); byte caps; threat-model schema check | test-architect (every); security-reviewer (one-line CLEAN unless a trust boundary is touched); **threat-model checker** (new; STRIDE + OWASP ASVS 5.0; L or risk tags); devops-iac-reviewer (IaC); standards / best-practice (M+); optional AWS Security Agent design review (L + auth/money, budget-capped) |
| IMPLEMENTATION-READY | spec-implementer (waves), ci-workflow-agent, code-merge-reviewer | ruff, mypy, bandit, secret scan, tests; **diff coverage on changed lines** (new); **OSV-Scanner** (new); **IaC gate: cdk-nag + cfn-lint + Checkov or cfn-guard + `cdk diff --security-only`** (new); import/architecture contracts; mutation testing on changed functions (L or risk tags); **dead/unnecessary code on the diff** (vulture or Skylos `--diff`, knip); IAM Policy Autopilot (actions the code needs vs the CDK grants) | adversarial-verifier (every); **logic-bug reviewer** (new, M+: find → verify-to-disprove → rank); standards (M+); security and devops lanes by risk tag; unnecessary-code reviewer (M+) |
| TEST-READY | merge steward, deploy pipeline | train CI; pre-flight (§10.3: IAM simulation, export-in-use, change-set validation); **stateful replacement/deletion detector** on the change set (new); smoke/E2E | failure attributor for smoke failures (CloudWatch and CloudTrail MCP, read-only); optional batch release readiness (AWS DevOps Agent) for batches with `iam-iac` |
| REWORK-REQUIRED | any implementer | the same deterministic set on the new SHA; SARIF baselines show which findings are fixed, new or unchanged | only the lanes with open findings, plus lanes whose files the fix touched (delta) |
| CLOSE-READY | close-out worker | leftover checks on the diff (TODO, debug flags); temporary-resource ledger empty (§11) | **retro checker**: every learning is backed by evidence, is not already a rule or memory, and nothing is filed without an observed defect |

Two existing agents break maker ≠ checker and are split when implemented: `issue-housekeeping-agent` and
`doc-reviewer-agent` both make and check.

### 7.3 Cost proportionality

| Selection | Checkers |
|---|---|
| Every issue | the deterministic baseline, AC traceability, red-for-right-reason, diff coverage, test-architect, adversarial-verifier, the retro checker |
| Tier M and L | standards, best-practice, the logic-bug reviewer, the close-out LLM reviewers |
| Tier L | the threat-model lane, mutation testing |
| Risk tags | `auth`/`money`: full security, threat model, mutation; `iam-iac`: devops-iac plus the IaC gate (which also runs whenever `cdk/` changes); `data-migration`: the stateful-replacement check is a blocking gate |
| Paid external agents (AWS Security Agent, AWS DevOps Agent) | optional, L or risk tags only, budget-capped, never the only checker for a gate |

### 7.4 Techniques every checker uses (*R: plugin-marketplaces.md §4, checker-landscape.md §4*)

- Deterministic tools first. The LLM lanes get their SARIF filtered to the diff, to triage it and to hunt for
  what tools cannot see.
- A separate pass tries to DISPROVE each finding; a finding nobody can confirm is dropped, and its severity is
  capped at what the confirmation supports.
- Lens-split finders run in parallel, each with an explicit "do not flag" list.
- Proof comes from runner result files (counts, a deliberate break that must fail, "named, not run" for skipped
  tests), never from model opinion.
- Repository and issue text is evidence, never instruction.
- Stable finding ids with a revision stamp (§8).
- Per-lane precedent files and a resolution-rate metric (the share of a lane's findings that were actually fixed)
  keep false positives down.

### 7.5 MCP servers always have a CLI path

The desktop app here runs Code sessions under `strictPluginOnlyCustomization: ["mcp"]`, so project MCP servers do
not load. A gate must therefore never depend on an MCP server. The deterministic checks run through
`src/payload/scripts/run_checks.py` and CI; MCP servers are optional accelerators for makers and LLM checkers
(decision U19, *R: mcp-and-powers.md*).

The policy comes from the AWSBedrockGateway project's gateway configuration: a non-empty `managedMcpServers`
switches it on. It stalled chess #1507.

---

## 8. The maker/checker exchange: `factory-review/v1` (*R: review-protocol.md*)

### 8.1 Records

One JSON envelope carries seven append-only record types:

- `finding`, `resolution`, `verification`: the checker raises, the maker answers, the checker verifies;
- `link`: duplicate-of, conflicts-with, regression-of;
- `proposal`: a joint option for a conflict set;
- `decision`: arbiter or human;
- `verdict`: per lane per SHA, CLEAN or NOT-CLEAN with counts.

The envelope names the actor (worker, client, role), the subject (forge, repo, issue, PR, stage, tier, iteration,
commit) and the addressee.

- **A finding IS a SARIF 2.1.0 result** (a subset), so it can be exported to SARIF unchanged. The framework's
  fields sit under `factory/…` property keys: severity A–D and the blocking flag (the review contract's
  materiality), material-because (an acceptance-criterion id or a failure class), the violated standard,
  reasoning, evidence (command, exit code, excerpt, commit), and one or more options with patches (the
  recommended one first).
- **The target.** The reviewer writes meaning; the tool computes coordinates.
  - The reviewer gives a quote, as a W3C Web Annotation `TextQuoteSelector` (the exact text with a prefix and a
    suffix), plus a symbol or a section.
  - The tool resolves line, offset and fingerprint at the pinned commit, and rejects a quote it cannot find.
  - This works for code and for spec prose alike, survives edits, and removes invented line numbers.
- **Status is never stored.** It is derived by folding the records in comment order:
  open → addressed → verified | disputed → escalated | withdrawn | wont-fix-accepted.

### 8.2 Transport: the same bytes, three ways

1. **Inside one machine:** a file per lane per iteration.
2. **Between machines and issues:** an issue comment.
   - Layout: a hidden marker line, a one-line Conventional-Comments rendering for humans, and the JSON in a fenced
     block inside `<details>`.
   - Rules: at most 60,000 characters (GitHub refuses more than 65,536), deterministic ids, read before write,
     never edit.
   - Placement: records go on the issue whose holder must act. Cross-issue feedback from #A about #B's work is
     posted on #B, with a pointer on #A.
   - Index: the labels `review-open` and `review-verify`; workers read new comments from a stored cursor, not
     through search.
3. **On the PR/MR, as projections:** review threads and a `factory/review` commit status, which is the gate. A
   personal token can set a commit status on both forges. Check runs would need a GitHub App, and SARIF upload a
   paid tier on private repositories.

The marker also tells agent comments from human ones (decision U10). Only comments that are written by the shared
account AND carry the marker are parsed. Everything else is human input, handled by `/get-guidance`.

### 8.3 The normal round

1. The conductor pins the SHA and dispatches every lane in one message.
2. Each lane writes its envelope, which must validate.
3. The conductor folds the records: it dedupes, flags conflict candidates (overlapping anchors with different
   fixes) and posts the aggregate.
4. The maker answers every open blocking finding in one pass.
5. Each lane verifies ONLY its own findings at the new SHA, with fresh re-run evidence. A "verified" without fresh
   evidence is invalid.

### 8.4 Multi-way resolution

A **conflict set** is formed by overlapping anchors, a `regression-of` link, a maker's `conflict` answer, or an
oscillating fingerprint. Example: the Security and the DevOps reviewer flag the same code with incompatible fixes.

1. The maker posts a proposal: at most three options, each stating for EVERY finding in the set how its rule is
   met, where possible implemented on a commit.
2. Every affected lane votes:
   - accept, with evidence from its own check re-run against the option;
   - or reject, naming the unmet clause and offering a counter-option that satisfies the whole set (a
     constructive veto).
3. After two rounds without unanimity, a fresh **arbiter** agent decides, with no transcripts, only the records,
   the ask and the evidence. Its order of reasoning:
   1. facts: re-run the evidence;
   2. an option that satisfies every finding;
   3. the configured precedence of standards, by default: legal/security > data loss > the ask's criteria and
      correctness > operability > maintainability > style.
4. Only a genuine product decision, an irreversible or sensitive choice, or an exhausted budget reaches the human:
   as ONE five-line question, through `needs-input`.

The literature behind the low round cap: most of the gain of multi-agent debate comes from the first independent
answers (NeurIPS 2025), and reviewer–critic loops drift into false agreement unless disagreement is made explicit
(2026) (*R: review-protocol.md §6.3*).

---

## 9. The spec between workers

- **Where it lives:** the spec and the acceptance tests are committed on the pushed issue branch, with a DRAFT PR.
  The implementer continues on the same branch, and one PR carries spec, tests and code. The draft PR is the
  natural place for anyone to read the spec, and the steward refuses drafts, so draft means not ready.
- **`spec-approved` record:** `{sha, ask_hash, last_human_comment_id}`. A later commit touching the spec or the
  acceptance tests invalidates readiness until the spec checkers re-approve.
- **Acceptance tests at spec time.** The spec team writes the finish line as failing tests against public
  interfaces; the implementer makes them pass and may not change them without SPEC re-entry. This is maker ≠
  checker at the level of the issue. Where tests cannot express a criterion (IaC, refactors), the spec carries a
  verification plan, e.g. an expected `cdk diff`, a smoke script or a pre-flight check.
- **A short AC list on the issue**, so the human can follow the work in the tracker without opening the branch.
- **Optional local runtime check per project** (gap-analysis 2.1): for M/L changes that alter runtime behaviour,
  the implementation team starts the service locally and runs the same E2E group the deploy pipeline runs, where
  the project can run locally. There are no throwaway shared environments (decision U9).

---

## 10. TEST-READY: batching, merge, deploy and revert first (*R: revert-and-batching.md*)

### 10.1 Batching

Two mechanisms batch changes, so there is never one wait per issue:

- **Merge:** the steward lands batches through cumulative trains and blames only the first red prefix's newest PR
  (decision U2).
- **Deploy:** the deploy pipeline deploys the latest green trunk, so one deploy carries every landing since the
  last one.

Fast-moving organisations (Slack, Amazon, Shopify's Shipit, GitHub's deploy trains, CodePipeline) handle a failed
batch deploy the same way: restore the whole batch first, then ship it again without the suspect. None of them
routinely bisects on a shared environment: every step of a bisection costs a full deploy (⌈log₂ n⌉ deploys).

### 10.2 Three clocks

| Clock | Meaning | Cure |
|---|---|---|
| Non-functional time (NFT) | the environment cannot serve | the environment restore (Track E) |
| Verification-blocked time (VBT) | no deploy containing the culprit goes green, so innocent issues cannot be verified | a fast, correct trunk revert (Track T) |
| Trunk-blocked time (TBT) | landings are paused | never pause; keep batches small while red |

Chess's 50 red hours (2026-10-31 to 11-02) were mostly VBT: CloudFormation had rolled the failing stack back.

### 10.3 Track E: the environment restore (the deploy job; needs no attribution)

1. **Pre-flight**, seconds, before anything changes: IAM simulation of the actions the new templates need,
   export-in-use check, change-set validation.
2. **Deploy** with a result per stack. Independent stacks keep deploying after one fails, so a deploy shows more
   than one defect.
3. **Smoke**, retried once.
4. **On a failure**, the job auto-restores INSIDE THE SAME RUN, in the same concurrency slot (a separately
   dispatched restore could be superseded by a pending deploy):
   1. it takes the last green commit's cloud assembly from the cache;
   2. it redeploys only the stacks whose template changed, consumers before producers, with
      `cdk deploy --app <cached assembly> <stack> --exclusively`;
   3. it runs the smoke again.
5. **Last-good also red?** Then the cause is infra, drift or a flake: nobody is blamed (the "passes without" test,
   for free). An `UPDATE_ROLLBACK_FAILED` stack gets one automatic `continue-update-rollback`, never with skipped
   resources, and then becomes an infra event with the environment owner.

A naive revert rebuilds everything: chess's deploy job took a median of 94 min. The restore needs neither a
build nor synthesis.

### 10.4 Track T: the trunk revert (the steward; needs attribution)

1. **Classify infra first:** credentials, throttling, quota, runner loss, an `AccessDenied` on an action no PR in
   the window newly uses, a red restore, a failed rollback. None of these blames an issue.
2. **Attribute, stopping at the first conclusive step:**
   1. one landing in the window: that is the culprit;
   2. a deploy-stage failure: diff the failing stack's synthesized template across the window's cumulative states
      (the steward's train branches already are those states). The first step that changes the failing resource,
      or removes the named export or permission, is the culprit;
   3. a pre-flight failure names the step itself;
   4. a smoke failure: drop the PRs that produce an identical cloud assembly and touch no deploy footprint, then
      rank the rest by overlap with the failing checks;
   5. still ambiguous: revert every suspect.
3. **Revert** with `git revert -m 1 <merge>`, opened at once as **train 1 of the next batch**. Landings never pause;
   while red, a batch is capped small (the revert plus at most k PRs).
4. **The next green deploy** confirms the attribution and verifies the innocent landings by ancestry. A red one
   with the same signature means the attribution was wrong: revert the next suspect.
5. **Escalate** on the `delivery-status` issue after two wrong attributions in a row, or after a red streak longer
   than the configured clock (suggested 4 h).

### 10.5 How issues react

| Role in the red window | Effect |
|---|---|
| Culprit | → REWORK-REQUIRED with `reverted <landing> in <sha> (method, confidence)`. The rework branch starts with a revert of the revert: git brings nothing back when a reverted merge is merged again |
| Culprit whose fix needs a grant (e.g. an IAM action) | as above, plus `needs-input` of kind approval: the human is asked only for the grant |
| Innocent in the window | stays in TEST-READY; the next green deploy containing it verifies it; no rework, no re-landing |
| Reverted as an ambiguous suspect | stays in TEST-READY. The steward relands it itself, in bisection order; no worker involved |
| Landed after the red began | unchanged (the existing red-streak rule) |
| Infra red | no issue changes; the `delivery-status` issue records it with its owner |

### 10.6 What each AWS project provides

| Tier | The project provides | NFT after a smoke failure |
|---|---|---|
| **Minimum (REQUIRED, decision U20)** | cached cloud assemblies per deployed SHA; a deploy script that redeploys named stacks from a given assembly; a per-stack result file; CloudFormation rollback on; ECS deployment circuit breaker; custom-resource timeouts; an IAM action manifest; a smoke check that runs standalone | est. 5–30 min (against 1.5–3 h today) |
| Better | stateful stacks split out with stack policies; the smoke for user-facing entry points as pre-traffic hooks (traffic never reaches a broken version); expand–contract migrations | ≈ 0 for hooked components |
| Best | blue/green with bake time for all compute; feature flags | seconds |

**The cache** lives in an S3 bucket in the dev account, with retention at least the `cdk gc` rollback buffer
(decision M1). Chess already hit the GitHub artifact storage limit.

### 10.7 Prevention in the train (before the shared deploy)

These checks keep deploy-breaking changes out of the shared deploy:

- export-in-use compatibility;
- IAM simulation for the deploy role;
- the stateful replacement/deletion detector;
- the expand–contract migration lint;
- a revert-safety check on revert PRs.

Replay of chess #566: the export check would have refused it in the train (0 h red). Without the check, the design
gives about 2.5 h red, against about 44 h after the cause was known.

### 10.8 Hazards in today's code that revert-first triggers (fix together with it)

- **H1. A reverted culprit gets closed.** The verdict (`merge_steward.py` `verdict`) verifies an issue when its
  last landing is an ancestor of the deployed commit. A reverted landing stays an ancestor, so the first green
  deploy after the revert would close the culprit. A `reverted` line must supersede the landing.
- **H2. Re-merging a reverted merge brings nothing back** unless the revert is reverted first.
- **H3. A restore must not count as a trunk verdict:** record `<env> serving <sha> (restored)`.
- **H4. A separately dispatched restore can be superseded** by a pending trunk deploy, so it runs inside the
  failing run.
- **H5. A revert can itself be undeployable:** a later landing imports the export it removes, or it undoes a
  migration. The prevention checks also run on reverts.
- **H6. Serial stack masking hides later defects:** a result per stack, and independent stacks keep deploying.

Not fixable by a faster revert: a failed rollback, an irreversible migration, a replaced stateful resource. These
need the prevention checks and an owner.

---

## 11. CLOSE-READY (decision U18)

CLOSE-READY is NOT code clean-up. Anything that changes code or other repository assets needs a PR and the
machinery of TEST-READY; dead-code and unnecessary-code checks therefore run in the implementation team, on the
diff, before the PR (§7.2).

**Scope:**

1. **Local and temporary clean-up:**
   - temp files the agents created;
   - local and remote branches no longer needed;
   - worktrees;
   - **temporary test and verification infrastructure**: test users, staged uploads, probe stacks.

   Every team records what it creates in a **temporary-resource ledger** on the issue (one machine line per
   resource: kind, id, environment, created-by). CLOSE-READY removes exactly those. Example: chess #1130 left 1,000
   staged uploads that later blocked other issues' deploy checks.
2. **New issues uncovered by the deployment, even a successful one,** under the filing discipline (observed
   defects only; zero is a valid result).
3. **Learnings and documentation:**
   - machine-local memory and steering proposals are written directly;
   - repository-side changes (docs, `docs/lessons-learned.md`, steering files in the repository) are appended as
     records to ONE rolling **learning-batch issue**, worked like any tier-S issue when it has collected enough
     items or once a day. Many issues' learnings thus land in one PR, not one follow-up PR each: such follow-up
     PRs were 40 % of chess's PRs, and each cost a trunk run.
   - This learning-batch issue is a proposal for review (decision M5).
4. **A structured close-out summary on the issue:** what was asked and built, the evidence, the landing and
   deploy, the checkers' outcome, temporary resources removed, issues filed, learnings recorded, and residuals. The
   human reads it in the tracker or in the digest (§17), because the operator rarely returns to sessions.

Exit predicate: §4.2.

---

## 12. Human input (decisions U1, U12, U14, U17)

### 12.1 The `needs-input` lifecycle

- **Blocking question:** set `needs-input`, release the claim, pull other work. No unattended worker ever blocks
  on an interactive question; asking interactively stays only in a session the human is actively driving.
- **Reversible decision:** proceed with the recommended option and record it as an assumption the human may
  override (decision U12). An override after the spec stage becomes REWORK-REQUIRED or SPEC-REQUIRED; after the
  landing, a new issue.
- **Format:** every question is a record in the five-line shape of `clients/claude/rules/continuous-work.md` (one
  line of context, two to four options with consequences, the recommended option first), with an id and
  blocking/non-blocking.

### 12.2 Decision inventory, up front

At START and at SPEC entry, the maker lists EVERY decision and human input the issue will need through to
CLOSE-READY:

- product choices;
- inputs (accounts, data, folders);
- permissions;
- sign-offs.

All of them go out in ONE batch. A question raised later must state why it was not foreseeable. A foreseeable late
question is a defect of the spec stage, recorded in the retro.

### 12.3 The question checker (maker ≠ checker for questions)

Before anything reaches the human, a separate agent tries to answer it from the spec, the issue, the codebase, the
docs, the decision records and the steering. Only these pass:

- irreversible;
- sensitive;
- a genuine product decision;
- a hard blocker.

These are the four Proven Exceptions of `continuous-work.md`.

### 12.4 Routing by kind

Environment health, credentials and dependency/contention never become an issue's question.

| Kind | Goes to |
|---|---|
| Environment health, credentials | the environment owner and the `delivery-status` issue, as ONE record per root cause, deduped across issues; the affected issues get `blocked-by` it |
| Dependency, contention | `blocked-by #N`, or the merge steward |

Example from the data: the same Security Hub finding (SSM.1) was asked about from four different issues.

### 12.5 Standing permissions are policy

Examples: "agents may dispatch the prod deploy after a green stage", "may change IAM in the shared dev account".
They are asked once per project and recorded as a decision record or steering line, never per issue again.

### 12.6 A human review task is one sheet

When the human must judge many items (e.g. 107 sentences), the items form ONE artefact the human completes in one
sitting, not a stream of questions.

### 12.7 `/get-guidance`

Run by the human when there is time; the same prompt on Kiro.

1. **Collect** across issues (later across projects), in order:
   1. blocking questions and approvals;
   2. "stuck" reports from the budgets;
   3. non-blocking assumptions the human may override.
2. **Dedupe** the same decision across issues.
3. **Ask** one item, or a small batch, at a time.
4. **Record** each answer verbatim on every affected issue (`factory: answer Q-<n> = <option> (by <user>)`), and
   clear `needs-input` when no blocking question is left.
5. **Transition** only when the answer clearly sends the issue to another stage; otherwise the next worker in the
   stage reads the answer.
6. **Generalise:** offer to turn a general answer into a decision record or steering line, so it is not asked
   again.
7. **End** with a fixed summary. The command can be stopped at any point, because all state is on the issues.

An answer written directly on the issue (an unmarked comment after an open question) works equally.

### 12.8 Optional approval setting (decision U17)

Off by default; no stage requires a human. A project that needs one (e.g. a bank, or AI-DLC's "implements after a
human validates") switches on approval for M/L specs or sensitive paths. The approval then arrives as one batched
`needs-input` of kind approval through `/get-guidance`, while independent work continues.

### 12.9 The data behind §12 (*R: questions-data.md, thresholds.md §M6*)

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
- a **hard** limit (about p99 or above the observed maximum) that sets `needs-input` with a "stuck because …"
  record naming the counter, its value, the last three causes and a recommended option. That record is the proof
  that the agents tried.

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

**Resets:**

- per stage visit: review, verifier and question counters. Re-entering SPEC gets half the cap, so REWORK ↔ SPEC
  ping-pong gets no fresh budget.
- per PR: CI rounds.
- never by a worker: queue returns, culprit failures, rework, claims and cost. Only a human answer raises the
  limit of the counter that tripped.

**What does not count as a bounce:** infra failures, flakes fixed by a re-run of the same SHA, landing into an
already-red environment, and conflicts an automatic rebase resolves.

**Expected escalation rate from budgets:** about 2–3 %, falling towards 1 % with culprit-only attribution
(measured for the tracker counters alone: 1.3 % pooled). Today's time tripwires do not fit elapsed time (89 % of
S issues take more than 3 h from claim to merge, mostly waiting), so any time budget counts active time only.

---

## 14. Scheduling: the dispatcher

Hand-offs between stages are safe only if something guarantees a worker for every non-empty queue. Decision A2 of
2026-11-02 ("the session owns its PR until it lands") was taken because hand-offs stranded: 0 of 10 closed, since
no one picked returned work up. The dispatcher is what lets this design reverse A2.

- **Polling, not webhooks:** a laptop cannot receive forge webhooks (*R: webhook-triggers-analysis-2026-11-06*,
  in `docs/reports/`). The dispatcher polls the tracker every few minutes, counts the issues per stage that are
  pullable (no claim, no `hold`, no `needs-input`, no open `blocked-by`), and starts workers per role up to a
  configured capacity per host.
- **Pull order, right to left**, then priority within a queue:
  1. REWORK-REQUIRED;
  2. CLOSE-READY;
  3. IMPLEMENTATION-READY;
  4. SPEC-REQUIRED;
  5. START.

  The human sets priority with labels. While trunk is red or nothing is ready for implementation, workers write
  specs rather than idle (decision U8).
- **Footprint-aware selection:** between equals, prefer an issue whose declared footprint does not overlap work in
  flight. The steward already does this inside a batch.
- **Leases:** the dispatcher hosts the lease reaper (§5.2).
- **Hosts:** Kiro Crew (cron, heartbeat crew, webhooks where reachable), headless CLI runs on CI runners, or a
  scheduled task on a workstation. The dispatcher itself makes no code changes and needs only tracker read access
  plus the ability to start a worker.

---

## 15. Tools and trust (*R: mcp-and-powers.md, plugin-marketplaces.md, checker-landscape.md*)

**Sources checked:**

- the awslabs MCP catalogue (consolidated in 2026: the IaC server replaces the CDK and CloudFormation servers;
  several servers deprecated);
- the official MCP registry;
- vendor MCP servers;
- Kiro powers;
- Claude Code plugin marketplaces;
- the products and deterministic tools of each checker category.

**Rule: imitate by default, install by exception.** Plugins, hooks and MCP servers run with the user's full
permissions. 2026 had real supply-chain incidents: compromised scanner GitHub Actions (Trivy, KICS), malicious
skills in community catalogues, a trojanised Claude Code extension on another IDE's marketplace.

**Trust rules:**

1. Checkers get read-only tools only; read-only is enforced in IAM first and by server flags second. A 2026 CVE
   showed the AWS API MCP server silently skipping its own policy check after a failed policy load.
2. Never give a checker a mutating tool; deny by tool name.
3. Pin every server, scanner, action, plugin and power, never `@latest`. Bump pins by reviewed PR.
4. Headless checkers run with `--strict-mcp-config` (Kiro: `includeMcpJson: false`), so a PR cannot add an MCP
   server to its own checker through `.mcp.json`.
5. No deploy credentials in a session that reads untrusted content: logs, issue text, web pages.
6. An "untrusted input" line in every checker prompt.

**Framework gaps found:**

- Both setup prompts install their MCP servers `@latest`.
- `prompts/setup-claude.txt` auto-allows every tool of `awslabs.aws-api-mcp-server`, protected only by
  `READ_OPERATIONS_ONLY`.
- Kiro powers rely on `AWS_PROFILE` in their `env` blocks, which the setup prompts forbid; this needs a decision
  before any power is adopted.

---

## 16. Client parity and distribution

- **What lives where.** The state machine (transition verb, claims, records, budgets) lives in the wrappers and
  CI, so Claude Code and Kiro enforce it the same way. Client hooks add the in-session guardrails each harness
  supports.
- **Kiro's missing pieces** are covered by the design's cross-machine machinery: no session watchdog (the lease
  reaper replaces it), no StopFailure event (the lease expires), no session cron (the dispatcher).
- **Distribution stays file-based** per project (decision U19).
- **A plugin is a future option.** It would be tied to the AWSBedrockGateway project, which hosts the
  `bedrock-gateway` plugin marketplace and the managed-MCP configuration of the desktop app, and it would need
  equivalents for Kiro (powers, a different format with no pinning) and other harnesses.

---

## 17. Measurement

The transition lines (§4.4), claim lines (§5), review records (§8), question records (§12) and revert records
(§10) give, without hand-made analyses:

- lead time and time per stage;
- queue age;
- bounce and rework rates;
- review rounds;
- question episodes per issue and the share of time waiting for answers;
- NFT, VBT and TBT per red event;
- cost per issue.

A digest (the `/delivery-status` option D2 of `docs/reports/session-endings-analysis-2026-11-01.md`) prints them
per project. It is also where close-out summaries (§11) and elapsed-time alarms (§13) reach the human.

---

## 18. What would change in the framework (for planning, not now)

| Area | New | Changed | Reused |
|---|---|---|---|
| Tracker state | stage labels, transition verb, reconciler, audit lines | `release-issue` stops writing the whole label set | additive label primitives |
| Claims | claim comments with leases; reaper | `start-issue` becomes the comment protocol; the `mkdir` lock stays a same-clone optimisation | — |
| Spec hand-off | `spec-approved` record, ask hash, acceptance tests at spec time | the orchestrator's FIX splits into SPEC and IMPLEMENTATION teams | the spec phases, the review panel, the tiers |
| Review exchange | `factory-review/v1` records, a validation script, the `factory/review` commit status, the arbiter | the review lanes emit records instead of prose files | the review contract's materiality rules |
| Checkers | IaC gate, OSV-Scanner, diff coverage, spec lint, logic-bug reviewer, threat-model lane, duplicate-confirmer, retro checker | housekeeping and doc-reviewer split into maker and checker | the existing lanes |
| Delivery | Track E restore in the deploy template; Track T revert and attribution in the steward; `reverted` records | H1–H6 fixes in `merge_steward.py`; the deploy template | trains, ancestry verification, `delivery-status` |
| Human input | `/get-guidance`, question checker, decision inventory, standing-permission records | `continuous-work.md` escalation text | the five-line question shape |
| Scheduling | dispatcher | decision A2 reversed | — |
| Setup | Minimum revert tier required for AWS projects; pinned MCP servers; strict MCP config for checkers | both setup prompts and the update prompt | — |

Small defects found on the way, to fix when the framework is changed:

- `clients/claude/agents/spec-review-agent.md` repeats one paragraph.
- `clients/claude/docs/dead-code-language-matrix.md` lists `ts-prune` as required although it is in maintenance
  mode and knip covers it.
- The two maker-checker agents named in §7.2.

---

## 19. Known weaknesses: where a reviewer should push

1. **The comment-order assumption.** The claim tie-break and the record fold rely on comment ids increasing in
   creation order on both forges. This is observed behaviour, not a documented guarantee; it needs checking for
   GitHub and GitLab.
2. **Lease clocks.** Leases compare a worker's ISO time with the reaper's. Clock skew between machines needs a
   margin or server timestamps.
3. **API rate limits.** Many workers and a dispatcher polling one tracker, plus record comments, could hit
   GitHub's and GitLab's limits; long issues accumulate many comments.
4. **Label atomicity.** Swapping a stage label takes two calls; a crash between them leaves zero or two stage
   labels until the reconciler runs.
5. **Hand-off cost.** Every hand-off between workers re-reads issue, spec and code. Affinity and the tier-S fast
   path reduce it, but the token cost of a fully decoupled flow is not measured.
6. **Attribution of smoke failures** is heuristic (§10.4, step 2.4). A wrong guess costs one deploy and one
   reland, never a broken trunk, but repeated wrong guesses lengthen VBT.
7. **The arbiter's authority.** A fresh agent decides between two checkers. How it is kept from simply siding with
   the more confident lane is open.
8. **The learning-batch issue** (§11) is my proposal, not a user decision.
9. **Not designed here:**
   - automated capture of corrections (gap-analysis 2.5 a, b);
   - backlog drift measurement (gap-analysis row 11);
   - the Jira wrapper (gap-analysis 3.8);
   - the details of the production intake (gap-analysis 2.6);
   - the contract-drift check per project (gap-analysis 3.7).

   [traceability.md](traceability.md) lists them.
