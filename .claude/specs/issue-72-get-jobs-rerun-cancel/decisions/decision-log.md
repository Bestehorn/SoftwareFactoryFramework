# Decision Log

## DL-001 — 2026-11-26T15:00:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S: three subcommands on existing records in one module, their tests, and three sentences of prose.
**Driver:** issue #72 "Tier: S"; the records exist (`families/actions.py`); no new interface beyond the replaced copy's.
**Alternatives considered:** M (rejected: no design choice across components).
**Evidence:** issue #72 body; `src/payload/scripts/github_api/commands/ci.py` `register`.
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-26T15:00:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The three take the replaced copy's parser and output exactly (get-jobs: `--failed-only`, `--all-attempts`, `--show-steps`, `--show-runner`, `--timing`, `--step-status`; `--failed-only` keeps `failure`, `cancelled`, `timed_out`), settling #72's two open questions.
**Driver:** `docs/ci-capacity-ladder.md` reads the step and runner columns; the parser-parity mechanism (`test/test_github_wrapper_fork_parity.py`) compares option by option; the operator asked to restore what the promotion dropped.
**Alternatives considered:** list + `--failed-only` only (breaks the ladder's per-job evidence); every non-success conclusion (diverges from the copy sessions used).
**Evidence:** `git show v2026.11.10.1:scripts/github_wrapper.py` `cmd_get_jobs`; issue #72 "Open questions".
**Artifacts touched:** prompt.md

## DL-003 — 2026-11-26T15:00:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** `test/test_github_wrapper_fork_parity.py` reads its oracle, the replaced copy, from the tag `v2026.11.10.1` instead of `scripts/github_wrapper.py`.
**Driver:** since PR #71 `scripts/github_wrapper.py` is the product wrapper, so the test compares the product with itself (observed: `FORK_SCRIPT = ROOT / "scripts" / "github_wrapper.py"`; the integrity test proves that file equals `src/payload/scripts/github_wrapper.py`).
**Alternatives considered:** retire the test (deleting a test is forbidden; its oracle still exists in git); a vendored copy of the fork under `test/` (a 315 KB duplicate of what git holds).
**Evidence:** `config/toolchain.json` `files["scripts/github_wrapper.py"]`; PR #71.
**Artifacts touched:** prompt.md

## DL-004 — 2026-11-26T16:30:00Z — issue-work-orchestrator — phase:REVIEW

**Decision:** change.md approved at combined review iteration 02 (CLEAN, TEST-READY); its one C (the attempt suffix tested without `--all-attempts`, `success` billed) applied by the conductor without another round.
**Driver:** review/spec-review-agent/iteration-02.md; `spec-phase-review.md` Readiness gate.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-02.md C1.
**Artifacts touched:** change.md § Tests AC-2, AC-6
