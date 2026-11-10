# Refutation report: issue #3, bandit's report on a cp1252 console

## First verification (HEAD 4caddb5)

Change `git diff f285222..HEAD -- src/`; venv Python 3.14.2, bandit 1.9.4; every run
`venv/Scripts/python.exe scripts/run_tests.py src/payload/test/test_run_checks.py` (9 items). No CI run existed for
`4caddb5` (`git branch -r --contains HEAD` empty); no local full suite.

| Claim | Mutation | Result | Verdict |
|---|---|---|---|
| baseline | none | 9 passed | green |
| AC-4, I1 (M0) | `run_checks.py` = `f285222` version | 1 failed: `test_ac1` (`B101` missing, `UnicodeEncodeError`, `Unable to output report using 'txt' formatter`) | FAILED-TO-REFUTE |
| AC-1, UB-3 relay (M1) | `relay_text(...)` -> `pass` | 2 failed: `test_ac1`, `test_ub3` | FAILED-TO-REFUTE |
| AC-1 backslashreplace (M2) | `errors="strict"` | 2 failed: `test_ac1`, `test_ac2` | FAILED-TO-REFUTE |
| AC-1 `-f txt -o` (M3) | the four arguments removed | 1 failed: `test_ac1` | FAILED-TO-REFUTE |
| AC-1, AC-3 report dir (M4) | `mkdir` -> `pass` | 4 failed: `test_ac1`, `test_ac3[cp1252]`, `test_ac3[utf-8]`, `test_ub3` | FAILED-TO-REFUTE |
| AC-1 stream encoding (M7) | `encoding = "utf-8"` | 2 failed: `test_ac1`, `test_ac2` | FAILED-TO-REFUTE |
| CHG-STALE (M5) | `report.unlink()` -> `pass` | 9 passed | REFUTED |
| CHG-LIST (M6) | `LIST_MAX_ARGS = 12` | 9 passed | REFUTED |
| newline guard (M8) | `shown = text` | 9 passed; equivalent mutant (bandit's txt formatter ends every report with a newline) | not a claim |
| UB-1, UB-2 | in-process tests | green under every mutant; assert `-m bandit`, the fallback argv, the `-c pyproject.toml` pair | FAILED-TO-REFUTE |

Vacuity: no skip, xfail, importorskip or deselection; every test asserts. Red: `evidence/red/wave-1.txt` fails
`test_ac1` on an `AssertionError` (`B101` missing), not a load error; M0 reproduced it. Coverage: every new line ran
except `report.unlink()` and `LIST_MAX_ARGS`. Verdict then: `REFUTED CHG-STALE CHG-LIST`; tree restored, `cmp`
identical.

## Re-verification

Dispatched at HEAD `52354a3` (delta `git diff 4caddb5..HEAD`). Mid-run, at 17:34:18, another process rebased the
branch onto `origin/main` `f13cf20` (reflog `rebase (start): checkout origin/main`); HEAD is now `a33b392`.
`git diff --quiet 52354a3 a33b392 -- src test .claude/specs scripts pyproject.toml` exits 0: the rebase brought only
toolchain files and the `release_tag`/`installed` fields of `config/toolchain.json` (its `files` map is unchanged).
Every mutant ran on the `52354a3` content before the rebase: each restore `cmp`-matched the pre-rebase LF backup,
and a rebase starts only on a clean tree.

Method: `cp -p` backup to `tmp/`, one Edit, `scripts/run_tests.py`, `cp -p` restore, `cmp` (identical every time),
`git status --porcelain` (empty). No `git stash`.

| Claim | Command or mutation | Result | Verdict |
|---|---|---|---|
| baseline `52354a3` | `run_tests.py src/payload/test/test_run_checks.py test/test_layout.py` | 67 passed, exit 0 | green |
| CHG-STALE (M5) | `report.unlink()` -> `pass` | 1 failed, 10 passed: `test_chg_stale_report_deleted_before_the_check_runs` line 215, `STALE-REPORT-SENTINEL` relayed before `--- PASS security/bandit (0.1s, exit 0)` | FAILED-TO-REFUTE |
| CHG-LIST (M6) | `LIST_MAX_ARGS = 12` | 1 failed, 10 passed: `test_chg_list_shows_the_bandit_command_whole` line 238, line ends `-f txt ... (+2 more)` | FAILED-TO-REFUTE |
| CHG-LIST boundary (M6b) | `LIST_MAX_ARGS = 13` (the argv has 14) | 1 failed, 10 passed: same test, line ends `-f txt -o ... (+1 more)` | FAILED-TO-REFUTE |
| shadow is load-bearing (T1) | the test's `bandit.py` write removed | 1 failed: line 215 `not stale.exists()`; output is the installed bandit's report (`No issues identified.`, `Text output written to file: reports/bandit.txt`, 0.6s) | FAILED-TO-REFUTE |
| layout exemption (L1) | `HISTORICAL` reverted to the `4caddb5` pattern | 1 failed, 55 passed: `test_every_framework_path_named_in_a_live_file_exists`, 3 tokens, all `src/payload/test/test_run_checks.py::test_...` ids in this spec's `evidence/red/wave-1.txt` and `evidence/verify/mutants-after-reopen.txt` | FAILED-TO-REFUTE |
| green at `a33b392` | same command as the baseline | 67 passed, exit 0 | green |

Stale-report test soundness. `importable("bandit")` runs `PY -c "...find_spec('bandit')..."` from the scratch
project; `-c` puts the cwd first on `sys.path`, so the probe finds the shadow (or the installed bandit) and returns
True either way, and `runnable` keeps `PY -m bandit ...`. `-m` also puts the cwd first, so the child runs the
scratch `bandit.py`: M5's run took 0.1s with no bandit log lines; T1's took 0.6s with bandit's `[main] INFO` lines.
No vacuous pass: the installed bandit writes a report (T1), so `not stale.exists()` holds only when the shadow ran
and `run_check` deleted the stale file; a `--- SKIP` path prints no `PASS_LINE`; a delete-after-relay mutant
relays the sentinel.

Layout exemption. The new pattern exempts 15 tracked files the old one did not. Five are
`.claude/specs/_workflow/phases/*.md`, listed in `config/toolchain.json` `files` and already skipped by
`f in installed`. The other ten are this spec's own records (change, decision log, prompts, qa_log, review,
evidence). No live file leaves the guard. L1 also shows the guard was red at `4caddb5`, which already tracked
`evidence/red/wave-1.txt`; the first verification ran only `test_run_checks.py`.

Step 1: `git branch -r --contains HEAD` is empty for `a33b392`, so no CI run exists. The whole-suite verdict is the
CI run on the SHA pushed after this verdict; no local full suite was run.

Steps 3 to 5 on the delta. Vacuity: neither new test has skip, xfail or deselection; both assert. Red: there is no
`evidence/red` capture for tests added after the implementation; M5, M6 and M6b falsify them with an
`AssertionError`, not a load error, and reproduce `evidence/verify/mutants-after-reopen.txt` (1 failed, 10 passed
each). Coverage: the delta changes no product line; the `test_layout.py` change is exercised by L1;
`report.unlink()` and `LIST_MAX_ARGS` are now covered.

Tree: the three mutated files were restored (`cmp` identical, `git status --porcelain` empty before this report was
written); `tmp/` is empty. The working files are CRLF because the other process's rebase checked them out under
`core.autocrlf=true`; their content is the index blobs (`git show HEAD:src/payload/test/test_run_checks.py` hashes
to the backup's `13b0eb95...`). This report is the only change.

VERIFIED
