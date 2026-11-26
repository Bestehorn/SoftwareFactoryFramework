# Evidence report — issue #73: the session title says what the session is doing

Tier S, one wave (T1, I1). Spec: `change.md`. E2E: not applicable (natural-language assets and a structural test).

## Proof

| Claim | Evidence |
|---|---|
| Red for the right reason | `evidence/red/wave-1.txt` (`# tasks: T1`): 29 failed, 36 passed; every failure an `AssertionError`; `red_for_right_reason.py` → OK |
| Green, wave 1 | `evidence/green/wave-1.txt` (`# tasks: T1, I1`): 65 passed |
| Proof cycle 1 | `evidence/verify/refutation-report.md`: CI run 45839898768 green on 75ce112; mutants M9–M12 survived → REFUTED AC-1, AC-2, AC-3, AC-5 (DL-005) |
| Fix | 9dc2336: the test requires the doc's trigger, its end and no-question clauses, each work command's trigger and the orchestrator's phase-to-activity pairs |
| Green, cycle 2 | `evidence/green/wave-1-cycle-2.txt`: 65 passed |
| Proof cycle 2 | `evidence/verify/refutation-report-cycle-2.md`: CI run 45842892204 green on 9dc2336; M9–M12 killed; new mutants N1–N3 survived → REFUTED AC-1, AC-2, AC-3 (DL-006) |
| Fix | the rename trigger must follow the tool within one clause; every form bullet names its activities; the doc keeps "the session skips this rule" and "A subagent ignores this rule" |
| Green, cycle 3 | `evidence/green/wave-1-cycle-3.txt`: 65 passed |
| Proof cycle 3 | `evidence/verify/refutation-report-cycle-3.md` — CI_CYCLE_3 |
| Local checks | `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed |

## Coverage

| Criterion | Test |
|---|---|
| AC-1 | `test_the_doc_states_the_form_and_how_to_rename`, `test_the_doc_gives_every_kind_of_session_a_form` (7) |
| AC-2 | `test_the_doc_keeps_the_four_properties` |
| AC-3 | `test_every_main_session_command_renames_by_the_shared_rule` (11), `test_every_main_session_agent_renames_by_the_shared_rule` (2), `test_no_work_entry_point_limits_the_rename_to_the_set` (3) |
| AC-4 | the allowlist and `tools` checks of the AC-3 tests, `test_every_desktop_tool_an_agent_calls_is_in_its_tools` (20) |
| AC-5 | `test_the_orchestrator_renames_when_the_activity_changes`, `test_the_doc_lists_the_issue_work_activities` |
| AC-6 | `test_the_claude_md_template_names_the_rule`, `test_the_setup_prompt_installs_the_doc` |
| UB-1 to UB-3 | `test_the_title_rule_names_every_mode_and_survives_compaction`, `test_every_work_entry_point_keeps_the_session_title`, `test_every_desktop_tool_a_command_calls_is_allowlisted` |

## Residuals

- The installed copies (`.claude/`, this repository's `CLAUDE.md`) change only at the next release and promotion.
- Skills do not rename; the sidebar's visible title length is not measured.
