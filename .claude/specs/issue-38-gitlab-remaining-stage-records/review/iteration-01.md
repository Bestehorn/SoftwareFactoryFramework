# Review — issue #38 `change.md`, tier S combined pass (all lenses), iteration 01

### B1 — UB-2's "AC-2's included" has no test that can fail
Severity: B
Location: change.md § Tests, rows AC-1 and UB-2
Defect: The UB-2 row cites F's AC-2 test, which only checks `PENDING`, and the AC-1 row does not say its table must
equal the module's records. So a record declared for a kept ID (`agent-foundations#trigger-a-flow`), with its key
left on `PENDING`, passes all of these: F; N, because it matches its section; V, because `coverage_gaps` and
`family_problems` never flag a key that is both mapped and pending; and K, because
`test_an_unknown_operation_is_refused` uses only `plan#` IDs.
Material-because: UB-2 is not protected for AC-2's IDs, and those IDs are the flows and imports that DL-002 keeps out
of `call` because they would get around the merge and filing gates.
Proposed-edit: AC-1 row: "F `test_every_reference_has_its_record` (`{operation_id: (method, path)}` equality); V …";
UB-2 row: "…; F's AC-1 test." in place of "…; F's AC-2 test."

### C1 — "else the first" points to two different endpoints in one section
Severity: C
Location: change.md § AC-1
Defect: In `developer-experience#file-path-branches-and-tags-name`, the first endpoint on the section's line is
`GET /projects/1/repository/files/src%2FREADME.md`. `operations-index.md` lists
`GET /projects/1/branches/my%2Fbranch/commits` first. This is the only several-endpoint section in the slice where
the two orders differ. TEST-3 and IMPL-3 transcribe it independently, so each can pick a different endpoint.
Proposed-edit: "…; of several endpoints, the `/projects/:id/…` one, else the first of its section's line."

### C2 — The secrets residual leaves out a stdout token and two argv values
Severity: C
Location: change.md § Residuals, "In argv"
Defect: Three sections print a runner token to stdout through #41 D3: `tenant-scale#retrieve-a-project`,
`#list-all-personal-projects-for-a-user` and `#list-all-projects-contributions-for-a-user` all document
`runners_token` in their response attributes. Two values go into argv as `-f` text: `import_url` (`create-a-project`,
`create-a-project-for-a-user`, `update-a-project`, `upload-a-project-avatar`), which carries the credentials of a
private source (GitLab, "Migrate through a Git URL"), and `fulfillment#create-a-license`'s `license`. #42's Residuals
do list stdout secrets.
Proposed-edit: "- In argv (#36 DL-003): hook `token`, `signing_token`, importer tokens, `import_url`, `license`,
`configuration[access_token]`; on stdout `runners_token` → ledger." change.md is at its byte cap, so cut as many
bytes elsewhere, for example § Tasks' "(`python scripts/run_tests.py` on F, N)".

### C3 — DL-002 counts 17 kept keys and leaves the new-project importers unstated
Severity: C
Location: decisions/decision-log.md § DL-002
Defect: DL-002 says "the two imports that write into an existing project". AC-2 keeps three such imports besides the
S3 one: `import-project-resources` and the local and remote archives, both of which take `overwrite`. DL-002 also does
not say what happens to the importers that create issues and merge requests in a new project:
`gitlab-dedicated#import-repository-from-github`, `#import-repository-from-bitbucket-server`,
`#import-repository-from-bitbucket-cloud` and `#start-a-group-or-project-migration`. Under DL-002's existing-project
line they get records, while #41 D8's exception row reads "creates an issue". No other section in the 13 pages
merges, writes a branch of an existing project, or creates an issue in one.
Proposed-edit: append a DL entry that supersedes DL-002's enumeration: "the three imports that write into an existing
project (`import-relation`, the `overwrite` archives); importers into a new project stay records (#35's `/clone`
precedent)".

### D1 — The four token keys do not all match the pattern
Severity: D
Location: change.md § AC-2
Defect: Two of the four keys end in `/rotate`, so the pattern `…_access_tokens/:id` does not cover them.
Proposed-edit: "the four `/groups/:id/manage/…_access_tokens/:id…` keys".

## Coverage (tier S, combined)

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_every_reference_has_its_record` (equality, B1); V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | a Reference has no record, or a record carries a key its rows do not |
| AC-2 | F `test_only_the_kept_keys_are_pending` | a module's `PENDING` differs from the kept set |
| AC-3 | N `test_every_record_matches_its_reference_section` | a row is missing, misplaced or misnamed |
| AC-4 | F `test_every_param_is_typed_as_its_row` | a `Kind`, a `required` flag, a body format or `fixed` differs |
| AC-5 | F `test_only_the_list_records_are_paged` | the `OFFSET` set differs, or a `KEYSET` record is present |
| AC-6 | N `test_every_record_is_sent_as_its_section_documents` | a call exits non-zero or sends an undocumented shape |
| AC-7 | F `test_a_list_record_prints_every_page` | the second page is not read, or the output is not one array |
| AC-8 | F `test_a_download_is_written_unchanged` (`capsysbinary`) | the bytes are altered |
| UB-1 | C, unedited | a compatibility argv or exit code changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F AC-1 equality | a gate is dropped, or a kept ID is declared |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | an environment token is read, or a non-stdlib import is added |
| UB-4 | `test_wrapper_delivery.py`; the PR diff | a GitHub file is touched |

No property test is owed: every criterion fixes the values of named records and does not range over an input domain.

NOT-CLEAN (0 A, 1 B)
Verdict: NOT-READY
