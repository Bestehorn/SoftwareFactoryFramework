# Test architect — tasks review, iteration 01

## Findings

### C1 — Wave 5's runs leave out L, the structural tests over the files wave 5 writes
Severity: C
Location: tasks.md § Runs; § Wave 5
Defect: The Runs bullet gives a wave "the W, S and L files the wave writes, with 1.4's guards"; wave 5 writes no L, so
L's `test_the_forge_path_collects_every_forge_test` (AC-7.2), `test_nothing_keeps_a_forge_test_from_running` (AC-7.3)
and `test_the_forge_tests_reach_only_the_ephemeral_repository` (AC-8.1, AC-8.6), which read the four modules wave 5
writes by `--collect-only` and `ast`, first judge them in CI's `verify`, while wave 5's only local runs are the guards
and a forge run that stays red until the operator grants D6's permissions.
Material-because: none of the five classes; `verify` runs L before merge, so a wave-5 module that skips a test or
gives `--path owner=` costs one more CI run, not a regression.
Proposed-edit: in § Runs, after "with 1.4's guards", insert "; wave 5's runs add L, whose structural tests read the
forge modules wave 5 writes".

### C2 — Wave 5's declared red does not hold for 5.2, nor for 4.3's tests in the same run
Severity: C
Location: tasks.md § Wave 5 (the "Red:" sentence); 5.2
Defect: D6's permission table gives 5.2's records (`repos/get`: Metadata, "in place"; `git/get-commit`,
`git/get-tree`: Contents, "granted") and 4.3's (`repos/get`, `repos/list-for-org`) no permission "to grant", so
wherever the test credential is present those four tests pass in the run the wave declares red.
Material-because: none of the five classes; the VERIFY check that a wave's captures match the tasks they declare would
find 5.2 passing in its declared red capture.
Proposed-edit: replace "Red: the forge run fails for want of a permission D6 marks "to grant" (GitHub's `403`
"Resource not accessible by personal access token") or, locally, of the test credential file." with "Red: without the
test credential every forge test errors in the session fixture (D8); with it, 5.1, 5.3 and 5.4 fail for want of a
permission D6 marks "to grant" (GitHub's `403` "Resource not accessible by personal access token"), while 4.3 and 5.2,
whose permissions D6 marks granted or in place, pass."

### C3 — 1.1 names `load_wrapper`, a function of a test module that `--import-mode=importlib` makes unimportable
Severity: C
Location: tasks.md § 1.1
Defect: `load_wrapper` is defined in `src/payload/test/test_github_wrapper_compat.py` (C), and `pyproject.toml`
`[tool.pytest.ini_options]` `addopts` holds `--import-mode=importlib`, under which a test module is not importable by
name; W importing it from C fails at collection in its red and its green run, an import error rather than the guard.
Material-because: none of the five classes; it would make W's red the wrong reason and its green unreachable until the
import is rewritten.
Proposed-edit: replace "in-process on `load_wrapper`, `github_wrapper_fixtures.enter_project` and `FakeGitHub`" with
"in-process on `github_wrapper_fixtures.load_script` (the call C's `load_wrapper` makes), `enter_project` and
`FakeGitHub`, the fixtures module loaded by path as C loads it".

## Coverage

Every test function that the design's Acceptance Criteria Mapping assigns to a criterion is written, in the named
file, by the TEST task listed. The guards (C, P, K, V, I) are 1.4's and run in every wave. B joins wave 3.

| Criterion | TEST task(s) | State |
|---|---|---|
| AC-1.1 | 1.3, 3.1, 4.1, 4.3 | OK |
| AC-1.2 | 2.1 | OK |
| AC-1.3 | 3.1, 4.3, 5.2 | OK |
| AC-1.4 | 3.1, 4.1 | OK |
| AC-2.1 | 2.1 | OK |
| AC-2.2 | 2.1 | OK |
| AC-2.3 | 3.1 | OK |
| AC-3.1 | 2.1, 4.3 | OK |
| AC-3.2 | 2.1 | OK |
| AC-4.1 | 1.1 | OK |
| AC-4.2 | 1.1, 4.3, 5.1, 5.2, 5.3, 5.4 | OK |
| AC-4.3 | 1.1, 2.1, 2.2 | OK |
| AC-5.1 | 1.2 | OK |
| AC-5.2 | 1.2, 4.1 | OK |
| AC-5.3 | 1.3, 4.2 | OK |
| AC-5.4 | 1.2 | OK |
| AC-6.1 | 1.3 | OK |
| AC-6.2 | 3.1 | OK |
| AC-6.3 | 1.2, 1.3, 3.1 | OK |
| AC-7.1 | 1.2 | OK |
| AC-7.2 | 4.1 | OK |
| AC-7.3 | 4.1 | OK |
| AC-8.1 | 2.2, 4.3, 5.1, 5.2, 5.3, 5.4 | OK |
| AC-8.2 | 5.1 | OK |
| AC-8.3 | 5.2 | OK |
| AC-8.4 | 5.3 | OK |
| AC-8.5 | 5.4 | OK |
| AC-8.6 | 2.2 | OK |
| AC-9.1 | 3.2 | OK |
| AC-9.2 | 3.2 (with B) | OK |
| AC-9.3 | 3.2 | OK |
| UB-1 | 1.1, 1.2, 1.3, 2.1 | OK |
| UB-2 | 3.1 | OK |
| UB-3 | 1.1, 1.4 | OK |
| UB-4 | 1.4 | OK |

35 OK, 0 GAP.

CLEAN — TEST-READY
