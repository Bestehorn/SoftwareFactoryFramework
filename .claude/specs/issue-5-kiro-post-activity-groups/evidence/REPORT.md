# Evidence report — issue #5: post-activity step 2 runs only the non-test groups

Tier S, one wave (T1, I1). Branch `issue-5-kiro-post-activity-groups`.

| Criterion | Test (`test/test_post_activity_prompts.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 setup-kiro 8.6 step 2 runs the three non-test groups | `test_kiro_step2_runs_the_non_test_groups` | red/wave-1.txt; green/wave-1.txt | green |
| AC-2 no 8.6 sentence says the checklist runs the tests group | `test_kiro_body_never_runs_the_tests_group` | red; green | green |
| AC-3 setup-claude porting guidance names the non-test groups | `test_claude_porting_paragraph_names_the_non_test_groups` | red; green | green |
| AC-4 setup-claude self-check flags a plain `run_checks.py` | `test_claude_self_check_flags_a_plain_run_checks` | red; green | green |
| UB-1 the deliberate full runs stay plain | `test_deliberate_full_runs_stay_plain[*]` (six sites) | green | green |
| UB-2 step 1 still runs only the affected tests | `test_kiro_step1_still_runs_only_affected_tests` | green | green |
| §Files: the 8.23 Integration line names the non-test groups | `test_kiro_823_integration_names_the_non_test_groups` | verify (COV-1 mutant killed) | green |

Green capture (`# tasks: T1 I1`): the module with `test/test_layout.py`, 68 passed; after the rebase onto the trunk (b496691) the module, `test/test_layout.py` and `test/test_agent_rule_references.py` give 150 passed.

**Verifier.** First pass REFUTED COV-1 (the 8.23 edit had no test); T1 reopened; re-verification VERIFIED (`verify/refutation-report.md`).

**Whole suite.** The CI run on the pushed head SHA; its id and SHA are in the PR and the closing comment. CI runs for this batch: target one.

**Diff.** `prompts/setup-kiro.txt` (8.6 step 2, 8.23 Integration line); `prompts/setup-claude.txt` (porting paragraph, verification item 6).
