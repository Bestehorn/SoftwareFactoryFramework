# Evidence report — issue #36: GitLab wrapper rewrite, part 2 slice: the no-stage-assigned records

Tier S, one wave. Branch `issue-36-gitlab-no-stage-records`, PR #53. It merged the trunk once: f97ca06 took #33 (d30d022), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending key of `no_stage_assigned` has one record; `PENDING` empty | F `test_nothing_is_pending`; V | red/green wave-1 | green |
| AC-2 one `Param` per row, typed and required as the row | N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` | red/green wave-1 | green |
| AC-3 only the two list records are `Paging.OFFSET` | F `test_only_the_list_records_are_paged` | red/green wave-1 | green |
| AC-4 every record is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-5 a list record prints every page | F `test_a_list_record_prints_every_page` | red/green wave-1 | green |
| AC-6 a settings write sends its typed JSON body | F `test_a_settings_write_sends_its_typed_body` | red/green wave-1 | green |
| UB compatibility, the two refusals, the credential, the GitHub wrapper untouched | C, K, P; `test_wrapper_delivery.py`; the PR diff | green wave-1 | green |

Green capture, wave 1: 196 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):

- **Targeted mutants:** 13, all killed. They covered kinds, `required`, paging both ways, `PENDING`, a dropped body name, the `:id` encoding of a nested group path, the GCP `integration/` path, `fixed` pairs, a `Param` on a section that has no table, and a FORM body.
- **Wave reverted to the merge base:** the same 6 failures as the red capture.
- **Reference spot-check:** 14 sections of `rest/no-stage-assigned.md` match their records.

**Whole suite.** CI run 42977407373 success on f97ca06.

E2E: the real-instance run is #11's. N runs every declared record through the product's `main` up to the API boundary,
in CI job `verify`.
