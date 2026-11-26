# Prompt — issue #73: the session title says what the session is doing

Tier: S — natural-language assets across agents and commands plus one structural test; no new interface (DL-001).

Kind: FEATURE.

## Goal

In the Claude desktop app a main session can rename itself (`mcp__ccd_session_mgmt__set_session_title`,
`session_id: "self"`). Today only the issue-work orchestrator and `/work-issue`, `/auto-work`, `/issues-work` do,
and only to the claimed issue set. The operator: "Generally, the session title should always reflect what the agent
is doing." Every main session names its subject and its current activity.

## Scope (the ask)

- One rule text, `clients/claude/docs/session-title.md`: the form, the trigger, the tool, the four kept properties,
  the forms per kind of session.
- The orchestrator's "Session title" section and its three commands: rename on an activity change too.
- spec-conductor and `/spec-new`, `/spec-review`, `/spec-tasks`, `/spec-implement`; `/close-session`,
  `/continue-work`, `/supervise`, `/compile-memory`: rename by the doc, the tool allowlisted or in `tools`.
- An interactive main session: one CLAUDE.md fleet line in the setup prompt's Part 8.1 template (DL-002).
- `prompts/setup-claude.txt` Part 13.1d and its docs copy list, `docs/design/agents/issue-work-orchestrator.md`,
  `docs/forLLMConsumption.md`.
- Kiro: recorded that no agent-callable rename exists; no Kiro change (DL-002).

## Out of scope

- The installed toolchain copies (release and promotion).
- Skills: they run inside another session's activity.

## Tests

`test/test_session_title.py` extended; every criterion pinned. E2E: not applicable — no runtime behaviour of a
deployed system changes; CI's `tests` group runs the test.
