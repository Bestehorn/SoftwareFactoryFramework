# Test-architect review — tasks, iteration 01

Scope: `tasks.md` against the frozen `requirements.md`, the approved `design.md` (§ Correctness Properties, § Acceptance
Criteria Mapping, D9) and DL-007.

## Checks

- **Every test the design names is in one TEST task.** R's two tests are in 1.1, T's one in 1.2, Q's five in 2.1 and
  `test_the_map_names_the_graphql_call` in 3.2. G's eight are in 2.2 and `test_the_usage_names_every_graphql_record`
  in 3.1. No task adds a test, helper, option or mechanism that the design lacks.
- **Red for the right reason (checked against the worktree's code).**
  - 1.1: `registry.py` has neither `upload_variables` nor `split_uploads`, so the test raises `AttributeError` inside
    its body.
  - 1.2: `Transport.graphql(self, *, document, variables=None)` takes no `files`, so the test raises `TypeError`
    inside its body. This includes its job-token case.
  - Wave 2: `graphql_only.OPERATIONS` is `()` and `PENDING_CAPABILITIES` holds all eight cells. So Q fails on its
    assertions, and every G call exits 2 on `registry.lookup`'s unknown-ID refusal. Two G tests see exit 2 and no
    request even at red: `test_a_refused_mutation_sends_nothing` and `test_a_file_for_a_variable_that_is_no_upload_is_refused`.
    They stay red on their log assertions ("no subcommand sends it"; `"projectPath" given with --file`), and the first
    also on its record check.
  - Wave 3: the entry script's docstring has no `call graphql#` line. The `gitlab_api/` bullet of the map holds none
    of `call graphql#`, `--file NAME=PATH` or `Upload`. So 3.1 and 3.2 fail on assertions.
  - No red is a collection error, because G and Q parametrize over constants only and import inside the test body.
- **Each IMPL task has a test that is red without it.** G's upload test fails without 2.5: `registry.call` would pass a
  `Path` into the JSON variables, which `json.dumps` refuses. G's refusal and upload tests fail without 2.4.
- **Each wave's tasks own disjoint files.**
  - Wave 1: R, T, `registry.py`, `transport.py`.
  - Wave 2: Q, G, `graphql_only.py`, `commands/call.py`, `registry.py`.
  - Wave 3: G, Q, `gitlab_wrapper.py`, `docs/forLLMConsumption.md`.
  - 2.4 reads 2.3's two constants by the names D6 fixes (DL-007). The wave's single green run comes after all three
    IMPL tasks.
- **Run lines.** Each wave's Run line holds every existing suite that imports a module the wave edits.
  - Waves 1 and 2: K, N, H, C and P.
  - Wave 2 adds V, the only other gitlab suite that reads `graphql_only`. K appends its synthetic records to
    `OPERATIONS`, and N iterates only REST records, so neither depends on `OPERATIONS` being empty.
  - Wave 3: C (its `test_the_usage_names_the_operation_call` reads the entry script's docstring), P (it scans
    docstrings for `os.environ`/`getenv`) and `test_llm_map_within_cap`.
- **Drift on `origin/main`.** Since the merge base `d30d022`, `origin/main` changes only K's `OP_PENDING_ONLY`
  constant and adds `test_gitlab_api_plan.py` and `test_gitlab_api_no_stage_assigned.py`. None of the three names
  `graphql_only`, `GATED_OPERATIONS` or `refuse_gated`, so no task or Run line is affected.
- **Final.** F.1 names the `verify` job of `.github/workflows/ci.yml`, matrix leg `tests` (present in the workflow's
  matrix). The real-instance run stays #11's, as the frozen "Out of scope" says. F.2 and F.3 check the diff from the
  merge base.
- **Cap.** `tasks.md` is under its 15,000-byte cap.

No finding.

## Coverage

| Criterion | Task(s) and test | Status |
|---|---|---|
| AC-1.1 | design inspection; 2.1 Q `test_every_record_matches_the_reference` | COVERED |
| AC-1.2 | 2.1 Q `test_every_capability_has_a_record`; V `test_every_graphql_only_capability_is_served_or_pending` on wave 2's line | COVERED |
| AC-1.3 | 2.1 Q `test_every_member_a_row_names_is_selected`; method case `async: false` | COVERED |
| AC-1.4 | 2.2 G `test_every_record_id_is_looked_up_once` | COVERED |
| AC-2.1 | 2.2 G `test_a_variable_holds_the_given_json_value`, `test_every_record_is_called_through_main`; H on waves 1-2 | COVERED |
| AC-2.2 | 2.2 G `test_a_work_item_list_prints_every_node`; G structural | COVERED |
| AC-2.3 | 2.2 G `test_every_record_is_called_through_main` | COVERED |
| AC-2.4 | 2.2 G `test_a_graphql_failure_exits_1_with_its_details` | COVERED |
| AC-2.5 | 2.2 G `test_every_record_is_called_through_main` (two pages per connection) | COVERED |
| AC-3.1 | 1.1 R (two tests); 1.2 T `test_graphql_sends_files_as_one_multipart_request`; 2.2 G `test_a_design_upload_sends_each_file_as_a_part` | COVERED |
| AC-3.2 | 2.2 G two-file case | COVERED |
| AC-4.1 | 2.2 G `test_a_refused_mutation_sends_nothing`; 2.1 Q ID-to-root-field check | COVERED |
| AC-4.2 | 2.2 same G test; K `test_a_gated_operation_names_its_subcommand` on waves 1-2 | COVERED |
| AC-4.3 | 2.2 same G test, failing when an ID names no record | COVERED |
| AC-5.1 | 3.1 G `test_the_usage_names_every_graphql_record` | COVERED |
| AC-5.2 | 3.2 Q `test_the_map_names_the_graphql_call`; F.4 `test_llm_map_within_cap` | COVERED |
| UB-1.1 | F.3; C on every Run line | COVERED |
| UB-1.2 | 2.2 G `test_a_file_for_a_variable_that_is_no_upload_is_refused`; F.3; K, N, R on waves 1-2 | COVERED |
| UB-2.1 | F.3; C on every Run line, K on waves 1-2 | COVERED |
| UB-2.2 | F.3; P `test_standard_library_only` on every Run line | COVERED |
| UB-3.1 | F.2 | COVERED |

21 COVERED, 0 GAP.

CLEAN

Verdict: READY
