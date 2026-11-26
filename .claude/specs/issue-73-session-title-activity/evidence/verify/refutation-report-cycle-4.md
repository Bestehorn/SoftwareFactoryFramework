# Refutation report, cycle 4: issue #73 (tier S), head e60420a

Worktree `.claude/worktrees/issue-73`, branch `issue-73-session-title-activity`, HEAD
`e60420a45f975fb53a2c86d6041f40e18404da1c`; e60420a changes only `test/test_session_title.py` and spec artefacts
(`git diff 2fcfeb7 e60420a --stat`). Every local run is `python scripts/run_tests.py test/test_session_title.py`
(clean tree: `65 passed`). Captures are quoted inline: this report is the only file written.

## 1. Whole-suite verdict

- `get-run 45846642210` (main checkout): workflow `ci`, `event pull_request`, PR 74, `status completed`,
  `conclusion success`, `head_sha e60420a45f975fb53a2c86d6041f40e18404da1c`, the worktree HEAD.
- `get-pr-checks 74`: head e60420a, all 7 check runs `completed`/`success` (report, verify types/tests/lint/security,
  forge, forge-gitlab); `combined_status pending` with 0 legacy statuses, `mergeable_state unknown`.

## 2. Wave mutant and red audit (regenerated against the e60420a test)

- M0: the 18 modified implementation files restored to ce950f4, the doc removed: `29 failed, 36 passed`. Every
  failure is `AssertionError` (rename instruction, pointer, trigger, forms, `_read`'s `is_file`, Part 8.1, copy
  line). No collection or import error. Killed. All 19 sha1 values identical before and after restoration.
- `evidence/red/wave-1.txt`: `29 failed, 36 passed`; 29 `E   …Error:` lines, all 29 `AssertionError`. Red for the
  right reason.

## 3. Earlier mutants re-applied (one at a time, each restored)

| Id | AC | Mutation | Result |
|---|---|---|---|
| P1 | AC-1 | doc Issue-work bullet: "Examples: `Issue 77 · CI`, `Auto-Work 12, 15 · 15 implementing`." deleted | killed: `…every_kind_of_session_a_form[/work-issue]`, "bullet has no `<subject> · <activity>` example"; 1 failed |
| P2 | AC-3 | `spec-review.md`: rename sentence replaced by "this command keeps the title the session already has and never calls `…set_session_title`." | killed: `…command_renames_by_the_shared_rule[spec-review.md]`; 1 failed |
| P3 | AC-5 | orchestrator: "PREPARE, CLASSIFY and FIX while the spec is written `spec`; the spec's review loop `spec review`;" deleted, "`spec` and `spec review` are the spec workflow's activities, not this section's." added | killed: lacks pairs 2 and 3; 1 failed |
| N1 | AC-3 | `work-issue.md`: rename and APPEND triggers swapped | killed: `…limits_the_rename_to_the_set[work-issue.md]`; 1 failed |
| M10 | AC-5 | orchestrator "The activity": "any one of the doc's words, as the session sees fit:" plus the nine words | killed: lacks all nine pairs; 1 failed |

## 4. New mutants (each removes or contradicts what the AC states; each restored)

| Id | AC | Exact edit | Result |
|---|---|---|---|
| R1 | AC-6 | `prompts/setup-claude.txt` Part 8.1 fleet line "- Desktop app: the main session's title is `<subject> · <activity>`, renamed when either changes (`.claude/docs/session-title.md`)." to "- Desktop app: the main session keeps its own title (`.claude/docs/session-title.md`)." | **SURVIVED: 65 passed** |
| R2 | AC-3 | `spec-review.md` "Session title": "rename this session to `Spec <feature> · spec review` with `mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`) before the panel is dispatched. A declined rename is not a blocker." to "this command only reports, so do NOT rename this session with `mcp__ccd_session_mgmt__set_session_title`; the title it already has stays." | **SURVIVED: 65 passed** |
| R3 | AC-2 | doc "A refused rename…" bullet: "A decline or an error changes nothing else" to "A decline changes nothing else" | **SURVIVED: 65 passed** |
| R4 | AC-5 | orchestrator "The activity": deleted "LOAD_ISSUES and ", "PREPARE, ", "DOCUMENT, and " and "the direct merge, its trunk run and "; the nine pinned pairs kept verbatim | **SURVIVED: 65 passed** |

Why each survives:

- R1: AC-6 requires the fleet line to name "the form and `.claude/docs/session-title.md`".
  `test_the_claude_md_template_names_the_rule` asserts only `DOC_POINTER` in the section; the form, the one thing an
  interactive session learns from that line (DL-002), is unchecked.
- R2: `RENAME_INSTRUCTION_RE`'s guards are the lowercase literals `(?<!never )(?<!not )`, compiled without
  `re.IGNORECASE`. "do NOT rename … with the tool" matches as an instruction. The capitalised form is the file's own
  style: `spec-review.md` already says "Do NOT revise the spec".
- R3: AC-2 says "a declined or failed rename is not a blocker". The only asserted phrase, `not a blocker`, sits in
  the bold head "A refused rename is not a blocker", which covers refusals; "or an error" is the doc's sole
  statement of the failed case and no phrase pins it. This refutes cycle 3's statement that every remaining AC-2
  clause is pinned.
- R4: AC-5 requires the section to "map its phases". `PHASE_MAPPING_PHRASES` pins one pair per activity, not per
  phase: LOAD_ISSUES, PREPARE and DOCUMENT (outer-loop phases) and the direct merge with its trunk run lose their
  activity. Under `merge: direct` + `verification: watcher` the loop runs `merge → HAND_OFF` without MERGE_CLEANUP,
  so after R4 that path never names `merging`.

No new mutant went to AC-1: the cap of four was spent on AC-2, AC-3, AC-5 and AC-6.

## 5. Vacuity scan

- `RENAME_INSTRUCTION_RE`: fires on P2 (no rename verb) and on M0 (nine entry points report "does not tell the
  session to rename itself"). Its negation guard is case-sensitive (R2). Reading the pattern, sentence-initial
  "Never rename" and "don't rename" also pass the guard; not run.
- `DOC_KINDS` binding: `len(bullets) == 1` per bold label; P1 now fails on its own bullet, so the cycle-3 `any()`
  leak is closed. Each `kind` is carried by its own bullet on the clean tree. `ACTIVITIES_RE` ends after one
  backticked token, so a bullet keeping only its first activity satisfies it; no mutant was spent on this.
- The new pairs: P3 fires pairs 2 and 3; M10 fires all nine, `needs you` included. R4 shows what they leave open.
- Grep of the test for `skip|xfail|mark.|deselect` and commented-out `def`/`assert`: only `@pytest.mark.parametrize`.
  No skip, xfail, deselection or commented-out test.

## Verdict table

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI suite on e60420a | `get-run 45846642210`, `get-pr-checks 74` | FAILED-TO-REFUTE | section 1 |
| Wave I1, red for the right reason | M0, red-capture Grep | FAILED-TO-REFUTE | section 2 |
| AC-1 | P1 killed | FAILED-TO-REFUTE | section 3 |
| AC-2 | R3 survived | REFUTED | R3 |
| AC-3 | P2, N1 killed; R2 survived | REFUTED | R2 |
| AC-5 | P3, M10 killed; R4 survived | REFUTED | R4 |
| AC-6 | R1 survived | REFUTED | R1 |
| Vacuity of the new helpers | P1, P2, P3, M10, R2, Grep | FAILED-TO-REFUTE (non-vacuous; R2 is graded under AC-3) | section 5 |

AC-4 and UB-1 to UB-3 are not re-graded: e60420a does not change their tests or the files they read (cycle 1:
FAILED-TO-REFUTE).

## Tree restoration

- CRLF files restored with `git checkout --` (P2, P3, N1, M10, R1, R2, R4) and `git restore --source=HEAD
  --worktree` (M0); the LF doc with `git cat-file blob HEAD:clients/claude/docs/session-title.md >` (P1, R3, M0):
  sha1 `935e049d…`, `i/lf w/lf`, as found. Every file's sha1 after restoration equals its value before
  (`4279b96c…` orchestrator, `64e49ce8…` spec-review, `8f66d175…` work-issue, `03d84921…` setup-claude, all 19 of M0).
- `git status --porcelain` was empty after every restoration and before this report; HEAD e60420a; no stash, no
  scratch file.

REFUTED AC-2 AC-3 AC-5 AC-6
