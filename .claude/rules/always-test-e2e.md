# End-to-End Tests Are Automated, or They Are Not Tests (MANDATORY)

Every change that alters runtime behaviour ships an automated end-to-end check that exercises the
deployed or running system through its real interfaces (API, CLI, queue, event), committed under
`test/e2e/` (or the project's equivalent) and named in the spec's test plan together with the job
that runs it.

## Where it runs

- A project that deploys: the pipeline's post-deploy stage runs the script after the merge
  (`deploy-<env>` → `e2e`/`smoke`). Its verdict on the merged SHA is the end-to-end evidence, read
  through the wrapper. The agent never deploys a branch to a shared environment, never takes a
  deploy lock or asks for a merge freeze, and never runs the check by hand as a substitute for the
  job.
- A local-only project: `python scripts/run_checks.py --group e2e`.
- A red post-merge end-to-end run is a defect fixed in an immediate follow-up on a fresh worktree,
  or reverted when the fix is not immediate.
- Where `config/delivery.json` names the verdict watcher, the post-deploy run on the first deployed
  commit that CONTAINS the landing is the end-to-end evidence: the deploy's last job judges it,
  ticks the `(post-deploy)` items and closes the issue, or returns a red one to the issue as
  `needs-rework`. The worker never waits for the deploy.

## No human step is ever part of a test

No sign-in by hand, no copying a response from a console, no visual check, no "the operator
confirms". A check only a person can perform is not reproducible and does not scale, so it is
recorded as a residual, never as a gate. Where the system has no machine path for the feature (a
browser-only SSO flow), the design adds one — a test principal, client credentials, a
pre-provisioned token — as in-scope product work, or the check stops at the API boundary.

## What needs no end-to-end check

A change that alters no runtime behaviour — docs, tests, tooling, a comment — says
`E2E: not applicable` in its spec and is done when CI is green.

## Integration

The test SUITE is CI's (`ci-owns-the-test-suite.md`); the end-to-end check is the one thing the
suite cannot do — exercise the deployed system — and it is still CI's. Follows `no-guessing.md` (a
verdict is a quoted run), `no-environment-vars.md`, `use-venv.md`.
