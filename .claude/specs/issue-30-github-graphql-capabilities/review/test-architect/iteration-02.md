# Test-architect review — design, iteration 02 (delta)

## Fix sites

| Finding | Fix site | Status | What was checked |
|---|---|---|---|
| A1 | design.md § D6 `document_problems` (connection rule); § Correctness Properties "Q's method" `test_the_method_rejects_a_document_that_differs` | APPLIED | The `after: $after`, `nodes`/`pageInfo` and `$after: String` checks run only on a path that matches the connection. The oracle now reads "at least one problem, and one of them names what differs" (the conductor's Y1 form). Both cases now meet it: `since:` gives the lacking-argument problem naming `since`, and `connection=("repository", "mergeQueue")` gives the path problem. Paired with `test_every_record_matches_the_reference` (empty for every record), a method that over-reports still fails. |
| B1 | § D6 "G" `test_every_record_is_called_through_main` | APPLIED (verbatim) | The exclusion is G's own constant of AC-3.1's four IDs, which `test_a_refused_mutation_sends_nothing` also iterates. A record gated by mistake exits 2 and fails the test. The test fails when it calls no record, so it is red over the empty `OPERATIONS` of the TEST step. |
| B2 | § Correctness Properties AC-4.1 | APPLIED (verbatim) | On `origin/main` (`f374b3d`) the `call issues/get` entry is the docstring's last usage line, and its `#` run ends at the blank line before the `Credentials:` prose. That prose holds none of `-F NAME=JSON`, `input`, `JSON array`, `data`, `exit 2` or `merge-pr` (it says "exits 2"), so the bounded `call graphql/` entry has no match before D7's text is written. |
| C1 | § Correctness Properties AC-2.1 | APPLIED | K `test_a_body_member_holds_the_given_json_value` compares with `json.dumps(obj=..., sort_keys=True)` (`src/payload/test/test_github_api_call.py`). |
| C2 | Q `test_the_reference_is_read_as_written` | APPLIED | Both `selected_members` pins are present, each with a member that must be absent. |
| C3 | R `test_variables_are_the_documents_definitions` | APPLIED | The body uses `$owner`, `$name` and `$after`; `$name :` keeps the white-space case. |
| C4 | AC-2.5, the `-f after=c` case | APPLIED | Under Y3's Glossary a paging record's `$after` is not a declared variable, so the case proves AC-2.5 and D3's refusal together. Its expected `["owner", "name"]` matches what `declared_variables` gives with a `connection`. |
| C5 | Q `test_every_record_matches_the_reference` | APPLIED | "it fails when it finds no record". |
| C6 | AC-4.2; mapping row AC-4.2 | APPLIED | Q `test_the_map_names_the_graphql_call`. `docs/forLLMConsumption.md` on `origin/main` holds no `call graphql/` (`git grep` exit 1), so the test is red before its IMPL; `test_llm_map_within_cap` exists in `test/test_instruction_corpus_budget.py`. |
| D1 | AC-2.5 oracle | APPLIED | "naming each refused name". |

## Other edits of this pass, checked for test defects

- Y4 (§ D6 mutation rule; swapped-document case; AC-3.1 row names Q): the new case is the enable document under the
  `graphql/disablePullRequestAutoMerge` ID, which D1 gives the same `pullRequest { id }` selection. So the case
  fails only by the new ID rule. Every D1 mutation record has the ID `graphql/<m>`, so
  `test_every_record_matches_the_reference` can still pass. The rule forces any record whose document runs a mutation
  of AC-3.1 to carry that mutation's gated ID, so AC-3.1 has a failing test for a swapped document.
- Y2 (§ D4 `ownerId`): AC-1.1 is checked by inspection only, and no oracle changed.
- Y3 (requirements Glossary "Declared variables"): agrees with D3, AC-2.5's third case and R's `connection`
  expectation. G's argv "`-f <name>=v-<name>` for any other variable" now ranges over declared variables, without
  `after`.

## Findings

None.

## Coverage

| Criterion | Test | Fails when | Status |
|---|---|---|---|
| AC-1.1 | design review; Q `test_every_record_matches_the_reference` | a decision is unrecorded; a document differs from the reference | COVERED |
| AC-1.2 | Q `test_every_capability_has_a_record`; V `…covered_or_pending`, `…its_own_ids` | a capability has no record; a capability is not a row; pending is not empty | COVERED |
| AC-1.3 | Q `test_every_member_a_row_names_is_selected` | no record of its row selects a named member | COVERED |
| AC-1.4 | V `test_a_graphql_record_id_is_its_own`, `…its_own_ids` | two records share an ID, or one is an index ID | COVERED |
| AC-1.5 | V's two tests | either reports a problem on the merged tree | COVERED |
| AC-2.1 | G `test_a_variable_holds_the_given_json_value`, `test_every_record_is_called_through_main` | `query` is not the document; a variable is missing or differs by JSON kind | COVERED |
| AC-2.2 | G structural, `test_a_merge_queue_prints_every_entry` | `after` is not `null` then `"c1"`; stdout is not both pages' nodes | COVERED |
| AC-2.3 | G structural | stdout is not `printed_json` of `data` | COVERED |
| AC-2.4 | G `test_a_graphql_failure_exits_1_with_its_details` | exit is not 1; stdout is not empty; no message or `Details:` record | COVERED |
| AC-2.5 | G `test_an_undeclared_variable_is_refused`; R `test_variables_…`, `test_graphql_lookup_…` | a request is sent; exit is not 2; a refused name or the variables are not named | COVERED |
| AC-2.6 | G `test_every_record_is_called_through_main` | a callable record is refused, not called, called wrongly, or no record is called | COVERED |
| AC-3.1 | G `test_a_refused_mutation_sends_nothing`; Q `test_every_record_matches_the_reference` | a request is recorded; exit is not 2; the ID is not named; an ID differs from its document's mutation | COVERED |
| AC-3.2 | G `test_a_refused_mutation_sends_nothing` | `merge-pr`, or "no subcommand sends it", is absent | COVERED |
| AC-3.3 | same | as AC-3.1 and AC-3.2 | COVERED |
| AC-4.1 | G `test_the_usage_names_every_graphql_record` | a capability or ID is missing from the `call graphql/` entry; a print form, `exit 2` or `merge-pr` is missing from it | COVERED |
| AC-4.2 | Q `test_the_map_names_the_graphql_call`; `test_llm_map_within_cap` | the map lacks `call graphql/`, or is over cap | COVERED |
| UB-1.1 | C; P parity tests; PR diff | a golden case's output or exit changes; `CASES`, C or P edited | COVERED |
| UB-1.2 | K; N; R's existing tests | a REST call or refusal changes | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | a file names `environ`/`getenv`; an option takes a token | COVERED |
| UB-2.2 | V `test_the_wrapper_imports_only_the_standard_library` | an import comes from outside the standard library | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | it fails, or the diff names either file | COVERED |

21 COVERED, 0 GAP.

Verdict: CLEAN
