# Refutation report: issue #2, tier S, wave 1 (T1 + I1)

Worktree `.claude/worktrees/issue-2`, branch `issue-2-anchor-gitignore-dirs`. RT =
`venv/Scripts/python.exe scripts/run_tests.py -p no:cacheprovider test/test_setup_prompts_gitignore.py` (18 items).
Each mutant changed the working tree only. Before any mutation, the files were copied byte-for-byte to `tmp/`.
`git stash` was not used. After every mutant the files were restored from that copy and checked with `cmp`. The
dispatch allows only this report, so each row quotes the summary of its run.

## First pass (HEAD 25685a6)

- Step 1: the branch was unpushed and had no CI run, so the whole suite was not graded. The paired tests plus
  `test/test_layout.py` gave 74 passed.
- Step 2: M0, with the wave reverted to f285222, gave 8 failed, the same ids as `evidence/red/wave-1.txt`. M1 to M9
  and M13 to M16 each failed. They cover the anchors, the comments, `reports/` beside `/reports/`, an anchored
  `build/`, the UB-2 phrase and `HISTORICAL`. Two mutants passed 18 of 18: M10, with the setup-claude replace sentence
  reversed, and M11, with the setup-kiro sentence negated. The AC-4 test checked only that the tokens `REPLACED`,
  `/reports/` and `/lib/` appear.
- Steps 3 to 5 outside the replace sentences: FAILED-TO-REFUTE. There was no vacuity, every red was an
  `AssertionError`, and every other changed line was exercised. An independent `git check-ignore` of the setup-kiro
  block agreed with AC-5 and UB-3.

The first pass ended REFUTED AC-4.

## Re-verification (HEAD 4141e11)

Delta (`git diff c39d672..HEAD`):

- `test_section_says_to_replace_a_slash_free_entry` now reads the prose outside the block with whitespace collapsed.
  It requires "is REPLACED by", "not kept beside it" and the arrows `` `reports/` → `/reports/` `` and
  `` `lib/` → `/lib/` ``. It rejects both reversed arrows, "never REPLACED" and "without a leading slash".
- The `change.md` test-plan line for AC-4 restates this. The green evidence was re-captured.
- No prompt changed. The sha256 values are setup-claude `4695f73e...` and setup-kiro `9e274aeb...`, the same as in
  the first pass.

Every row was run with RT. The failing-assert column gives the assert that failed: required is line 223, forbidden is
line 226.

| Id | Mutant | Claim | Result | Summary, failing assert |
|---|---|---|---|---|
| base | none | - | green | 18 passed |
| M10+M11 | claude: "without a leading slash (`/reports/` → `reports/`, `/lib/` → `lib/`)"; kiro: "is never REPLACED by that entry (...), but kept beside it" | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed: claude lacks both forward arrows; kiro lacks "is REPLACED by" and "not kept beside it" (required) |
| R2 | sentence intact; claude adds `/reports/` → `reports/`, kiro adds "never REPLACED" | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, forbidden, each naming its added phrase |
| R3 | claude adds "never REPLACED", kiro adds `/lib/` → `lib/` | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, forbidden |
| R4 | claude adds `/lib/` → `lib/`, kiro adds "without a leading slash" | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, forbidden |
| R5 | claude adds "without a leading slash", kiro adds `/reports/` → `reports/` | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, forbidden |
| R6 | claude drops ", not kept beside it"; kiro "may be REPLACED by" | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, required |
| R7 | claude "may be REPLACED by"; kiro drops `` `lib/` → `/lib/` `` | AC-4 | FAILED-TO-REFUTE | 2 failed, 16 passed, required |
| M0 | both prompts restored to merge-base f13cf20 | T1 red | FAILED-TO-REFUTE | 8 failed, 10 passed, the same 8 ids; AC-4 lacks all four required phrases |
| P1 | sentence intact; claude adds "undo it (`/lib/` -> `lib/`)" (ASCII arrow), kiro adds "Turn `/reports/` back into `reports/`" | probe | survived | 18 passed |

- **Step 1.** `git ls-remote --heads origin issue-2-anchor-gitignore-dirs` printed nothing, so 4141e11 is unpushed
  and has no CI run. The whole suite is not graded here, and the CI run on the pushed SHA is still owed.
- **Step 3.** The module's only `pytest.mark` uses are four `parametrize` decorators. The delta touches neither
  `pyproject.toml` nor a conftest. FAILED-TO-REFUTE.
- **Step 4.** Every failure above is an `AssertionError` at the test's own asserts, with no import or collection error.
  The committed `evidence/red/wave-1.txt` predates the strengthened test, and M0 regenerates its red.
  FAILED-TO-REFUTE.
- **Step 5.** Every RT runs the delta's lines: `REPLACED_ENTRIES` and the phrase constants, `flat_prose`,
  `_replacement` and both asserts. Each assert fails under at least one mutant: the required assert under M10, M11, R6
  and R7, the forbidden assert under R2 to R5. FAILED-TO-REFUTE.
- **P1 is not a refutation.** The forward instruction stays whole under P1, so the behaviour AC-4 requires is still
  present ("SHALL instruct the project to replace that line with the anchored form"), and the pass is correct. The
  forbidden scan is a deny-list of exact strings and goes beyond the criterion. Every single-point mutation that
  removes or inverts the instruction itself fails: M10, M11, R6, R7 and M0.
- **Other criteria.** The tests and prompt text for AC-1 to AC-3, AC-5 and UB-1 to UB-3 are unchanged, so their
  first-pass grades stand. M0 re-confirms their red ids.

**Tree.** After every mutant both prompts were restored and `cmp`-identical to the backup, with the sha256 values
above. `tmp/`, which held the backups and a throwaway mutant runner, is deleted. Apart from this report,
`git status --porcelain` is empty. The ignored set is unchanged (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`).
`git stash list` is empty and was never used. After the last restore, RT plus `test/test_layout.py` gave 74 passed.

VERIFIED
