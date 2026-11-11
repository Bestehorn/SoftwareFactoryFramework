# Change — issue #14: GitHub wrapper rewrite, part 2: the last pending operations

Tier: S (DL-001). Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn").
In `src/payload/test/`: F = `test_github_api_<module>.py` for `pulls`, `code_scanning`, `copilot`; K =
`test_github_api_call.py`, R = `test_github_api_registry.py`, C = `test_github_wrapper_compat.py`. In `test/`: N =
`test_github_wrapper_contract.py`, P = `test_github_wrapper_fork_parity.py`, V = `test_github_wrapper_coverage.py`.

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #14's family slices landed; three IDs stay pending; `prompt.md` from #14's body; no interview
   (`qa_log.md`).

## Ask

Issue #14: "Done: part 1's pending list empty (completes #12 AC-1)". What remains: AC-1's three IDs.

## Acceptance criteria

- AC-1: `pulls/update-branch`, `code-scanning/commit-autofix` and
  `copilot/set-copilot-content-exclusion-for-organization` SHALL each have one `RestOperation` in its family module's
  `OPERATIONS` whose method and path, and whose path, query and body names, are its `rest/<category>.md` section's as
  N reads them (the content-exclusion body's: `{"*"}`, "any key"), with `multi_segment` empty, `Paging.NONE`,
  `item_key` `None`, `API_VERSION_DEFAULT`, `ACCEPT_JSON` and `content_type` `None`.
- AC-2: The `PENDING` of `families/pulls.py`, `code_scanning.py` and `copilot.py` SHALL be empty, leaving every
  family's `PENDING` and `graphql_only.PENDING_CAPABILITIES` empty, and V SHALL pass.
- AC-3: `commands/call.py` `GATED_OPERATIONS` SHALL map to `None` `pulls/update-branch` and
  `code-scanning/commit-autofix`, which write a branch as the official page each section links says. WHEN `call` is
  given either with a value for each parameter its section documents, THEN it SHALL exit 2 before any request,
  logging the ID and that no subcommand sends it.
- AC-4: WHERE a record's `body_params` holds `*`, `call` SHALL send every body member given. WHEN
  `call copilot/set-copilot-content-exclusion-for-organization --path org=<org>` is given one
  `-F <repository>=<JSON array>` per repository, THEN it SHALL exit 0 and send one
  `PUT /orgs/<org>/copilot/content_exclusion` whose JSON body is exactly those members, as the example of the page
  its section links: `{"octo-repo": ["/src/some-dir/kernel.rs"]}`.

## Unchanged behaviour

- UB-1: The compatibility subcommands and `CASES` SHALL CONTINUE TO behave as they do.
- UB-2: `call` SHALL CONTINUE TO refuse with exit 2 and no request every other `GATED_OPERATIONS` ID with its
  message, and an ID no record declares.
- UB-3: `call` and `registry.send` SHALL CONTINUE TO refuse before any request an undocumented body name of a record
  without `*`, and an undocumented path or query name or a missing path parameter of any record.
- UB-4: Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, imports only from the Python 3.9
  standard library.
- UB-5: `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.

## Files

- `src/payload/scripts/github_api/families/pulls.py`, `code_scanning.py`, `copilot.py`: AC-1's record; `PENDING`
  empty; the docstring's pending sentence restated.
- `src/payload/scripts/github_api/commands/call.py`: AC-3's IDs in `GATED_OPERATIONS`; `_undocumented` accepts every
  body name when `body_params` holds `registry.ANY_BODY_NAME`; the module and `check_call` docstrings say so.
- `src/payload/scripts/github_api/registry.py`: `ANY_BODY_NAME = "*"`; `_check_names` accepts every body name when
  `documented` holds it; the module docstring says so.
- F, the three: per Tests.
- `src/payload/test/test_github_api_call.py` (K): `_unknown_cases`' `pending-id` row and `OP_PULLS_UPDATE_BRANCH`
  removed; the AC-2.1 docstrings of `_unknown_cases` and `test_an_unknown_operation_is_refused` name an ID in no row
  of the index.
- `docs/findings-ledger.md`: per open row of #31 DL-003, #32 DL-002, #33 DL-004, one with status
  `enforced <its F path>`.

`registry.py` and `call.py` beyond `GATED_OPERATIONS` are a #28 D8 exception this issue names: a body of any key.
No other file or doc.

## Tests

Example tests. F's IDs, paths, body names and argv are literal, from the sections, never read from the records or
`GATED_OPERATIONS`.

- AC-1 — N `test_every_record_matches_its_reference_section`; V `test_one_module_per_family_holding_only_its_own_ids`;
  F `test_the_records_follow_the_transcription_rules` (pulls, copilot),
  `test_every_record_sends_the_default_version_and_media_type` (code_scanning), copilot's `UNPAGED_IDS` and
  code_scanning's `RECORDED_IDS` gaining their ID; pulls' test reads every record.
- AC-2 — F `test_nothing_is_pending`, replacing `test_only_the_residual_ids_are_pending` (pulls, copilot) and
  `test_only_the_branch_writing_record_is_pending` (code_scanning); V `test_every_operation_is_covered_or_pending`.
- AC-3 — F `test_a_branch_writing_record_is_refused` (pulls, code_scanning), #33 AC-6's form: `registry.lookup`
  returns the record, the run exits 2 with no request, `fx.assert_log` finds the ID and the refusal.
- AC-4 — F `test_the_content_exclusion_map_is_sent_as_given` (copilot), through `fx.run_product_case`: `--path org=…`
  and two `-F` members, a string array and an array holding an `ifAnyMatch` object; exit 0, one `PUT` to the
  expanded path, its JSON body exactly the two members. N `test_every_record_is_sent_as_its_section_documents`.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; #27's and #33's
  `test_a_branch_writing_record_is_refused`.
- UB-3 — K `test_an_undocumented_parameter_is_refused`, `test_a_missing_path_parameter_is_refused`; R
  `test_call_refuses_an_undocumented_parameter`; F `test_the_content_exclusion_call_checks_its_query` (copilot):
  `--path org=…`, one `-F` member and an undocumented `--query` name exit 2 with no request, and `fx.assert_log` finds
  the query name with its kind.
- UB-4 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-5 — `test_wrapper_delivery.py`; the PR diff names neither file.
- E2E — no deployed system; the real-forge check is #10's (`sff-test-*`). F and N run `call` through `main` to the
  API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

- TEST-1 — Files: `src/payload/test/test_github_api_pulls.py`, `src/payload/test/test_github_api_call.py`.
  Validates: AC-1, AC-2, AC-3.
- TEST-2 — Files: `src/payload/test/test_github_api_code_scanning.py`. Validates: AC-1, AC-2, AC-3.
- TEST-3 — Files: `src/payload/test/test_github_api_copilot.py`. Validates: AC-1, AC-2, AC-4, UB-3.
- Red: the three F modules; `test_nothing_is_pending` fails, AC-3's cases find no record, AC-4's case exits 2.
- IMPL-1 — Files: `src/payload/scripts/github_api/families/pulls.py`. Validates: AC-1, AC-2.
- IMPL-2 — Files: `src/payload/scripts/github_api/families/code_scanning.py`. Validates: AC-1, AC-2.
- IMPL-3 — Files: `src/payload/scripts/github_api/families/copilot.py`. Validates: AC-1, AC-2.
- IMPL-4 — Files: `src/payload/scripts/github_api/commands/call.py`. Validates: AC-3, AC-4, UB-2, UB-3.
- IMPL-5 — Files: `src/payload/scripts/github_api/registry.py`. Validates: AC-4, UB-3.
- Green: F (the three), K, R, N, V, C, P. The wave's commit carries the ledger rows.

## Residuals

- AC-4's ID replaces the organisation's exclusion rules and writes no branch, so it stays callable (#28 Security
  "Destructive operations").
