# Traceability: the design against the keynote and the gap analysis (2026-11-11)

Target documents:

- the keynote "AI-DLC in Practice: Thinking in agentic loops with Kiro" (an engineering keynote held at a
  customer, 2026-11-03): its slide text and speaker notes;
- the gap analysis "SoftwareFactoryFramework vs. the software factory of the keynote" (2026-11-09).

Neither is in this repository, which is public; the operator provides both to the reviewer
([README.md](README.md)). Slide numbers below refer to the keynote deck, section numbers of the gap analysis to that
document. Section numbers (§) without a document refer to [design.md](design.md); decision ids (U, M, B, O) to
[decisions.md](decisions.md).

Status values:

- **designed**: the design covers it with a mechanism;
- **partial**: some of it is covered, and the rest is named;
- **deviation**: the design deliberately differs, with the reason;
- **not designed**: open, and listed in design §19.

## A. The keynote

| # | Keynote element (slide) | Design element | Status |
|---|---|---|---|
| A1 | The SDLC loop with the return path: "Issues found? Update the spec." (2) | REWORK-REQUIRED → SPEC-REQUIRED with a code-or-requirement classification; a requirement cause amends the criteria before code is touched (§4.2); the spec lives on the issue branch (§9) | designed |
| A2 | The unit of work moves from agent to loop to crew (3, 4) | teams per stage (§7), the dispatcher (§14) | designed; the dispatcher's host is open |
| A3 | Gather → act → verify → repeat; "verify is where most loops break" (5) | the team loop with deterministic checks first and checker verdicts per SHA (§7.1, §4.1) | designed |
| A4 | Loops inside loops: task, autonomous (/goal), crew (6) | task loop = waves inside IMPLEMENTATION; the independent "done" decision = the transition predicate over checker verdicts (§4); crew = dispatcher (§14) | partial: `/goal` itself is not used (row C3) |
| A5 | Every loop needs a provable finish line: task, issue, backlog (7) | the exit predicate of every transition (§4.2). The backlog's finish line: no open issue in any stage (all closed). The dispatcher works the queues right to left until then (§14) | designed |
| A6 | Feedback: bugs found in logs or CI become issues (7) | inflows into START: agent-filed, production signals, close-out findings (§6, §11); smoke attribution reads CloudWatch and CloudTrail (§7.2) | partial: no scheduled scan of application logs |
| A7 | Learnings are captured automatically; a correction made twice becomes steering (7, 19) | CLOSE-READY learnings and the learning-batch issue (§11); `/get-guidance` turns general answers into decision records (§12.7) | partial: no automatic detection of corrections, no recurrence counting |
| A8 | Workers coordinate on the backlog and in issue comments (7) | claims as leases in comments (§5); structured `factory-review/v1` records in comments (§8); no free-text negotiation | designed: structured, which is stricter than the keynote |
| A9 | The biggest loop: the empty backlog (8) | the dispatcher guarantees a worker for every non-empty queue (§14); budgets end every loop (§13) | designed |
| A10 | Security Agent on the verify step; DevOps Agent in production, every incident a new issue (9) | optional external checkers, budget-capped (§7.2, §7.3); `Origin: production` inflow (§6) | partial: the details of the production intake are not designed |
| A11 | Guardrails: no early stop, no guessing, someone else decides, effort matched to the task (10) | predicates and leases (§4, §5), evidence in every record (§8), maker ≠ checker (§7), tiers (P8). The client stop gates stay | designed |
| A12 | Drift: the reference is the spec, a separate check compares (11) | acceptance tests written at spec time and frozen for the implementer; ask hash (§9, §4.3) | designed |
| A13 | Cost: every unattended loop gets a budget (11) | soft and hard budgets per loop, including cost per issue (§13); measurement (§17) | designed |
| A14 | Control: central rules every loop and Crew agent follows (11) | trust rules for tools (§15); enforcement in the wrappers and CI (P9) | partial: per-agent deny rules and Kiro's central MCP and model allowlists are not designed |
| A15 | "Can the agent run the thing?" (12) | optional local runtime check per project (§9); Playwright MCP as a pilot; the post-deploy smoke is the gate (§10) | partial, by decision U9 (no throwaway environments) |
| A16 | Maker ≠ checker (12, 23, 24) | dedicated checkers per stage, verify-to-disprove, the arbiter (§7, §8) | designed |
| A17 | Kiro Crew: many loops, scheduled, unattended (14–16) | one possible dispatcher host (§14) | partial |
| A18 | The demo: agents report what they did NOT verify (16, 27) | verdict counts and "named, not run" reporting from runner result files (§7.4) | designed |
| A19 | Caveats: verification is still your job, comprehension debt, a bank is not a startup (18) | auditable transition lines and records (§4.4, §8); the structured close-out summary (§11); admission and read-only checkers (§6, §15); the optional approval setting (§12.8) | designed |
| A20 | Do's and don'ts: verifier before generator; give it a stop condition; smallest context (23) | acceptance tests before implementation (§9); budgets (§13); diff-scoped checkers (§7.4) | designed |
| A21 | AI-DLC: AI plans, asks, implements after a human validates (28); Inception / Construction / Operations (29) | START + SPEC / IMPLEMENTATION / TEST-READY + production inflow; human validation only as the optional approval setting | deviation (row C1) |

## B. The gap analysis

### B.1 Its summary table (§1 of the gap analysis)

| # | Gap-analysis row | How the design addresses it | Status |
|---|---|---|---|
| 1 | Task loop: the running system is first exercised after the merge | optional local runtime check for M/L runtime changes (§9) | partial (U9) |
| 2 | Issue loop: no single immutable record per issue | transition audit lines, review records, the close-out summary (§4.4, §8, §11) | designed |
| 3 | Backlog loop: manual start; no product priority input; fleet size is an operator action | dispatcher, priority labels, right-to-left pull order, capacity per role (§14) | designed (host open) |
| 4 | Parallel workers scale only on one host | cross-machine claims with leases (§5) | designed |
| 5 | Guardrails: Kiro has no watchdog, StopFailure recorder or `/supervise` | lease reaper and dispatcher replace them for both clients (§5.2, §16) | designed |
| 6 | Feedback loop: nothing reads runtime logs on purpose | smoke attribution from CloudWatch and CloudTrail; close-out files deployment findings (§7.2, §11) | partial |
| 7 | Learning loop: capture by prose; compiling is manual | close-out learnings, the learning-batch issue, decision records from `/get-guidance` (§11, §12.7) | partial: no correction hook |
| 8 | Production loop missing | `Origin: production` inflow (§6) | partial: intake details not designed |
| 9 | Security beyond the diff | OSV-Scanner, IaC gate, threat-model lane, optional AWS Security Agent (§7.2) | designed (pen testing optional) |
| 10 | SDLC return path into the spec | rework classifies code vs requirement; a requirement cause amends the criteria first (§4.2) | designed; a living system spec is not |
| 11 | Drift of the backlog from the product | — | not designed |
| 12 | Cost: no budget, no per-issue cost | budgets per loop and per issue; measurement (§13, §17) | designed |
| 13 | Control: write scope optional on Claude; no Kiro governance tie-in | trust rules for tools (§15) | partial |
| 14 | Crew loop: worker sessions are not started by anything | dispatcher (§14) | designed (host open) |
| 15 | Human validation (AI-DLC) | optional approval setting, off by default (§12.8) | deviation by decision U6, U17 (row C1) |
| 16 | Measuring the factory | measurement from the records and a digest (§17) | designed |

### B.2 Its cross-cutting sections

| Gap-analysis section | Design | Status |
|---|---|---|
| 3.1 Cost: (a) tokens per run and issue, (b) tier budgets that ask once, (c) Kiro OTEL export | (a) §17; (b) soft limits act automatically, hard limits ask once (§13); (c) not designed | partial |
| 3.2 Control: deny rules per agent by default; a governance profile for Kiro | trust rules for tools only (§15) | partial |
| 3.3 Who starts the loops | dispatcher (§14) | designed |
| 3.4 Kiro parity | client-neutral enforcement (P9, §16) | partial: the phase-2 renderer stays as planned |
| 3.5 Human validation | optional approval setting (§12.8) | designed by decision U17 |
| 3.6 Measuring the factory | §17 | designed |
| 3.7 The update loop to consumer projects | — | not designed |
| 3.8 A Jira wrapper | — | not designed (out of scope of the state model) |

### B.3 Its recommended order (§5 of the gap analysis), mapped

| Rank | Change | In the design |
|---|---|---|
| 1 | Cost per run and issue; tier budgets | §13, §17 |
| 2 | Production intake path | §6 (inflow only) |
| 3 | Event- and schedule-started runs | §14 |
| 4 | Automated learning capture | §11 (partial) |
| 5 | Dependency scan; then the AWS Security Agent | §7.2 |
| 6 | Returned work classified as code or requirement | §4.2 |
| 7 | Configurable human approval point | §12.8 |
| 8 | Pre-merge runtime check for M/L | §9 (optional, local) |
| 9 | Contract drift check per project | not designed |
| 10 | `/delivery-status` digest | §17 |
| 11 | Jira wrapper | not designed |
| 12 | Phase 2 of the restructure | unchanged plan |

## C. Deliberate deviations and conflicts

| # | Source says | The design says | Why |
|---|---|---|---|
| C1 | AI-DLC: implement only after a human validates (keynote slide 28; gap analysis 3.5) | no human-only gates; an optional approval setting, off by default | decisions U6 and U17: humans are the last-resort conflict resolver; a bank switches approval on |
| C2 | "File an issue for everything you find" (keynote call to action) | fix it, or file it with evidence (filing discipline) | measured: 60 % of all issues were spawned by working other issues; the gap analysis (2.4) recommends rewording the slide |
| C3 | `/goal` as the independent judge (keynote slides 6 and 13) | the transition predicate over checker verdicts is the independent judge; `/goal` is not used | a command cannot set `/goal`; the predicate works the same on both clients |
| C4 | "Start the service, call the endpoint" before the PR (keynote slide 12; gap analysis 2.1) | optional local runtime check; the gate is the post-deploy smoke on the shared environment | decision U9: shared environments only, no throwaway environments |
| C5 | INPUT-REQUIRED as a state (the original state proposal) | `needs-input` as a flag on the current stage | decision U1: no return-address problem; questions arise in every stage |
| C6 | Return the whole CI batch to REWORK-REQUIRED (the original state proposal) | only the culprit returns, through cumulative trains | decision U2: blame-all bounced 37 landings in chess (2026-11-02) |
| C7 | A LANDED state between merge and close (the first design round) | TEST-READY spans up to the green smoke | decision U7 |
