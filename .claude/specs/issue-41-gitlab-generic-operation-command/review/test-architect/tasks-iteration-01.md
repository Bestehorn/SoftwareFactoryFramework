# Test Architect — tasks review, iteration 01

Scope: `tasks.md` against `requirements.md` (frozen), `design.md` (approved, DL-003) § Correctness Properties,
§ Acceptance Criteria Mapping and D8, `spec-phase-tasks.md`, the RED/GREEN steps of `spec-phase-implement.md`, and
`.claude/hooks/red_for_right_reason.py`.

## The author's choices, judged

- **1.3, fx helpers in wave 1 with no test of their own: sound.** K and N both need D8's helpers (N needs
  `script_next` for D5's answers). Left in 2.1, they would make N depend on a file of its own wave. A helper defect
  shows up as a K or N failure, never as a vacuous pass:
  - An unserved request raises the fake's `AssertionError`. Neither `Transport._attempt` nor `main` catches it.
  - K judges a refusal by its log record, not by `run_main`'s code.
  - C, R and T load fx when they are imported, so a broken fx shows in wave 1's own capture.
- **3.2, `graphql_only.py` in wave 3 paired with V: sound.** No other task writes the file; K only monkeypatches
  `OPERATIONS`. P and K are on wave 3's Run line.
- **Wave 3's mutant: sound.** Every 3.1 test fails under it, each on its assertion:
  - The regenerated-index cases, the route-prefix test and the capability test each assert a named key, ID or
    capability. `[]` and `["mutant"]` name none.
  - `test_every_declared_key_is_in_its_family` and `test_every_graphql_only_capability_is_served_or_pending` assert
    an empty result. `["mutant"]` breaks that and `[]` would not, which is why those two functions return
    `["mutant"]`.
  - `test_the_only_in_graphql_table_is_read_whole` expects two named cells from `only_in_graphql`, which returns `[]`.
  - The existing `test_checker_names_each_unlisted_row` also fails under `coverage_gaps` returning `[]`, still on an
    assertion.
  - Undoing the mutant by its inverse edit keeps the uncommitted 3.1 tests, as in #28.
- **Wave 3's green run needs no family-module edit.** A disposable script (since deleted) computed D6's three
  `family_problems` arms with V's own `index_rows`, `key_families` and `operation_id`. It ran over the real
  `operations-index.md` (2,013 rows) and the records and `PENDING` keys of every module `discover_families()`
  yields (19 records, 1,973 pending keys), and it named nothing. So 3.2 owning only `graphql_only.py` is complete.
- **2.5: sound.**
  - Its five modules are exactly the ones that declare records: `operation_id=` occurs only in `ai_coding`,
    `create`, `plan`, `software_supply_chain_security` and `verify`.
  - It is dispatched after the red capture, which is when the set of named records is known.
  - C and V on wave 2's Run line hold UB-1.1 and the index keys for any correction.
  - An empty 2.5 is a valid outcome.
- **`test_call_takes_no_token_option` fails when the `call` subparser is missing: sound.** Without that check, the
  test passes before 2.4 on an empty option list.

## Red for the right reason

- **Wave 1.** R's tests fail inside the test body: an `AttributeError` on `registry.send`, `attribute_name` and
  `variables`, and a `TypeError` on `GraphQLOperation(capability=…)`. T's test fails on `Response.is_json`. No product
  or test file builds a `GraphQLOperation` today, so the new required `capability` field breaks no caller.
- **Wave 2.** Before 2.4, `call` is argparse's "invalid choice", exit 2:
  - Every K success case fails on its exit code.
  - Every K refusal fails because no log record exists. The `-F` NaN case fails because no `-F/--field` usage
    message exists.
  - H fails on its file assertion, under `Falsifying example`.
  - N `test_every_record_is_sent_as_its_section_documents` fails on its file assertion, and
    `test_an_unreachable_call_matches_its_reference_section` fails at D5 step 5.
  - N's three reader and rejection tests are green. They test helpers that live in N, against fixed oracles, which
    is accepted on #28's precedent (its tasks iteration 02).
  - No new module imports `commands/call.py` at module level, so the capture cannot hold `ERROR collecting`.
- **Wave 4.** C's new test fails on `call plan#retrieve-a-project-issue`. Each string it checks sits on one line of
  D7's text.

## Ownership, order, Run lines

- **Files.** Each wave's files are disjoint. TEST tasks come before IMPL tasks in every wave, and each wave reads only
  earlier waves. `mr.OP_MERGE_MR` and `issue.OP_CREATE_ISSUE` already exist, so 2.4 needs no edit to `mr.py` or
  `issue.py`.
- **Run lines.** Every Run line holds its paired suites, C, `test_wrapper_delivery.py` and P, so the "every wave"
  checks of F.2 and F.3 can be run. No Run line holds two test files with the same basename.
- **Final tasks.** F.1 names the `verify` job's `tests` leg (`ci.yml` matrix `group: [lint, types, security, tests]`).
  The `origin/main...HEAD` diff in F.2 and F.3 is taken from the merge base.

## Findings

### C1 — Wave 4's Run line leaves out the layout guard for the files it edits
Severity: C
Location: tasks.md § Wave 4, Run
Defect: 4.2 and 4.3 edit two tracked live files, the entry script and the map. `test/test_layout.py`
  (`test_every_framework_path_named_in_a_live_file_exists`, `test_relative_markdown_links_resolve`) reads both. By
  wave 4 the files from waves 1–3 are tracked too, so this run is the first one that can check every path the change
  names. #28's wave 4 ran it; as written, CI would be the first run of it.
Proposed-edit: append `test/test_layout.py` to wave 4's Run line.

### D1 — V's `registry_module` does not check that a file exists
Severity: D
Location: tasks.md § preamble ("as R's `gitlab_module` and V's `registry_module` do")
Defect: `registry_module` turns the import's `ModuleNotFoundError` into an `AssertionError`. It checks no file.
Proposed-edit: "as R's `gitlab_module` asserts the file and V's `registry_module` asserts the import".

## Coverage

| Criterion | Test / VERIFY task(s) | Status |
|---|---|---|
| AC-1.1 | 2.1 (K gated), 2.3 (N every record sent); design D1, D8 | COVERED |
| AC-1.2 | 1.1 (R `send`), 2.1 | COVERED |
| AC-1.3 | 1.1 (R `attribute_name`), 2.1, 2.2 (H property) | COVERED |
| AC-1.4 | 2.1 | COVERED |
| AC-1.5 | 1.2 (T `is_json`), 2.1 | COVERED |
| AC-1.6 | 2.1 | COVERED |
| AC-1.7 | 2.1 | COVERED |
| AC-1.8 | 2.1 | COVERED |
| AC-1.9 | 2.1 | COVERED |
| AC-2.1 | 2.1 | COVERED |
| AC-2.2 | 1.1 (R `variables`), 2.1 | COVERED |
| AC-2.3 | 2.1 | COVERED |
| AC-2.4 | 2.1 | COVERED |
| AC-3.1 | 2.3 (`is_unreachable` arms); design D5 | COVERED |
| AC-3.2 | 2.3 (unreachable call, six rejections, reader pin) | COVERED |
| AC-4.1 | 4.1 | COVERED |
| AC-4.2 | F.4; `test_llm_map_within_cap` on wave 4's Run line | COVERED |
| AC-5.1 | design D6, by inspection (DL-003) | COVERED |
| AC-5.2 | design D6, by inspection (DL-003) | COVERED |
| AC-5.3 | 3.1 (red against the mutant) | COVERED |
| AC-6.1 | 3.1; existing V `test_every_index_row_is_mapped_or_pending` | COVERED |
| AC-6.2 | 3.1 | COVERED |
| AC-6.3 | 3.1, green with 3.2 | COVERED |
| UB-1.1 | F.3; C on every Run line | COVERED |
| UB-2.1 | 2.1 (K token option), F.3 | COVERED |
| UB-2.2 | F.3; P on every Run line | COVERED |
| UB-3.1 | F.2; `test_wrapper_delivery.py` on every Run line | COVERED |

Verdict: CLEAN (0 A, 0 B) — TEST-READY (27 COVERED, 0 GAP)
