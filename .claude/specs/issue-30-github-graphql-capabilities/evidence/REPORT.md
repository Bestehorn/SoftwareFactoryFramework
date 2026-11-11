# Evidence report — issue #30: GitHub wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier M, three waves and one rework. Branch `issue-30-github-graphql-capabilities`, PR #56.
- It was rebased onto d30d022 (#33). code-merge-reviewer kept all 21 `GATED_OPERATIONS` entries and both sides of the `commands/call.py` docstring.
- It was then rebased onto 52403f8 (#36), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 every capability row has records whose documents match the reference; mutations have D1's shape | Q `test_every_record_matches_the_reference`; G `test_every_mutation_document_has_the_designed_shape` (rework) | red/green wave-2; rework-1 | green |
| AC-1.2, AC-1.3 every capability has a record; every member a row names is selected | Q; V | red/green wave-2 | green |
| AC-1.4, AC-1.5 one id per record, no index id reused | V `test_a_graphql_record_id_is_its_own` | red/green wave-1 | green |
| AC-2.1..AC-2.4, AC-2.6 `call graphql/<member>` sends the variables, pages connections, prints merge-queue entries, exits 1 on GraphQL errors | G | red/green wave-2 | green |
| AC-2.5 undeclared variables and `--path`/`--query` refused, exit 2, no request | G; R `test_graphql_call_refuses_an_undeclared_variable` (rework) | red/green waves 1, 2; rework-1 | green |
| AC-3.1..AC-3.3 the four refused mutations send nothing; auto-merge names `merge-pr` | G `test_a_refused_mutation_sends_nothing` | red/green wave-2 | green |
| AC-4.1, AC-4.2 usage names every capability and id; the map names `call graphql/` | G, Q | red/green wave-3 | green |
| UB the compatibility cases, fork parity, stdlib only, the GitLab wrapper untouched | C, P, V, K, N, H; `test_wrapper_delivery.py` | every wave | green |

Red captures: wave 1, 6 failed; wave 2, 33 failed; wave 3, 2 failed. Every failure is an assertion or an exception inside a test body.

Green captures:
- Wave 1: 592 passed. Wave 2: 705 passed. Wave 3: 660 passed.
- Rework: 81 passed, after each new test failed under its mutant.
- After the rebase onto 52403f8: 1220 passed. Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.**
- **Round 1:** REFUTED (M2c, M2l), both test gaps (`evidence/verify/refutation-report.md`). The other 22 mutants were killed, the whole-wave reverts reproduced the red captures, and F.2 to F.4 held. DL-008 added the two tests and changed no product file.
- **Round 2:** VERIFIED (`evidence/verify/refutation-report-2.md`). M2c, M2l and nine near-variants were killed, and registry.py's refusal line is now covered.
- **The merge with #46** (5e6ad6f, code-merge-reviewer) kept both sides. Its follow-up c0b697b makes a `graphql/` call refuse `--input` (DL-009, #46 AC-1.3).
- **Round 3:** REFUTED (C3), a test gap (`evidence/verify/refutation-report-3.md`). No test noticed when the both-bodies refusal was removed from the GraphQL path. DL-010 added `test_a_raw_body_beside_a_variable_is_refused_first`.
- **Round 4:** VERIFIED (`evidence/verify/refutation-report-4.md`). C3 and six near-variants were killed.

**Whole suite.** CI run 42998537938 success on 683a86c.

E2E: not applicable. The real-forge check is #10's fixture on an ephemeral `sff-test-*` repository. G runs every call through `main`, and Q proves every document against the reference, in CI job `verify`, leg `tests`.
