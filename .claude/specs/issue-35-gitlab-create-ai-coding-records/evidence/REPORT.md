# Evidence report — issue #35: GitLab wrapper rewrite, part 2 slice: the create and ai-coding records

Tier S, one wave. Branch `issue-35-gitlab-create-ai-coding-records`, PR #59. It was rebased onto 25c91d3 (#39) before the push, with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending key has its record, but DL-002's kept set | F `test_only_the_kept_keys_are_pending` (×2); V | red/green wave-1 | green |
| AC-2 names and locations as the section; query member rows are their own `Param`s | N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` | red/green wave-1 | green |
| AC-3 kinds (blobs `files` ARRAY_OF_HASHES), `required`, body JSON, no `fixed` | F `test_every_param_is_typed_as_its_row` (×2) | red/green wave-1 | green |
| AC-4 paging, DL-005's four "Retrieve" lists included | F `test_only_the_list_records_are_paged` (×2) | red/green wave-1 | green |
| AC-5 every record is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 a new paged record prints every page | F `test_a_list_record_prints_every_page` (36 + 17 cases) | red/green wave-1 | green |
| AC-7 the raw blob's non-UTF-8 bytes are written unchanged | F `test_a_raw_download_is_written_unchanged` | red/green wave-1 | green |
| UB `mr` and `delete-branch`, the two refusals, stdlib only, the GitHub wrapper untouched | C, K, P; the PR diff | green wave-1 | green |

Red captures and green runs:
- Red: 60 failed. Green: 253 passed.
- After the rebase, the GitLab suites gave 414 passed.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- **Mutants:** 37 were killed, together with the whole-wave revert. They covered kinds, `required` (including a `conditional` row), paging including DL-005's lists, `PENDING` both ways with a branch-writing id declared, member rows, part 1's records with the gated merge, and the raw blob.
- **Reference check:** 40 sections were spot-checked across both pages.

**Whole suite.** CI run 42985585816 success on 0e6f27d.

E2E: not applicable. The real-instance run is #11's. N runs every record through `main` up to the API boundary in CI job `verify`.
