# Review — issue #35 `change.md`, iteration 01 (tier S, combined: all lenses)

### B1 — AC-4 leaves four paged ai-coding GETs unpaged
Severity: B
Location: change.md § AC-4 (Tests AC-4 and AC-6 follow from it)
Defect: AC-4 makes a record `Paging.OFFSET` only when it is a GET headed "List" or with a `page` row. That makes
`ai-coding#retrieve-merge-request-participants`, `ai-coding#retrieve-merge-request-reviewers`,
`ai-coding#retrieve-merge-request-dependencies` and `ai-coding#retrieve-blocked-merge-requests` `Paging.NONE`: each is
headed "Retrieve" and its table holds only path rows. GitLab pages all four. In gitlab-org/gitlab master (fetched for
this review), `lib/api/merge_requests.rb` presents `paginate(participants)` and `paginate(reviewers)`, and
`ee/lib/api/merge_request_dependencies.rb` presents `paginate(merge_request.blocks_as_blockee)` and
`paginate(blockees)`. `conventions.md` "Pagination" also says that offset pagination "works on every list endpoint
except where a page says otherwise".
Material-because: wrong-behaviour. A `Paging.NONE` record prints the first page (the default `per_page` is 20) as if
it were the whole answer. With no `page` row, D4 refuses `--query page=…`, so no caller can read past that first page.
The issue's AC-1 requires each record's paging to match its operation.
Proposed-edit: AC-4 → "A new record SHALL be `Paging.OFFSET` when it is a `GET` whose heading begins with "List",
whose table has a `page` row, or that is `ai-coding#retrieve-merge-request-participants`, `…-reviewers`,
`…-dependencies` or `ai-coding#retrieve-blocked-merge-requests` (each handler calls `paginate`), else `Paging.NONE`;
none SHALL be `Paging.KEYSET` (opt-in, `conventions.md` "Keyset-based")." Record this in a DL entry that supersedes
DL-003. F's AC-4 set and its AC-6 cases follow from the rule, so no other text changes. The file is 5 B under its
8,000 B cap, so make room by cutting, not adding. D1 saves a few bytes; the Residuals' "(tier M, the issue's Tier
line)" repeats DL-001 and the issue.

### C1 — AC-2's query member Params have no test that fails without them
Severity: C
Location: change.md § Tests, lines AC-2 and AC-3
Defect: N's `record_problems` requires only the rows that have no parent (`Section.attributes`). F's AC-3 table holds
only non-`SCALAR` Params. A record can therefore leave out the `SCALAR` members that AC-2 requires and still pass every
named test. Those members are `not[author_id]`, `not[milestone]` and the rest of the three merge-request lists, and
`range[start]` and `range[end]` of `create#retrieve-file-blame-history-from-a-repository`.
Proposed-edit: in Tests AC-3, replace "of every non-`SCALAR` `Param`" with "of every non-`SCALAR` or member `Param`".
In Tests AC-2, append "; F `test_every_param_is_typed_as_its_row` (members)".

### D1 — AC-6 covers records that its test does not
Severity: D
Location: change.md § AC-6
Defect: "a `Paging.OFFSET` record of either family" includes part 1's `ai-coding#list-merge-request-pipelines`. The
Tests line runs "one case per AC-4 record", and AC-4 covers only new records.
Proposed-edit: "WHEN a `Paging.OFFSET` record of either family is called" → "WHEN a new `Paging.OFFSET` record is
called".

## Coverage (test-architect lens)

| Criterion | Test | Can fail on the defect |
|---|---|---|
| AC-1 | F `test_only_the_kept_keys_are_pending`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | yes |
| AC-2 | N `test_every_record_matches_its_reference_section` | yes, except for the member Params (C1) |
| AC-3 | F `test_every_param_is_typed_as_its_row` | yes |
| AC-4 | F `test_only_the_list_records_are_paged` | yes, once B1 sets the rule |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | yes |
| AC-6 | F `test_a_list_record_prints_every_page` | yes |
| AC-7 | F `test_a_raw_download_is_written_unchanged` (`capsysbinary`) | yes |
| UB-1 | C (existing); PR diff | yes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 tests | yes, by composition: `prepare_call` runs `refuse_gated` and then `registry.lookup` before any send |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | yes |
| UB-4 | `test_wrapper_delivery.py`; PR diff | yes |
| E2E | none applicable: nothing is deployed. N and F run through `main` in `ci.yml` job `verify`, leg `tests`; #11 runs against a real instance | — |

No criterion ranges over an input domain, so no property-based test is owed.

Counts: 0 A, 1 B, 1 C, 1 D.

Verdict: NOT-READY
