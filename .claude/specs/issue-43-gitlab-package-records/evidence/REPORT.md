# Evidence report — issue #43: GitLab wrapper rewrite, part 2 slice: the package stage group

Tier M, three waves. Branch `issue-43-gitlab-package-records`, PR #65. The branch was rebased onto 252c21e (#40's path forms) before wave 1. It then merged the trunk at 70c4dba (#14's GitHub files), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1..AC-1.7 a record per package key but the kept ones, the first endpoint of a two-endpoint entry, Params typed as their rows, offset paging, `PENDING` the kept keys | F, N, V | red/green wave-2 | green |
| AC-2.1..AC-2.5 a `/<route-prefix>/` record sent under each value its page lists, routed before encoding, any other text refused | R, P, K, F, N | red/green waves 1, 2 | green |
| AC-3.1..AC-3.3 a hyphenated `:module-name` read as one name and sent as one segment | R, K, F, N | red/green waves 1, 2 | green |
| AC-4.1..AC-4.4 every record sent as its section documents; raw-body uploads through `--input`, `--file` multipart uploads | F, N, K | red/green wave-2 | green |
| UB-1..UB-4 compatibility, standard library and credentials, the GitHub wrapper untouched, existing paths and records unchanged | C, P, R, N, the family suites; the PR diff | every wave | green |

Red and green runs:
- Wave 1: red 16 failed, green 784 passed.
- Wave 2: red 56 failed, green 840 passed.
- Wave 3 (usage, map, ledger): green 189 passed.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- 22 targeted mutants: 21 killed, 1 equivalent (`route` writes the caller's text, equal by construction).
- Each whole-wave revert reproduces its red capture.
- `call.py` and `package.py` are at 100% coverage in CI.

**Whole suite.** CI run 43041025640 success on 7d20ead (3577 passed).

E2E: not applicable. The real-instance run is #11's. F runs the prefix, hyphenated, glob, list and upload forms, and N every record, through `main` against the fake host, in CI job `verify`, leg `tests`.
