# spec-review-agent — iteration 01 (tier S, combined pass)

Reviewed: `change.md`, the rule draft (`tmp/session-title-draft/session-title.md`, the AC-1/AC-2 artefact), issue #73,
against the orchestrator, spec-conductor, the eleven commands, `prompts/setup-claude.txt`, the design doc and
`test/test_session_title.py` in the worktree. Security lens not applicable.

### B1 — The trigger change, the core of the ask, is pinned by no test
Severity: B
Location: change.md § Tests (AC-1, AC-3, AC-5); § Acceptance criteria AC-3
Defect: No test asserts the trigger. The doc's `never within a phase` is not checked, and neither are the orchestrator
section's "set OR activity" rule and its phase mapping. Nothing checks that the old set-only wording is gone: the
orchestrator's "each time the set below changes, and at no other time", `work-issue.md`/`auto-work.md` "only when the
set changes", `issues-work.md` "each time that set changes". All of it can survive I1 with T1 green.
Material-because: AC-5 ("SHALL rename when the set OR the activity changes, map its phases to the doc's activities")
and the trigger clause of AC-1 are untested. Wrong-behaviour: the three work entry points keep renaming on a set
change only.
Proposed-edit: § Tests, AC-1 line: after "`ToolSearch` and the tool" insert ", `never within a phase`". AC-5 line →
"the orchestrator section holds both activity forms, the pointer and every issue-work activity the doc lists, and
no longer holds `each time the set below changes, and at no other time`". AC-3 line: append "; no work command's
body holds `only when the set changes` or `each time that set changes`". AC-3 text: append "; the three work
commands SHALL NOT limit the rename to a change of the set" (this restates § Files: "renames on an activity change
too").

### B2 — `closing out` contradicts `— done` and the end rule
Severity: B
Location: rule draft § The forms (Issue work, Close-out) and § The rule "The end"; change.md AC-2
Defect: Issue work lists the activity `closing out`, and the Close-out form renames during the close-out. "The end"
says the last rename comes before the close-out. `/work-issue` ("Drop X from the session title … before the
close-out", then "Run the `/close-session` checks as this command's last step") and orchestrator HAND_OFF step 5
both set `Issue X — done` before the close-out runs. So the `closing out` rename either never happens or replaces
`Issue 77 — done` on a finished session.
Material-because: AC-1's close-out form contradicts AC-2's "the last rename comes before the close-out". Regression:
today a finished `/work-issue` ends titled `Issue 77 — done` (UB-1's form).
Proposed-edit: in the draft, Issue work activities: delete "`closing out`, ". Close-out bullet → "**Close-out** —
`/close-session` run on its own. Subject: the one the title already names. Activity: `closing out`, set at its
first step. A flow whose last step runs the close-out checks (`/work-issue`, the orchestrator) keeps its
`<subject> — done`. Example: `Issue 77 · closing out`." "The end" → "**The end.** A flow's last rename,
`<subject> — done`, comes before the close-out; no rename follows the SESSION verdict: on `SESSION: CAN CLOSE` the
archive is the turn's last call." AC-2 → "a flow's last rename comes before the close-out and none follows the
SESSION verdict". The AC-2 test string `before the close-out` still holds.

### B3 — An interactive session's activity changes trigger no rename
Severity: B
Location: rule draft § The rule "When"; change.md AC-1 (the trigger)
Defect: "When" lists the triggers (a new `Phase:` value, a command step, "in an interactive session when the operator
starts a different task") and ends "and at no other time". An interactive session runs no agent and no command and
records no `Phase:`, so moving between its listed activities (`reading` … `CI`, `answering`, `needs you`) never
triggers a rename. Its title keeps its first activity.
Material-because: this contradicts AC-1's trigger ("a change of subject or activity") for the interactive kind.
Wrong-behaviour.
Proposed-edit: replace "and in an interactive session when the operator starts a different task" with "and in an
interactive session when the operator starts a different task or the work moves to another of its activities".

### C1 — The AC-6 test needs a whitespace-tolerant match
Severity: C
Location: change.md § Tests AC-6
Defect: The literal `cp clients/claude/docs/session-title.md .claude/docs/` has single spaces, but the copy list it
joins pads its columns, and § Files says "Every edited file keeps its line style".
Proposed-edit: "a line matching `cp +clients/claude/docs/session-title\.md +\.claude/docs/` exists".

### C2 — The client README's file table is not in § Files
Severity: C
Location: change.md § Files
Defect: `clients/claude/README.md` has a row for every on-demand doc (`docs/run-identity.md`,
`review-contract.md`, `delivery.md`), and the new doc gets none.
Proposed-edit: add "`clients/claude/README.md` — the file table gains the `docs/session-title.md` row".

### C3 — The spec-workflow form leaves three phases unmapped
Severity: C
Location: rule draft § The forms, Spec workflow
Defect: spec-conductor's phases include SETUP, TASKS_REVIEW_LOOP and DONE, and the bullet maps none of them.
Proposed-edit: append "The review phases are `spec review`; SETUP is `prompt`; DONE is `Spec <feature> — done`."

### C4 — T1's red claim overstates AC-4
Severity: C
Location: change.md § Tasks T1
Defect: AC-4's every-agent guard passes on today's text, because the orchestrator is the only agent that names a
desktop tool and it already lists that tool in `tools`.
Proposed-edit: "(AC-1 to AC-6 fail on today's text, except AC-4's every-agent guard; UB pass)".

## Coverage

| Criterion | Test of § Tests | Status |
|---|---|---|
| AC-1 | T1 AC-1 (doc strings, seven forms) | COVERED, except the trigger: GAP (B1) |
| AC-2 | T1 AC-2 (four strings) | COVERED |
| AC-3 | T1 AC-3 (tool + doc path per entry point) | COVERED, except the set-only wording: GAP (B1) |
| AC-4 | T1 AC-4 (allowed-tools, `tools`, every-agent guard) | COVERED |
| AC-5 | T1 AC-5 (two forms + pointer) | GAP: trigger and phase mapping (B1) |
| AC-6 | T1 AC-6 (fleet line, cp line) | COVERED |
| UB-1 | `test_the_title_rule_names_every_mode_and_survives_compaction` | COVERED |
| UB-2 | `test_every_work_entry_point_keeps_the_session_title` | COVERED |
| UB-3 | `test_every_desktop_tool_a_command_calls_is_allowlisted` | COVERED |

NOT-CLEAN (0 A, 3 B)
