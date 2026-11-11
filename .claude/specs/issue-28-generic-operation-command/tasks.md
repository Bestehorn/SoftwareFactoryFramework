# Tasks — issue #28: GitHub wrapper rewrite, part 2a (generic operation command)

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-005); nothing is added. Test files as
design § Acceptance Criteria Mapping: K = `src/payload/test/test_github_api_call.py`, R =
`src/payload/test/test_github_api_registry.py`, T = `src/payload/test/test_github_api_transport.py`, H =
`test/test_github_api_call_properties.py`, N = `test/test_github_wrapper_contract.py`, V =
`test/test_github_wrapper_coverage.py`, C = `src/payload/test/test_github_wrapper_compat.py`, P =
`test/test_github_wrapper_fork_parity.py`. Each test does what design § Correctness Properties states for its
criterion, against that oracle. In a wave the TEST tasks run first and add failing tests only, red for the right
reason — an assertion, or an exception raised inside the test body, never a collection error; the IMPL tasks then add
the minimal code that turns them green. No task edits an existing line of `CASES`, of C, of P or of an existing V test
(UB-1.1).

## Wave 1 — Registry and transport

Run: `python scripts/run_tests.py src/payload/test/test_github_api_registry.py src/payload/test/test_github_api_transport.py src/payload/test/test_github_wrapper_compat.py test/test_github_wrapper_fork_parity.py test/test_github_wrapper_coverage.py`

- [ ] 1.1 TEST: R, on its synthetic family and a `Transport` on the fake host:
  `test_send_returns_the_response_of_the_record` (`registry.send` returns the `Response`; the recorded request carries
  the record's method, the path as `expand` writes it, the decoded query, the JSON body, and the record's
  `api_version` and `accept`), `test_path_parameters_are_the_placeholders_in_order` (`registry.path_parameters` gives
  the path's `{name}` placeholders in order), `test_a_query_name_ending_in_brackets_is_sent_as_written` (`send` and
  `pages` accept `<name>[]` for a documented query name and send it as written). Existing R tests unedited. — Files:
  src/payload/test/test_github_api_registry.py — Validates: AC-1.2, AC-2.3
- [ ] 1.2 TEST: T — `test_link_pages_send_the_given_accept`: `Transport.pages` given a non-default `accept` sends it as
  `Accept` on every page of a two-page list route. — Files: src/payload/test/test_github_api_transport.py —
  Validates: AC-1.2
- [ ] 1.3 IMPL: D2's registry additions — `path_parameters` (`PATH_PARAMETER_PATTERN`), `query_name` (one trailing
  `[]` removed), `_check_names` comparing a query name through `query_name`,
  `send(transport, operation_id, *, path_params, query=None, body=None) -> Response`, `call` as `send(...).json()`,
  `pages` passing `accept=operation.accept`; and `Transport.pages` and `_page_items` taking
  `accept: str = ACCEPT_JSON`, sent on every page, every existing caller on the default. — Files:
  src/payload/scripts/github_api/registry.py, src/payload/scripts/github_api/transport.py — Validates: AC-1.2, AC-2.3

## Wave 2 — The `call` command

Run: `python scripts/run_tests.py src/payload/test/test_github_api_call.py src/payload/test/test_github_api_registry.py src/payload/test/test_github_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_github_wrapper_coverage.py test/test_github_wrapper_fork_parity.py test/test_github_api_call_properties.py test/test_github_wrapper_contract.py`

- [ ] 2.1 TEST: the fixtures module gains `PRODUCT_SCRIPT` and `run_product_case(*, case, root, monkeypatch, capsys)`
  per D8 (enters the project, runs the product's `main(argv=...)`, a `SystemExit` giving its code, calls
  `assert_outcome` and `assert_every_request_routed`, returns the recorded requests); `CASES` untouched. K:
  `CALL_CASES`, `GoldenCase` rows with argv `call …` run with `fx.run_product_case` against the fixture project
  (`origin` `o/r`); refusals judged by `assert_outcome` (no request for exit 2) and by `fx.assert_log` on
  `caplog.records`, each refusal row's `log` the `LogExpectation` that design § Correctness Properties names for it
  (`run_product_case` does not call `assert_log`); non-JSON bodies read with `capsysbinary`. Tests:
  `test_a_gated_operation_names_its_subcommand`, `test_an_operation_call_sends_its_record` (its two rows on
  `dataclasses.replace` copies of `issues/get` and `issues/list-comments` with `API_VERSION_NEXT` and
  `application/vnd.github.full+json`, set into `github_api.families.issues.OPERATIONS` with `monkeypatch.setattr`),
  `test_a_body_member_holds_the_given_json_value`, `test_a_list_prints_every_page_as_one_array`,
  `test_a_json_or_empty_body_prints_as_documented`, `test_a_body_that_is_not_json_is_written_unchanged`,
  `test_an_api_error_exits_1_with_its_details`, `test_an_unknown_operation_is_refused`,
  `test_an_undocumented_parameter_is_refused`, `test_a_missing_path_parameter_is_refused`. — Files:
  src/payload/test/github_wrapper_fixtures.py, src/payload/test/test_github_api_call.py — Validates: AC-1.1, AC-1.2,
  AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-2.1, AC-2.2, AC-2.3
- [ ] 2.2 TEST: H — a `scripts_on_path` fixture putting `src/payload/scripts` on `sys.path` as V does, applied with
  `@pytest.mark.usefixtures("scripts_on_path")`; `test_any_json_value_becomes_the_body_member`, AC-1.3's property over
  design's `json_values` strategy and a name from `[a-z_][a-z0-9_]*`, with `body_of(members=[])` `None`. It imports
  `github_api.commands.call` inside the test after asserting the file exists, as V's `_import_package_module` does, so
  a missing `call.py` is red on an assertion. — Files: test/test_github_api_call_properties.py — Validates: AC-1.3
- [ ] 2.3 TEST: N per D5 — `is_unreachable(operation_id, path)`; the reference half, `reference_sections(rest_dir)`
  (each `rest/<category>.md` read once, sections keyed by operation ID, D5's row rules for path, query and body names)
  and `record_problems(record, section)`; the call half, `CallShape(method, path, query_names, body_names)`,
  `expected_call(section, values)`, `sent_call(request)` and `call_problems(expected, sent)`. Tests:
  `test_a_section_is_read_as_the_reference_writes_it` (D5's five sections),
  `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents` (one
  temporary project and one fake host, every discovered record outside `GATED_OPERATIONS`),
  `test_an_unreachable_call_matches_its_reference_section` (`billing/update-budget-org`, D5's five steps, and AC-3.1's
  `is_unreachable` examples), `test_the_method_rejects_a_call_that_differs` (D5's five cases). It imports
  `GATED_OPERATIONS` inside the test after asserting the file exists, as 2.2 does; it builds its project with
  `fx.enter_project` and loads the entry script with `fx.load_script`, as C does, not with `run_product_case`, which
  2.1 writes in the same wave. — Files: test/test_github_wrapper_contract.py — Validates: AC-1.1, AC-3.1, AC-3.2
- [ ] 2.4 IMPL: `commands/_common.py` — `EXIT_REFUSED` (2) and `print_bytes` (flush `sys.stdout`, then
  `sys.stdout.buffer.write`, no line end added); `commands/call.py` per D2–D4 and D7 — the module docstring (D2's
  grammar, D3's print forms), `register(subparsers)` adding `call` with D2's options (`action="append"`, default
  `None`, `--raw-field` and `--field` sharing one `dest`, no option string containing `token`), `assignment` and
  `json_member` as argparse `type`s (`ArgumentTypeError` naming the option and the name rendered with `json.dumps`,
  never a value), `GATED_OPERATIONS`, `body_of`, D4's check, and `cmd_call(*, transport, owner, repo, args)` steps 1–7
  with D3's output, a refusal of steps 1–4 a `ValueError` logged with `logger.error` and returned as `EXIT_REFUSED`
  with nothing sent. No word `environ` or `getenv`; standard library only. — Files:
  src/payload/scripts/github_api/commands/_common.py, src/payload/scripts/github_api/commands/call.py — Validates:
  AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-2.1, AC-2.2, AC-2.3, UB-2.1, UB-2.2

## Wave 3 — Regeneration test

Run: `python scripts/run_tests.py test/test_github_wrapper_coverage.py`

This wave adds one test of #17's existing coverage checks (D6), so it has no IMPL task. Its red capture runs the Run
line with mutant M3 applied — `coverage_gaps` and `_family_problems` in V return `[]`, so every case of 3.1 fails —
and M3 is undone by its exact inverse edit, never by `git checkout` or `git stash`, which would discard the uncommitted
3.1 test; its green capture runs the Run line on the restored file.

- [ ] 3.1 TEST: V — `test_a_regenerated_index_names_each_changed_id`, parametrized on a synthetic index and a synthetic
  family module (a `types.ModuleType` with `FAMILY`, `OPERATIONS` and `PENDING`) over AC-5.3's cases: an added ID
  returned by `coverage_gaps`; a pending ID and a record ID the index lacks, a record whose row has another path, and
  one whose row has another method and the same path, each named by `_family_problems`. Existing V tests unedited. —
  Files: test/test_github_wrapper_coverage.py — Validates: AC-5.3

## Wave 4 — Usage docstring and map

Run: `python scripts/run_tests.py src/payload/test/test_github_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_github_wrapper_fork_parity.py test/test_github_wrapper_coverage.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [ ] 4.1 TEST: C — `test_the_usage_names_the_operation_call`: the entry script's `__doc__` holds `call issues/get`,
  `--path`, `--query`, `-f/--raw-field`, `-F/--field`, `JSON array`, `indented JSON`, `bytes unchanged` and `exit 2`;
  no existing C test edited. — Files: src/payload/test/test_github_wrapper_compat.py — Validates: AC-4.1
- [ ] 4.2 IMPL: the entry script's module docstring only, per D7 — the usage lines after `check-landed`,
  `commands/call.py` in the "Layout" paragraph, and its last sentence naming a refused `call` among the exit-2 cases.
  — Files: src/payload/scripts/github_wrapper.py — Validates: AC-4.1
- [ ] 4.3 IMPL: the map's `src/payload/scripts/github_api/` bullet per D7 — the `call` sentences before its closing
  sentence, which stays last and becomes D7's; the map under its cap. — Files: docs/forLLMConsumption.md — Validates:
  AC-4.2

## Final

- [ ] F.1 E2E: the real-forge run is #10's fixture on an ephemeral `sff-test-*` repository (requirements § Residuals).
  Until it exists, `call` runs through `main`'s argv up to the API boundary in K and N, and the entry script loads
  `commands/call.py` by path in C `test_the_script_runs_by_path` (unchanged), in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names neither `src/payload/scripts/gitlab_wrapper.py` nor `src/payload/test/test_wrapper_delivery.py`, and
  `test_wrapper_delivery.py` passes in the runs of waves 2 and 4. — Files: none (read-only) — Validates: UB-3.1
- [ ] F.3 VERIFY: that diff (`git diff origin/main...HEAD`) changes no existing line of `CASES`, of C or of P; C gains
  only `test_the_usage_names_the_operation_call` and V only `test_a_regenerated_index_names_each_changed_id`. The
  unchanged C `test_a_subcommand_matches_its_golden_case` and `test_the_credential_comes_only_from_the_file`, P
  `test_the_fork_produces_the_golden_case` and `test_the_parsers_match_option_by_option`, and V
  `test_the_wrapper_imports_only_the_standard_library` pass in the runs of waves 2 and 4. — Files: none (read-only) —
  Validates: UB-1.1, UB-2.1, UB-2.2
- [ ] F.4 VERIFY: the map's `github_api/` bullet holds D7's `call` sentences with its closing sentence last, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes in the run of wave 4. — Files: none
  (read-only) — Validates: AC-4.2

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1, 2.3; design D1, D8 (approved, DL-005) |
| AC-1.2 | 1.1, 1.2, 2.1 |
| AC-1.3 | 2.1, 2.2 |
| AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-2.1, AC-2.2 | 2.1 |
| AC-2.3 | 1.1, 2.1 |
| AC-3.1 | 2.3; design D5 (approved, DL-005) |
| AC-3.2 | 2.3 |
| AC-4.1 | 4.1 |
| AC-4.2 | F.4 |
| AC-5.1, AC-5.2 | none: criteria on `design.md` D6, met by its approval (DL-005) |
| AC-5.3 | 3.1 |
| UB-1.1, UB-2.1, UB-2.2 | F.3 |
| UB-3.1 | F.2 |
