# VERIFY 01 — test-architect — issue #10 (HEAD 59d5928)

## Findings

### C1 — L does not see a forge job muted by `continue-on-error`
Severity: C
Location: test/test_forge_suite_layout.py § `test_the_forge_job_runs_beside_verify` (AC-5.1, AC-5.4)
Defect: The test reads only the `forge` job's `needs:` and its last step's `run:`, so a `continue-on-error: true` on
  that step ("Set to `true` to allow a job to pass when this step fails", docs.github.com "Workflow syntax for GitHub
  Actions" `jobs.<job_id>.steps[*].continue-on-error`) would make `needs.forge.result` success on a red suite and pass
  every L test; today's `ci.yml` holds no such key, so the built behaviour is correct.
Material-because: risk only, no criterion's text is broken; the key would mute Requirement 5's "its failure to fail
  the pipeline", which AC-5.4's test cannot see because the job's result would be success.
Proposed-edit: in `test_the_forge_job_runs_beside_verify`, with a constant `KEY_CONTINUE_ON_ERROR = "continue-on-error"`,
  add `assert KEY_CONTINUE_ON_ERROR not in forge and not [step for step in steps_of(job=forge, name=JOB_FORGE) if
  KEY_CONTINUE_ON_ERROR in step]`, test-only, no criterion added. (A job-level `if:` that skips the job is already
  caught: `report` fails on `skipped`, which `test_the_report_judges_the_forge_job` pins.)

## Coverage

W `src/payload/test/test_github_wrapper_marker.py`, S `test/test_forge_support.py`, L `test/test_forge_suite_layout.py`,
F `test/forge/forge_<module>.py`; C, P, K, V, I, B as in design.md's legend.

| Criterion | Test(s) as built | Status |
|---|---|---|
| AC-1.1 | S `test_provisioning_runs_in_order`, `test_a_repository_created_other_than_private_is_refused_and_deleted`, `test_a_distributed_run_is_refused`; L `test_the_session_fixture_wraps_one_provision`; F:fixture `test_the_run_owns_a_private_seeded_repository` | OK |
| AC-1.2 | S `test_a_run_id_is_unique_and_names_a_repository` | OK |
| AC-1.3 | S `test_provisioning_runs_in_order` (workflow-seed case); F:fixture `test_the_run_owns_a_private_seeded_repository`; F:repos_git `test_the_git_records_read_the_seed_commit` | OK |
| AC-1.4 | S `test_provisioning_runs_in_order` (body returns, raises, deletion fails), `test_a_refused_removal_is_retried`, `test_a_removal_refused_every_time_fails_naming_the_path`; L `test_the_session_fixture_wraps_one_provision` | OK |
| AC-2.1 | S `test_the_teardown_deletes_only_this_runs_repository` | OK |
| AC-2.2 | S `test_the_teardown_refuses_any_other_target` (owner, prefix, run id) | OK |
| AC-2.3 | S `test_no_creation_no_deletion` | OK |
| AC-3.1 | S `test_the_sweep_deletes_exactly_the_old_ephemeral_repositories` (Hypothesis; expected set from the drawn owner, prefix and age sides, never `is_leftover`), `test_the_sweep_boundaries_and_refusals`, `test_a_failed_listing_stops_the_run`; F:fixture `test_no_leftover_survives_the_sweep` | OK |
| AC-3.2 | S the same property, `test_the_sweep_boundaries_and_refusals` | OK |
| AC-4.1 | W `test_the_marker_refuses_an_origin_without_the_prefix` (5 argv x 4 origins, inner and trailing `sff-test-` included), `test_the_interpreter_option_reaches_the_entry_script` (exit pinned by `fx.EXIT_REFUSED`, option by literal) | OK |
| AC-4.2 | W `test_the_marker_lets_an_ephemeral_origin_through` (with its in-process refusal control); every F test | OK |
| AC-4.3 | S `test_every_wrapper_invocation_carries_the_marker`; L `test_the_forge_tests_reach_only_the_ephemeral_repository`; W `test_the_interpreter_option_reaches_the_entry_script` (cwd outside the repository), `test_without_the_marker_every_origin_is_served` | OK |
| AC-5.1 | L `test_the_forge_job_runs_beside_verify` | OK (C1) |
| AC-5.2 | L `test_the_secret_reaches_one_step`, `test_nothing_keeps_a_forge_test_from_running` | OK |
| AC-5.3 | S `test_a_missing_secret_fails_the_credential_step` (`write_test_credential`; `write_credential.main` unset, empty, token) | OK |
| AC-5.4 | L `test_the_report_judges_the_forge_job` | OK |
| AC-6.1 | S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree` | OK |
| AC-6.2 | S `test_a_bad_test_credential_fails_before_any_request` (missing, empty, placeholder, two tokens) | OK |
| AC-6.3 | S `test_the_token_is_written_only_to_the_clone`, `test_the_credential_helper_answers_git_with_the_clone_token` (decoy helper reset); L `test_the_secret_reaches_one_step` | OK |
| AC-7.1 | L `test_the_default_configuration_collects_no_forge_test` | OK |
| AC-7.2 | L `test_the_forge_path_collects_every_forge_test` | OK |
| AC-7.3 | L `test_nothing_keeps_a_forge_test_from_running` | OK |
| AC-8.1 | L `test_the_forge_tests_reach_only_the_ephemeral_repository`; every F invocation asserts its exit code and printed answer | OK |
| AC-8.2 | F:subcommands `test_an_issue_round_trip`, `test_a_pull_request_round_trip` | OK (1) |
| AC-8.3 | F:repos_git `test_the_repository_record_names_the_seed_branch`, `test_the_git_records_read_the_seed_commit` | OK (green in run 43295116103) |
| AC-8.4 | F:ci_security four tests; module docstring names `checks` with its reason | OK (1) |
| AC-8.5 | F:collaboration `test_issue_and_reaction_records`, `test_pulls_search_activity_and_gists_records` | OK (1) |
| AC-8.6 | L `test_the_forge_tests_reach_only_the_ephemeral_repository` | OK |
| AC-9.1 | L `test_the_setup_note_names_the_credential` | OK |
| AC-9.2 | L `test_the_map_names_the_forge_suite`; B `test_llm_map_within_cap` | OK |
| AC-9.3 | L `test_the_debt_line_is_gone` | OK |
| UB-1 | W (`refuse_connections`, `FakeGitHub`), S (doubles, local git in `tmp_path`), L (`--collect-only`, text, `ast`); no fake-host suite in the diff | OK |
| UB-2 | S `test_the_token_is_written_only_to_the_clone` (sentinel content kept, opens recorded) | OK |
| UB-3 | C, P, K, V absent from the diff; W `test_without_the_marker_every_origin_is_served` | OK |
| UB-4 | I; the diff names no path `config/toolchain.json` lists | OK |

(1) Falsifiable and run: red in run 43295116103 only on GitHub's missing-permission 403 for the permissions D6 marks
"to grant" (DL-006); the green real-forge run is task F.1.

TEST-READY: 35 of 35 criteria OK, 0 GAP; no test is skipped, xfailed or weakened, and no existing test file is edited.

CLEAN
