# Tasks — issue #44: GitLab wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved); nothing is added. Test files as design
§ Acceptance Criteria Mapping (H: § Testing Strategy): G = `src/payload/test/test_gitlab_api_graphql_only.py` (new), R =
`src/payload/test/test_gitlab_api_registry.py`, T = `src/payload/test/test_gitlab_api_transport.py`, Q =
`test/test_gitlab_graphql_contract.py` (new), V = `test/test_gitlab_wrapper_coverage.py`, K =
`src/payload/test/test_gitlab_api_call.py`, N = `test/test_gitlab_wrapper_contract.py`, C =
`src/payload/test/test_gitlab_wrapper_compat.py`, P = `test/test_gitlab_api_properties.py`, H =
`test/test_gitlab_api_call_properties.py`; fx = `src/payload/test/gitlab_wrapper_fixtures.py`. Each test does what
design § Correctness Properties states for its criterion, with its cases, against that oracle. In a wave the TEST tasks
run first and add failing tests, red for the right reason — an assertion, or an exception raised inside the test body
(an `AttributeError` or `TypeError` on what is not yet written), never a collection error: G loads fx by path and
imports `gitlab_api` modules inside each test as R does, Q as N does (`src/payload/scripts` on `sys.path` and an import
that asserts the module file exists first), and G and Q parametrize over constants only. The IMPL tasks then add the
minimal code that turns them green, standard library only and with no text `os.environ` or `getenv` (UB-2.2). No
task edits fx, V, K, N, C, P, H, `families/`, `commands/_common.py`, or an existing R or T test (D9).

## Wave 1 — Uploads in the registry and the transport

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_registry.py src/payload/test/test_gitlab_api_transport.py src/payload/test/test_gitlab_api_call.py src/payload/test/test_gitlab_wrapper_compat.py test/test_gitlab_wrapper_contract.py test/test_gitlab_api_properties.py test/test_gitlab_api_call_properties.py`

- [ ] 1.1 TEST: R — `test_upload_variables_are_the_documents_upload_definitions`, on `GraphQLOperation`s built in the
  test (`$files : [Upload!]!` found and a list, `$file: Upload` found and not a list, `$n: [Int!]` not found), and
  `test_split_uploads_puts_null_where_each_file_goes` (`variables.files.0`, `variables.files.1`, `variables.file`, in
  order, each value `None`). Red: neither `registry.upload_variables` nor `registry.split_uploads` exists. — Files:
  src/payload/test/test_gitlab_api_registry.py — Validates: AC-3.1
- [ ] 1.2 TEST: T — `test_graphql_sends_files_as_one_multipart_request`: `Transport.graphql` given `files`, each pair an
  operations path and a file in `tmp_path`, sends AC-3.1's parts in D4's order; a `job` token raises before the file
  is read. Red: `Transport.graphql` takes no `files` (`TypeError`). — Files:
  src/payload/test/test_gitlab_api_transport.py — Validates: AC-3.1
- [ ] 1.3 IMPL: `registry.py` per D4 and D8 — `upload_variables(*, operation) -> Dict[str, bool]` (each declared
  variable whose type, with `[`, `]`, `!` and white space removed, is `Upload`, mapped to whether the type begins with
  `[`; the types read from the `$name: Type` definitions where `variables` reads the names) and
  `split_uploads(*, values) -> Tuple[Dict[str, Any], Tuple[Tuple[str, Path], ...]]` (each `Path` value and each `Path`
  item of a list replaced by `None`; the files in that order, each with the operations path it fills,
  `variables.<name>` or `variables.<name>.<index>`); the module docstring naming both, and it and `GraphQLOperation`'s
  saying that a record is one query or mutation of a capability and that several records may serve one capability.
  Every existing function unchanged. — Files: src/payload/scripts/gitlab_api/registry.py — Validates: AC-3.1
- [ ] 1.4 IMPL: `Transport.graphql` per D4 — `files: Sequence[Tuple[str, Path]] = ()`, each pair an operations path and
  its file. Without files, the JSON body it sends now; with files, the body and `Content-Type` that
  `request_body(form=..., json_body=None, files=...)` returns for the form pairs `operations` (`json.dumps` of
  `{"query": document, "variables": variables}`) and `map` (`json.dumps` of each part name `str(i)` mapped to a list
  holding the i-th file's operations path) and the files under the part names `str(i)`. The job-token refusal stays
  ahead of the body; `Authorization: Bearer`, the URL, `_send` and the reading of `data` and `errors` unchanged; the
  module docstring names the multipart GraphQL request. Nothing else of the module changes. — Files:
  src/payload/scripts/gitlab_api/transport.py — Validates: AC-3.1

## Wave 2 — The records, the call and the contract

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_graphql_only.py test/test_gitlab_graphql_contract.py test/test_gitlab_wrapper_coverage.py src/payload/test/test_gitlab_api_registry.py src/payload/test/test_gitlab_api_transport.py src/payload/test/test_gitlab_api_call.py src/payload/test/test_gitlab_wrapper_compat.py test/test_gitlab_wrapper_contract.py test/test_gitlab_api_properties.py test/test_gitlab_api_call_properties.py`

- [ ] 2.1 TEST: Q per D7, reading `docs/api-reference/gitlab/graphql/` — `reference_schema(*, graphql_dir)`,
  `read_document(*, document)`, `document_problems(*, record, schema)`, `selected_members(*, record, schema)`,
  `row_members(*, conventions)` and `member_problems(*, row, records, schema)`, each by D7's rules, the records found by
  iterating `graphql_only.OPERATIONS`. Tests: `test_the_reference_is_read_as_written` (its examples),
  `test_every_record_matches_the_reference` (failing on an empty `OPERATIONS`),
  `test_the_method_rejects_a_document_that_differs` (its cases, each a record ID and a change, the
  `dataclasses.replace` copy made inside the test), `test_every_capability_has_a_record`,
  `test_every_member_a_row_names_is_selected` (a failure names the row and the member; failing when the capabilities
  of `row_members` differ from the table's first cells or a row has no member). Red: with `OPERATIONS` empty and
  `PENDING_CAPABILITIES` full, each test fails inside its body — no record, a pending capability, a member no record
  selects, no record for a case's or an example's ID. — Files: test/test_gitlab_graphql_contract.py — Validates:
  AC-1.1, AC-1.2, AC-1.3, AC-4.1
- [ ] 2.2 TEST: G per D7 — fx's socket guard and `FakeGitLab` installed for every test, as R does; every call runs
  the product's `main` through `fx.write_config`, `fx.load_wrapper` and `fx.run_main`, as K's `run_call` does, each
  answer queued with `script_next`; a refusal read from its `caplog` record, a multipart body with
  `email.parser.BytesParser`, its `Content-Type` header prefixed, as N's `sent_call` does; D6's two IDs the module
  constant `REFUSED_IDS`. Tests, each with its cases: `test_every_record_is_called_through_main` (D7's argv, answers
  and oracle; failing when it calls no record), `test_every_record_id_is_looked_up_once`,
  `test_a_variable_holds_the_given_json_value`, `test_a_work_item_list_prints_every_node`,
  `test_a_graphql_failure_exits_1_with_its_details`, `test_a_design_upload_sends_each_file_as_a_part`,
  `test_a_refused_mutation_sends_nothing` (over `REFUSED_IDS`; failing when an ID names no record) and
  `test_a_file_for_a_variable_that_is_no_upload_is_refused`. Red: `registry.lookup` refuses every `graphql#` ID as one
  no record declares (exit 2), so each test fails on its exit-code, request, output or log assertion, or on finding no
  record. — Files: src/payload/test/test_gitlab_api_graphql_only.py — Validates: AC-1.4, AC-2.1, AC-2.2, AC-2.3,
  AC-2.4, AC-2.5, AC-3.1, AC-3.2, AC-4.1, AC-4.2, AC-4.3, UB-1.2
- [ ] 2.3 IMPL: `graphql_only.py` per D1, D2 and D6 — `OPERATIONS` holding D1's query records, each with its
  `connection`, and its mutation records: the `$input` shape (`<I>` the input type of the mutation's signature line),
  or for `graphql#designManagementUpload`, `graphql#pipelineCreate` (with `async: true`) and
  `graphql#workItemsCsvImport` the input object written into the document, each selecting `errors` beside D1's
  selection; every `capability` its row's first cell verbatim, every ID `graphql#<member>`, and a record whose
  reference section carries `Notes: experiment` or `Notes: **deprecated**` saying so in its comment;
  `OP_WORK_ITEM_CREATE` and `OP_WORK_ITEMS_CSV_IMPORT`; `PENDING_CAPABILITIES = frozenset()`; the module docstring
  stating the ID scheme, the query and the two mutation shapes, that a refused record is declared but never sent, and
  D1's comment rule (D8). — Files: src/payload/scripts/gitlab_api/graphql_only.py — Validates: AC-1.1, AC-1.2,
  AC-1.3, AC-1.4, AC-2.5, AC-4.1
- [ ] 2.4 IMPL: `commands/call.py` per D3, D4 and D6 — `GATED_OPERATIONS` becomes `Mapping[str, Optional[str]]`,
  mapping `graphql_only.OP_WORK_ITEM_CREATE` and `graphql_only.OP_WORK_ITEMS_CSV_IMPORT` (written by 2.3 in this wave;
  2.4 does not edit `graphql_only.py`) to `None`, its two entries as they are, its comment naming its class: a record
  that commits to or merges into a branch, or that creates an issue or another work item; `refuse_gated` testing
  membership, raising for `None` a `ValueError` ending ": no subcommand sends it" and for a subcommand today's message,
  unchanged; `documented_names` giving a GraphQL record's `ARG_FILES` the names of `registry.upload_variables`;
  `call_values` adding a GraphQL record's `--file` values after its `-f`/`-F` values — every `Path` of a name
  `upload_variables` maps to `True`, as a list in command-line order, else the last `Path` given, a name outside
  `upload_variables` included. The module docstring names a GraphQL record's `--file` and the "no subcommand sends it"
  refusal. No option added; the REST steps unchanged. — Files: src/payload/scripts/gitlab_api/commands/call.py —
  Validates: AC-3.1, AC-3.2, AC-4.1, AC-4.2, UB-1.2, UB-2.1
- [ ] 2.5 IMPL: `registry.call` per D4 — a GraphQL record without a `connection` sent as
  `transport.graphql(document=..., variables=..., files=...)` from `split_uploads(values=...)`; a record with a
  `connection` as now. Nothing else of the module changes. — Files: src/payload/scripts/gitlab_api/registry.py —
  Validates: AC-2.3, AC-3.1, AC-3.2

## Wave 3 — Usage docstring and map

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_api_graphql_only.py test/test_gitlab_graphql_contract.py src/payload/test/test_gitlab_wrapper_compat.py test/test_gitlab_api_properties.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [ ] 3.1 TEST: G — `test_the_usage_names_every_graphql_record`: the `__doc__` of the entry script, loaded with
  `fx.load_wrapper`, read within its GraphQL entry (the `call graphql#` usage line and the `#` lines under it), its
  lines joined with one space, each stripped of its indentation and `#`, holds every capability of
  `graphql_only.OPERATIONS` followed by the IDs of its records before the next capability, each ID matched whole (not
  followed by a letter, digit or `_`, nor by `.` and a letter); `-f NAME=TEXT`, `-F NAME=JSON`, `--file NAME=PATH`,
  `JSON array`, `data` and `exit 2`; and each ID of `REFUSED_IDS`. It fails when `OPERATIONS` holds no record. Red: the
  docstring has no `call graphql#` line. — Files: src/payload/test/test_gitlab_api_graphql_only.py — Validates: AC-5.1
- [ ] 3.2 TEST: Q — `test_the_map_names_the_graphql_call`: the `src/payload/scripts/gitlab_api/` bullet of
  `docs/forLLMConsumption.md` holds `call graphql#`, `--file NAME=PATH` and `Upload`. Red: the bullet holds none of
  them. — Files: test/test_gitlab_graphql_contract.py — Validates: AC-5.2
- [ ] 3.3 IMPL: the entry script's module docstring only, per D8 — D8's lines after the
  `call plan#retrieve-a-project-issue` entry, one capability line per capability in the table's order (`#   `, the
  capability verbatim, `:`, the IDs of its records), wrapped onto `#     ` lines at 120 columns. — Files:
  src/payload/scripts/gitlab_wrapper.py — Validates: AC-5.1
- [ ] 3.4 IMPL: the map's `src/payload/scripts/gitlab_api/` bullet per D8 — D8's sentences before "Not installed
  here", which stays last; the map under its cap. — Files: docs/forLLMConsumption.md — Validates: AC-5.2

## Final

- [ ] F.1 E2E: the real-instance check is #11's fixture on an ephemeral `sff-test-*` project (requirements "Out of
  scope"; design D7 names the records it cannot exercise). Until it exists, G runs every GraphQL call through `main`'s
  argv up to the API boundary and Q proves every document against the reference, in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names no file of UB-3.1, and their suites pass in CI's `tests` leg on the pushed SHA. — Files: none (read-only) —
  Validates: UB-3.1
- [ ] F.3 VERIFY: outside the spec directory and `docs/findings-ledger.md` (rows written by
  `scripts/memory_compile.py ledger add`), that diff names only D9's files; it changes no line of fx, V, K, N, C, P,
  H, `families/` or `commands/_common.py`, and no existing R or T test. C `test_load_config_refusals` and
  `test_environment_token_ignored`, K `test_call_takes_no_token_option` and
  `test_a_gated_operation_names_its_subcommand`, N, P `test_standard_library_only` and H pass in the run of every wave
  that names them. — Files: none (read-only) — Validates: UB-1.1, UB-1.2, UB-2.1, UB-2.2
- [ ] F.4 VERIFY: the map's `gitlab_api/` bullet holds D8's sentences before "Not installed here", which stays last,
  and `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes in the run of wave 3. — Files: none
  (read-only) — Validates: AC-5.2

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1; design D1, D2, D4, D5, D6, D7 (design review) |
| AC-1.2 | 2.1; V `test_every_graphql_only_capability_is_served_or_pending` on wave 2's Run line |
| AC-1.3 | 2.1 |
| AC-1.4 | 2.2 |
| AC-2.1 | 2.2; H on the Run lines of waves 1 and 2 |
| AC-2.2, AC-2.3, AC-2.4, AC-2.5 | 2.2 |
| AC-3.1 | 1.1, 1.2, 2.2 |
| AC-3.2 | 2.2 |
| AC-4.1 | 2.1, 2.2 |
| AC-4.2 | 2.2; K `test_a_gated_operation_names_its_subcommand` on the Run lines of waves 1 and 2 |
| AC-4.3 | 2.2 |
| AC-5.1 | 3.1 |
| AC-5.2 | 3.2, F.4 |
| UB-1.1 | F.3; C on every Run line |
| UB-1.2 | 2.2, F.3; K, N and R on the Run lines of waves 1 and 2 |
| UB-2.1 | F.3; C on every Run line, K on those of waves 1 and 2 |
| UB-2.2 | F.3; P on every Run line |
| UB-3.1 | F.2 |
