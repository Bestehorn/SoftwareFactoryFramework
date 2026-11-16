# Traceability: the design against the keynote's vision and the gap analysis (revision 2, 2026-11-16)

Two reference documents:

- the keynote "AI-DLC in Practice: Thinking in agentic loops with Kiro" (an engineering keynote held at a customer,
  2026-11-03): its slide text and speaker notes;
- the gap analysis "SoftwareFactoryFramework vs. the software factory of the keynote" (2026-11-09).

Neither is in this repository; the operator provides both to a reviewer ([README.md](README.md)). Section numbers (§)
without a document refer to [design.md](design.md). Decision ids (U, M, R, B, O) refer to [decisions.md](decisions.md),
finding ids ([A1], [T-05]) to the reviews in
[`docs/reports/factory-state-model-2026-11/reviews/`](../../reports/factory-state-model-2026-11/reviews/).

**How to read this file** (decision U22):

- **The keynote outlines a vision. It is in no way a specification.** Section A records how the design aligns with
  that vision, not whether it "meets" it.
  - **aligned:** the design has a mechanism for the idea;
  - **partly aligned:** some of it, and the rest is named;
  - **differs:** a deliberate design choice, with its reason in section C;
  - **not covered.**
- **The gap analysis lists gaps of the framework.** Section B records how the design addresses each one.
  - **designed:** a mechanism covers it;
  - **partial:** some of it, and the rest is named;
  - **deviation:** a deliberate choice, with its reason in section C;
  - **not designed:** open, and listed in design §19.
- Revision 2 corrected every status the target review disputed, for accuracy. Several moved to "designed" or "aligned"
  because revision 2 added the missing mechanism.

## A. Alignment with the keynote's vision

| # | Idea in the keynote (slide) | Design element | Alignment |
|---|---|---|---|
| A1 | The SDLC loop with the return path: "Issues found? Update the spec." (2) | every exit from REWORK-REQUIRED needs a rework analysis (code, requirement or environment); the test-architect confirms a "code" cause; a requirement cause amends the criteria before code is touched (§4.2) | partly aligned. Rest: a production incident reaches START as a new issue with no link back to the landed spec; no living system spec [T-01] |
| A2 | The unit of work moves from agent to loop to crew (3, 4) | teams per stage (§7); the dispatcher (§14) | partly aligned. Rest: the dispatcher's host and worker start (O12) [T-03] |
| A3 | Gather → act → verify → repeat; "verify is where most loops break" (5) | the team loop with deterministic checks first and checker verdicts per SHA (§7.1, §4.1) | aligned |
| A4 | Loops inside loops: task, autonomous (`/goal`), crew (6) | task loop = waves inside IMPLEMENTATION; the independent "done" decision = the transition predicate over checker verdicts (§4); crew = dispatcher (§14) | differs on `/goal` (C3); otherwise aligned |
| A5 | Every loop needs a provable finish line: task, issue, backlog (7) | every transition's predicate (§4.2). A task is done when PR CI is green AND the verifier agrees, before TEST-READY. The backlog is done when no issue is open, except the rolling learning-batch issue (§11) | aligned |
| A6 | Feedback: bugs found in logs or CI become issues (7, 19) | inflows into START (§6.1); the close-out scans the deploy window's logs where the project provides a log query (§11); smoke attribution reads logs as data (§7.2); the triage rule admits an agent's defect statement that cites log lines (§6.5) | partly aligned. Rest: no scheduled scan of application logs outside the deploy window [T-05, T-13] |
| A7 | Learnings are captured automatically; a correction made twice becomes steering (7, 19) | close-out learnings go to the learning-batch issue, never to machine-local memory (§11); `/get-guidance` turns general answers into decision records (§12.9) | partly aligned. Rest (gap analysis 2.5): (a) no detection of corrections, (b) no recurrence counting, (c) no scheduled `/compile-memory`, (d) factory reports still commissioned by hand [T-12] |
| A8 | Workers coordinate on the backlog and in issue comments (7) | claims as server-enforced refs (§5); structured `factory-review/v1` records in comments (§8); no free-text negotiation | aligned, and stricter |
| A9 | The biggest loop: the empty backlog (8) | the dispatcher's queues guarantee a role for all pullable work (§14); budgets end every loop (§13) | partly aligned. Rest: the dispatcher's host (O12) [T-03] |
| A10 | Security Agent on the verify step and on every PR, a pen test before release; DevOps Agent in production, every incident a new issue (9) | optional external security review of PRs (risk-tagged by default); optional batched pen test (§7.2); `Origin: production` inflow with `priority:critical` (§6.1, §14) | partly aligned. Differs on "every PR" by default (C10). Rest: the production intake's details (O8), a system-level threat model [T-04, T-09] |
| A11 | Guardrails: no early stop, no guessing, someone else decides, effort matched to the task (10) | predicates and claims (§4, §5); evidence in every record (§8); maker ≠ checker per agent context (§8.1); the tier floor (§6.4); the tier-S path (§7.3); the stop gates extended to accept a transition as a valid end (§16) | aligned [T-11, T-19] |
| A12 | Drift: the reference is the spec, a separate check compares (11) | acceptance tests written at spec time; the test-freeze run (S's tests over H's code); the ask hash (§4.2, §4.3, §9) | aligned |
| A13 | Cost: every unattended loop gets a budget; credits per user and model (11) | soft and hard budgets per loop; spend lines from each harness as the source; report-only calibration first (§13, §17) | partly aligned. Rest: Kiro's per-user and per-model usage export (gap analysis 3.1 c) [T-02] |
| A14 | Control: central rules every loop and Crew agent follows (11, 14) | the authority table (§4.5); trust rules for tools (§15.1); per-host tokens without the permissions behind irreversible operations (§15.2); dispatcher-started workers inherit an interactive session's rules (§14) | partly aligned. Rest: per-agent deny rules by default and Kiro's central MCP and model allow-lists (O11); sandboxing of workers [T-17] |
| A15 | "Can the agent run the thing?" (12) | optional local runtime check per project, with a Playwright pilot (§9); the gate is the post-deploy smoke (§10) | partly aligned; differs on running before the PR on a shared environment (C4) [T-20] |
| A16 | Maker ≠ checker (12, 23, 24) | dedicated checkers per stage (§7); per-context identity (§8.1); the steward re-runs the fold (§8.6); the checked arbiter (§8.7); the checked rework classification (§4.2); the tier floor (§6.4) | aligned [T-01, T-19] |
| A17 | Kiro Crew: many loops, scheduled, unattended (14–16) | one candidate host of the dispatcher (§14) | partly aligned. Rest: host and worker start (O12); per-agent governance (O11); no MCP auto-discovery for checkers (C11) [T-03, T-17] |
| A18 | The demo: agents report what they did NOT verify (16, 27) | a required `notVerified` list in every verdict, carried into the close-out summary (§8.1, §11); "named, not run" for skipped tests (§7.4) | aligned [T-06] |
| A19 | Caveats: verification is still your job; comprehension debt; a bank is not a startup (18) | transition audit lines and records (§4.4, §8), not immutable (§19 item 4); the structured close-out summary (§11); admission and read-only checkers (§6.3, §15) | partly aligned. Comprehension debt and "a bank is not a startup" rely on the optional approval setting, off by default (C1) [T-18] |
| A20 | Do's and don'ts: verifier before generator; give it a stop condition; smallest high-signal context (23) | acceptance tests before implementation (§9); budgets (§13); diff-scoped checkers (§7.4) | partly aligned. Rest: every hand-off re-reads issue, spec and code (§19 item 6) [T-18] |
| A21 | AI-DLC: AI plans, asks clarifying questions, implements after a human validates (28); Inception / Construction / Operations with mob rituals (29) | START + SPEC / IMPLEMENTATION / TEST-READY + production inflow; questions up front in one batch (§12.2); human validation as the optional approval setting (§12.10) | differs (C1, reason extended) [T-18] |
| A22 | "A one-line fix stays a one-line fix"; "simplest thing that works" (10, 23) | the tier-S minimum path (§7.3) | aligned [T-16] |
| A23 | MCP: the loop reaches Jira, CI and your logs (24) | MCP servers as optional accelerators; every gate has a CLI path (§7.5); the Jira mapping (§3.6) | differs on gates depending on MCP (C8); the Jira backend is not covered [T-17] |
| A24 | Steering files: memory that survives the session (24) | learnings flow through the learning-batch issue into steering and rules in the repository (§11) | aligned [T-12] |
| A25 | Crew's controls: sandbox, approval modes, audit log, MCP auto-discovery, webhooks (15) | audit lines (§4.4); read-only checkers and pinned servers (§15.1); polling (§14) | partly aligned. Differs on auto-discovery (C11) and webhooks (C9). Rest: worker sandboxing [T-17] |
| A26 | Governance declared per agent, reviewable like code (16, notes) | — | not covered: per-agent deny rules (O11) [T-17] |

## B. Coverage of the gap analysis

### B.1 Its summary table (§1 of the gap analysis)

| # | Gap-analysis row | How the design addresses it | Status |
|---|---|---|---|
| 1 | Task loop: the running system is first exercised after the merge | optional local runtime check for M/L runtime changes (§9) | partial; deviation C4 |
| 2 | Issue loop: no single immutable record per issue | the transition audit lines, the records and the close-out summary (§4.4, §8, §11) give one readable record | partial. Rest: immutability (§19 item 4, O15) [T-08] |
| 3 | Backlog loop: manual start; no product priority input; fleet size is an operator action | the dispatcher's queues; priority labels with `priority:critical` first; capacity per role (§14) | partial. Rest: the host and worker start (O12) [T-03, T-09] |
| 4 | Parallel workers scale only on one host | server-enforced claim refs with fencing (§5) | designed (namespaces to verify, O14) |
| 5 | Guardrails: Kiro has no watchdog, StopFailure recorder or `/supervise` | the lease reaper and the dispatcher replace them for both clients (§5.2, §16) | partial. Rest: the reaper runs in the dispatcher, whose host is open (O12) [T-03] |
| 6 | Feedback loop: nothing reads runtime logs on purpose | the close-out's deploy-window log scan where the project provides a query (§11); smoke attribution (§7.2) | partial. Rest: no scheduled scan outside deploys [T-13] |
| 7 | Learning loop: capture by prose; compiling is manual | the learning-batch issue (§11) | partial. Rest: 2.5 (a)–(d) as in A7 [T-12] |
| 8 | Production loop missing | `Origin: production` inflow with expedite (§6.1, §14) | partial. Rest: the intake's details (O8) [T-09] |
| 9 | Security beyond the diff | OSV-Scanner, IaC gate, per-change threat-model lane, optional external PR review and pen test (§7.2) | partial. Rest: a system-level threat model (2.7 c); external review on every PR is a setting, risk-tagged by default (C10) [T-04] |
| 10 | SDLC return path into the spec | the rework analysis on every exit from REWORK-REQUIRED (§4.2) | partial. Rest: the production path back to the landed spec; a living system spec [T-01] |
| 11 | Drift of the backlog from the product | — | not designed |
| 12 | Cost: no budget, no per-issue cost | budgets per loop and per issue, with spend lines as the source (§13, §17) | designed [T-02] |
| 13 | Control: write scope optional on Claude; no Kiro governance tie-in | the authority table (§4.5), trust rules (§15.1), per-host tokens (§15.2) | partial. Rest: per-agent deny rules by default, Kiro allow-lists (O11) [T-17] |
| 14 | Crew loop: worker sessions are not started by anything | the dispatcher (§14) | partial. Rest: host and worker start (O12) [T-03] |
| 15 | Human validation (AI-DLC) | a configurable approval for specs AND for sensitive PR paths (§12.10) | designed as configurable; its default off is deviation C1 [T-07] |
| 16 | Measuring the factory | the figures from the records, including the spend lines, and a digest (§17) | designed [T-02] |

### B.2 Its cross-cutting sections

| Gap-analysis section | Design | Status |
|---|---|---|
| 3.1 Cost: (a) tokens per run and issue, (b) tier budgets that ask once, (c) Kiro's OpenTelemetry usage export | (a) the spend lines (§13); (b) soft limits act automatically, hard limits ask once (§13); (c) not designed | partial [T-02] |
| 3.2 Control: deny rules per agent by default; a governance profile for Kiro | trust rules and the authority table (§15.1, §4.5) | partial (O11) |
| 3.3 Who starts the loops | the dispatcher (§14) | partial: host and worker start open (O12) [T-03] |
| 3.4 Kiro parity | client-neutral enforcement (P9, §16); about 14 new roles, so the phase-2 renderer is a precondition (§16) | partial [T-14] |
| 3.5 Human validation | as row 15 | designed as configurable; default off = C1 [T-07] |
| 3.6 Measuring the factory | §17 | designed |
| 3.7 The update loop to consumer projects | — | not designed. Precondition: a factory project runs `merge: steward` (§3.5), so projects in `merge: direct` (e.g. AWSBedrockGateway) must switch, which is the gap analysis's rank 9 [T-15] |
| 3.8 A Jira wrapper | the stages map onto Jira statuses; claims and records need Jira equivalents (§3.6) | not designed: the wrapper is out of scope of the state model [T-21] |

### B.3 Its recommended order (§5 of the gap analysis), mapped

| Rank | Change | In the design |
|---|---|---|
| 1 | Cost per run and issue; tier budgets | §13 (spend lines, budgets), §17 |
| 2 | Production intake path | §6.1 (inflow and expedite only) |
| 3 | Event- and schedule-started runs | §14 (host open) |
| 4 | Automated learning capture | §11 (partial) |
| 5 | Dependency scan; then the AWS Security Agent | §7.2 |
| 6 | Returned work classified as code or requirement | §4.2 (every exit from REWORK-REQUIRED) |
| 7 | Configurable human approval point | §12.10 (specs and PR paths) |
| 8 | Pre-merge runtime check for M/L | §9 (optional, local) |
| 9 | Contract drift check per project, then BG's switch to steward + watcher | not designed; the switch is a precondition (§3.5) |
| 10 | `/delivery-status` digest | §17 |
| 11 | Jira wrapper | not designed (§3.6) |
| 12 | Phase 2 of the restructure | a precondition for the new roles (§16) |

### B.4 What the gap analysis says to keep (its §6) [T-11]

| Keep | In the design |
|---|---|
| The Stop-gate design and its fail-closed library | kept; the release vocabulary extends to transitions, `needs-input`, `ci-pending` and release (§16) |
| The delivery redesign: trains, verification by ancestry, red-streak attribution, `check-handoff`, the SESSION verdict gate | trains and ancestry kept. Red-streak blame replaced by Track T (§10.5, H8). `check-handoff` superseded by the TEST-READY → CLOSE-READY predicate. The SESSION verdict kept for interactive sessions; headless workers end with a verdict line (§16). Partly reversed, for the reasons in §10 and §14 |
| The filing discipline and the findings ledger | kept (§6.1, §11) |
| Proportionality with hard byte caps and frozen scope; the corpus budget test | kept; the tier-S minimum path made explicit (§7.3) |
| The adversarial verifier's mutant check per wave | kept (§7.2) |
| Measuring before changing | kept; §17 makes the figures a by-product of the records |

## C. Deliberate differences and deviations

| # | Source says | The design says | Why |
|---|---|---|---|
| C1 | AI-DLC: plan, ask clarifying questions, implement only after a human validates, in mob rituals (keynote slides 28, 29; gap analysis 3.5) | no human-only gates; an optional approval setting, off by default (§12.10). Clarifying questions are asked up front in one batch, after a question checker has removed those an agent can answer (§12.2, §12.4). Maker and checker teams with asynchronous answers replace the mob rituals | decisions U6, U12, U14, U17: humans are the last-resort conflict resolver and rarely return to sessions; a bank switches approval on [T-18] |
| C2 | "File an issue for everything you find" (slide 8 notes, slide 19); "should not quietly fix it either" (slide 7 notes) | fix it in the open (named in the commit and the report, never quietly), or file it with evidence (filing discipline) | measured: 60 % of all issues were spawned by working other issues; the gap analysis (2.4) recommends rewording the slide [T-23] |
| C3 | `/goal` as the independent judge (slides 6, 13; the keynote's `/goal` is Kiro's) | the transition predicate over checker verdicts is the independent judge; `/goal` is not used by the factory | a command cannot set `/goal`, and the predicate works the same on both clients. A human driving a session may still state a `/goal` over the transition predicate [T-22] |
| C4 | "Start the service, call the endpoint" before the PR (slide 12; gap analysis 2.1) | an optional local runtime check; the gate is the post-deploy smoke on the shared environment | decision U9 (no throwaway shared environments), and the gap analysis's own reason that not every project can run locally [T-22] |
| C5 | INPUT-REQUIRED as a state (the original state proposal) | `needs-input` as a flag on the current stage | decision U1: no return-address problem; questions arise in every stage |
| C6 | Return the whole CI batch to REWORK-REQUIRED (the original state proposal) | only the culprit returns, through cumulative trains | decision U2: blame-all bounced 37 landings in chess (2026-11-02) |
| C7 | A LANDED state between merge and close (the first design round) | TEST-READY spans up to the green smoke | decision U7 |
| C8 | MCP lets the loop reach your tools (slide 24) | MCP servers are optional; every gate has a CLI path (§7.5) | the desktop app's managed policy blocks project MCP servers; a gate must work in every client and in CI [T-17] |
| C9 | Runs start from webhooks, e.g. a new issue in Jira (slide 15) | the dispatcher polls (§14) | a workstation cannot receive forge webhooks (`docs/reports/webhook-triggers-analysis-2026-11-06.md`) [T-17] |
| C10 | The Security Agent reviews every pull request (slide 9) | external security review of PRs is a project setting, risk-tagged by default; the in-fleet security lane and the deterministic scans run on every PR (§7.2) | cost: the AWS Security Agent is billed per task-hour; a project sets `all` when it wants every PR [T-04] |
| C11 | MCP auto-discovery (slide 15) | checkers run with a strict MCP configuration and pinned servers (§15.1 rule 4) | a pull request could otherwise add an MCP server to its own checker through `.mcp.json` [T-17] |
