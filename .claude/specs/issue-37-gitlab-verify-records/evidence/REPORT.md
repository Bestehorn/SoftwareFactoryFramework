# Evidence report — issue #37: GitLab wrapper rewrite, part 2 slice: the verify records

Tier S, one wave. Branch `issue-37-gitlab-verify-records`, PR #58. It was rebased onto 52403f8 (#36) before the push, with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending key of `verify` has one record, but for DL-003's seven kept keys | F `test_only_the_kept_keys_are_pending`; V | red/green wave-1 | green |
| AC-2 names and locations as the section; member rows get no `Param` | N `test_every_record_matches_its_reference_section` | green wave-1 | green |
| AC-3 kinds and `required` as the rows | F `test_every_param_is_typed_as_its_row` | red/green wave-1 | green |
| AC-4 paging (`list-pipelines` KEYSET, the scopes list NONE, other lists OFFSET) with their paging rows | F `test_only_the_list_records_are_paged` | red/green wave-1 | green |
| AC-5 every record is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 a paged record prints every page | F `test_a_list_record_prints_every_page` (50 cases) | red/green wave-1 | green |
| UB the `pipeline` compatibility cases, the two refusals, the artifacts redirect on the declared record, stdlib only | C, K, P; the PR diff | green wave-1 | green |

Green captures:
- Wave 1: 246 passed. Red was 52 failed.
- After the rebase: 346 passed.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- **Mutants:** 24 were applied, and all 23 that should fail were killed. They covered the kinds, `required` both ways, paging, `PENDING` both ways, a member row given a `Param`, dropped rows, method and path, part 1's four records, and K's redirect case.
- **Whole-wave revert:** it reproduced the red capture's 52 failures.
- **Reference check:** 32 records were spot-checked against `rest/verify.md`.

**Whole suite.** CI run 42984180429 success on a11645b.

E2E: not applicable. The real-instance run is #11's. N runs every record through `main` up to the API boundary in CI job `verify`.
