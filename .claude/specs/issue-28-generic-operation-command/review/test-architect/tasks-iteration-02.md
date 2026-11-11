# Test Architect — tasks review, iteration 02 (delta)

Scope: the fix sites of iteration 01's B1, C1, C2 and C3, the spec-review lane's B1 as merged, and any test-ordering
or coverage defect that the revision introduces.

## Fix sites

- **B1 is resolved.** Every TEST task of wave 2 now has at least one test that fails before 2.4:
  - 2.1 (K): no `call` subparser exists yet, so argparse exits 2. Every success row fails `assert_outcome`, and every
    refusal row fails `fx.assert_log`, because `caplog.records` holds no record of the refusal.
  - 2.2 (H): the test asserts that `commands/call.py` exists before it imports it, as V's `_import_package_module`
    does. The capture shows an `AssertionError` under `Falsifying example`.
  - 2.3 (N): `test_every_record_is_sent_as_its_section_documents` fails on the same file assertion before it reads
    `GATED_OPERATIONS`. `test_an_unreachable_call_matches_its_reference_section` fails at D5 step 5 (exit 0 expected):
    argparse exits 2, either as an assertion or as a `FAILED …::… - SystemExit: 2` line. pytest catches
    `SystemExit` inside a test and reports it as a failure.
  - No new module imports `commands.call` at module level, so the capture cannot hold `ERROR collecting`.
    `red_for_right_reason.py` accepts it through its `AssertionError`, `Falsifying example` and `FAILED .*::` arms.
- **The three N tests that are green in wave 2's red run are acceptable.**
  - `test_a_section_is_read_as_the_reference_writes_it` and `test_the_method_rejects_a_call_that_differs` test helpers
    that live in N itself. No IMPL task pairs with them. Their oracles are fixed: D5's name sets, and a problem that
    names the method, the path or the parameter. A constant helper therefore fails them.
  - `test_every_record_matches_its_reference_section` applies those helpers to #17's existing records. Two things keep
    it from passing vacuously: the rejection test's fifth case (a record lacking `expires_at`) and the rule that a
    record with no section is a problem.
  - The RED step and the verifier's red audit judge a wave capture (`spec-phase-implement.md` RED step;
    `adversarial-verifier` step 4). Task 2.3 is still red as a task, because two of its five tests fail.
  - #17 set the precedent. Its wave-3 red capture had `4 failed, 19 passed`, two of them D7 helper tests. The verifier
    accepted it and killed those tests with test-side mutants ("Tests green before their wave's code: D7 helpers
    (killed above, test-side)": `issue-17-github-wrapper-foundation/evidence/verify/refutation-report.md` § 3).
  - Step 2 of `adversarial-verifier` therefore covers these three tests with no text added to `tasks.md`.
- **Wave 3's red capture is sound.**
  - M3 edits `coverage_gaps` and `_family_problems`, which live in V (`test/test_github_wrapper_coverage.py`). With
    both returning `[]`, every case of 3.1 asserts a named ID and fails.
  - The existing tests `test_every_operation_is_covered_or_pending` and
    `test_one_module_per_family_holding_only_its_own_ids` assert emptiness, so they stay green under M3.
    `test_a_gap_is_named` also fails, which is still the right reason.
  - The task tells the conductor to undo M3 by its exact inverse edit. That protects the uncommitted 3.1 test in the
    same file.
- **C1 is applied.** Refusal rows carry their `LogExpectation`, and K calls `fx.assert_log` itself.
- **C2 is applied.** The preamble accepts "an exception raised inside the test body, never a collection error".
- **C3 is applied.** Wave 1's Run line includes V.
- **Ownership and order.**
  - Wave 2's files are disjoint: 2.1 owns the fixtures and K, 2.2 owns H, 2.3 owns N, and 2.4 owns `_common.py` and
    `call.py`.
  - 2.1–2.3 come before 2.4.
  - N reads `fx` (`enter_project`, `load_script`) but writes none of it, and it does not use 2.1's `run_product_case`.
  - 2.4 needs no edit to the entry script: `_build_parser` discovers `commands/*` through `pkgutil`.
- **The Run lines and the coverage table match the moved tasks.** Wave 2's Run line names H and N, and the table maps
  AC-1.1 and AC-3.x to 2.3, AC-1.3 to 2.2 and AC-5.3 to 3.1.

## Findings

None.

## Coverage

| Criterion | Test / VERIFY task(s) | Status |
|---|---|---|
| AC-1.1 | 2.1 (K gated), 2.3 (N every record sent); design D1, D8 | COVERED |
| AC-1.2 | 1.1, 1.2, 2.1 | COVERED |
| AC-1.3 | 2.1 (K example), 2.2 (H property) | COVERED |
| AC-1.4 | 2.1 | COVERED |
| AC-1.5 | 2.1 | COVERED |
| AC-1.6 | 2.1 | COVERED |
| AC-1.7 | 2.1 | COVERED |
| AC-2.1 | 2.1 | COVERED |
| AC-2.2 | 2.1 | COVERED |
| AC-2.3 | 1.1, 2.1 | COVERED |
| AC-3.1 | 2.3 (`is_unreachable` examples); design D5 | COVERED |
| AC-3.2 | 2.3 (unreachable call, rejection cases, reader pin) | COVERED |
| AC-4.1 | 4.1 | COVERED |
| AC-4.2 | F.4; `test_llm_map_within_cap` on wave 4's Run line | COVERED |
| AC-5.1 | design D6, by inspection (DL-005) | COVERED |
| AC-5.2 | design D6, by inspection (DL-005) | COVERED |
| AC-5.3 | 3.1 (red against M3) | COVERED |
| UB-1.1 | F.3; C and P on the Run lines of waves 1, 2 and 4 | COVERED |
| UB-2.1 | F.3; C on the Run lines of waves 1, 2 and 4 | COVERED |
| UB-2.2 | F.3; V on the Run lines of waves 1, 2, 3 and 4 | COVERED |
| UB-3.1 | F.2; `test_wrapper_delivery.py` on the Run lines of waves 2 and 4 | COVERED |

Verdict: CLEAN (0 A, 0 B) — TEST-READY (21 COVERED, 0 GAP)
