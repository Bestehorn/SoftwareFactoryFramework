# Evidence report — issue #63: GitLab wrapper rewrite, part 2 slice: request forms the records lack

Tier M, three waves and three test-only reworks. Branch `issue-63-gitlab-request-forms`, PR #66. The branch was rebased onto 6beeb77 (#43's route prefix and package records) before wave 1.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1..AC-1.4 every issue key mapped by a record, none pending; later records of an ID copy the base | the F modules, N `test_each_record_of_an_id_copies_its_base_record`, V | red/green wave-2 | green |
| AC-2.1..AC-2.4 F1 several endpoints: `call --endpoint 'METHOD path'`, the first declared by default, an undeclared one refused | R, P, K, F:plan, F:developer_experience, F:sscs | red/green waves 1, 2 | green |
| AC-3.1..AC-3.3 F2 one value per place of a repeated name; wrong counts refused | R, P, K, F:create, F:tenant_scale, N | red/green waves 1, 2; rework-1 | green |
| AC-4.1, AC-4.2 F3 `[.format]` suffix from the listed formats only | R, P, K, F:create | red/green waves 1, 2 | green |
| AC-5.1..AC-5.3 F4 the host root and the container registry: login, origin from `container_registry_image_prefix`, `/jwt/auth` token by HTTP Basic, each failure refused before the registry | R, T, G, F:package, F:sscs | red/green waves 1, 2; rework-1..3 | green |
| AC-6.1..AC-6.3 F5 request headers declared and sent; transport-owned, credential and CR/LF/NUL refused | R, T, K, F:sscs, F:openapi_only, N | red/green waves 1, 2 | green |
| AC-7.1, AC-7.2 F6 two-level members sent at their full names; the S3 import refused by a `None` gate | K, F:gitlab_dedicated, N | red/green wave-2 | green |
| AC-8.1..AC-8.3 every record read and sent as its section documents | N, the F modules | red/green wave-2 | green |
| AC-9.1, AC-9.2 usage docstring and map name the forms | C, K, N | red/green wave-3 | green |
| UB-1..UB-4 existing calls unchanged; standard library only, credentials only from `config/gitlab.json` and the token only to its origin; undeclared values refused; the GitHub wrapper untouched | C, P, K, T, the family suites; the PR diff | every wave | green |

Red and green runs:
- Wave 1: red 27 failed, green 866 passed.
- Wave 2: red 82 failed, green 924 passed.
- Wave 3: red 2 failed, green 1030 passed.
- Reworks: 957, 962 and 988 passed; each new test failed under its mutant.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.**
- **Round 1:** REFUTED RF-1..RF-6 (`evidence/verify/refutation-report.md`), all test gaps; 61 of 70 mutants killed, every wave revert reproduced its red capture. DL-010 added tests only.
- **Round 2:** REFUTED R2-1, R2-2 (`refutation-report-2.md`), two near-variants; all nine round-1 survivors killed. DL-011 added two cases.
- **Round 3:** REFUTED R3-1 (`refutation-report-3.md`), the rest of the `\s` white-space set. DL-012 pinned every `str.isspace()` character with a guard against drift.
- **Round 4:** VERIFIED (`refutation-report-4.md`): each character's mutant killed alone, and the guard holds the tuple.

**Whole suite.** CI run 43106939480 (workflow_dispatch) success on 6687d9b, 3725 passed. PR run 43096840286 stayed pending through GitHub's 2026-11-11 Actions incident.

E2E: not applicable. The real-instance run is #11's. N and the F modules run every record through `main` against the fake host, in CI job `verify`, leg `tests`.
