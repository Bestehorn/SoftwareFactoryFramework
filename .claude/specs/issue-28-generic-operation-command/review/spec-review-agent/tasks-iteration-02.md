# Tasks review — issue #28, iteration 02 (delta) — spec-review-agent

Fix sites, each APPLIED with no new A or B:
- Iteration-01 B1: wave 2 holds 2.1 K and the fixtures, 2.2 H, 2.3 N and 2.4 IMPL. 2.2 and 2.3 import inside the
  test after asserting that the file exists. V `_import_package_module` and the `scripts_on_path` fixture are the
  precedent, and `commands/__init__.py` already exists, so a missing `call.py` fails on an assertion and not at
  collection. 2.3 uses `fx.enter_project` and `fx.load_script`, both in the fixtures module, loaded by path as C
  `_load_fixtures` does, and not 2.1's `run_product_case`. Wave 2's Run line names H and N. Wave 3 holds only 3.1.
- Iteration-01 C1: F.2 reads `git diff --name-only origin/main...HEAD`. F.3 reads the same three-dot diff without
  `--name-only`, which it needs to judge existing lines.
- Test-architect M3: `coverage_gaps` and `_family_problems` are defined in V. When both return `[]`, every 3.1 case
  fails on its assertion: the added ID, the pending ID, the missing record ID, the other path and the other method.
  The existing `test_a_gap_is_named` also fails. That is still a red for the right reason. The exact-inverse revert
  keeps the uncommitted 3.1 test, and F.3's diff check catches a revert that is not exact.
- Test-architect C1: 2.1 now judges refusals with `fx.assert_log` on `caplog.records` through each row's
  `GoldenCase.log`, and `LogExpectation` exists. Before 2.4, argparse's refusal writes only to stderr, so every
  refusal row fails on the log assertion.
- Test-architect C2: the preamble wording now admits wave 1's `AttributeError` and `TypeError` failures inside the
  test. `red_for_right_reason.py` accepts them through `FAILED .*::`.
- Test-architect C3: wave 1's Run line names V.
- Traceability: the `Validates:` lines of 2.1, 2.2, 2.3 and 3.1 match the Coverage rows for AC-1.1, AC-1.3, AC-3.1,
  AC-3.2 and AC-5.3.
- File ownership: the Files lists of 2.1, 2.2, 2.3 and 2.4 share no file. No test task depends on another task in its
  own wave.
- Run lines: every path on a Run line exists or is created by a TEST task of that wave. `tasks.md` is under its
  15,000-byte cap.

### D1 — "M3" names a mutant from another lane's numbering
Severity: D
Location: tasks.md § Wave 3 (the note)
Defect: `tasks.md` has no M1 or M2. The label comes from the test lane's iteration-01 file, which this artefact does
not reference.
Proposed-edit: replace "with mutant M3 applied — " with "with one mutant applied — ", and "and M3 is undone" with
"and the mutant is undone".

Verdict: READY
