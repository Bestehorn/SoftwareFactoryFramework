# Evidence report — issue #42: GitLab wrapper rewrite, part 2 slice: the security records

Tier S, one wave and one rework. Branch `issue-42-gitlab-security-records`, PR #55. It merged the trunk at 041980e (25c91d3, #36 and #39), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending key of the five modules has its record | F `test_every_key_has_its_record` (×5); V | red/green wave-1 | green |
| AC-2 only DL-003's keys stay pending | F `test_only_the_unmapped_keys_are_pending` (×5); V | red/green wave-1 | green |
| AC-3 names and locations as the section; body JSON, `fixed` empty | N `test_every_record_matches_its_reference_section`; F `test_every_body_is_json_and_unfixed` (×5, rework) | green wave-1; rework-1 | green |
| AC-4 kinds and `required` as the rows | F `test_every_kind_is_its_rows_type`, `test_the_required_attributes_are_the_sections` | red/green wave-1 | green |
| AC-5 the list records and DL-005's two NONE exceptions | F `test_every_list_record_has_a_case` | red/green wave-1 | green |
| AC-6 every record is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-7 a list record prints every item | F `test_a_list_record_prints_every_item` | red/green wave-1 | green |
| UB `issue start`/`issue assign` (part 1's two records), the refusals, stdlib only, the GitHub wrapper untouched | C, K, P; the PR diff | green wave-1 | green |

Red captures and green runs:
- Red: 71 failed. Green: 250 passed. Rework: 255 passed, after each new test failed under its mutant.
- After the trunk merge, the GitLab suites gave 430 passed.
- Product `run_checks.py --group lint --group types --group security`: all passed.

**Verifier.**
- **Round 1:** REFUTED (AC-3), a test gap (`evidence/verify/refutation-report.md`). The 46 other mutants were killed and 63 sections were spot-checked. No test checked a record's body or an empty `fixed`. DL-009 added the five tests and changed no product file.
- **Round 2:** VERIFIED (`evidence/verify/refutation-report-2.md`). B1, B3, one mutant per module and three near-variants were killed, and each new test fails on an empty `OPERATIONS`.

**Whole suite.** CI run 42990143891 success on 041980e.

E2E: not applicable. The real-instance run is #11's. N runs every record through `main` up to the API boundary in CI job `verify`.
