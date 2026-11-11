# Test Architect — design review, iteration 03 (delta)

## Fix sites

- Iteration-02 B1 (Z1), AC-1.3: APPLIED. With `--path issue_iid=5`, step 4 passes. So a `json_member` without
  `parse_constant` yields the float `nan`, `_is_scalar` takes it (`registry.py` `KIND_ACCEPTS`: `str, int, float`), and
  the `PUT` is recorded: "no request" fails. A `json_member` that lets the `ValueError` reach argparse gets `invalid …
  value: 'title=NaN'`, which holds `NaN` and not `"title"`: the standard-error oracle fails. `title` is a BODY `Param`
  of `plan#update-an-issue` (`families/plan.py`), and argparse names the action `-F/--field` by its option strings, so a
  correct build passes.
- C1: APPLIED. `rest/create.md` "Add changelog data to file" has the body rows `version[^version-attribute-include]` and
  `from[^unspecified-automatically-finds]`.
- C2: APPLIED. Both headings occur once in `rest/openapi-only.md` (`GET /geo/proxy`,
  `PUT /hooks/:hook_id/custom_headers/:key`).
- C3: APPLIED ("then any details (the two path errors carry none)").
- The new pins hold against the reference. "Set commit pipeline status" has the rows `name or context`, `name` and
  `context`. Z3's `create#health` is `GET /projects/:id/repository/health`, with `generate` as its only row, a query row.

### B1 — Z2's member rule has no test, and the method passes an unreachable call that breaks it
Severity: B
Location: design.md § D5 `record_problems`, `test_the_method_rejects_a_call_that_differs`
Defect: `record_problems` matches a `Param` to a row by name. Member rows have to stay matchable, because part 1
  declares `not[labels]` (`families/plan.py`) against the `not[labels]` row (`rest/plan.md`), and D5 states one member
  rule for `[` and `:`. So no arm reports a `Param` that D5 says is never declared: a `[].key` or `:key` member, or a
  bracketed name outside the query and a FORM body. No named case fails when that rule is left out.
Material-because: AC-3.2 — `software-supply-chain-security#create-an-application` (`POST /applications`, page
  Offering "GitLab Self-Managed, GitLab Dedicated", so unreachable) has the rows `granular_scopes` and
  `granular_scopes[].access`. A record that declares `granular_scopes[].access` as a BODY `Param` passes
  `record_problems`. Its call sends the top-level JSON member `granular_scopes[].access`, which `call_problems` finds
  documented in the body. So a call that differs from its section in an attribute's name passes the method that D5
  calls the whole proof of an unreachable operation.
Proposed-edit: in `record_problems`, replace "a `Param` that matches no row by name, or whose location differs from its
  row's `In`;" with "a `Param` that matches no row by name, or whose location differs from its row's `In`, or whose
  name holds `[` or `:` and is not a `parent[key]` name of a `Location.QUERY` `Param` or of a `BodyFormat.FORM`
  record's `Param` (part 1's `not[labels]`);". In `test_the_method_rejects_a_call_that_differs`, replace "is
  parametrized on that section, with five cases:" with "is parametrized, with five cases on that section and one on
  another:", and add the case "a record built as `software-supply-chain-security#create-an-application` that declares
  `granular_scopes[].access` as a BODY `Param`, which `record_problems` checks."

Every part-1 bracketed `Param` is a `parent[key]` QUERY name (`families/plan.py` `not[...]`), so the restated arm
reports none of them.

### C1 — Z3's "a placeholder with no such row is no difference" has no named case
Severity: C
Location: design.md § D5 `test_a_section_is_read_as_the_reference_writes_it`
Defect: No case the design names gives `record_problems` a record whose table omits a placeholder row. Suppose a
  `record_problems` still reports the omitted placeholder. The first slice that declares `create#health` then has to
  edit N, which D8 lists as "never".
Proposed-edit: add the pin "a record built as `create#health` (`GET /projects/:id/repository/health`, `generate` a
  QUERY `Param`) gets no problem from `record_problems`, though its table has no `id` row."

## Coverage

Design phase: the column names the design's tests (the mapping's legend).

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` | COVERED |
| AC-1.2 | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` | COVERED |
| AC-1.3 | H `test_any_json_value_becomes_the_attribute_value`; K `test_an_attribute_carries_its_kind`, `test_a_field_that_is_not_json_is_refused`; R `test_attribute_name_drops_one_trailing_bracket_pair` | COVERED |
| AC-1.4 | K `test_a_list_prints_every_page_as_one_array` | COVERED |
| AC-1.5 | K `test_a_json_or_empty_body_prints_as_documented`; T `test_is_json_reads_the_content_type` | COVERED |
| AC-1.6 | K `test_a_body_that_is_not_json_is_written_unchanged` | COVERED |
| AC-1.7 | K `test_an_api_error_exits_1_with_its_details` | COVERED |
| AC-1.8 | K `test_a_project_path_takes_the_configured_project` | COVERED |
| AC-1.9 | K `test_a_graphql_record_sends_its_document` | COVERED |
| AC-2.1 | K `test_an_unknown_operation_is_refused` | COVERED |
| AC-2.2 | K `test_an_undocumented_parameter_is_refused`; R `test_variables_are_the_documents_definitions` | COVERED |
| AC-2.3 | K `test_a_missing_path_parameter_is_refused` | COVERED |
| AC-2.4 | K `test_a_value_of_the_wrong_shape_is_refused` | COVERED |
| AC-3.1 | design review; N `test_the_unreachable_rule_has_two_arms` | COVERED |
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` | COVERED (B1, C1) |
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
