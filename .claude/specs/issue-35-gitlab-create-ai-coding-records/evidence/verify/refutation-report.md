# Refutation report: issue #35 (create and ai-coding GitLab records), tier S, wave 1

Subject: worktree `.claude/worktrees/issue-35`, HEAD 0e6f27d (PR #59), merge-base origin/main 25c91d3. P8 = the
wave's paired tests: F create, F ai-coding, N contract, V coverage, K call, C compat, P properties, wrapper delivery,
run as `python scripts/run_tests.py <P8> --tb=line`. A disposable harness (tmp/, deleted) applied each mutant as an
exact byte replacement on the CRLF working-tree bytes, checked sha256 before, after mutation and after restore, and
restored the mtime; no `git checkout`, no `git stash`.

## Step 1: whole suite

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI green on this tree | wrapper `get-run 42985585816`, `get-jobs`, `get-job-logs 130405849416` | FAILED-TO-REFUTE: completed/success, head_sha = HEAD, base = merge-base; 5/5 jobs success; 3057 passed, 1053 passed, 0 failed | full-suite.txt |

## Step 2: kill the mutant (one run of P8 per mutant)

| Id | Mutation | Failing tests | Result |
|---|---|---|---|
| W1 | both modules reverted to origin/main | all 60 F items; 193 passed | killed |
| C1 | blobs `files` ARRAY_OF_HASHES to ARRAY | Fc typed | killed |
| C2 | merge-base `refs` ARRAY to SCALAR | Fc typed | killed |
| C3 | blame `range` HASH to SCALAR | Fc typed | killed |
| C4 | pipeline status `state` required off | Fc typed | killed |
| C5 | update-snippet `files` (conditional) required | Fc typed | killed |
| C6 | new-tag `message` required | Fc typed | killed |
| C7 | changed-paths (`page` row) OFFSET to NONE | Fc paged, Fc AC-6 case | killed |
| C8 | gitignore list OFFSET to NONE | Fc paged, Fc AC-6 case | killed |
| C9 | retrieve-a-commit NONE to OFFSET | Fc paged | killed |
| C10 | list-all-snippets OFFSET to KEYSET | Fc paged, Fc AC-6 case | killed |
| C11 | POST branches off PENDING, create-repository-branch declared | Fc pending, Fc typed | killed |
| C12 | GET tree put back on PENDING | Fc pending | killed |
| C13 | query member `range[start]` dropped | Fc typed | killed |
| C14 | body member `position[base_sha]` given a Param | Fc typed, N record | killed |
| C15 | body name `line_type` dropped | N record | killed |
| C16 | archive key off PENDING, undeclared | Fc pending, V mapped-or-pending | killed |
| C17 | raw-blob record OFFSET (bytes decoded as pages) | Fc paged, Fc AC-7 | killed |
| P1 | part 1 delete-repository-branch body FORM | Fc typed | killed |
| A1 | context commits `commits` ARRAY to SCALAR | Fa typed | killed |
| A2 | completions `current_file` HASH to SCALAR | Fa typed | killed |
| A3 | time estimate `duration` required off | Fa typed | killed |
| A4 | `blocking_merge_request_id` (conditional) required | Fa typed | killed |
| A5 | DL-005 participants OFFSET to NONE | Fa paged, Fa AC-6 case | killed |
| A6 | DL-005 blockees OFFSET to NONE | Fa paged, Fa AC-6 case | killed |
| A7 | time_stats NONE to OFFSET | Fa paged | killed |
| A8 | rebase key off PENDING, rebase record declared | Fa pending | killed |
| A9 | time_stats key put back on PENDING | Fa pending | killed |
| A10 | query member `not[author_id]` dropped | Fa typed | killed |
| A11 | body member `position[base_sha]` given a Param | Fa typed, N record | killed |
| A12 | body name `discussion_locked` dropped | N record | killed |
| A13 | `not[labels]` ARRAY to SCALAR | Fa typed | killed |
| P2 | part 1 create-a-merge-request `title` required off | Fa typed | killed |
| P3 | part 1 retrieve-a-merge-request query row dropped | N record | killed |
| P4 | part 1 approve-merge-request body row dropped | N record | killed |
| P5 | part 1 gated merge-a-merge-request `sha` required | Fa typed | killed |
| P6 | part 1 MR pipelines OFFSET to NONE | Fa paged, C `mr-checks` | killed |

FAILED-TO-REFUTE: 37 of 37 killed, each on an AssertionError naming the mutated record; every restore sha256-equal
(mutant-wave-1.txt). Re-confirm on the restored tree: 253 passed (green-reconfirm.txt).

## Steps 3 to 5

| Claim | Command | Result | Capture |
|---|---|---|---|
| Step 3: no vacuous F test | Grep of both F modules for skip, xfail, importorskip, marks, commented tests; pyproject `addopts` | FAILED-TO-REFUTE: only `parametrize` (36 and 17 cases); addopts `-ra --import-mode=importlib`, unchanged; W1 fails every one of the 60 F items | mutant-wave-1.txt (W1) |
| Step 4: red for the right reason | Grep of evidence/red/wave-1.txt; W1 regenerates it | FAILED-TO-REFUTE: 60 failed, 60 `E   AssertionError` lines, no other exception or collection error; W1 fails the same 60 items on assertions (PENDING, typed and paged sets, `assert 2 == 0` exit codes) | red/wave-1.txt, mutant-wave-1.txt |
| Step 5: changed lines exercised | CI job log coverage | FAILED-TO-REFUTE: families/create.py and ai_coding.py 100%; N calls every new record (none gated), F types and pages each; F's uncovered lines are the fixture-reuse branch and failure-message helpers (test code), run by W1 | full-suite.txt |
| Spot-check vs reference | Read of rest/create.md (21 sections) and rest/ai-coding.md (19 sections); whole-page Greps | FAILED-TO-REFUTE: method, path, rows, Kind, Required, paging match; every `page`-row and "List" GET is in F's paged sets (create 32+4, ai-coding 12+2+4); every array/hash row, Required `yes` row and query member row of a declared record is in F's tables | none (reading) |
| UB-1 part 1 unedited | `git diff origin/main...HEAD` of both modules | FAILED-TO-REFUTE: part-1 record lines are context only; C mr and delete-branch forms green; P1 to P6 killed | mutant-wave-1.txt |
| UB-2 refusals | diff stat of `commands/`; Read `GATED_OPERATIONS`; Grep of gitlab_api for the 14 kept IDs | FAILED-TO-REFUTE: call.py untouched; gated set is `mr merge` and `issue create` only; no kept ID declared; K gated and unknown tests green; A8, C11 killed | green-reconfirm.txt |
| UB-3 stdlib only | Grep imports of both modules | FAILED-TO-REFUTE: `__future__`, `typing`, `gitlab_api.registry`; P `test_standard_library_only` green | green-reconfirm.txt |
| UB-4 GitHub untouched | `git diff --stat origin/main...HEAD` on github_wrapper.py, github_api, test_wrapper_delivery.py | FAILED-TO-REFUTE: empty; delivery tests green | green-reconfirm.txt |
| Ledger rows each 240 B or less | byte count of the 4 issue-35 rows | FAILED-TO-REFUTE: 232, 209, 228, 201 B | none (count) |

Claims tested: CI verdict, 37 mutants over AC-1 to AC-4, AC-6, AC-7 and UB-1/UB-2, vacuity, red reason, coverage,
spot-check, UB-1 to UB-4, ledger rows. Refuted ids: none.

Tree restored: `git status --porcelain` lists only `evidence/verify/` untracked, `git diff --stat` is empty, both
modules sha256-equal to their pre-run bytes, tmp/verify-35 removed.

Verdict: VERIFIED
