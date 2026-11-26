# spec-review-agent — iteration 02 (tier S, combined pass, delta)

Reviewed the fix sites only: `change.md` AC-2, AC-3, § Files, § Tests (AC-1, AC-3, AC-5, AC-6), § Tasks T1; the rule
draft (`tmp/session-title-draft/session-title.md`) "When", "The end", Issue work, Close-out, Spec workflow. Checked
against the worktree's orchestrator "Session title" section, `work-issue.md`, `auto-work.md`, `issues-work.md`,
spec-conductor's phase line, `clients/claude/README.md` and `test/test_session_title.py`. The B2/B3/C1-C4 fixes
hold: "The end" matches `/work-issue` ("before the close-out, never after the SESSION verdict") and the
orchestrator's Timing bullet; the spec-workflow mapping covers SETUP, CHANGE_REVIEW, DESIGN_REVIEW_LOOP,
TASKS_REVIEW_LOOP and DONE of spec-conductor's phase line; the AC-3 negative phrases each sit on one line of today's
`work-issue.md`, `auto-work.md` and `issues-work.md`, so those assertions are red today and can fail.

### B1 — Two of the new phrase assertions straddle a line break
Severity: B
Location: change.md § Tests (preamble, AC-5 line, AC-1 line)
Defect: § Tests matches phrases against the file text as read, and the existing helper `_split_front_matter` only
normalises `\r\n`. The orchestrator's sentence is wrapped as "each time the set" / "below changes, and at no other
time", so the AC-5 negative `each time the set below changes, and at no other time` is absent from today's text:
the check passes before I1 and after it, whatever I1 does to the trigger. The draft doc likewise wraps "never" /
"within a phase", so the AC-1 assertion `never within a phase` is red against the artefact I1 installs.
Material-because: AC-5 ("SHALL rename when the set OR the activity changes") is not tested: its only trigger
check cannot fail, so the orchestrator's set-only trigger can survive I1 with T1 green (the gap iteration 1's B1
named, still open at this site).
Proposed-edit: § Tests preamble → "`test/test_session_title.py`, files read as UTF-8 from
`Path(__file__).resolve().parents[1]`; every phrase is matched after collapsing each whitespace run, line breaks
included, to one space:".

### C1 — The orchestrator section has a second set-only sentence no test names
Severity: C
Location: change.md § Tests AC-5
Defect: The section's "A refused rename is not a blocker" bullet ends "rename again only when the set next
changes"; § Files folds the general properties into one pointer sentence, but no assertion checks it is gone.
Proposed-edit: AC-5 line, after "`each time the set below changes, and at no other time`" insert "or `only when the
set next changes`".

## Coverage

| Criterion | Test of § Tests | Status |
|---|---|---|
| AC-1 | T1 AC-1 (doc strings incl. `never within a phase`, seven bullets with ` · ` examples) | COVERED; red on the wrapped draft until whitespace is collapsed (B1) |
| AC-2 | T1 AC-2 (`never delegate`, `before the close-out`, `not a blocker`, `Kiro`) | COVERED (each on one line of the draft) |
| AC-3 | T1 AC-3 (tool + doc path per entry point; two set-only phrases absent) | COVERED |
| AC-4 | T1 AC-4 (allowed-tools, `tools`, every-agent guard) | COVERED |
| AC-5 | T1 AC-5 (two forms, pointer, issue-work activities, set-only phrase absent) | GAP: the negative is vacuous (B1) |
| AC-6 | T1 AC-6 (fleet line between the headings, `cp +…` regex) | COVERED |
| UB-1 | `test_the_title_rule_names_every_mode_and_survives_compaction` | COVERED |
| UB-2 | `test_every_work_entry_point_keeps_the_session_title` | COVERED |
| UB-3 | `test_every_desktop_tool_a_command_calls_is_allowlisted` | COVERED |

NOT-CLEAN (0 A, 1 B)
