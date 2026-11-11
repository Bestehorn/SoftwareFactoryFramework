# spec-review-agent — iteration 02 (tier S, combined, DELTA)

Scope: the three fix sites of iteration 01 and their surroundings. The spec directory is untracked, so the delta is
iteration 01's proposed edits compared with change.md § Tests and § Residuals. No other text changed.

## Fix sites

| Finding | Site | Applied | Check |
|---|---|---|---|
| B1 | § Tests, AC-2 | yes, verbatim | Every one of the 970 attribute rows of `rest/no-stage-assigned.md` is typed `string`, `boolean`, `integer`, `number` or `array of strings`. Only two are `array of strings`: `project_keys` of `set-up-jira` and of `set-up-jira-issues`. F's `Kind` table therefore holds two entries. The compared mapping is built from every `Param` of every record not `SCALAR` (`registry.Param.kind` defaults to `Kind.SCALAR`) and must EQUAL that table. A string, boolean, integer or number row declared `HASH`, `ARRAY`, `ARRAY_OF_HASHES` or `FILE` adds an entry, on its own record or on another one, so the test fails. A `project_keys` declared `SCALAR` drops an entry and a `project_keys` declared `HASH` changes the value, so both fail. The required-names table fails the same way in both directions (`Param.required`). The B1 defect is closed. |
| C1 | § Tests, AC-5 | yes, verbatim | `FakeGitLab.script(method, url, …)` queues answers under the exact `(METHOD, url)` key (`gitlab_wrapper_fixtures.py`). K `test_a_list_prints_every_page_as_one_array` asserts the `sent` list and `remaining() == []`, so a wrong `/groups/g%2Fsub/…` or `/projects/<project_id>/…` path fails. |
| D1 | § Residuals, third bullet | yes, verbatim | No section of the page has a `POST` or `PATCH` endpoint, so "every `DELETE` and every `PUT`" covers every writing record. The `GET` records are reads. |

## New defects introduced by the edits

None. The B1 parenthesis names only `RestOperation`/`Param` fields that exist (`kind`, `required`, `body`, `fixed`).
It adds no acceptance criterion and no test file, and it changes the Files and Tasks tables in no way. AC-2 stays the
criterion it validates.

## Caps

change.md is 7,476 B, at or under the 8,000 B cap (`wc -c`). Residuals has 8 lines, at or under 10. Scope is
unchanged: AC-1 to AC-6 and UB-1 to UB-4 are as they were reviewed in iteration 01.

## Coverage (rows changed by the delta)

| Criterion | Test | Fails when |
|---|---|---|
| AC-2 | N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` | a name or `In` differs; any `Param` has a `Kind` other than its row's (`ARRAY` for `array of strings`, `SCALAR` otherwise); `required` differs from the `yes` rows; a non-JSON body or a `fixed` pair |
| AC-5 | F `test_a_list_record_prints_every_page` (two cases, exact-URL scripting) | a page or item is missing; a wrong path is sent; a scripted page goes unserved |

Iteration 01's coverage for AC-1, AC-3, AC-4, AC-6, UB-1 to UB-4 and E2E stands unchanged.

Verdict: READY
