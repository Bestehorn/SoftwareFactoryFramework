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
| 2026-11-11 | hooklib task ids | CHECKED_TASK_RE parses 2.1 and F1 but not the F.n ids spec-phase-tasks.md prescribes | src/hooks/hooklib.py CHECKED_TASK_RE; issue-28 tasks review SR-C2 | no incident: specs leave F tasks unticked | open |
| 2026-11-11 | github_api repos | get-commit, compare-commits print one page (two item keys) | issue-27 change.md Residuals | needs a record field; no failure seen | open |
| 2026-11-11 | github_api call gate | git/delete-ref stays callable via call | issue-27 change.md UB-4; #28 Residuals | not AC-7's branch-writing class; no incident | open |
| 2026-11-11 | github_api code-scanning | code-scanning/commit-autofix stays pending (commits to target_ref) | issue-31 DL-003 | gating is one None entry now that #27 landed | open |
| 2026-11-11 | github_api code-scanning | get-analysis SARIF and get-codeql-database zip forms need a per-call Accept | issue-31 DL-005 | records send ACCEPT_JSON; no caller needs the forms | open |
| 2026-11-11 | github_api dependabot | repository-access-for-org/-enterprise print no default_level | issue-31 change.md Residuals | no other call returns it; no failure seen | open |
| 2026-11-11 | github_api apps | app-authenticated apps records go with the configured token (no JWT or client secret) | issue-29 DL-002; change.md Residuals | another credential source would break UB-3; no caller needs it | open |
| 2026-11-11 | github_api issues | issues/get-issue-artifact prints one page of versions | issue-32 change.md Residuals | paging a list inside an object needs a record field | open |
| 2026-11-11 | github_api pulls | pulls/update-branch stays pending (writes the PR head branch) | issue-32 DL-002 | gating needs #27's None mapping; one entry once it lands | open |
