# Budgets and bounce limits for the issue state model, derived from the data (2026-11-09)

> Record from the factory state-model design discussion (2026-11-09 to 2026-11-11), copied from the working notes. Paths to working files were rewritten to this folder; the text is otherwise as written. Where it differs from `docs/design/factory-state-model/decisions.md`, that file wins.

Status: analysis only. Nothing was changed in any project, tracker or the framework. All tracker reads were GET
requests through each project's own wrapper module (its own token or corporate sign-in cookie and config). Scripts and raw
extracts are in the analysis working directory, not committed (scripts in `scripts/`, the computed tables in `metrics.txt` and
`metrics_tracker.txt`).

## 0. What the thresholds are for, and the arithmetic that constrains them

A budget that trips raises the issue to the human. The target is that this happens to well under 5 % of issues,
ideally about 1 %. Two facts from the data set the frame:

1. **Several counters run per issue, so their trip rates add up.** With four or five counters at their own p95,
   15 to 25 % of issues would trip one. A counter can raise to the human only at about p99 or above. Below that, a
   counter should trigger an **automatic** corrective step (change strategy, fresh worker, revert, re-plan).
   This report therefore gives two numbers per loop: a **soft limit** (automatic action, about p90–p95) and a
   **hard limit** (human, about p99 or above the observed maximum).
2. **Today the human is already asked for 38 % of the issues that sessions on this machine worked since
   2026-10-01.** That is 51 of 133 issues (§M6). Exhausted loops (review cap, verifier loop, merge contention)
   explain 9 of those 51, i.e. 7 % of all worked issues. Most escalations are product or design decisions (two
   thirds of escalated issues), sign-in or trust prompts, and environment faults (IAM, Security Hub, quotas).
   Budgets alone cannot bring the rate to 1–5 %. That also needs: non-blocking questions answered with the
   recommended default (decision D8), an owner for the environment's health (red-pipeline report, F3), and
   credentials that do not expire in the middle of a run.

"Measured" below means: computed from the data named in the row. "Estimated" means: derived from a measured
number with a stated assumption.

## 1. Data sources and coverage

| Source | What it gave | n | Coverage limits |
|---|---|---|---|
| Spec trees `.claude/specs/*` of the four projects. Remote trunk (`origin/main`, ccet `origin/master`) read via `git ls-tree` / `git cat-file`, plus local checkouts and worktrees | review iteration files (`review/<lane>/iteration-NN.md`, `tasks-iteration-NN.md`, `verify-NN.md`), the tier line, decision logs (cap decisions), evidence trees (waves, `ci-fix-N`, refutation reports) | 1,769 specs; 635 tiered specs whose first DL entry is on or after 2026-10-01 ("capped era") | **chess gitignores `review/`** (its `.gitignore` rule `/.claude/specs/*/review/`), so chess has no review files on trunk. For chess the counts come from the reviewer dispatches in the transcripts and from the decision logs. Tiers exist only since the 2026-09-30 revision (d2fe664). |
| Claude Code transcripts of this machine: chess, AWSBedrockGateway, Insights Analyzer, ccet (main sessions plus subagents, about 30 GB) | tokens (usage deduplicated by message id), the harness's own `cost-state.totalCostUSD`, claims and `CURRENT_ISSUE` writes (session → issue attribution), reviewer dispatches with iteration numbers, `AskUserQuestion` calls, `AWAITING_USER` writes, verdict lines | 365 sessions; 121 since 2026-10-01 with 133 attributed issues | **This machine only.** chess ran about 20 workers on several machines, so the transcripts cover about a quarter of chess's issues. No `NEEDS YOU` verdict appears in any transcript, so escalations were counted from `AskUserQuestion` (archive prompts excluded) and `AWAITING_USER`. |
| Run state on disk (`.claude/agent-state/issue-work-orchestrator/**/resume_state.md*`) | phase sequences per run × issue (backward transitions), `AWAITING_USER` values, with the phase at the time | 566 files; 303 run × issue rows since 2026-10-01 | phase names are free text that varies by framework version; block timestamps are sparse |
| chess tracker (GitHub, `scripts/github_wrapper.py`'s token loader and request builder): issues + PRs, repo-wide comments since 09-01, repo-wide issue events (labels), Actions runs since 08-03, PR head refs | label bounce counts (`needs-rework`, `queue-failed`, `queue-conflict`, `verification-failed`, `in-progress`), steward machine lines, PR CI red → fix rounds, claim → merge / close | 376 issues first claimed since 2026-10-01; 702 PRs since 10-01 that reached green CI | chess switched to `merge: steward` + `verification: watcher` on 2026-10-30 20:22; before that, merges were direct and sessions verified. 10-31 to 11-02 was the 50-hour red streak with blame-all verdicts (red-pipeline report), which inflates the steward-era return counts |
| ccet tracker (GitHub, `github_wrapper_script.py`) | same | 8 issues claimed since 10-01; 23 green PRs | ccet has been nearly idle since mid-October: too small for percentiles, used as a cross-check only |
| Insights Analyzer and AWSBedrockGateway trackers (GitLab through each project's `gitlab_wrapper.py` `_load_config` / `_api_get`; the corporate sign-in cookie was valid) | issues, MRs, notes and label events (items updated since 09-15 / 09-25), pipelines | IA: 617 issues, 1,098 MRs, 924 pipelines; 93 issues claimed since 10-01, 206 green MRs. Gateway: 484 issues, 336 MRs, 807 pipelines; 123 issues claimed since 10-01, 194 green MRs | both run `merge: direct` + `verification: session`, so they have no steward or watcher labels (no M4/M5 data) |

## 2. Measurements

Percentiles are nearest-rank. "p99" with n < 100 is the maximum or close to it; read it as such.

### M1. Design review and tasks review iterations per spec (DESIGN_REVIEW_LOOP, TASKS_REVIEW_LOOP)

Source: review iteration files (gateway, IA, ccet); reviewer dispatches in transcripts (all four, the only source for
chess); decision-log entries that record a cap decision (all four). Capped era only.

| Tier (cap today) | Source | n | p50 | p75 | p90 | p95 | p99 | max | reach the cap | exceed the cap |
|---|---|---|---|---|---|---|---|---|---|---|
| M design (4) | files | 123 | 3 | 4 | 4 | 4 | 5 | 8 | 39 % | 3.3 % |
| M design (4) | transcripts, chess only | 34 | 3 | 3 | 4 | 4 | 4 | 4 | — | 0 |
| L design (6) | files | 13 | 4 | 5 | 6 | 6 | 6 | 6 | 23 % | 0 |
| L design (6) | transcripts, chess only | 19 | 3 | 4 | 4 | 5 | 5 | 5 | — | 0 |
| M tasks (2) | files | 103 | 2 | 2 | 2 | 2 | 3 | 3 | 86 % | 4.9 % |
| L tasks (3) | files | 13 | 3 | 3 | 3 | 3 | 3 | 3 | 69 % | 0 |

A cap decision is recorded in the decision log ("approve as reviewed at the cap, residuals recorded") for 30 % of
M specs (85 of 281), 24 % of L specs (13 of 55) and 17 % of S specs (44 of 258). chess is in the same range as
the other projects (M 47/171 = 27 % against 36–37 % in gateway and IA; L 10/42; S 28/173).

Before the revision (no tiers, cap 8, n = 765) the design loop had p90 7, p95 8, p99 15 and a maximum of 27. The
caps did what they were meant to do: the tail is gone.

Caveats:
- Reaching the cap is common and mostly harmless. Tasks review uses its full cap in 86 % (M) and 69 % (L) of the
  specs. The usual pattern is NOT-CLEAN at iteration 1 and CLEAN at the last one.
- A cap decision is almost always taken by the orchestrator itself, with the recommended option "approve as
  reviewed, residuals recorded". It reached the human as a question in **3 of 133 issues (2.3 %)**: chess #1248
  (design cap and tasks cap), chess #1435 and gateway #844, each time with small open B findings only.
- Iteration numbers from transcripts come from the dispatch prompts. The tasks-loop numbers from that source mix
  design and tasks numbering, so they are not used.

### M2. Tier S spec review (COMBINED mode, cap 2)

| Source | n | p50 | p75 | p90 | p95 | p99 | max | reach 2 | exceed 2 |
|---|---|---|---|---|---|---|---|---|---|
| files (gateway, IA, ccet) | 100 | 2 | 2 | 2 | 3 | 3 | 3 | 85 % | 7 % |
| transcripts, iteration numbers in prompts (chess mostly) | 58 | 2 | 2 | 2 | 2 | 2 | 2 | — | 0 |
| transcripts, dispatch rounds (30-minute clusters) | 63 | 1 | 1 | 2 | 2 | 5 | 5 | — | — |

S almost always takes exactly two passes: NOT-CLEAN, the edit, CLEAN. Spot-checked, e.g. IA #607. The seven
specs that exceeded the cap ran three passes. The 17 % of S specs with a cap decision were approved by the
orchestrator with the last B applied verbatim.

### M3. PR CI red → fix rounds per PR before the first green run

Definition: the number of distinct head SHAs whose PR-CI runs were all red (failure / timed out) before the first
SHA with a green run. Cancelled and skipped runs are ignored. A re-run of the same SHA is the same SHA.

| Project (source) | n PRs | any red | p50 | p75 | p90 | p95 | p99 | max | > 1 | > 2 | > 3 | > 4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chess (Actions `CI`, `pull_request`, PRs since 10-01) | 702 | 28.3 % | 0 | 1 | 1 | 2 | 3 | 5 | 8.1 % | 2.6 % | 1.0 % | 0.4 % |
| chess tier S / M / L | 181 / 347 / 122 | | 0 / 0 / 0 | 0 / 1 / 1 | 1 / 1 / 2 | 1 / 2 / 2 | 2 / 4 / 4 | 3 / 5 / 4 | | | | |
| ccet (`PR Validation`) | 23 | 60.9 % | 1 | 2 | 3 | 4 | 4 | 4 | 43.5 % | 21.7 % | 8.7 % | 0 |
| Insights Analyzer (GitLab pipelines on the MR source branch, MRs since 10-01) | 206 | 28.6 % | 0 | 1 | 1 | 1 | 1 | 2 | 0.5 % | 0 | 0 | 0 |
| AWSBedrockGateway (same) | 194 | 23.2 % | 0 | 0 | 1 | 1 | 2 | 2 | 1.0 % | 0 | 0 | 0 |
| **pooled, per PR** | 1,125 | 28.1 % | 0 | 1 | 1 | 2 | 3 | 5 | 6.2 % | 2.1 % | 0.8 % | 0.25 % |

The two GitLab projects merge directly, and their sessions run the full local gate before every push. That is why
they never needed more than 2 rounds. chess's longer tail (up to 5) is its larger and slower CI (Windows,
Android, E2E legs).

Per issue (all PRs of the issue; chess): max over its PRs p95 3, p99 4, max 5; summed over its PRs p95 3, p99 5,
max 10. Follow-up PRs make the sum per issue a poor counter. A counter that resets per PR works better.

Cross-check from the spec evidence trees: a `ci-fix-N` capture exists in 1.6 % (S), 8.8 % (M) and 22 % (L) of the
specs with a report. Run state: a backward transition from a delivery phase (PR/CI/merge) to a fix phase in a
run × issue had p90 1, p95 2, p99 5, max 9 (n = 303). That count also includes merge-conflict rounds.

### M4. Merge-queue returns and rework rounds per issue

Source: chess label events. `needs-rework` is set on the issue for every return (queue-failed / queue-conflict on
the PR, `verification-failed` on the issue). "Returns" is therefore the larger of the two counts, never their sum.

| Population | n | issues with ≥ 1 | p90 | p95 | p99 | max | > 1 | > 2 | > 3 |
|---|---|---|---|---|---|---|---|---|---|
| chess, all issues first claimed since 10-01 (direct merges until 10-30): rework rounds (`needs-rework`) | 376 | 19.9 % | 1 | 2 | 4 | 6 | 5.3 % | 2.1 % | 1.1 % |
| chess steward era (claimed ≥ 10-30 20:22): **queue returns only** (`queue-failed` + `queue-conflict`) | 90 | 25.6 % | 1 | 2 | 4 | 4 | 6.7 % | 3.3 % | 1.1 % |
| chess steward era: all returns (queue + blame-all verification) | 90 | 77.8 % | 2 | 3 | 6 | 6 | 23.3 % | 6.7 % | 2.2 % |
| the same, without issues that landed inside the 10-31 – 11-02 red streak | 58 | 65.5 % | 3 | 3 | 6 | 6 | 25.9 % | 10.3 % | 3.4 % |

Claims per issue (each `in-progress` label = one pickup; a re-claim follows a release, a return or a crash):
chess since 10-01: p90 2, p95 3, p99 5, max 8; share > 1: 12.8 %, > 2: 5.6 %, > 3: 1.9 %, > 4: 1.3 %.
chess steward era: > 1: 37.8 %, > 2: 21.1 %, > 3: 5.6 %, > 4: 3.3 %, mostly driven by the blame-all returns.
Gateway: > 1 5.7 %, > 2 1.6 %, max 3. IA: > 1 4.3 %, max 2. **Pooled (n = 600): > 1 10.0 %, > 2 3.8 %,
> 3 1.2 %, > 4 0.8 %, max 8.**

Caveats: the steward-era rows are inflated by chess's contract -5 watcher, which returned every issue a red deploy
contained (36 issues during the red streak; red-pipeline report). Under the culprit-only attribution decided on
2026-11-09, the **queue-only row is the best predictor**. GitLab projects have no queue labels (direct merges).

### M5. Post-deploy verification failures per issue

chess, all issues first claimed since 10-01 (n = 376): 66 issues (17.6 %) had a `verification-failed`; one issue
had two (0.3 %). In **27 of the 66 (41 %)** an agent comment after the verdict says, in writing, that the red was
not caused by this issue ("not ours", "unrelated", "pre-existing", "already red"). The true share of bystanders is
higher: the red-pipeline report traced the whole 10-31 – 11-02 streak to two changes, #566 and #1494. Gateway
and IA have no watcher, so there is no data there.

### M6. Escalations to the user

| Source | Population | Escalated | Notes |
|---|---|---|---|
| transcripts: `AskUserQuestion` (without "Archive this session?") + `AWAITING_USER` writes, attributed to the current issue | 133 issues worked since 10-01 | **51 (38 %)**; S 24 % (11/46), M 44 % (28/64), L 52 % (11/21); without credential-only cases 34 % | episodes (1-hour clusters) per escalated issue: p50 2, p75 2, p90 4, p95 8, max 20 |
| run state `AWAITING_USER` values | 303 run × issue rows since 10-01 | 57 (18.8 %) | distinct values per escalated row: p50 2, p90 5, max 16 (the same question restated) |

Causes (issues; one issue can have several): product or design decision 34; uncategorised 16 (read: also mostly
decisions and permissions, e.g. "Enable Macie?", "May this session edit .kiro/?"); credentials, sign-in or
workspace trust 13; manual human action (dispatch a prod deploy, edit model-drafted text, click a confirmation)
10; environment, infrastructure or permission (Security Hub findings, IAM, Actions minutes, CloudFormation limits)
10; contention (two sessions on one issue, PR overtaken six times, a merge freeze) 6; review cap 3; verifier
loop 1; user interrupt 1.

In which stage the human was asked (run state, episodes): IMPL 67, SPEC 29, DELIVER 28, POST 15. SPEC ↔
needs-input cycles: 18 of 303 run × issue rows asked in SPEC at least once, 6 twice or more, 3 three times or
more (max 4).

Caveats: many sessions were interactive (the human was present), which invites questions a worker would otherwise
settle with the recommended default. The rate is an upper bound for an unattended factory. It is still the right
order of magnitude for "how often does a worker need something only a human can give".

### M7. Wall-clock and cost per issue

Wall-clock, trackers (first `in-progress` label → first merged PR/MR of the issue; → issue closed), issues first
claimed since 10-01. Pooled n = 600: chess 376, gateway 123, IA 93, ccet 8.

| Tier | Project | n (merge) | claim → merge p50 / p75 / p90 / p95 / p99 / max (h) | claim → close p50 / p90 / p95 / p99 / max (h) |
|---|---|---|---|---|
| S | **pooled** | 210 | 6.5 / 12.8 / 23.9 / 31.9 / 81.1 / 345 | 13.2 / 50.1 / 70.0 / 346 / 558 |
| S | chess / gateway / IA | 133 / 40 / 35 | p50 6.6 / 6.7 / 6.1; p95 43.3 / 22.2 / 27.3 | p95 70.0 / 27.2 / 546 |
| M | **pooled** | 285 | 20.2 / 29.2 / 48.2 / 64.1 / 148.2 / 260 | 28.6 / 74.0 / 116.8 / 321.9 / 358 |
| M | chess / gateway / IA | 165 / 64 / 51 | p50 20.9 / 21.2 / 17.4; p95 79.3 / 44.0 / 49.6 | p95 136.3 / 85.0 / 75.1 |
| L | **pooled** | 57 | 37.4 / 56.4 / 74.6 / 124.0 / 150.4 / 150 | 57.7 / 145.1 / 203.7 / 232.2 / 232 |
| L | chess / gateway / IA | 43 / 10 / 4 | p50 37.4 / 26.9 / 61.9; p95 124.0 / 77.6 / 72.8 | p95 188.9 / 104.9 / 232 |

Share of issues whose claim → merge is above today's time tripwire (S 3 h, M 24 h, L 72 h, `work-issue.md`):
S 89 %, M 38 %, L 14 % (pooled). Share above S 48 h / M 96 h / L 168 h: 3.8 % / 2.1 % / 0 %.

Elapsed time is mostly waiting: CI, the queue, deploys, human answers, nights. The wait-time analysis measured
66.5 % waiting. Today's time tripwires (S 3 h, M 24 h, L 72 h, `work-issue.md`) would raise 89 % of S issues if
they measured elapsed time. A wall-clock budget has to count **active** time (the claim is held and a worker is
running) or serve only as a reporting alarm.

Cost and tokens per issue, transcripts. Each assistant message is attributed to the issue current at that moment,
subagents included. Cost = weighted tokens × the median of the harness's own $ per weighted token
($2.95 per million; input 1, cache write 1.25, cache read 0.1, output 5; n = 114 sessions with a `cost-state`
record):

| Tier | n | cost p50 / p75 / p90 / p95 / p99 / max (USD) | tokens p50 / p90 / p95 / max (million, ~97 % cache reads) | adversarial-verifier passes p50 / p90 / p95 / max |
|---|---|---|---|---|
| S | 46 | 149 / 239 / 292 / 318 / 416 / 416 | 238 / 564 / 672 / 911 | 1 / 3 / 3 / 4 (n = 35) |
| M | 64 | 498 / 696 / 964 / 1,306 / 3,042 / 3,042 | 977 / 2,038 / 2,145 / 5,230 | 1 / 3 / 4 / 5 (n = 54) |
| L | 21 | 1,437 / 1,646 / 2,439 / 2,795 / 3,221 / 3,221 | 2,825 / 4,311 / 5,368 / 7,043 | 2 / 4 / 6 / 6 (n = 13) |

Share of issues above a cost line: S > $300 6.5 %, > $400 2.2 %, > $500 0. M > $1,000 9.4 %, > $1,500 4.7 %,
> $2,000 1.6 %, > $3,000 1.6 % (one issue). L > $2,000 14 %, > $2,500 9.5 %, > $3,000 4.8 %, > $4,000 0.

Caveats: the $ figure is an estimate. The harness's cost record is cumulative and is not always written at the end
of a session, so each session is priced at the median ratio; the ratio's spread across sessions is
p50 $2.9, p75 $3.2, p90 $3.6 per million weighted tokens. Sessions per issue were 1 at p95 (max 2), so a rework
session on another machine is not included.

### M8. Implementation waves and verifier passes

| Tier | waves per spec (max wave number in the evidence tree) p50 / p90 / p95 / max | VERIFY panel passes (review files) | adversarial-verifier dispatches per issue (single-issue sessions) | specs whose report or review records a REFUTED verdict | verifier rounds stated in the report: share > 3 / > 4 / > 5, max |
|---|---|---|---|---|---|
| S | 1 / 2 / 3 / 7 (n = 246) | p50 1, max 2 (n = 23) | p50 1, p90 3, max 4 (n = 35) | 53 % | 5.9 % / 4.7 % / 2.0 %, max 6 (n = 253) |
| M | 4 / 6 / 7 / 9 (n = 268) | p50 1, max 2 (n = 62) | p50 1, p90 3, p95 4, max 5 (n = 54) | 79 % | 3.6 % / 1.8 % / ≈ 0.7 %, max 9 (n = 274) |
| L | 6 / 9 / 9 / 10 (n = 54) | p50 1, max 6 (n = 8) | p50 2, p90 4, max 6 (n = 13) | 76 % | 3.7 % / 1.9 % / 0, max 5 (n = 54) |

Waves are planned in `tasks.md`; they are not a loop and need no budget of their own. The verifier loop
(refute → fix → re-verify) is a loop, and it raised the human once (chess #1477, "refuted four times"). The
round counts in the last column come from the report text ("Six rounds", "Iteration 2: REFUTED"). A report that
states no count is taken as one round. Two values (48 and 60) were test counts, not rounds, and are excluded.
That the long verifier loops occur in tier S (six rounds in chess #1012, #1133, #1470, IA #537) suggests that
these issues were under-tiered.

### Not measurable, and why

- **Review findings per iteration (A/B count at the cap):** the lanes record them in prose. Only the decision-log
  cap decisions were countable.
- **Active time per stage:** the run state has too few timestamps and the transcripts cannot tell waiting from
  working without the full wait-time classifier. Only elapsed time and the transcript span were measured.
- **Culprit-only verification failures:** chess's watcher blamed every covered issue, so the post-decision rate is
  unknown. Estimate: about the queue-return rate or lower.
- **Escalations on other machines and in Kiro:** transcripts cover this machine and Claude Code only.
- **Token cost on GitLab projects' other machines:** same reason.

## 3. Proposed thresholds

| State / loop | Counter (scope; when it resets) | Soft limit: automatic action | Hard limit: raise to the human | Percentile of the hard limit (data) | Expected escalation rate |
|---|---|---|---|---|---|
| SPEC, tier S review (COMBINED) | review passes (per SPEC visit) | 2 (today's cap): approve with the last B applied by its proposed edit, residuals recorded | 3rd pass ends with an open **A** | > p99 (files: max 3) | < 0.5 % (estimate: 7 % run a 3rd pass, few with an A) |
| SPEC, M design review | panel iterations (per SPEC visit; a re-entry after REWORK gets a delta loop with half the cap) | 4: approve as reviewed, residuals recorded | an **A** still open at 4, or A+B not decreasing over 2 iterations with A > 0 | 4 = p90–p95; 5 = p99 | ≈ 1 % (measured: 2.3 % of issues asked today, all with only B findings open; 0 under this rule) |
| SPEC, L design review | panel iterations (per SPEC visit) | 6 | as for M | 6 = max | ≈ 1 % |
| SPEC, tasks review | iterations (per SPEC visit) | M 2, L 3: approve with residuals | never on its own: an open A becomes a design re-entry | 2 = p95 (M); 3 = max (L) | 0 % direct |
| SPEC ↔ needs-input | question episodes in SPEC (per SPEC visit; an answer that changes the ask resets it) | 2: batch the open questions into ONE record with recommended defaults; reversible ones go on with the default | 3rd blocking episode → "needs a human-led spec" (the human is already involved; this changes the mode, not the inbox) | 2 = p98 of run × issue rows (6 of 303 asked twice or more, 3 three times or more) | ≈ 1 % (measured: 3 of 303 rows) |
| IMPLEMENTATION, verifier | refute → fix → re-verify rounds (per IMPLEMENTATION visit) | 3 (all tiers): a fresh verifier and a fresh implementer, the refuted test re-derived from the AC; for S, re-tier to M | the 6th round ends REFUTED | soft ≈ p94–p96; hard > max for S and L, > p99 for M | ≈ 0.5 % (measured: S 0 %, M 0.4 %, L 0 % needed more than 6; one escalation in 133 issues today) |
| TEST-READY, PR CI | red → fix rounds (per PR; reset on green) | 2: classify the failure (infra or flake vs change); retry infra once without counting | the 5th change-attributed red round | 4 = p99.75 (pooled 1,125 PRs: 0.8 % > 3, 0.25 % > 4; chess max 5) | ≈ 0.3 % |
| TEST-READY → REWORK, merge queue | queue returns: `queue-failed` + `queue-conflict` (issue lifetime; conflicts that an automatic rebase resolves do not count) | 2: the next return is reworked against a fresh trunk with the train log attached | 4th return | 3 = p99 (steward era, queue only: 1.1 % > 3; max 4) | ≈ 1 % |
| LANDED → REWORK, post-deploy | culprit-attributed verification failures (issue lifetime; bystander verdicts in a red streak never count) | 1: revert first (D5), then rework | 2nd culprit verdict | > p99 (0.3 % had 2, even under blame-all) | < 0.5 % |
| all stages | total rework rounds (`needs-rework`, any cause except bystander verdicts, issue lifetime) | 2: the next rework starts from a fresh worktree and a re-read of all return causes | 4th rework | 3 = p99 (chess since 10-01: 1.1 % > 3; pooled: 0.7 % > 3) | ≈ 1 % |
| all stages | claims (pickups) without a stage advance (issue lifetime) | 3: next pickup only by a worker that has not held it | 5th claim | 4 = p99.2 (pooled n = 600: 1.2 % > 3, 0.8 % > 4) | ≈ 1 % (chess today 1.3 %, inflated by blame-all returns) |
| all stages | cost (issue lifetime, weighted tokens priced at the harness ratio) | S $300, M $1,000, L $2,500: checkpoint, re-plan, consider a re-tier | S $500, M $2,500, L $4,000 | soft ≈ p90; hard > max (S, L) and > p98 (M) | ≈ 1–2 % (measured: S 0 %, M 1.6 %, L 0 % above the hard line) |
| all stages | elapsed since claim, not yet merged | report in the digest at S 48 h, M 96 h, L 168 h (pooled: 3.8 % / 2.1 % / 0 % of issues above, ≈ p96–p100) | none on elapsed time alone. Lease expiry (no checkpoint for N minutes) reclaims the issue instead | — | 0 % (alarm only) |
| all stages | active worker time (only once measured) | S 3 h, M 24 h, L 72 h (today's tripwires) | 2 × soft | not measured | estimate |

Union of the tracker-side hard limits (claims > 4, returns > 3, verification failures > 1, CI rounds per PR
> 4), measured: **chess 8 of 376 issues = 2.1 %** (under blame-all and the red streak), **pooled 8 of 600 =
1.3 %** (gateway and IA: 0). With every limit one higher: chess 0.8 %, pooled 0.5 %. With every limit one lower:
chess 4.5 %, pooled 3.0 %. The spec loops, the verifier and cost add about 1–2 % under the rules above
(estimated from their own rows; they overlap with the tracker counters, so the sum is an upper bound). Expected
total from the loop budgets: **about 2–3 %, falling towards 1 % under culprit-only attribution and
revert-first.** The decision and environment escalations of M6 come on top, unless D8 and F3 remove them.

## 4. What counts as a bounce, and which counters reset

A **bounce** is a backward move of the issue that a deterministic event caused and that costs a new worker cycle:

| Bounce | Counts | Does not count |
|---|---|---|
| TEST-READY → REWORK (queue) | the PR is the culprit of the first red train prefix (after the steward's one retry); a conflict that needs a code change | no CI result (no runner, cancel, timeout): infra; a conflict that an automatic rebase resolves; a dequeue by a human |
| TEST-READY → REWORK (PR CI) | a red PR-CI run on a new head SHA, attributed to the change | a red run that a re-run of the same SHA turns green (flake: count separately per test, quarantine at 2) |
| LANDED → REWORK | the issue is the attributed culprit of a red deploy (fails with, passes without) | landed into an environment that was already red; a red streak's bystanders; infra (credentials, IAM, quota) |
| IMPLEMENTATION / REWORK → SPEC | the spec or the acceptance tests had to change (the design no longer holds) | a C/D wording fix |
| any stage → needs-input → same stage | a blocking question episode (one record, possibly several questions) | a non-blocking assumption posted for override; a credential or trust prompt (it belongs to the environment owner and gets its own counter) |
| claim → release without a stage advance | a released or expired lease | a planned hand-off at a stage boundary |

Reset rules:

1. **Per stage visit (reset when the issue moves forward past the stage):** review iterations, verifier passes,
   SPEC question episodes. Re-entering SPEC from REWORK starts a delta loop with half the cap (M 2, L 3, S 1). That
   stops a REWORK ↔ SPEC ping-pong from getting fresh full budgets.
2. **Per PR:** CI red → fix rounds reset on a green run (a follow-up PR starts at 0; the issue's lifetime rework
   counter still sees it if it was a return).
3. **Issue lifetime (never reset by a worker):** queue returns, culprit verification failures, total rework
   rounds, claims, cost. Only a human answer resets the counter that tripped, and it records the new limit with
   the answer (`factory: budget <counter> += n by <human>`). A human answer must not reset the other counters.
4. **What a hard limit does:** set `needs-input` with a "stuck because …" record that names the counter, its
   value, the last three causes and a recommended option, and release the claim. It does not move the stage, which
   is the same rule as D1.

## 5. Recommendation in short

Keep the spec review caps (S 2, M 4, L 6; tasks M 2, L 3). They sit at about p90–p95 and already cut the old
tail (p99 15 → 5). Make them exit automatically with residuals, and raise the human only for an open A.
Put the hard limits of PR CI, the merge queue, rework, verification and claims at about p99 or above of the
tracker data (table §3). Price cost budgets per tier with soft lines near p90 and hard lines at or above the
observed maximum. Never escalate on elapsed time. Then the loop budgets account for about 1–3 % of issues
(tracker counters measured at 1.3 % pooled and 2.1 % for chess). The remaining distance to 1–5 % overall is the
decision and environment questions (M6, 38 % of issues today), which budgets cannot fix.

## Reproduction

`scripts/specs.py` (spec trees) → `specs.json`; `scripts/transcripts.py <dir prefix> <label>` →
`transcripts_<label>.json`; `scripts/runstate.py` → `runstate.json`; `scripts/gh_pull.py` / `gh_pulls.py` (GitHub,
run from the project directory with its venv) and `scripts/gl_pull.py` (GitLab) → `tracker_<label>*.json`;
`scripts/analyze.py` → `metrics.txt` / `metrics.json`; `scripts/analyze_tracker.py` → `metrics_tracker.txt` /
`metrics_tracker.json`; `scripts/pooled.py` → `metrics_pooled.txt`. Helpers: `scripts/pct.py` (nearest-rank
percentiles), `scripts/gitshow.py` (read one blob of a ref). `scripts/fix_bs.py` was a one-off repair of the
run-state script's own regex text and touches nothing else.
