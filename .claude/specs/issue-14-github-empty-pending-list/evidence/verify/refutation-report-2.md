# Refutation report, round 2 (delta): issue #14, the last three GitHub pending operations (tier S)

Tree: worktree `.claude/worktrees/issue-14`, branch `issue-14-github-empty-pending-list`, PR #64, HEAD 0ffd759 = rework
a65fe83 + merge of origin/main 252c21e. Scope: the delta since round 1 (`refutation-report.md`: REF-1 UB-3, REF-2 AC-1,
one observation). CI read through `scripts/github_wrapper.py` from the main checkout. Local runs:
`scripts/run_tests.py -p no:cacheprovider --color=no <files>` in the worktree. Mutant set (109 tests): F (pulls,
code_scanning, copilot), K, R. Paired set (137): those plus N, V. Each mutant capture holds `git status`, the mutant's
`git diff`, the complete pytest output, the restore and a `sha256sum -c` of the five implementation files.

## The five steps

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Suite green on 0ffd759 | `list-runs --limit 3`, `get-run 43035112486`, `wait-run 43035112486 --timeout-seconds 540`, `get-jobs 43035112486` | FAILED-TO-REFUTE: head_sha = HEAD, completed/success, 5 of 5 jobs success | round2-full-suite.txt |
| S0 | Rework changed no product file; merge changed no GitHub file | `git diff cf17ede a65fe83 --name-only -- src/payload/scripts prompts clients templates src/hooks`; `git diff a65fe83 0ffd759 --name-only`, then filtered to the GitHub paths | FAILED-TO-REFUTE: rework = the 3 F files, `docs/lessons-learned.md`, this spec's files; merge = #40's spec, `docs/`, `gitlab_api/`, `gitlab_wrapper.py`, GitLab tests; GitHub filter empty | round2-delta-scope.txt |
| S2 | Each new test kills the mutant it answers | 10 mutants, table below | FAILED-TO-REFUTE: 9 killed, 1 equivalent | round2-mutant-*.txt |
| S3 | No vacuous new test | Grep `skip\|xfail\|importorskip\|deselect\|pytest.mark.\|# def test_\|# assert` on the 3 F files; read of the 4 new tests | FAILED-TO-REFUTE: only `parametrize` marks, none on a new test; every new test asserts (one record for a literal ID and its two fields; exit 2, empty stdout, log patterns naming the ID and `enterprise` as a path parameter; `pytest.raises(ValueError)`, a message regex naming `sort` as a query parameter, `sent == []`); all 4 PASSED by name under `-v` | round2-baseline-green.txt |
| S4 | Each kill fails for the right reason | read of every failing test in the captures | FAILED-TO-REFUTE: `AssertionError` on the field values (M5-M8); the fake host's `no route for PUT .../content_exclusion[?sort=name]`, the request the test forbids (M1-M3, M9, M10); an uncaught `ValueError` where exit 2 is required (M10, query case); no collection or import error. The rework has no red capture: its tests pin code that was already green, and the mutants are its red | round2-mutant-*.txt |
| S5 | Round 1's unpinned lines are pinned | M1-M3 (the `_check_names` guard), M6-M8 (commit-autofix `item_key=None`, both `content_type` defaults), M9 (`_undocumented`'s `path =` line) | FAILED-TO-REFUTE: each killed by a new test; the delta adds no product line | as below |
| UB-5 | After the merge the PR names neither `gitlab_wrapper.py` nor `test_wrapper_delivery.py` | `git diff 252c21e 0ffd759 --name-only -- <both files>`; the same `-- src test` | FAILED-TO-REFUTE: empty; the PR's `src`/`test` files are the 5 GitHub implementation files and 4 GitHub test files | round2-delta-scope.txt |
| G | Green before and after | paired set at HEAD; again after the last restore, with 8 sha256 checks (5 implementation, 3 F) | 137 passed both times; 8 OK; `git diff --stat HEAD` empty | round2-baseline-green.txt, round2-green-after-restore.txt |

## Mutants

| Id | Answers | Mutation | Result (of 109) | Killed by | Capture (round2-mutant-) |
|---|---|---|---|---|---|
| M1 | REF-1, round 1 Q6 | `_check_names` returns early for every kind when `operation.body_params` holds `*` | KILLED, 1 failed | copilot F `test_the_registry_refuses_the_content_exclusion_query`: `PUT ...?sort=name` sent | registry-every-kind |
| M2 | REF-1, near | `send` skips its query `_check_names` call for a `*` record | KILLED, 1 | same test, same request | registry-send-skips-query |
| M3 | REF-1, near: return keyed on `documented` for query | also returns early for a query whose `documented` is empty | KILLED, 3 (+2 teardown errors) | same test; R `test_call_refuses_an_undocumented_parameter` [body-name-sent-as-query], [path-name-sent-as-query] | registry-empty-query-documented |
| M4 | REF-1, round 1 Q1 | returns early when `documented` holds `*`, whatever the kind | equivalent, 109 passed: the one `"*"` in `github_api/` records is copilot's `body_params` (Grep) | none; not graded | registry-keyed-on-documented |
| M5 | REF-2, round 1 R4 widened | `item_key="items"` and `content_type` octet-stream on both branch writers | KILLED, 3 | code_scanning F and pulls F `test_the_branch_writing_record_has_no_item_key_and_no_content_type`; pulls F transcription (`item_key`) | records-both-fields |
| M6 | REF-2, near | `content_type` on `pulls/update-branch` only | KILLED, 1 | pulls F new test | update-branch-content-type |
| M7 | REF-2 | `item_key="items"` on `code-scanning/commit-autofix` only | KILLED, 1 | code_scanning F new test | autofix-item-key |
| M8 | REF-2, near | `content_type` on `code-scanning/commit-autofix` only | KILLED, 1 | code_scanning F new test | autofix-content-type |
| M9 | observation, round 1 Q4 | `_undocumented` skips the path names of a `*` record | KILLED, 1 | copilot F `test_the_content_exclusion_call_checks_its_path`: PUT sent | call-any-body-skips-path |
| M10 | observation + UB-3, round 1 Q2 | `_undocumented` skips the path and query names of a `*` record | KILLED, 2 | copilot F `test_the_content_exclusion_call_checks_its_query`, `..._checks_its_path` | call-any-body-skips-path-and-query |

`item_key` alone on `pulls/update-branch` did not get its own run: M5 shows that pulls F
`test_the_records_follow_the_transcription_rules` already fails on it (round 1 R3).

## Refutations

None. REF-1 is answered: with the query check of the `*` record removed from `registry` (M1, M2, M3), `registry.send`
sends the undocumented query name, and the new copilot F registry test fails. REF-2 is answered: each of the three
unnamed field lines (M6, M7, M8) fails one new branch-writer test. The observation is answered: M9 fails the new
copilot F path test.

## Tree restored

`git checkout --` restored each mutated file after its run. Every capture's `sha256sum -c` reports OK for the five
implementation files against the digests taken before M1, and round2-green-after-restore.txt adds the three F test
files. `git status --porcelain` shows only the new `round2-*.txt` captures and this report. No tmp/ file, no `.kiro/`
path, no commit.

Refuted ids: none
VERIFIED
Verdict: VERIFIED
