# Refutation report: issue #43, PR #65, head 7d20ead

Adversarial verification, 2026-11-11, worktree `.claude/worktrees/issue-43`. Paired files (P6): F
`src/payload/test/test_gitlab_api_package.py`, R `src/payload/test/test_gitlab_api_registry.py`, K
`src/payload/test/test_gitlab_api_call.py`, P `test/test_gitlab_api_properties.py`, N
`test/test_gitlab_wrapper_contract.py`, V `test/test_gitlab_wrapper_coverage.py`. Every local run is
`venv/Scripts/python.exe scripts/run_tests.py <files>` (2 workers). Baseline P6: 214 passed (`baseline-green.txt`).

## 1. Whole-suite verdict

| Claim | Command | Result | Capture |
|---|---|---|---|
| CI green on the pushed SHA | wrapper `get-run`, `wait-run 43041025640`, `get-jobs`, `get-job-logs 130592516968` | FAILED-TO-REFUTE: head_sha 7d20ead = HEAD; tree 4e28bc4e = `7d20ead^{tree}`; conclusion success; 5/5 jobs success; `3577 passed`, `1053 passed`, `CHECK SUMMARY - 2 passed, 0 failed, 0 skipped` | full-suite.txt |
| F.2 / UB-3 | `git diff --name-only origin/main...HEAD`; CI log | FAILED-TO-REFUTE: no `github_wrapper.py`, `github_api/`, `test_github_api_*` or `test_wrapper_delivery.py` in the diff; CI ran them with 0 failures (`test_wrapper_delivery.py` 100% executed) | full-suite.txt |

## 2. Kill the mutant: waves

| Wave | Mutation, tests | Result | Capture |
|---|---|---|---|
| 1 | registry.py, call.py, package.py from origin/main; R, P, N | FAILED-TO-REFUTE: 16 failed, 52 passed, the 16 ids of `red/wave-1.txt` | mutant-wave-1.txt |
| 2 | package.py, call.py from origin/main; F, K, N, V | FAILED-TO-REFUTE: 56 failed (F 45, K 11), 104 passed, as `red/wave-2.txt` | mutant-wave-2.txt |
| 3 | gitlab_wrapper.py, map, ledger from origin/main; wave-3 Run line | 189 passed. No behavioural claim: 3.1 is docstring text under UB-1 (preservation), 3.2 Validates none, 3.3 D8 ledger rows. Not a refutation | mutant-wave-3.txt |

Targeted mutants, each one replacement, P6 run, capture `mutant-<name>.txt`:

| Criterion | Mutant | Tests failing | Result |
|---|---|---|---|
| AC-3.1, UB-4 | hyphen-narrowed (#40's `name` group) | R hyphenated; K hyphenated x2; F hyphenated, raw[upload-module]; N upload-module-only, every-record-sent | killed (7) |
| AC-3.1 | hyphen-trailing-dash `(?:-[A-Za-z0-9_]*)*` | R `test_a_hyphenated_name_is_one_placeholder` | killed (1) |
| AC-2.4 | route-trailing-slash `value == prefix.rstrip("/")` | K [listed-value-and-a-slash]; P property | killed (2) |
| AC-2.4, UB-2 | route-suffix-match `prefix.endswith(value)` | P property; K [with-id-written-in], [git-bash-rewrite], [group-prefix-without-an-id]; R route, sent-only; F npm-group x2, npm-project, raw[dist-tag] | killed (10) |
| D2 | route-writes-caller-text `path=prefix + ...` | none, 214 passed | EQUIVALENT: `route` selects only on `value == prefix` (str), so both texts are equal; every loosening of that selection is killed above. Not a refutation |
| AC-2.2 | send-routes-after-encode | R sent-only; F prefix x7, raw[dist-tag]; N every-record-sent | killed (10) |
| AC-2.4 | expand-takes-unrouted-prefix (refusal removed) | R `test_a_prefix_record_is_sent_only_under_a_prefix` | killed (1) |
| AC-2.4 | route-prefix-for-any-record | K [rest-record-without-a-prefix-path], [graphql-record] | killed (2) |
| AC-2.4 | route-refusal-lists-nothing | K [no-route-prefix] and the 4 unlisted texts | killed (5) |
| AC-2.3 | call-routes-after-values | F npm, debian, nuget project rows; raw[dist-tag] | killed (4) |
| AC-2.2 | call-drops-prefix-for-send (`PreparedCall.prefix`) | F prefix x8, raw[dist-tag]; N every-record-sent | killed (10) |
| AC-2.1 | pkg-npm-prefixes-reordered | F npm x4; N every-record-matches | killed (5) |
| AC-2.1, AC-4.3 | pkg-debian-index-nuget-prefixes | N every-record-matches, every-record-sent | killed (2) |
| AC-1.6, AC-4.4 | pkg-pipelines-not-paged | F only-list-paged, list-prints[list-package-pipelines] | killed (2) |
| AC-4.2 | pkg-dist-tag-octet-stream | F typed, raw[dist-tag] | killed (2) |
| AC-1.4 | pkg-debian-components-scalar | F typed | killed (1) |
| AC-1.4 | pkg-archive-sha-not-required | F typed | killed (1) |
| AC-1.2, AC-1.7 | pkg-nuget-v2-key-unpended | F pending, two-endpoint; V mapped-or-pending | killed (3) |
| AC-1.4, AC-4.2 | pkg-maven-raw-upload-file-param (BODY, FILE) | F typed, raw[file-3]; N every-record-matches | killed (3) |
| AC-1.4, AC-4.3 | pkg-maven-raw-upload-file-query-param (QUERY, SCALAR) | N every-record-matches, every-record-sent | killed (2) |
| AC-1.1 | pkg-delete-dist-tag-method DELETE to GET | N x2; V mapped-or-pending, declared-key-in-family | killed (4) |
| AC-1.5 | pkg-upload-module-path-name-param | F `test_no_param_names_a_path_parameter` | killed (1) |

Re-confirmed green after every restore: P6 214 passed (`green-after-restore.txt`).

## 3. Vacuity scan

`git diff -U0 origin/main...HEAD` of F, R, K, P, N searched for skip, xfail, deselect, importorskip, `pragma: no cover`,
`assert True`, commented asserts, bare `pass`, filterwarnings and `mark.`: only 7 `@pytest.mark.parametrize` lines over
literal case tuples. No pyproject, conftest or pytest.ini change. 19 new test functions, each asserting an oracle; K's
cases go through `refused_messages` (exit 2, no request, empty stdout, an ERROR record). FAILED-TO-REFUTE.

## 4. Red for the right reason

`red/wave-1.txt`: 16 failed, 768 passed, 0 errors. AssertionError (R hyphenated, N upload-module-only), TypeError on
`route_prefixes` raised in R, P and N bodies, AttributeError from N's `prefix_problems` (tasks 1.3's stated mode).
`red/wave-2.txt`: 56 failed, 784 passed, 0 errors, all AssertionError (the lookup refusal; argparse `unrecognized
arguments: --route-prefix`). No collection error. Both reproduced by the wave reverts. FAILED-TO-REFUTE.

## 5. Coverage of the change

CI `--cov=src`: `commands/call.py` 100%, `families/package.py` 100%, `registry.py` 99% missing 315, 617, 621; `git
blame` gives 678c076b and 140bbe44 (base, 2026-11-10), not this change. The `gitlab_wrapper.py` change is docstring
only. FAILED-TO-REFUTE.

## F.3 scope

Outside the spec directory the diff names registry.py, commands/call.py, families/package.py, gitlab_wrapper.py, F,
R, K, P, N, forLLMConsumption.md and findings-ledger.md: D8's list. No fx, V, C, T, transport.py, `_common.py` or other
`commands/` module. K, R, P and F remove no line; N's removed lines are D4's (constants, `glob_names`, two docstrings,
`record_problems`' skip, `record_call`'s signature, the send loop's call), none an `assert`. No changed line of call.py
names `GATED_OPERATIONS`, a gated ID or `token`. The merge 7d20ead brought only #14's files (`git diff 7d20ead^1
7d20ead`). FAILED-TO-REFUTE.

## Restoration

Every mutant was restored from byte copies, and each file's sha256 after restore equals its pre-run value: registry.py
9f1656b1, call.py 17593471, package.py 89c70ed9, gitlab_wrapper.py 2d9d0b8e, forLLMConsumption.md 1b06f5d0,
findings-ledger.md 0c1b48c0. The wave-1 `git checkout HEAD --` rewrote package.py with CRLF (`core.autocrlf=true`);
its bytes were rewritten from the HEAD blob and the index entry refreshed (no staged change; blob 3223dfc7 equals
HEAD's). `git status --porcelain` shows only this `evidence/verify/` directory; tmp/ files removed; nothing committed.

Refuted ids: none.

Verdict: VERIFIED
