# Refutation report 2: issue #41 rework-1 delta, HEAD 2e96a8d

Tree: worktree `.claude/worktrees/issue-41`, branch `issue-41-gitlab-generic-operation-command`, PR #49, HEAD 2e96a8d,
`git status --porcelain` empty at the start. Scope: the delta ca4e2d7..2e96a8d, which closes the two refutations of
`refutation-report.md` (AC-1.5 empty-body clause; Requirement 2 / design D4 row 1). A disposable driver in the
worktree's `tmp/` (deleted) applied each mutant to `src/payload/scripts/gitlab_api/commands/call.py` as an exact byte
replacement on the CRLF working copy (anchor found once each), checked sha256 against the baseline before every
mutant and after every restore, deleted any `call.*.pyc` before each run (none was present), and ran only K
(`src/payload/test/test_gitlab_api_call.py`) through `scripts/run_tests.py`.

## Claims

| # | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green at the tree's SHA | wrapper `list-runs --limit 6`, `get-run 42966169391` (head_sha = HEAD 2e96a8d, PR #49), `wait-run 42966169391 --timeout-seconds 540` (exit 0), `get-jobs`, `get-job-logs 130343804921` | FAILED-TO-REFUTE: success, all five jobs success; 2565 + 1053 passed, 0 failed; 2565 = 2557 at ca4e2d7 + the 8 new cases | full-suite-2.txt |
| 2 | AC-1.5: an empty body under a JSON `Content-Type` writes nothing | mutant W2-empty-body (`if not response.body: return` removed from `print_response`), K only | FAILED-TO-REFUTE: killed, 2 failed / 65 passed: `[empty-204-json-content-type]` and `[empty-200-json-content-type]`, each `AssertionError ... assert 'null\n' == ''` | mutant-rework-1.txt |
| 3 | Requirement 2 / D4 row 1: text with no `=` is argparse's usage error, exit 2, no request | mutant split-no-equals (`_split`'s no-`=` raise replaced by `pass`), K only | FAILED-TO-REFUTE: killed, 3 failed / 64 passed: `raw-field-` (exit 0, request sent), `path-` (exit 1, empty path segment), `query-without-an-equals-sign` (exit 1), each an `AssertionError` on the exit code | mutant-rework-1.txt |
| 4 | Requirement 2 / D4 row 1: an empty name is argparse's usage error | mutant split-empty-name (`_split`'s empty-name raise replaced by `pass`), K only | FAILED-TO-REFUTE: killed, 3 failed / 64 passed: `path-`, `raw-field-`, `query-with-an-empty-name`; the call falls through to D4's refusal (exit 2, logged), and the test's `usage:` assertion fails (`AssertionError: standard error holds no usage`) | mutant-rework-1.txt |
| 5 | Green after restore | K on the restored tree | FAILED-TO-REFUTE: 67 passed; call.py sha256 equals the baseline | green-restored-2.txt |
| 6 | Every line of `call.py` runs under K | `run_tests.py --coverage` on K alone | FAILED-TO-REFUTE: `call.py` 179 statements, 0 missed, 100% (lines 150 and 152 now executed); CI tests leg agrees (log line 550, 179 / 0 / 100%) | coverage-2.txt, full-suite-2.txt |
| 7 | Every new test line runs | same coverage run | FAILED-TO-REFUTE: K's 3 missed lines are 65, 417, 1786, the unchanged defensive returns that were 64, 415, 1669 at ca4e2d7 (same text); the added hunks are lines 16-17, 155, 1060-1076, 1680-1777 | coverage-2.txt |
| 8 | The rework changes no other case's meaning | `git diff ca4e2d7..2e96a8d -- src`; `git diff -U0` hunk headers; Grep of the definitions | FAILED-TO-REFUTE: one file, +118 / -1; the one removed line is the module docstring's refusal bullet, restated over two lines; additions are the constant `RAW_FIELD_OPTION_NAME`, two rows appended to `test_a_json_or_empty_body_prints_as_documented`'s parameter list (the function body and the existing rows unchanged), and the new `MalformedCase`, constants, `argument_named` and `test_a_malformed_argument_is_refused_without_its_value`; every new module-level name is defined once, so nothing earlier is shadowed; no product file changed | - |
| 9 | Vacuity in the delta | Grep of K for marks, skip, xfail, deselect, commented tests; CI log | FAILED-TO-REFUTE: the only mark is `parametrize`; both new tests assert exit code, request list, standard output and standard error; CI log holds no skipped, xfail or deselected test (line 633 `0 skipped` counts checks) | full-suite-2.txt |
| 10 | Red for the right reason | rework-1 has no red capture: its tests were written against the finished implementation; the three mutant runs above are the falsification | FAILED-TO-REFUTE: all 8 failures are `AssertionError` in the test body; no collection or import error | mutant-rework-1.txt |
| 11 | The rest of the delta | `git diff --word-diff=porcelain` of tasks.md; diff of decision-log.md | FAILED-TO-REFUTE: tasks.md changes 14 `[ ]` to `[x]` and nothing else; decision-log.md appends DL-005 only | - |

## Refutations

None. Both refutations of `refutation-report.md` are closed: AC-1.5's empty-body clause by row 2, Requirement 2 /
design D4 row 1 by rows 3, 4 and 6. Claims of `refutation-report.md` outside the delta are not re-graded; the delta
touches no product file (row 8), and CI's full suite at 2e96a8d is green (row 1).

## Notes

- CI run 42966169391 checks out `refs/remotes/pull/49/merge`, f4771ae = 2e96a8d merged into f374b3d (log line 129).
  origin/main has since gained the merge of PR #48 (run 42966474822, in progress at reading); that commit is not part
  of this tree.
- The empty-name mutant shows why K asserts argparse's `usage:` line: without `_split`'s check the call is still
  refused with exit 2 by D4, so an exit-code-only test would have let it survive.

## Tree restored

`call.py` was written back from its saved bytes after every mutant; sha256 cd54a95f... equal to the baseline after
each restore and at the end. The `.pytest_cache` files were written back from their saved bytes; the one new ignored
file (`.coverage`) was deleted; no `call.*.pyc` remains; the driver and the saved CI log were deleted, and `tmp/` is
empty as found. `git diff --stat` is empty and HEAD is 2e96a8d; `git status --porcelain` shows only the new captures
`evidence/verify/mutant-rework-1.txt`, `green-restored-2.txt`, `coverage-2.txt`, `full-suite-2.txt` and this report.
No `.kiro/` path was touched; no code or test was edited.

Verdict: VERIFIED
