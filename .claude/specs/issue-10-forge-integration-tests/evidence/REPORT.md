# Evidence report — issue #10: forge integration tests against ephemeral `sff-test-*` repositories

Branch `issue-10-forge-integration-tests`, PR #68. Tier M. Spec: `requirements.md`, `design.md`, `tasks.md`
(design review converged at iteration 3, tasks at iteration 2), decisions DL-001..DL-008.

## Criterion → test → capture → verdict

W = `src/payload/test/test_github_wrapper_marker.py`, S = `test/test_forge_support.py`, L =
`test/test_forge_suite_layout.py`, F = `test/forge/forge_*.py` (real forge, run by the `forge` CI job).

| Criteria | Tests | Captures | Verdict |
|---|---|---|---|
| AC-4.1–4.3, UB-3 (origin guard) | W (refusal over five subcommands and two userinfo/near-miss origins; entry script with `-X`; ephemeral origin passes; no marker serves); S marker argv; L only `ephemeral.py` starts the wrapper | red/wave-1, green/wave-1, green/rework-1 | green |
| AC-5.1–5.4 (CI job) | L workflow structure (no `needs:`, one secret reference, `persist-credentials: false`, report needs both and fails unless forge succeeded, no `continue-on-error`) | red/wave-1, green/wave-1, green/rework-2 | green |
| AC-6.1–6.3, AC-1.1 refusal, AC-5.3 (credential, helper) | S lookup in checkout or main tree, helper via `git credential fill`, distributed-run refusal, missing secret, `write_credential.main` | red/wave-1, green/wave-1, red/wave-4, green/wave-4 | green |
| AC-1.2, AC-2.1–2.3, AC-3.1–3.2 (run id, teardown, sweep) | S run id; teardown deletes only this run's; refuses any other; Hypothesis property over listings; boundaries, 404 as deleted | red/wave-2, green/wave-2 | green |
| AC-1.1, AC-1.3, AC-1.4, AC-6.2, AC-6.3, UB-2 (provisioning) | S provisioning order, no creation no deletion, bad credential, token only in the clone (files, argv, `.git/config`, logs, repr), non-private creation refused and deleted, failed listing stops the run, removal retry | red/wave-3, green/wave-3, green/rework-1 | green |
| AC-7.1–7.3 (separation) | L default collection collects none; the forge path collects every forge test; nothing skips or deselects; `pytest.ini` exact option set; session fixture shape | red/wave-1, red/wave-4, green/wave-4 | green |
| AC-9.1–9.3 (docs) | L setup note `docs/forge-suite.md`, map, debt line; B `test_llm_map_within_cap` | red/wave-3, green/wave-3, green/rework-2 | green |
| UB-1, UB-4 | every W/S/L run needs no network or token; I `test_toolchain_integrity.py` and the C/P/K/V guards in every capture | all green captures | green |
| AC-1.1, AC-1.3, AC-3.1, AC-8.3 (real forge) | F:fixture (private seeded repository, no leftover), F:repos_git | regress/ci-43295116103-12d8df7 | green on github.com |
| AC-8.1, AC-8.2, AC-8.4, AC-8.5 (real forge) | F:subcommands, F:ci_security, F:collaboration | regress/ci-43295116103-12d8df7 | pending F.1: HTTP 403, token permissions not yet granted (DL-006) |

## CI

- Run 43295116103 on 12d8df7 (the batch's push): `verify` lint, types, security and tests all success.
  - The `forge` job created, pushed to and deleted `sff-test-20261112195559-…`; 5 passed, 7 failed.
  - The 7 failures are one root cause: GitHub's missing-permission 403 on calls needing Issues, Pull requests, Actions,
    Secret scanning alerts and Dependabot secrets, which the operator was asked to grant.
  - `report` failed because `forge` failed (AC-5.4).
- This report ships with the rework push; its run is the batch's second CI run.

## Verification

`adversarial-verifier`: round 1 REFUTED AC-1.1 AC-1.4 AC-3.1 AC-4.1 (35 of 40 mutants killed; five survivors on
untested branches). The test-only rework (DL-007) made round 2 VERIFIED (`verify/refutation-report-2.md`). The VERIFY
panel's one B is fixed (DL-008).

## Diff (`git diff --stat 590e4a9..HEAD`, spec excluded)

19 files: `ci.yml`, `github_wrapper.py`, the `test/forge/` suite (`ephemeral.py`, `conftest.py`, `pytest.ini`,
`write_credential.py`, five forge modules), W, S, L, `docs/forge-suite.md`, the map, the plan, the ledger, the lessons.
