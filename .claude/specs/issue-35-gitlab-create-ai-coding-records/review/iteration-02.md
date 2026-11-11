# Review — issue #35 `change.md`, iteration 02 (tier S, combined: all lenses; delta)

Delta reviewed: AC-4, AC-6, Tests AC-2 and AC-3, the Files list, the Tasks table's Validates, DL-005.

## Disposition of iteration 01

- B1 closed. AC-4 names the four `ai-coding#` IDs `retrieve-merge-request-participants`,
  `retrieve-merge-request-reviewers`, `retrieve-merge-request-dependencies` and `retrieve-blocked-merge-requests`.
  Each one is a `###` heading of `docs/api-reference/gitlab/rest/ai-coding.md`, and `operations-index.md` links to
  each as `rest/ai-coding.md#<id>`. Their GET keys (`…/participants`, `…/reviewers`, `…/blocks`, `…/blockees`) are on
  `families/ai_coding.py` `PENDING`. The rule can be implemented as written. When there is no `Link`, the transport's
  `_next_page_url` sets `page` from `x-next-page`, and it needs no `page` Param to do so. Part 1's
  `ai-coding#list-merge-request-pipelines` is already OFFSET with no Params. N's `paging_parameters` lets a paged
  record leave out `page` and `per_page`. DL-005 supersedes DL-003.
- C1 closed. Tests AC-3 reads "of every non-`SCALAR` or member `Param`", and Tests AC-2 names F
  `test_every_param_is_typed_as_its_row` (members). Both families have `SCALAR` member rows: `not[author_id]` in the
  three new ai-coding merge-request lists (on `PENDING`, not part-1 records), and `range[start]` and `range[end]` in
  create's blame-history section. So the test fails in either family when a member is left out.
- D1 closed. AC-6 reads "a new `Paging.OFFSET` record", which matches Tests AC-6 "one case per AC-4 record".

## New defects

None. Checks made:
- `change.md` is 7,965 B, under its 8,000 B cap. No line is longer than 120 columns.
- Traceability: TEST-1 (create) validates AC-1 to AC-4, AC-6 and AC-7. TEST-2 (ai-coding) validates AC-1 to AC-4
  and AC-6. Each of those criteria has an F line under Tests. AC-2 now has its member case in both families. AC-5 is
  tested by N and carried by the IMPLs. AC-7 applies to create only.
- The Files list names the same three paths that the Tasks table assigns.
- The Residuals no longer repeat DL-001.
- No hedge word was added.

## Coverage (test-architect lens)

Iteration 01's table still holds. Two rows change:

| Criterion | Test | Can fail on the defect |
|---|---|---|
| AC-2 | N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` (members) | yes |
| AC-4 | F `test_only_the_list_records_are_paged` (F's set includes the four named IDs) | yes |

No criterion ranges over an input domain, so no property-based test is owed.

Counts: 0 A, 0 B, 0 C, 0 D.

Verdict: READY
