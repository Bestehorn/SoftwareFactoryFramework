# Evidence report — issue #41: GitLab wrapper rewrite, part 2a (generic operation command)

Tier M, four waves plus one verification rework. Branch `issue-41-gitlab-generic-operation-command`, PR #49, rebased
onto #27's merge f374b3d.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 a declared record is a documented call; the merge-request merge and issue-creation records name their subcommands | K; N `test_every_record_is_sent_as_its_section_documents` | red/green wave-2 | green |
| AC-1.2, AC-1.3 the call sends path, query and attributes of their kinds; `-F` refuses `NaN`/`Infinity` without its value | R, T (wave 1); K; H `test/test_gitlab_api_call_properties.py` | wave-1, wave-2 | green |
| AC-1.4–AC-1.7 pages as one array, JSON indented, an empty body prints nothing (incl. under a JSON content type), other bodies unchanged, API errors exit 1 with details | K (rework DL-005) | wave-2; green/rework-1 | green |
| AC-1.8, AC-1.9 the configured project; GraphQL variables | K | wave-2 | green |
| AC-2.1–AC-2.4 unknown operation, undocumented or missing parameter, wrong shape, malformed `NAME=VALUE` refused with exit 2 before any request | K (rework: `test_a_malformed_argument_is_refused_without_its_value`) | wave-2; green/rework-1 | green |
| AC-3.1, AC-3.2 the unreachable rule and the contract-test proof | N | wave-2 | green |
| AC-4.1 the usage names the call; AC-4.2 the map | C `test_the_usage_names_the_operation_call`; map by inspection + `test_llm_map_within_cap` | red/green wave-4 | green |
| AC-5.x the target pin and regeneration; AC-6.x the coverage rule incl. GraphQL-only capabilities | V (named mutant for red) | red/green wave-3 | green |
| UB-1.1, UB-2.x, UB-3.1 compatibility, credential, standard library, GitHub untouched | C, P, V unchanged lines; F.2/F.3 diff checks | waves 2–4; verify | green |

Green captures: wave 1 had 197 passed, wave 2 had 175, wave 3 had 173 and wave 4 had 219. After the rebase, 383
passed over the affected suites. Rework 1 had 164 passed. Product
`run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.**
- First pass: 43 of 44 mutants killed. It REFUTED AC-1.5 (the empty-body check removed survived) and Requirement 2 /
  D4 row 1 (`_split`'s two refusals never ran), in `evidence/verify/refutation-report.md`.
- Rework DL-005 added the two empty-body rows and the six-case malformed-argument test.
- The re-verification killed all three mutants and measured `call.py` at 100% line coverage under K. Verdict:
  VERIFIED (`evidence/verify/refutation-report-2.md`).
- F.2 to F.4 held.

**Whole suite.** CI run 42961275618 success on ca4e2d7; CI run 42966169391 success on 2e96a8d (the rework head).

E2E: the real-instance run is #11's, on an ephemeral `sff-test-*` project. Until then K and N run `call` through the
product's `main` up to the API boundary, in CI job `verify`.
