# spec-review-agent — tasks.md, iteration 01

### C1 — Three of N's tests pass in wave 2's red run, against the preamble's "failing tests only"
Severity: C
Location: tasks.md § preamble ("add failing tests only"); § Wave 2, task 2.3
Defect: `test_the_unreachable_rule_has_two_arms`, `test_a_section_is_read_as_the_reference_writes_it` and
`test_the_method_rejects_a_call_that_differs` exercise only N's own `is_unreachable`, `reference_sections`,
`record_problems` and `call_problems` against the committed reference and wave 1's `registry.attribute_name`, so they
pass before 2.4 and 2.5 exist. The preamble says every TEST task adds failing tests only, and
`spec-phase-implement.md` RED re-dispatches a task whose tests are green. Wave 3 handles the same case for V with a
named mutant, and #13's `tasks.md` 3.2 names its "green before 3.12 by design" test together with its mutant. Wave 2
names neither.
Material-because: this does not gate. The capture as a whole passes `red_for_right_reason.judge`, because K and H
fail on assertions. The risk is a re-dispatch of 2.3 that cannot turn these tests red, and the verifier's wave-2
mutant (2.4 and 2.5 reverted) leaving them green with nothing in the tasks to say why.
Proposed-edit: at the end of 2.3's description, before "— Files:", add: "`test_the_unreachable_rule_has_two_arms`,
`test_a_section_is_read_as_the_reference_writes_it` and `test_the_method_rejects_a_call_that_differs` are green before
2.4 by design (they exercise N alone); their mutant is N with `is_unreachable` returning `False`, `record_problems`
`["mutant"]` and `call_problems` `[]`." In the preamble, replace "add failing tests only" with "add failing tests
only, but for a test its task names green by design". Do not mutate N for the red capture itself: 2.5 reads the record
names from the unmutated red run of `test_every_record_matches_its_reference_section`. To stay under the cap, offset
the bytes by deleting the `## Coverage` rows that only restate a `Validates:` line (AC-1.2/1.3/2.2, AC-1.5, the
AC-1.4… row, AC-3.2, AC-4.1, AC-5.3…). Keep the AC-1.1, AC-3.1, AC-4.2, AC-5.1/5.2 and UB rows.

### D1 — 2.5 validates AC-1.1, not AC-3.2
Severity: D
Location: tasks.md § Wave 2, task 2.5 `Validates:`
Defect: 2.5 corrects part-1 records so that N `test_every_record_matches_its_reference_section` passes, and through it
`test_every_record_is_sent_as_its_section_documents`. design.md § Acceptance Criteria Mapping gives AC-3.2 the
unreachable-call, rejection and reader tests, and § Correctness Properties AC-1.1 gives the sent-as-documented test to
AC-1.1.
Proposed-edit: "Validates: AC-3.2, UB-1.1" → "Validates: AC-1.1, UB-1.1".

### D2 — V's `registry_module` does not assert that a file exists
Severity: D
Location: tasks.md § preamble ("as R's `gitlab_module` and V's `registry_module` do")
Defect: `test/test_gitlab_wrapper_coverage.py` `registry_module` imports the registry and turns its
`ModuleNotFoundError` into an `AssertionError`. Only R's `gitlab_module` asserts `source.is_file()` first.
Proposed-edit: "as R's `gitlab_module` and V's `registry_module` do" → "as R's `gitlab_module` does".

Verdict: READY
