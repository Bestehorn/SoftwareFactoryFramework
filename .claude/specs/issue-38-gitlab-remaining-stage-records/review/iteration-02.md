# Review — issue #38 `change.md`, tier S combined pass (all lenses), iteration 02 (delta)

No findings. All five iteration-01 findings are closed at their fix sites, and the edits add no defect.

- B1 closed. § Tests AC-1 now requires `OPERATIONS` as `{operation_id: (method, path)}` to equal F's literal table,
  which holds the family's References minus AC-2's. The 13 modules' `OPERATIONS` are empty at 52403f8, so the table is
  exactly AC-1's new records. Declaring a kept ID, for example `agent-foundations#trigger-a-flow`, now fails that
  test. UB-2's row cites it ("F's AC-1 test").
- C1 closed. "The first `/projects/:id/…` one in its section, else the section's first" picks one endpoint in every
  several-endpoint section of the 13 pages. `developer-experience#file-path-branches-and-tags-name` gets
  `GET /projects/1/repository/files/src%2FREADME.md` whether or not the literal `/projects/1/` counts as `:id`. The
  invitations sections get their `/projects/:id/…` endpoint. `fulfillment#delete-an-ldap-group-link-deprecated` gets
  `DELETE /groups/:id/ldap_group_links/:cn`.
- C2 closed. § Residuals "In argv" now has the proposed text word for word, with `runners_token` routed to the ledger
  that IMPL-1 owns.
- C3 closed. DL-005 lists the three existing-project imports plus the S3 import, which matches AC-2's four `gitlab-dedicated#`
  IDs. It gives the four new-project importers records and supersedes only DL-002's import list.
- D1 closed. The pattern `/groups/:id/manage/…_access_tokens/:id…` matches exactly the four `tenant_scale` `PENDING`
  keys: `DELETE …/personal_access_tokens/:id`, `DELETE …/resource_access_tokens/:id` and their two `POST …/:id/rotate`.
  It matches no other index row.
- Caps: change.md is 7,981 B (cap 8,000), and no line is over 120 columns. Every AC and UB still has a Tests row.
  Every test name and helper the rows cite exists: V in `test/test_gitlab_wrapper_coverage.py`, N in
  `test/test_gitlab_wrapper_contract.py`, K in `src/payload/test/test_gitlab_api_call.py`, C in
  `src/payload/test/test_gitlab_wrapper_compat.py`, P in `test/test_gitlab_api_properties.py`.

## Coverage (tier S, combined)

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_every_reference_has_its_record` (`{operation_id: (method, path)}` equality); V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | a Reference has no record or the wrong endpoint, an AC-2 ID is declared, or a record carries a key outside its family |
| AC-2 | F `test_only_the_kept_keys_are_pending` | a module's `PENDING` differs from the kept set |
| AC-3 | N `test_every_record_matches_its_reference_section` | a row is missing, misplaced or misnamed |
| AC-4 | F `test_every_param_is_typed_as_its_row` | a `Kind`, a `required` flag, a body format or `fixed` differs |
| AC-5 | F `test_only_the_list_records_are_paged` | the `OFFSET` set differs, or a `KEYSET` record is present |
| AC-6 | N `test_every_record_is_sent_as_its_section_documents` | a call exits non-zero or sends an undocumented shape |
| AC-7 | F `test_a_list_record_prints_every_page` | the second page is not read, or the output is not one array |
| AC-8 | F `test_a_download_is_written_unchanged` (`capsysbinary`) | the bytes are altered |
| UB-1 | C, unedited | a compatibility argv or exit code changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 test | a gate is dropped, or a kept ID is declared |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | an environment token is read, or a non-stdlib import is added |
| UB-4 | `test_wrapper_delivery.py`; the PR diff | a GitHub file is touched |

No property test is needed. Every criterion fixes the values of named records and does not range over an input domain.

CLEAN
Verdict: READY
