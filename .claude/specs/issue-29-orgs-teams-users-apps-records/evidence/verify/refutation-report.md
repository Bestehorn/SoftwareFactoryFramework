# Refutation report — issue #29 (tier S, one wave), head c007a9f, PR #50

Scope: `git diff origin/main...HEAD`. Every capture is regenerated. Mutants were byte edits to the CRLF working copies
by a disposable `tmp/` harness (deleted). Each edit was restored in a `finally` with its original mtime and a sha256
check (`# sha256 restored … MATCH` in every capture). Tests ran through `scripts/run_tests.py`.

## Claims tested

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| CI | Whole suite green on the pushed SHA | wrapper `wait-run`, `get-run`, `get-jobs`, `get-job-logs`, run 42962058110 | head_sha = worktree HEAD; 5/5 jobs success; 2545 + 1053 passed, 0 failed, 0 skipped. FAILED-TO-REFUTE | `full-suite.txt` |
| W1 | The wave's tests need its implementation | four modules reverted to origin/main; F×4 + N + V | 78 failed, 26 passed; every F function fails in every family but the teams/apps empty-table tests (V2). FAILED-TO-REFUTE | `mutant-wave-1.txt` |
| AC-1a | `PENDING` empty, judged | one ID back on each `PENDING` (`orgs/get`, `teams/list`, `users/follow`, `apps/get-by-slug`) | each: F `test_nothing_is_pending` and V `test_one_module_per_family_holding_only_its_own_ids` fail. FAILED-TO-REFUTE | `mutant-pending-*.txt` |
| AC-1b | Names are the section's | drop a body name per family (`digest`, `privacy`, `bio`, `permissions`), query `since` of `users/list`, path `/orgs/{org}/team` of `teams/list` | each: N record test and N call test fail (path also fails F's AC-3 case). FAILED-TO-REFUTE | `mutant-body-*.txt`, `mutant-query-users-list.txt`, `mutant-path-teams-list.txt` |
| AC-2a | LINK where a `Paging:` line exists | LINK→NONE on `orgs/list-members`, `teams/list`, `users/list`, `apps/list-webhook-deliveries` | each: F list-set test and that AC-3 case fail. FAILED-TO-REFUTE | `mutant-link-none-*.txt` |
| AC-2b | Bulk `POST`s are NONE | NONE→LINK on `orgs/list-attestations-bulk`, `users/list-attestations-bulk` | each: F list-set test and N call test fail. FAILED-TO-REFUTE | `mutant-bulk-link-*.txt` |
| AC-2c | `item_key` is the section's | `installations` (apps→None, orgs→`installation`), `repositories` (apps→None, orgs→`repos`), `attestations` (orgs→`attestation`, users→None), `teams/list` None→`teams` | each: that AC-3 case fails (exit 1, "returned no item list"). FAILED-TO-REFUTE | `mutant-key-*.txt` |
| AC-2d | NONE records carry no key | `orgs/get` item_key→`x` | F list-set test fails. FAILED-TO-REFUTE | `mutant-key-orgs-none-record.txt` |
| AC-2e | `multi_segment` = the "may contain `/`" path rows | drop `subject_digest` on `orgs/list-attestations`, `orgs/list-artifact-storage-records`, `users/list-attestations`, `users/delete-attestations-by-subject-digest` | each: F multi-segment test fails; the two list records' AC-3 cases also fail (sent `sha256%2F…`, unrouted). FAILED-TO-REFUTE | `mutant-ms-*.txt` |
| AC-2f | Default version and media type | `teams/check-permissions-for-repo-in-org` accept→`application/vnd.github.v3.repository+json`; `apps/get-by-slug` api_version→`2026-03-10` | each: F default-version test fails. FAILED-TO-REFUTE. `mutant-version-apps.txt` (`2022-11-28` = `transport.API_VERSION_DEFAULT`) is equivalent, not counted | `mutant-accept-teams.txt`, `mutant-version-apps-nondefault.txt` |
| AC-3 | A LINK record prints both items | the AC-2a/c/e mutants | 25/10/17/12 cases pass green, fail on each paging, key, path and slash mutant. FAILED-TO-REFUTE | as above |
| AC-4 | Each new record sends its section's call | `GATED_OPERATIONS` in `commands/call.py` read; N mutants | no ID of the four families is gated, so N calls every record; N fails on each name, path and bulk mutant. FAILED-TO-REFUTE | `mutant-body-*.txt` |
| V1 | No vacuous test | added lines scanned for skip, xfail, deselect, importorskip, commented-out tests, `addopts` | only `pytest.mark.parametrize` ×4; no config file in the diff; each F function killed in each module. FAILED-TO-REFUTE | mutant captures |
| V2 | teams/apps empty-table tests can fail | add `org` to `teams/list`, `plan_id` to `apps/list-accounts-for-plan` multi_segment | each: F multi-segment test fails. FAILED-TO-REFUTE | `mutant-ms-{teams,apps}-add.txt` |
| V3 | F's tables come from the sections | Grep of `rest/{orgs,teams,users,apps}.md` | `Paging:` lines on the families' IDs: orgs 25 + bulk, teams 10, users 17 + bulk, apps 12; IDs and keys = `LIST_RECORDS`. Other `Link` headers: `hosted-compute/*` only. "may contain `/`" path rows: orgs 3, users 2 = `MULTI_SEGMENT_PARAMETERS`; the rest are body fields or a `repos/` query. FAILED-TO-REFUTE | doc reads |
| R1 | Red for the right reason | Grep of `evidence/red/wave-1.txt` and `mutant-wave-1.txt` | both 78 failed, all `AssertionError`, no collection or import error. List cases "exit code 2, the golden is 0" / "No GitHub operation record declares …"; structural "PENDING holds N IDs" / "no record". Stored red's 2 passed are the teams/apps empty-table tests (change.md D1). FAILED-TO-REFUTE | `mutant-wave-1.txt` |
| C1 | Changed lines exercised | CI coverage, tests job | the four family modules 100% each; every record called by N and judged by F; the remaining changed lines are docstrings, comments, spec files, one ledger row. FAILED-TO-REFUTE | `full-suite.txt` |
| S1 | Spot-check, 12 sections | Read vs record: `teams/list`, `teams/create`, `teams/check-permissions-for-repo-in-org`, `orgs/list-artifact-deployment-records` (not multi-segment), `orgs/list-artifact-storage-records`, `orgs/list-attestations-bulk`, `orgs/list-attestations`, `orgs/get-immutable-releases-settings-repositories`, `users/list`, `users/delete-attestations-by-subject-digest`, `apps/list-installations`, `apps/list-webhook-deliveries`, `apps/create-installation-access-token` | method, path, query, body, paging, key, multi_segment all match. FAILED-TO-REFUTE | — |
| UB-1 | Compat unchanged; `users/get-authenticated` as before | `cmp` of the record at origin/main and HEAD; diff names no fixture (`CASES`), command, registry or transport file; C, P in green runs | record byte-identical; C, P pass. FAILED-TO-REFUTE | `green-before.txt`, `green-after.txt` |
| UB-2 | Gated, unknown, undocumented refused | K in green runs; `commands/call.py` not in the diff | pass. FAILED-TO-REFUTE | same |
| UB-3 | Credential file only; stdlib only | C credential test, V stdlib test in green runs; modules import `typing`, `github_api` only | pass. FAILED-TO-REFUTE | same |
| UB-4 | gitlab wrapper and delivery test untouched, passing | `git diff --stat` on both: empty; delivery test in green runs | pass. FAILED-TO-REFUTE | same |

Green runs over the 11 affected files (F×4, C, K, N, P, V, properties, delivery): 653 passed before the mutants and 653
after the last restore. The `deadbeef…` hex in two users captures is the users F test's own `subject_digest` value.

## Tree restoration

After the last mutant and the final green run, each family module's sha256 equals its pre-run digest (orgs `441fa37c…`,
teams `67ecfdb3…`, users `1d2d04ff…`, apps `8ca72b46…`). `git diff --quiet` passes, and `git status` lists only this
`evidence/verify/` directory. `tmp/verify/` is deleted.

Verdict: VERIFIED
