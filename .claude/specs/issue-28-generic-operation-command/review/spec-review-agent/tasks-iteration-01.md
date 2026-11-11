# Tasks review — issue #28, iteration 01 — spec-review-agent

### B1 — H and N's call half test `call.py` from a wave after it, so they are never red
Severity: B
Location: tasks.md § Wave 3 (3.1, 3.2 and the wave's note); preamble sentence "In a wave the TEST tasks run first and
add failing tests only, red on an assertion"
Defect: 3.1 (H: `json_member`, `body_of`) and 3.2's call half (`test_every_record_is_sent_as_its_section_documents`
and `test_an_unreachable_call_matches_its_reference_section`, which read `GATED_OPERATIONS` and run `cmd_call`) test
2.2's code but sit in a later, test-only wave with "one capture". They are written against finished code, which
contradicts the preamble.
Material-because: unmaintainable-by-rule `.claude/specs/_workflow/phases/spec-phase-tasks.md` ("Every TEST task
precedes the IMPL task it pairs with"). `spec-phase-implement.md` VERIFY stubs a wave's implementation and runs "the
wave's paired tests", which for wave 2 is K alone, so a vacuous H, or a vacuous N call half, passes every gate.
Proposed-edit: Wave 2 becomes four tasks:
- 2.1 TEST: K and the fixtures, unchanged.
- 2.2 TEST: the former 3.1, plus "it imports `github_api.commands.call` inside the test after asserting the file
  exists, as V's `_import_package_module` does, so a missing `call.py` is red on an assertion".
- 2.3 TEST: the former 3.2, plus the same import rule for `GATED_OPERATIONS`, and "it builds its project with
  `fx.enter_project` and loads the entry script with `fx.load_script`, as C does. It does not use `run_product_case`,
  which 2.1 writes in the same wave."
- 2.4 IMPL: the former 2.2, unchanged.

Wave 2's `Run:` gains `test/test_github_api_call_properties.py test/test_github_wrapper_contract.py`.

Wave 3 keeps only the former 3.3, renumbered 3.1. Its note becomes "This wave adds one test of #17's existing coverage
checks (D6), so it has no IMPL task and one capture". Its `Run:` becomes
`python scripts/run_tests.py test/test_github_wrapper_coverage.py`.

Coverage rows: AC-1.1 → 2.1, 2.3; AC-1.3 → 2.1, 2.2; AC-3.1 and AC-3.2 → 2.3; AC-5.3 → 3.1.

### C1 — F.2 and F.3 do not say which diff they read
Severity: C
Location: tasks.md § Final F.2, F.3
Defect: "the branch's diff against `origin/main`", read as a tree diff, also lists files that a sibling PR changed on
`origin/main` after this branch was cut. F.2 would then fail even though this change did not touch the file.
Proposed-edit: in F.2, replace "the branch's diff against `origin/main`" with "the branch's diff from its merge base
with `origin/main` (`git diff --name-only origin/main...HEAD`)". In F.3, replace "the diff" with "that diff".

### C2 — Residual: the hooks cannot parse the `F.n` ids the phase template prescribes
Severity: C
Location: tasks.md § Final (F.1–F.4)
Defect: `CHECKED_TASK_RE` in `.claude/hooks/hooklib.py` does not match `- [x] F.1 …` but does match `2.1` and `F1`
(checked against the regex). `gate_spec_stop.evidence_problems` therefore reports any ticked F task as "a checked task
line carries no parseable task id". #17 left its F tasks unticked.
Proposed-edit: none in this spec; it follows `spec-phase-tasks.md`'s `F.1` template. The conductor records the
template/regex mismatch as a findings-ledger row (`issue-filing-discipline.md`).

Verdict: NOT-READY (0 A, 1 B)
