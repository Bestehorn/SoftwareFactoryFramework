# Evidence report — issue #44: GitLab wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier M, three waves and one rework. Branch `issue-44-gitlab-graphql-capabilities`, PR #61. It was rebased onto 5c55448 before the push. It then merged the trunk at 82aa3d9 (7c5b8b9: #30, #35, #42), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1..AC-1.3 every capability row has records whose documents match the reference; mutation shapes as D1 | Q; G `test_every_mutation_document_has_the_designed_shape` (rework) | red/green wave-2; rework-1 | green |
| AC-1.4 one id per record; several records may serve one capability | G `test_every_record_id_is_looked_up_once`; V | red/green wave-2 | green |
| AC-2.1..AC-2.4 variables as given, connections paged as D1, GraphQL failures exit 1 | G (incl. `test_every_paging_record_names_its_designed_connection`, rework) | red/green wave-2; rework-1 | green |
| AC-3.1, AC-3.2 an `Upload` sent as one multipart request; `--file` replaces a same-named field; a non-upload name refused | R, T, G (incl. `test_a_file_replaces_a_field_of_the_same_name`, R `test_upload_variables_leave_out_a_definition_without_a_type`, rework) | red/green waves 1, 2; rework-1 | green |
| AC-4.1..AC-4.3 `workItemCreate` and `workItemsCsvImport` refused, no request, "no subcommand sends it" | G `test_a_refused_mutation_sends_nothing` | red/green wave-2 | green |
| AC-5.1, AC-5.2 usage names every capability, id and the refusal sentence; the map names the call | G (incl. `test_the_usage_says_which_mutations_are_refused`, rework), Q | red/green wave-3; rework-1 | green |
| UB the REST `call`, compatibility, stdlib only, credentials, the GitHub wrapper untouched | K, C, N, P, H; the PR diff | every wave | green |

Red captures and green runs:
- Wave 1: red 6 failed, green 266 passed. Wave 2: red 41 failed, green 320 passed. Wave 3: red 2 failed, green 235 passed.
- Rework: 74 passed, after each new test failed under its mutant.
- After the rebase, 560 passed; after the trunk merge, 607 passed. Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.**
- **Round 1:** REFUTED (M2j, M2k, M2r, M3f, COV), all test gaps (`evidence/verify/refutation-report.md`). The other 37 mutants were killed, and the whole-wave reverts reproduced the red captures. DL-009 added five tests and changed no product file.
- **Round 2:** VERIFIED (`evidence/verify/refutation-report-2.md`). The five mutants and 18 near-variants were killed, and registry.py's uncovered branch is now covered.

**Whole suite.** CI run 43004808641 success on 82aa3d9.

E2E: not applicable. The real-instance run is #11's. G runs every call through `main`, and Q proves every document against the reference, in CI job `verify`, leg `tests`.
