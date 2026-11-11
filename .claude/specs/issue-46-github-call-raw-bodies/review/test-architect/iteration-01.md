# Test-architect review — issue #46 design, iteration 01

## Findings

### B1 — The standard-input raw body has no oracle that a re-encoding fails
Severity: B
Location: design.md § Correctness Properties, AC-4.3 (and AC-1.2)
Defect: The only test of `--input -` feeds "the Markdown bytes" unspecified, and H `test_any_bytes_are_sent_as_given`
covers `read_input` with a file path only, so an implementation reading `sys.stdin.read().encode()` instead of D1's
`sys.stdin.buffer.read()` passes every named test whenever the chosen bytes are ASCII with `\n` line ends.
Material-because: AC-1.2 ("none added, removed, re-encoded") is not tested for the standard-input form of the raw body
that D1 defines.
Proposed-edit: In § Correctness Properties, AC-4.3, replace "`sys.stdin` is monkeypatched to a text wrapper over the
Markdown bytes." with "`sys.stdin` is monkeypatched to `io.TextIOWrapper(io.BytesIO(<the Markdown bytes>))`, the
bytes holding a `\r\n` line end and the byte `\xff`, which a read through the text layer translates or fails to
decode."

### C1 — The missing-file case of AC-1.1's refusal test passes before `--input` exists
Severity: C
Location: design.md § Correctness Properties, AC-1.1, K `test_a_raw_body_the_call_cannot_send_is_refused`
Defect: Before implementation, `main`'s `parse_args` answers `--input <missing>` with "unrecognized arguments:
--input …", exit 2 and no request, which already satisfies "argparse's message names `--input`"; the case is green
at the red capture and does not tell D1's `OSError` conversion from an unknown option.
Proposed-edit: Replace "argparse's message names `--input`." with "standard error holds `argument --input:` and the
missing path rendered with `json.dumps`."

### C2 — M's restatement rests on #33's test file, which origin/main does not hold yet
Severity: C
Location: design.md § D4, "The tests that encode the deferral are restated"
Defect: `src/payload/test/test_github_api_markdown.py` is absent at origin/main f374b3d; #33's `change.md` (worktree
`issue-33`, untracked) names `test_only_the_residual_ids_are_pending` (its AC-2) and its UB-2 refuses "an ID no
record declares, AC-2's included", so a #33 case expecting `call markdown/render-raw` to exit 2 would need restating
too, and "Every other test of G and M passes unedited" is unverified for M until the rebase.
Proposed-edit: After "M `test_only_the_residual_ids_are_pending` drops `markdown/render-raw` from its residual set."
add "So is any #33 case that expects `call markdown/render-raw` refused as undeclared (#33 UB-2); M is re-read at the
rebase onto #33."

## Coverage

| Criterion | Test(s) | Kind | Status |
|---|---|---|---|
| AC-1.1 | Inspection D1–D3; K `test_a_raw_body_the_call_cannot_send_is_refused`; T `test_a_cross_origin_307_is_not_followed` | inspection + example | COVERED |
| AC-1.2 | H `test_any_bytes_are_sent_as_given` (`st.binary()`, file form); R `test_send_sends_a_raw_record_to_its_origin`; T `test_a_raw_body_is_sent_unchanged_to_its_root`; K AC-4.2, AC-4.3 tests | property + example | GAP (standard-input form, B1) |
| AC-1.3 | K `test_a_raw_body_with_body_members_is_refused` (`-f`, `-F`; the log oracle tells step 1 from `check_call`) | example | COVERED |
| AC-2.1 | K `test_an_asset_is_uploaded_to_its_host`; N `test_every_record_is_sent_as_its_section_documents`, `test_a_section_is_read_as_the_reference_writes_it` (upload case) | example + contract | COVERED |
| AC-2.2 | K `test_an_asset_is_uploaded_to_its_host` (every request on the upload origin); T `test_a_raw_body_is_sent_unchanged_to_its_root` (third root refused) | example | COVERED |
| AC-3.1 | T `test_a_same_origin_307_is_re_sent_once` (absolute, relative, `:443`, `DELETE`); K `test_a_repository_update_follows_its_307` | example | COVERED |
| AC-3.2 | T `test_a_second_307_ends_as_an_http_error` (`PATCH`, `DELETE`; status 307, exactly two requests) | example | COVERED |
| AC-4.1 | N `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents`; V `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids`; G `test_no_repos_id_is_pending`; M `test_only_the_residual_ids_are_pending` | example + contract | COVERED |
| AC-4.2 | K `test_an_asset_is_uploaded_to_its_host` (non-UTF-8 file body) | example | COVERED |
| AC-4.3 | K `test_a_raw_markdown_document_is_rendered` (`capsysbinary`) | example | COVERED |
| AC-5.1 | C `test_the_usage_names_the_operation_call`, `test_the_usage_names_the_raw_body_input` | example | COVERED |
| AC-5.2 | Inspection of D6's map text (#28 precedent); B `test_llm_map_within_cap` | inspection + example | COVERED |
| UB-1.1 | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; K's existing tests; diff of `CASES`, C, P, K | regression | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | static + example | COVERED |
| UB-2.2 | T `test_a_cross_origin_redirect_drops_the_credential`, `test_a_cross_origin_307_is_not_followed` (four origins; one request) | example | COVERED |
| UB-3.1 | V `test_the_wrapper_imports_only_the_standard_library` | static | COVERED |

15 COVERED, 1 GAP.

Verdict: NOT-CLEAN (0 A, 1 B)
