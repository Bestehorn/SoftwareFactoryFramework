---
description: Implement an approved spec test-first (TDD), proving every task works with captured command/test evidence, then run adversarial verification and write the evidence report.
argument-hint: [feature slug, e.g. customer-count-fix]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, mcp__ccd_session_mgmt__set_session_title, Agent(spec-implementer, adversarial-verifier, spec-review-agent, test-architect, standards-reviewer, best-practice-reviewer, security-reviewer, devops-iac-reviewer)
---

Run the IMPLEMENT_LOOP + VERIFY + EVIDENCE_REPORT phases for the spec at
`.claude/specs/$ARGUMENTS/` (if no slug is given, use the most recently modified spec
under `.claude/specs/`).

**Readiness check first.** Read `review/review-latest.md` and the latest
`test-architect` coverage report. Proceed ONLY if the readiness gate is met: combined
A+B == 0 (after ≥1 review cycle) AND zero coverage GAPs (`TEST-READY`). If it is not
met, do not implement — run `/spec-review` (or the conductor's review loop) and report
the open A/B findings instead.

Then follow `.claude/specs/_workflow/phases/spec-phase-implement.md` exactly:
- Ensure the venv exists/active. The test command is `python scripts/run_tests.py`
  (bounded local workers, no fail-fast); never `pytest -n auto`.
- For each task in `tasks.md` order: TEST tasks via `spec-implementer` (you run them,
  capture `evidence/red/<task>.txt`, assert red-for-the-right-reason); IMPL tasks via
  `spec-implementer` (you run the PAIRED tests → `evidence/green`, commit, then mark
  `[x]`). No per-task full-suite run: commits are cheap and the regression verdict for the
  whole batch is the ONE CI run after you push (`ci-owns-the-test-suite.md`), captured to
  `evidence/regress/`. YOU run the tests and capture evidence — the implementer never
  certifies its own work.
- VERIFY: invoke `adversarial-verifier` (it takes an independent whole-suite result —
  normally the CI run for the pushed SHA — and tries to refute every claim)
  and re-run the reviewer panel on the implemented diff; reopen tasks on any
  refutation or new A/B.
- Write `evidence/REPORT.md` and finish by quoting the proof summary (every "passes"
  is a quoted command output, never an assertion).

Session title (Claude desktop app; `.claude/docs/session-title.md` is the rule): rename this session with
`mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`) as the phase changes —
`Spec <feature> · implementing` for the tasks, `Spec <feature> · verifying` for VERIFY, `Spec <feature> · report`
for the report, `Spec <feature> — done` when it is written. A declined rename is not a blocker.

Append `DL-NNN` entries throughout per `.claude/rules/agent-state-convention.md`.
Honor the spec-drift guard (do not let the implementer edit requirements/design/
tasks). Never touch `.kiro/`.
