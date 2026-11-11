# Test Architect — design review, iteration 02 (delta)

## Fix sites

- Iteration-01 B1 (Y4), AC-1.7: APPLIED. Both path cases tell the two outcomes apart. `GitLabAPIError` derives from
  `RuntimeError` (`errors.py`), so D4's `ValueError` catch lets it through to `main`. `registry.pages` runs `expand`
  before it returns the generator (`registry.py` `pages`), so `--path id=..` on `plan#list-all-project-labels` (OFFSET)
  raises inside step 5. `_segment`'s message names `:id` / `:issue_iid`. A handler that catches `GitLabAPIError` around
  steps 1 to 5 exits 2 on the labels case and fails it.
- Iteration-01 B2 (Y5), AC-5.3: APPLIED. The fifth case matches D6's `family_problems` arm "a record whose operation ID
  is the Reference of no row".
- C1 to C5: APPLIED. D7's docstring keeps "an empty body as" on one line. The C5 `header` half is carried by Y1's
  restated `In` rule.
- Y1 pins: APPLIED, and both hold against the reference. In `rest/create.md` "Create a commit", the parent row is
  `` `actions[]` ``, which `attribute_name` reads as `actions`, so `actions[].action` is its member. A reader that
  matched raw text would fail the pin. In `rest/ai-coding.md` "Update approval configuration for a project", the
  backticked text is `approvals_before_merge (deprecated)`. The `header` rows (NuGet, `rest/openapi-only.md`) are read by
  the pin "every row of `operations-index.md` names … a section", so a reader that refuses an unknown `In` fails it.
- Y2, `-F` refuses `NaN`/`Infinity`: APPLIED WITH DEFECT (B1 below).

### B1 — The NaN example passes without `parse_constant`
Severity: B
Location: design.md § Correctness Properties AC-1.3, K `test_a_field_that_is_not_json_is_refused`
Defect: The three cases call `plan#update-an-issue` (`/projects/:id/issues/:issue_iid`) without `--path issue_iid`, and
  the oracle is only "exit 2 with no request". So with plain `json.loads` the call still exits 2 with no request: D4's
  step-4 check refuses the missing `issue_iid`, and the case passes.
Material-because: wrong-behaviour — without `parse_constant`, `_is_scalar` accepts the float `nan` (`registry.py`
  `KIND_ACCEPTS`) and `transport.py` `json.dumps(obj=json_body)` (default `allow_nan=True`) sends `{"title": NaN}`, which
  is not JSON. That is Y2's defect, and the test stays green.
Proposed-edit: replace the example with "Example, K `test_a_field_that_is_not_json_is_refused`:
  `call plan#update-an-issue --path issue_iid=5 -F title=NaN`, and the same with `title=Infinity` and
  `title=-Infinity`, each exit 2 with no request. Standard error holds argparse's usage message naming `-F/--field` and
  `"title"` (D2)."

### C1 — The footnote form of D5's name rule has no pin
Severity: C
Location: design.md § D5 `test_a_section_is_read_as_the_reference_writes_it`
Defect: The pins exercise ` (` (`approvals_before_merge`) but not `[^`. The only footnoted names in the reference are
  `` `version[^version-attribute-include]` `` and `` `from[^unspecified-automatically-finds]` `` (`rest/create.md`
  "Add changelog data to file"). No part-1 record reads that section, so a reader that drops the `[^` clause passes N on
  this tree, and the slice that adds the record has to edit N, which D8 lists as "never".
Proposed-edit: add the pin "`create#add-changelog-data-to-file` has the body attributes `version` and `from`
  (footnoted `[^…]`)."

### C2 — The path arm's `/geo/` and `/hooks/` have no case
Severity: C
Location: design.md § Correctness Properties AC-3.1
Defect: SR-C3 added `/geo/` and `/hooks/` to the path arm, but `test_the_unreachable_rule_has_two_arms` checks `/admin/`
  only, so an `is_unreachable` that tests `/admin/` alone passes it. `rest/openapi-only.md` has no page or section
  Availability line, so for these keys only the path arm decides.
Proposed-edit: add to the true cases "`openapi-only#determine-if-a-geo-site-should-proxy-requests` (`GET /geo/proxy`)
  and `openapi-only#update-a-custom-header` (`PUT /hooks/:hook_id/custom_headers/:key`), the path arm only".

### C3 — AC-1.7's "then the details" does not hold for the two path cases
Severity: C
Location: design.md § Correctness Properties AC-1.7
Defect: `_segment` raises `GitLabAPIError` without `details`, and `_report` logs `details` only when it is set
  (`gitlab_wrapper.py` `_report`). So a test that expects a details record on every case fails against a correct
  handler.
Proposed-edit: "the log records hold the message and then the details" → "the log records hold the message and then the
  details, where the error carries any (the two path errors carry none)".

## Coverage

Design phase: the column names the design's tests (the mapping's legend).

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` | COVERED |
| AC-1.2 | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` | COVERED |
| AC-1.3 | H `test_any_json_value_becomes_the_attribute_value`; K `test_an_attribute_carries_its_kind`, `test_a_field_that_is_not_json_is_refused`; R `test_attribute_name_drops_one_trailing_bracket_pair` | COVERED (B1 on the D2 example) |
| AC-1.4 | K `test_a_list_prints_every_page_as_one_array` | COVERED |
| AC-1.5 | K `test_a_json_or_empty_body_prints_as_documented`; T `test_is_json_reads_the_content_type` | COVERED |
| AC-1.6 | K `test_a_body_that_is_not_json_is_written_unchanged` | COVERED |
| AC-1.7 | K `test_an_api_error_exits_1_with_its_details` | COVERED (C3) |
| AC-1.8 | K `test_a_project_path_takes_the_configured_project` | COVERED |
| AC-1.9 | K `test_a_graphql_record_sends_its_document` | COVERED |
| AC-2.1 | K `test_an_unknown_operation_is_refused` | COVERED |
| AC-2.2 | K `test_an_undocumented_parameter_is_refused`; R `test_variables_are_the_documents_definitions` | COVERED |
| AC-2.3 | K `test_a_missing_path_parameter_is_refused` | COVERED |
| AC-2.4 | K `test_a_value_of_the_wrong_shape_is_refused` | COVERED |
| AC-3.1 | design review; N `test_the_unreachable_rule_has_two_arms` | COVERED (C2) |
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` | COVERED (C1) |
| AC-4.1 | C `test_the_usage_names_the_operation_call` | COVERED |
| AC-4.2 | design review; `test_llm_map_within_cap` | COVERED |
| AC-5.1 | design review (D6, the banner's pin) | COVERED |
| AC-5.2 | design review (D6 table, "Which change fixes it") | COVERED |
| AC-5.3 | V `test_a_regenerated_index_names_each_changed_key` (five cases), `test_every_declared_key_is_in_its_family` | COVERED |
| AC-6.1 | V `test_a_route_prefix_key_is_held_to_the_rule`, `test_every_index_row_is_mapped_or_pending` | COVERED |
| AC-6.2 | V `test_a_capability_neither_served_nor_pending_is_named`, `test_the_only_in_graphql_table_is_read_whole` | COVERED |
| AC-6.3 | V `test_every_graphql_only_capability_is_served_or_pending`, `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | COVERED |
| UB-1.1 | C, every existing case unedited; `test_script_usage_error_exits_2`; PR diff | COVERED |
| UB-2.1 | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` | COVERED |
| UB-2.2 | P `test_standard_library_only` | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |

Verdict: NOT-CLEAN (0 A, 1 B) — NOT-TEST-READY (27 COVERED, 0 GAP)
