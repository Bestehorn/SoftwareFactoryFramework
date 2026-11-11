# Test-architect review — design, iteration 02 (delta)

Scope: the C1-C3 fix sites, the restated AC-3.2 with D5, D6 and their Correctness Properties, and the R/T/K/F/G/N
placements against `testing.md` item 3.

## Findings

### B1 — F's `REQUIRED` oracle expects a `file` Param on the three `openapi-only#` raw-body records
Severity: B
Location: design.md § Correctness Properties, AC-1.3 (F `test_every_param_is_typed_as_its_row`, the `REQUIRED` bullet)
Defect: `REQUIRED` is "the `yes` rows that name no path parameter". The `file` rows of `openapi-only#upload-package-file`, `openapi-only#upload-terraform-module-package-file` and `openapi-only#create-or-update-a-terraform-state` read Required `yes` and name no path parameter (`rest/openapi-only.md`, `| \`file\` | form | file | yes |`), so the literal table holds `file` for each, while D4 gives those records no `file` Param. `KINDS`, one bullet above, carries the exclusion "but a raw-body record's `file` row"; `REQUIRED` does not.
Material-because: AC-3.2 ("A raw-body record's `file` row is that body and no `Param`") and AC-1.3. As written, the test fails against records built to D4, and passes only if a `file` Param is declared, which N's `documented_raw_body` then flags.
Proposed-edit: in that bullet replace "the `yes` rows that name no path parameter;" with "the `yes` rows that name no path parameter but a raw-body record's `file` row;".

## Coverage

| Criterion | Tests (design D6) | Kind | Fails when | Status |
|---|---|---|---|---|
| AC-1.1 | as iteration 01 | example; structural | as iteration 01 | COVERED |
| AC-1.2 | as iteration 01 | example | as iteration 01 | COVERED |
| AC-1.3 | N `test_every_record_matches_its_reference_section` through `documented_raw_body`; F, G `test_every_param_is_typed_as_its_row` | structural; example | a `Param` off its row; a raw-body `file` declared (`KINDS`, N); a raw-body Param not `Location.QUERY` or `content_type` not octet-stream (`RAW_BODIES`, G); `REQUIRED` as written also fails a correct raw-body record | COVERED (B1) |
| AC-1.4 | F `test_no_param_names_a_path_parameter`; G typing; N `test_a_path_form_is_read_and_sent_as_written` | structural; example | `OPERATIONS` empty, so red before IMPL (C2 closed); a Param named as a placeholder; `record_problems` names `file` of the raw `upload-package-file` or stops naming `status` | COVERED |
| AC-1.5 | F `test_only_the_list_records_are_paged` | example | the OFFSET set differs from D4's eight; a paged record lacks `Param(name="page", location=Location.QUERY)` or the `per_page` one. All eight sections' rows are `query`, `integer (int32)`, not required, so the literal equals a correct Param (C3 closed) | COVERED |
| AC-1.6 | as iteration 01 | example; structural | as iteration 01 | COVERED |
| AC-2.1 | as iteration 01 | property; example; `main` | as iteration 01 | COVERED |
| AC-2.2 | P; R `test_a_glob_part_that_is_no_segment_is_refused`; F `test_a_glob_part_that_is_no_segment_sends_nothing` | property; example; `main` | before D1 `*path` is literal and nothing raises; after, a `_glob` that checks only the parts between slashes passes `.` or `..` alone (C1 closed) | COVERED |
| AC-2.3 to AC-3.1 | as iteration 01 | example; `main`; structural | as iteration 01 | COVERED |
| AC-3.2 multipart | F `test_the_job_artifacts_upload_sends_the_file_as_its_part` | `main` | not `multipart/form-data`; the `file` part lacks a `filename` or the `\r\n`/`\xff` bytes; the `-f` part carries a `filename`; `metadata` not `FILE` (`KINDS`) | COVERED |
| AC-3.2 raw | F `test_a_raw_upload_sends_the_bytes_as_its_body` (3); G `test_the_upload_sends_the_bytes_as_its_body` (`--input -`); R `test_send_sends_a_raw_record_its_bytes`; T `test_a_raw_body_is_sent_unchanged` | `main`; unit | the body differs from the bytes (a text-layer read translates `\r\n` under cp1252 and fails on `\xff` under UTF-8; G's `TextIOWrapper` exposes the bytes only through `.buffer`); `Content-Type` not octet-stream; `status`/`select` missing from the URL; `data` for a `content_type=None` record not `ValueError`; `data=None` sends a body or a `Content-Type` | COVERED |
| AC-3.2 refusals | K `test_a_raw_body_the_call_cannot_send_is_refused` | `main` | exit not 2, a request recorded, or no ERROR record naming `--input`, `-f/--raw-field` and `-F/--field` (beside `-f` and beside `-F`), or the ID and `--input` (`plan#retrieve-a-project-issue`, in `families/plan.py`; K's synthetic `graphql#syntheticProject`); a missing file whose standard error lacks `argument --input:` and the `json.dumps` path | COVERED |
| AC-3.3 | N both record tests; `test_a_path_form_is_read_and_sent_as_written` | structural; example | as iteration 01; the raw `upload-package-file` case above | COVERED |
| AC-3.4 | as iteration 01 | `main` | as iteration 01 | COVERED |
| UB-1 to UB-4 | as iteration 01 | regression; example; property | as iteration 01 | COVERED |

COVERED 20, GAP 0 (AC-3.2 counted once).

Test-first: before D5's code `--input` is an unrecognised argument of `parse_args` (`gitlab_wrapper.py` `main`), so F and G
exit 2, not 0. K's `refused_messages` finds no ERROR record, because argparse writes only to standard error, and the
missing-file case reads "unrecognized arguments", not `argument --input:`. T raises `AttributeError` (`request_raw`) and R
`TypeError` (`content_type`), each inside the test, because R builds its records in the test and T imports in a helper.
N's new helpers are named inside the test body. None of them is a collection error.

Placement: R covers `registry.send`'s `data`, T covers `Transport.request_raw`, and K covers `read_input`,
`refuse_both_bodies` and `refuse_raw_body` in `commands/call.py`. F and G cover their family modules through `main`
(#41 D8), and N and P stay in `test/`. Each test module covers its source module (`testing.md` item 3).

NOT-CLEAN (0 A, 1 B; 0 C, 0 D)

Verdict: NOT-READY
