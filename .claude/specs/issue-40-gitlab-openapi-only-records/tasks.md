# Tasks — issue #40: GitLab wrapper rewrite, part 2 slice: the OpenAPI-only operations

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved); nothing is added. Test files as design
§ Acceptance Criteria Mapping: F = `src/payload/test/test_gitlab_api_openapi_only.py` (new), G =
`src/payload/test/test_gitlab_api_deploy.py` (new), R = `src/payload/test/test_gitlab_api_registry.py`, K =
`src/payload/test/test_gitlab_api_call.py`, T = `src/payload/test/test_gitlab_api_transport.py`, C =
`src/payload/test/test_gitlab_wrapper_compat.py`, P = `test/test_gitlab_api_properties.py`, N =
`test/test_gitlab_wrapper_contract.py`, V = `test/test_gitlab_wrapper_coverage.py`; H =
`test/test_gitlab_api_call_properties.py` and the family suites `src/payload/test/test_gitlab_api_no_stage_assigned.py`,
`test_gitlab_api_plan.py` and `test_gitlab_api_verify.py` run as regression; fx =
`src/payload/test/gitlab_wrapper_fixtures.py`. Each test does what design § Correctness Properties states for its
criterion, with its cases, against that oracle. In a wave the TEST tasks run first and add failing tests, red for the
right reason — an assertion, or an exception raised inside the test body (an `AttributeError` or `TypeError` on what is
not yet written), never a collection error: F and G load fx by path and import `gitlab_api` modules inside each test as
`test_gitlab_api_no_stage_assigned.py` does, and R, T, K, P and N keep their own import rule. A product name this
change adds (`required_placeholders`, `content_type`, `request_raw`, `--input`) appears only inside a function body, and
a parametrized test runs over literal constants, never over a record tuple. The IMPL tasks then add the minimal code
that turns them green, standard library only and reading no environment (UB-2). No task edits fx, V, C,
`commands/_common.py` or a `commands/` module other than `call.py`, nor an existing test function or assertion (D7
"Not edited"; UB-1, UB-4).

## Wave 1 — The path forms and the raw send in the registry and the transport

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_registry.py src/payload/test/test_gitlab_api_transport.py test/test_gitlab_api_properties.py test/test_gitlab_wrapper_contract.py src/payload/test/test_gitlab_api_call.py src/payload/test/test_gitlab_wrapper_compat.py test/test_gitlab_api_call_properties.py src/payload/test/test_gitlab_api_no_stage_assigned.py src/payload/test/test_gitlab_api_plan.py src/payload/test/test_gitlab_api_verify.py`

- [ ] 1.1 TEST: R — `test_placeholders_name_every_path_form`, `test_a_glob_value_keeps_its_slashes`,
  `test_a_glob_part_that_is_no_segment_is_refused`, `test_an_optional_group_is_written_only_when_given`,
  `test_an_escaped_parenthesis_is_sent_without_its_backslash` and `test_send_sends_a_raw_record_its_bytes`, on
  synthetic records as R builds them. Red: `placeholders` names no `*name`, `expand` leaves `*name`, `(` and `\(` in
  the path and refuses no glob part (assertions), `registry.required_placeholders` does not exist (`AttributeError`),
  and `RestOperation` takes no `content_type` (`TypeError`). — Files: src/payload/test/test_gitlab_api_registry.py —
  Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-3.2
- [ ] 1.2 TEST: T — `test_a_raw_body_is_sent_unchanged`, parametrized over T's `TOKEN_TYPES`. Red: `Transport` has no
  `request_raw` (`AttributeError`). — Files: src/payload/test/test_gitlab_api_transport.py — Validates: AC-3.2
- [ ] 1.3 TEST: P — the properties `test_glob_value_keeps_each_slash` (`@example(parts=["1.0", "rc 1"])`) and
  `test_a_glob_value_with_a_refused_part_is_refused`, each `@settings(deadline=None)`, and the module docstring's
  sentence naming them. Red: `expand` leaves `*glob` in the path and raises for no part (assertions). — Files:
  test/test_gitlab_api_properties.py — Validates: AC-2.1, AC-2.2
- [ ] 1.4 TEST: N per D3 and D5 — `PATH_PLACEHOLDER` with the sigil `[:*]` in a `sigil` group; `glob_names(*, path)`;
  `expanded_path` dropping each unescaped `(` and `)`, then the backslash of each `\(` and `\)`, then writing each
  `:name` and `*name`; `record_problems`' rule for a row the record lacks skipping a name of `glob_names`;
  `RAW_BODY_ROW` and `documented_raw_body(*, section, record)`, read by `record_problems` and by `sent_record_problems`
  before `documented_paging`; the docstrings of `expanded_path` and `route_problems` and the module docstring naming
  the forms; and `test_a_path_form_is_read_and_sent_as_written`, its records built in the test. Red: until 1.5, the
  new test's raw-body record raises `TypeError` on `content_type`, and its other `record_problems` cases and N's
  existing record tests raise `AttributeError` on `content_type` inside `documented_raw_body`. — Files:
  test/test_gitlab_wrapper_contract.py — Validates: AC-1.3, AC-1.4, AC-3.3
- [ ] 1.5 IMPL: `registry.py` per D1 and D5 — `PLACEHOLDER` with its `sigil` group and the constants `GROUP_SIGIL`,
  `GLOB_SIGIL`, `GLOB_SEPARATOR`, `OPTIONAL_GROUP`, `GROUP_INNER`, `ESCAPED_PARENTHESIS` and `GROUP_PARENTHESIS`;
  `required_placeholders(*, path)`; `_glob(*, name, values)`; `expand`'s three steps; `RestOperation.content_type:
  Optional[str] = None` after `fixed`; `send` taking `data: Optional[bytes] = None`, a record with no `content_type`
  sent through `transport.request` as now (refusing a `data` value with `ValueError`, nothing sent), any other
  through `transport.request_raw`; the module docstring's `expand` and `send` bullets and the docstrings of
  `placeholders`, `expand` and `send`. The bodies of `placeholders`, `_segment`, `call` and `pages` unchanged. —
  Files: src/payload/scripts/gitlab_api/registry.py — Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-3.2, UB-4
- [ ] 1.6 IMPL: `Transport.request_raw(*, method, path, query=None, data=None, content_type)` per D5 — the URL from
  `_rest_url`, then `_send` with `data` unchanged and `content_type`; the module docstring's body bullet naming it.
  Nothing else of the module changes. — Files: src/payload/scripts/gitlab_api/transport.py — Validates: AC-3.2

## Wave 2 — The records and the call

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_openapi_only.py src/payload/test/test_gitlab_api_deploy.py src/payload/test/test_gitlab_api_call.py test/test_gitlab_wrapper_contract.py test/test_gitlab_wrapper_coverage.py src/payload/test/test_gitlab_api_registry.py src/payload/test/test_gitlab_api_transport.py test/test_gitlab_api_properties.py src/payload/test/test_gitlab_wrapper_compat.py test/test_gitlab_api_call_properties.py src/payload/test/test_gitlab_api_no_stage_assigned.py src/payload/test/test_gitlab_api_plan.py src/payload/test/test_gitlab_api_verify.py`

- [ ] 2.1 TEST: F per D6 — built as `test_gitlab_api_no_stage_assigned.py` is: fx's fake host and socket guard
  autouse, `config/gitlab.json` in `tmp_path`, each call `main(argv=["call", …])` through `fx.run_main`; D6's literal
  tables (`OPERATION_IDS`, `KINDS`, `REQUIRED`, `RAW_BODIES`). Tests: `test_nothing_is_pending`,
  `test_every_param_is_typed_as_its_row`, `test_no_param_names_a_path_parameter`,
  `test_only_the_list_records_are_paged`, `test_a_list_record_prints_every_page`,
  `test_a_path_form_is_sent_as_the_route_declares`,
  `test_a_glob_part_that_is_no_segment_sends_nothing`, `test_the_job_artifacts_upload_sends_the_file_as_its_part`,
  `test_a_raw_upload_sends_the_bytes_as_its_body` and `test_a_token_attribute_is_the_value_given`. Red: `OPERATIONS`
  is empty and `PENDING` full, so each table test fails its assertion, and `registry.lookup` refuses every
  `openapi-only#` ID (exit 2), failing each call's exit-code or request assertion. — Files:
  src/payload/test/test_gitlab_api_openapi_only.py — Validates: AC-1.1, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-2.1,
  AC-2.2, AC-2.3, AC-2.5, AC-2.6, AC-3.1, AC-3.2, AC-3.4, UB-2
- [ ] 2.2 TEST: G per D6, built as F — `test_nothing_is_pending`, `test_no_record_declares_an_openapi_only_model_id`,
  `test_every_param_is_typed_as_its_row`, `test_the_optional_group_is_sent_only_when_given` and
  `test_the_upload_sends_the_bytes_as_its_body` (`sys.stdin` monkeypatched to
  `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=<the bytes>))`). Red: `deploy.OPERATIONS` is empty and `PENDING`
  full, so the table tests fail their assertions and each call exits 2;
  `test_no_record_declares_an_openapi_only_model_id` pins an absence and passes on both runs, its mutant an
  `openapi_only.OPERATIONS` record with the ID `openapi-only#download-an-ml_model-package-file`. — Files:
  src/payload/test/test_gitlab_api_deploy.py — Validates: AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-2.3, AC-2.6,
  AC-3.2
- [ ] 2.3 TEST: K — `test_a_missing_path_parameter_is_refused_unless_optional` (its AC-2.3 and AC-2.4 cases) and
  `test_a_raw_body_the_call_cannot_send_is_refused` (its cases, `graphql#syntheticProject` installed as K installs
  it). Red: `registry.lookup` refuses the `openapi-only#` IDs and argparse refuses `--input` as unrecognized, so each
  case fails on its log-record or standard-error assertion. — Files: src/payload/test/test_gitlab_api_call.py —
  Validates: AC-2.3, AC-2.4, AC-3.2
- [ ] 2.4 IMPL: `families/openapi_only.py` per D4 — `OPERATIONS: Tuple[RestOperation, ...]`, one record per key of
  today's `PENDING` in the page order of `rest/openapi-only.md`, each under a comment naming its `##` and `###`
  headings and written by D4's table, the raw-body records with `content_type=CONTENT_TYPE_OCTET_STREAM` imported from
  `gitlab_api.transport`; `PENDING: FrozenSet[Tuple[str, str]] = frozenset()`; the module docstring stating D4's rules
  in prose, that the `ml_models` file keys are `deploy`'s, and which uploads take `--file` and which `--input`. —
  Files: src/payload/scripts/gitlab_api/families/openapi_only.py — Validates: AC-1.1, AC-1.3, AC-1.4, AC-1.5, AC-1.6,
  AC-3.2
- [ ] 2.5 IMPL: `families/deploy.py` per D4 — `deploy#authorize-the-upload`,
  `deploy#download-a-machine-learning-model-package-file` and `deploy#send-the-file` (with `content_type`), none with a
  `Param`; `OPERATIONS` and `PENDING` typed as in 2.4, `PENDING` empty; the module docstring. — Files:
  src/payload/scripts/gitlab_api/families/deploy.py — Validates: AC-1.2, AC-1.3, AC-1.6, AC-3.2
- [ ] 2.6 IMPL: `commands/call.py` per D2 and D5 — `missing_path_parameters` reading `registry.required_placeholders`,
  with its docstring; `OPTION_INPUT`, `ARG_RAW_BODY`, `METAVAR_FILE` and `STDIN_INPUT`; `read_input(text)` as the
  `--input` option's `type`, default `None`; `refuse_both_bodies` first and `refuse_raw_body` after `registry.lookup`
  in `prepare_call`, each with D5's message; `PreparedCall.raw_body`, which `send_call` passes to `registry.send` as
  `data`; the module docstring's grammar, `--path` and `--input` bullets, refusal paragraph and `GitLabAPIError` list
  as D2 and D5 word them. No option string holds `token`; `GATED_OPERATIONS` and every other function unchanged. —
  Files: src/payload/scripts/gitlab_api/commands/call.py — Validates: AC-2.3, AC-2.4, AC-3.2, UB-2, UB-4

## Wave 3 — Usage docstring, map and ledger

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_compat.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [ ] 3.1 IMPL: the entry script's module docstring only, per D5 — its `call` usage lines name `--input FILE`, every
  text of C's `USAGE_CALL_TEXTS` kept (C `test_the_usage_names_the_operation_call`). — Files:
  src/payload/scripts/gitlab_wrapper.py — Validates: UB-1
- [ ] 3.2 IMPL: the map's `src/payload/scripts/gitlab_api/` bullet per D5 — its option list names `--input`; "Not
  installed here" stays last; the map under its cap (`test_llm_map_within_cap`). — Files: docs/forLLMConsumption.md —
  Validates: none (D5 documentation)
- [ ] 3.3 IMPL: the Residuals' rows per D7 — one per requirements Residual, one for the token-revoking records and one
  for each secrets residual of design § Residuals, each written with `python scripts/memory_compile.py ledger add`. —
  Files: docs/findings-ledger.md — Validates: design § Residuals (D7)

## Final

- [ ] F.1 E2E: the real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project (requirements
  "Out of scope"). Until it exists, N calls every record of this change, and F and G the path forms, lists and
  uploads, through `main`'s argv against the fake host up to the API boundary, in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`); for a `/admin/`,
  `/geo/` or `/hooks/` record N's two record tests are the whole proof (AC-3.3). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names no file of UB-3, and `src/payload/test/test_github_api_*.py` and `src/payload/test/test_wrapper_delivery.py`
  pass in CI's `tests` leg on the pushed SHA. — Files: none (read-only) — Validates: UB-3
- [ ] F.3 VERIFY: outside the spec directory, that diff names only D7's files; it changes no line of fx, V, C or
  `commands/_common.py`, no `commands/` module but `call.py`, no existing test function or assertion, and no
  `GATED_OPERATIONS` entry. C `test_load_config_refusals` and `test_environment_token_ignored`, K
  `test_call_takes_no_token_option`, `test_a_gated_operation_names_its_subcommand` and
  `test_a_missing_path_parameter_is_refused`, R `test_project_path_is_encoded` and
  `test_empty_and_dot_segments_are_refused`, P `test_path_value_is_one_segment` and `test_standard_library_only`, and
  N's and V's existing tests pass in the run of every wave that names them. — Files: none (read-only) — Validates:
  UB-1, UB-2, UB-4

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1; V `test_every_declared_key_is_in_its_family` on wave 2's Run line |
| AC-1.2 | 2.2 |
| AC-1.3 | 1.4, 2.1, 2.2; N `test_every_record_matches_its_reference_section` on wave 2's Run line |
| AC-1.4 | 1.4, 2.1, 2.2 |
| AC-1.5 | 2.1, 2.2 |
| AC-1.6 | 2.1, 2.2; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` on wave 2's Run line |
| AC-2.1, AC-2.2 | 1.1, 1.3, 2.1 |
| AC-2.3 | 1.1, 2.1, 2.2, 2.3 |
| AC-2.4 | 1.1, 2.3 |
| AC-2.5 | 1.1, 2.1 |
| AC-2.6 | 2.1, 2.2 |
| AC-3.1 | 2.1; N `test_every_record_is_sent_as_its_section_documents` on wave 2's Run line; K's existing tests on waves 1 and 2 |
| AC-3.2 | 1.1, 1.2, 2.1, 2.2, 2.3 |
| AC-3.3 | 1.4; N's two record tests on wave 2's Run line |
| AC-3.4 | 2.1 |
| UB-1 | F.3; C on every Run line |
| UB-2 | 2.1, F.3; P `test_standard_library_only` on the Run lines of waves 1 and 2 |
| UB-3 | F.2 |
| UB-4 | F.3; R, P, K, N and the family suites on the Run lines of waves 1 and 2, V on wave 2's |
