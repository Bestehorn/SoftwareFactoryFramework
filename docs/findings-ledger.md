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
| 2026-11-10 | test_mypy_baseline | an inline overrides table under [tool.mypy] passes the AC-1 scan | issue-7 spec evidence/verify/refutation-report.md O2 | spelling outside #7's AC-1; no such table exists | open |
| 2026-11-10 | toolchain-promotion | next promotion lists github_api/* and its tests under not_installed | issue-17 design.md Residuals X4 | manifest lists unnamed src/payload sources; integrity test then needs them installed | open |
| 2026-11-10 | toolchain-promotion | next promotion lists gitlab_api/* and its tests under not_installed | issue-13 design.md Residuals X4 | manifest lists unnamed src/payload sources; integrity test then needs them installed | open |
