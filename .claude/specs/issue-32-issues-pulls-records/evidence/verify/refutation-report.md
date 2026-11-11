# Refutation report: issue #32 (tier S, one wave)

Subject: branch `issue-32-issues-pulls-records`, HEAD 234772e, PR #48, on origin/main f374b3d (holds #27). Diff:
`git diff origin/main...HEAD`. H = the disposable harness `tmp/issue32_verify/mutants.py` (main checkout, deleted
after the run). Each mutant replaced one text in one file, ran the named paired tests through `scripts/run_tests.py`,
restored the original bytes in a `finally`, and checked sha256 (original = restored on every mutant, recorded in each
capture header). No `git checkout` and no `git stash` was used. Captures are under `evidence/verify/`. Paired set P17 =
the six F files, K, G, `test_dispatcher.py`, C, N, P, V, `test_github_api_call_properties.py`,
`test_wrapper_delivery.py`, `test_github_api_repos.py` and `test_github_api_git.py`.

| # | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the pushed SHA | wrapper `wait-run 42960788592` (exit 0), `get-run`, `get-jobs` | `completed`/`success`, head_sha = HEAD; verify (security, lint, tests, types) and report all `success`: FAILED-TO-REFUTE | full-suite.txt |
| 2 | P17 green at HEAD, the DL-008 rebase resolution included | H `green --label baseline` | 814 passed, 0 skipped: FAILED-TO-REFUTE | green-baseline.txt |
| 3 | AC-3/AC-4: `search/code` item key `items` | H M01 (`item_key` set to None) | KILLED: F search structural + paged `search/code` (exit 1): FAILED-TO-REFUTE | mutant-wave-1-M01.txt |
| 4 | AC-3/AC-4: `search/*` paging | H M02 (`search/commits` LINK set to NONE) | KILLED: structural + paged case (stdout differs): FAILED-TO-REFUTE | mutant-wave-1-M02.txt |
| 5 | AC-3: `issues/get-issue-artifact` NONE (DL-004) | H M03 (set to LINK) | KILLED: F issues structural: FAILED-TO-REFUTE | mutant-wave-1-M03.txt |
| 6 | AC-2: `pulls.PENDING` = {`pulls/update-branch`} | H M04 (emptied) | KILLED: F pulls pending + V coverage: FAILED-TO-REFUTE | mutant-wave-1-M04.txt |
| 7 | AC-6: `pulls/merge-async` gated | H M05 (entry removed) | KILLED: K `pulls-merge-async-is-merge-pr`: FAILED-TO-REFUTE | mutant-wave-1-M05.txt |
| 8 | AC-6 / DL-007: the merge-async refusal omits ", which sends it"; the others keep it | H M06 (`ending` condition inverted), targeted, then `--full` on P17 | SURVIVED: 367/367, then 814/814 passed: REFUTED | mutant-wave-1-M06.txt, -M06-full.txt |
| 9 | same | H M06b (`GATED_NOT_SENT` emptied), targeted, then `--full` | SURVIVED: 367/367, then 814/814 passed: REFUTED | mutant-wave-1-M06b.txt, -M06b-full.txt |
| 10 | DL-008 / UB-2: membership test keeps #27's `None` refusals | H M07 (`refuse_gated` reverted to `.get(...)`, so `None` returns) | KILLED: all 7 (`repos/merge`, `merge-upstream`, `rename-branch`, `create-or-update-file-contents`, `delete-file`, `git/create-ref`, `git/update-ref`): FAILED-TO-REFUTE | mutant-wave-1-M07.txt |
| 11 | AC-7: `CREATE_RE` lookarounds | H M08 (lookarounds removed) | KILLED: G `call-create-issue-artifact`: FAILED-TO-REFUTE | mutant-wave-1-M08.txt |
| 12 | UB-5: quoted create word still blocked | H M09a (lookbehind + `"`), M09b (lookahead + `"`) | KILLED: G `quoted-create-word` (both): FAILED-TO-REFUTE | mutant-wave-1-M09a.txt, -M09b.txt |
| 13 | AC-3/AC-4: reactions, activity, gists paging | H M10, M11, M12 (one LINK record each set to NONE) | KILLED: structural + paged case in each F: FAILED-TO-REFUTE | mutant-wave-1-M10/M11/M12.txt |
| 14 | AC-1: body names are the section's | H M13 (`bypass_rules` dropped from `pulls/merge-async`) | KILLED: N `test_every_record_matches_its_reference_section`: FAILED-TO-REFUTE | mutant-wave-1-M13.txt |
| 15 | AC-1/AC-5: method and query names | H M14 (`pulls/update-review` PUT set to PATCH), M15 (`head` dropped from `pulls/list`) | KILLED: both N tests, each: FAILED-TO-REFUTE | mutant-wave-1-M14.txt, -M15.txt |
| 16 | Vacuity | Grep of the 8 changed test files for skip/xfail/deselect/importorskip/commented tests; read of each new test body | none found; every new test asserts, directly or through `run_product_case`/`assert_log`/`assert_block`; F tables (IDs, paths, item keys) are literals, never read from records: FAILED-TO-REFUTE | none (inspection) |
| 17 | Red for the right reason | Read/Grep `evidence/red/wave-1.txt` | 77 failed, 128 passed; every failure is an `AssertionError` (exit 2 against golden 0 with "No GitHub operation record declares", PENDING/structural sets, merge-async log, gate block); no collection or import error: FAILED-TO-REFUTE | evidence/red/wave-1.txt |
| 18 | Records match their sections (spot-check, 15) | Grep of `rest/{pulls,issues,search,reactions,activity,gists}.md` and `conventions.md` | match: pulls/merge-async, get-merge-async-result, list-requested-reviewers, request-reviewers; issues/create-issue-artifact, get-issue-artifact, list-for-org, lock; search/issues-and-pull-requests; reactions/list-for-issue; activity/list-stargazers-for-repo, mark-thread-as-done; gists/list-comments, update. Only `issues/get-issue-artifact` (`versions`) and `search/*` (`items`) of the six families are in the item-key table: FAILED-TO-REFUTE | none (inspection) |
| 19 | UB-1: existing records, `CASES`, compat commands unchanged | full family/command diff in tmp, Grep of removed lines; C and P in P17 | removed lines are only docstrings, the old `PENDING` sets, `OPERATIONS = ()`, and the closing bracket moved by appended records; `pulls.py` gains a type annotation; fixtures and `commands/{issues,claim,pulls,ci}.py` are not in the diff: FAILED-TO-REFUTE | green-baseline.txt |
| 20 | UB-2 | K (existing gated cases, pending `pulls/update-branch`, unknown ID) in P17; M07 | green; M07 killed: FAILED-TO-REFUTE | green-baseline.txt |
| 21 | UB-3 | C credential test, V stdlib test in P17 | green: FAILED-TO-REFUTE | green-baseline.txt |
| 22 | UB-4 | `git diff --stat` of `gitlab_wrapper.py`, `test_wrapper_delivery.py` | empty; `test_wrapper_delivery.py` green in P17: FAILED-TO-REFUTE | green-baseline.txt |
| 23 | UB-5 | G existing block cases in P17; M09a/b | green; killed: FAILED-TO-REFUTE | green-baseline.txt |
| 24 | Coverage of the change | rows 3-15 | every changed code line is under a killing test, except `GATED_NOT_SENT`, `SENDS_IT` and the `ending` line of `refuse_gated` (rows 8-9): REFUTED (AC-6) | as rows 8-9 |

## The refutation (AC-6, DL-007)

`commands/call.py` adds `GATED_NOT_SENT`, `SENDS_IT` and
`ending = "" if operation_id in GATED_NOT_SENT else SENDS_IT`. DL-007 accepts them so the `pulls/merge-async` refusal
does not say that `merge-pr` sends it. Inverting the condition (every gated ID with a subcommand then gets the
opposite ending) or emptying `GATED_NOT_SENT` leaves all 814 paired tests and the targeted 367 green. K's
`pulls-merge-async-is-merge-pr` (and `pulls-merge-is-merge-pr`, `issues-create-is-create-issue`) match only the
quoted ID and the subcommand name, so no test separates the true refusal text from the false one. AC-6's literal
outcome (exit 2, no request, log naming `pulls/merge-async` and `merge-pr`) holds under both mutants. What no test
pins is the behaviour these changed lines exist for. No code or test was changed by this verification.

## Tree

Every mutant was restored byte for byte (sha256 original = restored, all 19 mutant runs). After all restores, P17 passed
again: 814 passed (green-after-restore.txt). `git diff --stat HEAD` is empty, and `git status --porcelain` shows only
the untracked `evidence/verify/` holding this report and the captures. The harness and its tmp diff are deleted.

Verdict: REFUTED (AC-6)
