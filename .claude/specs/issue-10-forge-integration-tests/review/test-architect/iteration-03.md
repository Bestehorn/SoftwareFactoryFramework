# Test architect — design review, iteration 03 (delta)

## Iteration-02 items

- B1 resolved: AC-4.3's L `test_the_forge_tests_reach_only_the_ephemeral_repository` now requires, by `ast` of the
  `.py` files of `test/forge/`, that only `ephemeral.py` names `product_wrapper` and that no file reads an attribute
  `main`, so the in-process `product_wrapper().main(argv=...)` route fails it; no D1/D9/D10 element reads `.main`
  (`write_credential.py`'s entry call is a bare name), so the oracle is satisfiable.
- C1 applied: AC-6.1's example adds the linked worktree holding its own file with a different token.
- C2 applied: L requires `refuse_distributed_run(worker_id=worker_id)` with the fixture's own parameter; consistent
  with D1 (xdist's `worker_id` fixture; `run_tests.py` `build_command` adds no `-n` for `--workers 1` and does not
  disable xdist, so the fixture resolves to `master`).
- D1 applied: AC-7.3 (and AC-4.3) scan the `.py` files of `test/forge/`.

The other delta edits (D2 `USERINFO_SEPARATOR`, D8's Windows sentence, the D10 row's parentheses, Rollback, the
Residuals line, the AC-6.2 mapping row's D9 step 2) change no criterion and no oracle; D9 step 2 is `read_test_token`,
which matches AC-6.2's "no wrapper or git invocation recorded".

## Findings

### C1 — "names" in the AC-4.3 `ast` check does not say an attribute counts
Severity: C
Location: design.md § Correctness Properties AC-4.3 (L `test_the_forge_tests_reach_only_the_ephemeral_repository`)
Defect: Read as `ast.Name` only, a forge module's `ephemeral.product_wrapper()._run_command(...)` or
`runpy.run_path(str(ephemeral.PRODUCT_WRAPPER))` reaches neither check (an attribute, and no `.main`), so the
in-process route B1 closed reopens through any wrapper function other than `main`.
Proposed-edit: replace "or names `product_wrapper`, `PRODUCT_WRAPPER` is named, outside its definition," with "or
names `product_wrapper` (as a name, an attribute or an imported alias, here and below), `PRODUCT_WRAPPER` is named,
outside its definition,".

## Coverage

Tests by the design's legend (W, S, L, F, B, C, P, K, V, I).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning, S distributed run; L session fixture (`worker_id=worker_id`) | COVERED |
| AC-1.2 | S run id | COVERED |
| AC-1.3 | F fixture, F repos_git; S provisioning (workflow seed, workspace removed) | COVERED |
| AC-1.4 | S provisioning (returns, raises, failed deletion); L session fixture | COVERED |
| AC-2.1 | S teardown deletes | COVERED |
| AC-2.2 | S teardown refuses | COVERED |
| AC-2.3 | S no creation, no deletion (workspace removed) | COVERED |
| AC-3.1 | S sweep property, boundaries; F sweep (`swept_at`) | COVERED |
| AC-3.2 | S sweep property, boundaries | COVERED |
| AC-4.1 | W refuses (incl. userinfo sentinel origin), W entry script | COVERED |
| AC-4.2 | W ephemeral origin; every F | COVERED |
| AC-4.3 | S marker argv; L ephemeral only (`subprocess`, `product_wrapper`, `PRODUCT_WRAPPER`, no `.main`); W entry script, W without marker | COVERED |
| AC-5.1 | L forge beside verify (`on:` exact) | COVERED |
| AC-5.2 | L secret step; L nothing keeps a test from running (ini option set) | COVERED |
| AC-5.3 | S missing secret | COVERED |
| AC-5.4 | L report | COVERED |
| AC-6.1 | S credential lookup (own file, main tree's, worktree's own, neither) | COVERED |
| AC-6.2 | S bad credential | COVERED |
| AC-6.3 | S written only to the clone (files, argv, exclude, `caplog`, `repr`), S helper; L secret step | COVERED |
| AC-7.1 | L default collects none | COVERED |
| AC-7.2 | L forge path collects all | COVERED |
| AC-7.3 | L nothing keeps a test from running (`ast` of `.py` files, conftest, ini) | COVERED |
| AC-8.1 | L ephemeral only; every F | COVERED |
| AC-8.2 | F subcommands, two round trips | COVERED |
| AC-8.3 | F repos_git, two tests | COVERED |
| AC-8.4 | F ci_security, four tests; docstring | COVERED |
| AC-8.5 | F collaboration, two tests | COVERED |
| AC-8.6 | L ephemeral only | COVERED |
| AC-9.1 | L setup note | COVERED |
| AC-9.2 | L map; B | COVERED |
| AC-9.3 | L debt line | COVERED |
| UB-1 | W, S, L in `verify` on doubles | COVERED |
| UB-2 | S sentinel, clone file holds the test token | COVERED |
| UB-3 | C, P, K, V unedited; W without marker | COVERED |
| UB-4 | I; the PR diff | COVERED |

35 COVERED, 0 GAP.

CLEAN — TEST-READY
