# Refutation report: issue #17 (PR #26, head 95fc3b8)

Worktree `.claude/worktrees/issue-17`, diff `origin/main...HEAD` (merge base 1c69c2a). `RT` = `venv\Scripts\python.exe
scripts/run_tests.py`, run from the worktree. Each mutant was applied with Edit, its paired tests run once, then
`git checkout -- <file>`; `git status --porcelain` printed nothing after every restore. Captures are quoted inline:
the dispatch allowed this one file.

## 1. Whole-suite verdict

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI green on the tree's SHA | `github_wrapper.py get-run 42903402594`, `get-pr-checks 26` | FAILED-TO-REFUTE | `head_sha 95fc3b82…` = local HEAD; `completed`/`success`; verify lint, types, security, tests and report all `success` |

## 2. Mutants per wave (T R C V P S = design's test files)

| Wave, criterion | Mutant | Command | Result | Capture |
|---|---|---|---|---|
| 1 AC-3.1 | `remove_header` dropped | RT T -k cross_origin | killed | `5 failed`: `Bearer …` at index 1 != None |
| 1 AC-2.1 | API version never set | RT T -k (5 tests) | killed | `('…/repos/o/r', None)` != `'2022-11-28'` |
| 1 AC-3.2 | retry-after skipped when remaining 0 | same run | killed | `assert [3600.0] == [5]` |
| 1 AC-4.3 | errors raised only with data null | same run | killed | `DID NOT RAISE GitHubGraphQLResponseError` |
| 1 AC-2.2, 2.4 | `_send` origin refusal dropped | same run | killed | `no route for GET https://api.github.com.example.net/…`, upload to API host |
| 1 AC-2.2 | `link` split at every comma | RT T -k (6 tests) | killed | comma-in-the-next-query: `{'number': 3}` missing |
| 1 AC-2.3 | item key ignored | same run | killed | `returned no item list under "workflow_runs"` x5 |
| 1 AC-3.3 | bucket not named | same run | killed | `'"search"' in '… the primary rate limit …'` false |
| 1 AC-3.4 | error body dropped | same run | killed | `assert None == {'message': 'Not Found', …}` (404, 422, 403) |
| 1 AC-4.1 | variables dropped | same run | killed | `{'variables': {}}` != `{'owner': 'o', 'name': 'r'}` |
| 1 AC-4.2 | cursor not advanced (alone) | RT T -k page_info_cursors | killed | index 1 `after: None` |
| 2 AC-1.1 | `.`/`..` refusal, undocumented-name refusal, single-segment `safe` | RT R | killed | `14 failed, 6 errors`: `DID NOT RAISE GitHubAPIError` x7; `no route for PATCH …?issue_number=7`; `needs%20review/ui` |
| 3 AC-5.2, 5.3 | `activity/get-feeds`, `Sponsors` unlisted | RT V | killed | `neither covered … nor pending: Sponsors, activity/get-feeds` |
| 3 AC-1.3 | checks record path off its row | same run | killed | `declares ('GET', '…/check-run'), its index row is …/check-runs` |
| 3 UB-2.2 | `import yaml` in a family | same run | killed | `github_api/families/emojis.py:9: yaml` |
| 3 AC-1.2 | discovery drops a module | RT V -k discovery | killed | `Right contains one more item: ('github_api.families.users', …)` |
| 3 AC-5.1, 5.2 (D7 helpers) | gaps ignore capabilities; header rows read | RT V -k "read_whole or gap_is_named" | killed | `['beta/delete-thing'] == ['Uncovered capability', …]`; `read ['Capability', 'Capability', '---']` |
| 4 UB-1.1 | list line width; checklist re-read check dropped | RT C -k "list-issues or checklist or …" | killed | 3 list-issues `standard output differs`; `write-not-on-re-read: exit code 0, the golden is 1` |
| 4 secrets | `_without_userinfo` returns the URL | same run | killed | `a log record holds the withheld 'ghp_T'` and `'secret'` |
| 4 UB-1.2 | dequeue-pr drops `--reason` | same run | killed | `['--token-std…equeue', '77']` short of `--reason` |
| 4 UB-1.1 | API error exits 0 | RT C -k "issue/exit-1 or …" | killed | 16 cases `exit code 0, the golden is 1` |
| 4 UB-3.2 | logging set up at import | same run | killed | `loading the module set up logging` |
| 4 UB-2.1 | env fallback in `_load_token` | same run | killed | `these files read the process environment` |
| 4 UB-3.2 | `sys.path` insertion dropped | RT delivery + C | killed | `8 failed`: `No module named 'github_api'` |
| 4 P oracle | golden `claimed` negated | RT P -k claim-check | killed | `8 failed`: `standard output differs from the golden` |
| 5 UB-1.1 | claim-check 0; timeout exits 10; get-logs filter inverted; merge default `squash` | RT C P S -k … | killed | `golden is 3` x2; `exit code 10, the golden is 11`; failed-only stdout differs; parity `default='merge'` vs `'squash'` |
| 5 UB-1.3 Kiro | Part 6.2 copy line; shipped-Python line | RT S | killed | `Part 6.2 … does not name src/payload/scripts/github_api/`; `Shipped Python … does not name scripts/github_api/` |
| **R1** 5 UB-1.3 Claude | Part 5.3 copy step deleted (`and src/payload/scripts/github_api/ to scripts/github_api/ (…copied together)`) | RT S | **REFUTED** | `1 passed` |

R1: `missing_paths` checks substring presence in the whole Part 5.3 section, and its three pointers ("See
`src/payload/scripts/github_api/` for GitHub …") satisfy it without the copy step. A project set up from that prompt
copies the entry script alone, which cannot import its package (the S module's own docstring).

## 3. Vacuity

| Claim | Command | Result | Capture |
|---|---|---|---|
| No skip, xfail, deselect or assert-nothing test | Grep `skip\|xfail\|deselect\|pytest\.mark\|assert True` over the 7 test files | FAILED-TO-REFUTE | only `parametrize`, `usefixtures` |

Tests green before their wave's code: D7 helpers (killed above, test-side), P (fork oracle, killed by P-A), UB-3.2
load test (unchanged behaviour, killed by two mutants).

## 4. Red for the right reason

| Claim | Command | Result | Capture |
|---|---|---|---|
| Waves 1-5 red on assertions | `python .claude/hooks/red_for_right_reason.py evidence/red/wave-N.txt` | FAILED-TO-REFUTE | `OK … genuine assertion/property falsification`, exit 0 x5 |

Waves 1-2 fail on the fixture's `<module>.py is not written` assertion; wave 3 `4 failed, 19 passed` (17 R, 2 D7
helpers); wave 4 `70 failed, 78 passed`; wave 5 `117 failed, 635 passed`.

## 5. Coverage of the change

`RT --coverage` over T, R, C, V, P, S and `test_wrapper_delivery.py`: `564 passed`, 96.14%.

| Id | Criterion | Result | Unexercised lines |
|---|---|---|---|
| **R2** | UB-1.1 | REFUTED | `commands/issues.py` 151 (`list-issues --limit` 0 or less); `github_wrapper.py` 161-162 (a credential file that is not UTF-8, the exit-2 refusal) |
| **R3** | AC-3.4 (D3's routing of AC-3.2's boundary) | REFUTED | `transport.py` 269-270 (a 403/429 whose rate header is no integer: no retry, `GitHubAPIError` with its status) |

Not graded, no criterion constrains them (malformed-response and refusal guards of D3-D5): transport 121-122, 164,
181-182, 225, 310-313, 321, 339-356, 537, 542; registry 97, 99, 126; ci 124, 244-245, 254-255; claim 135, 160;
issues 134. `github_wrapper.py` 322-323 run in the `test_the_script_runs_by_path` subprocess.

## Other checks

| Claim | Command | Result | Capture |
|---|---|---|---|
| F.2 | `git diff --name-only origin/main...HEAD -- src/payload/scripts/gitlab_wrapper.py src/payload/test/test_wrapper_delivery.py` | FAILED-TO-REFUTE | empty |
| No environment read, stdlib only | Grep `os\.environ\|getenv`, Grep imports, entry script and `github_api/` | FAILED-TO-REFUTE | no match; stdlib and `github_api` only |
| Token only in `Authorization` | Grep `_token` in `github_api/` | FAILED-TO-REFUTE | one use, `_build_request` |

## Tree

Every mutated file restored with `git checkout`. Re-green after the last restore: `RT` T R C V P S delivery,
`564 passed`. This run's residue (`tmp/verify-coverage.txt`, `.coverage`) removed; `tmp/fx-17.txt` and `tmp/pr-17.md`
predate this run and were left. The only change to the tree is this file.

REFUTED R1 R2 R3

## Re-verification 2026-11-10 (head faa6ceb)

`git diff 95fc3b8 faa6ceb -- src/payload/scripts prompts docs` printed nothing: the delta is three test files and spec
evidence. Each mutant was applied with Edit, its paired tests run once, then `git checkout -- <file>`; every target's
sha256 equalled its pre-mutation value and `git status --porcelain` printed nothing after each restore.

| Id | Claim | Mutant | Command | Result | Capture |
|---|---|---|---|---|---|
| CI | suite green on the tree's SHA | none | `get-pr-checks 26` | FAILED-TO-REFUTE | `head faa6cebe…` = local HEAD; `report`, `verify (lint/tests/types/security)` all `completed`/`success`; `statuses: []` under `combined_status: pending` |
| R1 | Part 5.3 copies the package | copy clause deleted | RT S | FAILED-TO-REFUTE | `1 failed`: `the sentence that copies …github_wrapper.py… does not copy src/payload/scripts/github_api/ to scripts/github_api/` |
| R1 | rewritten test still holds Part 6.2 | package bullet deleted | RT S | FAILED-TO-REFUTE | `1 failed`: `the top-level bullet that copies … does not copy …`; `section does not name src/payload/scripts/github_api/` |
| R2 | `--limit` 0 and below print nothing | `if args.limit <= 0` guard deleted | RT C -k "limit-of-zero or negative-limit" | FAILED-TO-REFUTE | `2 failed`: `the standard output differs from the golden` |
| R2 | non-UTF-8 credential exits 2 | `_one_token` try/except deleted | RT C -k credential-not-utf-8 | FAILED-TO-REFUTE | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x93 in position 0` |
| R2 | same | decode with `errors="ignore"` | same | FAILED-TO-REFUTE | `exit code 0, the golden is 2; stdout '{\n  "number": 5, …'` |
| R3 | non-integer rate header: plain error, no retry | `_integer_header` reads a non-integer as 0 | RT T -k non_integer_rate_limit_header | FAILED-TO-REFUTE | `6 failed`: `GitHubRateLimitError … still applied after 3 retries` |
| R3 | same | `_rate_limit_of` `except ValueError` returns a 0 s retry-after limit | same | FAILED-TO-REFUTE | `6 failed`: same, `waiting 0.0 seconds before retry 1 of 3` |

Vacuity: Grep `skip|xfail|deselect|assert True|pytest\.mark\.|#\s*assert|^\s*pass$` over the three changed test files
matches only `parametrize`; every new test is killed above. The `credential-not-utf-8` row routes the issue, and the
`errors="ignore"` kill shows the bytes reach `credentials/github-pat.txt`. The row carries no `log` expectation, like
the existing `credential-refused` rows. The three new rows are not `c_only`, so P runs them on the fork too.

Existing rows: the fixture diff changes no existing row's argv, stdout, exit code or routes (the first `list-issues`
row's route moved into `open_issues`, the same `ListRouteSpec` arguments); `Project.build` still writes `str` content
as `content.encode(encoding="utf-8")`. RT S T C P: `539 passed` before the first mutant and after the last restore.

Coverage: the R2/R3 lines (the `--limit` guard, `_one_token`'s `except UnicodeDecodeError`, `_rate_limit_of`'s
`except ValueError`) run under their tests: mutating each flips the test's verdict.

Tree: restored; `tmp/` empty, no `.coverage`; the only change is this section.

Verdict: VERIFIED
