# Tasks — issue #30: GitHub wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-006); nothing is added. Test files as
design § Acceptance Criteria Mapping: G = `src/payload/test/test_github_api_graphql_only.py` (new), R =
`src/payload/test/test_github_api_registry.py`, Q = `test/test_github_graphql_contract.py` (new), V =
`test/test_github_wrapper_coverage.py`, K = `src/payload/test/test_github_api_call.py`, N =
`test/test_github_wrapper_contract.py`, C = `src/payload/test/test_github_wrapper_compat.py`, P =
`test/test_github_wrapper_fork_parity.py`, H = `test/test_github_api_call_properties.py`; fx =
`src/payload/test/github_wrapper_fixtures.py`. Each test does what design § Correctness Properties states for its
criterion, with its cases, against that oracle. In a wave the TEST tasks run first and add failing tests (and the
test-side helpers D1 and D6 name), red for the right reason — an assertion, or an exception raised inside the test body
(an `AttributeError` or `TypeError` on what is not yet written), never a collection error: G imports `github_api`
modules inside each test with `fx.import_api_module`, Q as V does (a `scripts_on_path` fixture and an import that
asserts the module file exists first), and G parametrizes over constants only. The IMPL tasks then add the minimal code
that turns them green. No task edits fx, `CASES`, C, P, K, N, H or an existing R test; V's existing lines change only
in `_capability_problems` and its call in `test_one_module_per_family_holding_only_its_own_ids` (D1).

## Precondition — the rebase (the conductor; no task)

Before wave 1's red run the conductor rebases the branch onto `origin/main`, which holds #27 (`f374b3d`:
`GATED_OPERATIONS` is `Mapping[str, Optional[str]]`, and `None` makes `refuse_gated` say that no subcommand sends the
operation) and #32 (`6fd2f64`: `GATED_NOT_SENT`), as design D5 requires. Every Run line and every diff of § Final is
read on the rebased branch.

## Wave 1 — Registry and the capability rule

Run: `python scripts/run_tests.py src/payload/test/test_github_api_registry.py test/test_github_wrapper_coverage.py src/payload/test/test_github_api_call.py src/payload/test/test_github_wrapper_compat.py test/test_github_wrapper_fork_parity.py src/payload/test/test_wrapper_delivery.py`

- [ ] 1.1 TEST: R, the registry reached through `load_api` and a synthetic `graphql_only.OPERATIONS` set with
  `monkeypatch.setattr`: `test_variables_are_the_documents_definitions` (the document with `$name : String` gives
  `("owner", "name", "after")`, and `("owner", "name")` on a record with a `connection`),
  `test_graphql_lookup_finds_one_record` (a declared ID is found; an undeclared ID and an ID declared twice each raise
  `ValueError` naming the ID). Red: neither `declared_variables` nor `graphql_lookup` exists, and a `GraphQLOperation`
  built with `operation_id=` raises `TypeError`. — Files: src/payload/test/test_github_api_registry.py — Validates:
  AC-2.5
- [ ] 1.2 TEST: V per D1 — `_capability_problems` gains an `index` parameter, which
  `test_one_module_per_family_holding_only_its_own_ids` passes from `index_rows`; its duplicate check reads
  `record.operation_id`, and it names a record whose `operation_id` is an operation ID of `index`. New:
  `test_a_graphql_record_id_is_its_own`, on a synthetic module (a `types.ModuleType` with `OPERATIONS` and
  `PENDING_CAPABILITIES`) of `GraphQLOperation`s built with `operation_id=` from the registry `_import_package_module`
  imports: two records sharing a capability give no problem; two sharing an ID give one problem naming the ID; a record
  whose ID is an index ID gives one naming it. Red: `operation_id=` raises `TypeError`. `coverage_gaps`,
  `_covered_and_pending` and every other V test unedited. — Files: test/test_github_wrapper_coverage.py — Validates:
  AC-1.4, AC-1.5
- [ ] 1.3 IMPL: D2's and D3's registry changes — `GraphQLOperation.operation_id: str` as its first field and
  `connection` defaulting to `()`; `GRAPHQL_ID_PREFIX = "graphql/"`; `graphql_lookup(*, operation_id)` (`graphql_only`
  imported inside the function; `ValueError` naming the ID when no record or more than one declares it);
  `declared_variables(*, operation)` (each `$name` followed, after any white space, by `:`, in order; for a record with
  a `connection`, without `transport.FIELD_AFTER`); the module docstring describing a `GraphQLOperation` as one
  operation serving a capability (D7). `lookup`, `send`, `call` and `pages` unchanged; standard library only; no text
  `environ` or `getenv`. — Files: src/payload/scripts/github_api/registry.py — Validates: AC-1.4, AC-2.5

## Wave 2 — The records, the GraphQL call and the contract

Run: `python scripts/run_tests.py src/payload/test/test_github_api_graphql_only.py test/test_github_graphql_contract.py test/test_github_wrapper_coverage.py src/payload/test/test_github_api_registry.py src/payload/test/test_github_api_call.py src/payload/test/test_github_api_git.py src/payload/test/test_github_api_repos.py test/test_github_api_call_properties.py test/test_github_wrapper_contract.py src/payload/test/test_github_wrapper_compat.py test/test_github_wrapper_fork_parity.py src/payload/test/test_wrapper_delivery.py`

- [ ] 2.1 TEST: Q per D6, reading `docs/api-reference/github/graphql/` — `reference_schema(*, graphql_dir)`,
  `read_document(*, document)`, `document_problems(*, record, schema)`, `selected_members(*, record, schema)` and
  `row_members(*, conventions)`, each by D6's rules. Tests: `test_the_reference_is_read_as_written` (its examples,
  `selected_members` of `graphql/pinIssue` and `graphql/Repository.discussions` included),
  `test_every_record_matches_the_reference` (failing when it finds no record),
  `test_the_method_rejects_a_document_that_differs` (its cases, on `dataclasses.replace` copies of the named records),
  `test_every_capability_has_a_record`, `test_every_member_a_row_names_is_selected` (a failure names the row and the
  member). Red: with `OPERATIONS` empty and `PENDING_CAPABILITIES` full, each test fails on an assertion or, for a
  named record, on `registry.graphql_lookup`'s `ValueError`, inside the test body. — Files:
  test/test_github_graphql_contract.py — Validates: AC-1.1, AC-1.2, AC-1.3, AC-3.1
- [ ] 2.2 TEST: G per D6 — loads fx by path as R does; every call runs the product's `main` through
  `fx.run_product_case` against a `fx.StaticRouteSpec(method="POST", url="/graphql", replies=...)` route, each posted
  body judged by `GoldenCase.writes` and, in `test_a_variable_holds_the_given_json_value`, also by
  `json.dumps(sort_keys=True)` (design AC-2.1), a refusal by its `caplog` record; AC-3.1's four IDs are one module
  constant. Tests: `test_every_record_is_called_through_main` (every record of `graphql_only.OPERATIONS` whose ID is
  not in that constant, with D6's argv, answers and oracle; failing when it calls no record),
  `test_a_variable_holds_the_given_json_value`, `test_a_merge_queue_prints_every_entry`,
  `test_a_graphql_failure_exits_1_with_its_details`, `test_an_undeclared_variable_is_refused`,
  `test_a_refused_mutation_sends_nothing` (over the constant; the `graphql/enablePullRequestAutoMerge` record names
  `merge-pr` without "which sends it"). Red: `call` refuses every `graphql/` ID as one no record declares
  (`registry.lookup`, exit 2), so each test fails on its exit-code, request or log assertion. — Files:
  src/payload/test/test_github_api_graphql_only.py — Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6,
  AC-3.1, AC-3.2, AC-3.3
- [ ] 2.3 IMPL: `graphql_only.py` per D1 and D2 — `OPERATIONS` holding D1's query records, each with its `connection`,
  and its mutation records (`mutation($input: <I>!) { <m>(input: $input) { clientMutationId <selection> } }`, `<I>` the
  input type `mutations.md`'s signature line names, `connection` `()`), every `capability` its row's first cell
  verbatim and every ID `graphql/<member>`; `PENDING_CAPABILITIES = frozenset()`; the module docstring stating the ID
  scheme, the two document shapes, and that a refused record is declared but never sent (D7). — Files:
  src/payload/scripts/github_api/graphql_only.py — Validates: AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-3.1
- [ ] 2.4 IMPL: `commands/call.py` per D3, D5 and D7 — `GATED_OPERATIONS` gains `graphql/enablePullRequestAutoMerge`
  → `"merge-pr"` and `graphql/createCommitOnBranch`, `graphql/revertPullRequest`, `graphql/transferIssue` → `None`, and
  `GATED_NOT_SENT` gains `graphql/enablePullRequestAutoMerge`, its comment adding that `merge-pr` never turns
  auto-merge on; `check_graphql_call(*, operation, path_names, query_names, variable_names)` (one `ValueError` naming
  each `--path` or `--query` name given, then each variable outside `registry.declared_variables`, then those
  variables); `cmd_call`'s branch for an ID starting with `registry.GRAPHQL_ID_PREFIX` — `refuse_gated`,
  `registry.graphql_lookup`, `check_graphql_call`, a refusal logged and returned as `EXIT_REFUSED` before any request,
  then `print_json(value=registry.graphql_call(...))` (the function 2.5 writes in this wave with D3's signature; 2.4
  does not edit `registry.py`) with `body_of(members=...) or {}` as the variables; every other ID
  on #28's steps, unchanged. The module docstring gains D3's GraphQL grammar and print forms; it and the
  `GATED_OPERATIONS` comment name, beside a branch-writing record, a record that moves an issue into another
  repository. No option added; `refuse_gated` unchanged; no text `environ` or `getenv`; standard library only. —
  Files: src/payload/scripts/github_api/commands/call.py — Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-3.1,
  AC-3.2, UB-1.2, UB-2.1, UB-2.2
- [ ] 2.5 IMPL: `registry.graphql_call(transport, operation_id, *, variables)` per D3 (`graphql_lookup`, an undeclared
  name refused with `ValueError` as `_check_names` refuses, then `list(transport.graphql_nodes(...))` for a record with
  a `connection`, else `transport.graphql(...)`); nothing else of the module changes. — Files:
  src/payload/scripts/github_api/registry.py — Validates: AC-2.1, AC-2.2, AC-2.3

## Wave 3 — Usage docstring and map

Run: `python scripts/run_tests.py src/payload/test/test_github_api_graphql_only.py test/test_github_graphql_contract.py src/payload/test/test_github_wrapper_compat.py test/test_github_wrapper_fork_parity.py test/test_github_wrapper_coverage.py src/payload/test/test_wrapper_delivery.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [ ] 3.1 TEST: G — `test_the_usage_names_every_graphql_record`: the `__doc__` of `fx.PRODUCT_SCRIPT`, loaded with
  `fx.load_script`, read within its GraphQL entry (the `call graphql/` usage line and the `#` lines under it, up to the
  next usage line), holds every capability of `graphql_only.OPERATIONS` followed by the IDs of its records before the
  next capability; `-F NAME=JSON`, `input`, `JSON array`, `data` and `exit 2`; each of AC-3.1's IDs, and `merge-pr`.
  Red: the docstring has no `call graphql/` line. — Files: src/payload/test/test_github_api_graphql_only.py —
  Validates: AC-4.1
- [ ] 3.2 TEST: Q — `test_the_map_names_the_graphql_call`: `docs/forLLMConsumption.md` holds `call graphql/`. Red: the
  map does not. — Files: test/test_github_graphql_contract.py — Validates: AC-4.2
- [ ] 3.3 IMPL: the entry script's module docstring only, per D7 — D7's lines after the `call issues/get` entry, one
  capability line per capability in D1's order, wrapped onto further `#     ` lines at 120 columns. — Files:
  src/payload/scripts/github_wrapper.py — Validates: AC-4.1
- [ ] 3.4 IMPL: the map's `src/payload/scripts/github_api/` bullet per D7 — D7's sentences before its closing
  sentence, which stays last; the map under its cap. — Files: docs/forLLMConsumption.md — Validates: AC-4.2

## Final

- [ ] F.1 E2E: the real-forge check is #10's fixture on an ephemeral `sff-test-*` repository (requirements "Out of
  scope"; design D6 names the records it cannot exercise). Until it exists, G runs every GraphQL call through `main`'s
  argv up to the API boundary and Q proves every document against the reference, in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names neither `src/payload/scripts/gitlab_wrapper.py` nor `src/payload/test/test_wrapper_delivery.py`, and
  `test_wrapper_delivery.py` passes in the run of every wave. — Files: none (read-only) — Validates: UB-3.1
- [ ] F.3 VERIFY: outside the spec directory and `docs/findings-ledger.md` (rows written by
  `scripts/memory_compile.py ledger add`), that diff names only D8's files; it changes no line of fx, `CASES`, C,
  P, K, N, H, `families/`, `transport.py` or `commands/_common.py`, and no existing R test; V's existing lines change
  only in `_capability_problems` and its call in `test_one_module_per_family_holding_only_its_own_ids`. The unchanged C
  `test_a_subcommand_matches_its_golden_case` and `test_the_credential_comes_only_from_the_file`, P
  `test_the_fork_produces_the_golden_case` and `test_the_parsers_match_option_by_option`, V
  `test_the_wrapper_imports_only_the_standard_library`, and K and N pass in the run of every wave that names them. —
  Files: none (read-only) — Validates: UB-1.1, UB-1.2, UB-2.1, UB-2.2
- [ ] F.4 VERIFY: the map's `github_api/` bullet holds D7's sentences with its closing sentence last, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes in the run of wave 3. — Files: none
  (read-only) — Validates: AC-4.2

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1; design D1, D2, D4, D6 (approved, DL-006) |
| AC-1.2 | 2.1; V `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` on wave 2's Run line |
| AC-1.3 | 2.1 |
| AC-1.4 | 1.2 |
| AC-1.5 | 1.2; V's two tests above on wave 2's Run line |
| AC-2.1 | 2.2; H on wave 2's Run line |
| AC-2.2, AC-2.3, AC-2.4, AC-2.6 | 2.2 |
| AC-2.5 | 1.1, 2.2 |
| AC-3.1 | 2.1, 2.2 |
| AC-3.2, AC-3.3 | 2.2 |
| AC-4.1 | 3.1 |
| AC-4.2 | 3.2, F.4 |
| UB-1.1 | F.3; C and P on every Run line |
| UB-1.2 | F.3; K and R on the Run lines of waves 1 and 2, N on wave 2's |
| UB-2.1 | F.3; C on every Run line |
| UB-2.2 | F.3; V on every Run line |
| UB-3.1 | F.2 |
