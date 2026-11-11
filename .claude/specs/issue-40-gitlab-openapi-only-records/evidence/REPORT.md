# Evidence report — issue #40: GitLab wrapper rewrite, part 2 slice: the OpenAPI-only operations

Tier M, three waves and one rework. Branch `issue-40-gitlab-openapi-only-records`, PR #62. It was rebased onto 7ec47d1 (#44's GraphQL uploads) before the push; code-merge-reviewer resolved the overlap in `registry.py`, `transport.py`, `call.py`, the usage and the map, keeping #44's text.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1..AC-1.6 a record for every pending key, `ml_models` file keys in `deploy`, Params typed as their rows, offset paging, both `PENDING` empty | F, G, N, V | red/green wave-2 | green |
| AC-2.1, AC-2.2 a glob value keeps its slashes; an empty, `.` or `..` part is refused, nothing sent | R, P, F | red/green waves 1, 2 | green |
| AC-2.3, AC-2.4 an optional group written only when given; glob and group parameters are path parameters | R, F, G, K | red/green waves 1, 2 | green |
| AC-2.5 an escaped parenthesis sent without its backslash | R, F | red/green waves 1, 2 | green |
| AC-2.6 each form through `main` against the fake host | F, G | red/green wave-2 | green |
| AC-3.1 every record sent as `call` sends any record | N, K | green waves 1, 2 | green |
| AC-3.2 `--file` multipart for job artifacts; `--input` raw body as `application/octet-stream`; `--input` beside `-f`/`-F` or on another record refused | R, T, F, G, K (D5's refusal order and the raw send's retry, rework) | red/green waves 1, 2; rework-1 | green |
| AC-3.3 every record matches its section and is sent as it documents | N | red/green waves 1, 2 | green |
| AC-3.4 a paged record prints every page | F | red/green wave-2 | green |
| UB-1..UB-4 compatibility, standard library and credentials, the GitHub wrapper untouched, existing records unchanged | C, P, K, R, N, the family suites; the PR diff | every wave | green |

Red captures and green runs:
- Wave 1: red 35 failed, green 405 passed. Wave 2: red 40 failed, green 459 passed. Wave 3 (usage, map, ledger): green 189 passed.
- After the rebase onto 7ec47d1, 797 passed. Rework: 285 passed, after each new test failed under its mutant. Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`): 71 mutants over the three waves; each whole-wave revert reproduces its red capture; no criterion refuted. Its two observations, D5's "refuse both bodies first" order and `request_raw` going through `_send` (the 429 retry), were pinned by two tests in the rework (`evidence/green/rework-1.txt`), each failing under its mutant.

**Whole suite.** CI run 43016731121 success on 48929f3 (3504 passed, 0 skipped).

E2E: not applicable. The real-instance run is #11's. F and G run the path forms, lists and uploads, and N every record, through `main` against the fake host, in CI job `verify`, leg `tests`.
