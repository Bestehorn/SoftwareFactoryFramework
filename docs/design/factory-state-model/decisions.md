# Decisions behind the factory state model (as of 2026-11-11)

Four kinds of entry:

- **U**: decided by the operator in the design discussion.
- **M**: decided by the designer because it is reversible.
- **B**: the working baseline. Recommended, not objected to, and open to review.
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
| U17 | 2026-11-11 | A human approval point exists only as an optional per-project setting, off by default | §12.8 |
| U18 | 2026-11-11 | CLOSE-READY is not code clean-up; anything that changes repository assets needs a PR. CLOSE-READY covers: local temp files, unneeded branches, temporary test and verification infrastructure, new issues found through the deployment, documentation and lessons-learned updates, and a structured summary for the operator | §11 |
| U19 | 2026-11-11 | Distribution stays file-based, project by project. A plugin is a future option tied to AWSBedrockGateway and needs equivalents for Kiro and other harnesses | §16 |
| U20 | 2026-11-11 | The Minimum revert tier (cached cloud assemblies plus a restore hook in the deploy script) is required for every AWS project, through the setup and update prompts | §10.6 |

## M: decided by the designer (reversible)

| Id | Decision | Reason | Design |
|---|---|---|---|
| M1 | Cached cloud assemblies live in an S3 bucket in the dev account, with retention at least the `cdk gc` rollback buffer | chess hit the GitHub artifact storage limit; CI artifacts are the fallback for projects without AWS | §10.6 |
| M2 | The guidance command is named `/get-guidance` | commands name what the agent does; "guidance" also covers approvals and stuck reports | §12.7 |
| M3 | An optional local runtime check per project before the PR, for M/L runtime changes | gap analysis 2.1, within U9 | §9 |
| M4 | Production alarms are an inflow into START (`Origin: production`) under the filing gate | gap analysis 2.6 | §6 |
| M5 | Repository-side learnings found at CLOSE-READY go to one rolling learning-batch issue, not a follow-up PR per issue | reconciles U18 with the measured follow-up-PR cost (40 % of chess PRs) | §11 |

## B: working baseline (recommended, open to review)

| Id | Baseline | Design |
|---|---|---|
| B1 | Claims are comments with a worker id and a lease; the earliest unexpired claim wins (server-assigned comment ids); a reaper releases expired leases | §5 |
| B2 | Stages are checkpoints, not compulsory hand-offs; one claim may carry a tier-S issue from START to TEST-READY, recording each transition | §3.4 |
| B3 | One transition verb in the wrappers: compare-and-set, predicate check, additive label swap, an audit line | §4.4 |
| B4 | Stage storage as prefixed labels on both forges, plus a reconciler; native single-select storage later | §4.4 |
| B5 | The spec lives on the pushed issue branch with a draft PR; a `spec-approved` record pins SHA, ask hash and last human comment | §9 |
| B6 | Acceptance tests are written at spec time and must fail for the right reason; the implementer may not change them without SPEC re-entry | §9 |
| B7 | A human edit of the ask after approval sends the issue back to SPEC-REQUIRED (pickup and checkpoint check) | §4.3 |
| B8 | The `factory-review/v1` record format: SARIF-compatible findings, text-quote anchors, an append-only fold. The canonical log is on the work issue; the JSON sits in a fenced block inside `<details>`; the gate is a `factory/review` commit status; the arbiter is a separate agent | §8 |
| B9 | The default standards precedence for the arbiter: legal/security > data loss > the ask's criteria and correctness > operability > maintainability > style | §8.4 |
| B10 | Revert details: while red, cap the batch size instead of pausing landings; ambiguous windows revert every suspect and reland in bisection order; smoke is retried once; reverts get the full train CI (no reduced fast lane) | §10.4 |
| B11 | The pull order, right to left: REWORK > CLOSE-READY > IMPLEMENTATION-READY > SPEC-REQUIRED > START, then priority | §14 |
| B12 | The dispatcher polls the tracker; webhooks cannot reach a workstation | §14 |
| B13 | The budget values and reset rules of the thresholds report | §13 |
| B14 | Question discipline: decision inventory up front, question checker, routing by kind, standing permissions as policy, review tasks as one sheet | §12 |
| B15 | Trust rules: read-only checkers enforced in IAM; no mutating tool for a checker; everything pinned; strict MCP config for headless checkers; no deploy credentials with untrusted content | §15 |
| B16 | Admission for authors outside the allow-list: read-only triage, then an `admitted` label set by the human | §6 |

## O: open or deferred

| Id | Item | Note |
|---|---|---|
| O1 | Packaging the framework, or only its MCP servers, as a pinned plugin | future (U19); tied to the AWSBedrockGateway marketplace; Kiro and other harnesses need equivalents |
| O2 | Whether CI job environment variables (e.g. a plugin seed directory) are allowed under the no-environment-variables rule | only relevant with O1 |
| O3 | A reduced check for clean reverts (the "fast lane") | B10 uses the full train CI until data shows the cost |
| O4 | Reconciling the Kiro powers' `AWS_PROFILE` in `env` blocks with the setup prompts' ban | before any power is adopted |
| O5 | Pinning the MCP servers the setup prompts install `@latest`, and narrowing the wildcard allow of the AWS API server | a framework change |
| O6 | Automated capture of corrections and recurrence counting (gap analysis 2.5) | not designed |
| O7 | Backlog drift measurement (gap analysis row 11) | not designed |
| O8 | The details of the production intake, incl. the AWS DevOps Agent (gap analysis 2.6) | inflow only (M4) |
| O9 | The contract-drift check per consumer project (gap analysis 3.7) | not designed |
| O10 | A Jira wrapper (gap analysis 3.8) | out of scope of the state model |
| O11 | Per-agent deny rules by default; Kiro's central MCP and model allowlists (gap analysis 3.2) | not designed |
| O12 | The dispatcher's host: Kiro Crew, headless CLI on CI runners, or a workstation task | B12 fixes polling only |
