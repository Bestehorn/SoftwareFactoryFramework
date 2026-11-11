# Refutation report: issue #30 (PR #56, head f3bc2b4, base 52403f8)

Mutations ran in the issue-30 worktree and were restored from byte backups; after each restore `sha256sum -c` printed OK for all six mutated files (CRLF kept). Whole-wave reverts ran in a throwaway detached worktree under `tmp/`, removed after use. Only named test files ran, via `scripts/run_tests.py`; no local full suite. Letters as in `tasks.md`.

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Suite green on the pushed SHA | wrapper `get-run`/`get-jobs`/`get-logs` 42982391700 | FAILED-TO-REFUTE: completed/success, `head_sha` = worktree HEAD; 5 jobs success; 2977 + 1053 passed on merge 3008f4c (f3bc2b4 into its merge base 52403f8) | full-suite.txt |
| W1 | Wave 1's tests kill its implementation | R+V | FAILED-TO-REFUTE: 1a `declared_variables` keeps `after` (1 failed); 1b duplicate ID accepted (1); 1c V index check removed (1); 1d no white space before `:` (2); 1e V counts capabilities (3); 1w registry.py at c6451cd (6); restored 43 passed | mutant-wave-1.txt |
| W2 | Wave 2's tests kill its implementation | G+Q+V+R | FAILED-TO-REFUTE: 2a member renamed (1); 2b input type (1); 2d capability text (5); 2e record removed (1); 2f transferIssue ungated (1); 2g `merge-pr` to None (1); 2h `GATED_NOT_SENT` entry removed (1); 2i `--query` passed (1); 2j undeclared variable passed (2); 2k gated record sent, then refused (4); 2m paging branch inverted (15); 2w wave-2 files at 52a5a51 (33); restored 78 passed | mutant-wave-2.txt |
| M2c | D1's `{ clientMutationId <selection> }` is tested (task 2.3; AC-1.1 via Q `test_every_record_matches_the_reference`) | G+Q+V+R, `clientMutationId` cut from `_mutation` | REFUTED: 78 passed, exit 0 | mutant-wave-2.txt "2c" |
| M2l | `graphql_call` refuses an undeclared variable (task 2.5) | G+Q+V+R, that refusal cut | REFUTED: 78 passed, exit 0 | mutant-wave-2.txt "2l" |
| W3 | Wave 3's tests kill its implementation | G+Q+budget | FAILED-TO-REFUTE: 3a ID dropped from usage (1); 3b map's `call graphql/` cut (1); 3c `(use merge-pr)` cut (1); 3w both files at 180e63e (2); restored 44 passed | mutant-wave-3.txt |
| VAC | G and Q not vacuous | Grep for skip/xfail/deselect/marks/commented tests; read of each test | FAILED-TO-REFUTE: only `parametrize`/`usefixtures`; every parametrization a non-empty constant; G and Q assert a record exists before judging; no test-config file in the diff | none |
| RED | Reds failed for the right reason | the whole-wave reverts | FAILED-TO-REFUTE: regenerated reds equal evidence/red: wave 1, 6 `TypeError` in test bodies; wave 2, 33 `AssertionError` or `graphql_lookup` `ValueError` in test bodies; wave 3, 2 `AssertionError`; no collection error | mutant-wave-N.txt "whole-wave revert" |
| COV | Every new line is exercised | CI coverage, `--cov=src`, full suite | REFUTED (AC-2.5): registry.py misses 114, 168, 275; only 275 (`graphql_call`'s `raise ValueError`) is in the change; call.py and graphql_only.py 100%; github_wrapper.py's 100, 354-355 are outside its docstring-only hunk | full-suite.txt |
| F2 | UB-3.1 files untouched | `git diff --name-only origin/main...HEAD` | FAILED-TO-REFUTE: neither file named; `test_wrapper_delivery.py` 100% covered in CI | none |
| F3 | Only D8's files | same, `-U0` | FAILED-TO-REFUTE: outside the spec dir, D8's nine files and `findings-ledger.md` (3 rows, at most 231 B); R removes 0 lines; V only in `_capability_problems` and its call; no fx, `CASES`, C, P, K, N, H, `families/`, `transport.py`, `_common.py` | none |
| F4 | Map bullet per D7 | map diff; `test_llm_map_within_cap` | FAILED-TO-REFUTE: D7's sentences, closing sentence last; budget file in the 44-passed run | mutant-wave-3.txt |
| RB | Rebase kept #27/#32 gating | AST of `GATED_OPERATIONS` at origin/main and HEAD; `refuse_gated` read | FAILED-TO-REFUTE: d30d022, 52403f8, f374b3d, 6fd2f64 ancestors of HEAD; 21 entries = main's 17 in order + 4 `graphql/`; `refuse_gated` unchanged; "no subcommand sends it", "use the X subcommand, which sends it", "use the X subcommand" intact | none |

## Refuted

- **M2c** (AC-1.1, task 2.3, D1): no test checks that a mutation document selects `clientMutationId`. Q's D6 rules have no such rule, and G builds its expected `query` from the record's own document (`record_case`, `declared_document`), so G cannot see a document change.
- **M2l** (AC-2.5, task 2.5): registry.py line 275 runs in no test; `check_graphql_call` refuses first. Under mutant 2j that line is reached, and its `ValueError` escapes `main`, because `_call_graphql` calls `graphql_call` outside its `try`: a traceback, not exit 2.

## Tree

After the last restore, `sha256sum -c` printed OK for all six files, `git diff --stat HEAD` was empty, HEAD was f3bc2b4, and the ignored set matched the pre-run baseline. The only new path is `evidence/verify/`; the throwaway worktree is gone. mutant-wave-3.txt holds one cp1252 byte from pytest, as red/wave-3.txt does.

Verdict: REFUTED (M2c, M2l)
