# devops-iac-reviewer — design iteration 01 — issue #40

No IaC, no deploy, and no CI-definition edit: D6 names only `src/payload/` product files, `test/` project files and
`docs/findings-ledger.md`, and none of them is a `config/toolchain.json` `files` key. The rest was checked and has no
defect:

- **CI collection.** F and G (`src/payload/test/`) and P and N (`test/`) are in `pyproject.toml` `testpaths`, which
  the `tests` leg of `.github/workflows/ci.yml` `verify` runs through `run_checks.py` → `run_tests.py --workers auto
  --coverage`.
- **No network in CI.** F and G copy `test_gitlab_api_no_stage_assigned.py`'s autouse `socket_guard` and fake host.
- **Hypothesis determinism.** The installed Hypothesis 6.170.15 `_settings.py` loads its `ci` profile
  (`derandomize=True`, `database=None`) when `is_in_ci()` sees `CI` or `GITHUB_ACTIONS`. `@settings(deadline=None)`
  falls back to the loaded profile (`self._fallback = parent or settings.default`), so P's two new properties are
  derandomized in CI.
- **Observability.** A refused glob part sends nothing, because `registry.send` and `registry.pages` call `expand`
  before `transport.request` or `transport.pages`. It is logged by `gitlab_wrapper.py` `_report` (`logger.error`,
  under `basicConfig`, so to stderr) and exits 1. A missing glob is logged by `call.py` `logger.error` and exits 2
  (`EXIT_REFUSED`).
- **E2E.** The check stops at the API boundary, which `always-test-e2e.md` allows, and has no human step. The
  real-forge check is tracked on open #11 ("Real-GitLab integration tests", unticked).
- **Promotion.** At promotion, `toolchain_manifest.py` `LAYOUT` maps the new F and G with the other `src/payload/`
  files. That class is the open ledger row `toolchain-promotion` (#13 Residuals X4), so there is no new finding.

### D1 — Operability names one of the two new refusals
Severity: D
Location: design.md § Operability
Defect: The section gives the refused glob part (exit 1) but not the other new refusal: a glob outside a group left
without a value, which D2's table gives as exit 2.
Proposed-edit: after "A refused glob part is logged to standard error with `registry.expand`'s message (exit 1)."
append " A glob outside an optional group given no value is refused as #41 refuses a missing path parameter: logged,
exit 2, nothing sent (D2)."

CLEAN

Verdict: READY
