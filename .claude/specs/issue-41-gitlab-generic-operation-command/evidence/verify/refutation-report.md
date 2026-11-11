# Refutation report - issue #41 (tier M, four waves), HEAD ca4e2d7

Tree: worktree `.claude/worktrees/issue-41`, branch `issue-41-gitlab-generic-operation-command`, PR #49. Each mutant was
applied byte for byte (the file's CRLF kept) by a disposable driver in the worktree's `tmp/` (deleted); only its paired
tests ran, through `scripts/run_tests.py --tb=line`; the saved bytes were written back and the sha256 of all nine
touched files compared with the pre-run baseline before and after every mutant.

## Claims

| # | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green at the tree's SHA | wrapper `wait-run`, `get-run`, `get-jobs`, `get-job-logs`: run 42961275618, head_sha = HEAD ca4e2d7 | FAILED-TO-REFUTE: success; 2557 + 1053 passed, 0 failed | full-suite.txt |
| 2 | Wave 1: R and T need the registry and transport additions | W1-revert (10 failed), send-guard, send-query, variables-connection, variables-regex, attribute-name, is-json | FAILED-TO-REFUTE: 7/7 killed | mutant-wave-1.txt |
| 3 | Wave 2: K, H, N need `call.py` | W2-remove: `call.py` deleted, `_common.py` as on origin/main; 62 failed; the 9 passing are tasks.md 2.3's green-by-design N helpers and the reference-section test, killed in row 4 | FAILED-TO-REFUTE | mutant-wave-2.txt |
| 4 | Targeted mutants | 22 on `call.py`/`_common.py` (gated refusal off, no `parse_constant`, `-F` unparsed, `check_parameters` accepting, `--query` not narrowed, documented text dropped, missing-path off, `attribute_name` dropped x2, ARRAY query, project default, page join, bytes path, line end added, shape pre-check off, `except Exception`, message dropped, `EXIT_REFUSED=1`, `file_member` text, GraphQL variables dropped, `--token` added, `os.environ` text); N-combo (tasks.md), N `call_problems` [], N `record_problems` []; FAM-param (`plan.py` `internal` as QUERY) | FAILED-TO-REFUTE: 26/26 killed | mutant-wave-2.txt |
| 5 | AC-1.5: an empty body writes nothing | W2-empty-body: `if not response.body: return` removed from `call.print_response` | **REFUTED**: survived, 70 passed (K + N) | mutant-wave-2.txt |
| 6 | Wave 3 | W3-revert, drop-one ("Design uploads"), V-combo (tasks.md), V `coverage_gaps` [], `family_problems` [], `capability_problems` [], `only_in_graphql` [], FAM-path (`plan.py` `.../note`) | FAILED-TO-REFUTE: 8/8 killed | mutant-wave-3.txt |
| 7 | Wave 4 | W4-revert: `gitlab_wrapper.py` as on origin/main | FAILED-TO-REFUTE: killed | mutant-wave-4.txt |
| 8 | Green after restore | union of the four Run lines | FAILED-TO-REFUTE: 383 passed | green-restored.txt |
| 9 | Vacuity (K, R, T, C, H, N, V, fx) | diff scanned for skip, xfail, importorskip, deselect, marks, commented tests; every new test read | FAILED-TO-REFUTE: marks are `parametrize` and `usefixtures` only; every test asserts; CI log: 0 skipped, no xfail or deselect | full-suite.txt |
| 10 | Red for the right reason | `evidence/red/wave-1..4.txt` read whole | FAILED-TO-REFUTE: wave 1 AttributeError/TypeError raised in the test body (tasks.md admits it); waves 2-4 AssertionError; no collection error | evidence/red/ |
| 11 | Every new line is exercised | `run_tests.py --coverage` on K H N R T; CI tests-leg coverage | **REFUTED**: `call.py` 150 and 152 run in no test, locally and in CI's full suite | coverage.txt, full-suite.txt |
| 12 | F.2 | `git diff --name-only origin/main...HEAD` | FAILED-TO-REFUTE: no UB-3.1 file; product and test files are D8's table; outside D8 only the spec directory and one `docs/findings-ledger.md` row (committed with its change, issue-filing-discipline.md); delivery suite green (rows 1, 8) | - |
| 13 | F.3 | `git diff` of C, P, R, T, V | FAILED-TO-REFUTE: C +26/-0 (`USAGE_CALL_TEXTS`, `test_the_usage_names_the_operation_call`); P absent; R +112/-0; T's one removed line is module docstring; V's is the `typing` import; no existing test line changed; C config/env and P std-lib tests green (rows 1, 8) | - |
| 14 | F.4 | map bullet read; `test_llm_map_within_cap` | FAILED-TO-REFUTE: D7's two sentences verbatim before "Not installed here: ...", which stays last; cap test passed | green-restored.txt |

## AC/UB -> killing mutant

AC-1.1 gated, W2-remove (N every record sent), FAM-param; AC-1.2 send-query, send-guard, project default; AC-1.3
`-F` unparsed (H fails), no `parse_constant`, `file_member`, attribute-name, ARRAY query; AC-1.4 page join; AC-1.5
is-json (JSON half), empty half REFUTED (row 5); AC-1.6 bytes path, line end; AC-1.7 `except Exception`; AC-1.8
project default, missing-path; AC-1.9 GraphQL variables, variables-connection; AC-2.1 message dropped,
`EXIT_REFUSED=1`; AC-2.2 `check_parameters` accepting, `--query` narrowing, documented text, variables-regex; AC-2.3
missing-path; AC-2.4 shape pre-check; AC-3.1 N-combo; AC-3.2 N `call_problems` [], `record_problems` []; AC-4.1
W4-revert; AC-4.2 F.4 inspection and cap test; AC-5.1, AC-5.2 inspection: D6 names gitlab-org/gitlab@a186442, the pin
on line 1 of `operations-index.md`; AC-5.3 V `family_problems` [], `coverage_gaps` [], FAM-path; AC-6.1 V
`coverage_gaps` [] (route-prefix test); AC-6.2 V `capability_problems` [], `only_in_graphql` [], drop-one; AC-6.3
drop-one, W3-revert; UB-1.1 F.3 and C green; UB-2.1 `--token` and C green; UB-2.2 `os.environ`; UB-3.1 F.2 and
delivery green.

## Refutations

**AC-1.5, empty-body clause.** Without the empty-body check, `print_response` sends an empty body under a JSON
`Content-Type` to `print_json(value=response.value)`; `transport.Response.value` returns `None` for an empty body, so
standard output is `null` and a line end where AC-1.5 requires nothing. No test notices: K
`test_a_json_or_empty_body_prints_as_documented[empty-204]` serves its 204 with no `Content-Type`, where
`print_bytes(b"")` also writes nothing; K `test_an_operation_call_sends_its_record[delete-one-encoded-segment]` serves a
204 with `Content-Type: application/json` and an empty body but asserts nothing about standard output. Missing: an
empty-body case under a JSON `Content-Type` that asserts empty standard output.

**Requirement 2, design D4 row 1 (a malformed `NAME=VALUE` exits 2 before any request).** `call._split` raises
`ArgumentTypeError` for text with no `=` (line 150) and for an empty name (line 152); no test executes either line
(coverage.txt; CI tests-leg coverage, full-suite.txt log line 548). Without line 150, `-f title` would send `title` as an
empty string. Missing: K cases `-f title` and `-f =x` asserting exit 2, argparse's usage message and no request.

## Notes

- W1-send-guard failed its test with `AttributeError` from `registry.encode` on the GraphQL record instead of
  `ValueError`; the test fails either way, so the mutant is killed.
- tasks.md at ca4e2d7 leaves 2.1-4.3 and F.1-F.4 unticked; ticks are the orchestrator's.

## Tree restored

Every mutant's files were written back from their saved bytes; sha256 equal to the baseline after all 44 mutants and
at the end (`baseline drift: none`). The driver, its baseline and the saved CI log were deleted; `tmp/` is empty as
found; no `.coverage` file remains. `git status --porcelain` shows only `?? .../evidence/verify/`; `git diff --stat` is
empty; HEAD is ca4e2d7. No `.kiro/` path was touched.

Verdict: REFUTED (AC-1.5, Requirement 2 / D4 row 1)
