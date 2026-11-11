# Evidence report — issue #39: GitLab wrapper rewrite, part 2 slice: the plan records

Tier S, one wave. Branch `issue-39-gitlab-plan-records`, PR #54. It merged the trunk once: e09f2ad took #33 (d30d022), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending key of `plan` has one record, but for the kept set (DL-003) | F `test_only_the_kept_keys_are_pending`; V | red/green wave-1 | green |
| AC-2 names and locations as the section, member query rows included | N `test_every_record_matches_its_reference_section` | green wave-1 | green |
| AC-3 `FILE`, `ARRAY`, `HASH` kinds and `required` as the rows | F `test_the_typed_attributes_are_the_sections` | red/green wave-1 | green |
| AC-4 a GET headed "List" or "Get all" is `Paging.OFFSET` | F `test_every_list_record_has_a_case` | red/green wave-1 | green |
| AC-5 every record is sent as its section documents | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 a list record prints every item of two pages | F `test_a_list_record_prints_every_item` | red/green wave-1 | green |
| UB part-1 records, the two refusals (K's pending-only case restated, DL-004), the credential, the GitHub wrapper untouched | C, K, P; `test_wrapper_delivery.py`; the PR diff | green wave-1 | green |

Green capture, wave 1: 254 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):

- **Targeted mutants:** 14, all killed. They covered the kinds, `required` both ways, paging both ways, the two kept ids given a record, a second endpoint mapped, a member query row dropped, a body row dropped or moved to the query, and K's pending-only case reverted.
- **Wave reverted to the merge base:** the same 58 failures as the red capture.
- **Reference spot-check:** 15 records match their `rest/plan.md` sections field for field.

**Whole suite.** CI run 42977947467 success on e09f2ad.

E2E: the real-instance run is #11's. N runs every declared record through the product's `main` up to the API boundary,
in CI job `verify`.
