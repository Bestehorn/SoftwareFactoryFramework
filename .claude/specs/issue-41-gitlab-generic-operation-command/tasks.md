# Tasks — issue #41: GitLab wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-003); nothing is added. Test files as
design § Acceptance Criteria Mapping: K = `src/payload/test/test_gitlab_api_call.py`, R =
`src/payload/test/test_gitlab_api_registry.py`, T = `src/payload/test/test_gitlab_api_transport.py`, H =
`test/test_gitlab_api_call_properties.py`, N = `test/test_gitlab_wrapper_contract.py`, V =
`test/test_gitlab_wrapper_coverage.py`, C = `src/payload/test/test_gitlab_wrapper_compat.py`, P =
`test/test_gitlab_api_properties.py`; fx = `src/payload/test/gitlab_wrapper_fixtures.py`. Each test does what design
§ Correctness Properties states for its criterion, with its cases, against that oracle. In a wave the TEST tasks run
first and add failing tests only, but for a test its task names green by design, red for the right reason — an
assertion, or an exception raised inside the test body (an `AttributeError` or `TypeError` on what is not yet
written), never a collection error: a test reaching a module this change writes imports it inside the test, after
asserting its file exists as R's `gitlab_module` does or turning an import failure into an assertion as V's
`registry_module` does, and no new test module imports `commands/call.py` at module level. The IMPL tasks then add the
minimal code that turns them green. No task edits an existing line of C, of P, or of an existing test of R, T or V
(UB-1.1).

## Wave 1 — Registry, transport and fixtures

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_registry.py src/payload/test/test_gitlab_api_transport.py src/payload/test/test_gitlab_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_gitlab_wrapper_coverage.py test/test_gitlab_api_properties.py`

- [x] 1.1 TEST: R, on its synthetic families (`serve_families`) and a `Transport` on the fake host, each reaching
  `registry.<name>` through `gitlab_module`: `test_send_returns_the_response_of_the_record` (a `204`'s `Response` is
  returned; a GraphQL ID raises `ValueError` with no request), `test_attribute_name_drops_one_trailing_bracket_pair`,
  `test_variables_are_the_documents_definitions` (its `GraphQLOperation`s built with `capability`). — Files:
  src/payload/test/test_gitlab_api_registry.py — Validates: AC-1.2, AC-1.3, AC-2.2
- [x] 1.2 TEST: T — `test_is_json_reads_the_content_type`: true for `application/json; charset=utf-8`, false for
  `text/plain` and with no `Content-Type`. — Files: src/payload/test/test_gitlab_api_transport.py — Validates: AC-1.5
- [x] 1.3 TEST (fixtures; adds no test): fx gains D8's `FakeGitLab.script_next(*, status=200, headers=(), body=None)`
  (served to the next request that matches no scripted method and URL, recorded as usual), `load_wrapper(*,
  module_name)`, `write_config(*, root, config)` and `run_main(*, wrapper, argv)` (the return value or the `SystemExit`
  code). C keeps its own `load_wrapper`, `write_json` and `main_exit_code`, unedited. — Files:
  src/payload/test/gitlab_wrapper_fixtures.py — Validates: UB-1.1 (C, R and T load fx on this Run line)
- [x] 1.4 IMPL: D2's registry additions — `GraphQLOperation.capability: str` after `operation_id`;
  `attribute_name(*, name)`; `variables(*, operation)` (each `$name` followed, after any white space, by `:`, in order;
  for a record with a `connection`, without `transport.FIELD_AFTER`, imported inside the function);
  `send(transport, operation_id, *, values=None) -> Response` (`lookup`, `encode`, `expand`, `Transport.request`; a
  GraphQL record raises `ValueError`), and `call` as `send(...).value` for a REST record; and D2's transport addition,
  `Response.is_json`, which `Response.value` reads in place of its own comparison. Standard library only. — Files:
  src/payload/scripts/gitlab_api/registry.py, src/payload/scripts/gitlab_api/transport.py — Validates: AC-1.2, AC-1.3,
  AC-1.5, AC-2.2, AC-6.2

## Wave 2 — The `call` command and the contract

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_call.py test/test_gitlab_api_call_properties.py test/test_gitlab_wrapper_contract.py src/payload/test/test_gitlab_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_gitlab_wrapper_coverage.py test/test_gitlab_api_properties.py`

- [x] 2.1 TEST: K — loads fx by path as R does; each test writes `config/gitlab.json` into `tmp_path` with
  `fx.write_config` (`hostname` `fx.HOST`) and runs the product's `main(argv=["call", …])` with `fx.load_wrapper` and
  `fx.run_main`. Requests are judged by the fake host's records; refusals by a `caplog` record (argparse's by `capsys`)
  plus no request recorded; non-JSON output by `capsysbinary`; design's synthetic records are set into a family
  module's `OPERATIONS` or `graphql_only.OPERATIONS` with `monkeypatch.setattr`. Tests:
  `test_a_gated_operation_names_its_subcommand`, `test_an_operation_call_sends_its_record`,
  `test_an_attribute_carries_its_kind`, `test_a_field_that_is_not_json_is_refused`,
  `test_a_list_prints_every_page_as_one_array`, `test_a_json_or_empty_body_prints_as_documented`,
  `test_a_body_that_is_not_json_is_written_unchanged`, `test_an_api_error_exits_1_with_its_details`,
  `test_a_project_path_takes_the_configured_project`, `test_a_graphql_record_sends_its_document`,
  `test_an_unknown_operation_is_refused`, `test_an_undocumented_parameter_is_refused`,
  `test_a_missing_path_parameter_is_refused`, `test_a_value_of_the_wrong_shape_is_refused`,
  `test_call_takes_no_token_option` (a missing `call` subparser fails it). — Files:
  src/payload/test/test_gitlab_api_call.py — Validates: AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8,
  AC-1.9, AC-2.1, AC-2.2, AC-2.3, AC-2.4, UB-2.1
- [x] 2.2 TEST: H — puts `src/payload/scripts` on `sys.path` and carries `@settings(deadline=None)`, as P does;
  `test_any_json_value_becomes_the_attribute_value`, AC-1.3's property over design's `kind_values` and a name from
  `[a-z_][a-z0-9_]*`: `json_member` returns `(name, value)`, and `registry.encode` on a JSON record whose BODY `Param`
  of that `Kind` is given the value yields `json_body == {name: value}`. It imports `gitlab_api.commands.call` inside
  the test after asserting the file exists. — Files: test/test_gitlab_api_call_properties.py — Validates: AC-1.3
- [x] 2.3 TEST: N per D5 — `is_unreachable(*, path, section)`; the reference half, `reference_sections(*, rest_dir)`
  (D5's anchor rule restated, importing neither `verify.py` nor `common.Slugger`), D5's section, attribute and offering
  rules, `PAGING_PARAMETERS` and `record_problems(*, record, section)`; the call half, `sent_call(*, request)` and
  `call_problems(*, section, values, sent)`. Tests of N's own helpers, green before 2.4 by design, whose mutant for the
  verifier is N with `is_unreachable` returning `False`, `record_problems` `["mutant"]` and `call_problems` `[]`:
  `test_the_unreachable_rule_has_two_arms`, `test_a_section_is_read_as_the_reference_writes_it`,
  `test_the_method_rejects_a_call_that_differs` (D5's six cases). Other tests:
  `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents` (one
  temporary project and one fake host, every discovered REST record outside `GATED_OPERATIONS`, D5's typed values,
  answers through `FakeGitLab.script_next`), `test_an_unreachable_call_matches_its_reference_section`
  (`gitlab-dedicated#update-a-geo-site`, D5's five steps). It imports `GATED_OPERATIONS` inside the test after
  asserting `commands/call.py` exists, and runs `call` with wave 1's fx helpers. — Files:
  test/test_gitlab_wrapper_contract.py — Validates: AC-1.1, AC-3.1, AC-3.2
- [x] 2.4 IMPL: `commands/_common.py` — `EXIT_REFUSED` and `print_bytes(*, data)` (flush `sys.stdout`, then
  `sys.stdout.buffer.write`, no line end added), its module docstring naming both output forms and `EXIT_REFUSED`;
  `commands/call.py` per D1–D4 and D7 — the module docstring (D2's grammar, D3's print forms), `register(*,
  subparsers)` adding `call` with D2's options (`action="append"`, default `None`, `-f` and `-F` sharing one `dest`, no
  option string containing `token`), `assignment`, `json_member` (`parse_constant` raising `ValueError`) and
  `file_member` as argparse `type`s (`ArgumentTypeError` naming the option and the name rendered with `json.dumps`,
  never a value), `GATED_OPERATIONS` from `mr.OP_MERGE_MR` and `issue.OP_CREATE_ISSUE`, `call_values`,
  `check_parameters` (D4's one message), and `call_operation(*, transport, project, in_progress_label, args)` steps 1–6
  with D3's output, a refusal of steps 1–5 a `ValueError` logged with `logger.error` and returned as `EXIT_REFUSED`
  with nothing sent. No text `os.environ` or `getenv`; standard library only. — Files:
  src/payload/scripts/gitlab_api/commands/_common.py, src/payload/scripts/gitlab_api/commands/call.py — Validates:
  AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9, AC-2.1, AC-2.2, AC-2.3, AC-2.4, UB-2.1, UB-2.2
- [x] 2.5 IMPL: each part-1 record that N `test_every_record_matches_its_reference_section` names in this wave's red
  run, corrected to its section (D8), C staying green unedited; a module with no named record is left unedited. —
  Files: src/payload/scripts/gitlab_api/families/ (`ai_coding.py`, `create.py`, `plan.py`,
  `software_supply_chain_security.py`, `verify.py`) — Validates: AC-1.1, UB-1.1

## Wave 3 — Coverage rule and regeneration

Run: `python scripts/run_tests.py test/test_gitlab_wrapper_coverage.py test/test_gitlab_api_properties.py src/payload/test/test_gitlab_api_call.py src/payload/test/test_gitlab_wrapper_compat.py src/payload/test/test_wrapper_delivery.py`

The red capture runs the Run line before 3.2 with one mutant applied in V — `coverage_gaps` and `only_in_graphql`
return `[]`, `family_problems` and `capability_problems` return `["mutant"]` — under which every test of 3.1 fails on
its assertion. The mutant is undone by its exact inverse edit, never by `git checkout` or `git stash`; then 3.2 runs,
and the green capture runs the Run line.

- [x] 3.1 TEST: V per D6 — `family_problems(*, rows, families)`, `only_in_graphql(*, path)` and
  `capability_problems(*, capabilities, module)`. Tests: `test_a_regenerated_index_names_each_changed_key` (AC-5.3's
  five cases on a synthetic index and a `write_package` package of `SyntheticFamily`s),
  `test_every_declared_key_is_in_its_family`, `test_a_route_prefix_key_is_held_to_the_rule` (the synthetic `gamma`
  without `RELEASE_FILE` on its `PENDING`), `test_a_capability_neither_served_nor_pending_is_named`,
  `test_the_only_in_graphql_table_is_read_whole`, `test_every_graphql_only_capability_is_served_or_pending` (importing
  `gitlab_api.graphql_only` inside the test, as `registry_module` imports the registry). Existing V tests unedited. —
  Files: test/test_gitlab_wrapper_coverage.py — Validates: AC-5.3, AC-6.1, AC-6.2, AC-6.3
- [x] 3.2 IMPL: `graphql_only.py` — `PENDING_CAPABILITIES`, every first cell of the table under `### Only in GraphQL`
  in `docs/api-reference/gitlab/graphql/conventions.md`, verbatim, experimental or not; the module docstring stating
  D6's rule and that a record of a `Status: Experiment` query or mutation says so in its comment. No text `os.environ`
  or `getenv`. — Files: src/payload/scripts/gitlab_api/graphql_only.py — Validates: AC-6.2, AC-6.3, UB-2.2

## Wave 4 — Usage docstring and map

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_gitlab_wrapper_coverage.py test/test_gitlab_api_properties.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [x] 4.1 TEST: C — `test_the_usage_names_the_operation_call`: the entry script's `__doc__` holds
  `call plan#retrieve-a-project-issue`, `--path`, `--query`, `-f/--raw-field`, `-F/--field`, `--file`, `variables`,
  `JSON array`, `indented JSON`, `empty body`, `bytes unchanged` and `exit 2`. — Files:
  src/payload/test/test_gitlab_wrapper_compat.py — Validates: AC-4.1
- [x] 4.2 IMPL: the entry script's module docstring only, per D7 — the usage lines after `check-landed`, "2 a usage
  error or a refused `call`" in the "Exit codes" paragraph, and "(`commands/call.py` calls any record by its id)" in
  the last paragraph. — Files: src/payload/scripts/gitlab_wrapper.py — Validates: AC-4.1
- [x] 4.3 IMPL: the map's `src/payload/scripts/gitlab_api/` bullet per D7 — D7's sentences before its closing
  sentence, which stays last; the map under its cap. — Files: docs/forLLMConsumption.md — Validates: AC-4.2

## Final

- [x] F.1 E2E: the real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project (requirements
  § Residuals). Until it exists, `call` runs through `main`'s argv up to the API boundary in K and N, and C
  `test_script_usage_error_exits_2` (unchanged) runs the script by path, so its parser holds `call.py`; these suites run
  in the `verify` job of `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
  — Files: none
- [x] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names neither `src/payload/scripts/github_wrapper.py`, a file under `src/payload/scripts/github_api/`, a
  `src/payload/test/*github*.py` or `test/*github*.py` file, nor `src/payload/test/test_wrapper_delivery.py`, and
  `test_wrapper_delivery.py` passes in the run of every wave. — Files: none (read-only) — Validates: UB-3.1
- [x] F.3 VERIFY: that diff (`git diff origin/main...HEAD`) changes no existing line of C, of P, or of an existing test
  of R, T or V; C gains only `test_the_usage_names_the_operation_call`. The unchanged C `test_load_config_refusals` and
  `test_environment_token_ignored` and P `test_standard_library_only` pass in the run of every wave. — Files: none
  (read-only) — Validates: UB-1.1, UB-2.1, UB-2.2
- [x] F.4 VERIFY: the map's `gitlab_api/` bullet holds D7's sentences with its closing sentence last, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes in the run of wave 4. — Files: none
  (read-only) — Validates: AC-4.2

## Coverage

A criterion not listed is held by the TEST tasks whose `Validates:` names it.

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1, 2.3; design D1, D8 (approved, DL-003) |
| AC-3.1 | 2.3; design D5 (approved, DL-003) |
| AC-4.2 | F.4 |
| AC-5.1, AC-5.2 | none: criteria on design D6, met by its approval (DL-003) |
| UB-1.1 | 1.3, F.3; C on every Run line |
| UB-2.1 | 2.1, F.3 |
| UB-2.2 | F.3; P on every Run line |
| UB-3.1 | F.2 |
