# DevOps / IaC review — issue #10 design, iteration 02 (delta)

## Iteration-01 findings

- B1 (`swept_at`) — resolved. D9 lists `swept_at` among the `EphemeralRepository` fields as "the `now` step 4 passed to
  `sweep_leftovers`", step 4 passes it, and the D6 row asserts "no item `is_leftover` with `now=swept_at`". A
  repository created after the sweep has a negative age at `swept_at`, so it can no longer cause a false red.
- C1 (Operability, Leftovers) — applied. It names the cancelled or superseded CI run and the local Ctrl-C, says the
  repository lasts until the first run more than a day later, and says the local workspace, the clone and its
  credential file stay behind. D5 Concurrency now points to that text.
- C2 (`log_cli`) — applied, and the quote checks out against docs.pytest.org `how-to/logging.html` ("By setting the
  `log_cli` configuration option to `true`, pytest will output logging records as they are emitted directly into
  the console"). `scripts/run_tests.py` `REPORT_ARGS` (`-ra`, `--tb=short`, `--continue-on-collection-errors`) and
  `build_command` add nothing that overrides it, and `--workers 1` adds no `-n`. The default collection reads
  `pyproject.toml`, not `test/forge/pytest.ini`, so `verify` does not change (UB-1). The AC-7.3 oracle's exact key
  set includes both new keys.
- C3 (Rollback) — applied. "The job, the suite with its sweep, and the guard go together", and a leftover from
  before the revert stays until the suite returns.

## Delta checked, no defect found

- D5 "`ci.yml` is not toolchain": `config/toolchain.json` `files` lists no `.github/workflows/` path. Its
  `not_installed` entry `templates/ci/*` says ".github/workflows/ci.yml is the project's own". `templates/ci/` holds
  only `github-deploy`, `github-merge-steward`, `github-steward-wake` and `gitlab-delivery` templates.
  `gate_toolchain_paths.py` `run` refuses only paths in `files`, and `test/test_toolchain_integrity.py` names no
  workflow. So the edit is implementable and keeps UB-4.
- D1 Alternatives, `test/e2e/`: `run_checks.py` has `ON_REQUEST_GROUPS = ("e2e",)`, the `ci.yml` matrix is `[lint,
  types, security, tests]`, and `e2e_argv` runs only `test/e2e`. The stated reason is accurate. The end-to-end check
  stays an automated pipeline job with no human step (`always-test-e2e.md`).
- AC-5.1's trigger oracle (`push` `branches: [main]`, `pull_request`, `workflow_dispatch`) matches the current
  `ci.yml` `on:` exactly.
- D9's reordered steps: the `finally` covers steps 2 to 6, so a credential refusal still removes the workspace
  (AC-2.3's added assertion). The CI runner's workspace goes away with the runner.

### D1 — The residual overstates that nothing removes a stale local workspace
Severity: D
Location: design.md § Residuals ("Nothing removes the workspace an interrupted local run leaves in the temporary
directory")
Defect: The sentence is false where the temporary directory is scoped. When TMPDIR is this tree's `tmp/os-temp`, the
`tempfile.mkdtemp` workspace lands inside it, and `scripts/reap_agent_temp.py --scoped-temp tmp/os-temp --apply`
removes "its CONTENTS ... wholesale" (module docstring, "THE OWNERSHIP RULE"). That is the cleanup
`no-environment-vars.md` Clarification 2 names. The defect is the scope of the claim: nothing in this change removes
the workspace, but other tooling can.
Proposed-edit: "Nothing in this change removes the workspace an interrupted local run leaves in the temporary
directory."

CLEAN
