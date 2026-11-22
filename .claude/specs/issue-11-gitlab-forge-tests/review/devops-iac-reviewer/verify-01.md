# DevOps / IaC review — issue #11 VERIFY, pass 01 (implemented diff 83a1415..HEAD)

Checked and found to hold, with no finding:
- `.github/workflows/ci.yml` `forge-gitlab` matches design D5 exactly. It has no `needs:`, uses
  `persist-credentials: false`, hands the secret to one step through its `env:`, and runs one check command. The job
  inherits the workflow's `permissions: contents: read`, and the run log shows `Contents: read`, `Metadata: read`.
  `report` needs all three jobs and appends the two `forge-gitlab` verdict lines. The header comment is accurate.
- CI run 45033382186 behaved as designed. The credential step logged "the secret SFF_GITLAB_TEST_TOKEN is unavailable
  to this run" and exited 1 before the suite ran (AC-5.3). `report` printed `forge job: success` and
  `forge-gitlab job: failure`, then exited 1 (AC-5.4). All four `verify` legs and the `forge` job succeeded.
- The suite logs each creation, each teardown deletion and each sweep deletion by full path, which carries the run
  id. Logging is live through `log_cli_level = INFO`. A failed teardown deletion raises `ForgeCommandError` naming the
  target, so the run goes red.
- Every wrapper and git subprocess is bounded by `SUBPROCESS_TIMEOUT_SECONDS` (`SubprocessWrapperRunner.run`, the
  reused `_invoke`). `wait_until_checked` is bounded by `CHECK_DEADLINE_SECONDS`, measured with `time.monotonic`.
- When a run is cancelled, the runner sends SIGINT to the step's `bash`, then SIGTERM after 7500 ms, and kills the
  process tree 2500 ms later (docs.github.com "Workflow cancellation reference"). So Operability "Leftovers" is right
  that a cancelled run can leave its project unmarked. The next run more than a day later sweeps it.
- `report` keeps `if: always()`, which survives cancellation (same page), so a cancelled run still gets a verdict.
- The marked projects are removed by gitlab.com: "Projects are permanently deleted after a 30-day delay"
  (docs.gitlab.com/user/gitlab_com/), the retention DL-006 records.
- Rollback is a revert. Without the marker the product guard returns before reading or sending anything (UB-3).
- The end-to-end check needs no human step: the `forge-gitlab` job runs on every PR, push to `main` and dispatch.
  Storing the secret is a one-time setup step, not a step of the test.
- My iteration-01 items were applied: C1 and C2 in design.md Operability and D5, C3 in `docs/forge-suite.md` ("When
  the token expires or is revoked..."), and C4 as a findings-ledger row.

### C1 — Every run logs every marked project, up to 30 days of them, at INFO
Severity: C
Location: test/forge_gitlab/ephemeral.py § `sweep_leftovers`; design.md § D9 "The sweep"
Defect: The sweep logs one INFO line for every selected project that is already scheduled for deletion.
- The teardown only marks a run's project, and gitlab.com keeps a marked project for 30 days
  (docs.gitlab.com/user/gitlab_com/).
- A marked project's path still starts with `sff-test-` after the `-deletion_scheduled-<id>` rename (D4), so it
  stays selected.
- So each run prints a line for each earlier run's project aged one to 30 days. With `log_cli_level = INFO` these lines
  surround the run's own creation and deletion lines in the job log. No test asserts the level (S `caplog` checks
  only the credential step and the token).
Proposed-edit: in `sweep_leftovers`, change the call that logs "The leftover project %s is already marked for deletion
(on %s); the sweep sends nothing" from `logger.info(` to `logger.debug(`.

### C2 — No end-to-end verdict exists yet (risk, nothing to edit)
Severity: C
Location: tasks.md § Final F.1
Defect: In run 45033382186 the `forge-gitlab` job stopped at the credential step, so no `test/forge_gitlab/forge_*.py`
test has run against gitlab.com yet. F.1 is still unticked, and DL-009 records the wait for the operator's token.
READY in this lane covers the diff only. A merge before a green `forge-gitlab` run on the PR would fail `report` on
`main` and on every later PR until the secret is stored (`remote-ci-must-pass.md`).
Proposed-edit: none to the artefacts. The conductor keeps the merge behind a green `forge-gitlab` run on the PR's head.

Counts: 0 A, 0 B, 2 C, 0 D. CLEAN

Verdict: READY
