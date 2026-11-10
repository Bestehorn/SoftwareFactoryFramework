# Refutation report: issue #5 (tier S, wave 1 = T1 + I1)

Tree: worktree `issue-5`, branch `issue-5-kiro-post-activity-groups`, HEAD `7a2270f9eb0f`, unpushed. Runner for every
row: `venv\Scripts\python.exe scripts/run_tests.py test/test_post_activity_prompts.py` (11 items). The dispatch allowed
only this report in the tree, so each mutant's full output was kept in the worktree's tmp/ while grading and deleted
with it. The table quotes each run's pytest summary.

## 1. Whole-suite verdict

No CI run exists for 7a2270f. `git ls-remote --heads origin issue-5-kiro-post-activity-groups` printed nothing (exit
0), and the branch has no remote-tracking ref. The dispatch defers the whole-suite verdict to the CI run on the SHA
pushed after this report and forbids a local full run, so none was run. That CI run is still owed.

## 2. Mutants

| Id | Mutant | Claim | Result | Summary |
|---|---|---|---|---|
| M0 | both prompts restored to f285222 | AC-1..AC-4 | FAILED-TO-REFUTE | 4 failed, 7 passed (the four AC tests) |
| M1 | step 2 drops `--group security` | AC-1 | FAILED-TO-REFUTE | 1 failed: `..._step2_runs_the_non_test_groups` |
| M2 | plain `python scripts/run_checks.py` added to step 3 | AC-1 | FAILED-TO-REFUTE | 1 failed: "1 of 2 ... lack" |
| M3 | step 2 command made plain | AC-1 | FAILED-TO-REFUTE | 1 failed: same test |
| M6b | ` --group tests` appended to step 2 | AC-1, AC-2 | FAILED-TO-REFUTE | 2 failed |
| M4 | "It runs lint, type, security and test groups." added | AC-2 | FAILED-TO-REFUTE | 1 failed: "8.6 still says ['and test groups']" |
| M4b | old explanatory sentence restored | AC-2 | FAILED-TO-REFUTE | 1 failed: `..._never_runs_the_tests_group` |
| M5 | lead back to "Run every project check" | AC-2 | FAILED-TO-REFUTE | 1 failed: same test |
| M6 | "the `tests` group is CI's" changed to "runs too" | AC-2 | FAILED-TO-REFUTE | 1 failed: same test |
| M7 | "every project check" added to step 4 | AC-2 | FAILED-TO-REFUTE | 1 failed: "8.6 still says ['every project check']" |
| M8 | AC-3 sentence removed | AC-3 | FAILED-TO-REFUTE | 1 failed: `..._porting_paragraph_...` |
| M8b | AC-3 command drops `--group security` | AC-3 | FAILED-TO-REFUTE | 1 failed: same test |
| M8c | "non-test groups" changed to "check groups" | AC-3 | FAILED-TO-REFUTE | 1 failed: same test |
| M9 | AC-4 sentence removed | AC-4 | FAILED-TO-REFUTE | 1 failed: `..._self_check_flags_...` |
| M9b | AC-4 reason removed | AC-4 | FAILED-TO-REFUTE | 1 failed: same test |
| M9c | "(no `--group`)" removed | AC-4 | FAILED-TO-REFUTE | 1 failed: same test |
| U1-U6 | `--group` added at each UB-1 site (Rung 3, 9.1, `run-ci.md`, 3 rows) | UB-1 | FAILED-TO-REFUTE | each: 1 failed, that site's param id |
| B1 | step 1 command changed to bare `run_tests.py` | UB-2 | FAILED-TO-REFUTE | 1 failed: `..._step1_still_...` |
| B2 | step 1 "CI's job" sentence changed | UB-2 | FAILED-TO-REFUTE | 1 failed: same test |
| X1 | 8.23 `## Integration` reverted to "plus `run_checks.py`" | COV-1 | REFUTED | 11 passed |
| X2 | "re-run `run_checks.py` with no arguments" added to step 3 | (probe) | survived | 11 passed |
| X3 | "Read all of it (...)" reverted to "Apply Rule 3 ..." | (probe) | survived | 11 passed |

Every failing run failed on `AssertionError`. No capture held a Traceback, ImportError or SyntaxError. After each
mutant, both prompts were restored byte-for-byte (`cmp` against the backups; sha256 kiro `a70b62cb...`, claude
`814c46ee...`). After the last one, the paired module plus `test/test_layout.py` gave 67 passed.

## 3. Vacuity scan

FAILED-TO-REFUTE. The module has no skip, xfail, importorskip or deselect. There is no `test/conftest.py`, and the
pyproject `addopts` value (`-ra --import-mode=importlib`) deselects nothing. All six test functions (11 items) assert,
either directly or through `assert_stays_plain`, and the mutants above make each of them fail at least once.

## 4. Red for the right reason

FAILED-TO-REFUTE. `evidence/red/wave-1.txt` records `# tasks: T1` and 4 failed, 7 passed. All four failures are
`AssertionError`, at the AC-1..AC-4 asserts. The seven passes are the UB-1/UB-2 tests, which the spec requires to be
green before I1. Regenerated as M0: the same 4/7 split with the same four messages. The file is not valid UTF-8
because it holds cp1252 console bytes in a pytest repr. That is a capture-encoding issue, not a load error.

## 5. Coverage of the change

The changed prompt lines are: 8.6 step 2 (lead, command, text), 8.23 `## Integration`, the setup-claude porting
paragraph and self-check item 6. Every one of them except 8.23 sits inside a slice whose assertion outcome depends on
its content: the phrase pins, plus the section-wide forbidden-phrase scan for step 2.

- **COV-1: REFUTED.** The setup-kiro 8.23 `## Integration` line ("runs the affected tests plus the non-test
  `run_checks.py` groups") is never read by any test. `git grep` over `test/` and `src/` finds only
  `test/test_post_activity_prompts.py` reading prompt content, and none of its slices reaches 8.23. X1, a full
  reversion of the line, passes 11/11. I1 claims "Validates: AC-1, AC-2, AC-3, AC-4", but none of those tests touches
  this edit, and DL-002 records it as "no new criterion". One assertion pinning the line would clear this, e.g. the
  8.23 `## Integration` slice contains "plus the non-test `run_checks.py` groups" and not "plus `run_checks.py`;".
- X3 (no refutation): the D1 rewording has no pin of its own. It serves no criterion, and its line is inside the
  step-2 slice that the forbidden scan reads.
- X2 (no refutation): AC-2's head clause says "state or imply", and its operative clauses (the lead, two phrases and
  three forbidden strings) are each killed by M4-M7. A bare-name `run_checks.py` instruction falls outside those
  clauses, and AC-1's scope is `python scripts/run_checks.py`.

## Dispatch item 4: other sentences

I grepped both prompts for `run_checks`, `post-activity`, "test groups", "every project check", "--group tests",
"checklist runs" and "activity complete". No remaining sentence tells the post-activity checklist to run a plain
`run_checks.py` or the `tests` group. Every other match is one of:

- a UB-1 site;
- a CI-job description (setup-kiro Part 7 and setup-claude: `--group <lint|types|security|tests>`);
- a site the Residuals put out of scope (setup-kiro `docs/forLLMConsumption.md` common commands, and the "Checks"
  item of both verification checklists);
- a general description of `run_checks.py`.

One nearby wording: the setup-kiro 8.23 procedures bullet under "The baseline assumption" says the checklist
"mandates green tests", where the installed Claude companion says "green affected tests". It names neither the
command nor the `tests` group.

## Tree restored

Both prompts were restored byte-for-byte after every mutant. `git status --porcelain` was empty before this report
was written. The worktree `tmp/` (backups, a throwaway mutant runner, run outputs) has been deleted. The ignored set
is unchanged (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`).

HEAD moved during grading, but not because of anything this verifier did. At 17:34:22 the reflog shows the branch
rebased onto `origin/main` f13cf20, so HEAD is now `dfe117f`. That happened after my last mutant was restored and the
67-passed re-run, and `git stash list` is empty. `git diff 7a2270f dfe117f -- prompts test .claude/specs` is empty: the
graded content is identical. On dfe117f, the paired module plus `test_layout.py` gave 67 passed. The CI run is now owed
on dfe117f, or on whatever SHA gets pushed.

REFUTED COV-1
