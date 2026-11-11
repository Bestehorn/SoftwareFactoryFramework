# Evidence report — issue #31: GitHub wrapper rewrite, part 2 slice: actions, checks, code-scanning, dependabot, secret-scanning

Tier S, one wave. Branch `issue-31-actions-checks-scanning-records`, PR #51, rebased onto #27's merge f374b3d.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending ID but `code-scanning/commit-autofix` has one record | F `test_nothing_is_pending`, `test_only_the_branch_writing_record_is_pending`; V | red/green wave-1 | green |
| AC-2 method, path, query and body names as the section | N `test_every_record_matches_its_reference_section` | green wave-1 | green |
| AC-3 `multi_segment` (`ref` on two `checks` records), default version and media type | F multi-segment and default tests; the `ref`-holding-`/` case | red/green wave-1 | green |
| AC-4 `Paging.LINK` only with a `Paging:` line; the two `Link`-header objects `NONE` | F `test_every_list_record_has_a_case` | red/green wave-1 | green |
| AC-5 every record sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 a paged record prints both items | F `test_a_list_record_prints_every_item` | red/green wave-1 | green |
| UB the six existing records, `commands/ci.py`, `get-pr-checks`, credential, GitLab untouched | C, P, K, V unedited; `test_wrapper_delivery.py` | green wave-1 | green |

Green capture: 646 passed. After the rebase, 697 passed over the affected suites, including #27's. Product
`run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`): 14 mutants killed. They covered the whole wave,
item keys, a `Link`-header object set to `LINK`, `multi_segment`, `commit-autofix` declared or unpended, paging,
body names and a method. The vacuity scan was clean and red was for the right reason.

**Whole suite.** CI run 42964120783 success on 85f9f8f.

E2E: the real-forge run is #10's. N runs `call` through the product's `main` up to the API boundary in CI job
`verify`.
