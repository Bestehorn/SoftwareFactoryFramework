# Refutation report 2: issue #32, delta re-verification after rework-1

Subject: branch `issue-32-issues-pulls-records`, HEAD 8e80256, PR #48. The delta is `git diff 234772e..8e80256 -- src`:
one file, K = `src/payload/test/test_github_api_call.py` (17 insertions, 6 deletions). The first pass
(`refutation-report.md`) REFUTED AC-6 because M06 and M06b survived. H = a disposable harness in the worktree's
`tmp/` (absent before this run, deleted after it). For each mutant H checked that `commands/call.py` hashed to the
first-pass original, replaced one line as bytes (CRLF kept), required the mutated sha256 to EQUAL the mutated sha256
the first pass recorded for that mutant, ran K through `scripts/run_tests.py`, restored the original bytes in a
`finally` and re-hashed. No `git checkout` and no `git stash` was used. Captures are under `evidence/verify/`.

| # | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the pushed head | wrapper `list-runs --limit 6` (newest: 42964842191, `in_progress`), `wait-run 42964842191 --timeout-seconds 540` (exit 0), `get-run`, `get-jobs`; `git rev-parse HEAD` in the worktree | `completed`/`success`; `head_sha` = worktree HEAD 8e80256; jobs verify (security), verify (lint), verify (types), verify (tests) and report all `completed`/`success`: FAILED-TO-REFUTE | full-suite-2.txt |
| 2 | The mutants are the first pass's, byte for byte | H: sha256 of `call.py` at HEAD, of each mutated file | HEAD file = first-pass original; M06 mutated = first-pass M06 mutated; M06b mutated = first-pass M06b mutated (`mutated equals the first-pass mutant: True` in both headers): FAILED-TO-REFUTE | mutant-rework-1-M06.txt, -M06b.txt |
| 3 | AC-6 / DL-007: the refusal ends ", which sends it" for `pulls/merge` and `issues/create` and not for `pulls/merge-async` | H M06 (`ending = SENDS_IT if operation_id in GATED_NOT_SENT else ""`), K | KILLED, exit 1: 3 failed, 39 passed: `pulls-merge-is-merge-pr`, `pulls-merge-async-is-merge-pr`, `issues-create-is-create-issue`, each an `AssertionError` in `fx.assert_log`: FAILED-TO-REFUTE | mutant-rework-1-M06.txt |
| 4 | same | H M06b (`GATED_NOT_SENT = frozenset()`), K | KILLED, exit 1: 1 failed, 41 passed: `pulls-merge-async-is-merge-pr`, `AssertionError` in `fx.assert_log` (message `...use the merge-pr subcommand, which sends it`): FAILED-TO-REFUTE | mutant-rework-1-M06b.txt |
| 5 | Restore re-confirms green | H: re-hash after each `finally`, then K | restored = original after both mutants; K 42 passed, exit 0: FAILED-TO-REFUTE | green-after-restore-2.txt |
| 6 | The rework changes no other case's meaning | read of `git diff 234772e..8e80256 -- src`; Grep of K for `SENDS_IT`, `lacking(` | the 6 removed lines are 3 docstring lines (2 in `_gated_cases`, 1 in `test_a_gated_operation_names_its_subcommand`) and the `patterns=` lines of the three gated cases, each re-added with its two original patterns unchanged plus one; slugs, argv and criterion of those cases are unchanged; `SENDS_IT` and `lacking` are used only in those three cases; no other case, fixture or helper is in the diff; `commands/call.py` is not in the diff (last changed in eb63d18): FAILED-TO-REFUTE | none (inspection) |
| 7 | Vacuity of the delta | read of the diff; `fx.assert_log` in `github_wrapper_fixtures.py` | no skip, xfail, deselect or commented-out test added; `assert_log` requires ONE record to match every pattern (`any(all(...))`), so `lacking` is judged on the same record that names the ID and `merge-pr`; `lacking` passes on the true message (row 5) and fails on the one holding the text (rows 3-4), so it is not vacuous: FAILED-TO-REFUTE | as rows 3-5 |
| 8 | Red for the right reason | read of the mutant captures | every failure is an `AssertionError` raised by `assert_log` with the logged message quoted; no collection, import or load error: FAILED-TO-REFUTE | as rows 3-4 |
| 9 | Coverage of the changed lines (first-pass row 24) | rows 3-4 | `GATED_NOT_SENT` is pinned by M06b; the `ending` line by M06; `SENDS_IT` by K's `pulls-merge-is-merge-pr` and `issues-create-is-create-issue`, which M06 shows reject the message without the ending (`...use the merge-pr subcommand`, the message an emptied `SENDS_IT` gives): FAILED-TO-REFUTE | mutant-rework-1-M06.txt |

## Outcome for the first pass's refutation

The first pass refuted AC-6 because K matched only the quoted ID and the subcommand name. K now also requires
`which sends it` for `pulls/merge` and `issues/create` and its absence for `pulls/merge-async`. The same two mutant
files, reproduced to the recorded sha256, now fail K (3 and 1 failures), so the behaviour DL-007 added is pinned. No
code or test was changed by this verification.

## Tree

`commands/call.py` hashes to its original after both mutants. The harness directory `tmp/` is deleted (it did not
exist before this run). `git diff --stat HEAD` is empty, and `git status --porcelain` shows only the untracked
captures `full-suite-2.txt`, `green-after-restore-2.txt`, `mutant-rework-1-M06.txt`, `mutant-rework-1-M06b.txt` and
this report under `evidence/verify/`.

Verdict: VERIFIED
