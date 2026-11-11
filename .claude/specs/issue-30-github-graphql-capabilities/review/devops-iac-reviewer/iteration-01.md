# Design review — devops-iac-reviewer — iteration 01

The change touches no workflow, no check runner and no deploy path. The facts behind CLEAN:

- CI collects both new suites. `.github/workflows/ci.yml` job `verify`, leg `tests`, runs `scripts/run_checks.py --group
  tests`, which calls `scripts/run_tests.py` with no path. pytest then collects `testpaths` (`src/hooks/tests`,
  `src/payload/test`, `test`), so G and Q are both collected, and so are R's and V's new tests. No conftest filters
  collection. The `--cov=src` 80% gate covers the new `registry.py` and `call.py` code that G and R exercise.
  `docs/api-reference/github/graphql/*.md` and `operations-index.md` are tracked, so Q reads them on the runner.
  Between `aafecbb` and `origin/main` (`f374b3d`) no CI, runner, `pyproject.toml` or fixture file changed.
- The API-boundary E2E proof is stated, together with its job: requirements "Out of scope" and Testing Strategy
  "E2E." (G through `main` in CI's `tests` leg; the real-forge run is #10's). This is #28's accepted arrangement.
- The AC-2.4 cases do not slow CI. `Transport._send` retries only a rate limit, through the injected `sleep`, with
  `retry-after: 0`. A `502` and a `URLError` raise at once.
- "Operability: Not applicable" holds. `config/toolchain.json` maps the installed `scripts/github_wrapper.py` to the
  chess fork (a recorded deviation), so no session runs this code before a release is promoted. The new failure modes
  are logged (AC-2.4, AC-3.1). There is no persisted state, so rollback is a revert of the merge.
- D7's map text names no `FRAMEWORK_PATH` token, so `test/test_layout.py` is unaffected.

### C1 — D6 states #10's real-forge run as a present proof
Severity: C
Location: design.md § D6 "What an `sff-test-*` repository cannot exercise", the closing sentence
Defect: "Every other record is proven by Q, G and #10's real-forge run" reads as current evidence. #10's fixture does
  not exist, and requirements "Out of scope" says so ("Until it exists, …").
Proposed-edit: replace "Every other record is proven by Q, G and #10's real-forge run." with "Every other record is
  proven by Q and G in CI's `tests` leg, and by #10's real-forge run once its fixture exists (requirements "Out of
  scope")."

### D1 — Operability gives no reason why no session runs the change
Severity: D
Location: design.md § Operability
Defect: "Nothing deploys" is true but leaves out why no session here runs the product wrapper, which #28 stated.
Proposed-edit: replace "Not applicable: nothing deploys." with "Not applicable. Nothing deploys, and a session here
  runs the product wrapper only after a release is promoted (`config/toolchain.json` deviation for
  `scripts/github_wrapper.py`)."

Verdict: CLEAN
