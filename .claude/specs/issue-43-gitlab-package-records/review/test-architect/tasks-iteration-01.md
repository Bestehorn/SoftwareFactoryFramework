# Test architect — tasks iteration 01 — issue #43

## Findings

### C1 — Task 2.1's red sentence does not hold for its `--file` refusal call
Severity: C
Location: tasks.md § Wave 2, 2.1 (Red); design.md § Correctness Properties, AC-4.2
Defect: 2.1 says each call is red by "exit 2 (...), failing its exit-code or request assertion". The refusal call of `package#upload-a-package-file-3` with `--file file=…` expects exit 2 and no request, and the red tree already gives both because `registry.lookup` refuses the ID. Written as a case of its own, it passes on the red run.
Material-because: clarification only. The call can still fail after 2.3: a `file` `FILE` `Param` on that record would be accepted and sent. F's `KINDS` also pins the same absence.
Proposed-edit: append to 2.1's Red sentence: "; the `--file` refusal of `package#upload-a-package-file-3` is asserted inside that record's case, after its `--input` send, so that case is red on the send".

### D1 — F.3's "the run of every wave" includes wave 1's red run
Severity: D
Location: tasks.md § Final, F.3
Defect: Wording. 1.3 states that N's existing record tests raise `AttributeError` on wave 1's red run. F.3 says they pass "in the run of every wave that names them".
Proposed-edit: replace "pass in the run of every wave that names them" with "pass in the green run of every wave that names them".

## Checks

- **#40's symbols.** Every #40 symbol the Precondition and the tasks cite exists on #40's branch (`6f0ced8`): `PLACEHOLDER` with its `sigil` group, `required_placeholders`, `RestOperation.content_type`, `send(data=)`, `Transport.request_raw`, `refuse_both_bodies` and `refuse_raw_body`, and N's `glob_names` (read only by `record_problems`) and `documented_raw_body`.
- **`origin/main` since `25c91d3`.** Issue #44's GraphQL uploads and the `None` values in `GATED_OPERATIONS` leave `prepare_call`'s `lookup` → `refuse_raw_body` order and `send_call` as 2.4 names them. Nothing on main touches `families/package.py`.
- **N's existing tests red until 1.4.** N's existing record tests going red with `AttributeError` on `route_prefixes` is the #40 precedent. #40's wave-1 red capture (`8b489b0`, `evidence/red/wave-1.txt`) shows six existing N tests failing on `AttributeError: 'RestOperation' object has no attribute 'content_type'`, and its green capture passes them. The error is raised inside the test body, which is the red class the preamble admits. Accepted.
- **D1 changes no existing assertion.** No existing case of R, P, N, K, F, G, C or T holds a `:name-x` form. `operations-index.md` holds one, the "Upload module" row.
- **No existing record is a prefix record.** Every `/<route-prefix>/` row of the index is a `rest/package.md` Reference, and only `rest/package.md` has a `<route-prefix>` line. So neither `expand`'s refusal nor `prefix_problems` reaches an existing record.
- **The new field breaks no test.** No test enumerates `RestOperation`'s fields.
- **K is red for the right reason.** `refused_messages` asserts an ERROR log record. argparse's refusal of the unrecognized `--route-prefix` writes only to standard error, so it fails that assertion. Each `lookup` refusal fails the content assertion instead: the three values, `"id"`, "has no value", or the ID.
- **F is red for the right reason.** `fx.run_main` returns the code of argparse's `SystemExit`, so each send fails on exit 2 ≠ 0, and the glob `..` case fails on exit 2 ≠ 1. The table tests fail on their equalities, and `test_no_param_names_a_path_parameter` fails because `OPERATIONS` is empty.
- **R and P are red for the right reason.** The synthetic records are built inside the test body, so each fails with a `TypeError` on `route_prefixes`, never with a collection error.
- **Wave 2 must stay unsplit.**
  - N's send test over every record needs 2.3's prefix records and 2.4's `--route-prefix` in one green run.
  - K's cases need 2.3's `package#` records.
  - Files are disjoint in every wave: R / P / N / `registry.py`; F / K / `package.py` / `call.py`; the entry script / the map / the ledger.
  - Each TEST precedes its IMPL.
- **Run lines.** On the rebased tree, the globs of waves 1 and 2 expand to every file of the legend:
  - F (wave 2 on), R, K, T, C, H, P, N and V;
  - every family suite, #40's `test_gitlab_api_openapi_only.py` and `test_gitlab_api_deploy.py` included;
  - `test/test_gitlab_graphql_contract.py`.

  `scripts/run_tests.py` hands the file targets to pytest. Wave 3's line covers 3.1 (C `test_the_usage_names_the_operation_call`), 3.2 (`test_llm_map_within_cap`) and 3.3 (the ledger cap), all in `test_instruction_corpus_budget.py` except C's.
- **F.1.** It names `.github/workflows/ci.yml`'s `verify` job, matrix `group` `tests` (`python scripts/run_checks.py --group ${{ matrix.group }}`).

## Coverage

| Criterion | Test task(s) | Status |
|---|---|---|
| AC-1.1 | 2.1 F `test_nothing_is_pending_but_the_kept_keys`; V `test_every_declared_key_is_in_its_family` (wave 2 Run line) | COVERED |
| AC-1.2 | 2.1 F `test_a_two_endpoint_entry_maps_its_first_endpoint` | COVERED |
| AC-1.3 | 2.1 F `test_nothing_is_pending_but_the_kept_keys` | COVERED |
| AC-1.4 | 2.1 F `test_every_param_is_typed_as_its_row`; N `test_every_record_matches_its_reference_section` (wave 2) | COVERED |
| AC-1.5 | 1.3 N pinning example; 2.1 F `test_no_param_names_a_path_parameter` | COVERED |
| AC-1.6 | 2.1 F `test_only_the_list_records_are_paged` | COVERED |
| AC-1.7 | 2.1; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` (wave 2) | COVERED |
| AC-2.1 | 1.3 N reader and `prefix_problems`; 2.1 F literal tuples; N structural (wave 2) | COVERED |
| AC-2.2 | 1.1 R `test_route_writes_the_chosen_prefix`; 2.1 F `test_a_prefix_record_is_sent_under_each_of_its_values` | COVERED |
| AC-2.3 | 2.1 F rows under `/projects/:id/…` given no `id` | COVERED |
| AC-2.4 | 1.1 R `test_a_prefix_record_is_sent_only_under_a_prefix`; 1.2 P property; 2.2 K `test_a_route_prefix_the_record_does_not_list_is_refused` | COVERED |
| AC-2.5 | 2.1 F sends (one row per value, one record per page); 2.2 K refusals | COVERED |
| AC-3.1 | 1.1 R; 1.3 N; 2.1 F `test_the_hyphenated_names_are_sent_as_one_segment_each`; 2.2 K `test_a_hyphenated_name_is_documented_and_required` | COVERED |
| AC-3.2 | 2.1 F `test_a_glob_record_is_sent_with_its_slashes`, F Debian rows | COVERED |
| AC-3.3 | 2.1 F hyphenated and glob tests through `main` | COVERED |
| AC-4.1 | 2.1; N `test_every_record_is_sent_as_its_section_documents` (wave 2); K's existing tests | COVERED |
| AC-4.2 | 2.1 F both upload tests; K `test_a_raw_body_the_call_cannot_send_is_refused`, G `test_the_upload_sends_the_bytes_as_its_body` (wave 2) | COVERED |
| AC-4.3 | 1.3 N pinning example; N's two record tests (wave 2) | COVERED |
| AC-4.4 | 2.1 F `test_a_list_record_prints_every_page` | COVERED |
| UB-1 | F.3 diff; C on every Run line | COVERED |
| UB-2 | 1.2 P property; F.3 (C, K, T tests named); P `test_standard_library_only` | COVERED |
| UB-3 | F.2 diff and the GitHub suites in CI's `tests` leg | COVERED |
| UB-4 | 1.1 R; 1.3 N `test_only_the_upload_module_path_holds_a_hyphenated_name`; F.3; the GitLab suites on waves 1 and 2 | COVERED |

A 0, B 0, C 1, D 1. COVERED 23, GAP 0.

Verdict: READY
