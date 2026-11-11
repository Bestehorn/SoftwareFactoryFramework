# Test-architect review — design, iteration 03 (delta)

Scope: iteration 02's B1 fix site (F `REQUIRED`), the job-artifacts `file`-only edit (AC-3.2, D4), D5 step 1's refusal
message naming `--query`, and AC-1.3's reordered clause, each against its oracle.

B1 is closed. F's `REQUIRED` bullet now reads "the `yes` rows that name no path parameter, a raw-body record's `file`
row excepted". This matches `KINDS`. Against `rest/openapi-only.md`:

- the three `openapi-only#` raw-body records have no remaining `yes` row: `package_version` and `module_version` are
  globs, and `file` is excepted. So they are absent from `REQUIRED`, and a record built to D4 passes.
- a raw-body record that declares a required `file` `Param` fails three times: `REQUIRED` gains its ID, `KINDS` gains
  `file`, and N's `documented_raw_body` finds the row missing from the section.

The oracle can fail, and only on a wrong record.

The job-artifacts edit leaves `KINDS` determinate. The `metadata` row (`form`, `file`, not required) is on a record
that is not raw-body, so AC-1.3 and D4's `params` rule still make it a `FILE` `Param`. `KINDS` holds `file` and
`metadata` for `openapi-only#upload-job-artifacts`, and N's "every `query` and `body` row is declared" fails a record
that omits `metadata`. N reads `form` as `body` (`test_gitlab_wrapper_contract.py`, the `IN_FORM` mapping), so
`documented_raw_body`'s "every other `body` row read as `query`" also covers the `form` rows of the raw-body sections.
AC-1.3's reordered clause states what N, F and G already assert. It removes no oracle and adds no criterion.

## Findings

### C1 — K's refusal oracle does not assert the `--query` wording that D5 step 1 now gives the message
Severity: C
Location: design.md § Correctness Properties, AC-3.2 (K `test_a_raw_body_the_call_cannot_send_is_refused`, first bullet)
Defect: D5 step 1's message now says that a raw-body record's attributes are given with `--query`, but K's oracle checks
only for `--input`, `-f/--raw-field` and `-F/--field`. An implementation that leaves the sentence out still passes. AC-3.2
requires only that nothing is sent and the exit is 2, so this is not a coverage gap.
Proposed-edit: replace "a log record names `--input`, `-f/--raw-field` and `-F/--field`;" with "a log record names
`--input`, `-f/--raw-field`, `-F/--field` and `--query`;".

## Coverage

| Criterion | Tests (design D6) | Kind | Fails when | Status |
|---|---|---|---|---|
| AC-1.1, AC-1.2 | as iteration 01 | example; structural | as iteration 01 | COVERED |
| AC-1.3 | N `test_every_record_matches_its_reference_section` through `documented_raw_body`; F, G `test_every_param_is_typed_as_its_row` | structural; example | a `Param` is not on its row; a raw-body `file` is declared (`KINDS`, `REQUIRED`, N); a raw-body `Param` is not `Location.QUERY`, or its `content_type` is not octet-stream (`RAW_BODIES`, G); `metadata` is missing or not `FILE` (`KINDS`, N) | COVERED (B1 closed) |
| AC-1.4 | as iteration 02 | structural; example | as iteration 02 | COVERED |
| AC-1.5, AC-1.6 | as iteration 02 | example; structural | as iteration 02 | COVERED |
| AC-2.1 to AC-2.6 | as iteration 02 | property; example; `main` | as iteration 02 | COVERED |
| AC-3.1 | as iteration 01 | structural; `main` | as iteration 01 | COVERED |
| AC-3.2 multipart | F `test_the_job_artifacts_upload_sends_the_file_as_its_part` | `main` | the body is not `multipart/form-data`; the `file` part lacks a `filename` or the `\r\n`/`\xff` bytes; the `-f` part carries a `filename` | COVERED |
| AC-3.2 raw | F `test_a_raw_upload_sends_the_bytes_as_its_body` (3); G `test_the_upload_sends_the_bytes_as_its_body`; R `test_send_sends_a_raw_record_its_bytes`; T `test_a_raw_body_is_sent_unchanged` | `main`; unit | as iteration 02 | COVERED |
| AC-3.2 refusals | K `test_a_raw_body_the_call_cannot_send_is_refused` | `main` | the exit is not 2; a request is recorded; the message does not name the options (C1 adds `--query`), or does not name the ID and `--input`; a missing file's standard error lacks `argument --input:` | COVERED |
| AC-3.3, AC-3.4 | as iteration 02 | structural; example; `main` | as iteration 02 | COVERED |
| UB-1 to UB-4 | as iteration 01 | regression; example; property | as iteration 01 | COVERED |

COVERED 20, GAP 0 (AC-3.2 counted once).

Test-first is unchanged from iteration 02: F and G are red before IMPL because `OPERATIONS` is empty and `--input` is
unrecognised. Placement is unchanged: each test module covers its source module (`testing.md` item 3).

CLEAN (0 A, 0 B; 1 C, 0 D)

Verdict: READY
