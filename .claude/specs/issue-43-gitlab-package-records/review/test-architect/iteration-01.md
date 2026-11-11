# Test architect — design iteration 01 — issue #43

## Findings

### C1 — AC-4.2's standard-input clause and its third bullet are held by #40's tests, which the entry does not name
Severity: C
Location: design.md § Correctness Properties, AC-4.2
Defect: The AC-4.2 entry names F's two upload tests. Neither one gives `--input -`, and neither gives `--input` beside `-f`/`-F` or to a record without a `content_type`. The case F does refuse (`--file` given to `package#upload-a-package-file-3`) is #41's undocumented-name refusal, not AC-4.2's IF clause. Both behaviours are record-independent (`read_input`, `refuse_both_bodies`, `refuse_raw_body`) and are held by #40's tests on the rebased tree, but the mapping does not say so.
Material-because: clarification only. UB-4 keeps those tests running unedited, and F's `RAW_BODIES` equality fixes which records of this change have a `content_type`, so nothing is untested.
Proposed-edit: append to the AC-4.2 entry: "- Held unedited from #40: G `test_the_upload_sends_the_bytes_as_its_body` (`--input -`, the bytes of standard input) and K `test_a_raw_body_the_call_cannot_send_is_refused` (`--input` beside `-f` or `-F`, and `--input` to a record whose `content_type` is `None`); F `test_every_param_is_typed_as_its_row`'s `RAW_BODIES` equality fixes which records of this change take `--input`."

## Coverage

| Criterion | Test(s), kind | Fails when | Status |
|---|---|---|---|
| AC-1.1 | F `test_nothing_is_pending_but_the_kept_keys` (example); V `test_every_declared_key_is_in_its_family` (structural) | an ID is missing, extra or duplicated; a key is not on its Reference's row | COVERED |
| AC-1.2 | F `test_a_two_endpoint_entry_maps_its_first_endpoint` (example) | a record maps a second endpoint, or the other key leaves `PENDING` | COVERED |
| AC-1.3 | F `test_nothing_is_pending_but_the_kept_keys` (example) | a registry-host key is recorded or leaves `PENDING` | COVERED |
| AC-1.4 | N `test_every_record_matches_its_reference_section` (structural); F `test_every_param_is_typed_as_its_row` (example: `KINDS`, `REQUIRED`, `RAW_BODIES`, JSON body, no `fixed`) | a `Param` is mistyped, misplaced, not required, or undeclared | COVERED |
| AC-1.5 | F `test_no_param_names_a_path_parameter`; N `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written` (examples) | `upload-module` declares a `module-*` `Param`; N names its `body` rows as undeclared | COVERED |
| AC-1.6 | F `test_only_the_list_records_are_paged` (example) | the `OFFSET` set differs from D6's literal list, which matches every entry with `page` and `per_page` query rows | COVERED |
| AC-1.7 | F `test_nothing_is_pending_but_the_kept_keys`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | `PENDING` is not exactly the kept keys | COVERED |
| AC-2.1 | N `prefix_problems` inside `test_every_record_matches_its_reference_section` (structural); N pinning example; F literal tuples | a record's `route_prefixes` differ from its page's line, or are non-empty on a record off a prefix path | COVERED |
| AC-2.2 | F `test_a_prefix_record_is_sent_under_each_of_its_values` (parametrized example); R `test_route_writes_the_chosen_prefix` | a sent URL differs from the row's, `id` included (`my-group%2Fsub`) | COVERED |
| AC-2.3 | F rows under `/projects/:id/…` with no `id` | the configured project is missing, or the call is refused because `encode` ran on the record before routing | COVERED |
| AC-2.4 | K `test_a_route_prefix_the_record_does_not_list_is_refused` (parametrized example); P `test_route_accepts_only_the_records_prefixes` (property over any text); R `test_a_prefix_record_is_sent_only_under_a_prefix` | an unlisted, normalised or empty prefix is accepted; a request is recorded; the exit code is not 2; the message omits the values; `id` is accepted under `/packages/npm` | COVERED |
| AC-2.5 | F rows for every value of one npm, one Debian and one NuGet record; K refusals | as AC-2.2 and AC-2.4 | COVERED |
| AC-3.1 | R `test_a_hyphenated_name_is_one_placeholder`; F `test_the_hyphenated_names_are_sent_as_one_segment_each`; K `test_a_hyphenated_name_is_documented_and_required`; N pinning example | the name is read as `module`; `:name-/` swallows the `-`; `module-system` is not required | COVERED |
| AC-3.2 | F `test_a_glob_record_is_sent_with_its_slashes`; F Debian prefix rows | the slashes are encoded; `..` is sent; a missing glob is accepted | COVERED |
| AC-3.3 | F hyphenated-name and glob tests, through `main` | as AC-3.1 and AC-3.2 | COVERED |
| AC-4.1 | N `test_every_record_is_sent_as_its_section_documents` (structural); F rows; K's existing output tests | a record exits non-zero, sends anything but one request, or sends an undocumented name | COVERED |
| AC-4.2 | F `test_a_raw_upload_sends_the_bytes_as_its_body`, `test_an_upload_sends_the_file_as_its_part` (parametrized examples); F `RAW_BODIES`; #40's G and K tests (C1) | the body is not the exact bytes or the wrong media type; a part lacks its `filename` or its bytes; a form field is not a part | COVERED |
| AC-4.3 | N's two structural tests; N pinning example (`routed_section`, `call_problems`, `prefix_problems`) | N passes an unrouted path or a prefix from another page, or misses a wrong `route_prefixes` | COVERED |
| AC-4.4 | F `test_a_list_record_prints_every_page` (one case per paged record of D6) | the second page is not fetched, not printed, or printed out of order | COVERED |
| UB-1 | C, unedited; PR diff | a compat case breaks | COVERED |
| UB-2 | P `test_standard_library_only`; C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` (reads the parser's options); T origin and redirect tests; P route property | a non-stdlib import appears; a token option appears; another origin is reached | COVERED |
| UB-3 | `test_github_api_*.py`, `test_wrapper_delivery.py` in CI `tests`; PR diff | a GitHub file changes or a GitHub test fails | COVERED |
| UB-4 | N `test_only_the_upload_module_path_holds_a_hyphenated_name` (every index row against #40's literal pattern); R in-segment and repeated-name examples; existing suites unedited | any index row other than "Upload module" changes its names (`operations-index.md` has only one `[:*]name-x` match, the "Upload module" row); a repeated `:file_name` is written two ways | COVERED |

Red before implementation, on the tree rebased onto #40 (DL-001): F calls fail at `lookup` (exit 2); R, K and P fail inside the test body (`route`, `route_prefixes` and `--route-prefix` are absent). The N UB-4 sweep fails on the "Upload module" row (`module` ×3). R and P build their synthetic records inside the test (`glob_operation`, `one_query_parameter_operation`), and F imports the family inside each test, so no new test adds a collection error.

A 0, B 0, C 1, D 0. COVERED 23, GAP 0.

Verdict: READY
