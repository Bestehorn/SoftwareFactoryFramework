# DevOps / IaC review — issue #10 design, iteration 01

### B1 — The leftover integration test judges at the test's instant, not the sweep's
Severity: B
Location: design.md § D6 (F:fixture `test_no_leftover_survives_the_sweep`); § D9 `provision` (`EphemeralRepository`)
Defect: The test asserts that no listed item `is_leftover` "at the test's time", which is later than the `now` that
D9 step 4 swept with, so an `sff-test-*` repository that crosses the one-day line between the sweep and the test (one
AC-3.2 requires the sweep to spare) fails the forge job although the sweep did exactly what AC-3.1 asks; such
repositories exist routinely, because every superseded pull-request run is cancelled (`ci.yml` `cancel-in-progress`)
and leaves its repository behind (C1).
Material-because: AC-3.1 — its integration test asserts "more than a day before the test" instead of "more than a
day before the sweep", and the false red fails the pipeline on a pull request or on `main` (wrong-behaviour).
Proposed-edit: D9, the `EphemeralRepository` field list: "(`run_id`, `owner`, `name`, `default_branch`, `seed_sha`,
`seed_tree_sha`, `swept_at`, `clone`, `wrapper`, `git`)", with "`swept_at` is the `now` step 4 passed to
`sweep_leftovers`"; D6, the row's assertion: "no item `is_leftover` with `now=swept_at` (AC-3.1)".

### C1 — No interrupted run finishes its teardown
Severity: C
Location: design.md § D5 Concurrency; § Operability (Leftovers)
Defect: The design says a cancelled run's teardown may not finish; it never does. GitHub's cancellation sends
`SIGINT` to the step's entry process, then `SIGTERM` after 7500 ms, then kills the process tree (docs.github.com
"Workflow cancellation"), and a local Ctrl-C interrupts `scripts/run_tests.py`, which runs pytest through
`subprocess.call`; CPython `Lib/subprocess.py` `call` kills the child once the interrupt reaches it
(`except:  # Including KeyboardInterrupt` → `p.kill()`, after `Popen.wait`'s `_sigint_wait_secs = 0.25`). So every
superseded pull-request run leaves its repository for a day, and an interrupted local run also leaves its workspace,
the clone's `credentials/github-pat.txt` included, in the temporary directory.
Proposed-edit: Operability, Leftovers: "An interrupted run (a superseded pull-request run, a Ctrl-C) never finishes
its teardown: `run_tests.py` kills pytest at the interrupt. Its repository is deleted by the first run more than a
day after its creation; a local run's workspace, the clone's credential file included, stays in the temporary
directory until it is removed." Removing a stale workspace automatically is outside the ask (Residuals).

### C2 — The creation and deletion log lines reach no job output
Severity: C
Location: design.md § D1 Mechanism (`test/forge/pytest.ini`); § D9 (the sweep); § Operability (Logs)
Defect: pytest "captures log messages of level `WARNING` or above automatically and displays them in their own
section for each failed test" (docs.pytest.org `how-to/logging.html`), and D1's `pytest.ini` sets no `log_cli`, so
the lines naming each repository the run creates and each one the teardown or the sweep deletes appear in no run's
output (passing, failing or cancelled), and a leftover or a sweep deletion cannot be traced from the job log.
Proposed-edit: D1 Mechanism: "`test/forge/pytest.ini`: `[pytest]`, `python_files = forge_*.py`, `addopts = -p
no:cacheprovider`, `log_cli = true`, `log_cli_level = INFO` (each creation and deletion is printed as it happens:
"By setting the `log_cli` configuration option to `true`, pytest will output logging records as they are emitted
directly into the console", ibid.)". L `test_nothing_keeps_a_forge_test_from_running` is unaffected (no `-m`, `-k`,
`--deselect` or `--ignore`).

### C3 — The rollback sentence relies on a sweep the revert removes
Severity: C
Location: design.md § Operability (Rollback)
Defect: "a remaining leftover goes with a later run's sweep" is false after the revert: the sweep is reverted with
the job and the suite.
Proposed-edit: "Rollback. Revert the change: the job, the suite and the guard go together. A leftover from before the
revert stays in `bestehorn-sff-test`, the only owner the token reaches, until the suite returns and its sweep deletes
it; the secret `SFF_TEST_TOKEN` and the token's grants can stay."

## Residuals (C, outside the ask)

- A `403` names no permission: `github_api/transport.py` `_http_failure` prints the status and GitHub's body
  ("Resource not accessible by personal access token"), not the `X-Accepted-GitHub-Permissions` header ("You can use
  the `X-Accepted-GitHub-Permissions` header to identify the permissions that are required to access the REST API
  endpoint", docs.github.com "Troubleshooting the REST API"); until a wrapper change surfaces it, D6's permission
  table is the diagnosis.
- Token expiry: the token's creation form asks for one ("Under Expiration, select an expiration for the token",
  docs.github.com "Managing your personal access tokens"); if it was given one, every forge job on every pull request
  and on `main` fails at that date until the secret and the local file hold a new token. AC-9.1's note list does not
  name the expiry or the rotation.
- A stale local workspace left by an interrupted run (C1) is removed by nothing in this change.

NOT-CLEAN (0 A, 1 B)
