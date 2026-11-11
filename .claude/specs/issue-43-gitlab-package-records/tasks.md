# Tasks — issue #43: GitLab wrapper rewrite, part 2 slice: the package stage group

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-007); nothing is added. Test files as the
legend of design § Correctness Properties: F = `src/payload/test/test_gitlab_api_package.py` (new), R =
`src/payload/test/test_gitlab_api_registry.py`, K = `src/payload/test/test_gitlab_api_call.py`, T =
`src/payload/test/test_gitlab_api_transport.py`, C = `src/payload/test/test_gitlab_wrapper_compat.py`, P =
`test/test_gitlab_api_properties.py`, N = `test/test_gitlab_wrapper_contract.py`, V =
`test/test_gitlab_wrapper_coverage.py`; H = `test/test_gitlab_api_call_properties.py` and the family suites
`src/payload/test/test_gitlab_api_<family>.py` (#40's `test_gitlab_api_openapi_only.py` and `test_gitlab_api_deploy.py`
among them) run as regression; fx = `src/payload/test/gitlab_wrapper_fixtures.py`. The shell expands the globs of the
Run lines of waves 1 and 2 to every one of these files on the rebased branch. Each test does what design § Correctness
Properties states for its criterion, with its cases, against that oracle. In a wave the TEST tasks run first and add
failing tests (and N's test-side readers of D4), red for the right reason — an assertion, or an exception raised inside
the test body (an `AttributeError` or `TypeError` on what is not yet written), never a collection error: F loads fx by
path and imports `gitlab_api` modules inside each test as `test_gitlab_api_no_stage_assigned.py` does, and R, K, P and
N keep their own import rule. A product name this change adds (`route`, `route_prefixes`, `ROUTE_PREFIX`,
`takes_route_prefix`, `OPTION_ROUTE_PREFIX`) is read only inside a function body, and a parametrized test runs over
literal constants, never over a record tuple. The IMPL tasks then add the minimal code that turns them green, standard
library only and reading no environment (UB-2). No task edits fx, V, C, T, `transport.py`, `commands/_common.py` or a
`commands/` module other than `call.py`, nor an existing assertion; of N's existing test functions only the send
test's loop changes (D4; D8 "Not edited"; UB-1, UB-4).

## Precondition — the rebase (the conductor; no task)

Before wave 1's red run, once #40's PR has merged, the conductor rebases the branch onto `origin/main` (DL-001). Its
base then holds the #40 forms this change uses by reference: `registry.PLACEHOLDER` with its `sigil` group,
`required_placeholders`, `RestOperation.content_type`, `send`'s `data`, `Transport.request_raw`, `call --input` with
`refuse_both_bodies` and `refuse_raw_body`, N's `glob_names` and `documented_raw_body`, and the openapi-only and deploy
suites (design D1 to D5). Every Run line and every diff of § Final is read on the rebased branch.

## Wave 1 — The hyphenated name and the route prefix in the registry

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_*.py test/test_gitlab_*.py`

- [ ] 1.1 TEST: R — `test_a_hyphenated_name_is_one_placeholder`, `test_route_writes_the_chosen_prefix` and
  `test_a_prefix_record_is_sent_only_under_a_prefix`, on synthetic records as R builds them. Red: `placeholders` reads
  `:module-name` as `module` (assertion), and `RestOperation` takes no `route_prefixes` (`TypeError`). — Files:
  src/payload/test/test_gitlab_api_registry.py — Validates: AC-2.2, AC-2.4, AC-3.1, UB-4
- [ ] 1.2 TEST: P — the property `test_route_accepts_only_the_records_prefixes` (`prefix` drawn from `st.text() |
  st.sampled_from(elements=<the npm values, a literal tuple>)`, its `@example` cases, `@settings(deadline=None)`) and
  the module docstring's sentence naming it. Red: `RestOperation` takes no `route_prefixes` (`TypeError`). — Files:
  test/test_gitlab_api_properties.py — Validates: AC-2.4, UB-2
- [ ] 1.3 TEST: N per D4 — `PATH_PLACEHOLDER`'s `name` group widened as D1's; `glob_names` replaced by
  `path_names(*, path)`, the names of either sigil, in `record_problems`' rule for a row the record lacks;
  `Section.route_prefixes` and `page_sections` reading a page's `<route-prefix>` line; `prefix_problems(*, record,
  section)` in `record_problems`; `call_prefix(*, record, section)`, `record_call`'s `prefix=None` (the argv gains
  `--route-prefix <prefix>`, its path names read with the prefix written in) and `routed_section(*, section, prefix)`
  (the section unchanged for `None`), used in the send test's loop; the module docstring naming the route prefix; the
  tests `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written` (its records built in the test) and
  `test_only_the_upload_module_path_holds_a_hyphenated_name` (its literal copy of #40's pattern). Red: until 1.4, the
  new test's records raise `TypeError` on `route_prefixes`, `prefix_problems` raises `AttributeError` on
  `route_prefixes` inside N's existing record tests, and `registry.placeholders` gives `module` for the
  `package#upload-module` row (assertion). — Files: test/test_gitlab_wrapper_contract.py — Validates: AC-1.5, AC-2.1,
  AC-3.1, AC-4.3, UB-4
- [ ] 1.4 IMPL: `registry.py` per D1 and D2 — `PLACEHOLDER`'s `name` group and its comment;
  `RestOperation.route_prefixes: Tuple[str, ...] = ()` after `content_type`; `ROUTE_PREFIX`; `takes_route_prefix(*,
  path)`; `route(*, operation, prefix)` by D2's table (`dataclasses.replace` writing the record's own value; each
  `ValueError` naming the ID and either the text given, as `json.dumps` renders it, with the record's values, or that
  the record takes no route prefix); `send` taking `prefix=None`, routing after `lookup` and its GraphQL refusal and
  before #40's `data` check; `expand` raising `ValueError` for a path that `takes_route_prefix`, before writing
  anything; the module docstring's `route`, `expand` and `send` bullets and the docstrings of `placeholders`, `expand`,
  `send` and `route`. The bodies of `placeholders`, `required_placeholders`, `_segment`, `_glob`, `encode`, `call` and
  `pages` unchanged. — Files: src/payload/scripts/gitlab_api/registry.py — Validates: AC-2.1, AC-2.2, AC-2.4, AC-3.1,
  UB-2, UB-4

## Wave 2 — The records and `call --route-prefix`

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_*.py test/test_gitlab_*.py`

- [ ] 2.1 TEST: F per D7 — built as `test_gitlab_api_no_stage_assigned.py` is: fx's fake host and socket guard
  autouse, `config/gitlab.json` in `tmp_path`, each call `main(argv=["call", …])` through `fx.run_main`; literal tables
  transcribed from the index and the entries (`KEPT`, `OPERATION_IDS`, `FIRST_ENDPOINTS`, `KINDS`, `REQUIRED`,
  `RAW_BODIES`, the paged IDs, the prefix tuples, and the argv and sent rows of design AC-2.2, AC-3.2 and AC-4.2).
  Tests: `test_nothing_is_pending_but_the_kept_keys`, `test_a_two_endpoint_entry_maps_its_first_endpoint`,
  `test_every_param_is_typed_as_its_row`, `test_no_param_names_a_path_parameter`,
  `test_only_the_list_records_are_paged`, `test_a_list_record_prints_every_page`,
  `test_a_prefix_record_is_sent_under_each_of_its_values`, `test_the_hyphenated_names_are_sent_as_one_segment_each`,
  `test_a_glob_record_is_sent_with_its_slashes`, `test_an_upload_sends_the_file_as_its_part` and
  `test_a_raw_upload_sends_the_bytes_as_its_body`. Red: `OPERATIONS` is empty and `PENDING` full, so each table test
  fails its assertion, and each call exits 2 (`registry.lookup` refuses every `package#` ID, argparse
  `--route-prefix`), failing its exit-code, request or log-record assertion; the `--file` refusal of
  `package#upload-a-package-file-3` is asserted inside that record's case, after its `--input` send, so that case is
  red on the send. — Files: src/payload/test/test_gitlab_api_package.py — Validates: AC-1.1, AC-1.2, AC-1.3, AC-1.4,
  AC-1.5, AC-1.6, AC-1.7, AC-2.1, AC-2.2, AC-2.3, AC-2.5, AC-3.1, AC-3.2, AC-3.3, AC-4.1, AC-4.2, AC-4.4
- [ ] 2.2 TEST: K — `test_a_route_prefix_the_record_does_not_list_is_refused` (its cases, `graphql#syntheticProject`
  installed as K installs it) and `test_a_hyphenated_name_is_documented_and_required`. Red: `registry.lookup` refuses
  the `package#` IDs and argparse refuses `--route-prefix` as unrecognized, so each case fails on its log-record
  assertion. — Files: src/payload/test/test_gitlab_api_call.py — Validates: AC-2.4, AC-2.5, AC-3.1
- [ ] 2.3 IMPL: `families/package.py` per D5 and D6 — `DEBIAN_ROUTE_PREFIXES`, `NPM_ROUTE_PREFIXES` and
  `NUGET_ROUTE_PREFIXES`, each `Tuple[str, ...]` under a comment naming its page; `OPERATIONS: Tuple[RestOperation,
  ...]`, one record per pending key but D6's kept keys, in the page order of `rest/package.md`, each under a comment
  naming its `##` and `###` headings and written by D6's table; D5's raw-body records with `content_type`
  `CONTENT_TYPE_OCTET_STREAM`, npm's two `CONTENT_TYPE_JSON`, both imported from `gitlab_api.transport`; `PENDING:
  FrozenSet[Tuple[str, str]]` holding D6's kept keys; the module docstring stating D6's rules in prose, which uploads
  take `--file` and which `--input`, and that a record whose path starts with `/<route-prefix>/` takes
  `--route-prefix`. — Files: src/payload/scripts/gitlab_api/families/package.py — Validates: AC-1.1, AC-1.2, AC-1.3,
  AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-2.1, AC-4.2
- [ ] 2.4 IMPL: `commands/call.py` per D3 — `OPTION_ROUTE_PREFIX`, `ARG_ROUTE_PREFIX` (default `None`) and
  `METAVAR_PREFIX`; the `--route-prefix` option in `register` (argparse `store`) with D3's help text; `prepare_call`'s
  step `operation = registry.route(operation=operation, prefix=args.route_prefix)` right after `registry.lookup` and
  `refuse_raw_body`, its `ValueError` a refusal as #41 D4's; `PreparedCall.prefix: Optional[str] = None`, which
  `prepare_call` sets to `args.route_prefix` on the `PreparedCall` of a `Paging.NONE` REST record and `send_call`
  passes to `registry.send` as `prefix`; the module docstring's grammar, `--route-prefix` bullet and refusal paragraph
  as D3 words them. No option string holds `token`; `GATED_OPERATIONS` and every function but `register`,
  `prepare_call` and `send_call` unchanged. — Files: src/payload/scripts/gitlab_api/commands/call.py — Validates:
  AC-2.1, AC-2.2, AC-2.3, AC-2.4, UB-2, UB-4

## Wave 3 — Usage docstring, map and ledger

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_compat.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`

- [ ] 3.1 IMPL: the entry script's module docstring only, per D3 — its `call` usage lines name `--route-prefix PREFIX`
  and its refusal, every text of C's `USAGE_CALL_TEXTS` kept (C `test_the_usage_names_the_operation_call`). — Files:
  src/payload/scripts/gitlab_wrapper.py — Validates: UB-1
- [ ] 3.2 IMPL: the map's `src/payload/scripts/gitlab_api/` bullet per D3 — its option list names `--route-prefix`;
  "Not installed here" stays last; the map under its cap (`test_llm_map_within_cap`). — Files:
  docs/forLLMConsumption.md — Validates: none (D3 documentation)
- [ ] 3.3 IMPL: the Residuals' rows per D8 — one for each of the first three requirements Residuals (more than one key
  under one Reference, the registry host, the project update) and one for each design Residual after the first (Git
  Bash's rewrite of `/packages/npm`, the uploads through Workhorse's catch-all `proxy`, the package routes no header of
  the transport authenticates), each written with `python scripts/memory_compile.py ledger add`. — Files:
  docs/findings-ledger.md — Validates: design § Residuals (D8)

## Final

- [ ] F.1 E2E: the real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project (requirements "Out
  of scope"). Until it exists, N calls every record of this change, a prefix record under its page's first value, and
  F the prefix, hyphenated, glob, list and upload forms, through `main`'s argv against the fake host up to the API
  boundary, in the `verify` job of `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py
  --group tests`); for a record #41 D5 calls unreachable (the Debian pages, Go Proxy, Ruby gems, Protected packages)
  N's two record tests are the whole proof (AC-4.3). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base with `origin/main` (`git diff --name-only origin/main...HEAD`)
  names no file of UB-3, and `src/payload/test/test_github_api_*.py` and `src/payload/test/test_wrapper_delivery.py`
  pass in CI's `tests` leg on the pushed SHA. — Files: none (read-only) — Validates: UB-3
- [ ] F.3 VERIFY: outside the spec directory, that diff names only D8's files; it changes no line of fx, V, C, T,
  `transport.py`, `commands/_common.py` or a `commands/` module but `call.py`, no existing assertion, no existing test
  function but the loop of N's `test_every_record_is_sent_as_its_section_documents` (D4), and no `GATED_OPERATIONS`
  entry. C `test_load_config_refusals` and `test_environment_token_ignored`, K `test_call_takes_no_token_option`,
  `test_a_gated_operation_names_its_subcommand` and `test_a_missing_path_parameter_is_refused`, T
  `test_next_url_on_another_origin_is_refused` and `test_cross_origin_redirect_drops_credentials`, R
  `test_project_path_is_encoded` and `test_empty_and_dot_segments_are_refused`, P `test_path_value_is_one_segment` and
  `test_standard_library_only`, and the existing tests of N, V, H and the family suites pass in the green run of every
  wave that names them. — Files: none (read-only) — Validates: UB-1, UB-2, UB-4

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1; V `test_every_declared_key_is_in_its_family` on wave 2's Run line |
| AC-1.2, AC-1.3 | 2.1 |
| AC-1.4 | 2.1; N `test_every_record_matches_its_reference_section` on wave 2's Run line |
| AC-1.5 | 1.3, 2.1 |
| AC-1.6 | 2.1 |
| AC-1.7 | 2.1; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` on wave 2's Run line |
| AC-2.1 | 1.3, 2.1; N `test_every_record_matches_its_reference_section` on wave 2's Run line |
| AC-2.2 | 1.1, 2.1 |
| AC-2.3 | 2.1 |
| AC-2.4 | 1.1, 1.2, 2.2 |
| AC-2.5 | 2.1, 2.2 |
| AC-3.1 | 1.1, 1.3, 2.1, 2.2 |
| AC-3.2, AC-3.3 | 2.1 |
| AC-4.1 | 2.1; N `test_every_record_is_sent_as_its_section_documents` on wave 2's Run line; K's existing tests on waves 1 and 2 |
| AC-4.2 | 2.1; K `test_a_raw_body_the_call_cannot_send_is_refused` and the deploy suite's `test_the_upload_sends_the_bytes_as_its_body` on wave 2's Run line |
| AC-4.3 | 1.3; N's two record tests on wave 2's Run line |
| AC-4.4 | 2.1 |
| UB-1 | F.3; C on every Run line |
| UB-2 | 1.2, F.3; P `test_standard_library_only` on the Run lines of waves 1 and 2 |
| UB-3 | F.2 |
| UB-4 | 1.1, 1.3, F.3; the GitLab suites on the Run lines of waves 1 and 2 |
