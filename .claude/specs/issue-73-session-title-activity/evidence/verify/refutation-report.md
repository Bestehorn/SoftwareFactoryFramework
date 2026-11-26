# Refutation report: issue #73 (tier S), head 75ce112

Worktree `.claude/worktrees/issue-73`, branch `issue-73-session-title-activity`. Every local run is
`python scripts/run_tests.py test/test_session_title.py` (65 items). Captures are quoted inline: by the
launcher's instruction this report is the only file written.

## 1. Whole-suite verdict

- `wait-run 45839898768`: `{"status": "completed", "conclusion": "success"}`, exit 0.
- `get-run`: `head_sha 75ce1123bf5f60da3d41248aeeba4c34dfc7d44c`, the worktree HEAD.
- `get-pr-checks 74`: head 75ce112, all 7 check runs `success` (report, verify tests/types/security/lint,
  forge, forge-gitlab). `combined_status pending` because there are 0 legacy statuses.

## 2. Red for the right reason (regenerated, not read from evidence)

`git restore --source=ce950f4 -- clients docs prompts` (the test kept at HEAD) gives `29 failed, 36 passed`, the
same 29 ids as `evidence/red/wave-1.txt`. All 29 are `AssertionError`:

- 19 fail on the asserted text.
- 10 fail on `_read`'s `assert path.is_file()`, because the doc is absent at ce950f4.

There is no import or collection error. These passed in the red run: UB-1
(`test_the_title_rule_names_every_mode…`), UB-2 (`…work_entry_point_keeps…` 3/3), UB-3
(`…a_command_calls_is_allowlisted` 11/11, `…orchestrator_may_rename…`) and the AC-4 every-agent guard (20/20).

## 3. Mutants (each restored before the next)

| Id | Claim | Mutation | Result |
|---|---|---|---|
| M0 | wave I1 | revert I1 (section 2) | killed: 29 failed |
| M1 | AC-5 | orchestrator "each time the set or the activity below changes" → "each time the set below changes" (straddles a line break) | killed: `…renames_when_the_activity_changes`, kept phrase |
| M2 | AC-4 | `spec-review.md` `allowed-tools` without the tool | killed: 2 failed |
| M3 | AC-6 | Part 8.1 fleet line deleted | killed: `…claude_md_template_names_the_rule` |
| M3b | AC-6 | `cp clients/claude/docs/session-title.md` line deleted | killed: `…setup_prompt_installs_the_doc` |
| M4 | AC-1 | "The forms" Supervisor bullet deleted | killed: `…every_kind…[/supervise]` |
| M5 | AC-2 | doc "Who." bullet deleted | killed: `…four_properties` `['never delegate']` |
| M6 | AC-3 | `supervise.md` doc pointer deleted | killed: `…main_session_command…[supervise.md]` |
| M7 | AC-3 | `work-issue.md` "only when the⏎set changes" (straddling) | killed: `…no_work_entry_point…[work-issue.md]` |
| M8 | AC-4 | spec-conductor `tools` without the tool | killed: 2 failed |
| M9 | AC-1 | doc "When.": "each time the subject or the activity changes — at each phase transition…" → "each time the subject changes — when the run claims or finishes an issue…", "never within a phase" kept | **SURVIVED: 65 passed** |
| M10 | AC-5 | orchestrator "The activity": the phase→activity mapping replaced by "any one of the doc's words, as the session sees fit:" plus the nine activities | **SURVIVED: 65 passed** |
| M11 | AC-2 | doc "no rename follows the SESSION verdict…" → "rename again after the SESSION verdict and before the archive"; "never ask about the title" → "ask the operator whether to retry the title" | **SURVIVED: 65 passed** |
| M12 | AC-3 | `work-issue.md` "each time the set or the activity changes" → "each time the set changes and never for an activity" | **SURVIVED: 65 passed** |

All four survivors have one cause: the ACs are pinned by fixed phrase lists that leave the guarded clause out.

- `DOC_FORM_PHRASES` holds "never within a phase" and nothing for "a change of subject or activity" (AC-1's
  trigger, the behaviour the issue exists for).
- `DOC_PROPERTY_PHRASES` holds "before the close-out" and "not a blocker". It has nothing for "none follows the
  SESSION verdict" or "never a question" (AC-2).
- `SET_ONLY_IN_COMMANDS` is a denylist of the two exact pre-change strings. Any other set-only wording passes
  (AC-3).
- `test_the_orchestrator_renames_when_the_activity_changes` checks that the activity words are present, not that
  any phase is mapped to them (AC-5).

Each test does what change.md § Tests states; the gap is between § Tests and the AC text.

## 4. Vacuity scan

- No skip, xfail, deselection or commented-out test. The only marks are `parametrize`. `testpaths` includes
  `test`, and no conftest governs this file.
- Every multi-word phrase check runs on collapsed whitespace: the doc, the orchestrator section, the
  work-command bodies and the fleet section. `_form_bullets` joins wrapped lines. M1 and M7 prove that a phrase
  straddling a line break is caught.
- The `any()` in `…every_kind_of_session_a_form` runs over the 7 form bullets and fails on an empty list (M4).
- `if not named: return` (UB-3, unchanged) never fires now, because all 11 commands name a desktop tool.
- The every-agent guard passes trivially for the 18 agents that name no desktop tool. It is not vacuous for the
  2 that do (M8).

Result: FAILED-TO-REFUTE.

## 5. Coverage of the change

These changed lines have no assertion:

- the `clients/claude/README.md` row
- `docs/design/agents/issue-work-orchestrator.md`
- `docs/forLLMConsumption.md`
- `prompts/setup-claude.txt` Part 13.1d and the final-report docs line
- the `clients/common/docs/delivery.md` row (DL-003)

change.md § Files ties none of them to an AC, so none is refuted. Lines that do serve an AC but are pinned by no
assertion: the doc's "When." trigger, its "The end." and refused-rename clauses, the orchestrator's phase
mapping, and the work commands' trigger sentence (M9 to M12).

## 6. Ask conformance (read only)

- All 13 entry points of AC-3 name `.claude/docs/session-title.md` in their body and carry the tool: in
  `allowed-tools` for the 11 commands, in `tools` for the 2 agents (Grep, and the green run).
- Nothing contradicts "The end":
  - `close-session.md` renames at its first step only, "renames nothing after the SESSION verdict", and keeps
    `<subject> — done` when it runs as the last step of `/work-issue` or the orchestrator.
  - `work-issue.md` Step 8 sets `Issue X — done` "before the close-out, never after the SESSION verdict".
  - The orchestrator's DONE marks the title done before the verdict.
  - `compile-memory`, `supervise` and the `spec-*` commands rename nowhere after a SESSION verdict.
  - `continue-work` re-applies the title once, before it resumes.

Result: FAILED-TO-REFUTE.

## Verdict table

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI suite on 75ce112 | `wait-run 45839898768`, `get-pr-checks 74` | FAILED-TO-REFUTE | section 1 |
| Red for the right reason | revert I1, run test | FAILED-TO-REFUTE | section 2 |
| AC-1 | M4 killed, M9 survived | REFUTED | M9 |
| AC-2 | M5 killed, M11 survived | REFUTED | M11 |
| AC-3 | M6 and M7 killed, M12 survived | REFUTED | M12 |
| AC-4 | M2, M8 | FAILED-TO-REFUTE | M2, M8 |
| AC-5 | M1 killed, M10 survived | REFUTED | M10 |
| AC-6 | M3, M3b | FAILED-TO-REFUTE | M3, M3b |
| UB-1 to UB-3 | red run, green run | FAILED-TO-REFUTE | section 2 |
| Vacuity | test file scan | FAILED-TO-REFUTE | section 4 |
| Ask conformance | Grep and read | FAILED-TO-REFUTE | section 6 |

## Tree restoration

Every mutation was restored. The CRLF files went back with `git checkout -- <file>`. The doc, which is LF on disk,
went back with `git cat-file blob HEAD:<doc> > <doc>`: 4244 bytes, `w/lf`, as found. Once, after M0, a
`git restore` rewrote the doc as CRLF and left a size-only `M`. That was corrected the same way before M1.

Final state: `65 passed`, `git status --porcelain` empty before this report, HEAD
75ce1123bf5f60da3d41248aeeba4c34dfc7d44c, no stash. This report is the only new file.

REFUTED AC-1 AC-2 AC-3 AC-5
