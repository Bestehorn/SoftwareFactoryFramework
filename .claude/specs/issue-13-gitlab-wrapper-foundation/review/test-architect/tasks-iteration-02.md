# Test architect — tasks review, iteration 02 (delta; issue #13, tier M)

B1 resolved. 3.2 adds the subprocess `test_script_loads_by_path`, and design.md names it in § Testing Strategy
"Subcommands" and in the UB-1 row of § Acceptance Criteria Mapping. Its oracle fails when the defect is present. A
`python -c` interpreter started with `cwd=tmp_path` finds `gitlab_api` on no `sys.path` entry: the venv's only `.pth` is
`a1_coverage.pth`, and no workflow, runner or conftest sets `PYTHONPATH`. So an entry script that imports `gitlab_api`
without D3's bootstrap raises `ModuleNotFoundError` and exits 1. The test passes against today's skeleton, and that is
correct for an unchanged-behaviour guard: `test_wrapper_delivery.py`, the UB-1 test it covers, passes today as well. It
goes red at exactly the regression it guards. Accepted.

C1 resolved: 2.2 imports `Transport` inside the test, and 5.1 imports `pipeline_wait` inside the test. C2 resolved: 2.2
serves a `RestOperation` the test builds through a monkeypatched `lookup` and checks that the message names the
undeclared value. 1.1 serves its synthetic records through a monkeypatched `registry.discover_families`, so `lookup` sees
them, and checks each message. The changed text in 1.2 and 5.5 does not weaken their oracles: 1.2's join is the one D4
names, and 5.5 edits exactly what 5.2 asserts. In every wave the TEST tasks still come first and no two tasks share a
file.

### C1 — Reverting wave 3 does not make `test_script_loads_by_path` fail
Severity: C
Location: tasks.md § 3.2
Defect: Wave 3 reverted means the skeleton, which imports no `gitlab_api`, and the test passes against it. To make it
fail, the verifier's "passes without its behaviour" check needs a targeted mutant.
Proposed-edit: in 3.2, after "and exits 0)" add " — green before 3.12 by design; its mutant is 3.12 with the bootstrap
removed".

## Coverage

| Criterion | TEST task(s) | Status |
|---|---|---|
| AC-1.1 | 1.1, 2.2 | COVERED |
| AC-1.2 | 1.3 | COVERED |
| AC-1.3 | F.2 | COVERED |
| AC-2.1 | 2.1 | COVERED |
| AC-2.2 | 1.1, 1.2 | COVERED |
| AC-2.3 | 1.1, 1.2, 2.1 | COVERED |
| AC-2.4 | 2.1 | COVERED |
| AC-2.5 | 2.1 | COVERED |
| AC-2.6 | 2.1 | COVERED |
| AC-3.1 | 2.1 | COVERED |
| AC-3.2 | 2.1 | COVERED |
| AC-3.3 | 2.1 | COVERED |
| AC-3.4 | 2.1 | COVERED |
| AC-3.5 | 2.1 | COVERED |
| AC-4.1 | 2.1 | COVERED |
| AC-4.2 | 2.1 | COVERED |
| AC-4.3 | 2.1 | COVERED |
| AC-5.1 | 1.3 | COVERED |
| AC-5.2 | 1.3 | COVERED |
| AC-5.3 | 3.1 | COVERED |
| AC-5.4 | 3.1 | COVERED |
| UB-1 | 3.2 (incl. `test_script_loads_by_path`), 4.1, 5.1, 5.2; D unedited | COVERED |
| UB-2 | 2.3, 3.2, 4.1 | COVERED |
| UB-3 | F.2 | COVERED |

Verdict: TEST-READY — CLEAN (0 A, 0 B); 24 COVERED, 0 GAP.
