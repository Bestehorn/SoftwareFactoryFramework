# Test Architect — design review, iteration 04 (delta)

## Fix sites

- Iteration-03 B1 (member rule), AC-3.2: APPLIED. `record_problems` now reports a `Param` whose name holds `[` or `:`
  unless it is a `parent[key]` name of a `Location.QUERY` `Param` or of a `BodyFormat.FORM` record. The new case can
  fail:
  - `software-supply-chain-security#create-an-application` is the first of the page's two "Create an application"
    headings (`POST /applications`; the second, `POST /user/applications`, is `…-1`). Its table has the body rows
    `granular_scopes` and `granular_scopes[].access`.
  - Member rows stay matchable by name, because part 1's `not[labels]` must match its row. So a build without the
    new arm finds `granular_scopes[].access` a documented body row and reports nothing for it.
  - The QUERY exemption is held by `test_every_record_matches_its_reference_section`. Every part-1 `Param` with `[` or
    `:` is a `not[...]` QUERY `Param` (`families/plan.py`), so a build without the exemption fails on the `plan`
    records.
  - `BodyFormat.FORM` exists (`registry.py` `BodyFormat`).
- Iteration-03 C1: APPLIED. `create#health` is `GET /projects/:id/repository/health`, and `generate` is its only row, a
  query row (`rest/create.md` "Health"). A build that reports the placeholder `id` because no row holds it fails the
  pin.
- Spec lane C1: APPLIED. The path-row item reads "a placeholder … of none of the section's endpoints". It can only
  report fewer rows than the old item, so no record that passed before now fails N. D8's exceptions row names
  "`record_problems`' path-row rule".

### C1 — The new rejection case does not say that the record is complete
Severity: C
Location: design.md § D5 `test_the_method_rejects_a_call_that_differs`, the `create-an-application` case
Defect: The case's record is "built as `…#create-an-application` with the BODY `Param` `granular_scopes[].access`".
  The shared oracle is "a problem that names … the attribute". Suppose a build gives the record only that `Param`.
  Then "a query or body row that the record lacks" reports `name`, `redirect_uri`, `scopes`, `confidential` and
  `granular_scopes`, and the case passes without the member arm. Read like step 1 ("as a slice writes it"), the case
  fails as it should.
Proposed-edit: replace the case with "a record built as a slice writes
  `software-supply-chain-security#create-an-application` (the BODY `Param`s `name`, `redirect_uri`, `scopes`,
  `confidential` and the `ARRAY_OF_HASHES` `granular_scopes`), plus the BODY `Param` `granular_scopes[].access`; its
  one problem names `granular_scopes[].access`."

### C2 — Two halves of the delta that must report nothing have no pin
Severity: C
Location: design.md § D5 `test_a_section_is_read_as_the_reference_writes_it`
Defect: Two halves of the delta can be wrong without any named case failing:
  - the FORM exemption of the member arm;
  - the path-row item's "of none of the section's endpoints", as against the old "of the record's path".
  If either is built wrong, a correct record is reported, and the first slice that declares it has to edit N, which
  D8 lists as "never". Checked against the reference:
  - `growth#force-a-variant-assignment` (`POST /experiments/:experiment_name/assignments`) has the rows `variant`,
    `context[user]`, `context[namespace]` and `context[project]`, and no `context` row.
  - `fulfillment#delete-an-ldap-group-link-deprecated` has the endpoints `DELETE /groups/:id/ldap_group_links/:cn`
    and `…/:provider/:cn`. Its `path` rows are `id`, `cn` and `provider`.
Proposed-edit: after the `create#health` pin, add "A `BodyFormat.FORM` record built as
  `growth#force-a-variant-assignment` (the BODY `Param`s `variant`, `context[user]`, `context[namespace]`,
  `context[project]`) gets no problem from `record_problems`. Neither does a record built as
  `fulfillment#delete-an-ldap-group-link-deprecated` on `DELETE /groups/:id/ldap_group_links/:cn`, though its table
  has the `path` row `provider`."

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
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs` (six cases), `test_a_section_is_read_as_the_reference_writes_it` | COVERED (C1, C2) |
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

Verdict: CLEAN (0 A, 0 B) — TEST-READY (27 COVERED, 0 GAP)
