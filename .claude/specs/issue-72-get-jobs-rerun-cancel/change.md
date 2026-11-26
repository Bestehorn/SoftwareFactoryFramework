# Change: issue #72, `get-jobs`, `rerun` and `cancel` in the product GitHub wrapper

Tier: S. Kind: FEATURE. E2E: the compat golden cases drive the entry script's `main(argv)` against the fake host in
CI's `verify (tests)` leg; no forge call (Residuals).

## User Prompts

> Question: "Add get-jobs, rerun and cancel to the product GitHub wrapper?" Operator, 2026-11-26: "Yes, add them"

## Ask

Release v2026.11.26 (PR #71) installed the product wrapper as `scripts/github_wrapper.py`. The chess copy it replaced
had `get-jobs`, `rerun` and `cancel`; the product has none, and both setup prompts say they "arrive in a later
framework release". Add them with the copy's argv, options, output and exit codes (DL-002, DL-003).

## Acceptance criteria

"The copy" is `cmd_get_jobs`, `_job_billed_minutes`, `cmd_rerun`, `cmd_cancel`, their `add_parser` rows and usage
lines in `git show v2026.11.10.1:scripts/github_wrapper.py`.

- AC-1: WHEN `get-jobs <run_id>` runs, the wrapper SHALL send one request of `actions/list-jobs-for-workflow-run` with
  the copy's `per_page` and `filter=latest` (`filter=all` with `--all-attempts`), print the copy's
  `<id> <status> <conclusion> <name>` line, with its column widths and `None` for a missing conclusion, for each job of
  that page, and exit 0.
- AC-2: WHEN `--failed-only` is given, `get-jobs` SHALL print only the jobs whose `conclusion` is `failure`,
  `cancelled` or `timed_out`; WHEN the page's jobs carry more than one distinct `run_attempt`, each printed line SHALL
  end with `  [attempt=<run_attempt>]`.
- AC-3: WHEN `--show-steps`, `--timing` or `--show-runner` is given, each job line SHALL gain, after the attempt suffix
  and in this order, `  [steps=<number of steps>]`; `  [wall=<seconds>s billed=<minutes>min]` as
  `_job_billed_minutes` bills it, else `  [wall=? billed=?]`; `  [runner=<runner_name, else (none)> labels=<labels
  comma-joined, else ->]`. WHEN `--timing` is given, a last line SHALL give the copy's blank-column
  `TOTAL billed minutes (sum of per-job rounded-up): <sum over the printed jobs>`. WHEN `--step-status` is given, each
  job line SHALL be followed by the copy's `    step <number> <status> <conclusion> <name>` line per step, in order.
- AC-4: WHEN `rerun <run_id>` runs, the wrapper SHALL send a `POST` with no body on `actions/re-run-workflow`, or on
  `actions/re-run-workflow-failed-jobs` with `--failed-only`, print `Rerun requested for run <run_id>/rerun`
  (`<run_id>/rerun-failed-jobs` with `--failed-only`) and exit 0.
- AC-5: WHEN `cancel <run_id>` runs, the wrapper SHALL send a `POST` with no body on `actions/cancel-workflow-run`,
  print `Cancel requested for run <run_id>` and exit 0.
- AC-6: IF the host answers a request of the three with an error status, THEN the wrapper SHALL print nothing on
  standard output and exit 1; IF the argv is malformed, or the credential or the repository is refused, THEN it SHALL
  exit 2 and send nothing, as every other CI subcommand does.
- AC-7: The three subparsers SHALL take the copy's arguments (`get-jobs`: `run_id` as `int`, `--failed-only`,
  `--all-attempts`, `--show-steps`, `--show-runner`, `--timing`, `--step-status`; `rerun`: `run_id` as `int`,
  `--failed-only`; `cancel`: `run_id` as `int`) and the entry script's usage SHALL carry the copy's usage lines for
  them; `test/test_github_wrapper_fork_parity.py` SHALL list the three in `CI_SUBCOMMANDS` and load the copy's file as
  its oracle, written into a pytest temporary directory, a failing `git show` failing the test.
- AC-8: `prompts/setup-claude.txt` and `prompts/setup-kiro.txt` SHALL no longer say that `get-jobs`, `rerun` and
  `cancel` arrive in a later framework release; `CLAUDE.md` "This project" SHALL say, in place of the
  recorded-deviation sentence, that the toolchain wrapper is the product wrapper since v2026.11.26 and that a new
  subcommand is a module of `src/payload/scripts/github_api/commands/`; `docs/ci-capacity-ladder.md` and the ladder
  text of `prompts/setup-kiro.txt` SHALL name `get-jobs <run-id> --show-steps --show-runner` where they name
  `get-jobs <run-id> --steps`.

## Unchanged behaviour

- UB-1: Every existing subcommand SHALL CONTINUE TO match its golden case in `CASES`, on the product and on the copy,
  with no golden value edited.
- UB-2: `src/payload/scripts/github_wrapper.py` and `github_api/` SHALL CONTINUE TO import the standard library only.
- UB-3: No file `config/toolchain.json` lists SHALL be edited; the three reach `scripts/` at the next promotion.
- UB-4: The setup prompts' GitLab sentences and GitHub copy step SHALL CONTINUE TO read as they do.

## Files

The Tasks' `Files:` lists; there, `ci.py`'s and `actions.py`'s docstrings name the four records' commands, and the
three test files' docstrings name the copy at `v2026.11.10.1` as the oracle.

## Tests

Example tests: golden cases in `CASES`, run on the product by `test_a_subcommand_matches_its_golden_case`
(`src/payload/test/test_github_wrapper_compat.py`) and on the copy by `test_the_fork_produces_the_golden_case`.

- AC-1: `get-jobs/exit-0/latest-attempt` (one attempt, a job without a conclusion), `get-jobs/exit-0/all-attempts`;
  each a `StaticRouteSpec` whose query is the copy's `per_page` and `filter` and whose reply's `link` names a next page.
- AC-2: `get-jobs/exit-0/failed-only` with `--timing` on jobs of two attempts (`success` billed, `failure`,
  `cancelled`, `timed_out`, `skipped`); the suffix there and in `all-attempts`, none in `every-column`.
- AC-3: `get-jobs/exit-0/every-column`: `--all-attempts --show-steps --timing --show-runner --step-status` on jobs of
  one attempt, with and without steps, runner and labels, one running (no `completed_at`), one under a minute;
  `failed-only`'s TOTAL leaves the `success` job out.
- AC-4: `rerun/exit-0/whole-run`, `rerun/exit-0/failed-only`, each `POST` in `writes`.
- AC-5: `cancel/exit-0/requested`, its `POST` in `writes`.
- AC-6: one `<command>/exit-1/...` case per command and `_refusal_cases` per command.
- AC-7: `test_the_parsers_match_option_by_option` on the three new rows; both parity tests on the tag's copy;
  `test_the_usage_names_the_ci_commands` (the compat file): the copy's `get-jobs`, `rerun` and `cancel` usage lines
  in the entry script's `__doc__`.
- AC-8: checked on the diff.
- UB-1: the existing `CASES` and parser rows, unedited, on both sides.
- UB-2: `test_the_wrapper_imports_only_the_standard_library` (`test/test_github_wrapper_coverage.py`).
- UB-3: `test_an_installed_file_equals_its_source_at_the_release` (`test/test_toolchain_integrity.py`).
- UB-4: `test_the_setup_prompts_copy_the_package`, `test_both_prompts_copy_the_package_with_the_entry`; the GitLab
  sentences: checked on the diff, as AC-8.

## Tasks

Wave 1 (red: T1-T2 then green: T3-T4, one commit).

- [x] T1 TEST: the three's golden, refusal and usage cases. Files: `src/payload/test/github_wrapper_fixtures.py`,
  `src/payload/test/test_github_wrapper_compat.py`. Validates: AC-1 to AC-7. The exit-0 and exit-1 rows (an
  unknown subcommand exits 2) and the usage test red on the product, the refusal rows already exit 2 there; every
  golden row green on the copy.
- [x] T2 TEST: the oracle from the tag in place of `FORK_SCRIPT`; the three `CI_SUBCOMMANDS` rows. Files:
  `test/test_github_wrapper_fork_parity.py`. Validates: AC-7, UB-1. The three parser rows red.
- [x] T3 IMPL: the three commands, added by `register`, and their usage lines. Files:
  `src/payload/scripts/github_api/commands/ci.py`, `src/payload/scripts/github_api/families/actions.py`,
  `src/payload/scripts/github_wrapper.py`. Validates: AC-1 to AC-7, UB-1 to UB-3.
- [x] T4 IMPL: the prose. Files: `prompts/setup-claude.txt`, `prompts/setup-kiro.txt`, `CLAUDE.md`,
  `docs/ci-capacity-ladder.md`. Validates: AC-8, UB-4 (existing tests).

## Residuals

- No forge-suite case runs the three against an `sff-test-*` repository: it needs a workflow run there, outside the
  ask (findings ledger).
