# Evidence report — issue #3: bandit's report on a cp1252 console

Tier S, one wave (T1, I1). Branch `issue-3-bandit-cp1252-report`.

| Criterion | Test (`src/payload/test/test_run_checks.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 findings listed on a cp1252 stdout, no traceback | `test_ac1_findings_listed_on_a_cp1252_stdout` | red/wave-1.txt (failed: B101 missing, UnicodeEncodeError); green/wave-1.txt | green |
| AC-2 a finding still fails the check | `test_ac2_finding_fails_the_check` | green/wave-1.txt | green |
| AC-3 a clean project passes on cp1252 and UTF-8 | `test_ac3_clean_project_passes[cp1252]`, `[utf-8]` | green/wave-1.txt | green |
| AC-4 the cp1252 test fails before the change | `test_ac1_…` red for the right reason | red/wave-1.txt; `red_for_right_reason.py` OK | proven |
| UB-1 `-m bandit` probe and console-script fallback | `test_ub1_bandit_runs_as_a_module_of_this_interpreter`, `test_ub1_console_script_fallback_keeps_the_arguments` | green/wave-1.txt | green |
| UB-2 `-c pyproject.toml` only when the file exists | `test_ub2_config_passed_when_pyproject_is_a_file`, `test_ub2_config_omitted_without_pyproject` | green/wave-1.txt | green |
| UB-3 UTF-8 stdout still lists findings and fails | `test_ub3_findings_listed_and_failing_on_a_utf8_stdout` | green/wave-1.txt | green |
| §Change: stale report deleted before the run | `test_chg_stale_report_deleted_before_the_check_runs` | verify/mutants-after-reopen.txt (M5 killed) | green |
| §Change: `--list` prints the bandit command whole | `test_chg_list_shows_the_bandit_command_whole` | verify/mutants-after-reopen.txt (M6 killed) | green |

The green capture (`# tasks: T1 I1`) runs the module together with `test/test_layout.py` (67 passed); the layout guard needed the `.claude/specs/` historical-record exemption once the spec's evidence was committed.

**Verifier.** `adversarial-verifier`: first pass REFUTED CHG-STALE and CHG-LIST (two §Change lines with no test); T1 was reopened and both tests added; the re-verification returned VERIFIED (`verify/refutation-report.md`).

**Local checks.** `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Whole suite.** The CI run on the pushed head SHA is the regression verdict; its run id and SHA are recorded in the PR and in the issue's closing comment. CI runs for this batch: target one.

**Diff.** `run_checks.py` +45/−3; `test_run_checks.py` new; `test/test_layout.py` `HISTORICAL` +`.claude/specs/`.
