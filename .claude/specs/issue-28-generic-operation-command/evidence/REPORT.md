# Evidence report — issue #28: GitHub wrapper rewrite, part 2a (generic operation command)

Tier M, four waves plus one verification rework. Branch `issue-28-generic-operation-command`, PR #45 (rebased on #13's
merge 2eb1c9e, DL-007).

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 a declared record is a documented call; the gated operations name their subcommand | K `test_github_api_call.py`; N `test/test_github_wrapper_contract.py` (every record sent as its section documents) | red/green wave-2 | green |
| AC-1.2 the call sends method, path, query, body, `api_version`, `accept`; `[]` names as written; parse refusals | R, T (wave 1); K; rework K `test_a_malformed_argument_is_refused_without_its_value` | wave-1, wave-2; green/rework-1.txt | green |
| AC-1.3 `-F` values are typed JSON; `NaN`/`Infinity` and non-JSON refused | K; H `test/test_github_api_call_properties.py`; rework K | wave-2; rework-1 | green |
| AC-1.4–AC-1.7 pages as one array, JSON indented, empty prints nothing, other bodies unchanged, API error exit 1 | K | wave-2 | green |
| AC-2.1–AC-2.3 unknown operation, undocumented or missing parameter refused with exit 2 before any request | K; R | wave-1, wave-2 | green |
| AC-3.1, AC-3.2 unreachable rule and the contract-test proof method | N | wave-2 | green |
| AC-4.1 the usage names `call`; AC-4.2 the map | C `test_the_usage_names_the_operation_call`; map by inspection + `test_llm_map_within_cap` | wave-4 | green |
| AC-5.1, AC-5.2 target pin `2f8f80e` and the regeneration table | design D6 (approved) | — | met |
| AC-5.3 a regenerated index names each changed id | V `test_a_regenerated_index_names_each_changed_id` | red (named mutant) / green wave-3 | green |
| UB-1.1, UB-2.1, UB-2.2, UB-3.1 compatibility, credential, stdlib, GitLab untouched | C, P, V unchanged; F.2/F.3 diff checks | wave-2, wave-4; verify | green |

Green captures: wave 4 743 passed; rework 376 passed. Product `run_checks.py --group lint --group types --group
security`: 5 passed, 0 failed.

**Verifier.** First pass: 25 targeted mutants killed; REFUTED AC-1.2/AC-1.3 (the argparse refusals of `_split` and
`json_member` never ran — a combined mutant passed the wave-2 run). Rework DL-008 added the 7-case refusal test; the
re-verification killed the combined mutant and each of its parts, `call.py` at full line coverage, VERIFIED
(`evidence/verify/refutation-report.md`). Noted: the map's `call` content is guarded by inspection, as designed.

**Whole suite.** CI run 42943558168 success on b127712; CI run 42947226222 success on cbb8c0c (the rework head).
