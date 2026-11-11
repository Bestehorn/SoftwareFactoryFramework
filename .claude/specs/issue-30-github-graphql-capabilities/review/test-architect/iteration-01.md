# Test-architect review — design, iteration 01

## Findings

### A1 — Two of Q's falsification cases cannot give exactly one problem under D6's own rules
Severity: A
Location: design.md § Correctness Properties "Q's method" `test_the_method_rejects_a_document_that_differs`; § D6 `document_problems`
Defect: D6 names "an argument that the field lacks" and "a last field without `after: $after`" as separate problems, and `Repository.discussions` has no `since` argument (`objects-p-w.md`, `Repository` table), so the `since:` case meets both; `connection=("repository", "mergeQueue")` meets the path rule and, at `mergeQueue` (no `after:`, no `nodes`/`pageInfo`), the two other connection rules — yet the property demands exactly one problem per case.
Material-because: wrong-behaviour — a `document_problems` built as D6 states turns the test red, so Q (D6's proof of the unreachable records, AC-1.1; the walk AC-1.3 rests on) cannot be written as specified without relaxing an assertion.
Proposed-edit: in D6 replace "for a record with a connection: a path of selected fields that differs from it; a last field without `after: $after`; a selection without both `nodes` and `pageInfo { hasNextPage endCursor }`; a `$after` that is not declared `String`;" with "for a record with a connection: a path of selected fields that differs from it; and, only on a path that matches it, a last field without `after: $after`, a selection without both `nodes` and `pageInfo { hasNextPage endCursor }`, or a `$after` that is not declared `String`;". In the property replace "Each case gives exactly one problem, naming what differs:" with "Each case gives exactly one problem, naming what differs, but the `since:` case, which gives two: `since` is no argument of `Repository.discussions`, and `discussions` has no `after: $after`:".

### B1 — G's structural call test takes its exclusions from the code under test and passes on an empty module
Severity: B
Location: design.md § D6 "G" `test_every_record_is_called_through_main`; § Correctness Properties AC-2.6
Defect: the test leaves out every record in `GATED_OPERATIONS`, the product table it should judge, so a record gated by mistake (`graphql/deleteProjectV2`, say) exits 2 and no test fails; over an empty `OPERATIONS` (the TEST step) it calls nothing, and as a parametrize it is collected as skipped (`pyproject.toml` sets no `empty_parameter_set_mark`).
Material-because: AC-2.6 and AC-2.1 — a record outside AC-3.1 that the wrapper refuses has no failing test, and the test cannot be red before its IMPL task.
Proposed-edit: replace "covers each record of `graphql_only.OPERATIONS` outside `GATED_OPERATIONS`." with "covers each record of `graphql_only.OPERATIONS` whose ID is not one of AC-3.1's four, which G holds as a constant that `test_a_refused_mutation_sends_nothing` also iterates; it fails when it calls no record."

### B2 — Three of AC-4.1's oracle strings are already in the docstring
Severity: B
Location: design.md § Correctness Properties AC-4.1 `test_the_usage_names_every_graphql_record`
Defect: the trunk's entry-script docstring (`origin/main`: the `call issues/get` entry, the `merge-pr` usage line) already holds `JSON array`, `exit 2` and `merge-pr`, so the assertions for how a connection prints and that AC-3.1's mutations exit 2 pass with no GraphQL text written.
Material-because: AC-4.1 — a docstring that omits both passes the test.
Proposed-edit: replace "The entry script's `__doc__` holds:" with "The GraphQL entry of the entry script's `__doc__` (its `call graphql/` usage line and the `#` lines under it, up to the next usage line) holds:".

## C and D

- C1 — § Correctness Properties AC-2.1: `test_a_variable_holds_the_given_json_value` compares by Python equality, where `True == 1`. Edit: append "compared by `json.dumps(sort_keys=True)`, as K's `test_a_body_member_holds_the_given_json_value` compares".
- C2 — § Correctness Properties AC-1.3: the verdict rests on `selected_members`, which no example pins; a walk that over-reports passes. Edit: add to `test_the_reference_is_read_as_written` "`selected_members` of `graphql/pinIssue` holds `pinIssue` and not `unpinIssue`; that of `graphql/Repository.discussions` holds `Repository.discussions` and not `Repository.discussionCategories`".
- C3 — § Correctness Properties AC-2.5, R `test_variables_are_the_documents_definitions`: the body `{ … }` uses no variable, so a reader that collects every `$name` passes. Edit: replace `{ … }` with `{ repository(owner: $owner, name: $name) { discussions(first: 100, after: $after) { … } } }`.
- C4 — § Correctness Properties AC-2.5, case `… -f after=c`: `$after` is a declared variable (requirements Glossary), so the case proves D3's refusal (DL-004), not AC-2.5. Edit: append "(D3, DL-004: declared, but set by the transport)".
- C5 — § Correctness Properties `test_every_record_matches_the_reference`: vacuous over an empty `OPERATIONS`. Edit: append "it fails when it finds no record".
- C6 — § Correctness Properties AC-4.2: the map clause has inspection only. Edit: "Static, Q `test_the_map_names_the_graphql_call`: `docs/forLLMConsumption.md` holds `call graphql/`; `test_llm_map_within_cap` passes."
- D1 — § Correctness Properties AC-2.5: "naming each name given" → "naming each refused name".

## Coverage

| Criterion | Test | Fails when | Status |
|---|---|---|---|
| AC-1.1 | design review; Q `test_every_record_matches_the_reference` | a decision is unrecorded; a document differs from the reference | COVERED (A1) |
| AC-1.2 | Q `test_every_capability_has_a_record`; V `…covered_or_pending`, `…its_own_ids` | a capability has no record; a capability is no row; pending not empty | COVERED |
| AC-1.3 | Q `test_every_member_a_row_names_is_selected` | a named member is selected by no record of its row | COVERED (C2) |
| AC-1.4 | V `test_a_graphql_record_id_is_its_own`, `…its_own_ids` | two records share an ID, or one is an index ID | COVERED |
| AC-1.5 | V's two tests | either reports a problem on the merged tree | COVERED |
| AC-2.1 | G `test_a_variable_holds_the_given_json_value`, structural | `query` is not the document; a variable is missing or differs | COVERED (C1) |
| AC-2.2 | G structural, `test_a_merge_queue_prints_every_entry` | `after` not `null` then `"c1"`; stdout not both pages' nodes | COVERED |
| AC-2.3 | G structural | stdout is not `printed_json` of `data` | COVERED |
| AC-2.4 | G `test_a_graphql_failure_exits_1_with_its_details` | exit not 1; stdout not empty; no message or `Details:` record | COVERED |
| AC-2.5 | G `test_an_undeclared_variable_is_refused`; R `test_variables_…`, `test_graphql_lookup_…` | a request is sent; exit not 2; the name or the variables unnamed | COVERED (C3, C4) |
| AC-2.6 | G `test_every_record_is_called_through_main` | a callable record is not called, or called wrongly | GAP (B1) |
| AC-3.1 | G `test_a_refused_mutation_sends_nothing` | a request is recorded; exit not 2; the ID unnamed | COVERED |
| AC-3.2 | same | `merge-pr` or the trunk's "no subcommand sends it" absent | COVERED |
| AC-3.3 | same | as AC-3.1 and AC-3.2 | COVERED |
| AC-4.1 | G `test_the_usage_names_every_graphql_record` | a capability or ID missing; print forms, exit 2 unpinned | GAP (B2) |
| AC-4.2 | inspection; `test_llm_map_within_cap` | the map is over cap; the call unnamed (inspection) | COVERED (C6) |
| UB-1.1 | C; P parity tests; PR diff | a golden case's output or exit changes; `CASES`, C or P edited | COVERED |
| UB-1.2 | K; N; R's existing tests | a REST call or refusal changes | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | a file names `environ`/`getenv`; an option takes a token | COVERED |
| UB-2.2 | V `test_the_wrapper_imports_only_the_standard_library` | an import outside the standard library | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | it fails, or the diff names either file | COVERED |

Verdict: NOT-CLEAN (1 A, 2 B)
