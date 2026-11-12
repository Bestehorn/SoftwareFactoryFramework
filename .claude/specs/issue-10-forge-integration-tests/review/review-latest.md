# Review — design iteration 01 (consolidated)

Lanes: spec-review-agent NOT-CLEAN (1 A, 1 B); test-architect NOT-CLEAN (0 A, 4 B), NOT-READY; standards-reviewer
NOT-CLEAN (0 A, 1 B); devops-iac-reviewer NOT-CLEAN (0 A, 1 B); security-reviewer CLEAN; best-practice-reviewer CLEAN.

Combined A+B: 8 (1 A, 7 B). Every A/B names its criterion or failure class and carries a proposed edit; none rejected.

## A/B (apply all)

| Id | Lane | Defect | Fix |
|---|---|---|---|
| A1 | spec-review A1 | `SubprocessGitRunner` passes `-C <clone>` before `<workspace>/clone` exists | D9 step 3 creates `<clone>` (`Path.mkdir`) before `git init`; D3 wording |
| B1 | spec-review B1 | D8's main-working-tree lookup contradicts AC-6.1 | restate AC-6.1 (DL-002): the checkout that runs it or, for a linked worktree without one, the repository's main working tree |
| B2 | devops B1 = spec-review C3 (deduped, B kept) | `test_no_leftover_survives_the_sweep` judges at the test's time | `EphemeralRepository.swept_at` = the sweep's `now`; the test uses it |
| B3 | standards B1 | `TeardownRefusedError`, `SweepRefusedError` hide their base | `ForgeTeardownRefusedError`, `ForgeSweepRefusedError` everywhere |
| B4 | test-architect B1 | `refuse_distributed_run` untested | S example: `gw0` refused, `master` passes |
| B5 | test-architect B2 | nothing pins the session fixture's scope and teardown | L check by `ast` of `test/forge/conftest.py` (scope `session`, yield inside `with provision(...)`) |
| B6 | test-architect B3 | a fail-fast/selection option in `test/forge/pytest.ini` passes every test | L oracle: the file's exact option set |
| B7 | test-architect B4 | AC-6.3's "log line" and "test report" untested | `caplog` check over a scripted provision; the `repr` of `EphemeralRepository` holds no token |

## C/D (apply in the same pass — restate, clarify, tighten, remove)

- spec-review C1: bind `run_id`/`name` before the `try`, so a refused credential is not masked by `UnboundLocalError`.
- spec-review C2: the clone's credential file is written as bytes with `\n` (`Path.write_bytes`).
- spec-review D1, best-practice D1: correct D1's and D3's rejected-alternative reasons as proposed.
- devops C1: Operability "Leftovers" states what a cancelled CI run or an interrupted local run leaves (the repository for a day; locally the clone and its credential copy in the temp directory).
- devops C2: `test/forge/pytest.ini` adds `log_cli = true`, `log_cli_level = INFO`, so the create/delete log lines reach the job log (B6's exact option set includes them).
- devops C3: Rollback says a revert also removes the sweep.
- standards C1: D5 says why `ci.yml` may be edited (`config/toolchain.json` lists no workflow; `not_installed` `templates/ci/*`); C2: the Overview names the one deviation (the forge job's command is `run_tests.py`, not `run_checks.py`); C3: `EPHEMERAL_REPOSITORY_PREFIX` and `TEST_MARKER_OPTION` read from `product_wrapper()`, not redefined; C4: D1 Alternatives says why not `test/e2e/`; C5: the map row points to `credentials/README.md`; D1: `RepositoryRecord.of(item=...)`.
- security C1: D2's claim that owner/repo never hold userinfo is false for a crafted origin; the refusal names the owner after its last `@`, and W covers that origin; C2: restate "owner-only file mode" (on Windows the protection is `mkdtemp`'s owner-only ACL); C3: the CI-trust bullet says a same-repository branch or a dispatch runs its own code with the secret; C4: register the helper as `credential.https://github.com.helper` after the empty `credential.helper=` reset.
- best-practice C3: `git rev-parse --path-format=absolute --git-common-dir`; drop the relative-path handling.
- test-architect C1–C6: the sweep property's expected set comes from the generated data; state how "starts the wrapper" is checked; state UB-2's read check; setup-failure tests also assert the workspace is removed; the skip check uses `ast`; name the triggers.

## Residuals (out of the ask, left out)

best-practice C1 (`if: always()` vs `!cancelled()`, pre-existing), C2 (Node 20 action versions, workflow-wide);
security: a protected deployment environment for the secret; the existing `@`-in-owner parsing without the marker
(UB-3); devops: `X-Accepted-GitHub-Permissions` not printed by the wrapper; token expiry; no cleanup of a clone an
interrupted local run leaves.

## Coverage (test-architect)

30 of 35 OK; GAP: AC-1.1, AC-1.4, AC-5.2, AC-6.3, AC-7.3 — closed by B4–B7.
