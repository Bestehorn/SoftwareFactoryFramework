# Tasks — issue #17: GitHub wrapper rewrite, part 1

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved). Test files as design § Acceptance
Criteria Mapping: T = `src/payload/test/test_github_api_transport.py`, R = `src/payload/test/test_github_api_registry.py`,
C = `src/payload/test/test_github_wrapper_compat.py`, V = `test/test_github_wrapper_coverage.py`,
P = `test/test_github_wrapper_fork_parity.py`, S = `test/test_setup_prompts_github_wrapper.py`. Package paths below are
under `src/payload/scripts/`. Each test does what design § Correctness Properties states for its criterion.

## Wave 1 — Errors, transport and the fake host

Run: `python scripts/run_tests.py src/payload/test/test_github_api_transport.py`

- [x] 1.1 TEST: the fake host and the transport tests. The fixtures module (loaded by path as
  `test_wrapper_delivery.load` loads a wrapper, never collected) holds `FakeGitHub`: installed with `monkeypatch` over
  `urllib.request.HTTPSHandler.https_open` and `HTTPHandler.http_open`; answers with `urllib.response.addinfourl`
  objects with `msg` set; records each request's method, URL, body and the headers `do_open` sends
  (`unredirected_hdrs` merged with `headers`, compared case-insensitively); matches static routes on method, URL path
  and decoded query, serving a route's responses in order with the last repeating; serves list routes as
  `page`/`per_page` slices with a `link` `rel="next"`; fails the test on an unrouted request. T, with a recording
  `sleep` and a fixed `clock`: `test_every_rest_request_sends_the_api_version`, `test_link_pages_are_followed_as_given`,
  `test_wrapped_pages_return_the_item_key_items`, `test_an_asset_is_uploaded_to_the_upload_url`,
  `test_a_cross_origin_redirect_drops_the_credential`, `test_a_rate_limit_is_waited_out_and_retried`,
  `test_spent_retries_raise_naming_the_limit`, `test_an_error_status_raises_with_the_documented_body`,
  `test_graphql_posts_query_and_variables`, `test_graphql_follows_page_info_cursors`,
  `test_graphql_errors_raise_even_with_200`. Every line holding a URL with a `user:…@` part (the AC-3.1 redirect
  target) ends with `# pragma: allowlist secret`. — Files: src/payload/test/github_wrapper_fixtures.py,
  src/payload/test/test_github_api_transport.py — Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-3.1, AC-3.2, AC-3.3,
  AC-3.4, AC-4.1, AC-4.2, AC-4.3
- [x] 1.2 IMPL: `errors.py` — `GitHubAPIError(message, status_code=None, details=None)`, `GitHubRateLimitError`,
  `GitHubGraphQLResponseError` (X2); `transport.py` — D3's constants, `origin`, `CredentialStrippingRedirectHandler`,
  `build_opener`, `Transport` (`_send`, `request`, `pages`, `upload`, `download`, `graphql`, `graphql_nodes`) and D3's
  failures, every response value in a message or log line rendered with `json.dumps`; `__init__.py` empty. — Files:
  src/payload/scripts/github_api/__init__.py, src/payload/scripts/github_api/errors.py,
  src/payload/scripts/github_api/transport.py — Validates: AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-3.1, AC-3.2, AC-3.3,
  AC-3.4, AC-4.1, AC-4.2, AC-4.3

## Wave 2 — Registry

Run: `python scripts/run_tests.py src/payload/test/test_github_api_registry.py`

- [x] 2.1 TEST: R, against a synthetic family module and a `Transport` on the fake host:
  `test_call_refuses_an_undocumented_parameter` (a query or body name the record does not document raises
  `ValueError`, no request recorded) and `test_expand_encodes_and_refuses_dot_segments` (`/` and a space
  percent-encoded in a single-segment value, `/` kept in a multi-segment one, a `.` or `..` segment refused with
  `GitHubAPIError`). — Files: src/payload/test/test_github_api_registry.py — Validates: AC-1.1
- [x] 2.2 IMPL: `registry.py` per D4 — `Paging`, `RestOperation`, `GraphQLOperation`, `discover_families()` (sorted
  `pkgutil.iter_modules` over `github_api.families`, imported by absolute name), `lookup` (`ValueError` for an unknown
  or twice-declared ID), `expand`, `call`, `pages`; `families/__init__.py` empty. — Files:
  src/payload/scripts/github_api/registry.py, src/payload/scripts/github_api/families/__init__.py — Validates: AC-1.1

## Wave 3 — Families, GraphQL capabilities and the coverage test

Run: `python scripts/run_tests.py test/test_github_wrapper_coverage.py src/payload/test/test_github_api_registry.py`

- [ ] 3.1 TEST: V per D7 — `index_rows`, `graphql_only` and the pure `coverage_gaps`, the package loaded with
  `src/payload/scripts` on `sys.path`; `test_the_reference_is_read_whole`, `test_a_gap_is_named` (synthetic index),
  `test_every_operation_is_covered_or_pending` (its failure message lists every gap),
  `test_discovery_follows_the_directory`, `test_one_module_per_family_holding_only_its_own_ids`,
  `test_the_wrapper_imports_only_the_standard_library` (the entry script and every module under `github_api/`). —
  Files: test/test_github_wrapper_coverage.py — Validates: AC-1.2, AC-1.3, AC-5.1, AC-5.2, AC-5.3, UB-2.2
- [ ] 3.2 IMPL: the records D5 names for the issues and claim commands — `issues/list-for-repo`, `issues/get`,
  `issues/list-comments`, `issues/create`, `issues/update`, `issues/create-comment`, `issues/add-labels`,
  `issues/remove-label`, `issues/add-assignees`, `issues/remove-assignees`, `users/get-authenticated` — each with its
  index row, the parameter names documented in the section its index row's Reference links, its paging kind and item
  key (D4); each module's `FAMILY`, and `PENDING` every other ID of the family. — Files:
  src/payload/scripts/github_api/families/issues.py, src/payload/scripts/github_api/families/users.py — Validates:
  AC-1.2, AC-1.3, AC-5.3
- [ ] 3.3 IMPL: as 3.2 for `pulls/create`, `pulls/get`, `pulls/create-review`, `pulls/merge`, `checks/list-for-ref`,
  `repos/get-combined-status-for-ref`. — Files: src/payload/scripts/github_api/families/pulls.py,
  src/payload/scripts/github_api/families/checks.py, src/payload/scripts/github_api/families/repos.py — Validates:
  AC-1.2, AC-1.3, AC-5.3
- [ ] 3.4 IMPL: as 3.2 for `actions/list-repo-workflows`, `actions/list-workflow-runs-for-repo`,
  `actions/list-workflow-runs`, `actions/get-workflow-run`, `actions/download-workflow-run-logs`, `git/delete-ref`
  (`ref` in `multi_segment`). — Files: src/payload/scripts/github_api/families/actions.py,
  src/payload/scripts/github_api/families/git.py — Validates: AC-1.2, AC-1.3, AC-5.3
- [ ] 3.5 IMPL: `graphql_only.py` — `OPERATIONS` empty (D5 declares no `GraphQLOperation`), `PENDING_CAPABILITIES`
  every first cell of the "Only in GraphQL" table, verbatim; and one module per index family 3.2–3.4 do not own, each
  with `FAMILY`, an empty `OPERATIONS` and `PENDING` every ID of the family (D2 requires a module per family, so this
  one data task spans more than three files). — Files: src/payload/scripts/github_api/graphql_only.py,
  src/payload/scripts/github_api/families/<family>.py (each family 3.2–3.4 do not own) — Validates: AC-1.2, AC-1.3,
  AC-5.3

## Wave 4 — Entry script and the issues commands

Run: `python scripts/run_tests.py src/payload/test/test_github_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_github_wrapper_coverage.py test/test_github_wrapper_fork_parity.py`

- [ ] 4.1 TEST: `CASES` in the fixtures module — argv, host state, exact stdout, exit code and the expected non-GET
  requests (method, path, decoded query, JSON body), every golden value the fork's own output — for each issues
  subcommand of UB-1.1: exit 0; exit 1 from a `GitHubAPIError`; exit 2 for a usage error, a credential refusal and a
  repository refusal; `list-issues --label <name>`; and rows marked C-only: `list-issues --token-stdin` and
  `create-issue --token-stdin` (exit 2, empty stdout, no request) and the two userinfo `origin` cases of design
  UB-1.1 (exit 2, empty stdout, the `caplog` refusal naming `.git/config` and `github.com/o/socket.io.git`, neither
  the records nor stderr holding the token or the password), each line holding a `user:…@` URL ending with
  `# pragma: allowlist secret`. C, in a temporary project (fixture `credentials/github-pat.txt`, `.git/config` with a
  GitHub `origin`), stdout by `capsys`, the exit code from the return value or `SystemExit`:
  `test_a_subcommand_matches_its_golden_case` (over `CASES`), `test_a_delivery_verb_delegates_to_the_steward`,
  `test_the_script_runs_by_path`, `test_the_credential_comes_only_from_the_file`,
  `test_the_module_loads_without_credential_or_network`. P: `test_the_fork_produces_the_golden_case` runs every
  `CASES` row except the delivery verbs and the C-only rows against the installed fork `scripts/github_wrapper.py`
  (`sys.argv` set) in a temporary project and fixture token built as C builds them, comparing stdout, exit code and
  non-GET requests. `test_wrapper_delivery.py` runs unchanged in this wave's captures. — Files:
  src/payload/test/github_wrapper_fixtures.py, src/payload/test/test_github_wrapper_compat.py,
  test/test_github_wrapper_fork_parity.py — Validates: UB-1.1, UB-1.2, UB-1.3, UB-2.1, UB-3.1, UB-3.2
- [ ] 4.2 IMPL: the entry script per D6 — the `sys.path` insertion, the skeleton's kept names, the fork's bodies of
  `_load_token` and `_detect_repo` (its message without the URL's userinfo), `GitHubAPIError` re-exported, the
  skeleton's `_api_request`, `wait_run`, `API_ROOT`, field constants and instructions block removed, `main(argv=None)`
  steps 1–6, `_build_parser()` with the delivery subcommands and every discovered command module (`_`-prefixed
  skipped), and `__main__`'s logging; `commands/__init__.py` empty. — Files: src/payload/scripts/github_wrapper.py,
  src/payload/scripts/github_api/commands/__init__.py — Validates: UB-1.1, UB-1.2, UB-1.3, UB-2.1, UB-3.1, UB-3.2
- [ ] 4.3 IMPL: `commands/_common.py` (body resolution, JSON printing, the fork's `FIELD_*` names) and
  `commands/issues.py` — `register(subparsers)` with the fork's arguments of `list-issues`, `get-issue`,
  `get-issue-comments`, `comment-issue`, `create-issue`, `update-issue`, `reopen-issue`, `checklist` (no
  `--token-stdin`), and handlers `(*, transport, owner, repo, args)` that re-create the fork handlers' requests and
  stdout on D5's records (`list-issues` and `get-issue-comments` follow `link`). — Files:
  src/payload/scripts/github_api/commands/_common.py, src/payload/scripts/github_api/commands/issues.py — Validates:
  UB-1.1

## Wave 5 — Claim, pull-request and CI commands; fork parity; setup prompts

Run: `python scripts/run_tests.py src/payload/test/test_github_wrapper_compat.py src/payload/test/test_wrapper_delivery.py test/test_github_wrapper_coverage.py test/test_github_wrapper_fork_parity.py test/test_setup_prompts_github_wrapper.py test/test_layout.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_setup_prompts_gitignore.py test/test_agent_rule_references.py test/test_no_ai_attribution_rule.py test/test_post_activity_prompts.py`

- [ ] 5.1 TEST: `CASES` rows for each claim, pull-request and CI subcommand of UB-1.1 and each nested `issue …`
  spelling: exit 3 (`claim-check` on an open unclaimed issue); 10 and 11 (`wait-run`, `--timeout-seconds 0`);
  `start-issue` and `issue start` on an open unclaimed issue (exit 0); `get-logs` served the `302` to a storage host;
  each with its expected non-GET requests. — Files: src/payload/test/github_wrapper_fixtures.py — Validates: UB-1.1
- [ ] 5.2 TEST: P — adds `test_the_parsers_match_option_by_option`, comparing the fork's and the product's
  `_build_parser()` subparsers for each caller-used subcommand of the fork's parser and each nested spelling, except
  the fork's `--token-stdin`. — Files: test/test_github_wrapper_fork_parity.py —
  Validates: UB-1.1
- [ ] 5.3 TEST: S — `test_the_setup_prompts_copy_the_package`: Part 5.3 of `prompts/setup-claude.txt` and Part 6.2
  of `prompts/setup-kiro.txt`, each cut to the next `### Part` heading as `test/test_setup_prompts_gitignore.py` cuts
  PART 3, name `src/payload/scripts/github_api/` beside `src/payload/scripts/github_wrapper.py`; each shipped-Python
  list, cut to the next `###` heading, names `scripts/github_api/`. — Files: test/test_setup_prompts_github_wrapper.py
  — Validates: UB-1.3
- [ ] 5.4 IMPL: `commands/claim.py` — `start-issue`, `release-issue`, `claim-check`, `label-add`, `label-remove`,
  `assign` and the nested `issue` group, both spellings sharing one argument helper and one handler (the fork's
  `ISSUE_GROUP_DISPATCH`). — Files: src/payload/scripts/github_api/commands/claim.py — Validates: UB-1.1
- [ ] 5.5 IMPL: `commands/pulls.py` — `create-pr`, `get-pr`, `get-pr-checks`, `approve-pr`, `merge-pr`,
  `delete-remote-branch`; the module docstring carries the PR endpoints and `cmd_approve_pr`'s own-PR approval caveat.
  — Files: src/payload/scripts/github_api/commands/pulls.py — Validates: UB-1.1
- [ ] 5.6 IMPL: `commands/ci.py` — `list-workflows`, `list-runs`, `get-run`, `wait-run` (the fork's poll, deadline
  check, sleep order and defaults), `get-logs` (`Transport.download`, the fork's archive printing). — Files:
  src/payload/scripts/github_api/commands/ci.py — Validates: UB-1.1
- [ ] 5.7 IMPL: D8's edits — Part 5.3 (copy step, the docstring pointers, the skeletons sentence's GitHub half) and
  the shipped-Python list of `setup-claude.txt`; Part 6.2 (copy step, skeletons sentence), the APPENDIX directory
  structure and the shipped-Python list of `setup-kiro.txt`, each GitLab half as the tree holds it; and the map
  `docs/forLLMConsumption.md` names `src/payload/scripts/github_api/`, under its cap. — Files: prompts/setup-claude.txt,
  prompts/setup-kiro.txt, docs/forLLMConsumption.md — Validates: UB-1.3

## Final

- [ ] F.1 E2E: stops at the API boundary until #10's ephemeral `sff-test-*` fixture exists (requirements
  § Residuals; its work item stays open on #17). Until then the CLI runs through its real interface in `test_the_script_runs_by_path` and the golden `CASES`, in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`). — Files: none
- [ ] F.2 VERIFY: the branch's diff against `origin/main` names neither `src/payload/scripts/gitlab_wrapper.py` nor
  `src/payload/test/test_wrapper_delivery.py`. — Files: none (read-only) — Validates: UB-3.1

Design § Residuals X4: its one findings-ledger row is routed by the conductor, not an implementer task.

## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 2.1 |
| AC-1.2, AC-1.3, AC-5.1, AC-5.2, AC-5.3, UB-2.2 | 3.1 |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-4.1, AC-4.2, AC-4.3 | 1.1 |
| UB-1.1 | 4.1, 5.1, 5.2 |
| UB-1.2, UB-2.1, UB-3.2 | 4.1 |
| UB-1.3 | 4.1, 5.3 |
| UB-3.1 | 4.1, F.2 |
