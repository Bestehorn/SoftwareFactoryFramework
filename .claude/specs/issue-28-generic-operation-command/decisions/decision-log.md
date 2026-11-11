# Decision Log

## DL-001 — 2026-11-10T22:57:47Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's own tier line); the three open questions are design choices settled in design.md, not operator questions.
**Driver:** issue #28 Tier line and Open questions; #17 design D1/D2/D5 give the precedent (records as data, commands/ modules discovered by the entry script).
**Alternatives considered:** tier L (rejected: no new subsystem — one command layer over part 1's registry).
**Evidence:** issue #28 body; .claude/specs/issue-17-github-wrapper-foundation/design.md Residuals.
**Supersedes:** none
**Artifacts touched:** prompt.md, qa_log.md

## DL-002 — 2026-11-10T23:07:55Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Accept requirements.md as written: concrete print forms (paged → one JSON array of item_key items, JSON → print_json, empty → nothing, non-JSON → raw bytes) and refusals exit 2 (EXIT_REFUSED); the call mechanism itself stays design.md's choice.
**Driver:** AC-1/AC-2 of #28 need testable output and exit codes; exit 2 is the entry script's usage-error code.
**Alternatives considered:** leave print forms to design (rejected: criteria would not be testable).
**Evidence:** requirements.md AC-1.4..AC-1.7, AC-2.1..AC-2.3.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-10T23:51:12Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Consolidate iteration 01 into six root causes (X1–X6) and fix SEC-B1 inside `call`: it refuses an operation id a gated compatibility subcommand covers (pulls/merge → merge-pr, issues/create → create-issue), exit 2; extending the hooks is left to the slice that adds a trunk-writing record (residual).
**Driver:** review/security-reviewer/iteration-01.md B1 (gate_merge_steward and gate_filing match subcommand names only); scope freeze — no new guard mechanism beyond keeping the existing guarantee.
**Alternatives considered:** extend both hooks to parse `call` (rejected here: a second component and a new matching rule in this change).
**Evidence:** review/review-latest.md X1–X6.
**Supersedes:** none
**Artifacts touched:** review/review-latest.md

## DL-004 — 2026-11-11T00:09:15Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Accept the author's two deviations from review-latest.md: the refusal exception is caught in `cmd_call` (not `_run_command`), and the AC-1.2/1.3/2.2 examples move from `issues/create` to `issues/update` once X4 refuses `issues/create`.
**Driver:** catching ValueError in `_run_command` would change every compatibility command's exit path (UB-1.1); X4 makes `issues/create` unreachable through `call`.
**Alternatives considered:** catch in the entry script (rejected: UB-1.1 risk).
**Evidence:** design.md D2 step 4, D4 'How a refusal is written'; author report of iteration 01 fixes.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-005 — 2026-11-11T00:27:16Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve design.md after iteration 02 (all six lanes CLEAN/READY, A+B = 0; TEST-READY 21/21); the iteration-02 C/D items applied in one author pass without a further round.
**Driver:** review/<lane>/iteration-02.md verdicts.
**Alternatives considered:** none
**Evidence:** review/review-latest.md iteration 02 section.
**Supersedes:** none
**Artifacts touched:** design.md, review/review-latest.md
