# Findings Ledger

Findings recorded but deliberately NOT filed as issues, per
`.claude/rules/issue-filing-discipline.md`. Active rows only: a row older than six weeks
is promoted to an issue, enforced by a test or rule (`enforced <path>`), or archived
verbatim to docs/archive/findings-ledger-<YYYY-MM>.md by /compile-memory. Nothing is
deleted from git; what changes is what a session loads.

| Date | Subject | Finding | Evidence | Why not filed | Status |
|---|---|---|---|---|---|
| 2026-11-10 | issue-intake state | parallel intake runs write the same top-level state files; one resume_state.md was overwritten | 8 parallel intakes 2026-11-10 | no lost work; no measured damage | open |
| 2026-11-10 | setup prompts | 4 prose spots name AWS/MCP rules unconditionally | issue-8 spec evidence/verify/refutation-report.md | outside #8's agent-body ask; no observed failure | open |
