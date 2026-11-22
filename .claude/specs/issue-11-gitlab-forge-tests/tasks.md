# Tasks — issue #11: real-GitLab integration tests on ephemeral `sff-test-*` projects

Tier: M. Sources: `requirements.md` (frozen) and `design.md` (approved at iteration 03, DL-007). Test files by the
legend of `design.md` Acceptance Criteria Mapping (W, S, G, F:<module>; C, A, K, V, P, H, L, I and B run unedited, L
but for one extended expectation). Each test's oracle is its `design.md` Correctness Properties entry; each IMPL
follows the D section it cites.

- **Runs.** A wave's red and green runs are `python scripts/run_tests.py` on the W, S, G and L files the wave writes,
  with 1.2's guards; wave 5's runs add S, since 5.9 edits the module S loads. The GitLab forge modules (5.2 to 5.6),
  and 5.9's `push_branch` and `wait_until_checked`, which only they call, are declared on wave 5's red and green
  captures, whose G tests collect and read them; they are validated only by F.1, against gitlab.com, as
  `python scripts/run_tests.py --workers 1 test/forge_gitlab`. G `test_each_uncalled_form_is_named_with_its_reason`
  reads the docstring 5.6 writes, so it is green in wave 5's red capture.
- **Operator prerequisite.** The first green GitLab forge run waits on the operator's gitlab.com test group
  (`TEST_GROUP`, DL-002), its group service account with the Owner role, and that account's personal access token
  with the scope `api`, stored as the Actions secret `SFF_GITLAB_TEST_TOKEN` and, for a local run, as
  `credentials/gitlab-sff-testing-pat.txt` (issue #11 comment 6923784402); no task is blocked on it except F.1.

## Wave 1 — The project guard and the reused module's parameters

- [x] 1.1 TEST: W, created: `test_the_marker_refuses_a_project_without_the_prefix`,
  `test_the_interpreter_option_reaches_the_entry_script`, `test_the_marker_lets_an_ephemeral_project_through`,
  `test_the_marker_values_are_issue_10s`, `test_without_the_marker_every_project_is_served`, in-process through
  `gitlab_wrapper_fixtures` (`write_config`, `FakeGitLab`, `install_socket_guard`, `load_wrapper`, `run_main`), the
  fixtures module loaded by path as C's `load_fixtures` loads it, with the marker set on `sys._xoptions` by
  `monkeypatch.setitem` or not, the entry-script example as a subprocess — Files:
  src/payload/test/test_gitlab_wrapper_marker.py — Validates: AC-4.1, AC-4.2, AC-4.3, UB-1, UB-3
- [x] 1.2 TEST: the unchanged-behaviour guards, no file written, added to every wave's red and green runs (green
  before and after; L's 2.3 expectation red until 2.4): C, A, K, V and P, P `test_standard_library_only` included
  (UB-1, UB-3); H, the pair of 1.4, and L (UB-4); I (UB-5); B `test_llm_map_within_cap` (AC-9.2) — Files, run and
  unedited: src/payload/test/test_gitlab_wrapper_compat.py, src/payload/test/test_gitlab_api_*.py,
  src/payload/test/test_wrapper_delivery.py, test/test_layout.py, test/test_gitlab_graphql_contract.py,
  test/test_github_graphql_contract.py, test/test_toolchain_manifest.py, test/test_gitlab_api_*.py,
  test/test_gitlab_wrapper_contract.py, test/test_gitlab_wrapper_coverage.py, test/test_forge_support.py,
  test/test_forge_suite_layout.py (written only by 2.3), test/test_toolchain_integrity.py,
  test/test_instruction_corpus_budget.py — Validates: UB-1, UB-3, UB-4, UB-5, AC-9.2
- [x] 1.3 IMPL: the project guard (D2): `TEST_MARKER_OPTION`, `EPHEMERAL_PROJECT_PREFIX`, `PROJECT_PATH_SEPARATOR`,
  `EXIT_PROJECT_REFUSED`, `_test_marker_set`, `_is_ephemeral_project`, `_refuse_unless_ephemeral`, its two calls in
  `_run`, `main`'s mapping of `GitLabProjectRefusedError`, the docstrings; `GitLabProjectRefusedError(GitLabAPIError)`
  and the module docstring of `errors.py` — Files: src/payload/scripts/gitlab_wrapper.py,
  src/payload/scripts/gitlab_api/errors.py — Validates: AC-4.1, AC-4.2, AC-4.3, UB-3
- [x] 1.4 IMPL: the keyword-only parameters of D10's `test/forge/ephemeral.py` row, each defaulting to today's value,
  used in the six bodies and described in their docstrings, #10's refusal words kept; paired with 1.2's H, unedited
  — Files: test/forge/ephemeral.py — Validates: UB-4

## Wave 2 — The GitLab forge job and the credential primitives

- [x] 2.1 TEST: S, created. It loads `test/forge_gitlab/ephemeral.py` by path from inside each test body, through a
  cached helper like #10's S `_load_by_path`, never at import and never in a fixture, so S collects in every wave and
  a test whose symbol does not exist yet fails in its own body; its doubles (3.1, 4.1) are built from the loaded
  module, and 3.1 loads `test/forge_gitlab/write_credential.py`, the same way: `test_a_distributed_run_is_refused`,
  `test_a_run_id_names_an_ephemeral_project`, `test_the_credential_helper_answers_git_with_the_clone_token` (through
  `CLONE_GIT_HELPER`), `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree`,
  `test_a_missing_secret_fails_the_credential_step` (`write_test_credential` with this suite's keywords); checkouts in
  `tmp_path`, local git only — Files: test/test_forge_gitlab_support.py — Validates: AC-1.1, AC-1.2, AC-5.3, AC-6.1,
  AC-6.3, UB-1
- [x] 2.2 TEST: G, created; it loads L by path, registered in `sys.modules` before it runs as #10's S
  `_load_by_path` does, for its workflow reader and `collect_only`: `test_the_gitlab_forge_job_runs_beside_verify`,
  `test_the_gitlab_secret_reaches_one_step`, `test_the_report_judges_the_gitlab_forge_job`, and
  `test_the_default_configuration_collects_no_gitlab_forge_test` (red while `test/forge_gitlab/` does not exist) —
  Files: test/test_forge_gitlab_layout.py — Validates: AC-5.1, AC-5.2, AC-5.4, AC-6.3, AC-7.1, UB-1
- [x] 2.3 TEST: L, `test_the_report_judges_the_forge_job`'s expected `needs` becomes `verify`, `forge` and
  `forge-gitlab` (D5); no other assertion changed or removed — Files: test/test_forge_suite_layout.py — Validates:
  AC-5.4, UB-4
- [x] 2.4 IMPL: the job `forge-gitlab`, the changed `report` and the header comment (D5) — Files:
  .github/workflows/ci.yml — Validates: AC-5.1, AC-5.2, AC-5.4, AC-6.3
- [x] 2.5 IMPL: `test/forge_gitlab/ephemeral.py`, part 1: the reused symbols of `test/forge/ephemeral.py`, loaded by
  path under `forge_ephemeral` (Overview); `GITLAB_FORGE_COMMAND`, `GITLAB_HELPER_KEY`, `GIT_USERNAME`,
  `CLONE_GIT_TOKEN_FILE`, `TEST_GROUP`, `TEST_CREDENTIAL_FILE`, `SECRET_NAME`, `PRODUCT_WRAPPER`,
  `PRODUCT_WRAPPER_MODULE`; `refuse_distributed_run(*, worker_id)` (D1); `CLONE_GIT_HELPER` and
  `product_wrapper()` (D10); `ephemeral_path`, `ephemeral_full_path` (D4) — Files: test/forge_gitlab/ephemeral.py —
  Validates: AC-1.1, AC-1.2, AC-6.1, AC-6.3

## Wave 3 — The wrapper runner, the teardown guard, the sweep and the credential step

- [x] 3.1 TEST: S, extended with `RecordingWrapperRunner(WrapperRunner)`:
  `test_every_wrapper_invocation_carries_the_marker`, `test_the_teardown_deletes_only_this_runs_project`,
  `test_the_teardown_refuses_any_other_target`,
  `test_the_sweep_deletes_exactly_the_old_unscheduled_ephemeral_projects` (the one Hypothesis property),
  `test_the_sweep_boundaries_and_refusals`, and `test_a_missing_secret_fails_the_credential_step` extended:
  `write_credential.main`, loaded by path, logs the refusal and returns 1, and with a token writes the file and returns
  0 — Files: test/test_forge_gitlab_support.py — Validates: AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-3.3, AC-4.3, AC-5.3,
  UB-1
- [x] 3.2 TEST: G, `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project`, by L's `ast` helpers over the
  `.py` files of `test/forge_gitlab/`; "`PRODUCT_WRAPPER` (in `SubprocessWrapperRunner` and `product_wrapper` only)" is
  read as exactly there, so it is red until 3.3 — Files: test/test_forge_gitlab_layout.py — Validates: AC-4.3,
  AC-8.1, AC-8.7
- [x] 3.3 IMPL: `ephemeral.py`, part 2: `SubprocessWrapperRunner` (D10); `CreatedProject`, `delete_ephemeral` (D9
  "The teardown guard"); `ProjectRecord`, `ProjectRecord.of`, `list_group_projects`, `is_leftover`,
  `select_leftovers`, `sweep_leftovers`, `delete_leftover` (D9 "The sweep") — Files: test/forge_gitlab/ephemeral.py —
  Validates: AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-3.3, AC-4.3, AC-8.7
- [x] 3.4 IMPL: the CI step's command (D8 "CI"): it loads `test/forge_gitlab/ephemeral.py` by path under
  `forge_gitlab_ephemeral`, the key of `conftest.py` (D1); `main` reads `SFF_GITLAB_TEST_TOKEN`, calls the reused
  `write_test_credential` with this suite's keywords, logs a refusal and returns 1 — Files:
  test/forge_gitlab/write_credential.py — Validates: AC-5.3

## Wave 4 — Provisioning, the setup note and the map

- [ ] 4.1 TEST: S, extended with `ScriptedGitRunner(GitRunner)`: `test_provisioning_runs_in_order`,
  `test_a_project_created_other_than_private_is_refused_and_deleted`, `test_no_creation_no_deletion`,
  `test_a_bad_test_credential_fails_before_any_request`, `test_the_token_is_written_only_to_the_clone` (with UB-2's
  sentinel), `test_the_clone_commits_no_credential` — Files: test/test_forge_gitlab_support.py — Validates: AC-1.1,
  AC-1.3, AC-1.4, AC-2.3, AC-6.2, AC-6.3, UB-2
- [ ] 4.2 TEST: G, the docs read as text: `test_the_setup_note_names_the_gitlab_credential`,
  `test_the_map_names_the_gitlab_forge_suite` — Files: test/test_forge_gitlab_layout.py — Validates: AC-9.1, AC-9.2
- [ ] 4.3 IMPL: `ephemeral.py`, part 3: `EphemeralProject`, `CLONE_CONFIG_FILE`, `read_test_token` (D8);
  `prepare_clone`, `read_test_group`, `create_ephemeral`, `fetch_seed` and the context manager `provision` (D9 steps 1
  to 8, D3 "The clone") — Files: test/forge_gitlab/ephemeral.py — Validates: AC-1.1, AC-1.3, AC-1.4, AC-2.3, AC-6.2,
  AC-6.3, UB-2
- [ ] 4.4 IMPL: the GitLab section of the setup note, the GitHub sections as they are (D7) — Files:
  docs/forge-suite.md — Validates: AC-9.1
- [ ] 4.5 IMPL: AC-9.2's names in the map's testing section, under its cap (D10) — Files: docs/forLLMConsumption.md —
  Validates: AC-9.2

## Wave 5 — The session fixture, the suite's collection and the real-GitLab tests (D6)

- [ ] 5.1 TEST: G, `test_the_session_fixture_wraps_one_provision`,
  `test_the_gitlab_forge_path_collects_every_gitlab_forge_test`, `test_nothing_keeps_a_gitlab_forge_test_from_running`,
  `test_each_uncalled_form_is_named_with_its_reason` — Files: test/test_forge_gitlab_layout.py — Validates: AC-1.1,
  AC-1.4, AC-5.2, AC-7.2, AC-7.3, AC-8.5, AC-8.6
- [ ] 5.2 TEST: F:fixture, `test_the_run_owns_a_private_seeded_project`, `test_no_leftover_survives_the_sweep`, with
  its module docstring — Files: test/forge_gitlab/forge_fixture.py — Validates: AC-1.1, AC-1.3, AC-3.1, AC-4.2,
  AC-8.1, AC-8.3
- [ ] 5.3 TEST: F:subcommands (#13), `test_an_issue_and_label_round_trip`, `test_a_merge_request_round_trip`,
  `test_delete_branch_removes_a_pushed_branch`, `test_no_pipeline_has_run`, with its module docstring — Files:
  test/forge_gitlab/forge_subcommands.py — Validates: AC-1.3, AC-4.2, AC-8.1, AC-8.2
- [ ] 5.4 TEST: F:records, `test_the_repository_records_read_the_seed`, `test_the_issue_and_note_records`,
  `test_the_merge_request_records`, with its module docstring — Files: test/forge_gitlab/forge_records.py —
  Validates: AC-1.3, AC-4.2, AC-8.1, AC-8.3
- [ ] 5.5 TEST: F:graphql (#44), `test_the_work_items_of_the_project`, with its module docstring — Files:
  test/forge_gitlab/forge_graphql.py — Validates: AC-4.2, AC-8.1, AC-8.4
- [ ] 5.6 TEST: F:request_forms (#63), `test_an_endpoint_named_by_endpoint`, `test_a_format_suffix`; its module
  docstring names each form D6 lists as not called, with D6's reason — Files: test/forge_gitlab/forge_request_forms.py
  — Validates: AC-4.2, AC-8.1, AC-8.5, AC-8.6
- [ ] 5.7 IMPL: the suite's configuration, #10 D1's four keys verbatim (D1) — Files: test/forge_gitlab/pytest.ini —
  Validates: AC-5.2, AC-7.2, AC-7.3
- [ ] 5.8 IMPL: the by-path load of `ephemeral.py` under `forge_gitlab_ephemeral` and the session fixture
  `ephemeral_project` (D1 "One project per run", D9), its git runner given `helper=CLONE_GIT_HELPER` (D10) — Files:
  test/forge_gitlab/conftest.py — Validates: AC-1.1, AC-1.4, AC-6.3, AC-7.1, AC-7.3
- [ ] 5.9 IMPL: `ephemeral.py`, part 4: `push_branch`, `wait_until_checked` and its pause and deadline constants
  (D10) — Files: test/forge_gitlab/ephemeral.py — Validates: AC-8.2, AC-8.3, AC-8.5

## Final

- [ ] F.1 E2E: the GitLab forge suite itself, every `test/forge_gitlab/forge_*.py`, run by the `forge-gitlab` job of
  `.github/workflows/ci.yml` on the PR (`python scripts/run_tests.py --workers 1 test/forge_gitlab`) and judged by
  `report`, its verdict read through the wrapper's `get-pr-checks` and `get-run`; and locally once the operator
  prerequisite is in place (issue #11 comment 6923784402). Nothing deploys. — Files: test/forge_gitlab/ — Validates:
  AC-5.1, AC-5.2 and the criteria of 5.2 to 5.6
