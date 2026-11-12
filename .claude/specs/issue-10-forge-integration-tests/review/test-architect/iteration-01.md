# Test architect — design review, iteration 01

## Findings

### B1 — The distributed-run refusal that keeps AC-1.1's one repository has no test
Severity: B
Location: design.md § D1 "One repository per run"; § Correctness Properties AC-1.1
Defect: `refuse_distributed_run` alone stands between `python scripts/run_tests.py test/forge` and one repository per xdist worker (the runner's default `--workers local` adds `-n` on any host where `cores // 4` is 2 or more, `build_command`), and no listed test fails if it lets a worker id other than `master` through.
Material-because: AC-1.1 ("every test of the run SHALL use that one repository") is untested under the runner's default worker count.
Proposed-edit: append to Correctness Properties AC-1.1 and to the mapping row AC-1.1: "Example, S `test_a_distributed_run_is_refused`: `refuse_distributed_run(worker_id="gw0")` raises `ForgeSetupError` naming `--workers 1`; `worker_id="master"` returns."

### B2 — The session fixture itself is exercised by no test that can fail
Severity: B
Location: design.md § D9 `ephemeral_repository`; § Correctness Properties AC-1.1, AC-1.4
Defect: S tests `provision`, L's `--collect-only` sets up no fixture, and no F test can observe its own teardown or the fixture's scope, so an `ephemeral_repository` without `scope="session"`, or yielding outside `with provision(...)`, leaves every listed test green while each test creates a repository or none is deleted (the sweep removes it a day later; `test_no_leftover_survives_the_sweep` runs after the sweep).
Material-because: AC-1.1 (one repository per run) and AC-1.4 (deleted whether the tests passed, failed or raised an error) are pinned only below the component pytest finalizes.
Proposed-edit: append to Correctness Properties AC-1.1 and AC-1.4 and both mapping rows: "Structural, L `test_the_session_fixture_wraps_one_provision`: by `ast` of `test/forge/conftest.py`, `ephemeral_repository` is decorated `pytest.fixture(scope="session")`, calls `refuse_distributed_run` before `provision`, and its one `yield` lies inside the `with provision(...)` block."

### B3 — Fail-fast and selection options in `test/forge/pytest.ini` escape every test
Severity: B
Location: design.md § Correctness Properties AC-7.3; § D1 Mechanism
Defect: `run_tests.py` `reject_failfast` checks only the runner's own argv (`extra`), and L `test_nothing_keeps_a_forge_test_from_running` checks `addopts` only for `-m`, `-k`, `--deselect`, `--ignore`, so `-x`, `--maxfail`, `--sw` or `--collect-only` in the new ini passes every listed test while the forge job stops at the first failure or runs nothing and exits 0.
Material-because: AC-5.2 (one command that reports every failing forge test) and AC-7.3 (nothing keeps a forge test from running).
Proposed-edit: replace "`pytest.ini`'s `addopts` holds no `-m`, `-k`, `--deselect` or `--ignore`" with "`pytest.ini`, read with `configparser`, holds exactly the `[pytest]` keys `python_files` = `forge_*.py` and `addopts` = `-p no:cacheprovider`", and add this L test to the mapping row AC-5.2.

### B4 — AC-6.3's "log line" and "test report" have no oracle
Severity: B
Location: design.md § Correctness Properties AC-6.3
Defect: `test_the_token_is_written_only_to_the_clone` checks files, argv and the exclude line; nothing fails if the suite's log record of a creation or deletion, or the `repr` of the `EphemeralRepository` every F test receives (printed in a failure report), held the token.
Material-because: AC-6.3 ("SHALL appear in no ... log line, test report").
Proposed-edit: append to that example: "; no record `caplog` captured at `DEBUG` during the provision holds the token, nor does the `repr` of the yielded `EphemeralRepository`."

### C1 — The sweep property's expected set must not come from the code under test
Severity: C
Location: design.md § Correctness Properties AC-3.1, AC-3.2
Proposed-edit: after "none for any other" add "(the expected set computed from the strategy's drawn owner, prefix and age side, never through `is_leftover` or `select_leftovers`)".

### C2 — "Starts the wrapper" has no stated check
Severity: C
Location: design.md § Correctness Properties AC-4.3, AC-8.1
Proposed-edit: replace "no other file of `test/forge/` starts the wrapper" with "no file of `test/forge/` but `ephemeral.py` imports `subprocess`, and `PRODUCT_WRAPPER` is named only in `SubprocessWrapperRunner` and `product_wrapper`".

### C3 — UB-2's read check names no mechanism
Severity: C
Location: design.md § Correctness Properties UB-2
Proposed-edit: replace "and no path the provision reads is that file" with "and the clone's `credentials/github-pat.txt` holds the test token, not the sentinel's text".

### C4 — Workspace removal on the setup-failure paths
Severity: C
Location: design.md § Correctness Properties AC-1.3, AC-2.3
Proposed-edit: append "and the workspace no longer exists" to the AC-1.3 S example (a workflow in the seed) and to the AC-2.3 provision whose creation answers exit 1.

### C5 — The skip check is a text match an import escapes
Severity: C
Location: design.md § Correctness Properties AC-7.3
Proposed-edit: replace the string list with "by `ast`: no `pytest.` attribute `skip`, `skipif`, `xfail`, `importorskip` or `exit`, none of these imported from `pytest`, and no `SkipTest`" (`from pytest import skip` holds none of the listed strings).

### C6 — "The triggers are unchanged" is relative
Severity: C
Location: design.md § Correctness Properties AC-5.1
Proposed-edit: replace "the triggers are unchanged" with "`on:` holds exactly `push` (`branches: [main]`), `pull_request` and `workflow_dispatch`".

## Coverage

Tests by the design's legend (W, S, L, F, B, C, P, K, V, I).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning | GAP (B1, B2) |
| AC-1.2 | S run id | OK |
| AC-1.3 | F fixture, F repos_git; S provisioning | OK |
| AC-1.4 | S provisioning (returns, raises, failed deletion) | GAP (B2) |
| AC-2.1 | S teardown deletes | OK |
| AC-2.2 | S teardown refuses | OK |
| AC-2.3 | S no creation, no deletion | OK |
| AC-3.1 | S sweep property, boundaries; F sweep | OK |
| AC-3.2 | S sweep property, boundaries | OK |
| AC-4.1 | W refuses, W entry script | OK |
| AC-4.2 | W ephemeral origin; every F | OK |
| AC-4.3 | S marker argv; L; W entry script, W without marker | OK |
| AC-5.1 | L forge beside verify | OK |
| AC-5.2 | L secret step | GAP (B3) |
| AC-5.3 | S missing secret | OK |
| AC-5.4 | L report | OK |
| AC-6.1 | S credential lookup | OK |
| AC-6.2 | S bad credential | OK |
| AC-6.3 | S written only to the clone, helper; L secret step | GAP (B4) |
| AC-7.1 | L default collects none | OK |
| AC-7.2 | L forge path collects all | OK |
| AC-7.3 | L nothing keeps a test from running | GAP (B3) |
| AC-8.1 | L ephemeral only; every F | OK |
| AC-8.2 | F subcommands, two round trips | OK |
| AC-8.3 | F repos_git, two tests | OK |
| AC-8.4 | F ci_security, four tests; docstring | OK |
| AC-8.5 | F collaboration, two tests | OK |
| AC-8.6 | L ephemeral only | OK |
| AC-9.1 | L setup note | OK |
| AC-9.2 | L map; B | OK |
| AC-9.3 | L debt line | OK |
| UB-1 | W, S, L in `verify` on doubles | OK |
| UB-2 | S sentinel | OK |
| UB-3 | C, P, K, V unedited; W without marker | OK |
| UB-4 | I; the PR diff | OK |

30 OK, 5 GAP.

NOT-CLEAN (0 A, 4 B) — NOT-READY
