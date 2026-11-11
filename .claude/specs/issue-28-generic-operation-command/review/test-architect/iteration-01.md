# Test Architect — design review, iteration 01

### A1 — AC-1.2's header oracle cannot fail, and the LINK path drops the record's `accept`
Severity: A
Location: design.md § Correctness Properties AC-1.2; § D2 "Registry additions"; § D3 "Paging.LINK"
Defect: Every record in `families/*.py` and every record of R's synthetic family (`RecordSpec.build`, `RecordSpec.source`) carries `API_VERSION_DEFAULT` and `ACCEPT_JSON`, which are `Transport.request`'s defaults, so the `X-GitHub-Api-Version`/`Accept` assertion passes for a call that never passes them; and a `Paging.LINK` record goes through `registry.pages` → `Transport.pages`, which takes no `accept` and sends `ACCEPT_JSON` on every page (`Transport._page_items`), so a LINK record with another `accept` is sent with the wrong one, contrary to D2's "the request is therefore exactly AC-1.2's".
Material-because: AC-1.2 ("and the record's `api_version` and `accept`"), stated for every record a family module declares.
Proposed-edit: D2 "Registry additions", add: "`pages` passes the record's `accept` to `Transport.pages`, which gains `accept: str = ACCEPT_JSON` and sends it on every page request." D8 "This change" adds the row "`src/payload/scripts/github_api/transport.py` | `Transport.pages` gains `accept`". Correctness Properties AC-1.2, add: "- Two rows on records replaced for the test with `monkeypatch.setattr` (as D5 step 3) by `dataclasses.replace(record, api_version=API_VERSION_NEXT, accept="application/vnd.github.full+json")`: `issues/get` (`Paging.NONE`) and `issues/list-comments` (`Paging.LINK`, two pages). Oracle: every recorded request carries `X-GitHub-Api-Version: 2026-03-10` and that `Accept`."

### B1 — No call case gives a path value that `registry.expand` changes
Severity: B
Location: design.md § Correctness Properties AC-1.2
Defect: Every path value K and N give (`5`, `x`, `y`, `7`, `acme`, `b1`, N's alphanumeric values, `heads/topic` on the multi-segment `ref`) comes out of `expand` unchanged, so a `send` that fills the template without `quote` (`str.format`) passes every test of the call.
Material-because: AC-1.2 ("each `{name}` replaced by its value as `registry.expand` encodes it").
Proposed-edit: Correctness Properties AC-1.2, add the row: "- `call issues/remove-label --path issue_number=5 --path "name=area/ui"` sends one `DELETE /repos/o/r/issues/5/labels/area%2Fui`; with `--path "name=help wanted"` it sends `…/labels/help%20wanted`."

### B2 — AC-2.2's "each such parameter" has no case with more than one
Severity: B
Location: design.md § Correctness Properties AC-2.2
Defect: Each of the three cases gives exactly one undocumented name, so a check that refuses on the first undocumented name it meets passes, although D4 promises one message naming every undocumented name with its kind.
Material-because: AC-2.2 ("a message naming each such parameter").
Proposed-edit: Correctness Properties AC-2.2, add a fourth case: "`issues/create --field title=T --path number=5 --query sort=created --field color=red`: exit 2, no request, and one log record names `number`, `sort` and `color`, each with its kind."

### B3 — AC-5.3's "another method" has no case
Severity: B
Location: design.md § Correctness Properties AC-5.3; § D6 "AC-5.3"
Defect: The synthetic cases give a record's index row another path but never another method, so `_record_problems` cut down to a path comparison passes `test_a_regenerated_index_names_each_changed_id`.
Material-because: AC-5.3 ("gives a record's operation ID another method or path, … SHALL fail and name that ID").
Proposed-edit: Correctness Properties AC-5.3, after "a record whose index row has another path is named by `_family_problems`" add "- a record whose index row has another method is named by `_family_problems`".

### C1 — AC-1.4's routing oracle does not show the `rel="next"` target was followed
Severity: C
Location: design.md § Correctness Properties AC-1.4
Defect: A `ListRoute` answers any `page`/`per_page` and its next link is the first URL plus `page=2`, so a call that counts pages itself is routed too; "which means the second page was requested by its `rel="next"` target" does not follow (the transport alone is pinned by `test_link_pages_are_followed_as_given`).
Proposed-edit: replace that clause with: "The first page is a static route whose `link` names `https://api.github.com/repositories/1/issues?per_page=2&page=2`, as GitHub names a next page, and a second static route serves that URL, so only a request of the target as given is routed."

### C2 — AC-4.1's oracle omits the JSON-body print form
Severity: C
Location: design.md § Correctness Properties AC-4.1
Defect: The required strings name the list form (`JSON array`) and the non-JSON form (`bytes unchanged`) but no string of the JSON-body form, so D7's "a JSON body as indented JSON" can be dropped with the test green.
Proposed-edit: add `indented JSON` to the strings `test_the_usage_names_the_operation_call` requires.

### C3 — The `is_unreachable` examples do not separate the rule's two arms
Severity: C
Location: design.md § Correctness Properties AC-3.1
Defect: `billing/update-budget-org` is unreachable by its `{org}` path and by its `billing` family at once, so a rule holding either arm alone passes.
Proposed-edit: "`is_unreachable` is true for `billing/update-budget-org`, `orgs/get` (`/orgs/{org}`: the path arm only) and `apps/get-authenticated` (`/app`: the family arm only), and false for `issues/get`."

## Coverage

Design phase: no tasks exist yet, so the column names the design's tests (K, R, N, V, C, P as in the Acceptance Criteria Mapping).

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | design review; N `test_every_record_is_sent_as_its_section_documents` | COVERED |
| AC-1.2 | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` | GAP (A1, B1) |
| AC-1.3 | K `test_any_json_value_becomes_the_body_member` (property), `test_a_body_member_holds_the_given_json_value` | COVERED |
| AC-1.4 | K `test_a_list_prints_every_page_as_one_array` | COVERED (C1) |
| AC-1.5 | K `test_a_json_or_empty_body_prints_as_documented` | COVERED |
| AC-1.6 | K `test_a_body_that_is_not_json_is_written_unchanged` | COVERED |
| AC-1.7 | K `test_an_api_error_exits_1_with_its_details` | COVERED |
| AC-2.1 | K `test_an_unknown_operation_is_refused` | COVERED |
| AC-2.2 | K `test_an_undocumented_parameter_is_refused` | GAP (B2) |
| AC-2.3 | K `test_a_missing_path_parameter_is_refused` | COVERED |
| AC-3.1 | design review; N `is_unreachable` example | COVERED (C3) |
| AC-3.2 | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` | COVERED |
| AC-4.1 | K `test_the_usage_names_the_operation_call` | COVERED (C2) |
| AC-4.2 | design review; `test_llm_map_within_cap` | COVERED |
| AC-5.1 | design review (D6) | COVERED |
| AC-5.2 | design review (D6) | COVERED |
| AC-5.3 | V `test_a_regenerated_index_names_each_changed_id`, `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` | GAP (B3) |
| UB-1.1 | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; PR diff | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | COVERED |
| UB-2.2 | V `test_the_wrapper_imports_only_the_standard_library` | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |

Verdict: NOT-CLEAN (1 A, 3 B) — NOT-TEST-READY (18 COVERED, 3 GAP)
