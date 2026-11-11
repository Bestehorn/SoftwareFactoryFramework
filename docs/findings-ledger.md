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
| 2026-11-11 | github_api copilot | copilot/set-copilot-content-exclusion-for-organization stays pending | issue-33 DL-004 | body is a map of any key; call refuses undocumented names | open |
| 2026-11-11 | github_api gitignore, licenses | get-template and get-for-repo send ACCEPT_JSON, not their raw/html types | issue-33 change.md Residuals | needs a per-call Accept; no caller needs it | open |
| 2026-11-11 | hooks gate_filing | blocks any command whose text holds its create phrase (commit message, ledger row) | issue-41 run 2026-11-11, before 94986b0 | scans the whole command; narrowing is a design choice | open |
| 2026-11-11 | github_api code-scanning | code-scanning/commit-autofix stays pending (commits to target_ref) | issue-31 DL-003 | gating is one None entry now that #27 landed | open |
| 2026-11-11 | github_api code-scanning | get-analysis SARIF and get-codeql-database zip forms need a per-call Accept | issue-31 DL-005 | records send ACCEPT_JSON; no caller needs the forms | open |
| 2026-11-11 | github_api dependabot | repository-access-for-org/-enterprise print no default_level | issue-31 change.md Residuals | no other call returns it; no failure seen | open |
| 2026-11-11 | github_api apps | app-authenticated apps records go with the configured token (no JWT or client secret) | issue-29 DL-002; change.md Residuals | another credential source would break UB-3; no caller needs it | open |
| 2026-11-11 | github_api issues | issues/get-issue-artifact prints one page of versions | issue-32 change.md Residuals | paging a list inside an object needs a record field | open |
| 2026-11-11 | github_api pulls | pulls/update-branch stays pending (writes the PR head branch) | issue-32 DL-002 | gating needs #27's None mapping; one entry once it lands | open |
| 2026-11-11 | gitlab_api plan | plan#clone-an-issue and plan#create-a-merge-request-note (the merge quick action) stay pending | issue-39 DL-003 | GitLab gate has no no-subcommand form | open |
| 2026-11-11 | gitlab_api plan | emoji MR/snippet keys and group notification_settings keys stay pending | issue-39 change.md Residuals | one record per Reference | open |
| 2026-11-11 | gitlab_api plan | emoji combined path row declared as written; giving it sends a stray attribute | issue-39 change.md Residuals | N needs the row; no failure seen | open |
| 2026-11-11 | gitlab_api plan | the clone quick action runs from saved issue notes and descriptions (part 1, update-an-issue-note) | issue-39 review iteration-01 C3 | quick actions run server-side; guarding is a mechanism | open |
| 2026-11-11 | gitlab_api call | integration secrets passed with -f are visible in process arguments | issue-36 change.md Residuals; #41 design Residuals | no non-argv text input; guarding is a new mechanism | open |
| 2026-11-11 | gitlab_api verify | artifact glob routes, the merge-train add, later endpoints of multi-endpoint References stay pending | issue-37 DL-003 | no glob form; no no-subcommand gate; one record per id | open |
| 2026-11-11 | gitlab_api verify | variable values and runner, trigger, job tokens go as -f or query text; query tokens reach error and 429 logs | issue-37 change.md Residuals | #41 Residuals; no failure seen | open |
| 2026-11-11 | gitlab_api verify | deletes, token resets, deployment approvals, pipeline and job runs, release tag creation are callable ungated | issue-37 change.md Residuals | #41 Security: outside the gated class | open |
| 2026-11-11 | github_api call | a secret body value given with -f/-F still shows on the command line; --input carries no JSON body | issue-46 design.md Residuals | needs #28 D4's name check over a parsed input | open |
| 2026-11-11 | github_api repos | release-asset upload sends octet-stream and builds its URL from the record; Transport.upload has no caller | issue-46 design.md Residuals | per-asset media type is a requirements residual | open |
| 2026-11-11 | github_api markdown | markdown/render-raw always sends text/plain; no per-call media type | issue-46 design.md Residuals | #28 requirements residual | open |
| 2026-11-11 | github_api transport | REST_ROOTS holds github.com roots only; GHES upload hosts are outside it | issue-46 design.md Residuals | conventions.md Hosts and base URLs; no GHES caller | open |
| 2026-11-11 | github_api call | no guard refuses an --input path naming the credentials file; the 307 re-send is not logged | issue-46 design.md Security Considerations, Residuals | no failure seen; a guard is a mechanism | open |
| 2026-11-11 | gitlab_api graphql | branchRuleUpdate and branchRuleDelete stay callable and can lift trunk protection | issue-44 DL-002; design.md Residuals | gate_merge_steward enforces; refusing is its own change | open |
| 2026-11-11 | gitlab_api graphql | a mutation with errors beside partial data exits 1 printing nothing; its effect may have applied | issue-44 design.md Residuals | conventions.md Errors and partial data; no failure seen | open |
| 2026-11-11 | gitlab_api graphql | nested connections print their first page; WorkItem.widgets prints three widgets in full | issue-44 design.md Residuals | a record pages one connection | open |
| 2026-11-11 | gitlab_api graphql | designManagementUpload (18.6) and workItemExport (18.0) are deprecated; a regeneration dropping them fails Q | issue-44 design.md Residuals | Q flags it when the reference changes | open |
