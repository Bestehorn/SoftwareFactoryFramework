# Test-architect review — issue #46 design, iteration 02 (delta)

## Fix sites

| Finding | Fix site | Status | Check |
|---|---|---|---|
| B1 (Z1) | design.md § Correctness Properties, AC-4.3 | APPLIED | `sys.stdin` is `io.TextIOWrapper(io.BytesIO(...))` over bytes holding `\r\n` and `\xff`. The wrapper's default `newline=None` turns `\r\n` into `\n` on any text read, so `sys.stdin.read().encode()` sends other bytes and the body oracle fails; `\xff` also fails a UTF-8 decode. `.buffer` is the `BytesIO`, so D1's `sys.stdin.buffer.read()` gives the bytes exactly. `run_product_case` and `capsysbinary` leave `sys.stdin` alone (`github_wrapper_fixtures.py` `run_product_case`). |
| C1 | design.md § Correctness Properties, AC-1.1, the missing-file case | APPLIED | Before `--input` exists argparse writes `unrecognized arguments: --input <path>`, which holds neither `argument --input:` nor the `json.dumps` form: the case is red at the capture. K's `argument_named` and `run_reading_stderr` already read that message. |
| C2 | design.md § D4, last two bullets | APPLIED | Checked against #33's draft M (worktree `issue-33`): `RECORDED_IDS = FAMILY_IDS - RESIDUAL_PENDING`, so dropping the ID from the residual set also moves `test_the_records_follow_the_transcription_rules`, whose `_rule_problems` D4's record meets (`ACCEPT_JSON`, `API_VERSION_DEFAULT`, no item key, no `multi_segment`). #33's UB-2 runs through K `_unknown_cases` (`pulls/list`, `issues/levitate`), which neither record touches. M has not landed, so the re-read at the rebase stays the check. |

## Other lanes' edits

- `origin` → `root` (ST-D1) and `_api_url(root=...)` (SEC-C2): T `test_a_raw_body_is_sent_unchanged_to_its_root` sends
  on both roots and AC-4.3 asserts `https://api.github.com`, so a wrong default or a wrong record `root` fails. No test
  calls `_api_url` directly, so UB-1.1 is unaffected.
- K rows `issue-46/<criterion>/…` outside `CALL_CASES` (SR-C1): `CALL_CASES` and `rows_of` stay unedited, as UB-1.1
  requires; no suite collects case names across modules; each new K test runs its rows with `fx.run_product_case`.
- The restated #27 G tests (TA-C2, SR-C3, ST-C1), against G at origin/main f374b3d: `test_no_repos_id_is_pending`
  compares `OPERATIONS` with `REPOS_OPERATION_IDS`, a superset of the removed `RECORDED_IDS`, so the assertion is
  stronger, not relaxed, and red until the upload record exists. `test_every_record_sends_the_default_version_and_media_type`
  holds for D4's record. The multi-segment and `Paging.LINK` tests are untouched by a `Paging.NONE` record with no
  `multi_segment`.
- UB-2.2's `Transport.upload` clause (SR-C4) and the Out of scope redirect list (SR-C5, SR-D1) add no criterion;
  T `test_an_asset_is_uploaded_to_the_upload_url` still protects the former.

No new finding.

## Coverage

| Criterion | Test(s) | Kind | Status |
|---|---|---|---|
| AC-1.1 | Inspection D1–D3; K `test_a_raw_body_the_call_cannot_send_is_refused` (JSON record: log names ID and `--input`; missing file: `argument --input:` and the `json.dumps` path); T `test_a_cross_origin_307_is_not_followed` | inspection + example | COVERED |
| AC-1.2 | H `test_any_bytes_are_sent_as_given` (file form); R `test_send_sends_a_raw_record_to_its_origin`; T `test_a_raw_body_is_sent_unchanged_to_its_root`; K AC-4.2 (non-UTF-8 file), AC-4.3 (standard input, `\r\n` and `\xff`) | property + example | COVERED |
| AC-1.3 | K `test_a_raw_body_with_body_members_is_refused` (`-f`, `-F`) | example | COVERED |
| AC-2.1 | K `test_an_asset_is_uploaded_to_its_host`; N `test_every_record_is_sent_as_its_section_documents`, `test_a_section_is_read_as_the_reference_writes_it` (upload case) | example + contract | COVERED |
| AC-2.2 | K `test_an_asset_is_uploaded_to_its_host`; T `test_a_raw_body_is_sent_unchanged_to_its_root` (third root refused) | example | COVERED |
| AC-3.1 | T `test_a_same_origin_307_is_re_sent_once` (absolute, relative, `:443`, `DELETE`); K `test_a_repository_update_follows_its_307` | example | COVERED |
| AC-3.2 | T `test_a_second_307_ends_as_an_http_error` (`PATCH`, `DELETE`) | example | COVERED |
| AC-4.1 | N `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents`; V `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids`; G `test_no_repos_id_is_pending`; M `test_only_the_residual_ids_are_pending` (restated) | example + contract | COVERED |
| AC-4.2 | K `test_an_asset_is_uploaded_to_its_host` | example | COVERED |
| AC-4.3 | K `test_a_raw_markdown_document_is_rendered` (`capsysbinary`, `sys.stdin` over `\r\n` and `\xff`) | example | COVERED |
| AC-5.1 | C `test_the_usage_names_the_operation_call`, `test_the_usage_names_the_raw_body_input` | example | COVERED |
| AC-5.2 | Inspection of D6's map text; B `test_llm_map_within_cap` | inspection + example | COVERED |
| UB-1.1 | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; K's existing tests; diff of `CASES`, C, P, K | regression | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | static + example | COVERED |
| UB-2.2 | T `test_a_cross_origin_redirect_drops_the_credential`, `test_a_cross_origin_307_is_not_followed` | example | COVERED |
| UB-3.1 | V `test_the_wrapper_imports_only_the_standard_library` | static | COVERED |

16 COVERED, 0 GAP.

Verdict: CLEAN
