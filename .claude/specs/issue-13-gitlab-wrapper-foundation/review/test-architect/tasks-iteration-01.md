# Test architect — tasks review, iteration 01 (issue #13, tier M)

The tasks.md coverage table matches the tasks. The 26 family modules of 3.3–3.11 match the 26 stems of
`docs/api-reference/gitlab/rest/`. In every wave the TEST tasks come before the IMPL tasks, and no two tasks of a wave
share a file.

### B1 — No test fails when the entry script's import bootstrap is missing
Severity: B
Location: tasks.md § Wave 3, task 3.2
Defect: D3's bootstrap matters only when `gitlab_wrapper.py` is loaded by path, and no planned test can see it missing.
Under `--import-mode=importlib` (`pyproject.toml`), R, T, P and V put `src/payload/scripts` on `sys.path` and import
`gitlab_api` at collection, before `test_wrapper_delivery.py` runs. The two subprocess tests start
`python <scripts dir>/gitlab_wrapper.py`, and Python itself puts that directory first on `sys.path` (D3). So an entry
script without the bootstrap passes every capture and every CI run.
Material-because: UB-1 (`test_wrapper_delivery.py` SHALL CONTINUE TO pass unchanged). `prompts/setup-claude.txt`
installs it as `test/test_wrapper_delivery.py` and copies none of R, T or C, so in a project it loads the wrapper by path
with nothing else on `sys.path` and fails with `ModuleNotFoundError` (regression).
Proposed-edit: in 3.2, after "the subprocess `test_script_usage_error_exits_2`", add ", and the subprocess
`test_script_loads_by_path` — `sys.executable -c` loads `<scripts dir>/gitlab_wrapper.py` with
`importlib.util.spec_from_file_location` and `exec_module`, `cwd=tmp_path`, and exits 0". In design.md § Testing
Strategy "Subcommands", replace "Two subprocess tests run `sys.executable <scripts dir>/gitlab_wrapper.py` with
`cwd=tmp_path`, proving the bootstrap when the script is run." with "Subprocess tests run with `cwd=tmp_path`: two run
`sys.executable <scripts dir>/gitlab_wrapper.py`, and `test_script_loads_by_path` loads the file by path in a fresh
interpreter, the one place the bootstrap is exercised." Add `test_script_loads_by_path` to the UB-1 row of § Acceptance
Criteria Mapping.

### C1 — A later wave's import at the top of a module turns that module's earlier tests into collection errors
Severity: C
Location: tasks.md § 2.2, § 5.1
Defect: 2.2 needs `gitlab_api.transport`, which 2.4 creates, and 5.1 needs `gitlab_api.commands.pipeline`, which 5.3
creates. If either is imported at the top of R or C, that module cannot be collected in the wave's red capture. The
capture then shows neither the earlier waves' tests still passing nor the new test failing on its own assertion.
Proposed-edit: append "— `Transport` imported inside the test" to 2.2, and append "— imported inside the test" to
5.1's `pipeline_wait` clause.

### C2 — R's `ValueError` checks cannot tell the refusals apart
Severity: C
Location: tasks.md § 1.1 `test_lookup_refuses_unknown_and_duplicate_ids`, § 2.2
Defect: D5 raises `ValueError` both for an unknown id and for an undeclared value, and no family declares a record
before wave 3. A 2.2 that names a real id (`plan#create-an-issue`) gets "unknown id" in wave 2 and passes while the
undeclared-value refusal is missing. A duplicate case whose injected records `lookup` does not see passes the same way.
Proposed-edit: in 2.2, replace "raises `ValueError` and nothing is recorded" with "on a `RestOperation` the test builds
and serves through `monkeypatch.setattr(registry, "lookup", …)`, raises `ValueError` whose message names the
undeclared value, and nothing is recorded". In 1.1, after `test_lookup_refuses_unknown_and_duplicate_ids`, add "(each
case matches its message: the unknown id, the twice-declared id)".

## Coverage

| Criterion | TEST task(s) | Status |
|---|---|---|
| AC-1.1 | 1.1, 2.2 (C2); review D1 | OK |
| AC-1.2 | 1.3 | OK |
| AC-1.3 | F.2; review D2 table | OK |
| AC-2.1 | 2.1 | OK |
| AC-2.2 | 1.1, 1.2 | OK |
| AC-2.3 | 1.1, 1.2, 2.1 | OK |
| AC-2.4 | 2.1 | OK |
| AC-2.5 | 2.1 | OK |
| AC-2.6 | 2.1 | OK |
| AC-3.1 | 2.1 | OK |
| AC-3.2 | 2.1 | OK |
| AC-3.3 | 2.1 | OK |
| AC-3.4 | 2.1 | OK |
| AC-3.5 | 2.1 | OK |
| AC-4.1 | 2.1 | OK |
| AC-4.2 | 2.1 | OK |
| AC-4.3 | 2.1 | OK |
| AC-5.1 | 1.3 | OK |
| AC-5.2 | 1.3 | OK |
| AC-5.3 | 3.1 | OK |
| AC-5.4 | 3.1 | OK |
| UB-1 | 3.2, 4.1, 5.1, 5.2; D unedited | OK — loading by path is open (B1) |
| UB-2 | 2.3, 3.2, 4.1 | OK |
| UB-3 | F.2 | OK |

Verdict: NOT-TEST-READY — NOT-CLEAN (0 A, 1 B); 24 OK, 0 GAP.
