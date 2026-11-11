# Tasks — issue #63: GitLab wrapper rewrite, part 2 slice: request forms the records lack

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-007); nothing is added. Test files as the
legend of design § Acceptance Criteria Mapping (R, T, K, C, G new, F:<family>, P, N, V); fx =
`src/payload/test/gitlab_wrapper_fixtures.py`. Each test does what design § Correctness Properties states for its
criterion, with its cases, against that oracle. In a wave the TEST tasks run first and add failing tests (and restate
D9's), red for the right reason — an assertion, or an exception raised inside the test body (`AttributeError`,
`TypeError`) on what is not yet written, never a collection error: G loads fx by path and imports `gitlab_api`
modules inside each test as T does, the other files keep their own import rule, and N reads a field the base lacks as
D7 says. A product name this change adds is read only inside a function body; a parametrized test runs over literal
constants, never over a record tuple. The IMPL tasks then add the minimal code that turns them green, standard library
only and reading no environment (UB-2), each file's symbols those its D12 row names. No task edits a D12 "Not edited"
file or an existing assertion but D9's; of N's existing test functions only the send test's loop (D7) and D9's
`test_only_the_upload_module_path_holds_a_hyphenated_name` change (UB-1).

## Precondition — the rebase (the conductor; no task)

Before wave 1's red run, once #43's PR #65 has merged, the conductor rebases the branch onto `origin/main` (DL-001). Its
base then holds #43's forms: `registry.route`, `RestOperation.route_prefixes`, `call --route-prefix`,
`families/package.py`, F:package, and N's route-prefix readers with
`test_only_the_upload_module_path_holds_a_hyphenated_name`. Every Run line and every diff of § Final is read on the
rebased branch.

## Wave 1 — The forms in the registry, the transport and the container registry

Run: `python scripts/run_tests.py src/payload/test/test_gitlab_*.py test/test_gitlab_*.py`

- [ ] 1.1 TEST: R — `test_lookup_chooses_an_endpoint_of_a_reference`,
  `test_each_place_of_a_positional_name_takes_its_own_value`, `test_the_suffix_is_written_only_when_given`,
  `test_the_base_is_read_from_the_path`, `test_a_header_param_is_encoded_as_a_header` and
  `test_send_fetches_the_registry_token_before_the_registry` (its record built with `token_scope`), on synthetic
  records. Red: `lookup` takes no `endpoint` and `RestOperation` none of D12's new fields (`TypeError`); `base_of` and
  `Location.HEADER` are missing (`AttributeError`). — Files: src/payload/test/test_gitlab_api_registry.py — Validates:
  AC-2.2, AC-2.4, AC-3.1, AC-3.2, AC-4.1, AC-5.1, AC-5.2, AC-6.2, UB-1
- [ ] 1.2 TEST: T — `test_a_host_request_is_sent_outside_the_api` (over T's `TOKEN_TYPES`),
  `test_the_registry_token_is_asked_for_with_basic_credentials`,
  `test_a_registry_request_carries_only_the_registry_token` and
  `test_a_request_header_is_sent_beside_the_transport_headers`. Red: `request` takes no `base` or `headers`
  (`TypeError`); `Base` and the two registry methods are missing (`AttributeError`). — Files:
  src/payload/test/test_gitlab_api_transport.py — Validates: AC-5.1, AC-5.2, AC-6.2, UB-2
- [ ] 1.3 TEST: P — `test_only_a_declared_endpoint_is_chosen`, `test_each_place_takes_its_own_value` and
  `test_only_a_listed_format_reaches_the_path` (the eight formats a literal tuple), each `@settings(deadline=None)`,
  and the module docstring's sentence naming them. Red: as 1.1 (`TypeError`). — Files:
  test/test_gitlab_api_properties.py — Validates: AC-2.4, AC-3.1, AC-3.2, AC-4.2
- [ ] 1.4 TEST: G — `test_a_job_token_logs_in_as_gitlab_ci_token`, on `container_registry.send` with its answers
  queued through fx. Red: `gitlab_api.container_registry` does not exist (the import helper's `AssertionError` or
  `ModuleNotFoundError`). — Files: src/payload/test/test_gitlab_api_container_registry.py — Validates: AC-5.2
- [ ] 1.5 TEST: N per D9's last bullet — `test_only_the_upload_module_path_holds_a_hyphenated_name` gains its two
  literal exceptions. Red: `registry.placeholders` names neither `format` nor a `${NAME}` for those rows (assertion). —
  Files: test/test_gitlab_wrapper_contract.py — Validates: UB-1
- [ ] 1.6 IMPL: `registry.py` per D1 to D5 — `lookup` by D1's table; `send`, `call` and `pages` calling
  `lookup(operation_id=...)` alone when `endpoint` is `None`; `send` passing a container-registry record to
  `container_registry.send` (written by 1.8 in this wave); `pages` refusing a base other than `REST` and any header. —
  Files: src/payload/scripts/gitlab_api/registry.py — Validates: AC-2.2, AC-2.4, AC-3.1, AC-3.2, AC-4.1, AC-4.2,
  AC-5.1, AC-5.2, AC-6.2, UB-1
- [ ] 1.7 IMPL: `transport.py` per D4 and D5 — a header name D5 refuses, and a value `registry.check_header_value`
  refuses, raise before anything is sent. — Files: src/payload/scripts/gitlab_api/transport.py — Validates: AC-5.1,
  AC-5.2, AC-6.2, UB-2
- [ ] 1.8 IMPL: `container_registry.py` (new) per D4 — `send` and its four steps on the answers they expect; the
  module docstring. — Files: src/payload/scripts/gitlab_api/container_registry.py — Validates: AC-5.2, UB-2

## Wave 2 — The records, the call and the contract

Run: wave 1's.

- [ ] 2.1 TEST: N per D7 — `IN_HEADER`, the readings of D7's table and the module docstring naming the forms; the
  tests `test_each_record_of_an_id_copies_its_base_record`, `test_a_two_level_member_is_read_and_sent_as_written` (the
  gate lifted for that test only, D6), `test_an_endpoint_a_place_a_suffix_and_a_base_are_read_as_written` and
  `test_a_request_header_is_read_and_sent_as_written`, each on the declared records of the IDs whose sections or paths
  its oracle names, a "built" record a `dataclasses.replace` of one. Red: `header_problems` names the NuGet symbol
  downloads, which lack `Symbolchecksum`, in N's record test, and each new test finds no record of an ID or endpoint
  D8 adds (assertion). — Files: test/test_gitlab_wrapper_contract.py — Validates: AC-1.2, AC-6.1, AC-7.2, AC-8.1,
  AC-8.2
- [ ] 2.2 TEST: K — `test_an_endpoint_is_named_by_its_method_and_path`,
  `test_an_endpoint_the_reference_does_not_declare_is_refused`, `test_a_two_value_path_given_one_value_is_refused`,
  `test_a_format_the_page_does_not_list_is_refused`, `test_an_undeclared_header_is_refused`,
  `test_the_s3_import_is_refused` and `test_the_call_docstring_names_the_request_forms`. Red: argparse refuses
  `--endpoint` and `--header` and `registry.lookup` each ID D8 adds, so each refusal fails on its standard-error or
  log assertion and each accepted call on its exit code; the docstring lacks AC-9.1's spellings. — Files:
  src/payload/test/test_gitlab_api_call.py — Validates: AC-2.1, AC-2.4, AC-3.3, AC-4.2, AC-6.3, AC-7.1, AC-8.3,
  AC-9.1, UB-3
- [ ] 2.3 TEST: F:plan `test_an_other_endpoint_is_sent_when_named`; F:developer_experience
  `test_the_literal_endpoints_are_sent_as_written`; F:create `test_each_id_of_the_certificate_path_takes_its_place`
  and `test_the_archive_format_is_sent_as_its_suffix`; F:tenant_scale `test_each_id_of_a_token_path_takes_its_place`;
  D9's tests of these and of F:fulfillment, F:security_risk_management and F:verify. Red: each `PENDING` holds its
  issue keys and each `OPERATIONS` lacks D8's records (assertions), and each call exits 2 on `--endpoint` or an ID no
  record declares. — Files: F:create, F:developer_experience, F:fulfillment, F:plan, F:security_risk_management,
  F:tenant_scale, F:verify — Validates: AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-2.1, AC-2.2, AC-2.3, AC-3.1, AC-3.2,
  AC-4.1, AC-8.3
- [ ] 2.4 TEST: F:software_supply_chain_security — `test_the_user_status_patch_is_sent_when_named`,
  `test_the_token_information_is_sent_outside_the_api`, `test_the_external_control_status_carries_its_headers` and
  D9's tests of the family. Red: as 2.3, `--header` too. — Files: F:software_supply_chain_security — Validates:
  AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-2.1, AC-5.1, AC-6.2, AC-8.3
- [ ] 2.5 TEST: F:package — `test_a_registry_record_is_sent_to_the_registry_with_its_token` and
  `test_no_registry_token_sends_nothing_to_the_registry`; D9's two #43 tests. Red: as 2.3. — Files:
  src/payload/test/test_gitlab_api_package.py — Validates: AC-1.1, AC-1.3, AC-1.4, AC-5.2, AC-5.3, AC-8.3, UB-2
- [ ] 2.6 TEST: F:gitlab_dedicated `test_the_s3_import_sends_every_member_at_its_name` (the gate lifted for that test
  only) and D9's tests of the family; F:openapi_only
  `test_the_symbol_download_sends_its_checksum_header` and D9's `test_every_param_is_typed_as_its_row`. Red: the S3 key
  is pending and the NuGet downloads type no `Symbolchecksum` (assertions); each call exits 2. — Files:
  F:gitlab_dedicated, F:openapi_only — Validates: AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-6.2, AC-7.1, AC-8.3
- [ ] 2.7 IMPL: the seven families of 2.3 per D8 — each key D8's table gives the module: an F1 record after its base
  record, in its section's endpoint order, by D8's Rules; an F2 ID with `positional_names=("id",)`; the F3 ID with
  D3's `suffix_values`; `PENDING` less those keys; the docstrings. — Files: src/payload/scripts/gitlab_api/families/
  create.py, developer_experience.py, fulfillment.py, plan.py, security_risk_management.py, tenant_scale.py, verify.py
  — Validates: AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2, AC-2.3, AC-3.1, AC-3.2, AC-4.1, AC-4.2
- [ ] 2.8 IMPL: `software_supply_chain_security.py` per D8 — its F1 records, the token-information record and the
  external control with its three required `Location.HEADER` `Param`s; `PENDING` less those keys; the docstring. —
  Files: src/payload/scripts/gitlab_api/families/software_supply_chain_security.py — Validates: AC-1.1, AC-1.2,
  AC-2.1, AC-5.1, AC-6.1, AC-6.2
- [ ] 2.9 IMPL: `package.py` per D8 — each Conan v1 record and the NuGet v2 `PUT` after their base records; the two
  registry records with D4's `token_scope`; `PENDING` less those keys; the docstring. — Files:
  src/payload/scripts/gitlab_api/families/package.py — Validates: AC-1.1, AC-1.2, AC-5.2
- [ ] 2.10 IMPL: `gitlab_dedicated.py` per D6 — `OP_IMPORT_FROM_S3` and its record, `PENDING` less its key — and
  `openapi_only.py` per D8 — `Symbolchecksum` on both NuGet symbol downloads; each docstring's changed rule. — Files:
  src/payload/scripts/gitlab_api/families/gitlab_dedicated.py and openapi_only.py — Validates: AC-1.1, AC-1.2,
  AC-6.1, AC-7.1
- [ ] 2.11 IMPL: `commands/call.py` per D1 to D6 and D11 — `GATED_OPERATIONS` maps
  `gitlab_dedicated.OP_IMPORT_FROM_S3` (written by 2.10 in this wave) to `None`, its comment naming the class; no
  option string holds `token`. — Files: src/payload/scripts/gitlab_api/commands/call.py — Validates: AC-2.1, AC-2.4,
  AC-3.3, AC-4.2, AC-6.3, AC-7.1, AC-9.1, UB-2, UB-3
- [ ] 2.12 IMPL: AC-5.3 in `container_registry.py` and `transport.py` per D4 — each failure a `GitLabAPIError` before
  step 4; the registry token in no URL, log record or exception message. — Files:
  src/payload/scripts/gitlab_api/container_registry.py and transport.py — Validates: AC-5.3, UB-2

## Wave 3 — Usage docstring, map and ledger

Run:

```
python scripts/run_tests.py src/payload/test/test_gitlab_*.py test/test_gitlab_*.py \
  test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py
```

- [ ] 3.1 TEST: C `test_the_usage_names_the_request_forms`. Red: the entry script's docstring lacks AC-9.1's
  spellings (assertion). — Files: src/payload/test/test_gitlab_wrapper_compat.py — Validates: AC-9.1
- [ ] 3.2 TEST: N `test_the_map_names_the_request_forms`. Red: the `gitlab_api/` bullet holds none of the five
  spellings (assertion). — Files: test/test_gitlab_wrapper_contract.py — Validates: AC-9.2
- [ ] 3.3 IMPL: the entry script's module docstring only, per D11 — every text of C's `USAGE_CALL_TEXTS` kept. —
  Files: src/payload/scripts/gitlab_wrapper.py — Validates: AC-9.1, UB-1
- [ ] 3.4 IMPL: the map's `src/payload/scripts/gitlab_api/` bullet per D11, the map under its cap. — Files:
  docs/forLLMConsumption.md — Validates: AC-9.2
- [ ] 3.5 IMPL: the Residuals' rows per D12 — one per requirements Residual and one per design Residual after the
  first, each written with `python scripts/memory_compile.py ledger add`. — Files: docs/findings-ledger.md —
  Validates: design § Residuals (D12)

## Final

- [ ] F.1 E2E: the real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project. Until it exists,
  N calls every record of this change and the tests of AC-8.3 run `call` through `main`'s argv against the fake host
  to the API boundary, in the `verify` job of `.github/workflows/ci.yml`, matrix leg `tests`
  (`python scripts/run_checks.py --group tests`). — Files: none — Validates: AC-8.1, AC-8.3
- [ ] F.2 VERIFY: the branch's diff (`git diff --name-only origin/main...HEAD`) names no file of UB-4, and
  `src/payload/test/test_github_api_*.py` and `src/payload/test/test_wrapper_delivery.py` pass in CI's `tests` leg on
  the pushed SHA. — Files: none (read-only) — Validates: UB-4
- [ ] F.3 VERIFY: outside the spec directory, that diff names only D12's files; it changes no "Not edited" file, no
  existing assertion but D9's, no existing N test function but the send test's loop and D9's, and of
  `GATED_OPERATIONS` only D6's entry. C `test_load_config_refusals` and `test_environment_token_ignored`, K
  `test_call_takes_no_token_option` and its existing refusal tests, R `test_call_refuses_an_undeclared_value`, P
  `test_standard_library_only` (its scan reaching `container_registry.py`) and every other existing test pass in the
  green run of every wave that names them. — Files: none (read-only) — Validates: AC-1.4, UB-1, UB-2, UB-3

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.3 to 2.6 |
| AC-1.2 | 2.1, 2.3, 2.4, 2.6; N's record test on wave 2's Run line |
| AC-1.3 | 2.3 to 2.6; V on wave 2's Run line |
| AC-1.4 | 2.3 to 2.6, F.3; V's two tests it names |
| AC-2.1 | 2.2, 2.3, 2.4 |
| AC-2.2 | 1.1, 2.3 |
| AC-2.3 | 2.3 |
| AC-2.4 | 1.1, 1.3, 2.2 |
| AC-3.1, AC-3.2 | 1.1, 1.3, 2.3 |
| AC-3.3 | 2.2 |
| AC-4.1 | 1.1, 2.3 |
| AC-4.2 | 1.3, 2.2 |
| AC-5.1 | 1.1, 1.2, 2.4 |
| AC-5.2 | 1.1, 1.2, 1.4, 2.5 |
| AC-5.3 | 2.5 |
| AC-6.1 | 2.1 (`header_problems` in N's record test) |
| AC-6.2 | 1.1, 1.2, 2.4, 2.6 |
| AC-6.3 | 2.2 |
| AC-7.1 | 2.2, 2.6 |
| AC-7.2 | 2.1 |
| AC-8.1 | 2.1, F.1; N's record and send tests on wave 2's Run line |
| AC-8.2 | 2.1 |
| AC-8.3 | 2.2 to 2.6, F.1 |
| AC-9.1 | 2.2, 3.1 |
| AC-9.2 | 3.2; `test_llm_map_within_cap` on wave 3's Run line |
| UB-1 | 1.1, 1.5, F.3; C and the existing suites on every Run line |
| UB-2 | 1.2, 2.5, F.3 |
| UB-3 | 2.2, F.3 |
| UB-4 | F.2 |
