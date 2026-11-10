# Refutation report: issue #5 (tier S, wave 1 = T1 + I1)

Worktree `issue-5`, branch `issue-5-kiro-post-activity-groups`. RT =
`venv\Scripts\python.exe scripts/run_tests.py -p no:cacheprovider test/test_post_activity_prompts.py`. Each mutant
changed the working tree only. Before any mutation, the files were copied byte-for-byte to `tmp/`. `git stash` was
not used. After every mutant the files were restored from that copy and checked with `cmp`. The dispatch allows only
this report, so each row quotes the summary of its run.

## First pass (HEAD 7a2270f, content-identical to dfe117f)

- Step 1: the branch was unpushed and had no CI run, so the whole suite was not graded.
- Step 2 (11 items): M0, with both prompts reverted to f285222, gave 4 failed: the four AC tests. Every other mutant
  failed on an `AssertionError`. M1 to M9c cover the AC-1 to AC-4 commands, phrases and forbidden strings, U1 to U6
  the UB-1 sites, and B1 and B2 the UB-2 step.
- Steps 3 and 4: FAILED-TO-REFUTE. There was no skip, xfail or deselect, and the red file holds 4 `AssertionError`s
  at the AC asserts.
- Step 5, COV-1: no test read the setup-kiro 8.23 `## Integration` line. X1, which reverted that line to
  "plus `run_checks.py`;", passed 11 of 11. Two probes also survived and served no criterion: X2 (a bare-name re-run
  in step 3) and X3 (the D1 rewording reverted).

The first pass ended REFUTED COV-1.

## Re-verification (HEAD bebfe62)

Delta (`git diff dfe117f..HEAD`):

- A new test, `test_kiro_823_integration_names_the_non_test_groups`, slices 8.23, then its `## Integration` list,
  then the `` - `post-activity.md` `` bullet. It requires "plus the non-test `run_checks.py` groups" and rejects
  "plus `run_checks.py`;".
- The green evidence was re-captured (68 items).
- No prompt changed. The sha256 values are setup-kiro `a70b62cb...` and setup-claude `814c46ee...`, the same as in
  the first pass.

Every row was run with RT (12 items).

| Id | Mutant | Claim | Result | Summary, failing assert |
|---|---|---|---|---|
| base | none | - | green | 12 passed |
| X1 | 8.23 bullet set to "plus `run_checks.py`; this rule is what governs"; whitespace-collapsed it equals the pre-I1 line (f285222) | COV-1 | FAILED-TO-REFUTE | 1 failed, 11 passed: "bullet lacks ['plus the non-test `run_checks.py` groups']" (required assert) |
| X4 | required phrase kept, "(in short, plus `run_checks.py`; the full suite)" added to the bullet | COV-1 | FAILED-TO-REFUTE | 1 failed, 11 passed: "bullet still says ['plus `run_checks.py`;']" (forbidden assert) |
| M0 | both prompts restored to merge-base f13cf20 | T1 red | FAILED-TO-REFUTE | 5 failed, 7 passed: the four AC tests and the new test (required assert) |

- **Step 1.** `git ls-remote --heads origin issue-5-kiro-post-activity-groups` printed nothing, so bebfe62 is
  unpushed and has no CI run. The whole suite is not graded here, and the CI run on the pushed SHA is still owed.
- **Step 3.** The module's only `pytest.mark` use is one `parametrize` decorator. The delta touches neither
  `pyproject.toml` nor a conftest. The new test asserts twice. FAILED-TO-REFUTE.
- **Step 4.** Every failure above is an `AssertionError` at the test's own asserts, with no import or collection
  error. The committed `evidence/red/wave-1.txt` predates the new test, and M0 regenerates its red. FAILED-TO-REFUTE.
- **Step 5.** COV-1 is cleared. The 8.23 line now has its own pin, and each of the pin's two asserts fails under a
  mutant: X1 the required assert, X4 the forbidden assert. The other changed lines and their tests are unchanged, so
  their first-pass grades stand, and M0 re-confirms the four AC reds. FAILED-TO-REFUTE.

**Tree.** After every mutant the prompts were restored and `cmp`-identical to the backup, with the sha256 values
above. `tmp/`, which held the backups, is deleted. Apart from this report, `git status --porcelain` is empty. The
ignored set is unchanged (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`). `git stash list` is empty and was never
used. After the last restore, RT plus `test/test_layout.py` gave 68 passed.

VERIFIED
