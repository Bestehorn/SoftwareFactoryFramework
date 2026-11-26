# Prompt — issue #72: add get-jobs, rerun and cancel to the product GitHub wrapper

Tier: S — three subcommands on existing operation records in one module (`github_api/commands/ci.py`), their golden
cases and parity rows, and three sentences of prose; no new interface beyond restoring the replaced copy's (DL-001).

Kind: FEATURE.

## Goal

Release v2026.11.26, promoted by PR #71, installed the product wrapper as `scripts/github_wrapper.py`. The chess copy
it replaced had `get-jobs`, `rerun` and `cancel`; the product wrapper has none of them, and both setup prompts list them
in the GitHub minimum set while saying they "arrive in a later framework release".

> Question: "Add get-jobs, rerun and cancel to the product GitHub wrapper?" — Operator, 2026-11-26: "Yes, add them"

## Scope

1. `get-jobs`, `rerun` and `cancel` in `src/payload/scripts/github_api/commands/ci.py`, each with the replaced copy's
   argv, options, output lines and exit codes (`git show v2026.11.10.1:scripts/github_wrapper.py`: `cmd_get_jobs`,
   `cmd_rerun`, `cmd_cancel`, their `add_parser` rows), sent through the existing records
   `actions/list-jobs-for-workflow-run`, `actions/re-run-workflow`, `actions/re-run-workflow-failed-jobs`,
   `actions/cancel-workflow-run` (DL-002).
2. Their golden cases in `src/payload/test/github_wrapper_fixtures.py` `CASES`, which `test_github_wrapper_compat.py`
   runs on the product and `test/test_github_wrapper_fork_parity.py` on the replaced copy; the three added to that
   test's parser-parity rows; and the test's oracle read from `v2026.11.10.1` (DL-003), because `scripts/` holds the
   product wrapper since PR #71 and the test now compares the product with itself.
3. Prose: `prompts/setup-claude.txt` and `prompts/setup-kiro.txt` drop the "arrive in a later framework release" clause
   for these three; `CLAUDE.md` "This project" says the toolchain wrapper is the product wrapper since v2026.11.26;
   `docs/ci-capacity-ladder.md` names the real option (`--show-steps`, not `--steps`).

## Constraints

- UB: every existing subcommand unchanged (the compat and parity suites pass with no golden value edited); standard
  library only; no toolchain file edited (the change reaches `scripts/` at the next promotion).
- Test-first: the golden cases and parity rows red before the commands exist.

## Out of scope

The fork's other 34 subcommands; the release and promotion that install the three here (issue #72's last item, a later
step after the merge).

E2E: the wrapper's command line against the fake host in CI's `tests` leg; no forge call needed — `get-jobs` on a real
run is exercised by the next session that reads a CI run, and the GitHub forge suite does not call these three.
