# Test Architect — design review, iteration 02 (delta)

Scope: the fix sites of iteration-01 A1, B1–B3 and C1–C3, plus the test coverage of the text X1–X4 and DL-004 changed
(`GATED_OPERATIONS`, `query_name`, H moved to `test/`, the `issues/create` → `issues/update` examples).

## Fix sites

| Finding | Fix site | Status | Evidence |
|---|---|---|---|
| A1 | D2 "Registry additions" (`pages` passes `accept`; `Transport.pages` gains `accept`); D8 `transport.py` row; Correctness Properties AC-1.2, the two copied-record rows and the oracle on every recorded request | APPLIED | `transport.py` defines `API_VERSION_NEXT = "2026-03-10"`; `registry.lookup` reads `module.OPERATIONS` on each call through `discover_families`, so `monkeypatch.setattr` takes effect; `RecordedRequest.headers` holds the sent headers; `Transport._page_items` sends `ACCEPT_JSON` today, so the paged row stays red until D2's fix lands |
| B1 | AC-1.2 `issues/remove-label` row (`area%2Fui`, `help%20wanted`) | APPLIED | the record's `multi_segment` is empty, so `_encode_path_value` quotes with `safe=""`; a fill without `quote` sends `area/ui` and fails the row |
| B2 | AC-2.2 fourth case (`number`, `sort`, `color` in one call, each with its kind) | APPLIED | `issues/update` documents path `owner`/`repo`/`issue_number`, no query, and no body `color`; a check that stops at the first name fails the case |
| B3 | AC-5.3 "another method, and the same path" case | APPLIED | `_record_problems` compares `(record.method, record.path)` with the index row, so a path-only comparison fails the case |
| C1 | AC-1.4 first bullet (page 2 at `/repositories/1/issues?per_page=2&page=2`) | APPLIED | `Route.matches` compares method, endpoint and decoded query exactly, and `_target_of` takes an absolute URL, so a request that builds page 2 itself goes unrouted |
| C2 | AC-4.1 strings gain `indented JSON` | APPLIED | D7's usage lines hold "a JSON body as indented JSON"; `JSON array`, `bytes unchanged` and `exit 2` each sit on one line |
| C3 | AC-3.1 example (`orgs/get`, `apps/get-authenticated`) | APPLIED | `rest/orgs.md` `GET /orgs/{org}` (path arm only); `rest/apps.md` `GET /app` (family arm only) |

Changed text that needs no finding:
- The DL-004 examples on `issues/update` (AC-1.2, AC-1.3, AC-2.2) use the names its record documents (`title`,
  `labels`) where a case is sent, and names it does not document (`number`, `sort`, `color`) where a case is refused.
- The `state[]` row fails if either D4's check or `_check_names` skips `query_name`. Either way no request is sent:
  the call is refused, or a `ValueError` is raised outside `cmd_call`'s catch.
- K `test_a_gated_operation_names_its_subcommand` gives `pulls/merge` its `pull_number` and `issues/create` the
  documented `title`. So D4's checks pass, and only the gated refusal can make either exit 2 with no request.
- H moved to `test/`, where it still runs in CI's `tests` leg, as V does.
- DL-004 catches the refusal in `cmd_call` and logs it with `logger.error`, so K's `caplog` oracle still reads it. If
  a build left out D4's check, the `ValueError` from `registry` would leave `main` without a `SystemExit`, and the
  refusal cases would fail.

## Findings

### C4 — The gated test's oracle passes a swapped subcommand
Severity: C
Location: design.md § Correctness Properties AC-1.1 (K `test_a_gated_operation_names_its_subcommand`)
Defect: "The log record names `merge-pr` or `create-issue`" is also true when `GATED_OPERATIONS` maps both IDs to one
subcommand. D4's row "the ID and the subcommand to use" can then be wrong while the test passes. The no-request
oracle is unaffected.
Proposed-edit: replace "and the log record names `merge-pr` or `create-issue`" with "and the log record of the first
names `pulls/merge` and `merge-pr`, that of the second `issues/create` and `create-issue`".

### C5 — "Set into" `OPERATIONS` does not say that the copy replaces the original
Severity: C
Location: design.md § Correctness Properties AC-1.2 (the two copied-record rows)
Defect: A copy added beside the original makes `registry.lookup` raise "is declared 2 times", so the row exits 2. It
fails loudly instead of passing, which is why this is graded C.
Proposed-edit: "…set into `github_api.families.issues.OPERATIONS` in place of the original record, with
`monkeypatch.setattr` for the test."

## Coverage

Design phase: the column names the design's tests (K, R, H, N, V, C, P as in the Acceptance Criteria Mapping).

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` | COVERED (C4) |
| AC-1.2 | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` | COVERED (C5) |
| AC-1.3 | H `test_any_json_value_becomes_the_body_member` (property); K `test_a_body_member_holds_the_given_json_value` | COVERED |
| AC-1.4 | K `test_a_list_prints_every_page_as_one_array` | COVERED |
| AC-1.5 | K `test_a_json_or_empty_body_prints_as_documented` | COVERED |
| AC-1.6 | K `test_a_body_that_is_not_json_is_written_unchanged` | COVERED |
| AC-1.7 | K `test_an_api_error_exits_1_with_its_details` | COVERED |
| AC-2.1 | K `test_an_unknown_operation_is_refused` | COVERED |
| AC-2.2 | K `test_an_undocumented_parameter_is_refused` | COVERED |
| AC-2.3 | K `test_a_missing_path_parameter_is_refused` | COVERED |
| AC-3.1 | design review; N `is_unreachable` example | COVERED |
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` | COVERED |
| AC-4.1 | C `test_the_usage_names_the_operation_call` | COVERED |
| AC-4.2 | design review; `test_llm_map_within_cap` | COVERED |
| AC-5.1 | design review (D6) | COVERED |
| AC-5.2 | design review (D6) | COVERED |
| AC-5.3 | V `test_a_regenerated_index_names_each_changed_id`, `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` | COVERED |
| UB-1.1 | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; PR diff | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | COVERED |
| UB-2.2 | V `test_the_wrapper_imports_only_the_standard_library` | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |

Verdict: CLEAN (0 A, 0 B) — TEST-READY (21 COVERED, 0 GAP)
