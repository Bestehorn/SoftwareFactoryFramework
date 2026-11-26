# Change — issue #73: the session title says what the session is doing

Tier: S. Kind: feature (natural-language assets and a structural test; no shipped code).

## User Prompts

- "Did the new mechanism get integrated into the agents? Give me an overview of the new flow. Generally, the session
  title should always reflect what the agent is doing. As we recently tested, agents have the ability to change their
  session label (at least in Claude Code. What about Kiro?)"
- "I agree to the point about session titles. We should implement this as an issue, i.e., file an issue and then we
  can execute this."

## Ask

Only the issue-work orchestrator and its three commands rename the desktop session today, and only to the claimed
issue set; no title says what the session is doing, and no other main session renames. Every main session in the
Claude desktop app keeps its title as `<subject> · <activity>`, renamed when either changes, from ONE rule text,
`clients/claude/docs/session-title.md` (installed at `.claude/docs/session-title.md`), that the agents and commands
point to. Kiro documents no rename an agent can call: no Kiro change (DL-002).

## Acceptance criteria

- AC-1 The doc SHALL state the form `<subject> · <activity>` and `<subject> — done`; the trigger (a change of
  subject or activity, never within a phase); the tool with `session_id: "self"` and its `ToolSearch` load; and one
  "The forms" bullet, with its activities and a ` · ` example, for issue work, the spec workflow, `/close-session`,
  `/continue-work`, `/supervise`, `/compile-memory` and an interactive session.
- AC-2 The doc SHALL keep four properties: only the main session renames (never delegated; a subagent ignores the
  rule); a flow's last rename comes before the close-out and none follows the SESSION verdict; a declined or failed
  rename is not a blocker and never a question; a session without the tool (the CLI, Kiro) skips the rule.
- AC-3 The text of each main-session entry point SHALL tell the session to rename with the tool and SHALL point to
  `.claude/docs/session-title.md`: the agents `issue-work-orchestrator` and `spec-conductor`; the commands
  `work-issue`, `auto-work`, `issues-work`, `spec-new`, `spec-review`, `spec-tasks`, `spec-implement`,
  `close-session`, `continue-work`, `supervise`, `compile-memory`; the three work commands SHALL NOT limit the
  rename to a change of the set.
- AC-4 Every command of AC-3 SHALL allowlist the tool in `allowed-tools`; every agent whose body names a desktop-app
  tool SHALL name it in `tools`.
- AC-5 The orchestrator's "Session title" section SHALL rename when the set OR the activity changes, map its phases
  to the doc's activities, and carry the forms `Issue 77 · CI` and `Auto-Work 12, 15 · 15 implementing`.
- AC-6 The CLAUDE.md template of `prompts/setup-claude.txt` Part 8.1 SHALL carry one "Fleet conventions" line naming
  the form and `.claude/docs/session-title.md`, so an interactive session learns the rule (DL-002); the setup prompt
  SHALL copy the doc into `.claude/docs/` with the other on-demand docs.

## Unchanged behaviour

- UB-1 The orchestrator's section SHALL CONTINUE TO carry `Issue 77`, `Issues 77, 80`, `Issue 77 — done`,
  `Auto-Work 12, 15, 19`, `Issues-Work 12, 15`, the `SESSION_ISSUES:` record and `"self"`.
- UB-2 The three work commands SHALL CONTINUE TO point to the agent definition's "Session title" section.
- UB-3 Every command that names a desktop-app tool SHALL CONTINUE TO allowlist it.

## Files

Every edited file keeps its line style, within 120 columns.

- `clients/claude/docs/session-title.md` — new: the rule and the forms (AC-1, AC-2).
- `clients/claude/agents/issue-work-orchestrator.md` — "Session title": the set or the activity, the phase-to-activity
  mapping, the activity forms, the pointer; its general properties become one pointer sentence (AC-3, AC-5).
- `clients/claude/agents/spec-conductor.md` — `tools` gains the tool; Conventions gains the title line (AC-3, AC-4).
- `clients/claude/commands/work-issue.md`, `auto-work.md`, `issues-work.md` — the title text renames on an activity
  change too and points to the doc (AC-3).
- `clients/claude/commands/spec-new.md`, `spec-review.md`, `spec-tasks.md`, `spec-implement.md`, `close-session.md`,
  `continue-work.md`, `supervise.md`, `compile-memory.md` — `allowed-tools` gains the tool; one title paragraph
  each (AC-3, AC-4).
- `prompts/setup-claude.txt` — Part 8.1 fleet line and the `.claude/docs/` copy list (AC-6); Part 13.1d restated to
  the new rule; the final report's on-demand docs line names the doc.
- `docs/design/agents/issue-work-orchestrator.md` — "The session title names the work" restated.
- `docs/forLLMConsumption.md` — the `test_session_title.py` entry.
- `clients/claude/README.md` — the file table gains the `docs/session-title.md` row.
- `test/test_session_title.py` — extended (Tests).
- In passing (`issue-filing-discipline.md` branch 2, DL-003): `clients/common/docs/delivery.md` §4 gains the row for
  a deploy the guard refuses — red `REFUSED … superseded`, no verdict, the tip's deploy verifies by ancestry.

## Tests

`test/test_session_title.py`, files read as UTF-8 from `Path(__file__).resolve().parents[1]`; every phrase is matched
after collapsing each whitespace run, line breaks included, to one space:

- AC-1 — the doc holds `<subject> · <activity>`, `<subject> — done`, `"self"`, `ToolSearch`, the tool and
  `never within a phase`; under `## The forms`, a bullet naming each of the seven kinds holds a backticked ` · `
  example.
- AC-2 — the doc holds `never delegate`, `before the close-out`, `not a blocker` and `Kiro`.
- AC-3 — each listed agent and command body names the tool and `.claude/docs/session-title.md`; no work command's
  body holds `only when the set changes` or `each time that set changes`.
- AC-4 — each listed command allowlists the tool, each listed agent's `tools` names it, and every agent under
  `clients/claude/agents/` names in `tools` each desktop-app tool its body names.
- AC-5 — the orchestrator section holds both activity forms, the pointer and every issue-work activity the doc
  lists, and no longer holds `each time the set below changes, and at no other time` or `only when the set next
  changes`.
- AC-6 — Part 8.1's template, between its `## Fleet conventions` and `## This project`, names the doc; a line
  matching `cp +clients/claude/docs/session-title\.md +\.claude/docs/` exists.
- UB-1, UB-2, UB-3 — the existing tests, unchanged.
- E2E: not applicable; CI's `tests` group runs the test (`pyproject.toml` `testpaths` includes `test`).

## Tasks (one wave)

- [ ] T1 TEST: the tests of § Tests, captured red before I1 (AC-1 to AC-6 fail on today's text, except AC-4's every-agent guard; UB pass) — Files:
  `test/test_session_title.py` — Validates: AC-1 to AC-6, UB-1 to UB-3
- [ ] I1 IMPL: every file of § Files but the test; T1 green — Validates: AC-1 to AC-6

## Residuals

- The installed copies (`.claude/`, this repository's `CLAUDE.md`) change only at the next release and promotion.
- Skills (`git-commit`, `git-push`, …) run inside another session's activity and do not rename.
- The sidebar's visible title length is not measured; the subject-first form is the only mitigation.
