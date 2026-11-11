# Review — issue #14 `change.md`, iteration 01 (tier S, combined: all lenses)

## A — Execution blockers

None.

## B — Intent deviations

None.

## C — Clarifications / risks

### C1 — K's `pending-id` row outlives the last pending ID
Severity: C
Location: change.md § Files; § Tests UB-2
Defect: After AC-1 and AC-3, `call pulls/update-branch` is refused by `refuse_gated`, which `cmd_call` runs before
`registry.lookup`. K's `_unknown_cases` row `pending-id` ("an ID no record declares, pending or not in the index"),
`OP_PULLS_UPDATE_BRANCH`'s comment ("on the PENDING of `families/pulls.py`: indexed, no record") and the docstring of
`test_an_unknown_operation_is_refused` then describe a state no family has (AC-2). The row keeps passing, because its
one pattern is the ID, so it silently becomes a second gate case; "No other file or doc" leaves it that way.
Material-because: none of the five classes — the row passes, and UB-2's unknown-ID refusal stays covered by the
`id-not-in-the-index` row; a stale test label.
Proposed-edit: Files gains the row "`src/payload/test/test_github_api_call.py` (K) | `_unknown_cases`' `pending-id`
row and `OP_PULLS_UPDATE_BRANCH` removed, and the AC-2.1 docstrings of `_unknown_cases` and
`test_an_unknown_operation_is_refused` restated to an ID in no row of the index: AC-2 leaves no pending ID, and AC-3
refuses `pulls/update-branch`"; TEST-1's Files gain K.

### C2 — The `*` record's query case does not pin why it is refused
Severity: C
Location: change.md § Tests UB-3 (`test_the_content_exclusion_call_checks_its_query`)
Defect: The case reads "an undocumented `--query` name exits 2 with no request". Written without `--path org=…`,
`check_call` also refuses it for the missing path parameter (one message), so it still passes when the `*` early
return wrongly skips the query check in `_undocumented`. In Red it passes on the `registry.lookup` refusal.
Material-because: risk — UB-3's query check on the one `*` record is guarded only if the case takes the falsifiable
form the sentence does not require.
Proposed-edit: "F `test_the_content_exclusion_call_checks_its_query` (copilot): `--path org=…`, one `-F` member and
an undocumented `--query` name exit 2 with no request, and `fx.assert_log` finds the query name with its kind."

## D — Minor nits

### D1 — "each recorded-ID set" names a set pulls' F does not have
Severity: D
Location: change.md § Tests AC-1
Defect: `test_github_api_pulls.py` has no recorded-ID set: its transcription test reads every record of `OPERATIONS`,
and its only ID set is `RESIDUAL_IDS`, which AC-2's test replaces. The sets are copilot's `UNPAGED_IDS` and
code_scanning's `RECORDED_IDS`.
Proposed-edit: replace "each recorded-ID set gaining its ID" with "copilot's `UNPAGED_IDS` and code_scanning's
`RECORDED_IDS` gaining their ID; pulls' test reads every record".

### D2 — AC-1's "method, path and path, query and body names"
Severity: D
Location: change.md § Acceptance criteria AC-1
Defect: "whose method, path and path, query and body names are" reads as a doubled word.
Proposed-edit: "whose method and path, and whose path, query and body names, are its `rest/<category>.md`
section's as N reads them".

## Coverage table

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | N `test_every_record_matches_its_reference_section`; V `test_one_module_per_family_holding_only_its_own_ids`; F copilot and pulls `test_the_records_follow_the_transcription_rules`, code_scanning `test_every_record_sends_the_default_version_and_media_type` | a record is missing or its method, path or names differ from the section (N's `first_level_name` reads the copilot body as `{"*"}`); Red: copilot and code_scanning F find no record |
| AC-2 | F `test_nothing_is_pending` (three); V `test_every_operation_is_covered_or_pending` | an ID stays on `PENDING`; Red: each of the three holds one ID |
| AC-3 | F `test_a_branch_writing_record_is_refused` (pulls, code_scanning), #33 AC-6's form | no record (Red); no `None` entry (the call sends a request); a subcommand named instead of "no subcommand sends it" |
| AC-4 | F `test_the_content_exclusion_map_is_sent_as_given`; N `test_every_record_is_sent_as_its_section_documents` | Red: no record, exit 2; `_undocumented` unchanged: `check_call` refuses, exit 2; `_check_names` unchanged: `registry.send` raises `ValueError` past `cmd_call`'s `try`, no exit 0; body not exactly the two members (`NonGetRequest.body`) |
| UB-1 | C `test_a_subcommand_matches_its_golden_case`; P | a compatibility case changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused` (`id-not-in-the-index`); #27's and #33's F refusal tests | a gate entry or the lookup refusal is lost |
| UB-3 | K `test_an_undocumented_parameter_is_refused`, `test_a_missing_path_parameter_is_refused`; R `test_call_refuses_an_undocumented_parameter`; F copilot query case | the `*` return reaches another record's body check or the `*` record's query check (the latter only in C2's form) |
| UB-4 | C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library` | a non-file credential or third-party import |
| UB-5 | `src/payload/test/test_wrapper_delivery.py`; PR diff | either file in the diff |
| E2E | none: no deployed system; F and N run `call` through `main` in `.github/workflows/ci.yml` job `verify`, leg `tests` | — |

Verdict: READY
