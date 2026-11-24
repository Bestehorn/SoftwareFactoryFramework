# Test architect — tasks review, iteration 01

## Findings

### C1 — 1.1 and 1.3 load modules by path but never say "registered in `sys.modules` first"
Severity: C
Location: tasks.md § 1.1; § 1.3
Defect: `pyproject.toml` `addopts` holds `--import-mode=importlib`, and no `conftest.py` puts `src/payload/test` on
`sys.path`, so W can reach `gitlab_wrapper_fixtures` only by path, as every GitLab suite does (C `load_fixtures`).
Separately, L declares `@dataclass(frozen=True)` classes under `from __future__ import annotations`. Creating them
reads `sys.modules.get(cls.__module__).__dict__` (`dataclasses.py` `_is_type`), so G's by-path load of L raises unless
L is registered first, as #10's S `_load_by_path` registers its modules.
Material-because: none of the five classes. A plain import, or an unregistered load, errors at collection. The
`red_for_right_reason.py` `judge` refuses such a capture, and the green run cannot pass, so wave 1's red run catches
it.
Proposed-edit: in 1.1, after "`run_main`)" insert ", the fixtures module loaded by path as C's `load_fixtures` loads
it"; in 1.3, replace "it loads L by path" with "it loads L by path, registered in `sys.modules` before it runs as
S's `_load_by_path` does,".

### C2 — Wave 4's runs leave out S, although 4.9 edits the module S tests
Severity: C
Location: tasks.md § Runs; § 4.9
Defect: The Runs bullet gives each wave "the W, S, G and L files the wave writes". Wave 4 writes no S file, but 4.9
edits `test/forge_gitlab/ephemeral.py`, whose parts 1 to 3 are exercised in the default collection only by S. A 4.9
edit that breaks those parts would first show up in CI's `verify`.
Material-because: none of the five classes. `verify` runs S before merge, so the cost is one more CI run (#10 tasks
review C1).
Proposed-edit: in § Runs, after "with 1.4's guards", insert "; wave 4's runs add S, since 4.9 edits the module S
loads".

### C3 — 1.4's guards leave out existing default-collection tests that read files this change edits
Severity: C
Location: tasks.md § 1.4
Defect: `src/payload/test/test_wrapper_delivery.py` loads `src/payload/scripts/gitlab_wrapper.py` (its `ROOT` is
`src/payload`) and asserts `steward_delegate` and `EXIT_DELIVERY_ELSEWHERE`. Those are the very places 1.6 changes,
so it is one of the existing wrapper tests UB-3 keeps. Four more tests read files this change edits:
- `test/test_layout.py` checks the framework paths and relative links of every tracked live file, including the setup
  note, the map, `ci.yml` and the wrapper's docstrings.
- `test/test_gitlab_graphql_contract.py` and `test/test_github_graphql_contract.py` (each `test_the_map_names_the_graphql_call`)
  and `test/test_toolchain_manifest.py` (`test_the_map_names_the_manifest_command_of_the_promotion`) read
  `docs/forLLMConsumption.md`, which 3.5 edits.

None of these five files is in any wave's runs.
Material-because: none of the five classes. `verify` runs every one of them before merge (UB-1), so a break costs one
CI run, not a regression.
Proposed-edit: in 1.4's Files, after "src/payload/test/test_gitlab_api_*.py," insert
"src/payload/test/test_wrapper_delivery.py, test/test_layout.py, test/test_gitlab_graphql_contract.py,
test/test_github_graphql_contract.py, test/test_toolchain_manifest.py,".

## Coverage

Each wave lists every TEST task before its IMPL tasks, and the tasks of a wave own disjoint files: 1.4 writes nothing,
and only 1.5 edits L. Every test function the design's Acceptance Criteria Mapping assigns is written in its named
file by the TEST task listed below:
- W: 5 functions, in 1.1.
- S: 16 functions, in 1.2, 2.1 and 3.1.
- G: 11 functions, in 1.3, 2.2, 3.2 and 4.1.
- F: 12 functions, in 4.2 to 4.6.
- L `test_the_report_judges_the_forge_job` in 1.5, and B in 1.4.

Every wave's red run can fail on an assertion rather than a load error, given what the earlier waves built:
- S's loads, and its 2.1 and 3.1 doubles, happen inside test bodies (1.2).
- G reads the subjects that are still missing inside its test bodies.
- 2.2 stays red until 2.3, because `product_wrapper_problems` requires `PRODUCT_WRAPPER` in `SubprocessWrapperRunner`.
- Wave 4's collection test stays red until 4.7 and 4.8, because the root configuration's `python_files` collects no
  `forge_*.py`.

L stays green with only 1.5's edit. Its verdict guard matches only `needs.forge.result`, and its `product_wrapper_problems`
walks the whole `FunctionDef`, argument defaults included, so 1.8's `product_wrapper(path=PRODUCT_WRAPPER, ...)`
passes. `ci.yml` is listed under `config/toolchain.json` `not_installed` (`templates/ci/*`), so 1.7 leaves I green.
F.1 runs every F module against gitlab.com in `forge-gitlab`, and `report` judges it.

| Criterion | TEST task(s) | State |
|---|---|---|
| AC-1.1 | 1.2, 3.1, 4.1, 4.2 | OK |
| AC-1.2 | 1.2 | OK |
| AC-1.3 | 3.1, 4.2, 4.3, 4.4 | OK |
| AC-1.4 | 3.1, 4.1 | OK |
| AC-2.1 | 2.1 | OK |
| AC-2.2 | 2.1 | OK |
| AC-2.3 | 3.1 | OK |
| AC-3.1 | 2.1, 4.2 | OK |
| AC-3.2 | 2.1 | OK |
| AC-3.3 | 2.1 | OK |
| AC-4.1 | 1.1 | OK |
| AC-4.2 | 1.1, 4.2, 4.3, 4.4, 4.5, 4.6 | OK |
| AC-4.3 | 1.1, 2.1, 2.2 | OK |
| AC-5.1 | 1.3 (F.1) | OK |
| AC-5.2 | 1.3, 4.1 (F.1) | OK |
| AC-5.3 | 1.2 | OK |
| AC-5.4 | 1.3, 1.5 | OK |
| AC-6.1 | 1.2 | OK |
| AC-6.2 | 3.1 | OK |
| AC-6.3 | 1.2, 1.3, 3.1 | OK |
| AC-7.1 | 1.3 | OK |
| AC-7.2 | 4.1 | OK |
| AC-7.3 | 4.1 | OK |
| AC-8.1 | 2.2, 4.2, 4.3, 4.4, 4.5, 4.6 | OK |
| AC-8.2 | 4.3 | OK |
| AC-8.3 | 4.2, 4.4 | OK |
| AC-8.4 | 4.5 | OK |
| AC-8.5 | 4.1, 4.6 | OK |
| AC-8.6 | 4.1, 4.6 | OK |
| AC-8.7 | 2.2 | OK |
| AC-9.1 | 3.2 | OK |
| AC-9.2 | 3.2, 1.4 (B) | OK |
| UB-1 | 1.1, 1.2, 1.3, 1.4, 2.1 | OK |
| UB-2 | 3.1 | OK |
| UB-3 | 1.1, 1.4 | OK |
| UB-4 | 1.4 (H, L), 1.5 | OK |
| UB-5 | 1.4 (I) | OK |

37 OK, 0 GAP.

CLEAN — TEST-READY
