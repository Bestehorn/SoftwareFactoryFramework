# Test architect — design review, iteration 02 (delta)

## Iteration-01 findings

- B1 resolved: AC-1.1 and its mapping row name S `test_a_distributed_run_is_refused` (`gw0` raises naming
  `--workers 1`, `master` returns).
- B2 resolved: L `test_the_session_fixture_wraps_one_provision` pins `scope="session"`, the refusal before `provision`
  and the one `yield` inside `with provision(...)`, under AC-1.1 and AC-1.4 and in both mapping rows.
- B3 resolved: AC-7.3 reads `test/forge/pytest.ini` with `configparser` and requires exactly `python_files`,
  `addopts`, `log_cli` and `log_cli_level` with D1 Mechanism's values; the test is in AC-5.2's property and mapping row.
- B4 resolved: AC-6.3's example adds the `caplog` (`DEBUG`) check and the `repr` of the yielded `EphemeralRepository`.
- C1 to C6 applied as proposed; AC-5.1's `on:` oracle matches the current `.github/workflows/ci.yml` `on:` block.

## Findings

### B1 — An in-process `main` call through `product_wrapper()` escapes AC-4.3's restated oracle
Severity: B
Location: design.md § Correctness Properties AC-4.3 (L `test_the_forge_tests_reach_only_the_ephemeral_repository`), AC-8.1
Defect: The restated check (iteration-01 C2) looks only at `subprocess` imports and `PRODUCT_WRAPPER` names, but D10's
`product_wrapper()` returns the loaded wrapper module, so a forge module calling `product_wrapper().main(argv=...)`
runs the wrapper in the pytest process without `-X sff_test_marker` (no origin guard; `_detect_repo` and `_load_token`
read the working directory's `.git/config` and `credentials/github-pat.txt`), and every listed test stays green.
Material-because: AC-4.3 (the marker on every product-wrapper invocation the suite makes) and AC-8.1 (each real-forge
test runs the wrapper as a subprocess with the marker set) are untested on the one other route the design provides.
Proposed-edit: in AC-4.3, replace "and `PRODUCT_WRAPPER` is named only in `SubprocessWrapperRunner` and
`product_wrapper`" with "`PRODUCT_WRAPPER` is named, outside its definition, only in `SubprocessWrapperRunner` and
`product_wrapper`; by `ast`, no file of `test/forge/` but `ephemeral.py` names `product_wrapper`, and no file of
`test/forge/` reads an attribute `main`".

### C1 — AC-6.1's restated first branch has no linked-worktree case
Severity: C
Location: design.md § Correctness Properties AC-6.1
Defect: The restated AC-6.1 (DL-002) prefers a linked worktree's own file; S's example covers a main tree with the
file and a worktree without it, so a lookup that always takes the main tree's file for a linked worktree passes.
Proposed-edit: after "finds the main tree's" add "; the worktree given its own file, holding a token other than the
main tree's, finds its own".

### C2 — The structural fixture check accepts a constant worker id
Severity: C
Location: design.md § Correctness Properties AC-1.1 (L `test_the_session_fixture_wraps_one_provision`)
Defect: `refuse_distributed_run(worker_id="master")` inside the fixture satisfies "calls `refuse_distributed_run`
before `provision`" and never refuses.
Proposed-edit: replace "calls `refuse_distributed_run` before `provision`" with "calls `refuse_distributed_run` with
its own `worker_id` parameter (`worker_id=worker_id`) before `provision`".

### D1 — `ast` over a file that is not Python
Severity: D
Location: design.md § Correctness Properties AC-7.3
Proposed-edit: replace "in no file of `test/forge/`, by `ast`," with "in no `.py` file of `test/forge/`, by `ast`,".

## Coverage

Tests by the design's legend (W, S, L, F, B, C, P, K, V, I).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning, S distributed run; L session fixture | OK |
| AC-1.2 | S run id | OK |
| AC-1.3 | F fixture, F repos_git; S provisioning (workflow seed, workspace removed) | OK |
| AC-1.4 | S provisioning (returns, raises, failed deletion); L session fixture | OK |
| AC-2.1 | S teardown deletes | OK |
| AC-2.2 | S teardown refuses | OK |
| AC-2.3 | S no creation, no deletion (workspace removed) | OK |
| AC-3.1 | S sweep property, boundaries; F sweep (`swept_at`) | OK |
| AC-3.2 | S sweep property, boundaries | OK |
| AC-4.1 | W refuses (incl. userinfo sentinel origin), W entry script | OK |
| AC-4.2 | W ephemeral origin; every F | OK |
| AC-4.3 | S marker argv; L ephemeral only; W entry script, W without marker | GAP (B1) |
| AC-5.1 | L forge beside verify (`on:` exact) | OK |
| AC-5.2 | L secret step; L nothing keeps a test from running (ini option set) | OK |
| AC-5.3 | S missing secret | OK |
| AC-5.4 | L report | OK |
| AC-6.1 | S credential lookup | OK |
| AC-6.2 | S bad credential | OK |
| AC-6.3 | S written only to the clone (files, argv, exclude, `caplog`, `repr`), S helper; L secret step | OK |
| AC-7.1 | L default collects none | OK |
| AC-7.2 | L forge path collects all | OK |
| AC-7.3 | L nothing keeps a test from running (`ast`, conftest, ini) | OK |
| AC-8.1 | L ephemeral only; every F | GAP (B1) |
| AC-8.2 | F subcommands, two round trips | OK |
| AC-8.3 | F repos_git, two tests | OK |
| AC-8.4 | F ci_security, four tests; docstring | OK |
| AC-8.5 | F collaboration, two tests | OK |
| AC-8.6 | L ephemeral only | OK |
| AC-9.1 | L setup note | OK |
| AC-9.2 | L map; B | OK |
| AC-9.3 | L debt line | OK |
| UB-1 | W, S, L in `verify` on doubles | OK |
| UB-2 | S sentinel, clone file holds the test token | OK |
| UB-3 | C, P, K, V unedited; W without marker | OK |
| UB-4 | I; the PR diff | OK |

33 OK, 2 GAP.

NOT-CLEAN (0 A, 1 B) — NOT-READY
