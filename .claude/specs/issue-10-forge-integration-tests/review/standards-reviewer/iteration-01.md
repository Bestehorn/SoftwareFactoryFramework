# Standards review — design, iteration 01

### B1 — Two exception classes hide their base in their names
Severity: B
Location: design.md § D9 "The teardown guard" and "The sweep"; § D10 `test/forge/ephemeral.py` row; § Correctness Properties AC-2.2, AC-3.1/AC-3.2
Defect: `TeardownRefusedError` and `SweepRefusedError` subclass `ForgeSuiteError` but, unlike `ForgeSetupError` and `ForgeCommandError`, carry no `Forge` in their names, against `coding-standards.md` rule 9 ("The inheritance hierarchy must be visible from class names") and every exception family of the codebase (`Manifest*Error(ManifestError)` in `scripts/toolchain_manifest.py`, `GitHub*Error(GitHubAPIError)` in `github_api/errors.py`, `GitLab*Error(GitLabAPIError)` in `gitlab_api/errors.py`).
Material-because: unmaintainable-by-rule coding-standards.md — rule 9 requires the name to show that these are `ForgeSuiteError`s.
Proposed-edit: replace `TeardownRefusedError` with `ForgeTeardownRefusedError` and `SweepRefusedError` with `ForgeSweepRefusedError` everywhere in design.md (D9, D10, the Correctness Properties of AC-2.2 and AC-3.1/AC-3.2).

### C1 — The design does not state why `ci.yml` may be edited
Severity: C
Location: design.md § D5, first paragraph
Defect: `project-specific.md`'s table and the map's "Two halves" table list `.github/workflows/` as toolchain, "promotion only", with `templates/ci/` as its product. The edit conforms anyway: rule 1 defines the toolchain as "listed in `config/toolchain.json`", which lists no workflow; its `not_installed` entry `templates/ci/*` records "`.github/workflows/ci.yml` is the project's own"; `templates/ci/` holds no `ci.yml` source; and `gate_toolchain_paths.py` and `test_toolchain_integrity.py` judge only `files`. D5 does not say any of this. Only `prompt.md` does.
Proposed-edit: append to D5's first paragraph: "`ci.yml` is not toolchain: `config/toolchain.json` lists no workflow, its `not_installed` entry `templates/ci/*` records `ci.yml` as this project's own, and `templates/ci/` holds no source for it." Residual (a ledger row, not this change): `project-specific.md` and `docs/forLLMConsumption.md` "Two halves" call `.github/workflows/` promotion-only.

### C2 — "No deviation" leaves out the one CI check that does not go through `run_checks.py`
Severity: C
Location: design.md § Overview, "Patterns followed"
Defect: `remote-ci-must-pass.md` says "every CI job runs `scripts/run_checks.py`" and `ci-owns-the-test-suite.md` calls it "the same command CI runs, so a local pipeline cannot drift from the real one". The forge job's check is `run_tests.py`, so a local `run_checks.py` no longer reproduces every CI check. D5's Alternatives give the reason, but the Overview says "No deviation".
Proposed-edit: replace "No deviation." with "One deviation: the forge job's check is `python scripts/run_tests.py --workers 1 test/forge`, not a `run_checks.py` group, because `run_checks.py` is toolchain (D5 Alternatives); a local `run_checks.py` does not run the forge suite."

### C3 — The guard's prefix constant is defined twice
Severity: C
Location: design.md § D10, `test/forge/ephemeral.py` row; § D2; § D4
Defect: D2 defines `TEST_MARKER_OPTION` and `EPHEMERAL_REPOSITORY_PREFIX` in the product wrapper. D10 then puts "the constants D3 to D9 name" into `ephemeral.py`, and `EPHEMERAL_REPOSITORY_PREFIX` is among them (D4, D9), so one value gets a second definition (`design-principles.md` rule 2, reuse first). D8 already reads `_one_token` and `PLACEHOLDER` from `product_wrapper()`.
Proposed-edit: in D10's `ephemeral.py` row, after "the constants D3 to D9 name", insert "except `TEST_MARKER_OPTION` and `EPHEMERAL_REPOSITORY_PREFIX`, which it reads from `product_wrapper()` as it reads `_one_token` and `PLACEHOLDER`".

### C4 — `always-test-e2e.md`'s default location is not discussed
Severity: C
Location: design.md § D1, Alternatives
Defect: `always-test-e2e.md` puts the end-to-end check "under `test/e2e/` (or the project's equivalent)". The design makes the forge suite this change's end-to-end check but never says why `test/e2e/` is not used.
Proposed-edit: add to D1's Alternatives: "`test/e2e/` (`run_checks.py` `e2e_argv`, a post-merge group that runs only on request and that `ci.yml` does not run, whereas S4 runs the suite on every pull request; `test/forge/` is this project's equivalent)."

### C5 — The map names the credential file but not its setup note
Severity: C
Location: design.md § D10, `docs/forLLMConsumption.md` row
Defect: `tests-must-not-fail-procedures.md` ("Missing credentials: ... document the credential setup in `docs/forLLMConsumption.md`") and `pre-work.md` (the map holds "pointers to topic docs") both expect the map to lead to the setup. D10's row names the test credential file but not `credentials/README.md`.
Proposed-edit: in D10's map row, replace "the test credential file" with "the test credential file and its setup note `credentials/README.md`".

### D1 — The sweep's description shows a positional call
Severity: D
Location: design.md § D9, "The sweep"
Defect: `RepositoryRecord.of(item)` is written positionally, against `coding-standards.md` rule 4 and D10's own "Every function takes named parameters".
Proposed-edit: `RepositoryRecord.of(item=<item>)`.

## Brief items judged with no finding

1. D1 makes a separate suite, not an exclusion. `tests-must-not-fail.md` forbids "excluding the test file from a test config (`pyproject.toml` `[tool.pytest.ini_options]`, `pytest.ini`, `conftest.py` collect hooks)" and "any other mechanism that prevents the test from executing or from failing the build when it fails". D1 takes nothing out of any collection. `pyproject.toml` sets no `python_files`, and pytest's defaults never matched `forge_*.py`. `test/forge/pytest.ini` defines what the suite's own run collects. The forge job runs the whole suite on every pull request, and `report` fails when it fails. That is the hook-suite precedent (`src/hooks/tests/pytest.ini`, `hook_suite_argv`). `testing.md` rule 1 ("`test/` (tests of the framework itself") holds, and `test/` already tests the product wrapper (`test_github_wrapper_fork_parity.py`, `_contract.py`, `_coverage.py`). Rule 5 is the purpose of the suite.
2. The step `env:` (D5, D8) is allowed. `no-environment-vars.md` forbids "`set`, `setx`, `export`, or `$env:VAR=...`". Its CLARIFICATION exempts "scoped configuration consumed by ... one specific subprocess, and do not pollute global state", which describes a step-level `env:` on an ephemeral runner: nothing is exported and no later step sees the variable. AC-6.3 names this one exception. `use-git-wrapper-scripts.md`'s "no env-var fallbacks" applies to the wrapper, and the wrapper reads no environment (D2 uses `sys._xoptions`).
3. `use-git-wrapper-scripts.md`: every API request is a product-wrapper subcommand or `call`, and git fetch/push are on its Allowed list. There is no `gh`, curl or urllib.
4. UB-4: no file in D10 is a `config/toolchain.json` `files` key (C1 covers `ci.yml`).
5. `file-organization.md` and `test_layout.py`: the new Python lives under `test/` and `src/` only, and `.gitignore` `!credentials/README.md` tracks `credentials/README.md`, as `prompts/setup-claude.txt` prescribes for every project.
6. `coding-standards.md`: keyword-only signatures, JSON constants, logging, `pathlib`, and `ForgeSuiteError` (`details=None`) as the base all conform, apart from B1 and D1.
7. The `ci.yml` header contract holds. `forge` has no `needs:` and one check command (`run_tests.py`: `reject_failfast`, `-ra`), and its credential step is setup, like `verify`'s `pip install`. `report` has `needs: [verify, forge]` and `if: always()`, and fails unless `needs.forge.result` is `success`.

NOT-CLEAN (0 A, 1 B)
