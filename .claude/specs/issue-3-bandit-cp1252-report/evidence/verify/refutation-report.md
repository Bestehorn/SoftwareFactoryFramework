# Refutation report: issue #3, bandit's report on a cp1252 console

Verifier run 2026-11-10. Worktree `.claude/worktrees/issue-3`, branch `issue-3-bandit-cp1252-report`, HEAD
`4caddb5`, change under test `git diff f285222..HEAD -- src/`. Project venv: Python 3.14.2, bandit 1.9.4. Every
test command below is `venv/Scripts/python.exe scripts/run_tests.py src/payload/test/test_run_checks.py` (9 items
collected in every run).

## Step 1: whole-suite verdict

No CI run exists for `4caddb5`: `git branch -r --contains HEAD` lists no remote branch (the branch is pushed after
this verdict). The dispatch forbids a local full-suite run, so no `full-suite.txt` was written. The CI run on the
pushed SHA is still the pending whole-suite verdict.

## Results

| Claim | Command or mutation | Result | Verdict |
|---|---|---|---|
| baseline | unmodified tree | 9 passed, exit 0 | green |
| AC-4, I1 as a whole (M0) | `run_checks.py` overwritten with `git show f285222:src/payload/scripts/run_checks.py` | 1 failed, 8 passed: `test_ac1` at line 123, `B101` missing, bandit's `UnicodeEncodeError` then `RuntimeError: Unable to output report using 'txt' formatter` | FAILED-TO-REFUTE |
| AC-1, UB-3: the relay (M1) | `relay_text(...)` call replaced by `pass` | 2 failed: `test_ac1`, `test_ub3` (`B101` missing, `Text output written to file: reports/bandit.txt`) | FAILED-TO-REFUTE |
| AC-1: `errors="backslashreplace"` (M2) | `errors="strict"` | 2 failed: `test_ac1`, `test_ac2` (`UnicodeEncodeError` raised in `relay_text`) | FAILED-TO-REFUTE |
| AC-1: `-f txt -o` (M3) | the four arguments removed | 1 failed: `test_ac1` (formatter crash again) | FAILED-TO-REFUTE |
| AC-1, AC-3: report dir created (M4) | `report.parent.mkdir(...)` replaced by `pass` | 4 failed: `test_ac1`, `test_ac3[cp1252]`, `test_ac3[utf-8]`, `test_ub3` (bandit exit 2, `can't open 'reports/bandit.txt'`) | FAILED-TO-REFUTE |
| AC-1: the stream's own encoding (M7) | `encoding = "utf-8"` | 2 failed: `test_ac1`, `test_ac2` | FAILED-TO-REFUTE |
| CHG-STALE: `run_check` deletes an existing report before the command (§Change, run_check bullet) | `report.unlink()` replaced by `pass` (M5) | **9 passed, exit 0: the mutant survives** | **REFUTED** |
| CHG-LIST: `LIST_MAX_ARGS` rises to 16 so `--list` prints the bandit command whole (§Change, last bullet) | `LIST_MAX_ARGS = 12` (M6) | **9 passed, exit 0: the mutant survives** | **REFUTED** |
| relay newline guard (M8, a note, not a claim) | `shown = text` | 9 passed. Equivalent mutant: bandit `formatters/text.py` `report` builds `"\n".join(bits) + "\n"`, so a bandit report always ends with a newline. The line is executed; only its `else` arm is unreachable | not refuted |
| UB-1 | `test_ub1_bandit_runs_as_a_module_of_this_interpreter`, `test_ub1_console_script_fallback_keeps_the_arguments` | green in the baseline and in M0 to M8 | FAILED-TO-REFUTE |
| UB-2 | `test_ub2_config_passed_when_pyproject_is_a_file`, `test_ub2_config_omitted_without_pyproject` | green throughout; they assert the `("-c", "pyproject.toml")` pair present, then `-c` and `pyproject.toml` absent | FAILED-TO-REFUTE |
| UB-3 | `test_ub3_findings_listed_and_failing_on_a_utf8_stdout` | green in the baseline; killed by M1 and M4 | FAILED-TO-REFUTE |

Captures: every mutant run was captured to `tmp/` and is quoted above. The captures were deleted because the
dispatch allowed this report as the only artefact (agent-state-convention §1c makes the orchestrator the writer of
evidence captures).

## Step 2: kill the mutant (wave 1)

M0 and six of the eight targeted mutants fail the paired tests. M5 and M6 pass all 9 tests. Under this procedure, a
test suite that passes without the behaviour leaves that behaviour REFUTED.

## Step 3: vacuity scan

`test_run_checks.py` has no `skip`, `xfail` or `importorskip`, and no mark except `parametrize`. There is no
`conftest.py` under `src/payload/`. `pyproject.toml` `addopts` is `-ra --import-mode=importlib`, which deselects
nothing. Every one of the 8 test functions asserts. The precondition `pytest.raises(UnicodeEncodeError)` in
`test_ac1` is real: U+274C has no cp1252 code point. FAILED-TO-REFUTE.

## Step 4: red-for-the-right-reason

`evidence/red/wave-1.txt` collected 9 items. Its one failure is an `AssertionError` at `test_run_checks.py:123`
(`B101` missing), and the output carries the issue's exact symptom. It is not a load or collection error. M0
reproduced the same failing test at the same line. AC-2, AC-3 and UB-3 also passed at red, which is consistent:
the pre-change crash already exited 1, AC-3's clean source holds no U+274C, and UB-3 runs on UTF-8. AC-4 names only
the AC-1 test as the red one. FAILED-TO-REFUTE.

## Step 5: coverage of the change

Every new line of `run_checks.py` is executed by a child-process test except two:

- `report.unlink()` in `run_check`. Every child test builds a fresh scratch project (`make_project` creates only
  `project/src`), so `reports/bandit.txt` never exists before the run. The in-process tests never call
  `run_check`. M5 survives. A test that pre-creates the report with a sentinel would kill it.
- `LIST_MAX_ARGS = 16`. It is read only by `listed()`, which only `main(["--list"])` calls. Grep over every test
  suite finds no caller of either. `bandit_argv()` now has 14 elements, so at 12 `--list` would print
  `... (+2 more)`. M6 survives.

Both are REFUTED. Neither one maps to an AC or UB statement: they are §Change behaviours of I1.

## Dispatch point 4: UTF-8 stdout and the console-script fallback

- UTF-8 stdout. In `relay_text`, encoding with utf-8 and then decoding is a lossless round trip, because
  `read_text(errors="replace")` produces no lone surrogates. `test_ac3[utf-8]` and `test_ub3` are green. M1 kills
  `test_ub3`, so the UTF-8 listing depends on the relay.
- Console-script fallback. `runnable` returns `(script, *argv[3:])`, and `argv[3:]` holds
  `-f txt -o reports/bandit.txt`. `test_ub1_console_script_fallback_keeps_the_arguments` asserts exactly that.
  The script is `bandit = bandit.cli.main:main` (`bandit-1.9.4.dist-info/entry_points.txt`). That is the same
  `main` whose `-o` is `argparse.FileType("w", encoding="utf-8")` (`bandit/cli/main.py`). The relay is keyed on the
  check name, not on `argv[0]`. No test runs the console script end to end; `runnable` itself is unchanged code.

## Tree restoration

The worktree's `run_checks.py` has CRLF line endings, so it was backed up byte for byte to `tmp/`. M0 was restored
with `cp -p`. M1 to M8 were written and restored as bytes by a throwaway harness in `tmp/`, which checked each
restore. After M0 and again after the harness, `cmp` against the backup was identical and `git status --porcelain`
was empty. The `tmp/` files were removed afterwards. This report is the only file added.

REFUTED CHG-STALE CHG-LIST
