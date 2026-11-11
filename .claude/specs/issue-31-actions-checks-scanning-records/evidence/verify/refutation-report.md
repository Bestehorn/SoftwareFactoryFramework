# Refutation report: issue #31 (tier S, one wave)

Subject: branch `issue-31-actions-checks-scanning-records`, head 85f9f8f, PR #51, base origin/main f374b3d.
Diff: the five family modules, the five F test modules, three findings-ledger rows, spec files. `git diff --stat
origin/main...HEAD` names no file under `commands/`, no C, K, N, P or V test, no `registry.py`, `transport.py`,
`gitlab_wrapper.py`, `test_wrapper_delivery.py` or `pyproject.toml`.

Mutants were applied by a helper outside the worktree that backed up the five modules' bytes and sha256, edited
exactly one field of one record (asserting a single match), dropped the modules' `__pycache__` entries, and restored
the bytes and mtime, refusing unless every sha256 equalled its backup. No `git checkout`, no `git stash`.

## Claims tested

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Whole suite green on the pushed SHA | wrapper `get-run`, `wait-run`, `get-jobs` 42964120783 | FAILED-TO-REFUTE: head_sha = worktree HEAD, `completed`/`success`, wait-run exit 0, jobs security, lint, types, tests, report all success | full-suite.txt |
| M0 | F needs the wave (AC-1, AC-3, AC-4, AC-6) | five modules set to origin/main; `run_tests.py` F (5 files) | FAILED-TO-REFUTE: 69 failed, 4 passed, every failure an `AssertionError` | mutant-wave-1.txt |
| M1a | actions item key `jobs` (AC-4, AC-6) | `list-jobs-for-workflow-run` `jobs`->`job`; F actions | FAILED-TO-REFUTE: 2 failed (structural; AC-6 exit 1) | mutant-wave-1.txt |
| M1b | actions item key `artifacts` | `list-artifacts-for-repo` -> `artifact`; F actions | FAILED-TO-REFUTE: 2 failed (same two tests) | mutant-wave-1.txt |
| M1c | actions item key `workflow_runs` (part-1 record) | `list-workflow-runs` -> `runs`; F actions | FAILED-TO-REFUTE: 2 failed (same two tests) | mutant-wave-1.txt |
| M2 | Link header on one object is NONE (AC-4) | `get-actions-cache-usage-for-org` NONE->LINK; F actions | FAILED-TO-REFUTE: `test_every_list_record_has_a_case` failed (2 paging problems) | mutant-wave-1.txt |
| M3 | multi-segment `ref` (AC-3) | `checks/list-suites-for-ref` `{"ref"}`->empty; F checks | FAILED-TO-REFUTE: multi-segment test and the AC-6 case with `heads/feature/login` failed | mutant-wave-1.txt |
| M4a | only commit-autofix pending (AC-1, UB-2) | commit-autofix recorded, PENDING emptied; F code-scanning, V, K | FAILED-TO-REFUTE: `test_only_the_branch_writing_record_is_pending` and the multi-segment test failed | mutant-wave-1.txt |
| M4b | same, no record | commit-autofix off PENDING only; F code-scanning, V, K | FAILED-TO-REFUTE: F pending test and V `test_every_operation_is_covered_or_pending` failed | mutant-wave-1.txt |
| M5 | dependabot item key (AC-4, AC-6) | `repository-access-for-org` `accessible_repositories`->`repositories`; F dependabot | FAILED-TO-REFUTE: AC-6 case failed (exit 1) | mutant-wave-1.txt |
| M6a | secret-scanning LINK (AC-4, AC-6) | `list-locations-for-alert` LINK->NONE; F secret-scanning | FAILED-TO-REFUTE: structural test and AC-6 case failed | mutant-wave-1.txt |
| M6b | secret-scanning LINK, cursor-only list | `list-org-custom-patterns` LINK->NONE; F secret-scanning | FAILED-TO-REFUTE: `test_every_list_record_has_a_case` failed | mutant-wave-1.txt |
| M7a | body names (AC-2, AC-5) | `actions/create-workflow-dispatch` drops `return_run_details`; N | FAILED-TO-REFUTE: both N record tests failed (exit 2, 0 requests) | mutant-wave-1.txt |
| M7b | body names, secret write | `dependabot/create-or-update-org-secret` drops `key_id`; N | FAILED-TO-REFUTE: both N record tests failed | mutant-wave-1.txt |
| M8 | method (AC-2, AC-5) | `checks/set-suites-preferences` PATCH->POST; N | FAILED-TO-REFUTE: both N record tests failed (no route; method differs) | mutant-wave-1.txt |
| G1 | Restored tree green; UB-1 C and P, UB-2 K, UB-3 V | `git diff --quiet HEAD` on the modules (exit 0); `run_tests.py` F, N, C, K, P, V | FAILED-TO-REFUTE: 631 passed, 0 skipped, 0 failed | mutant-wave-1.txt |
| VS | No vacuous test | Grep of the five F modules and `pyproject.toml` pytest options | FAILED-TO-REFUTE: no skip, xfail, importorskip, commented-out or deselected test; every test asserts; each structural test fails on a missing record, so an empty `OPERATIONS` cannot pass (M0); all 73 F items run | - |
| RR | Red failed for the right reason | Grep of `evidence/red/wave-1.txt`; M0 regenerates it | FAILED-TO-REFUTE: 69 failed, 4 passed, all `AssertionError`, no collection or import error; the 4 passes are the AC-6 cases of the four part-1 list records (3 actions, `checks/list-for-ref`), exactly the M0 split | mutant-wave-1.txt (M0) |
| CV | Every new line exercised | Diff read; N calls every record outside `GATED_OPERATIONS` | FAILED-TO-REFUTE: the new lines are record data and docstrings; N sent 501 records and matched each to its section (M7a, M7b, M8 prove it reads the new records); F reads multi-segment, paging, item key, version and media type of every record of the five families; the ledger rows are docs | - |
| SC | Records match their sections | Read 15 records against `rest/*.md` | FAILED-TO-REFUTE: see below | - |
| T1 | F's oracle tables match the reference | Grep `- Paging:` and "may contain `/`" in the five `rest/*.md` | FAILED-TO-REFUTE: 32/4/4/8/5 `Paging:` sections = F's `LIST_RECORDS` counts; every actions "items in" key equals F's; only the two checks `ref` rows read "may contain `/`"; only `get-actions-cache-usage-for-org` and `get-hosted-runner-for-org` have a `Link` header without `Paging:` | - |
| UB1 | Part-1 records unchanged | Read `git diff origin/main...HEAD` of the modules | FAILED-TO-REFUTE: no removed line inside the five part-1 actions records or `checks/list-for-ref`; their hunks are docstrings, a comment line and the `OPERATIONS`/`PENDING` annotations | - |

Spot-checked records (method, path, query, body, paging, item key, media type, each equal to its section):
actions `get-actions-cache-usage-for-org`, `get-actions-cache-usage-by-repo-for-org`, `get-hosted-runner-for-org`,
`create-or-update-repo-secret`, `create-workflow-dispatch` (body of the default version, `return_run_details`
included); dependabot `list-alerts-for-repo` (16 query names), `repository-access-for-org`,
`create-or-update-org-secret`; secret-scanning `list-org-custom-patterns`, `list-locations-for-alert`,
`create-push-protection-bypass`; code-scanning `list-alert-instances`, `get-analysis` (`ACCEPT_JSON`, DL-005),
`upload-sarif`; checks `list-suites-for-ref`.

## Observations (no claim refuted)

- In checks, code-scanning, dependabot and secret-scanning, `test_every_list_record_has_a_case` compares only the set of
  `Paging.LINK` IDs. The item key is pinned by the AC-6 case alone, which is what the spec's AC-4 plan names. M5 shows
  that case dies.
- The cursor-only `secret-scanning/list-org-custom-patterns` and `list-repo-custom-patterns` serve both items on one
  page, so their AC-6 case cannot tell LINK from NONE. M6b dies on the structural test alone.
- No test runs `call code-scanning/commit-autofix`. UB-2's refusal rests on F's pin (no record, `PENDING` exactly that
  ID) plus K's generic unknown-ID refusal, as the spec's UB-2 plan states. M4a dies on F.

## Tree restored

All 14 restores logged `OK`: every module's sha256 equalled its backup. `git diff --quiet HEAD` exits 0. `git status
--porcelain` lists only `evidence/verify/` (this report, `full-suite.txt`, `mutant-wave-1.txt`). No stash entry was
created. The helper directory (main checkout `tmp/verify-issue-31/`) is deleted.

Claims tested: 22. Refuted: none.

Verdict: VERIFIED
