# Test-architect review — design, iteration 02 (delta)

Scope: the fix sites of iteration 01's B1, B2 and C1-C4 in `design.md` § Correctness Properties, and the D4 edit of
DL-006.

## Closure of iteration 01

- **B1 (AC-5.1): closed.** The oracle now matches each ID whole: "not followed by a letter, digit or `_`, nor by `.`
  and a letter". Every ID of D1 begins with `graphql#`, so the trailing boundary is the only one needed. The IDs that
  begin with another ID are `graphql#workItemsByReference`, `graphql#workItemCreate`, `graphql#workItemUpdate`,
  `graphql#workItemDelete`, `graphql#workItemExport` and `graphql#workItemsCsvImport`. Each continues
  `graphql#workItem` with a letter, so a docstring without `graphql#workItem` now fails the test.
- **Correction to iteration 01.** The `graphql#Query.vulnerability` example was wrong. That ID ends `…ility` and
  `graphql#Query.vulnerabilities` ends `…ilities`, so neither contains the other, and no ID of D1 other than
  `graphql#workItem` is a prefix of another. The finding stood on `graphql#workItem` alone. `review-latest.md` B2
  repeats the wrong example, but the design does not carry it, so no edit is owed.
- **B2 (AC-5.2): closed.** The `src/payload/scripts/gitlab_api/` bullet of the worktree's `docs/forLLMConsumption.md`
  (read in full) holds `--file` and "a GraphQL record's variables with `-f`/`-F`". It does not hold `call graphql#`,
  `--file NAME=PATH` or `Upload`. So each of the three assertions is red before D8's sentence lands and green after it.
  Scoping the check to the bullet also keeps another bullet's text from satisfying it.
- **C1 (AC-1.3): applied.** The test also fails when the capabilities of `row_members` differ from the table's first
  cells, or when a row has no member.
- **C2 (Q's method): applied.** "Each case is a record ID and a change; the copy is made inside the test."
- **C3 (AC-3.1): applied.** Each of the two files holds a byte that is not UTF-8 and a CRLF.
- **C4 (AC-5.1): applied.** "It fails when `graphql_only.OPERATIONS` holds no record."

## Other edits of this revision

- **DL-006 (D4 takes its multipart body from `transport.request_body`).** `request_body(*, form, json_body, files)`
  in `src/payload/scripts/gitlab_api/transport.py` calls `multipart_body`. That function writes the form parts before
  the file parts and reads each file in `_file_part`, which raises `GitLabAPIError` while the body is still being
  built. Three oracles keep the reason they are red before IMPL: T's part order, T's job-token case (the check comes
  first in `Transport.graphql`), and AC-2.4's missing-file case (no request recorded). No coverage change.
- **spec C1 (a `--file` name outside `upload_variables` gets one `Path` and is refused at step 4).** G
  `test_a_file_for_a_variable_that_is_no_upload_is_refused` (UB-1.2) is its oracle. No coverage change.

No new finding.

## Coverage

| Criterion | Test (red before IMPL because) | Status |
|---|---|---|
| AC-1.1 | design inspection; Q `test_every_record_matches_the_reference` (empty `OPERATIONS`) | COVERED |
| AC-1.2 | Q `test_every_capability_has_a_record` (no record; `PENDING_CAPABILITIES` not empty); V unchanged | COVERED |
| AC-1.3 | Q `test_every_member_a_row_names_is_selected` (no member selected; the row capabilities must equal the table's; a row with no member fails); method case `async: false` | COVERED (C1 applied) |
| AC-1.4 | G `test_every_record_id_is_looked_up_once` (empty `OPERATIONS`) | COVERED |
| AC-2.1 | G `test_a_variable_holds_the_given_json_value`, six JSON kinds (unknown ID, exit 2); G structural | COVERED |
| AC-2.2 | G `test_a_work_item_list_prints_every_node`; G structural; AC-2.4's no-`endCursor` case | COVERED |
| AC-2.3 | G `test_every_record_is_called_through_main` (calls none) | COVERED |
| AC-2.4 | G `test_a_graphql_failure_exits_1_with_its_details`, one case per listed condition (unknown ID or refused `--file`, exit 2) | COVERED |
| AC-2.5 | G `test_every_record_is_called_through_main`, two pages per connection (calls none) | COVERED |
| AC-3.1 | G `test_a_design_upload_sends_each_file_as_a_part`, files with a byte that is not UTF-8 and a CRLF; T `test_graphql_sends_files_as_one_multipart_request` (no `files`); R `upload_variables`, `split_uploads` (absent) | COVERED (C3 applied) |
| AC-3.2 | G two-file case, `map` per item | COVERED |
| AC-4.1 | G `test_a_refused_mutation_sends_nothing` over `REFUSED_IDS`; Q ID-to-root-field check | COVERED |
| AC-4.2 | same G test ("no subcommand sends it", not "which sends it"); K `test_a_gated_operation_names_its_subcommand` | COVERED |
| AC-4.3 | same G test, fails when an ID of `REFUSED_IDS` names no record | COVERED |
| AC-5.1 | G `test_the_usage_names_every_graphql_record` (no `call graphql#` entry; each ID matched whole, so a missing `graphql#workItem` fails; empty `OPERATIONS` fails) | COVERED (B1 closed, C4 applied) |
| AC-5.2 | Q `test_the_map_names_the_graphql_call` (the `gitlab_api/` bullet lacks `call graphql#`, `--file NAME=PATH` and `Upload` today); `test_llm_map_within_cap` | COVERED (B2 closed) |
| UB-1.1 | C unchanged; the diff touches no line of C | COVERED |
| UB-1.2 | K, N, R unchanged; G `test_a_file_for_a_variable_that_is_no_upload_is_refused` | COVERED |
| UB-2.1 | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` | COVERED |
| UB-2.2 | P `test_standard_library_only` (scans every module under the package) | COVERED |
| UB-3.1 | the diff names no GitHub file; the GitHub suites in CI's `tests` leg | COVERED |

CLEAN

Verdict: READY
