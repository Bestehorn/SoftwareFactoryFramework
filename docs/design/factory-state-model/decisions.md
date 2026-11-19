# Decisions behind the factory state model (revision 3, 2026-11-19)

Five kinds of entry:

- **U**: decided by the operator in the design discussion.
- **M**: decided by the designer because it is reversible.
- **R**: adopted from the reviews by the designer: R1–R33 in revision 2, R34–R56 in revision 3. All are reversible
  and open to the next review. The finding ids name their source: [aN3] and [tN3] are new findings of the adversarial
  and the alignment re-review of revision 2.
- **B**: the working baseline. Recommended, not objected to, open to review; revised where an R entry says so.
- **O**: open, or deferred to a later change.

The discussion that produced them is in
[`docs/reports/factory-state-model-2026-11/discussion-log.md`](../../reports/factory-state-model-2026-11/discussion-log.md).
Where an entry there differs from this file, this file wins.

## U: decided by the operator

| Id | Date | Decision | Design |
|---|---|---|---|
| U1 | 2026-11-09 | INPUT-REQUIRED is a flag (`needs-input`) on the current stage, not a stage; setting it releases the claim; a separate command gives access to all open items | §3.2, §12 |
| U2 | 2026-11-09 | Pre-merge failures are attributed with the merge steward's cumulative trains; only the culprit returns. The whole-batch return of the original proposal is dropped as a regression | §10.1 |
| U3 | 2026-11-09 | Revert first when a deployment fails or the deployed code fails the smoke test, minimising the time the solution is non-functional | §10 |
| U4 | 2026-11-09 | Maker ≠ checker everywhere, with dedicated checker agents; makers and checkers exchange structured data (JSON), also through issue comments or repository mechanisms across issues and machines | §7, §8 |
| U5 | 2026-11-09 | Every stage has a clearly defined, deterministically checkable goal; the team loops until it holds; only after the agents have tried does the human get involved, through the flag | §4, §7.1, §13 |
| U6 | 2026-11-09 | No stage or gate that only a human can pass; the system works without human intervention; the human resolves conflicts only when everything else is exhausted | P6, §12 |
| U7 | 2026-11-09 | TEST-READY covers queue, merge, CI, deploy and smoke; CLOSE-READY starts when all of that is green; no separate LANDED state | §3.1 |
| U8 | 2026-11-09 | No cap on the number of IMPLEMENTATION-READY issues; workers prefer them, and write specs when CI is red or nothing is ready | §4.3, §14 |
| U9 | 2026-11-09 | Assume shared environments and no throwaway environments; batch incoming changes so many issues share one CI or deploy run | §9, §10.1 |
| U10 | 2026-11-09 | Agent comments and human comments are told apart by an inline marker | §8.2 |
| U11 | 2026-11-09 | Budgets and bounce thresholds are derived from the projects' data; escalation to the human must be the absolute exception | §13 |
| U12 | 2026-11-10 | Reversible questions proceed with the recommended option, recorded as an assumption the human may override | §12.1 |
| U13 | 2026-11-10 | All new checker lanes are agreed; additional sources (the awslabs threat-modeling MCP server, plugin marketplaces, MCP catalogues, Kiro powers) were to be checked | §7.2, §15 |
| U14 | 2026-11-10 | Questions are welcome only when nothing but the human can answer them; they come in one batch, never drip-fed (the operator rarely returns to sessions) | §12 |
| U15 | 2026-11-11 | The review set lives in `docs/design/factory-state-model/` on a branch, not merged | this folder |
| U16 | 2026-11-11 | The operator's and the factory's issues are auto-admitted; every issue, the operator's included, goes through triage, with no pass-through | §6 |
| U17 | 2026-11-11 | A human approval point exists only as an optional per-project setting, off by default | §12.10 |
| U18 | 2026-11-11 | CLOSE-READY is not code clean-up; anything that changes repository assets needs a PR. CLOSE-READY covers: local temp files, unneeded branches, temporary test and verification infrastructure, new issues found through the deployment, documentation and lessons-learned updates, and a structured summary for the operator | §11 |
| U19 | 2026-11-11 | Distribution stays file-based, project by project. A plugin is a future option tied to AWSBedrockGateway and needs equivalents for Kiro and other harnesses | §16 |
| U20 | 2026-11-11 | The Minimum revert tier (cached cloud assemblies plus a restore hook in the deploy script) is required for every AWS project, through the setup and update prompts | §10.6 |
| U21 | 2026-11-16 | Equal scrutiny: the operator's input gets neither more nor less scrutiny than an agent's; every input is judged on its content. (The operator asked why authorship should matter at all; the design answers in §12.3: only for reserved decisions, and not because the operator is trusted more) | P12, §8.3, §12.3 |
| U22 | 2026-11-16 | The keynote is a high-level vision, in no way a specification; the design is traced against it as alignment, not compliance | traceability.md |
| U23 | 2026-11-16 | Adversarial reviews are permanent records: they are committed beside the design they reviewed, not kept local | `docs/reports/factory-state-model-2026-11/reviews/` |
| U24 | 2026-11-16 | The agents keep posting as the operator's account (no machine account, no GitHub App). The residual, that a compromised agent could forge a reserved decision, is accepted, limited by P12, the forge-bound gates and per-host tokens. The shared write budget makes the write reductions binding | §15.2, §4.5, §19 item 3 |

## M: decided by the designer (reversible)

| Id | Decision | Reason | Design |
|---|---|---|---|
| M1 | Cached cloud assemblies live in an S3 bucket in the dev account, with retention at least the `cdk gc` rollback buffer; only the deploy role writes it, and each assembly's SHA-256 is recorded and verified | chess hit the GitHub artifact storage limit; CI artifacts are the fallback for projects without AWS; integrity from B17 | §10.6 |
| M2 | The guidance command is named `/get-guidance` | commands name what the agent does; "guidance" also covers approvals and stuck reports | §12.9 |
| M3 | An optional local runtime check per project before the PR, for M/L runtime changes | gap analysis 2.1, within U9 | §9 |
| M4 | Production alarms are an inflow into START (`Origin: production`) under the filing gate | gap analysis 2.6 | §6.1 |
| M5 | ALL learnings found at CLOSE-READY go to one rolling learning-batch issue (none to machine-local memory); it rotates per PR and is exempt from the empty-backlog count and from its own learning capture | reconciles U18 with the measured follow-up-PR cost (40 % of chess PRs); T-12, C8 | §11 |

## R: adopted from the reviews (revision 2)

| Id | Decision | Findings | Design |
|---|---|---|---|
| R1 | Authority is explicit: a role table names who may call each edge and write each record; the steward and the watcher call the transition verb; anything else is data | A1, B3, B13 | §4.5 |
| R2 | One claim per issue, not per stage; the claim is a git ref acquired and renewed by `git push --force-with-lease` (a server-side compare-and-swap), its SHA is the fencing token, the reaper expires it by its own clock, ONE release verb | A3, B1, C11, C17, C20, C21 | §5 |
| R3 | The transition verb writes an intent line first and a done line last; the reconciler rolls forward; an issue with no stage label and no audit line is in START; a hand-set label is corrected or recorded as an override | B2, C16 | §4.4 |
| R4 | Maker ≠ checker is checked on a per-context `actor.agent` and the lane role, not on the session | A2 | §8.1 |
| R5 | A comment counts as an answer, approval or ask change only from an authorised human; all other comments are data, judged on content (U21) | A4, B5 | §8.3, §12.3 |
| R6 | Admission is by the issue's author; provenance lines never admit; the admission view shows the verbatim body | B8, C13 | §6.3 |
| R7 | The ask is the ask hash (title + body without ticks), changed only by an edit or `/amend` from an authorised human, checked in SPEC and IMPLEMENTATION only; answers do not re-open the spec | B5 | §4.3 |
| R8 | Landings and reverts are derived per PR from trunk's first-parent history (`Steward-PR`, `Reverts-PR` trailers); `merge-steward:` comments are projections | B7, B15 | §10.8 H1, H7 |
| R9 | A red verdict marks no issue; only Track T's culprit record returns one | B11 | §10.5 |
| R10 | The watcher never closes; it transitions TEST-READY → CLOSE-READY | B12 | §10.8 H9, §11 |
| R11 | The steward dispatches a revert PR's CI itself (or exempts it from PR CI), orders reverts first, and the deploy job skips commits containing an attributed culprit until its revert lands | B14, C18 | §10.4 |
| R12 | Attribution: exactly one step changing the failing resource and none changing its dependency closure is a culprit; several form a suspect set; a defined failure signature; refunds for wrong attributions; the log-reading attributor only ranks inside the suspect set | B16, C15 | §10.4, §13 |
| R13 | The restore checks its own change set for stateful replacement or deletion and stops into an `env-incident` | B17 | §10.3 |
| R14 | Environment problems and escalations are open `env-incident` issues per root cause; `delivery-status` stays the closed machine status record | B13 | §12.5 |
| R15 | Every exit from REWORK-REQUIRED needs a rework analysis (code, requirement or environment), and the test-architect confirms a "code" cause | T-01 | §4.2 |
| R16 | The worker never transitions with PR CI pending: it sets `ci-pending` and releases; the verifier lane completes the transition when CI has ended. `--allow-pending` only for a re-enqueue whose only unmet clause is pending CI | C1, C2, T-10 | §4.2, §14 |
| R17 | The acceptance-test freeze is a run: S's tests, fixtures and test configuration over H's code | B19 | §4.2, §9 |
| R18 | Readiness of the spec PR is the `do-not-merge` label, a draft only where the forge has drafts | B22 | §9 |
| R19 | A deterministic tier and risk floor that triage may raise but not lower, re-derived at SPEC exit, raise-only | B18, T-19 | §6.4 |
| R20 | Every verdict carries a required `notVerified` list, carried into the close-out summary | T-06 | §8.1, §11 |
| R21 | Spend lines per checkpoint and release are the source of the cost budget; budgets are report-only for the first 20 issues per tier, then recalibrated | T-02, C6 | §13 |
| R22 | One review envelope per round; PR projections off by default; comments paged with an id filter, the cursor in the claim ref; fold by id; edited record comments rejected; a continuation issue at 2,000 comments; a host-wide write token bucket | B10, C4, C5, C21 | §8.2, §15.2 |
| R23 | The steward re-runs the fold before landing; a downgrade of a blocking finding needs the lane's accept or the arbiter; an arbiter decision is re-checked, and one that overrules a security or legal finding becomes an approval | B6, C22 | §8.5–§8.7 |
| R24 | The dispatcher has queues per stage, per checker lane, for the verifier (`ci-pending`) and for the answer recorder; `priority:critical` goes first | B3, B4, T-09 | §14 |
| R25 | Temporary resources are tagged `factory-issue=<repo>#<n>`; close-out queries by tag as well as reading the ledger | B20 | §11 |
| R26 | Factory mode requires `merge: steward`; `verification: watcher` and `none` are both mapped; `merge: direct` projects keep the session workflow | B21, T-15 | §3.5 |
| R27 | External security review of PRs (AWS Security Agent) is a project setting, `risk` by default; an optional batched, budget-capped pen test in TEST-READY | T-04 | §7.2 |
| R28 | The approval setting also covers sensitive PR paths, at IMPLEMENTATION → TEST and REWORK → TEST | T-07 | §12.10 |
| R29 | A deterministic always-ask list for the question checker (IAM grants, deletions, production, credentials) | C12 | §12.4 |
| R30 | The triage rule against untrusted content refuses an instruction taken from quoted text, not an agent's defect statement citing logs | T-05 | §6.5 |
| R31 | The tier-S minimum path, with one combined review pass as today | C7, T-16 | §7.3 |
| R32 | The stop gates and release vocabulary accept a transition, `needs-input`, `ci-pending` or release as a valid end; the phase-2 renderer comes before the new roles | T-11, T-14 | §16 |
| R33 | Per-host fine-grained tokens, without the permissions behind irreversible operations | B9 | §15.2 |
| R34 | EVERY caller of the transition verb holds the claim ref for the length of its call (`record` claims for the steward, the recorder, `/get-guidance`, the dispatcher). The steward is the only caller of TEST-READY's exits; the watcher records facts. The reconciler touches only issues whose claim is free and whose intent is older than L | aN1, B2 | §4.4, §4.5, §5.3 |
| R35 | The authority table has Conductor, Arbiter, Question-checker and Dispatcher rows, and complete Steward and Watcher rows; the reconciler only completes or undoes another role's intent; the dispatcher closes `split` parents | aN2, A1, C9 | §4.5 |
| R36 | The claim ref is permanent: `held` and `free` commits, both keeping the fold cursor; the issue branch and the claim are pushed in one atomic push; renewal only on writing wrapper calls, with no heartbeat; group claims in one atomic push. Supersedes R2's delete-on-release and back-off | aN4, B1, C4, C17, C20 | §5 |
| R37 | The wrapper marks EVERY agent comment and body write and refuses unmarked ones from agent paths; forge MCP write tools are denied to agents; a human's comment changes state only through explicit forms (`/answer`, `/approve`, `/amend`, `/stage`); hand-set stage labels are reverted, never overrides | aN5, aN13, A4, B4, C16 | §8.2, §8.3, §4.4 |
| R38 | The ask is the title plus the body above a machine-owned marker; agents write only below it | aN6, B5 | §4.3 |
| R39 | Queue exclusions for every queue; a `ci-pending` timeout; `env-incident` issues outside every queue, with an owner on the allow-list; the recorder starts only on an explicit form newer than its last run; every steward reject and a PR closed unmerged return the issue | aN3 | §4.2, §12.5, §12.7, §14 |
| R40 | The revert fact is a `Steward-Reverts` trailer on the steward's own first-parent merge; a GitHub trunk ruleset is required; the steward checks each first-parent push's actor in the activity record | aN7, B7, B15 | §3.5, §10.4, §10.8 |
| R41 | Setup enables "Allow GitHub Actions to create and approve pull requests"; the steward checks it every tick; a refused revert PR is an immediate `env-incident`; the revert exemption and ordering require the steward's identity AND an exact `git revert -m 1` of a steward merge | aN8, B14 | §3.5, §10.4 |
| R42 | Every stage exit that closes a stage needs a verdict from a separately started checker; in-session lane records are as trustworthy as the maker's session; tier S's spec pass stays in-session as a recorded trade-off | aN9, A2, B6 | §8.5 |
| R43 | Deploy facts are read from the run API, pinned to the deploy workflow's path, event, trunk ref and environment; `verdict --conclusion` is replaced; issue records count only when they name a pinned run | aN10 | §4.2, §4.5, §10.8 H13 |
| R44 | `eligibility` waits while an issue the PR references carries `hold` | aN11 | §3.2 |
| R45 | The Minimum revert tier also requires the stateful replacement/deletion detector and a migration ledger; the cache digest sits in the S3 object's metadata | aN14, B17 | §10.3, §10.6 |
| R46 | An edited record comment puts the issue on `tamper` instead of being skipped | aN15, C21 | §8.2 |
| R47 | Whether an arbiter decision overrules a legal or security finding is computed from the records | C22 | §8.7 |
| R48 | The close-out reads no logs and may delete only resources tagged with its issue; a separately started, read-only log-scan lane scans the deploy window | tN1, T-13 | §7.2, §11 |
| R49 | The spend line carries `model=`, `writes=` and `step-seconds=`, and every role that runs an agent context writes it | tN3, B10 | §13 |
| R50 | Only the cost, bounce and claim counters are report-only for the first 20 issues per tier; the review caps stay enforced | tN4 | §13 |
| R51 | An "environment" rework cause is confirmed by the steward's infra classifier or the attributor; the issue stays in REWORK-REQUIRED, `blocked-by` the incident, and is re-checked when it closes | tN10 | §4.2 |
| R52 | Decision A2 is reversed, and `check-handoff` superseded, only once the dispatcher runs on a host | tN11 | §14, §16, §18 |
| R53 | A START issue filed by a factory login with `Origin: production` is pulled before everything else | T-09 | §6.1, §14 |
| R54 | A docs-drift checker and tools in IMPLEMENTATION-READY when a change touches a documented interface | tN7 | §7.2 |
| R55 | The pen test is batched and not a release gate; exploitable findings enter START as `priority:critical` | tN8 | §7.2, traceability C10 |
| R56 | Under U24 an approval's human authorship is not provable; a project whose auditors need it revisits U24 or uses a forge-native gate only the operator can pass | tN9 | §12.10 |

## B: working baseline (recommended, open to review)

| Id | Baseline | Design |
|---|---|---|
| B1 | ~~Claims as comments with leases~~: replaced by R2 | §5 |
| B2 | Stages are checkpoints, not compulsory hand-offs; one claim may carry a tier-S issue from START to TEST-READY, recording each transition | §3.4 |
| B3 | One transition verb in the wrappers (revised by R3: guard, intent, side effects, labels, done) | §4.4 |
| B4 | Stage storage as prefixed labels on both forges, plus a reconciler; native single-select storage later | §4.4 |
| B5 | The spec lives on the pushed issue branch with a PR (revised by R18: readiness is the `do-not-merge` label); a `spec-approved` record pins SHA and ask hash (revised by R7) | §9 |
| B6 | Acceptance tests are written at spec time and must fail for the right reason; the implementer may not change them, nor what they depend on, without SPEC re-entry (revised by R17) | §9 |
| B7 | A human edit of the ask after approval sends the issue back to SPEC-REQUIRED (revised by R7) | §4.3 |
| B8 | The `factory-review/v1` record format: SARIF-compatible findings, text-quote anchors, an append-only fold; the canonical log on the work issue; JSON in a fenced block inside `<details>`; the arbiter as a separate agent (revised by R4, R20, R22, R23) | §8 |
| B9 | The default standards precedence for the arbiter: legal/security > data loss > the ask's criteria and correctness > operability > maintainability > style | §8.7 |
| B10 | Revert details: while red, cap the batch size instead of pausing landings; ambiguous windows revert every suspect and reland in bisection order; smoke retried once; reverts get their train CI (revised by R11) | §10.4 |
| B11 | The pull order, right to left (revised by R24: `priority:critical` first; lane, verifier and recorder queues) | §14 |
| B12 | The dispatcher polls the tracker; webhooks cannot reach a workstation | §14 |
| B13 | The budget values and reset rules of the thresholds report (revised by R21) | §13 |
| B14 | Question discipline: decision inventory up front, question checker, routing by kind, standing permissions as policy, review tasks as one sheet (extended by R29, R14) | §12 |
| B15 | Trust rules: read-only checkers enforced in IAM; no mutating tool for a checker; everything pinned; strict MCP config for headless checkers; no deploy credentials with untrusted content | §15.1 |
| B16 | Admission for authors outside the allow-list: read-only triage, then an `admitted` label set by an authorised human (revised by R6) | §6.3 |

## O: open or deferred

| Id | Item | Note |
|---|---|---|
| O1 | Packaging the framework, or only its MCP servers, as a pinned plugin | future (U19); tied to the AWSBedrockGateway marketplace; Kiro and other harnesses need equivalents |
| O2 | Whether CI job environment variables (e.g. a plugin seed directory) are allowed under the no-environment-variables rule | only relevant with O1 |
| O3 | A reduced check for clean reverts (the "fast lane") | the full train CI until data shows the cost |
| O4 | Reconciling the Kiro powers' `AWS_PROFILE` in `env` blocks with the setup prompts' ban | before any power is adopted |
| O5 | Pinning the MCP servers the setup prompts install `@latest`, and narrowing the wildcard allow of the AWS API server | a framework change |
| O6 | Automated capture of corrections and recurrence counting (gap analysis 2.5) | not designed |
| O7 | Backlog drift measurement (gap analysis row 11) | not designed |
| O8 | The details of the production intake, incl. the AWS DevOps Agent (gap analysis 2.6) | inflow and expedite only (M4, R24) |
| O9 | The contract-drift check per consumer project (gap analysis 3.7) | not designed; switching projects to `merge: steward` is a precondition (R26) |
| O10 | A Jira wrapper (gap analysis 3.8) | out of scope; the stage mapping is in §3.6 |
| O11 | Per-agent deny rules by default; Kiro's central MCP and model allowlists (gap analysis 3.2); worker sandboxing | not designed |
| O12 | The dispatcher's host (Kiro Crew, headless CLI on CI runners, a workstation task), the command that starts a worker with a role and an issue per client, and the governance it inherits | B12 fixes polling only |
| O13 | ~~Which identity the agents post as~~ | decided as U24 (2026-11-16): the operator's account |
| O14 | Verify on `sff-test-*` repositories: that GitHub and GitLab accept pushes to `refs/factory/claims/*` and refuse a lease mismatch atomically, otherwise use the `factory-claim/` branch prefix; atomic multi-ref push support on both forges; whether a push to a custom ref starts any workflow; which actor a GitHub ruleset can exempt for a `GITHUB_TOKEN` trunk push | §5.1, §5.5, §3.5 |
| O15 | An immutable record per issue: a digest of the folded records written to a protected audit ref at close-out | §19 item 4 |
