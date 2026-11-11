# Design review — devops-iac-reviewer — iteration 02 (delta)

Fix sites of iteration 01:

- B1 resolved. AC-1.3's property is now H, `test/test_github_api_call_properties.py` (Testing Strategy "Unit tests",
  Correctness Properties AC-1.3, Acceptance Criteria Mapping, D8). Security Considerations "Dependencies" is now true:
  `hypothesis` is in `pyproject.toml`'s `dev` extra, which CI installs (`.github/workflows/ci.yml`
  `pip install -e ".[dev]"`). CI's `tests` leg collects H: `run_checks.py` `tests_argv` passes no paths, so pytest
  uses `testpaths` (it includes `test`) with `--import-mode=importlib`. `.hypothesis/` is in `.gitignore`. No
  `scripts/github_api/` exists to shadow the product package. `config/toolchain.json` claims no `test/` path other
  than `test/test_instruction_corpus_budget.py`, so the `toolchain-paths` gate does not refuse H. "As V does" means
  `@pytest.mark.usefixtures("scripts_on_path")`. The installed plugin (`_hypothesis_pytestplugin.py`, hypothesis
  6.170.15) skips any fixture whose name is not in the test's signature (`if fx.argname not in argnames: continue`),
  so the `function_scoped_fixture` health check does not fail H.
- C1 resolved. D7 "The map" puts the sentence before the closing sentence, which stays last and says the fork has no
  `call`. This matches the current bullet ("Not yet installed here: sessions run the fork (`config/toolchain.json`).").
- D1 resolved. Testing Strategy "E2E." names `main`'s argv for K and N, and C `test_the_script_runs_by_path` for the
  by-path run. That test exists in `src/payload/test/test_github_wrapper_compat.py` and runs `ENTRY_SCRIPT` in a
  child interpreter.

No new finding. Operability "Not applicable" still holds. The delta adds one test file under `test/` and changes no
deploy, CI or toolchain file.

Verdict: CLEAN
