# Refutation report: issue #27 (repos and git records), head 99c26c7, PR #47

Tier S, one wave (TEST-1, TEST-2, IMPL-1..3). Commands run in the worktree with the project venv; `rt` is
`python scripts/run_tests.py`. F-r is `src/payload/test/test_github_api_repos.py`, F-g is `src/payload/test/test_github_api_git.py`.
K, N and V are the spec's names. Captures are in `evidence/verify/`: `full-suite.txt` (FS) and `mutant-wave-1.txt` (MW, one
section per run). Every mutation was applied with Edit and reverted with Edit. Each restore was checked by sha256 against the
pre-mutation value.

## 1. Whole-suite verdict

| Claim | Command | Result | Capture |
|---|---|---|---|
| Suite green on the tree's SHA | wrapper `wait-run`, `get-run`, `get-jobs`, `get-job-logs` 42957338836 | FAILED-TO-REFUTE: `completed/success`, head_sha 99c26c7 = HEAD; verify types/lint/security/tests success; `2465 passed`, hook suite `1053 passed` | FS |

## 2. Kill the mutant (wave 1)

Baseline F-r + F-g on the unmutated tree: `66 passed` (MW BASELINE).

| Id | Claim / mutation | Command | Result | Capture |
|---|---|---|---|---|
| M1 | AC-3: `repos/list-commit-statuses-for-ref` multi_segment `{ref}` -> `{}` | rt F-r | killed, 2 failed: the multi-segment table test, and the AC-6 case (`no route for GET .../commits/heads%2Ffeature%2Flogin/statuses`) | MW M1 |
| M2 | AC-3: `git/list-matching-refs` multi_segment `{ref}` -> `{}` | rt F-g | killed, 2 failed: table + slash case (`.../matching-refs/heads%2Ffeature%2Flogin`) | MW M2 |
| M3 | AC-4: `repos/list-branches` LINK -> NONE | rt F-r | killed, 2 failed: `test_every_list_record_has_a_case`, AC-6 stdout differs | MW M3 |
| M4 | AC-6: `repos/get-all-environments` item_key `environments` -> `environment` | rt F-r | killed, 1 failed: exit 1, `no item list under "environment"` | MW M4 |
| M5 | AC-4/6: `repos/list-releases` item_key None -> `releases` | rt F-r | killed, 1 failed: exit 1 | MW M5 |
| M6 | AC-7: `git/update-ref` removed from GATED_OPERATIONS | rt F-g | killed, 1 failed: `PATCH .../git/refs/heads/topic` sent | MW M6 |
| M7 | AC-7: `repos/delete-file` removed from GATED_OPERATIONS | rt F-r | killed, 1 failed: `DELETE .../contents/docs/guide/intro.md` sent | MW M7 |
| M8 | AC-7: `refuse_gated` reverted to `.get(...) is not None` | rt F-r F-g K | killed, 7 failed: every AC-7 ID sent its request; K's 41 tests passed (UB-4 refusals intact) | MW M8 |
| M9 | AC-7 wording: None branch removed (logs "use the None subcommand") | rt F-r F-g | killed, 7 failed on `fx.assert_log` (exit 2 and no request still held) | MW M9 |
| M10 | AC-4: `repos/get-commit` NONE -> LINK | rt F-r | killed, 1 failed: `Paging.LINK records without a case: ['repos/get-commit']` | MW M10 |
| M11 | AC-1: `repos.PENDING` emptied | rt F-r V | killed, 2 failed: F-r `test_only_the_upload_is_pending`, V `test_every_operation_is_covered_or_pending` | MW M11 |
| M12 | AC-2/AC-5: `repos/create-deploy-key` body drops `read_only` | rt N | killed, 2 failed: record differs from its section; call exits 2, 0 requests (227 records called) | MW M12 |
| M13 | AC-3: `git/get-tag` api_version -> `"2026-03-10"` | rt F-g | killed, 1 failed | MW M13 |
| R | Restored tree green | rt F-r F-g C K N P V properties delivery | FAILED-TO-REFUTE: `639 passed` (= green evidence) | MW RESTORED |

Every mutant was killed. No test passes without the behaviour it claims.

## 3. Vacuity scan

| Claim | Command | Result |
|---|---|---|
| No skip/xfail/deselect/commented-out/assert-nothing test | Grep F-r, F-g for `skip`, `xfail`, `deselect`, `pytest.mark.` other than parametrize, commented `def`/`assert`, `assert True`, bare `pass` | FAILED-TO-REFUTE: only `parametrize` marks. Every test asserts exit code, exact stdout, request count, log content or a literal table |
| Tables are transcribed, not read from the records | Read F-r, F-g | FAILED-TO-REFUTE: `REPOS_OPERATION_IDS`, `MULTI_SEGMENT_PARAMETERS`, `LIST_RECORDS`, `BRANCH_WRITING_CALLS` and the git tuples are literals. `GATED_OPERATIONS` is never read by F. All tables are non-empty, so an empty record set fails (red run: 64 failed) |

## 4. Red for the right reason

| Claim | Command | Result |
|---|---|---|
| `evidence/red/wave-1.txt` fails on assertions | Grep for `^E   [A-Za-z]+Error`, Import/ModuleNotFound/Syntax/Name/Attribute/Type/Key errors, collection errors | FAILED-TO-REFUTE: 64 failed, 64 `E   AssertionError`, 0 load or collection errors. Messages falsify the behaviour ("no record", "PENDING holds 202 IDs", "declares 0 records", exit 2 "No GitHub operation record declares"). The 2 passes are the pre-existing records `git/delete-ref` and `repos/get-combined-status-for-ref` |

## 5. Coverage of the change

| Claim | Command | Result |
|---|---|---|
| New/changed lines exercised | CI tests-leg coverage (FS) | FAILED-TO-REFUTE: `call.py` 140/140, `git.py` 7/7, `repos.py` 7/7 (100%). The `None` and non-`None` branches of `refuse_gated` were each killed (M8, M9). N calls all 227 non-gated records, so every new record is sent |

## Transcription spot-check and unchanged behaviour

| Claim | Command | Result |
|---|---|---|
| Records match their sections | Read `rest/*.md` against `repos.py`: rename-branch, merge-upstream, merge (branches), add-collaborator, create-commit-status, create-deploy-key, create-deployment, get-all-environments, get-views (metrics), create-pages-site, update-release, list-public (repos), get-org-rule-suites (orgs); all 13 git records | FAILED-TO-REFUTE: method, path, query and body names, paging and item key all match |
| AC-3 table complete | Grep "may contain `/`" in rest/*.md | FAILED-TO-REFUTE: branches 35 + commits 9 + repos 8 path rows + releases 1 = 53 = F-r table; git 6 = F-g table. The `ref` rows of get-repo-rule-suites and get-org-rule-suites are `query` rows, correctly excluded |
| AC-4 list set complete | Grep `Paging:` / `Link` header with operation lines | FAILED-TO-REFUTE: 38 sections = `LIST_RECORDS` (get-commit and compare-commits excluded). Item keys environments, names, statuses, attestations, branch_policies and available_custom_deployment_protection_rule_integrations match "items in" |
| UB-1 records unchanged | `git show origin/main:.../repos.py` vs HEAD; git.py diff | FAILED-TO-REFUTE: `repos/get-combined-status-for-ref` has identical fields (it moved position only), and `git/delete-ref` is unchanged. C and P passed in R |
| UB-3 files untouched | `git diff --stat origin/main...HEAD` | FAILED-TO-REFUTE: neither `gitlab_wrapper.py` nor `test_wrapper_delivery.py` is in the 15 files. delivery passed (CI 100%, R) |
| UB-4 refusals unchanged, delete-ref sent | rt K (M8, R) | FAILED-TO-REFUTE: K 41 passed; its `exit-0/empty-body` case sends `git/delete-ref`; N sends it too |

## Tree restoration

After the last revert, the sha256 values match the pre-mutation values: repos.py `6642bbd4...8143058`, git.py `e3c6dd8e...0758e4`,
call.py `ed0e48f2...899e6d`. HEAD is still 99c26c7, and `git status --porcelain` lists only `?? .claude/specs/issue-27-repos-git-records/evidence/verify/`
(this report and its two captures). My `tmp/` files are deleted. No code or test was edited.

Claims refuted: none.

Verdict: VERIFIED
