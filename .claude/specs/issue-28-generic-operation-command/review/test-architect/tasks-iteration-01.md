# Test Architect — tasks review, iteration 01

Scope: `tasks.md` against `requirements.md` (frozen), `design.md` (approved, DL-005) § Correctness Properties,
§ Acceptance Criteria Mapping and D8, and the RED/GREEN steps of `spec-phase-implement.md`.

Sound, with no finding:
- The test names and modules of tasks 1.1–4.1 are the ones in D8 and the Mapping.
- Each wave's tasks own disjoint files, and wave 3 depends only on waves 1–2.
- Waves 1, 2 and 4 go red before their IMPL:
  - R reaches the registry as `api.registry.<name>`, as its existing tests do, so a missing `send` fails inside the
    test, not at collection.
  - K runs the product's `main`. An unregistered `call` is argparse's exit 2, and every success row fails
    `assert_outcome`.
  - C's docstring test fails on its strings.
- UB-1.1 is protected: P compares the fixed `PARSER_SPELLINGS`, so the new `call` subparser cannot break it.
- C's credential scan and V's import scan `rglob` the package, so they reach `commands/call.py` with no edit.
- Every file named on a Run line exists.
- F.1 names the `verify` job's `tests` leg (`ci.yml` matrix `group: [lint, types, security, tests]`).

## Findings

### B1 — Wave 3 has no red run: both the RED step and the verifier's red audit refuse it
Severity: B
Location: tasks.md § Wave 3 (its preamble; tasks 3.1, 3.2, 3.3)
Defect: Every test in this wave judges code that already exists when the wave starts, so `evidence/red/wave-3.txt`
comes out green:
- H judges the `call.py` of wave 2.
- N's call half judges `call.py` and `registry.py` from waves 1–2.
- V judges its own `coverage_gaps` and `_family_problems`, which date from #17.

When the RED step of `spec-phase-implement.md` gets a green capture, it re-dispatches the tasks. No re-dispatch can make
these tests red without weakening them. `adversarial-verifier` step 4 then refutes a red capture that did not fail.
Material-because: this breaks the rule `spec-phase-tasks.md` ("Test-first inside each wave"). AC-1.3's property, the
AC-3.1/AC-3.2 method and the AC-5.3 cases would ship with no run that shows they can fail.
Proposed-edit: replace "so it has no IMPL task and one capture." with: "so it has no IMPL task. Its red capture
(`# tasks: 3.1 3.2 3.3`) runs this Run line with three named mutants applied, as `adversarial-verifier` step 2's
targeted mutation does, and must pass `red_for_right_reason.py`:
- M1: `call.json_member` returns the text after the first `=` unparsed. H then finds a falsifying example, and N
  `test_an_unreachable_call_matches_its_reference_section` sends `"100"` for `budget_amount`.
- M2: `cmd_call` passes `query=None` to `registry.send` and `registry.pages`. N
  `test_every_record_is_sent_as_its_section_documents` then names `exclude_pull_requests`.
- M3: V's `coverage_gaps` and `_family_problems` return `[]`. Every case of 3.3 then fails.

Revert each mutant by its exact inverse edit. Never use `git checkout` or `git stash`: either would also throw away the
3.3 test that is not yet committed in V. The green capture is the same Run line on the reverted tree."

Why this is the smallest fix:
- Moving H and N into wave 2 needs more edits. Both import `github_api.commands.call`, which 2.2 creates.
- If that import sits at module level, wave 2's capture shows `ERROR collecting`, and `red_for_right_reason.py` refuses
  the whole wave, K included. The move works only if the import happens inside the test, the way V's
  `_import_package_module` does it.
- V would still need M3, because nothing in this change implements what V pins.

### C1 — K's refusal rows turn red only through the log check, and `run_product_case` does not run it
Severity: C
Location: tasks.md § Wave 2, task 2.1 ("refusals judged by `assert_outcome` … and `caplog`")
Defect: Before 2.2, argparse refuses the unregistered `call` with exit 2, no request and empty stdout. So
`assert_outcome` passes every refusal row of these four tests:
- `test_a_gated_operation_names_its_subcommand`
- `test_an_unknown_operation_is_refused`
- `test_an_undocumented_parameter_is_refused`
- `test_a_missing_path_parameter_is_refused`

D8's `run_product_case` calls only `assert_outcome` and `assert_every_request_routed`. A row that leaves its log check
to that helper is green in the red run. It also passes a `cmd_call` that returns 2 without logging anything.
Proposed-edit: "refusals judged by `assert_outcome` (no request for exit 2) and by `fx.assert_log` on
`caplog.records`, each refusal row carrying the `LogExpectation` that design § Correctness Properties names for it
(`run_product_case` does not call `assert_log`)".

### C2 — "Red on an assertion" does not describe how wave 1 fails
Severity: C
Location: tasks.md § preamble ("red on an assertion")
Defect: Before 1.3, wave 1's tests fail like this:
- R's new tests fail with `AttributeError` (`api.registry.send`, `api.registry.path_parameters`).
- The bracket test on `pages` fails with `_check_names`' `ValueError`.
- T's test fails with `TypeError` (`Transport.pages(accept=...)`).

`red_for_right_reason.py` accepts these failures through its `FAILED .*::` arm, since there is no collection error. A
conductor reading "red on an assertion" would still treat them as the wrong red.
Proposed-edit: "red on an assertion, or inside the test on the function or keyword not yet written (`AttributeError`,
`TypeError`, a refusal's `ValueError`), never at collection".

### C3 — Wave 1's Run line leaves out the standard-library guard for the files it edits
Severity: C
Location: tasks.md § Wave 1, Run
Defect: Task 1.3 edits `registry.py` and `transport.py`. Their UB-2.2 check, V
`test_the_wrapper_imports_only_the_standard_library`, first runs in wave 2, after wave 1 is committed.
Proposed-edit: append `test/test_github_wrapper_coverage.py` to wave 1's Run line.

## Coverage

| Criterion | Test / VERIFY task(s) | Status |
|---|---|---|
| AC-1.1 | 2.1 (K gated), 3.2 (N every record); design D1, D8 | COVERED (B1 for 3.2) |
| AC-1.2 | 1.1, 1.2, 2.1 | COVERED |
| AC-1.3 | 2.1 (K example), 3.1 (H property) | COVERED (B1 for 3.1) |
| AC-1.4 | 2.1 | COVERED |
| AC-1.5 | 2.1 | COVERED |
| AC-1.6 | 2.1 | COVERED |
| AC-1.7 | 2.1 | COVERED |
| AC-2.1 | 2.1 | COVERED (C1) |
| AC-2.2 | 2.1 | COVERED (C1) |
| AC-2.3 | 1.1, 2.1 | COVERED (C1) |
| AC-3.1 | 3.2; design D5 | COVERED (B1) |
| AC-3.2 | 3.2 | COVERED (B1) |
| AC-4.1 | 4.1 | COVERED |
| AC-4.2 | F.4 (inspection, as design sets it); `test_llm_map_within_cap` on wave 4's Run line | COVERED |
| AC-5.1 | design D6, by inspection (DL-005) | COVERED |
| AC-5.2 | design D6, by inspection (DL-005) | COVERED |
| AC-5.3 | 3.3 | COVERED (B1) |
| UB-1.1 | F.3; C and P on the Run lines of waves 1, 2, 4 | COVERED |
| UB-2.1 | F.3; C on the Run lines of waves 1, 2, 4 | COVERED |
| UB-2.2 | F.3; V on the Run lines of waves 2, 4 | COVERED (C3) |
| UB-3.1 | F.2; `test_wrapper_delivery.py` on the Run lines of waves 2, 4 | COVERED |

Verdict: NOT-CLEAN (0 A, 1 B) — NOT-TEST-READY (21 COVERED, 0 GAP)
