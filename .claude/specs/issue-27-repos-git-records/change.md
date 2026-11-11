# Change — issue #27: GitHub wrapper rewrite, part 2 slice: repos and git families

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn").

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed; #27 selected, `prompt.md` from its body; no interview.

## Ask

Issue #27: cover #14's slice "Families: repos, branches, commits, git, releases, deployments, pages": each pending
`repos/*` and `git/*` ID gets a record transcribed from its `docs/api-reference/github/rest/<category>.md` section,
called through `call <operation-id>` (#28), with fake-host tests, and both `PENDING` emptied. Open questions (#28 D5):
an `{org}` path is unreachable, proven by N alone; `/user…` and `/users/{username}/repos` are reachable, their
real-forge run #10's.

## Acceptance criteria

- AC-1 Every ID on the `PENDING` of `families/git.py` and `families/repos.py` before this change SHALL have one
  `RestOperation` in its module's `OPERATIONS`, except `repos/upload-release-asset`: `git.PENDING` SHALL be empty and
  `repos.PENDING` exactly `{"repos/upload-release-asset"}` per DL-002.
- AC-2 Each new record's `method`, `path`, `query_params` and `body_params` SHALL be those of its section as N's
  `reference_sections` reads it.
- AC-3 Each new record's `multi_segment` SHALL hold exactly the path parameters whose `Parameter` row reads "may contain
  `/` (multi-segment path)"; its `api_version` SHALL be `API_VERSION_DEFAULT` and its `accept` `ACCEPT_JSON`.
- AC-4 A new record SHALL be `Paging.LINK` when its section has a `Paging:` line or a `Link` response header, with
  `item_key` the one key after "items in", or `None` when its `Paging:` line or `200` response gives the body as an
  array. Every other record, and `repos/get-commit` and `repos/compare-commits` (two keys in their `Paging:` line),
  SHALL be `Paging.NONE`.
- AC-5 WHEN a record of either family outside `GATED_OPERATIONS` is called with `call <id>` and a value for every
  parameter its section documents, THE wrapper SHALL send one request with the section's method, path, query and body
  names and exit 0, reachable or not (#28 D5).
- AC-6 WHEN a `Paging.LINK` record of either family is called against a fake host serving two items under its
  `item_key` (one per page where the record documents `per_page`), THE wrapper SHALL print both as one JSON array.
- AC-7 `commands/call.py` `GATED_OPERATIONS` SHALL map to no subcommand the records whose call commits to, creates,
  moves or renames a branch: `repos/merge`, `repos/merge-upstream`, `repos/rename-branch`,
  `repos/create-or-update-file-contents`, `repos/delete-file`, `git/create-ref`, `git/update-ref`. WHEN `call` is given
  one, THE wrapper SHALL exit 2 before any request, logging the ID and that no subcommand sends it.

## Unchanged behaviour

- UB-1 Every compatibility subcommand SHALL CONTINUE TO work with its arguments, output and exit codes, on the
  unchanged records `repos/get-combined-status-for-ref` and `git/delete-ref`.
- UB-2 Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, imports only from the Python 3.9
  standard library.
- UB-3 `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.
- UB-4 `call` SHALL CONTINUE TO refuse `pulls/merge` and `issues/create` naming `merge-pr` and `create-issue`, and to
  send `git/delete-ref`.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/families/repos.py` | the records; `PENDING` per AC-1; docstring |
| `src/payload/scripts/github_api/families/git.py` | the records; `PENDING` empty; docstring |
| `src/payload/scripts/github_api/commands/call.py` | `GATED_OPERATIONS: Mapping[str, Optional[str]]` with AC-7's IDs mapped to `None`; `refuse_gated` refuses every ID in it by membership, worded for `None`; module docstring (#28 D8 exceptions row) |
| `src/payload/test/test_github_api_repos.py`, `src/payload/test/test_github_api_git.py` | new |
| `docs/findings-ledger.md` | the Residuals' rows, via `memory_compile.py ledger add` |

Nothing else (#28 D8 "never"), no other doc (#28 D7).

## Tests

Example tests. In `src/payload/test/`: F = `test_github_api_<family>.py`, its expected IDs, paths and item keys
transcribed from the sections, never read from the records; C = `test_github_wrapper_compat.py`, K =
`test_github_api_call.py`. N = `test/test_github_wrapper_contract.py`, P = `test/test_github_wrapper_fork_parity.py`,
V = `test/test_github_wrapper_coverage.py`; C, K, N, P, V unedited.

- AC-1 — F `test_only_the_upload_is_pending` (repos), `test_nothing_is_pending` (git); V
  `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids`.
- AC-2 — N `test_every_record_matches_its_reference_section`.
- AC-3 — F `test_every_record_sends_the_default_version_and_media_type`,
  `test_the_multi_segment_parameters_are_the_sections` (`{operation_id: multi_segment}` over the records with one
  equals F's "may contain `/`" table), plus the `ref`-holding-`/` cases of `git/list-matching-refs`,
  `repos/list-commit-statuses-for-ref`.
- AC-4 — F `test_every_list_record_has_a_case` (the family's `Paging.LINK` IDs equal F's case IDs) and AC-6's cases.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`.
- AC-6 — F `test_a_list_record_prints_every_item`: #28 D8's one `GoldenCase` per `Paging.LINK` record.
- AC-7 — F `test_a_branch_writing_record_is_refused`, over AC-7's IDs of the family, a literal tuple in F, never read
  from `GATED_OPERATIONS`: `registry.lookup` returns the record, the run exits 2 with no request, `fx.assert_log` finds
  the ID and the refusal.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`.
- UB-2 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-3 — `test_wrapper_delivery.py`; the PR diff names neither file.
- UB-4 — K `test_a_gated_operation_names_its_subcommand`, `test_a_json_or_empty_body_prints_as_documented`.
- E2E — the real-forge run is #10's, on an `sff-test-*` repository. Until then N and F run `call` through
  the product's `main` up to the API boundary in CI job `verify`, leg `tests`.

## Tasks (one wave)

- TEST-1 — F for `repos`. Files: `src/payload/test/test_github_api_repos.py`. Validates: AC-1, AC-3, AC-4, AC-6, AC-7.
- TEST-2 — F for `git`. Files: `src/payload/test/test_github_api_git.py`. Validates: AC-1, AC-3, AC-4, AC-6, AC-7.
- Red: `python scripts/run_tests.py` on both F modules.
- IMPL-1 — Files: `src/payload/scripts/github_api/families/repos.py`. Validates: AC-1 to AC-6, UB-1.
- IMPL-2 — Files: `src/payload/scripts/github_api/families/git.py`. Validates: AC-1 to AC-6, UB-1.
- IMPL-3 — Files: `src/payload/scripts/github_api/commands/call.py`. Validates: AC-7, UB-4.
- Green: both F modules, C, K, N, P and V.

## Residuals

- Split by DL-002, deferral recorded on #27: `repos/upload-release-asset` (`call` has no byte body, media type or
  upload origin; `Transport.upload` exists) and the `307` re-send of `repos/update`, `repos/delete` (exit 1, #28 D4).
- `repos/get-commit`, `repos/compare-commits` print one page of `files`/`commits`; paging them needs a record field
  → ledger.
- `git/delete-ref` stays callable (UB-4, #28 Residuals) → ledger.
- Branch protection, rulesets, `repos/update`, `repos/delete`, `repos/transfer` are outside AC-7's class (#28
  Security "Destructive operations"). `repos/create-deployment` (`auto_merge`) merges the default branch into `ref`,
  never into the default branch, and stays callable.
- The usage docstring names only `pulls/merge`, `issues/create` as refused (#28 D8 "never").
