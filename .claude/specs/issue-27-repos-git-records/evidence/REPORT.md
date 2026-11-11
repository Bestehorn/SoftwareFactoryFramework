# Evidence report — issue #27: GitHub wrapper rewrite, part 2 slice: repos and git families

Tier S, one wave. Branch `issue-27-repos-git-records`, PR #47, head 99c26c7 before this report.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending id has one record; `git.PENDING` empty, `repos.PENDING` the upload only | F `test_only_the_upload_is_pending`, `test_nothing_is_pending`; V | red/green wave-1 | green |
| AC-2 method, path, query and body names are the section's | N `test_every_record_matches_its_reference_section` | green wave-1 | green |
| AC-3 `multi_segment` the "may contain `/`" path rows; default version and media type | F `test_the_multi_segment_parameters_are_the_sections`, the `/`-holding `ref` cases, `test_every_record_sends_the_default_version_and_media_type` | red/green wave-1 | green |
| AC-4 `Paging.LINK` and `item_key` per the section | F `test_every_list_record_has_a_case` and the AC-6 cases | red/green wave-1 | green |
| AC-5 every record outside the gate is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 a list record prints every item as one array | F `test_a_list_record_prints_every_item` | red/green wave-1 | green |
| AC-7 the seven branch-writing records are refused before any request | F `test_a_branch_writing_record_is_refused` | red/green wave-1 | green |
| UB-1 to UB-4 compatibility, credential, stdlib, GitLab untouched, the existing refusals and `git/delete-ref` | C, P, V, K, `test_wrapper_delivery.py` unedited | green wave-1 | green |

Green capture: 639 passed. Product `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`): 13 targeted mutants killed. They covered `multi_segment`, paging, item keys, the gated set, the `refuse_gated` membership test and its wording, `PENDING`, a body name and the API version. The vacuity scan was clean, red was for the right reason, and the transcription spot-check matched.

**Whole suite.** CI run 42957338836 success on 99c26c7.

E2E: the real-forge run is #10's, on an `sff-test-*` repository. Until then N and F run `call` through the product's
`main` up to the API boundary, in CI job `verify`.
