# Refutation report: issue #2, tier S, wave 1 (T1 + I1)

Subject: worktree `.claude/worktrees/issue-2`, branch `issue-2-anchor-gitignore-dirs`, HEAD 25685a6 (unpushed).
I regenerated every run graded here and did not rely on any earlier `evidence/` file.

RT = `venv/Scripts/python.exe scripts/run_tests.py -p no:cacheprovider test/test_setup_prompts_gitignore.py`
(18 items). Each mutant changed the working tree only. The three files were first copied byte-for-byte to `tmp/backup/`
(`git stash` was not used) and were restored by copying them back. After every restore, the sha256 of all three files
matched the backup and `git status --porcelain` was empty.

## Step 1: whole-suite verdict

Not graded here. `git rev-parse --verify origin/issue-2-anchor-gitignore-dirs` exits 1, so 25685a6 has not been
pushed and has no CI run. The dispatcher gives the whole-suite verdict to the CI run on the pushed SHA and forbids a
local suite run. The paired tests at HEAD, `RT test/test_layout.py`, gave `74 passed` both before the first mutation and
after the last restore.

## Step 2: kill the mutant

| # | Mutation | RT result | Caught by |
|---|---|---|---|
| M0 | both prompts restored to f285222 (wave reverted) | 8 failed, 10 passed | the same 8 ids as `evidence/red/wave-1.txt` |
| M1 | kiro `/lib/` -> `lib/` only | 2 failed | AC-3 (`lacks ['/lib/']`), probe `cdk/lib/stack.ts` |
| M2 | claude replace sentence deleted | 1 failed | AC-4 `[setup-claude]` |
| M3 | claude `/reports/` -> `reports/` only | 2 failed | AC-1 `[setup-claude]`, docs-reports probe `[setup-claude]` |
| M4 | `test_layout.py` `HISTORICAL` without `\.claude/specs/` | 1 failed, 55 passed | `test_every_framework_path_named_in_a_live_file_exists`, 19 hits in this spec dir |
| M5 | kiro `/wheels/` -> `wheels/` (no git probe) | failed | AC-3 whole-line check |
| M6 | claude reports comment deleted | failed | AC-1 comment assertion |
| M7 | kiro `# Root only ... cdk/lib/` comment deleted | failed | AC-3 comment assertion |
| M8 | kiro `reports/` added beside `/reports/` | failed | AC-2 slash-free assertion, docs-reports probe `[setup-kiro]` |
| M9 | kiro `build/` -> `/build/` | failed | UB-3 test, probe `frontend/build/x.js` |
| M13 | claude "add only those missing" reworded | failed | UB-2 `[setup-claude]` |
| M14 | claude `/reports/` deleted | failed | AC-1, probes junit + checks-lint `[setup-claude]` (UB-1) |
| M15 | kiro `/lib/`, `/reports/`, `tmp/` deleted, UB-2 phrase reworded | 8 failed | AC-2, AC-3, kiro probes junit/checks/lib/tmp, UB-3, UB-2 |
| M16 | kiro reports comment deleted | 1 failed | AC-2 comment assertion |
| M10 | claude replace sentence reversed: "without a leading slash (`/reports/` -> `reports/`, `/lib/` -> `lib/`)" | **18 passed** | none: SURVIVED |
| M11 | kiro replace sentence negated: "is never REPLACED by that entry (...), but kept beside it" | **18 passed** | none: SURVIVED |

Some mutants ran together because their tests do not overlap: M5 with M6; M7, M8, M9, M13 and M14 in one run; M10 with
M11. Every one of the 18 collected tests failed under at least one mutant.

M10 and M11 make the replace instruction point the wrong way. Under M10, an agent applying setup-claude to an existing
project would turn `/reports/` and `/lib/` back into the slash-free form, which is exactly the defect issue #2 reports.
Under M11, it would keep the slash-free line. In both cases `test_section_says_to_replace_a_slash_free_entry` stays
green. That test only checks that the tokens `REPLACED`, `/reports/` and `/lib/` appear somewhere in the prose outside
the block, and both mutants keep all three. It does not check which way the replacement goes
(`` `reports/` → `/reports/` ``) or that the sentence tells the agent to replace rather than keep. So the AC-4 test
passes without AC-4's behaviour: REFUTED.

How the comment criteria were graded: the AC-1 to AC-3 comment assertions were graded on whether the comment is present
(M6, M7 and M16 were all caught). The wording of a comment does not change what git ignores.

## Step 3: vacuity scan

I grepped the new module for skip, xfail, importorskip, deselect, commented-out asserts, `assert True` and bare `pass`.
The only matches are four `@pytest.mark.parametrize` decorators. There is no `test/conftest.py`. `pyproject.toml` sets
`addopts = "-ra --import-mode=importlib"` and `testpaths` includes `test`. Every test asserts. `ScratchRepository`
fails the test on any git exit code other than 0 or 1, and it points `core.excludesFile` at an empty file.
FAILED-TO-REFUTE.

## Step 4: red for the right reason

M0 regenerated the red run. It failed the same 8 ids as `evidence/red/wave-1.txt`. Each failure is an `AssertionError`
raised by a test assertion, for example `setup-claude: the PART 3 block has no /reports/ line` and
`git reports cdk/lib/stack.ts ignored, expected not-ignored`. There was no collection or import error. The 10 passing
tests are exactly the UB tests and probes that the spec says are green before I1. FAILED-TO-REFUTE.

## Step 5: coverage of the change

Each changed line and the mutants that exercise it:

- `/reports/` in both prompts: M3, M8, M14, M15.
- Both reports comments: M6, M16.
- The nine anchored kiro lines: M0, M1, M5.
- The kiro `Root only` comment: M7.
- `test_layout.py` `HISTORICAL`: M4.
- Both replace sentences: M0 and M2 catch their absence. Nothing catches a reversed direction or polarity (M10, M11).

Two edits change no behaviour: the reflowed claude line "In addition to ... ADD the Claude Code entries:" has the same
words, and the `test_layout.py` docstring is text only. A Grep of `prompts/`, `templates/` and `clients/` for a
slash-free `reports|lib|lib64|var|wheels|eggs|parts|sdist|downloads|develop-eggs/` line finds none.

## Independent git check (setup-kiro block)

I wrote the fenced block (setup-kiro.txt PART 3) as the `.gitignore` of a scratch `git init` repository under `tmp/`.
A `diff` against the prompt lines with CR stripped showed it identical. Then I ran
`git -c core.excludesFile=<empty> check-ignore --no-index -v --non-matching`, which exited 0:

- Ignored (matching pattern): `reports/junit.xml` and `reports/checks-lint.json` (`/reports/`), `lib/x.py` (`/lib/`),
  `frontend/build/x.js` (`build/`), `tmp/x` (`tmp/`), `wheels/x.whl` (`/wheels/`).
- Not ignored (`::`): `docs/reports/x.md`, `cdk/lib/stack.ts`, `cdk/lib/nested/deep.ts`, `src/lib/util.py`,
  `pkg/wheels/x.py`, `docs/reports/sub/y.md`.

## Claims

| Claim | Evidence | Result |
|---|---|---|
| AC-1 claude `/reports/` + comment | M3, M6, M14 | FAILED-TO-REFUTE |
| AC-2 kiro `/reports/` + comment | M8, M15, M16 | FAILED-TO-REFUTE |
| AC-3 kiro packaging anchors + comment | M0, M1, M5, M7 | FAILED-TO-REFUTE |
| AC-4 replace instruction in both sections | M10, M11 survive (18 passed) | REFUTED |
| AC-5 git verdicts, both blocks | M0, M1, M3, independent git check | FAILED-TO-REFUTE |
| UB-1 root `reports/` stays ignored | M14, M15 | FAILED-TO-REFUTE |
| UB-2 add-only-missing kept | M13, M15 | FAILED-TO-REFUTE |
| UB-3 generated dirs slash-free | M9, M15, independent git check | FAILED-TO-REFUTE |
| `.claude/specs/` exemption needed | M4 | FAILED-TO-REFUTE |
| Whole suite | not pushed, no CI run | not graded (CI on the pushed SHA) |

The mutant captures are quoted above rather than saved as `evidence/verify/mutant-wave-N.txt`, because the dispatcher
restricted my writes to this report.

## Tree

The tree is restored. sha256 after the last restore matches the start:

- `prompts/setup-claude.txt` 4695f73e...
- `prompts/setup-kiro.txt` 9e274aeb...
- `test/test_layout.py` 87f67034...

HEAD is still 25685a6. `git status --porcelain` is empty. `git stash list` is empty and was never touched. `tmp/` did
not exist at the start; I deleted it. The ignored set (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`) is the same as
at the start, and every run used `-p no:cacheprovider`. The only file added is this report.

REFUTED AC-4
