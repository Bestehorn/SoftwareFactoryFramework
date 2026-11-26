# Refutation report, cycle 2: issue #73 (tier S), head 9dc2336

Worktree `.claude/worktrees/issue-73`, branch `issue-73-session-title-activity`, HEAD
`9dc233620689322f98893fe36b465bd115f03656`. Every local run is `python scripts/run_tests.py test/test_session_title.py`
(65 items). Captures are quoted inline: by the launcher's instruction this report is the only file written.

## 1. Whole-suite verdict

- `list-runs` gives run `45842892204` (`ci`). `get-run`: `event pull_request`, PR 74, `head_sha
  9dc233620689322f98893fe36b465bd115f03656`, the worktree HEAD.
- `wait-run 45842892204 --timeout-seconds 540`: `{"status": "completed", "conclusion": "success"}`, exit 0.
- `get-pr-checks 74`: head 9dc2336, all 7 check runs `completed`/`success` (report, verify security/types/tests/lint,
  forge, forge-gitlab), `mergeable_state clean`. `combined_status pending` because there are 0 legacy statuses.

## 2. Scope of 9dc2336

`git show --stat 9dc2336`: `test/test_session_title.py` plus spec artefacts only (change.md, decisions/decision-log.md,
evidence/green/wave-1-cycle-2.txt, evidence/verify/refutation-report.md). No product file. The test gains
`PHASE_MAPPING_PHRASES`, `ORCHESTRATOR_TRIGGER`, a positive `COMMAND_TRIGGER` assert, one `DOC_FORM_PHRASES` entry and
three `DOC_PROPERTY_PHRASES` entries.

## 3. Wave mutant and red audit (regenerated)

M0: the 18 modified implementation files restored to ce950f4 in the working tree, the doc removed, the test at HEAD:
`29 failed, 36 passed`, the same 29 ids as `evidence/red/wave-1.txt`. Every failure is `AssertionError`: 19 on asserted
text (the three work commands now on `COMMAND_TRIGGER`) and 10 on `_read`'s `is_file`. No collection or import error.
Killed, and red for the right reason.

## 4. Cycle-1 survivors re-applied (one at a time, each restored)

| Id | AC | Mutation (as cycle 1) | Result |
|---|---|---|---|
| M9 | AC-1 | doc "When." to "each time the subject changes, when the run claims or finishes an issue…", "never within a phase" kept | killed: `…states_the_form_and_how_to_rename` lacks `Rename each time the subject or the activity changes`; 1 failed, 64 passed |
| M10 | AC-5 | orchestrator "The activity": mapping replaced by "any one of the doc's words, as the session sees fit:" plus the nine activities | killed: `…renames_when_the_activity_changes` lacks all six phase pairs; 1 failed |
| M11 | AC-2 | doc "no rename follows the SESSION verdict" to "rename again after the SESSION verdict and before the archive"; "never ask about the title" to "ask the operator whether to retry the title" | killed: `…keeps_the_four_properties` lacks both phrases; 1 failed |
| M12 | AC-3 | `work-issue.md` "each time the set or the activity changes" (straddling) to "each time the set changes and never for an activity" | killed: `…limits_the_rename_to_the_set[work-issue.md]` lacks `COMMAND_TRIGGER`; 1 failed |

## 5. New mutants (guarded clause removed, asserted words kept)

| Id | AC | Mutation | Result |
|---|---|---|---|
| N1 | AC-3 | `work-issue.md` Step 1, rename and append triggers swapped: "Rename with … (`session_id: "self"`) each time the set changes, APPEND the set as `SESSION_ISSUES: X Y` each time the set or the activity changes" | **SURVIVED: 65 passed** |
| N2 | AC-2 | doc "Without the tool": "— the session skips this rule;" deleted, the Kiro citation kept | **SURVIVED: 65 passed** |
| N3 | AC-1 | doc "Memory" bullet: "Activities: `measuring`, `compiling`, `proving`, `committing`." deleted, example `Memory · compiling` kept | **SURVIVED: 65 passed** |

The survivors are the same class as in cycle 1: the tests check that a phrase is present, not the clause it should
guard.

- N1: `COMMAND_TRIGGER` asserts that the phrase occurs somewhere in the body, not that it governs the rename.
  `SET_ONLY_IN_COMMANDS` denylists only the two pre-change strings, and "Rename … each time the set changes" matches
  neither. AC-3: "the three work commands SHALL NOT limit the rename to a change of the set".
- N2: AC-2's fourth property ("a session without the tool (the CLI, Kiro) skips the rule") is pinned by the single word
  `Kiro`, and the bullet's citation keeps that word.
- N3: AC-1's "with its activities" is asserted only for the issue-work bullet
  (`test_the_doc_lists_the_issue_work_activities`). The other six bullets are checked only for a kind name and a ` · `
  example. change.md § Tests (AC-1) says exactly that, so the gap is between § Tests and the AC text.

No new mutant went to AC-5: the three were spent on AC-1, AC-2 and AC-3. M10 is killed.

## 6. Vacuity scan of the new assertions

- `PHASE_MAPPING_PHRASES`: M10 reports all six phrases missing, so each occurs only in the mapping. `assert not
  missing_pairs` runs over a non-empty tuple.
- `COMMAND_TRIGGER`: fires for each of the three commands (M0: all three; M12: `work-issue.md`).
- `ORCHESTRATOR_TRIGGER`: occurs once in the section (Grep: the "Session title" intro). It is a positive `in` assert on
  the collapsed section. It was not mutated alone in this cycle.
- The new `DOC_FORM_PHRASES` and `DOC_PROPERTY_PHRASES` entries fire (M9, M11). `comes before the close-out` is stricter
  than the earlier `before the close-out`.
- No skip, xfail, deselection or commented-out test; the only marks are `parametrize`. `pyproject.toml` has
  `addopts = "-ra --import-mode=importlib"` and `testpaths` includes `test`. The only conftests under `test/` are
  `test/forge/` and `test/forge_gitlab/`.

Result: FAILED-TO-REFUTE.

## Verdict table

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI suite on 9dc2336 | `wait-run 45842892204`, `get-pr-checks 74` | FAILED-TO-REFUTE | section 1 |
| Wave I1, red for the right reason | M0 | FAILED-TO-REFUTE | section 3 |
| AC-1 | M9 killed, N3 survived | REFUTED | N3 |
| AC-2 | M11 killed, N2 survived | REFUTED | N2 |
| AC-3 | M12 killed, N1 survived | REFUTED | N1 |
| AC-5 | M10 killed | FAILED-TO-REFUTE | M10 |
| Vacuity of the new assertions | test file scan | FAILED-TO-REFUTE | section 6 |

AC-4, AC-6 and UB-1 to UB-3 are not re-graded: 9dc2336 does not change their tests or the files they read (cycle 1:
FAILED-TO-REFUTE).

## Tree restoration

- The CRLF files were restored with `git checkout --` (M10, M12, N1) and `git restore --source=HEAD --worktree` (M0).
- The LF doc was restored with `git cat-file blob HEAD:clients/claude/docs/session-title.md >` (M9, M11, N2, N3, M0):
  blob 58982315d763, 4244 bytes, `w/lf`, as found.
- M0: the raw `sha1sum` of all 19 files is identical before and after.
- Final run: `65 passed`.
- `git status --porcelain` shows `?? .claude/specs/issue-73-session-title-activity/evidence/REPORT.md`, which appeared
  during this run (this verifier did not create it and left it untouched), plus this report. HEAD is 9dc2336, and no
  stash was created.

REFUTED AC-1 AC-2 AC-3
