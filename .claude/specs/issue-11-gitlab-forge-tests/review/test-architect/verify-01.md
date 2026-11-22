# Test architect: VERIFY 01, delta `83a1415..HEAD` (code under test `c389d46`)

## Findings

None. A 0, B 0, C 0, D 0.

Basis: `scripts/run_tests.py` over W, S, G, L, H in this worktree: `128 passed`, 0 skipped, 0 xfailed. A Grep for
skip, skipif, xfail, importorskip, `pytest.exit`, `collect_ignore` and `assert True` over W, S, G and
`test/forge_gitlab/` finds only G's own failure message. L's one edit keeps the exact `sorted(needs) == sorted([...])`
and adds `forge-gitlab` to it, so the check is extended, not weakened. The diff touches no C, A, K, V, P or H file, and
under `test/forge/` it touches only `ephemeral.py`. The red captures (exit 1) and green captures (exit 0) declare
tasks 1.1 to 5.9. CI run 45033382186 on `c389d46`: every `verify` leg and `forge` succeeded.

Oracles: each W, S and G expectation is fixed in the test, not taken from the code under test:
- W: literal marker and exit values. Its controls show the marker is read from `sys._xoptions`.
- S: the sweep's expected set comes from the drawn values, never from `is_leftover`. S checks the decoding against
  bytes that are not UTF-8 and hold `\r\n`.
- G: literal job, step and record names.

The F modules (`test/forge_gitlab/forge_*.py`) are judged statically, and their runtime verdict is F.1's. They assert
against two kinds of value:
- values the fixture or the test made: run id, full path, seed SHA, `git rev-parse <seed>:README.md`, `uuid4` titles,
  pushed SHAs;
- values GitLab documents: `opened`, `closed`, `merged`, `mergeable`, `OPEN`, `Issue`, `answered 404`, `[]`.

The printed shapes they expect match the product handlers:
- `pipeline status` prints the list `_newest_pipelines` returns.
- `delete-branch` prints `{branch, deleted: true}`.
- `issue label-add`, `issue close` and `mr merge` print the updated record.

## Coverage

Key to the files:
- W: `src/payload/test/test_gitlab_wrapper_marker.py`
- S: `test/test_forge_gitlab_support.py`
- G: `test/test_forge_gitlab_layout.py`
- L: `test/test_forge_suite_layout.py`
- H: `test/test_forge_support.py`
- F:m: `test/forge_gitlab/forge_m.py`

Test names below drop their `test_` prefix. An OK marked "static" is a judgement of the oracle by reading, with the
runtime verdict pending F.1.

| Criterion | Implemented test(s) | Status |
|---|---|---|
| AC-1.1 | S provisioning_runs_in_order, a_distributed_run_is_refused; G the_session_fixture_wraps_one_provision; F:fixture the_run_owns_a_private_seeded_project | OK |
| AC-1.2 | S a_run_id_names_an_ephemeral_project | OK |
| AC-1.3 | S provisioning_runs_in_order (`.gitlab-ci.yml` seed refused, deletion still sent); F:fixture the_run_owns_a_private_seeded_project; F:subcommands no_pipeline_has_run; F:records the_repository_records_read_the_seed | OK |
| AC-1.4 | S provisioning_runs_in_order (the body returns, the body raises, the deletion fails), a_project_created_other_than_private_is_refused_and_deleted; G the_session_fixture_wraps_one_provision | OK |
| AC-2.1 | S the_teardown_deletes_only_this_runs_project | OK |
| AC-2.2 | S the_teardown_refuses_any_other_target (another namespace, a subgroup, no prefix, another run) | OK |
| AC-2.3 | S no_creation_no_deletion | OK |
| AC-3.1 | S the_sweep_deletes_exactly_the_old_unscheduled_ephemeral_projects (property), the_sweep_boundaries_and_refusals; F:fixture no_leftover_survives_the_sweep | OK |
| AC-3.2 | S the same two (near-miss namespaces and paths; exactly a day old is kept) | OK |
| AC-3.3 | S the same two (a scheduled project is sent nothing; `answered 404` and the already-marked `400` are handled) | OK |
| AC-4.1 | W the_marker_refuses_a_project_without_the_prefix (5 argvs, 8 configs), the_interpreter_option_reaches_the_entry_script | OK |
| AC-4.2 | W the_marker_lets_an_ephemeral_project_through, with its refusal control; every F test runs with the marker | OK |
| AC-4.3 | S every_wrapper_invocation_carries_the_marker; W the_marker_values_are_issue_10s, without_the_marker_every_project_is_served; G the_gitlab_forge_tests_reach_only_the_ephemeral_project | OK |
| AC-5.1 | G the_gitlab_forge_job_runs_beside_verify | OK |
| AC-5.2 | G the_gitlab_secret_reaches_one_step, nothing_keeps_a_gitlab_forge_test_from_running | OK |
| AC-5.3 | S a_missing_secret_fails_the_credential_step (`main`: unset or empty returns 1, a token returns 0) | OK |
| AC-5.4 | G the_report_judges_the_gitlab_forge_job; L the_report_judges_the_forge_job (exact `needs`) | OK |
| AC-6.1 | S the_test_credential_is_found_in_the_checkout_or_its_main_tree | OK |
| AC-6.2 | S a_bad_test_credential_fails_before_any_request (7 kinds; a final `\r\n` accepted) | OK |
| AC-6.3 | S the_token_is_written_only_to_the_clone, the_clone_commits_no_credential, the_credential_helper_answers_git_with_the_clone_token; G the_gitlab_secret_reaches_one_step | OK |
| AC-7.1 | G the_default_configuration_collects_no_gitlab_forge_test | OK |
| AC-7.2 | G the_gitlab_forge_path_collects_every_gitlab_forge_test | OK |
| AC-7.3 | G nothing_keeps_a_gitlab_forge_test_from_running | OK |
| AC-8.1 | G the_gitlab_forge_tests_reach_only_the_ephemeral_project; every F test asserts each exit code and printed answer | OK (F static) |
| AC-8.2 | F:subcommands an_issue_and_label_round_trip, a_merge_request_round_trip, delete_branch_removes_a_pushed_branch, no_pipeline_has_run | OK (static) |
| AC-8.3 | F:records the_repository_records_read_the_seed, the_issue_and_note_records, the_merge_request_records; F:fixture the_run_owns_a_private_seeded_project | OK (static) |
| AC-8.4 | F:graphql the_work_items_of_the_project | OK (static) |
| AC-8.5 | F:request_forms an_endpoint_named_by_endpoint, a_format_suffix; G each_uncalled_form_is_named_with_its_reason | OK (F static) |
| AC-8.6 | G each_uncalled_form_is_named_with_its_reason | OK |
| AC-8.7 | G the_gitlab_forge_tests_reach_only_the_ephemeral_project | OK |
| AC-9.1 | G the_setup_note_names_the_gitlab_credential | OK |
| AC-9.2 | G the_map_names_the_gitlab_forge_suite; `test_llm_map_within_cap` (green in `verify (tests)`) | OK |
| UB-1 | W (socket guard), S (`tmp_path`, local git only) and G, all in `verify`; the fake-host suites are not in the diff | OK |
| UB-2 | S the_token_is_written_only_to_the_clone (the sentinel keeps its content; no `config/gitlab.json` opened outside the clone) | OK |
| UB-3 | W without_the_marker_every_project_is_served; C, A, K, V and P are not in the diff, and they are green in `verify (tests)` | OK |
| UB-4 | H unedited and green; L has one expectation extended and stays exact; under `test/forge/` only `ephemeral.py` changed | OK |
| UB-5 | I is green in `verify (tests)`; `config/toolchain.json` records `gitlab_wrapper.py` as not installed and `ci.yml` as the project's own | OK |

COVERED: 37. GAP: 0.

Verdict: CLEAN. TEST-READY
