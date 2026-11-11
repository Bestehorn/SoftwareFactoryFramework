# Spec review — issue #37, combined tier-S pass, iteration 01

### C1 — AC-1's "the first" endpoint has two readings
Severity: C
Location: change.md § Acceptance criteria AC-1
Defect: "every endpoint but the first of …" names no order. `operations-index.md` lists `GET /groups/:id/runners/all`
before `GET /groups/:id/runners`, and `…/permalink/latest/downloads/bin/asset.exe` first of the three
`get-the-latest-release` rows. The sections' endpoint lines (`rest/verify.md` "List all of a group's runners", "Get the
latest release") put `GET /groups/:id/runners` and `GET /projects/:id/releases/permalink/latest` first. Both readings
pass N and V, so only F's literal set decides, and the index reading records the docs-example path `…/bin/asset.exe`.
Proposed-edit: "every endpoint but the first of" → "every endpoint but its section's first of".

### C2 — F's AC-1 test sentence has no verb, and "kept IDs" can name six IDs
Severity: C
Location: change.md § Tests AC-1
Defect: "the `OPERATIONS` IDs F's tuple …" lacks its verb. "AC-1's kept IDs" can also be read as all six IDs AC-1
names, but AC-1 requires records for three of them (`metadata-api-1`, `get-the-latest-release`,
`list-all-of-a-groups-runners`).
Proposed-edit: "the `OPERATIONS` IDs F's tuple of the family's index References but AC-1's kept IDs" → "the
`OPERATIONS` IDs equal F's tuple of the family's index References but AC-1's first three IDs".

### C3 — change.md does not say the narrowed "PENDING empty" item is deferred on #37
Severity: C
Location: change.md § Residuals, first bullet
Defect: The issue's AC-2 ("`verify.PENDING` SHALL be empty") is narrowed for the two glob routes and the merge-train
key. Those are exactly the keys #41 assigns to this slice: its requirements Residuals say request forms "stay with the
slice whose family needs one", and its design Residuals say a merging record "is gated by its slice". DL-001 also
names a missing request form as the re-tier trigger, and DL-002 does not take it. Nothing is lost, because #15's open
work item "Empty part 1's pending list in the coverage test (AC-3)" still tracks the remainder. But only DL-003 says
the deferral is recorded on #37. change.md does not, although #39's and #42's Residuals do (`issue-tracking.md`
"Closing").
Proposed-edit: "- Kept pending (DL-003) →" → "- Kept pending (DL-003; deferral noted on #37) →". Whether DL-002 owes a
superseding entry for DL-001's trigger is the decision log's writer's call.

### C4 — AC-2's paging rows are untested
Severity: C
Location: change.md § Tests AC-2, AC-4
Defect: AC-2 requires every query row, but N's `param_problems` and `record_problems` skip `PAGING_PARAMETERS` on a
paged record (`test/test_gitlab_wrapper_contract.py` `paging_parameters`). F's AC-3 tables cover only non-`SCALAR`
kinds and required names, and F's AC-6 cases give no `per_page`. So a list record that leaves out `page`/`per_page`
(or `order_by`/`sort` on `verify#list-pipelines`) passes N, V and F. `call … --query per_page=5` is then refused with
exit 2 (`commands/call.py` `undocumented`), whereas part 1's `verify#list-project-pipelines` declares both.
Proposed-edit: Tests AC-4 "`{operation_id: Paging}` of the records not `NONE` equals F's table." → "`{operation_id:
(Paging, paging rows declared)}` of the records not `NONE` equals F's table."

### D1 — K's constant stays under the synthetic-records comment; UB-2 repeats the K row
Severity: D
Location: change.md § Files (K row); § Unchanged behaviour UB-2
Defect: After the K row's removals, `OP_DOWNLOAD_ARTIFACTS` still sits under K's comment "The synthetic records …, each
set into a module's OPERATIONS for one test" (`src/payload/test/test_gitlab_api_call.py`), which no longer describes
it. UB-2's last sentence says what the K row already says.
Proposed-edit: K row "`VERIFY` removed" → "`VERIFY` removed; `OP_DOWNLOAD_ARTIFACTS` leaves the synthetic IDs"; in
UB-2 delete "; K's `artifacts-after-a-redirect` case calls the declared record", leaving "(#41 D3).".

### D2 — byte headroom for the edits above
Severity: D
Location: change.md § Tests E2E
Defect: change.md is at 7,948 B, so the edits above need room. The E2E line's workflow path repeats #41's Testing
Strategy "Runner" item.
Proposed-edit: "in CI (`.github/workflows/ci.yml` job `verify`)." → "in CI job `verify`." Measured: with every edit in
this file applied, change.md is 7,976 B before re-wrapping.

## Coverage (combined pass)

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_only_the_kept_keys_are_pending` (literal key set, literal ID tuple); V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | a key is unmapped, pending wrongly, or recorded under a foreign Reference |
| AC-2 | N `test_every_record_matches_its_reference_section` | a method, path, `Param` name or location differs, or a non-paging row is missing (paging rows: C4) |
| AC-3 | F `test_every_param_is_typed_as_its_row` (literal kind and required tables) | a Type maps to the wrong `Kind`, `required` is not the Required column, or a body is not JSON or has `fixed` |
| AC-4 | F `test_only_the_list_records_are_paged` (literal table) | a "List" `GET` is `NONE`, `list-pipelines` is not `KEYSET`, or the scopes list is paged |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | a call exits non-zero, sends anything but one request, or its method, path, query or body names differ |
| AC-6 | F `test_a_list_record_prints_every_page`, one case per paged ID | a second page is not requested at its URL, an answer is left unserved, or stdout is not one `print_json` array |
| UB-1 | C, every existing case unedited; PR diff | a `pipeline` argv, output or exit code changes, or a part-1 record changes |
| UB-2 | K `test_a_body_that_is_not_json_is_written_unchanged` (redirect case on the declared record) | bytes are altered, or the storage origin receives a credential |
| UB-3 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F AC-1 test; diff | a gated ID is sent, or the merge-train ID gets a record |
| UB-4 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | a credential source or a non-standard-library import is added |
| UB-5 | `test_wrapper_delivery.py`; PR diff | a UB-5 file is touched |
| E2E | none deployable; #11's real-instance run; N and F through `main` in CI | — |

No property-based test is owed: AC-1 to AC-4 fix literal values, and AC-5 and AC-6 run over a finite declared set that
N and F enumerate completely.

Verdict: READY
