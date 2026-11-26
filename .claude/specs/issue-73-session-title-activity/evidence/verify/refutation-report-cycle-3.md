# Refutation report, cycle 3: issue #73 (tier S), head 2fcfeb7

Worktree `.claude/worktrees/issue-73`, branch `issue-73-session-title-activity`, HEAD
`2fcfeb796ab53072022ac6b7e77c57298f77a4ad`. Every local run is `python scripts/run_tests.py test/test_session_title.py`
(65 items; clean tree: `65 passed`). Captures are quoted inline: by the launcher's instruction this report is the only
file written.

## 1. Whole-suite verdict

- `list-runs --limit 5`: run `45844541424` (`ci`), `in_progress`. `get-run`: `event pull_request`, PR 74, `head_sha
  2fcfeb796ab53072022ac6b7e77c57298f77a4ad`, the worktree HEAD.
- `wait-run 45844541424 --timeout-seconds 540`: `{"status": "completed", "conclusion": "success"}`, exit 0.
- `get-pr-checks 74`: head 2fcfeb7, all 7 check runs `completed`/`success` (report, verify types/tests/lint/security,
  forge, forge-gitlab), `mergeable_state clean`; `combined_status pending` with 0 legacy statuses.

## 2. Wave mutant and red audit (regenerated)

M0: the 18 modified implementation files restored to ce950f4 in the working tree, the doc removed, the test at HEAD:
`29 failed, 36 passed`. Every failure is `AssertionError` (19 on asserted text, among them the three work commands on
`_rename_governed_by`; 10 on `_read`'s `is_file`). No collection or import error. Killed, red for the right reason.
`sha1sum -c` of all 19 files: `OK` after restoration.

## 3. Earlier survivors re-applied (one at a time, each restored)

| Id | AC | Mutation (as the earlier reports) | Result |
|---|---|---|---|
| M9 | AC-1 | doc "When." to "each time the subject changes — when the run claims or finishes an issue…", "never within a phase" kept | killed: `…states_the_form_and_how_to_rename` lacks `Rename each time the subject or the activity changes`; 1 failed |
| M10 | AC-5 | orchestrator "The activity": mapping replaced by "any one of the doc's words, as the session sees fit:" plus the nine activities | killed: `…renames_when_the_activity_changes` lacks all six phase pairs; 1 failed |
| M11 | AC-2 | doc "no rename follows the SESSION verdict" to "rename again after the SESSION verdict and before the archive"; "never ask about the title" to "ask the operator whether to retry the title" | killed: `…keeps_the_four_properties` lacks both; 1 failed |
| M12 | AC-3 | `work-issue.md` (straddling) "each time the set or the activity changes" to "each time the set changes and never for an activity" | killed: `…limits_the_rename_to_the_set[work-issue.md]`; 1 failed |
| N1 | AC-3 | `work-issue.md`: rename and APPEND triggers swapped (rename "each time the set changes", APPEND "each time the set or the activity changes") | killed: `…limits_the_rename_to_the_set[work-issue.md]` (`_rename_governed_by` False); 1 failed |
| N2 | AC-2 | doc "Without the tool": "— the session skips this rule;" deleted, Kiro citation kept | killed: `…keeps_the_four_properties` lacks `the session skips this rule`; 1 failed |
| N3 | AC-1 | doc "Memory" bullet: "Activities: `measuring`, `compiling`, `proving`, `committing`." deleted, example kept | killed: `…every_kind_of_session_a_form[/compile-memory]`; 1 failed |

## 4. New mutants (each removes or contradicts what the AC states; each restored)

| Id | AC | Mutation | Result |
|---|---|---|---|
| P1 | AC-1 | doc "Issue work" bullet: "Examples: `Issue 77 · CI`, `Auto-Work 12, 15 · 15 implementing`." deleted | **SURVIVED: 65 passed** |
| P2 | AC-3 | `spec-review.md` "Session title": "rename this session to `Spec <feature> · spec review` with `…set_session_title` (`session_id: "self"`) before the panel is dispatched. A declined rename is not a blocker." replaced by "this command keeps the title the session already has and never calls `mcp__ccd_session_mgmt__set_session_title`." | **SURVIVED: 65 passed** |
| P3 | AC-5 | orchestrator "The activity": "PREPARE, CLASSIFY and FIX while the spec is written `spec`; the spec's review loop `spec review`;" deleted, and "`spec` and `spec review` are the spec workflow's activities, not this section's." added | **SURVIVED: 65 passed** |

Why each survives (the test checks a token, not the relation the AC states):

- P1: AC-1 requires the issue-work bullet to carry "a ` · ` example". `test_the_doc_gives_every_kind_of_session_a_form`
  runs `any()` over ALL form bullets, so kind `/work-issue` is satisfied by the Close-out bullet, which names
  `/work-issue`, has `Activity: `closing out`` and the example `Issue 77 · closing out`.
  `test_the_doc_lists_the_issue_work_activities` checks that bullet's activities only, not its example.
- P2: AC-3 requires each entry point to "tell the session to rename with the tool".
  `test_every_main_session_command_renames_by_the_shared_rule` asserts only `TITLE_TOOL in body` and the pointer; a
  body that names the tool to forbid the call passes, and UB-3's allowlist check still holds. The same assertion
  guards the other seven non-work commands and both agents; only the three work commands have `_rename_governed_by`.
- P3: AC-5 requires the section to "map its phases to the doc's activities". `PHASE_MAPPING_PHRASES` pins six pairs;
  `spec`, `spec review` and `needs you` are checked only for presence in `ISSUE_WORK_ACTIVITIES`, so PREPARE, CLASSIFY,
  spec writing and the review loop can lose their activity while the words stay. The mutant also contradicts the
  doc, whose issue-work bullet lists `spec` and `spec review`.

No new mutant went to AC-2: M11 and N2 are killed, and the remaining AC-2 clauses are each pinned by a phrase that
only a negation of that phrase could keep.

## 5. Vacuity scan

- `_rename_governed_by`, work-command site: fires on N1 and M12 (`work-issue.md`) and on M0 (all three).
- `_rename_governed_by`, orchestrator site, V1: "each time the set or the activity below changes, and at no other
  time" to "each time the set below changes, and note each time the set or the activity below changes in the state
  file" (matches no `SET_ONLY_IN_ORCHESTRATOR` entry): killed, `the Session title section does not rename 'each time
  the set or the activity below changes'`; 1 failed. Restored.
- `ACTIVITIES_RE` in the every-form test: fires on N3. P1 shows that the `any()` around it does not bind a kind to
  its own bullet.
- New `DOC_PROPERTY_PHRASES` entries: `the session skips this rule` fires on N2; `A subagent ignores this rule`
  occurs once in the doc (Grep: the "Who." bullet), so its removal fails the test.
- Grep of the test file for `skip|xfail|mark.|deselect` and commented-out `def`/`assert`: only `@pytest.mark.parametrize`
  lines. No skip, xfail, deselection or commented-out test.

Result: FAILED-TO-REFUTE.

## Verdict table

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI suite on 2fcfeb7 | `wait-run 45844541424`, `get-pr-checks 74` | FAILED-TO-REFUTE | section 1 |
| Wave I1, red for the right reason | M0 | FAILED-TO-REFUTE | section 2 |
| AC-1 | M9, N3 killed; P1 survived | REFUTED | P1 |
| AC-2 | M11, N2 killed | FAILED-TO-REFUTE | section 3 |
| AC-3 | M12, N1 killed; P2 survived | REFUTED | P2 |
| AC-5 | M10, V1 killed; P3 survived | REFUTED | P3 |
| Vacuity of the new helpers | V1, Grep | FAILED-TO-REFUTE | section 5 |

AC-4, AC-6 and UB-1 to UB-3 are not re-graded: 2fcfeb7 does not change their tests or the files they read (cycle 1:
FAILED-TO-REFUTE).

## Tree restoration

- CRLF files restored with `git checkout --` (M10, M12, N1, P2, P3, V1) and `git restore --source=HEAD --worktree`
  (M0); `sha1sum` before and after identical for every file hashed.
- The LF doc restored with `git cat-file blob HEAD:clients/claude/docs/session-title.md >` (M9, M11, N2, N3, P1, M0):
  sha1 `935e049d…`, 4244 bytes, `i/lf w/lf`, as found.
- Final run: `65 passed`. `git status --porcelain` was empty before this report; HEAD 2fcfeb7; no stash created; the
  one scratch hash file of M0 (outside the worktree) was deleted.

REFUTED AC-1 AC-3 AC-5
