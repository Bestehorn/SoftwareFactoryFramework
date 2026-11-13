# Tasks — issue #10: integration tests of the forge wrapper against ephemeral `sff-test-*` repositories (S4)

Tier: M. Sources: `requirements.md` (frozen) and `design.md` (approved at iteration 03). Test files by the legend of
`design.md` Acceptance Criteria Mapping (W, S, L, F:<module>; C, P, K, V, I and B run unedited). Each test's oracle is
its `design.md` Correctness Properties entry; each IMPL follows the D section it cites.

- **Runs.** A wave's red and green runs are `python scripts/run_tests.py` on the W, S and L files the wave writes,
  with 1.4's guards. The forge modules (4.3, 4.7 to 4.10) are declared on wave 4's red and green captures, whose L
  tests read them. Against github.com they run only as `python scripts/run_tests.py --workers 1 test/forge`, which is
  F.1.
- **Operator prerequisite.** The first green forge run waits on the token permissions `design.md` D6's table marks
  "to grant" and on the local test credential file `credentials/github-sff-testing-pat.txt` (issue #10 comments
  6829284579, 6829880820); no task is blocked on it except F.1.

## Wave 1 — The origin guard, the forge job and the credential primitives

- [x] 1.1 TEST: W, the guard (D2): `test_the_marker_refuses_an_origin_without_the_prefix`,
  `test_the_interpreter_option_reaches_the_entry_script`, `test_the_marker_lets_an_ephemeral_origin_through`,
  `test_without_the_marker_every_origin_is_served`, in-process on `github_wrapper_fixtures.load_script` (the call
  C's `load_wrapper` makes), `enter_project` and `FakeGitHub`, the fixtures module loaded by path as C loads it, the
  entry-script example as a subprocess — Files: src/payload/test/test_github_wrapper_marker.py — Validates: AC-4.1,
  AC-4.2, AC-4.3, UB-1, UB-3
- [x] 1.2 TEST: L, created; the workflow read as text: `test_the_forge_job_runs_beside_verify`,
  `test_the_secret_reaches_one_step`, `test_the_report_judges_the_forge_job`; and <!-- pragma: allowlist secret -->
  `test_the_default_configuration_collects_no_forge_test` (red while `test/forge/` does not exist) — Files:
  test/test_forge_suite_layout.py — Validates: AC-5.1, AC-5.2, AC-5.4, AC-6.3, AC-7.1, UB-1
- [x] 1.3 TEST: S, created. It loads `test/forge/ephemeral.py` by path from inside each test body, through a cached
  helper that, like P's `_load_fixtures`, registers it in `sys.modules` before executing it and reuses it when its
  `__file__` is this path, never at import and never in a fixture; nothing at S's module level names a symbol of
  `ephemeral.py`. Its doubles (2.1, 3.1) are built from the loaded module the same way, and so is 4.2's load of
  `write_credential.py`, so S collects in every wave and a test whose symbol does not exist yet fails in its own body:
  `test_a_distributed_run_is_refused`, `test_the_credential_helper_answers_git_with_the_clone_token`,
  `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree`, and
  `test_a_missing_secret_fails_the_credential_step` with its `write_test_credential` assertions (4.2 adds
  `write_credential.main`); checkouts in `tmp_path`, local git only — Files: test/test_forge_support.py — Validates:
  AC-1.1, AC-5.3, AC-6.1, AC-6.3, UB-1
- [x] 1.4 TEST: the unchanged-behaviour guards, no file written, added to every wave's red and green runs (green
  before and after): C, P, K and V (UB-3), I (UB-4) — Files: src/payload/test/test_github_wrapper_compat.py,
  test/test_github_wrapper_fork_parity.py, test/test_github_wrapper_contract.py, test/test_github_wrapper_coverage.py,
  test/test_toolchain_integrity.py, all unedited — Validates: UB-3, UB-4
- [x] 1.5 IMPL: the origin guard (D2): `TEST_MARKER_OPTION`, `EPHEMERAL_REPOSITORY_PREFIX`, `_test_marker_set`,
  `_refuse_unless_ephemeral`, its call in `main` after `_detect_repo`, the docstrings of `main` and of the exit
  paragraph — Files: src/payload/scripts/github_wrapper.py — Validates: AC-4.1, AC-4.2, AC-4.3, UB-3
- [x] 1.6 IMPL: the job `forge` and the changed `report` (D5) — Files: .github/workflows/ci.yml — Validates: AC-5.1,
  AC-5.2, AC-5.4, AC-6.3
- [x] 1.7 IMPL: `ephemeral.py`, part 1 (D10): `ForgeSuiteError` (`details=None`) and its four subclasses;
  `refuse_distributed_run` (D1); `credential_helper_arguments` (D3); `find_test_credential` and
  `write_test_credential` (D8); the constants they use — Files: test/forge/ephemeral.py — Validates: AC-1.1, AC-5.3,
  AC-6.1, AC-6.3, AC-7.1

## Wave 2 — The runners, the run id and the two deletion paths

- [x] 2.1 TEST: S, extended with `RecordingWrapperRunner(WrapperRunner)`:
  `test_a_run_id_is_unique_and_names_a_repository`, `test_every_wrapper_invocation_carries_the_marker`,
  `test_the_teardown_deletes_only_this_runs_repository`, `test_the_teardown_refuses_any_other_target`,
  `test_the_sweep_deletes_exactly_the_old_ephemeral_repositories` (the one Hypothesis property),
  `test_the_sweep_boundaries_and_refusals` — Files: test/test_forge_support.py — Validates: AC-1.2, AC-2.1, AC-2.2,
  AC-3.1, AC-3.2, AC-4.3, UB-1
- [x] 2.2 TEST: L, `test_the_forge_tests_reach_only_the_ephemeral_repository`, by `ast` of the `.py` files of
  `test/forge/`; "`PRODUCT_WRAPPER` is named ... only in `SubprocessWrapperRunner` and `product_wrapper`" is read as
  exactly there, so it is red until 2.3 — Files: test/test_forge_suite_layout.py — Validates: AC-4.3, AC-8.1, AC-8.6
- [x] 2.3 IMPL: `ephemeral.py`, part 2: `Invocation`, `RepositoryRecord`, `CreatedRepository`, `WrapperRunner`,
  `SubprocessWrapperRunner`, `GitRunner`, `SubprocessGitRunner`, `PRODUCT_WRAPPER`, `product_wrapper()`, the commit
  identity and the subprocess timeout (D10); `TEST_ORGANIZATION` (D5); `new_run_id`, `ephemeral_name` (D4);
  `delete_ephemeral`, `RepositoryRecord.of`, `LEFTOVER_AGE`, `is_leftover`, `select_leftovers`, `sweep_leftovers`,
  `delete_leftover` (D9) — Files: test/forge/ephemeral.py — Validates: AC-1.2, AC-2.1, AC-2.2, AC-3.1, AC-3.2,
  AC-4.3, AC-8.6

## Wave 3 — Provisioning, the setup note and the docs

- [x] 3.1 TEST: S, extended with `ScriptedGitRunner(GitRunner)`: `test_provisioning_runs_in_order`,
  `test_no_creation_no_deletion`, `test_a_bad_test_credential_fails_before_any_request`,
  `test_the_token_is_written_only_to_the_clone` — Files: test/test_forge_support.py — Validates: AC-1.1, AC-1.3,
  AC-1.4, AC-2.3, AC-6.2, AC-6.3, UB-2
- [x] 3.2 TEST: L, the docs read as text: `test_the_setup_note_names_the_credential`,
  `test_the_map_names_the_forge_suite`, `test_the_debt_line_is_gone`; B `test_llm_map_within_cap` joins this wave's
  runs — Files: test/test_forge_suite_layout.py — Validates: AC-9.1, AC-9.2, AC-9.3
- [x] 3.3 IMPL: `ephemeral.py`, part 3: `EphemeralRepository`, `CHECKOUT`, `CLONE_CREDENTIAL_FILE`, `read_test_token`
  (D8); `prepare_clone`, `create_ephemeral`, `fetch_seed`, `remove_tree` and the context manager `provision` (D9
  steps 1 to 7, D3 "The clone") — Files: test/forge/ephemeral.py — Validates: AC-1.1, AC-1.3, AC-1.4, AC-2.3, AC-6.2,
  AC-6.3, UB-2
- [x] 3.4 IMPL: the setup note (D7) — Files: docs/forge-suite.md — Validates: AC-9.1
- [x] 3.5 IMPL: the map's `Testing` section, naming `docs/forge-suite.md`, under its cap, and the debt line removed
  (D10) — Files: docs/forLLMConsumption.md, docs/ProjectPlan.md — Validates: AC-9.2, AC-9.3

## Wave 4 — The session fixture, the suite's collection, the CI credential step and the real-forge tests of the deferred slices (D6)

- [x] 4.1 TEST: L, `test_the_session_fixture_wraps_one_provision`, `test_the_forge_path_collects_every_forge_test`,
  `test_nothing_keeps_a_forge_test_from_running` — Files: test/test_forge_suite_layout.py — Validates: AC-1.1,
  AC-1.4, AC-5.2, AC-7.2, AC-7.3
- [x] 4.2 TEST: S, `test_a_missing_secret_fails_the_credential_step` extended: `write_credential.main`, loaded by
  path, returns 1 on the refusal — Files: test/test_forge_support.py — Validates: AC-5.3
- [x] 4.3 TEST: F:fixture, `test_the_run_owns_a_private_seeded_repository`, `test_no_leftover_survives_the_sweep`
  (D6), with its module docstring — Files: test/forge/forge_fixture.py — Validates: AC-1.1, AC-1.3, AC-3.1, AC-4.2,
  AC-8.1
- [x] 4.4 IMPL: the suite's configuration (D1 "Mechanism") — Files: test/forge/pytest.ini — Validates: AC-5.2,
  AC-7.2, AC-7.3
- [x] 4.5 IMPL: the by-path load of `ephemeral.py` and the session fixture `ephemeral_repository` (D1 "One repository
  per run", D9, D10) — Files: test/forge/conftest.py — Validates: AC-1.1, AC-1.4, AC-7.1, AC-7.3
- [x] 4.6 IMPL: the CI step's command (D8 "CI"): it loads `ephemeral.py` by path, as `conftest.py` does (D10), and
  calls `write_test_credential` — Files: test/forge/write_credential.py — Validates: AC-5.3
- [x] 4.7 TEST: F:subcommands (#17), `test_an_issue_round_trip`, `test_a_pull_request_round_trip`, with its module
  docstring (D10) — Files: test/forge/forge_subcommands.py — Validates: AC-4.2, AC-8.1, AC-8.2
- [x] 4.8 TEST: F:repos_git (#27), `test_the_repository_record_names_the_seed_branch`,
  `test_the_git_records_read_the_seed_commit`, with its module docstring (D10) — Files: test/forge/forge_repos_git.py
  — Validates: AC-1.3, AC-4.2, AC-8.1, AC-8.3
- [x] 4.9 TEST: F:ci_security (#31), `test_no_workflow_has_run`, `test_code_scanning_answers_as_documented`,
  `test_secret_scanning_answers_as_documented`, `test_dependabot_lists_no_secret`; its module docstring (D10) <!-- pragma: allowlist secret -->
  names `checks` with its reason — Files: test/forge/forge_ci_security.py — Validates: AC-4.2, AC-8.1, AC-8.4
- [x] 4.10 TEST: F:collaboration (#32), `test_issue_and_reaction_records`,
  `test_pulls_search_activity_and_gists_records`, with its module docstring (D10) — Files:
  test/forge/forge_collaboration.py — Validates: AC-4.2, AC-8.1, AC-8.5

## Final

- [x] F.1 E2E: the forge suite itself, every `test/forge/forge_*.py`, run by the `forge` job of
  `.github/workflows/ci.yml` on the PR (`python scripts/run_tests.py --workers 1 test/forge`), its verdict read through
  the wrapper's `get-pr-checks` and `get-run`; and locally on this machine once the operator's test credential file
  and token permissions are in place (issue #10 comments 6829284579, 6829880820). Nothing deploys. — Files:
  test/forge/ — Validates: AC-5.1 and the criteria of 4.3 and 4.7 to 4.10
