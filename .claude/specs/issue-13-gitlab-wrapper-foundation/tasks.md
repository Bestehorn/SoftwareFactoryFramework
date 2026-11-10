# Tasks — issue #13: GitLab wrapper rewrite, part 1 (foundation)

Tier: M. Criteria: `requirements.md`; components: `design.md` D1–D8; oracles: design.md "Correctness Properties".
`gitlab_api/` stands for `src/payload/scripts/gitlab_api/`. T, R, C, V, P, S are the test modules of design.md
"Acceptance Criteria Mapping". Shipped code stays Python 3.9 and standard library only, and the shipped suites stay
pytest-only (D3, UB-2). An empty `__init__.py` package marker carries no behaviour: it is named in the task that first
imports its package and is not counted among that task's files.

## Wave 1 — Exceptions, records, registry
- [x] 1.1 TEST: `FakeGitLab` — installed with `monkeypatch` over `urllib.request.HTTPSHandler.https_open` and
  `HTTPHandler.http_open`; scripted `(status, headers, body)` responses per method and URL, in order, as
  `addinfourl` objects with `msg` and an `http.client.HTTPMessage`; every request recorded (method, URL, headers,
  body); an unscripted request recorded, then `AssertionError` — and a `socket.socket.connect` guard, the module
  loaded by path and not collected. R puts `Path(__file__).resolve().parents[1] / "scripts"` on `sys.path`, installs
  both autouse and holds `test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused`,
  `test_array_of_hashes_pairs`, `test_lookup_refuses_unknown_and_duplicate_ids` (synthetic `RestOperation`s that
  `lookup` sees through a monkeypatched `registry.discover_families`; each case matches its message: the unknown id,
  the twice-declared id) — Files:
  `src/payload/test/gitlab_wrapper_fixtures.py`, `src/payload/test/test_gitlab_api_registry.py` — Validates: AC-1.1,
  AC-2.2, AC-2.3
- [x] 1.2 TEST: P puts `src/payload/scripts` on `sys.path` and holds the Hypothesis properties
  `test_path_value_is_one_segment` and `test_array_and_hash_pairs` (over `registry.encode`'s pairs joined with
  `urllib.parse.urlencode(pairs, safe="[]", quote_via=urllib.parse.quote)`, the join D4 names) — Files:
  `test/test_gitlab_api_properties.py` — Validates: AC-2.2, AC-2.3
- [x] 1.3 TEST: V's `index_rows`, `coverage_gaps` and a `socket.socket.connect` guard for every test of the module;
  `test_a_family_module_is_discovered_alone` (a synthetic families package in `tmp_path` under a package name unique
  to the test, prepended with `monkeypatch.syspath_prepend`, one `discover_families` call per package after its files
  are written) and `test_checker_names_each_unlisted_row` — Files: `test/test_gitlab_wrapper_coverage.py` —
  Validates: AC-1.2, AC-5.1, AC-5.2
- [x] 1.4 IMPL: `errors.py` — `GitLabAPIError(message, status_code=0, details=None)` with the subclasses
  `GitLabRateLimitError`, `GitLabGraphQLResponseError`, `GitLabClaimError`; `registry.py` per D5 — `Param`,
  `Location`, `Kind`, `BodyFormat`, `Paging`, `RestOperation`, `GraphQLOperation`, `discover_families`, `lookup`,
  `expand`, `encode`; `graphql_only.py` with an empty `OPERATIONS`; markers `gitlab_api/__init__.py`,
  `gitlab_api/families/__init__.py` — Files: `gitlab_api/errors.py`, `gitlab_api/registry.py`,
  `gitlab_api/graphql_only.py` — Validates: AC-1.1, AC-1.2, AC-2.2, AC-2.3, AC-5.2

## Wave 2 — Transport
- [x] 2.1 TEST: T puts the scripts directory on `sys.path` as R does, installs `FakeGitLab` and the guard autouse,
  and builds `Transport` with a recording `sleep`, a fixed `clock` and its default opener:
  `test_one_credential_header_per_token_type`, `test_json_body_is_native`, `test_file_value_sends_multipart`,
  `test_offset_paging_follows_next_and_ignores_total_pages`, `test_keyset_paging_follows_link_unchanged`,
  `test_next_url_on_another_origin_is_refused`, `test_cross_origin_redirect_drops_credentials` (parametrized),
  `test_same_origin_redirect_keeps_credential`, `test_credential_stays_dropped_on_return_hop`,
  `test_429_waits_retry_after`, `test_429_without_headers_backs_off_increasingly`, `test_429_after_retries_raises`,
  `test_error_shape_raises_gitlab_api_error` (parametrized), `test_graphql_posts_to_api_graphql`,
  `test_graphql_pages_by_end_cursor`, `test_graphql_errors_at_200_raise`,
  `test_empty_payload_errors_and_query_errors_fields_return_data` — Files:
  `src/payload/test/test_gitlab_api_transport.py` — Validates: AC-2.1, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-3.1,
  AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-4.1, AC-4.2, AC-4.3
- [x] 2.2 TEST: R `test_call_refuses_an_undeclared_value` — `registry.call` on a `Transport` over `FakeGitLab`, on a
  `RestOperation` the test builds and serves through `monkeypatch.setattr(registry, "lookup", …)`, raises `ValueError`
  whose message names the undeclared value, and nothing is recorded — `Transport` imported inside the test — Files:
  `src/payload/test/test_gitlab_api_registry.py` — Validates: AC-1.1
- [x] 2.3 TEST: P `test_standard_library_only` — every import of the entry script and the package is `gitlab_api…`
  or in `sys.stdlib_module_names`, neither contains `os.environ` or `getenv`, and the scanned set includes
  `gitlab_wrapper.py`, `gitlab_api/transport.py`, `gitlab_api/registry.py` — Files:
  `test/test_gitlab_api_properties.py` — Validates: UB-2
- [x] 2.4 IMPL: `transport.py` per D4 — the config-key constants, `CREDENTIAL_HEADERS`, the paging, retry and timeout
  constants, `TokenType`, `origin`, `CredentialStrippingRedirectHandler`, `error_text`, `Transport` (`from_config`;
  `_send` with the origin check, the credential header and the `429` retry; `request` with query, form, JSON and
  multipart bodies; `pages` for OFFSET and KEYSET; `graphql`; `graphql_nodes`); `registry.call` and `registry.pages`
  per D5 — Files: `gitlab_api/transport.py`, `gitlab_api/registry.py` — Validates: AC-1.1, AC-2.1, AC-2.3, AC-2.4,
  AC-2.5, AC-2.6, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-4.1, AC-4.2, AC-4.3, UB-2

## Wave 3 — Endpoint families and the entry script
Every `gitlab_api/families/<module>.py` below follows D2's family module contract: `FAMILY` (the stem), `OPERATIONS`,
and `PENDING`, the `(method, path)` keys of the family's index rows that no record maps; a key two families link
belongs to the module whose name sorts first. A record is transcribed from its row's `rest/<stem>.md` attribute table
(D1, D5).
- [x] 3.1 TEST: V `test_every_index_row_is_mapped_or_pending` — the real `operations-index.md` against
  `discover_families()` under the socket guard — Files: `test/test_gitlab_wrapper_coverage.py` — Validates: AC-5.3,
  AC-5.4
- [x] 3.2 TEST: C — `config/gitlab.json` in `tmp_path` (chdir), `main(argv=…)`, standard output by `capsys`,
  `FakeGitLab` and the guard autouse — with `test_load_config_refusals`, `test_delivery_verb_through_main`, the
  subprocess `test_script_usage_error_exits_2`, and the subprocess `test_script_loads_by_path` (`sys.executable -c`
  loads `<scripts dir>/gitlab_wrapper.py` with `importlib.util.spec_from_file_location` and `exec_module`,
  `cwd=tmp_path`, and exits 0 — green before 3.12 by design; its mutant is 3.12 with the bootstrap removed); the
  wave's captures also run
  `src/payload/test/test_wrapper_delivery.py`, unedited — Files: `src/payload/test/test_gitlab_wrapper_compat.py` —
  Validates: UB-1, UB-2
- [x] 3.3 IMPL: the `plan#` and `verify#` records D6 names, the rest pending — Files: `gitlab_api/families/plan.py`,
  `gitlab_api/families/verify.py` — Validates: AC-5.3, UB-1
- [x] 3.4 IMPL: the `ai-coding#`, `create#` and `software-supply-chain-security#` records D6 names, the rest pending —
  Files: `gitlab_api/families/ai_coding.py`, `gitlab_api/families/create.py`,
  `gitlab_api/families/software_supply_chain_security.py` — Validates: AC-5.3, UB-1
- [x] 3.5 IMPL: pending only — Files: `gitlab_api/families/agent_foundations.py`, `gitlab_api/families/ai_clients.py`,
  `gitlab_api/families/analytics.py` — Validates: AC-5.3
- [x] 3.6 IMPL: pending only — Files: `gitlab_api/families/data_access.py`, `gitlab_api/families/deploy.py`,
  `gitlab_api/families/developer_experience.py` — Validates: AC-5.3
- [x] 3.7 IMPL: pending only — Files: `gitlab_api/families/facilitated_functionality.py`,
  `gitlab_api/families/fulfillment.py`, `gitlab_api/families/gitlab_dedicated.py` — Validates: AC-5.3
- [x] 3.8 IMPL: pending only — Files: `gitlab_api/families/gitlab_delivery.py`, `gitlab_api/families/growth.py`,
  `gitlab_api/families/no_stage_assigned.py` — Validates: AC-5.3
- [x] 3.9 IMPL: pending only — Files: `gitlab_api/families/openapi_only.py`, `gitlab_api/families/orbit.py`,
  `gitlab_api/families/package.py` — Validates: AC-5.3
- [x] 3.10 IMPL: pending only — Files: `gitlab_api/families/runtime.py`, `gitlab_api/families/security_factory.py`,
  `gitlab_api/families/security_governance.py` — Validates: AC-5.3
- [x] 3.11 IMPL: pending only — Files: `gitlab_api/families/security_platform.py`,
  `gitlab_api/families/security_risk_management.py`, `gitlab_api/families/tenant_scale.py` — Validates: AC-5.3
- [x] 3.12 IMPL: the entry script per D3 and D7 — the import bootstrap; `_load_config` with the token-character,
  `in_progress_label` and `token_type` rules; `main(argv=None)`: UTF-8 `reconfigure` of standard output and standard
  error, a delivery verb to the unchanged `steward_delegate`, the parser of the discovered `gitlab_api.commands`
  modules, `Transport.from_config`, a `GitLabAPIError` logged and returned as 1; `__main__`; the usage docstring for
  UB-1's whole set and `token_type`; `_api_request`, the skeleton's `pipeline_wait`, its field constants and its notes
  removed except the issue-metadata and checklist-toggle notes. The template's `_comment` documents `token_type`, its
  keys unchanged. Marker `gitlab_api/commands/__init__.py` — Files: `src/payload/scripts/gitlab_wrapper.py`,
  `templates/config/gitlab.json.template` — Validates: UB-1, UB-2

## Wave 4 — The issue commands
- [x] 4.1 TEST: C, `test_a_subcommand_form` cases for every `issue` form and flag of D6 — `list` with `--state`,
  `--assignee` `*`, `none` and a username, and `--labels`; `show`; `create` with `--description` and `--labels`;
  `comment`; `start`; `release`; `label-add`; `label-remove`; `assign` with `--me`, `--user U`, `--unassign`; `close`;
  `reopen` — each asserting the recorded requests, standard output and exit code; `test_claim_check_exit_codes`,
  `test_issue_start_refusals`, `test_issue_reopen_of_open_issue`, `test_template_config_sends_private_token`,
  `test_environment_token_ignored`, and the subprocess `test_script_without_config_exits_1` — Files:
  `src/payload/test/test_gitlab_wrapper_compat.py` — Validates: UB-1, UB-2
- [x] 4.2 IMPL: `commands/_common.py` — the JSON printing, the shared argument helpers and the `FIELD_*` keys more
  than one command module reads; `commands/issue.py` — `register(subparsers)` and the `issue` handlers of D6 —
  Files: `gitlab_api/commands/_common.py`, `gitlab_api/commands/issue.py` — Validates: UB-1, UB-2

## Wave 5 — The other commands and the install path
- [x] 5.1 TEST: C, `test_a_subcommand_form` cases for `pipeline status` with and without `--count N`,
  `pipeline log`, `label list`, `label create`, `mr create`, `mr get`, `mr checks`, `mr approve`, `mr merge` and
  `delete-branch`; `test_pipeline_wait_exit_codes` — 0, 10, and 11 with `--timeout-seconds 0`, and `pipeline_wait`
  directly on a `Transport` holding a fake clock and sleep, imported inside the test — Files:
  `src/payload/test/test_gitlab_wrapper_compat.py` — Validates: UB-1
- [x] 5.2 TEST: S `test_both_prompts_copy_the_package_with_the_entry` — each section cut from its heading to the next
  `###` heading, as `test/test_setup_prompts_gitignore.py` cuts PART 3; both GitLab copy steps name
  `src/payload/scripts/gitlab_api/` with the entry script, and both "Shipped Python" lists name `scripts/gitlab_api/`
  — Files: `test/test_setup_prompts_gitlab_wrapper.py` — Validates: UB-1
- [x] 5.3 IMPL: `commands/pipeline.py` — `pipeline status`, `pipeline log` and `pipeline wait` of D6, `pipeline_wait`
  on `transport.sleep` and `transport.clock` with the skeleton's exit constants and output — Files:
  `gitlab_api/commands/pipeline.py` — Validates: UB-1
- [x] 5.4 IMPL: the `label`, `mr` and `delete-branch` handlers of D6; `commands/mr.py`'s docstring carries the own-MR
  approval caveat — Files: `gitlab_api/commands/label.py`, `gitlab_api/commands/mr.py`,
  `gitlab_api/commands/branch.py` — Validates: UB-1
- [x] 5.5 IMPL: D2's install path — `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` Part 6.2 copy
  `src/payload/scripts/gitlab_api/` with the entry script, both "Shipped Python" lists name `scripts/gitlab_api/`,
  the GitLab half of the "skeletons" sentence and Part 5.3's docstring pointers restated as D2 states them (the GitHub text stays #17's), the setup-kiro APPENDIX lists
  `gitlab_api/  # if GitLab` under `scripts/`; the map names the package, its suites and the coverage test, under its
  cap — Files: `prompts/setup-claude.txt`, `prompts/setup-kiro.txt`, `docs/forLLMConsumption.md` — Validates: UB-1

## Final
- [ ] F.1 E2E: Not applicable in this change — nothing deployed changes; the real-instance run stays on #11. The
  fake-host suites above run in CI's `tests` group — Files: none
- [ ] F.2 TEST (verifier evidence; no file edited): `git diff --name-only` against the merge base lists neither
  `src/payload/scripts/github_wrapper.py`, nor a GitHub wrapper test, nor `src/payload/test/test_wrapper_delivery.py`;
  every file the diff adds under `gitlab_api/` is a row of D2's "What a family's change edits" table — Files: none —
  Validates: UB-3, AC-1.3

## Coverage

| Criterion | TEST tasks |
|---|---|
| AC-1.1 | 1.1, 2.2 |
| AC-1.2, AC-5.1, AC-5.2 | 1.3 |
| AC-1.3, UB-3 | F.2 |
| AC-2.1, AC-2.4–AC-2.6, AC-3.1–AC-3.5, AC-4.1–AC-4.3 | 2.1 |
| AC-2.2 | 1.1, 1.2 |
| AC-2.3 | 1.1, 1.2, 2.1 |
| AC-5.3, AC-5.4 | 3.1 |
| UB-1 | 3.2, 4.1, 5.1, 5.2 |
| UB-2 | 2.3, 3.2, 4.1 |
