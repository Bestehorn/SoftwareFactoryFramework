# Test Architect — design review, iteration 01

### B1 — AC-1.7's registry arm has no case
Severity: B
Location: design.md § Correctness Properties AC-1.7
Defect: All three cases (a `404`, spent `429`s, GraphQL `errors`) raise in the transport at step 6, so a `cmd_call` that also catches `GitLabAPIError` around steps 1 to 5, where `registry.pages` runs `registry.expand` for a paged record, exits 2 on D4's "an empty, `.` or `..` path value" row and passes every test.
Material-because: AC-1.7 ("WHEN the transport or the registry raises `GitLabAPIError` … exit 1").
Proposed-edit: AC-1.7, after "a GraphQL `errors` answer at `200`" add "; `--path id=..` on `plan#list-all-project-labels` (`registry.expand` inside step 5) and `--path issue_iid=..` on `plan#retrieve-a-project-issue` (step 6)", and end the oracle with "; for the two path cases, no request is recorded and the message names the path parameter".

### B2 — AC-5.3's "lacks a key that a record maps" has no case
Severity: B
Location: design.md § Correctness Properties AC-5.3; § D6 "AC-5.3's test"
Defect: No case removes the row of a record's Reference; a `family_problems` that compares a record's key only with the rows carrying its Reference finds none, names nothing and passes all four cases, and `coverage_gaps` reads rows, never records.
Material-because: AC-5.3 ("lacks a key that a record maps … SHALL fail and name that key or ID").
Proposed-edit: AC-5.3, "Four cases" → "Five cases", and add "- a record whose Reference no row carries (its row removed) is named by `family_problems`, by its ID."

### C1 — AC-4.1's strings omit the empty-body form
Severity: C
Location: design.md § Correctness Properties AC-4.1
Defect: AC-4.1 names "list, JSON, empty and other responses"; the strings pin three of the four, so D7's "an empty body as nothing" can be dropped with the test green.
Proposed-edit: add `empty body` to the strings (D7 keeps "an empty body as" on one line).

### C2 — AC-1.8's default is not pinned on a path that is exactly `/projects/:id`
Severity: C
Location: design.md § Correctness Properties AC-1.8
Defect: Both default cases continue past `/projects/:id/`, so a check of `startswith("/projects/:id/")` passes, though D2 gives the default to `/projects/:id` as well.
Proposed-edit: add "- A synthetic `GET /projects/:id` record without `--path id` sends to `/projects/<project_id>`."

### C3 — Two synthetic records are not named
Severity: C
Location: design.md § Testing Strategy "CLI tests, in K"
Defect: No declared record carries `fixed` (`families/*.py` hold no `fixed=`) and `GET /projects/:id/jobs/:job_id/artifacts` is on `verify`'s `PENDING`, yet AC-1.2 and AC-1.6 use such records; the synthetic list omits both.
Proposed-edit: in "A synthetic record (…)", add "a record with `fixed` pairs, the `verify#download-job-artifacts-by-job-id` record".

### C4 — R's and T's tests carry no oracle
Severity: C
Location: design.md § Correctness Properties AC-1.2, AC-1.3, AC-1.5, AC-2.2
Defect: `test_send_returns_the_response_of_the_record`, `test_attribute_name_drops_one_trailing_bracket_pair`, `test_variables_are_the_documents_definitions` and `test_is_json_reads_the_content_type` appear in the mapping only; and GraphQL allows white space between `$name` and `:`, which D2's "followed by `:`" leaves open.
Proposed-edit: add the oracles. `attribute_name`: `iids[]` → `iids`, `a[][]` → `a[]`, `not[labels]` unchanged. `variables`: `query Q($fullPath: ID!, $first : Int = 2) { project(fullPath: $fullPath) { id } }` → `("fullPath", "first")`, a connection record's `$after` left out; D2 reads "followed by `:` after any white space". `is_json`: true for `application/json; charset=utf-8`, false for `text/plain` and for no header. `send`: returns a `204`'s `Response`; a GraphQL ID raises `ValueError` with no request.

### C5 — Two reader rules leave rows of the reference unread
Severity: C
Location: design.md § D5 "Reference half"
Defect: An endpoint line can hold several comma-separated keys (`create#generate-changelog-data`, the Conan v1 sections of `rest/package.md`), which "each `` `METHOD path` `` line" misreads; and two rows of `rest/openapi-only.md` (the NuGet symbol-file sections) have `In` `header`, which the `In` rule does not name, so a reader that refuses an unknown `In` fails every N test that reads the reference.
Proposed-edit: "`endpoints`: each `` `METHOD path` `` span of the endpoint line, which can hold several, comma-separated." and "`header` (two `*name`-glob sections of `rest/openapi-only.md`, pending with the Residuals' request forms) is read as neither query nor body."

#28 lessons: X1 holds (`registry.attribute_name`, one rule for `cmd_call` and N; AC-1.2's `--query iids[]=3`). X2 does not apply (a GitLab record has no `accept` or version). X3 holds (H in `test/`). X4 holds (`GATED_OPERATIONS`; K `test_a_gated_operation_names_its_subcommand`). X5 holds but for C5. X6 holds (`feature%2Fx`, `group%2Fproject`, AC-2.2's three-name case, AC-5.3's method-only case) but for B2.

## Coverage

Design phase: the column names the design's tests (the mapping's legend).

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` | COVERED |
| AC-1.2 | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` | COVERED (C3, C4) |
| AC-1.3 | H `test_any_json_value_becomes_the_attribute_value` (property); K `test_an_attribute_carries_its_kind`; R | COVERED (C4) |
| AC-1.4 | K `test_a_list_prints_every_page_as_one_array` | COVERED |
| AC-1.5 | K `test_a_json_or_empty_body_prints_as_documented`; T `test_is_json_reads_the_content_type` | COVERED (C4) |
| AC-1.6 | K `test_a_body_that_is_not_json_is_written_unchanged` | COVERED (C3) |
| AC-1.7 | K `test_an_api_error_exits_1_with_its_details` | GAP (B1) |
| AC-1.8 | K `test_a_project_path_takes_the_configured_project` | COVERED (C2) |
| AC-1.9 | K `test_a_graphql_record_sends_its_document` | COVERED |
| AC-2.1 | K `test_an_unknown_operation_is_refused` | COVERED |
| AC-2.2 | K `test_an_undocumented_parameter_is_refused`; R `test_variables_are_the_documents_definitions` | COVERED (C4) |
| AC-2.3 | K `test_a_missing_path_parameter_is_refused` | COVERED |
| AC-2.4 | K `test_a_value_of_the_wrong_shape_is_refused` | COVERED |
| AC-3.1 | design review; N `test_the_unreachable_rule_has_two_arms` | COVERED |
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` | COVERED (C5) |
| AC-4.1 | C `test_the_usage_names_the_operation_call` | COVERED (C1) |
| AC-4.2 | design review; `test_llm_map_within_cap` | COVERED |
| AC-5.1 | design review (D6, the banner's pin) | COVERED |
| AC-5.2 | design review (D6 table, "Which change fixes it") | COVERED |
| AC-5.3 | V `test_a_regenerated_index_names_each_changed_key`, `test_every_declared_key_is_in_its_family` | GAP (B2) |
| AC-6.1 | V `test_a_route_prefix_key_is_held_to_the_rule`, `test_every_index_row_is_mapped_or_pending` | COVERED |
| AC-6.2 | V `test_a_capability_neither_served_nor_pending_is_named`, `test_the_only_in_graphql_table_is_read_whole` | COVERED |
| AC-6.3 | V `test_every_graphql_only_capability_is_served_or_pending`, `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | COVERED |
| UB-1.1 | C, every existing case unedited; `test_script_usage_error_exits_2` builds the parser with `call.py`; PR diff | COVERED |
| UB-2.1 | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` | COVERED |
| UB-2.2 | P `test_standard_library_only` (`rglob` over the package) | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |

Verdict: NOT-CLEAN (0 A, 2 B) — NOT-TEST-READY (25 COVERED, 2 GAP)
