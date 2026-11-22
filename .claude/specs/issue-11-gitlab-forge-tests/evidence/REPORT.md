# Evidence report — issue #11: real-GitLab integration tests on ephemeral `sff-test-*` projects

Tier M. PR 69, branch `issue-11-gitlab-forge-tests`. Legend as design.md's Acceptance Criteria Mapping: W
`src/payload/test/test_gitlab_wrapper_marker.py`, S `test/test_forge_gitlab_support.py`, G
`test/test_forge_gitlab_layout.py`, L `test/test_forge_suite_layout.py`, H `test/test_forge_support.py`, F
`test/forge_gitlab/forge_*.py`. Captures are under `evidence/`.

| Criterion | Tests | Red | Green | Verdict |
|---|---|---|---|---|
| AC-1.1 | S provisioning, distributed run; G session fixture; F fixture | red/wave-2, 4, 5 | green/wave-2, 4, 5; rework-1 | proven locally; F pending F.1 |
| AC-1.2 | S run id | red/wave-2 | green/wave-2 | proven |
| AC-1.3 | S provisioning (`.gitlab-ci.yml` seed); F fixture, no pipeline, records | red/wave-4 | green/wave-4 | proven locally; F pending F.1 |
| AC-1.4 | S provisioning (returns, raises, failed deletion), non-private creation; G session fixture | red/wave-4, 5 | green/wave-4, 5 | proven |
| AC-2.1 to AC-2.3 | S teardown deletes only its own, refuses others; no creation no deletion | red/wave-3, 4 | green/wave-3, 4 | proven |
| AC-3.1 to AC-3.3 | S sweep property and boundaries; F fixture sweep | red/wave-3 | green/wave-3 | proven locally; F pending F.1 |
| AC-4.1 | W refuses (40 cases incl. near misses; no config exits 1), W entry script | red/wave-1 | green/wave-1 | proven |
| AC-4.2 | W ephemeral through; every F test under the marker | red/wave-1 | green/wave-1 | proven locally; F pending F.1 |
| AC-4.3 | S marker argv and bytes; W values; G confinement | red/wave-1, 3 | green/wave-1, 3 | proven |
| AC-5.1, AC-5.2, AC-5.4 | G job, secret step, report; L report | red/wave-2 | green/wave-2 | proven; CI run 45033382186 shows the job and the verdict at runtime |
| AC-5.3 | S missing secret (`write_test_credential`, `write_credential.main`) | red/wave-2, 3 | green/wave-2, 3 | proven; CI run 45033382186 failed the job with the designed message |
| AC-6.1 to AC-6.3 | S credential lookup, bad credential, token only in the clone, clone commits none, helper | red/wave-2, 4 | green/wave-2, 4 | proven |
| AC-7.1 to AC-7.3 | G default collects none, path collects all, nothing keeps a test from running | red/wave-2, 5 | green/wave-2, 5 | proven |
| AC-8.1 to AC-8.7 | F modules (12 tests); G confinement and uncalled forms | red/wave-3, 5 | green/wave-3, 5 | structure proven; runtime pending F.1 |
| AC-9.1, AC-9.2 | G setup note, map; B map cap | red/wave-4 | green/wave-4 | proven |
| UB-1 to UB-5 | guards C, A, K, V, P, H, L, I, B in every wave run; S sentinel; W without marker | — | green/wave-1 to 5, rework-1 | proven |

## CI

- Run 45033382186 on c389d46 (the one push so far): `verify` lint, types, security and tests (incl. the hook suite)
  success; `forge` (github.com) success; `forge-gitlab` failure at its credential step, "the secret
  SFF_GITLAB_TEST_TOKEN is unavailable to this run"; `report` failure on it. One root cause, the unset secret
  (DL-009, `evidence/regress/ci-45033382186-c389d46.txt`). CI runs caused: 1.

## Verification

- `adversarial-verifier`: VERIFIED (`evidence/verify/refutation-report.md`): each wave's mutant killed by its paired
  tests; `push_branch` and `wait_until_checked` are proven only by F, as tasks.md says.
- VERIFY panel: six lanes READY, A+B 0; the C/D edits are in `green/rework-1.txt`'s run (`review/review-latest.md`).

## Open

- F.1: the GitLab forge suite against gitlab.com waits for the operator's group service-account token as the Actions
  secret `SFF_GITLAB_TEST_TOKEN` (issue #11 comment 6923784402).

## Diff (83a1415.., code, tests, workflow, docs)

20 files changed: `.github/workflows/ci.yml`, `docs/findings-ledger.md`, `docs/forLLMConsumption.md`,
`docs/forge-suite.md`, `src/payload/scripts/gitlab_api/errors.py`, `src/payload/scripts/gitlab_wrapper.py`, W, H's
subject `test/forge/ephemeral.py`, `test/forge_gitlab/` (conftest, ephemeral, five forge modules, pytest.ini,
write_credential), G, S, L.
