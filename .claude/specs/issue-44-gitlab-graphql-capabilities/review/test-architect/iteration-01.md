# Test-architect review — design, iteration 01

### B1 — AC-5.1's ID check cannot fail for two records
Severity: B
Location: design.md § Correctness Properties, AC-5.1
Defect: The oracle "holds every capability followed by the IDs of its records" is a containment check, and D8 writes
`graphql#workItem` on the line that also holds `graphql#workItemsByReference` and the `graphql#workItem…` mutations,
and `graphql#Query.vulnerability` beside `graphql#Query.vulnerabilities`, so the check passes with either shorter ID
missing from the docstring.
Material-because: AC-5.1 (the docstring names the operation ID of every GraphQL record) is untested for
`graphql#workItem` and `graphql#Query.vulnerability`.
Proposed-edit: after "before the next capability" insert ", each ID matched whole: not followed by a letter, digit or
`_`, nor by `.` and a letter (`graphql#workItem` is not found in `graphql#workItemsByReference`)".

### B2 — AC-5.2's file clause already holds before the change
Severity: B
Location: design.md § Correctness Properties, AC-5.2
Defect: `test_the_map_names_the_graphql_call` asserts that `docs/forLLMConsumption.md` holds `--file`, which its
`src/payload/scripts/gitlab_api/` bullet already holds in `call`'s REST option list ("`-f/--raw-field`, `-F/--field`,
`--file`; a GraphQL record's variables with `-f`/`-F`"), so that assertion is green before and after the change.
Material-because: AC-5.2's "a file included" has no oracle that can fail.
Proposed-edit: replace "`docs/forLLMConsumption.md` holds `call graphql#` and `--file`" with "the
`src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md` holds `call graphql#`, `--file NAME=PATH` and
`Upload` (D8's sentence)".

### C1 — AC-1.3's test iterates what the reader finds
Severity: C
Location: design.md § Correctness Properties, AC-1.3
Defect: `test_every_member_a_row_names_is_selected` passes for a row from which `row_members` reads no member;
`test_the_reference_is_read_as_written` pins rows 6 and 8 only.
Proposed-edit: append to AC-1.3's entry: "It fails when the capabilities of `row_members` differ from the table's first
cells, or when a row has no member."

### C2 — Q's altered copies must be made after collection
Severity: C
Location: design.md § Correctness Properties, Q's method, `test_the_method_rejects_a_document_that_differs`
Defect: The design does not say when the `dataclasses.replace` copies are made; built in the parametrization, they look
up records that do not exist before the IMPL wave, and the TEST wave's red run becomes a collection error.
Proposed-edit: append to the case list: "Each case is a record ID and a change; the copy is made inside the test."

### C3 — AC-3.1's "bytes unchanged" needs bytes a text round-trip alters
Severity: C
Location: design.md § Correctness Properties, AC-3.1
Defect: "two of distinct bytes" lets the example pass with ASCII bytes, which a decode-and-encode would not change.
Proposed-edit: replace "with two of distinct bytes" with "with two files of distinct bytes, each holding a byte that is
not UTF-8 and a CRLF".

### C4 — AC-5.1's test on an empty `OPERATIONS`
Severity: C
Location: design.md § Correctness Properties, AC-5.1
Defect: Unlike its other structural tests, the design does not say this test fails when it finds no record, as #30's
twin does.
Proposed-edit: append: "It fails when `graphql_only.OPERATIONS` holds no record."

## Coverage

| Criterion | Test (red before IMPL because) | Status |
|---|---|---|
| AC-1.1 | design inspection; Q `test_every_record_matches_the_reference` (empty `OPERATIONS`) | COVERED |
| AC-1.2 | Q `test_every_capability_has_a_record` (no record; `PENDING_CAPABILITIES` not empty); V unchanged | COVERED |
| AC-1.3 | Q `test_every_member_a_row_names_is_selected` (no member selected); method case `async: false` | COVERED (C1) |
| AC-1.4 | G `test_every_record_id_is_looked_up_once` (empty `OPERATIONS`) | COVERED |
| AC-2.1 | G `test_a_variable_holds_the_given_json_value`, six JSON kinds (unknown ID, exit 2); G structural | COVERED |
| AC-2.2 | G `test_a_work_item_list_prints_every_node`; G structural; AC-2.4's no-`endCursor` case fails a print before the last page | COVERED |
| AC-2.3 | G `test_every_record_is_called_through_main` (calls none) | COVERED |
| AC-2.4 | G `test_a_graphql_failure_exits_1_with_its_details`, one case per listed condition (unknown ID or refused `--file`, exit 2) | COVERED |
| AC-2.5 | G `test_every_record_is_called_through_main`, two pages per connection (calls none) | COVERED |
| AC-3.1 | G `test_a_design_upload_sends_each_file_as_a_part`; T `test_graphql_sends_files_as_one_multipart_request` (no `files`); R `upload_variables`, `split_uploads` (absent) | COVERED (C3) |
| AC-3.2 | G two-file case, `map` per item | COVERED |
| AC-4.1 | G `test_a_refused_mutation_sends_nothing` over `REFUSED_IDS`; Q ID-to-root-field check | COVERED |
| AC-4.2 | same G test ("no subcommand sends it", not "which sends it"); K `test_a_gated_operation_names_its_subcommand` | COVERED |
| AC-4.3 | same G test, fails when an ID of `REFUSED_IDS` names no record | COVERED |
| AC-5.1 | G `test_the_usage_names_every_graphql_record` (no `call graphql#` line) | GAP (B1) |
| AC-5.2 | Q `test_the_map_names_the_graphql_call` (no `call graphql#`); `test_llm_map_within_cap` | GAP (B2) |
| UB-1.1 | C unchanged; the diff touches no line of C | COVERED |
| UB-1.2 | K, N, R unchanged; G `test_a_file_for_a_variable_that_is_no_upload_is_refused` | COVERED |
| UB-2.1 | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` | COVERED |
| UB-2.2 | P `test_standard_library_only` (scans every module under the package) | COVERED |
| UB-3.1 | the diff names no GitHub file; the GitHub suites in CI's `tests` leg | COVERED |

NOT-CLEAN (0 A, 2 B)

Verdict: NOT-READY
