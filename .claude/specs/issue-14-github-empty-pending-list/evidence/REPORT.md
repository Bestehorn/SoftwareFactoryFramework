# Evidence report — issue #14: GitHub wrapper rewrite, part 2: the last pending operations

Tier S, one wave and one rework. Branch `issue-14-github-empty-pending-list`, PR #64. After the rework it merged the trunk at 252c21e (#40's GitLab changes), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 one record each for `pulls/update-branch`, `code-scanning/commit-autofix`, `copilot/set-copilot-content-exclusion-for-organization`, with method, path and names per the reference, `item_key` and `content_type` `None` | N, V, F (incl. `test_the_branch_writing_record_has_no_item_key_and_no_content_type`, rework) | red/green wave-1; rework-1 | green |
| AC-2 every GitHub family's `PENDING` empty | F `test_nothing_is_pending`; V | red/green wave-1 | green |
| AC-3 the two branch writers refused by `call` (a `None` gate), exit 2, no request | F `test_a_branch_writing_record_is_refused` (pulls, code_scanning) | red/green wave-1 | green |
| AC-4 a `*` body record sends every member given | F `test_the_content_exclusion_map_is_sent_as_given`; N | red/green wave-1 | green |
| UB-1 compatibility subcommands | C, P | green wave-1 | green |
| UB-2 every other gated or unknown ID refused | K | green wave-1 | green |
| UB-3 undocumented path or query names, and body names of a record without `*`, refused by `call` and `registry.send` | K, R, F (incl. `test_the_registry_refuses_the_content_exclusion_query`, `test_the_content_exclusion_call_checks_its_path`, rework) | green wave-1; rework-1 | green |
| UB-4, UB-5 credentials, standard library only, the GitLab wrapper and delivery tests untouched | C, V, `test_wrapper_delivery.py`; the PR diff | green wave-1 | green |

Red and green runs:
- Wave 1: red 10 failed, 63 passed (all assertions); green 641 passed.
- Rework: 109 passed, after each new test failed under its mutant.
- After the trunk merge, 654 passed. Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.**
- **Round 1:** REFUTED REF-1 (UB-3) and REF-2 (AC-1), both test gaps (`evidence/verify/refutation-report.md`). The other 14 mutants were killed, and the wave revert reproduced the red capture. DL-005 added tests only.
- **Round 2:** VERIFIED (`evidence/verify/refutation-report-2.md`): 9 of 10 delta mutants killed, 1 equivalent.

**Whole suite.** CI run 43035112486 success on 0ffd759.

E2E: not applicable. The real-forge check is #10's. F and N run `call` through `main` against the fake host, in CI job `verify`, leg `tests`.
