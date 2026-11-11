# Evidence report — issue #29: GitHub wrapper rewrite, part 2 slice: orgs, teams, users, apps

Tier S, one wave. Branch `issue-29-orgs-teams-users-apps-records`, PR #50, rebased onto the trunk.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending ID has one record; the four `PENDING` empty | F `test_nothing_is_pending`; N; V | red/green wave-1 | green |
| AC-2 `multi_segment` (path `subject_digest` rows), default version and media type, `Paging.LINK` set (bulk-list POSTs `NONE`) | F multi-segment, default and list-set tests | red/green wave-1 | green |
| AC-3 a list record prints every item | F `test_a_list_record_prints_every_item` (incl. a `subject_digest` holding `/`) | red/green wave-1 | green |
| AC-4 every record sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| UB-1 to UB-4 `users/get-authenticated` unchanged, refusals, credential, GitLab untouched | C, P, K, V unedited; `test_wrapper_delivery.py` | green wave-1 | green |

Green capture: 653 passed. After the rebase, 705 passed over the affected suites, including #27's. Product
`run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`). 33 targeted mutants and the wave revert were killed.
They covered `multi_segment`, paging, item keys, the bulk-list POSTs, `PENDING`, body and query names, the path, the
media type and the version. One mutant survived and is equivalent: the default API version written as a literal. The
vacuity scan was clean, and the tables matched an independent count of the reference.

**Whole suite.** CI run 42962058110 success on c007a9f.

E2E: the real-forge run is #10's. By #28 D5 the `teams`, `apps` and `{org}` records are proven by N alone, up to the
API boundary in CI job `verify`.
