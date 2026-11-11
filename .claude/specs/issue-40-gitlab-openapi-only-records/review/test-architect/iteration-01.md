# Test-architect review — design, iteration 01

## Findings

### C1 — A glob value that is only `.` or `..` has no test
Severity: C
Location: design.md § Correctness Properties, AC-2.2
Defect: P `test_a_glob_value_with_a_refused_part_is_refused` inserts the refused part into a list of one or more valid parts, so it never generates `.` or `..` as the whole value, and R `test_a_glob_part_that_is_no_segment_is_refused` lists `""` alone but neither of those.
Material-because: AC-2.2 — the bare traversal value is in its domain and no example or generated case reaches it.
Proposed-edit: in the R entry replace "`a//b`, `/a`, `a/`, `a/./b`, `a/../b` and `""` each raise" with "`a//b`, `/a`, `a/`, `a/./b`, `a/../b`, `""`, `.` and `..` each raise".

### C2 — The path-parameter check passes on an empty `OPERATIONS`
Severity: C
Location: design.md § Correctness Properties, AC-1.4 (F `test_no_param_names_a_path_parameter`)
Defect: the oracle quantifies over `openapi_only.OPERATIONS`, which is empty until the records land, so the test is green at the wave's red capture and alone proves nothing about an empty module.
Material-because: AC-1.4 — the test cannot be red for the right reason before the IMPL task.
Proposed-edit: append to the F entry: "`openapi_only.OPERATIONS` is not empty (as N's `assert records`)."

### C3 — The paged records' `page` and `per_page` Params fail no test when omitted
Severity: C
Location: design.md § D4 "The paged records"; § Correctness Properties, AC-1.5
Defect: D4 has each paged record declare its `page` and `per_page` rows (AC-1.3), but N `paging_parameters` lets a paged record omit them, and F's `KINDS` and `REQUIRED` hold neither (both `SCALAR`, not required).
Material-because: AC-1.3 — one `Param` per `query` row; sixteen rows are declared by D4 and checked by nothing.
Proposed-edit: append to the AC-1.5 F entry: "; each paged record's `params` holds `Param(name="page", location=Location.QUERY)` and `Param(name="per_page", location=Location.QUERY)`."

## Coverage

| Criterion | Tests (design D5) | Kind | Fails when | Status |
|---|---|---|---|---|
| AC-1.1 | F `test_nothing_is_pending`; V `test_every_declared_key_is_in_its_family` | example; structural | an ID missing, extra or repeated against literal `OPERATION_IDS`; a `(method, path)` not on a row carrying its Reference | COVERED |
| AC-1.2 | G `test_nothing_is_pending`, `test_no_record_declares_an_openapi_only_model_id` | example | `deploy.PENDING` non-empty or IDs not D4's three; `registry.lookup` finds an `openapi-only#` model ID | COVERED |
| AC-1.3 | N `test_every_record_matches_its_reference_section`; F, G `test_every_param_is_typed_as_its_row` | structural; example | a `Param` off its row's name or `In`; a row undeclared; `KINDS`, `REQUIRED`, body or `fixed` differ from the literal tables | COVERED (C3) |
| AC-1.4 | F `test_no_param_names_a_path_parameter`; G typing; N `test_a_path_form_is_read_and_sent_as_written` | structural; example | a `Param` named as a placeholder; `record_problems` flags a glob row or stops flagging `status` | COVERED (C2) |
| AC-1.5 | F `test_only_the_list_records_are_paged`; G typing | example | the OFFSET set differs from D4's eight (the eight `page`+`per_page` GET sections of `rest/openapi-only.md`); another record not NONE | COVERED |
| AC-1.6 | F, G `test_nothing_is_pending`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | example; structural | a key pending or unmapped | COVERED |
| AC-2.1 | P `test_glob_value_keeps_each_slash`; R `test_a_glob_value_keeps_its_slashes`; F path-form row "glob holding `/`" | property; example; `main` | a `/` encoded or lost, a piece not decoding to its part, raw `?`/`#`; the `%40`, `%3F%23`, `%252e` literals; the URL literal | COVERED |
| AC-2.2 | P `test_a_glob_value_with_a_refused_part_is_refused`; R `test_a_glob_part_that_is_no_segment_is_refused`; F `test_a_glob_part_that_is_no_segment_sends_nothing` | property; example; `main` | no `GitLabAPIError`; a request recorded; exit not 1 | COVERED (C1) |
| AC-2.3 | R `test_an_optional_group_is_written_only_when_given`; F rows "group given/left out", `test_a_missing_path_parameter_is_refused_unless_optional`; G `test_the_optional_group_is_sent_only_when_given` | example; `main` | group written when absent or `None`, dropped when given, `""` accepted; the refusal names `path` as missing | COVERED |
| AC-2.4 | F `test_a_missing_path_parameter_is_refused_unless_optional`; R `test_placeholders_name_every_path_form` | example; `main` | a missing glob accepted; the message omits `package_name` or `path`; the `placeholders`/`required_placeholders` tuples differ | COVERED |
| AC-2.5 | R `test_an_escaped_parenthesis_is_sent_without_its_backslash`; F NuGet and `$metadata` rows | example; `main` | a backslash sent; `\(\)` read as a group; `$`, `'`, `,`, `=` altered | COVERED |
| AC-2.6 | F `test_a_path_form_is_sent_as_the_route_declares` (7 rows), `test_a_glob_part_that_is_no_segment_sends_nothing`; G group test | `main` + `FakeGitLab` | the recorded `(method, url)` differs from the row's literal; a refused call records a request | COVERED |
| AC-3.1 | N `test_every_record_is_sent_as_its_section_documents`; F path-form rows | structural; `main` | a record exits non-zero, sends other than one request, or the call half names a difference; no configured project | COVERED |
| AC-3.2 | F `test_an_upload_sends_the_file_as_its_part` (4); G `test_the_upload_sends_the_file_as_its_part` | `main` | not multipart; the `file` part lacks `filename` or bytes; a `-f` part carries a `filename` | COVERED |
| AC-3.3 | N both record tests, `test_a_path_form_is_read_and_sent_as_written` | structural; example | a record differs from its section; D3's edits mask `(v1/)`, a dropped given group, or `\(` sent | COVERED |
| AC-3.4 | F `test_a_list_record_prints_every_page` (8) | `main` | a scripted page unserved; stdout not both pages' items | COVERED |
| UB-1 | C unedited; PR diff | regression | a compat case fails | COVERED |
| UB-2 | P `test_standard_library_only`; C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option`; F `test_a_token_attribute_is_the_value_given` | regression; example | a foreign import; the body `token` not the given value, or the configured token in a body | COVERED |
| UB-3 | `test_github_api_*.py`, `test_wrapper_delivery.py`; PR diff | regression | any fails | COVERED |
| UB-4 | R `test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused`; P `test_path_value_is_one_segment`; K all; N, V existing | regression; property | a `:name` path sent differently; a #41 refusal changes | COVERED |

COVERED 20, GAP 0. Test-first: F, G, R, P and N import the package inside each test, so before IMPL they fail on assertions or a missing attribute, never at collection; G `test_no_record_declares_an_openapi_only_model_id` and the UB regressions are green at the red capture by nature.

CLEAN (0 A, 0 B; 3 C, 0 D)

Verdict: READY
