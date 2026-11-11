# Evidence report — issue #15: GitLab wrapper rewrite, part 2: the kept keys

Tier S, one wave. Branch `issue-15-gitlab-gated-kept-keys`, PR #67. It was built on #63's branch, then rebased onto the trunk at d0d9eb9 once #63 merged. A conflict in `test_gitlab_api_package.py` was resolved by code-merge-reviewer keeping both sides (DL-003).

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 one record per kept key: method, path, Params, Kinds, required, `Paging.NONE` | N, V, the eight F record tables | red/green wave-1 | green |
| AC-2 every GitLab family's `PENDING` empty | F `test_nothing_is_pending` (eight); V | red/green wave-1 | green |
| AC-3 the 22 writers refused by a `None` gate: exit 2, no request, "no subcommand sends it" | F `test_a_writing_record_is_refused` (seven families) | red/green wave-1 | green |
| AC-4 orbit's and verify's glob reads sent with each `/` kept; `..` and empty parts refused | F `test_a_glob_record_is_sent_with_its_slashes` (orbit, verify); N | red/green wave-1 | green |
| UB-1..UB-4 existing records and compatibility, other gates, standard library and credentials, the GitHub wrapper untouched | C, K, P, `test_gitlab_api_graphql_only.py`, `test_wrapper_delivery.py`; the PR diff | green wave-1 | green |

Red and green runs:
- Red: 49 failed, 353 passed (assertions).
- Green: 967 passed; after the rebase onto d0d9eb9, 1024 passed.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- the wave revert reproduces the 49 red failures;
- every mutant of the gate, the `PENDING` sets, Kinds, required rows, methods and paths, Params, paging and the glob refusals is killed.

**Whole suite.** CI run 43109048909 success on b4d11ac.

E2E: not applicable. The real-instance run is #11's. F and N run `call` through `main` against the fake host, in CI job `verify`, leg `tests`.
