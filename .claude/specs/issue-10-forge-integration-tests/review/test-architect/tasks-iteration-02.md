# Test architect — tasks review, iteration 02 (delta)

## Iteration 01 findings

- C1 applied: B2 moves the forge modules into wave 4 (4.3, 4.7 to 4.10). Wave 4 writes L (4.1), so L's
  `test_the_forge_tests_reach_only_the_ephemeral_repository`, `test_the_forge_path_collects_every_forge_test` and
  `test_nothing_keeps_a_forge_test_from_running` judge those modules in wave 4's red and green captures. The Runs
  bullet says so.
- C2 applied: no "Red:" sentence is left, either for 4.3 or for the forge modules, and no reference to wave 5 remains.
- C3 applied: 1.1 names `github_wrapper_fixtures.load_script`. That function exists in
  `src/payload/test/github_wrapper_fixtures.py`, and `test_github_wrapper_compat.py` `load_wrapper` returns
  `fx.load_script(...)`, where `fx = _load_fixtures()` is the by-path load 1.1 now copies.

## Delta findings

None. These are the delta's fix sites, checked against the artefacts they depend on:

- 1.3: S loads `ephemeral.py` inside each test body, and the doubles of 2.1 and 3.1 and 4.2's load of
  `write_credential.py` are built the same way. A missing file or symbol therefore fails inside the test body, and the
  short summary (`-ra` in `pyproject.toml` `addopts`) prints it as `FAILED <path>::<test>`.
  `.claude/hooks/red_for_right_reason.py` `judge` counts that line as a right reason (`FAILED .*::`). It refuses a
  capture only when `ERROR collecting` or `errors during collection` also appears, and none can appear here. The red
  runs of waves 1, 2 and 4 pass the RED step.
- Wave 4's red capture: `pytest.ini` (4.4) and `conftest.py` (4.5) are absent, so 4.1's tests fail on assertions. The
  configparser read finds no keys, collection lists none of the `test_` functions `ast` finds, and `ast` finds no
  `ephemeral_repository`. 4.2 fails because `write_credential.py` is absent. 1.2's
  `test_the_default_configuration_collects_no_forge_test` stays green, since `forge_*.py` matches no default
  `python_files` pattern. The forge modules arrive in the TEST step, and 2.2 judges them in both captures.
- Wave 4 ownership: the ten tasks own ten distinct files. No IMPL task validates AC-8.2 to AC-8.5, so 4.7 to 4.10 pair
  with no IMPL task. The conductor dispatches every TEST task of a wave before any IMPL task
  (`spec-phase-implement.md` § IMPLEMENT). The test-first rule of `spec-phase-tasks.md` therefore holds, even though
  4.7 to 4.10 are listed after 4.6.
- 3.3 `CHECKOUT`: no test of waves 1 to 3 reads it. 4.5 and 4.6 use it in a later wave.
- 4.6: `write_credential.py` loads `ephemeral.py` by path. That does not break 2.2's `ast` rules: it imports no
  `subprocess`, names no `product_wrapper` and reads no attribute `main`.
- F.1: it covers AC-5.1 and the criteria of 4.3 and 4.7 to 4.10. Every test in those tasks can fail: each one asserts
  an exit code and the printed JSON (design § Correctness Properties AC-8.1).

## Coverage

The guards (C, P, K, V, I) belong to 1.4 and run in every wave. B joins wave 3. F.1 runs every F test against
github.com.

| Criterion | TEST task(s) | State |
|---|---|---|
| AC-1.1 | 1.3, 3.1, 4.1, 4.3 | OK |
| AC-1.2 | 2.1 | OK |
| AC-1.3 | 3.1, 4.3, 4.8 | OK |
| AC-1.4 | 3.1, 4.1 | OK |
| AC-2.1 | 2.1 | OK |
| AC-2.2 | 2.1 | OK |
| AC-2.3 | 3.1 | OK |
| AC-3.1 | 2.1, 4.3 | OK |
| AC-3.2 | 2.1 | OK |
| AC-4.1 | 1.1 | OK |
| AC-4.2 | 1.1, 4.3, 4.7, 4.8, 4.9, 4.10 | OK |
| AC-4.3 | 1.1, 2.1, 2.2 | OK |
| AC-5.1 | 1.2 (F.1) | OK |
| AC-5.2 | 1.2, 4.1 | OK |
| AC-5.3 | 1.3, 4.2 | OK |
| AC-5.4 | 1.2 | OK |
| AC-6.1 | 1.3 | OK |
| AC-6.2 | 3.1 | OK |
| AC-6.3 | 1.2, 1.3, 3.1 | OK |
| AC-7.1 | 1.2 | OK |
| AC-7.2 | 4.1 | OK |
| AC-7.3 | 4.1 | OK |
| AC-8.1 | 2.2, 4.3, 4.7, 4.8, 4.9, 4.10 | OK |
| AC-8.2 | 4.7 | OK |
| AC-8.3 | 4.8 | OK |
| AC-8.4 | 4.9 | OK |
| AC-8.5 | 4.10 | OK |
| AC-8.6 | 2.2 | OK |
| AC-9.1 | 3.2 | OK |
| AC-9.2 | 3.2 (with B) | OK |
| AC-9.3 | 3.2 | OK |
| UB-1 | 1.1, 1.2, 1.3, 2.1 | OK |
| UB-2 | 3.1 | OK |
| UB-3 | 1.1, 1.4 | OK |
| UB-4 | 1.4 | OK |

35 OK, 0 GAP. TEST-READY.

CLEAN
