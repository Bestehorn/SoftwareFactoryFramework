# Change — issue #33: GitHub wrapper rewrite, part 2 slice: the remaining 31 families

Tier: S (DL-001). Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn").
N, V, K, C, P as #28's test mapping; F = `src/payload/test/test_github_api_<module>.py`, `<module>` the family with
`-` as `_`.

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed (aafecbb); #33 selected, `prompt.md` from its body; no interview.

## Ask

Issue #33: "Give every pending operation of 31 family modules a record reachable through #28's generic call (part
2a), leaving each module's `PENDING` empty."

## Acceptance criteria

- AC-1: Every ID on the 31 family modules' `PENDING` at aafecbb except AC-2's SHALL have one `RestOperation` in its
  module whose method and path are its index row and whose path, query and body names are its linked section's, as N
  reads them (#28 D5).
- AC-2: The 31 `PENDING` SHALL be empty but for `markdown/render-raw` (DL-001) and
  `copilot/set-copilot-content-exclusion-for-organization` (DL-004).
- AC-3: Every new record SHALL be `Paging.LINK` when its section has a `Paging:` line or a `200` array with a `Link`
  header (`dependency-graph/diff-range`), else `Paging.NONE`; its `item_key` SHALL be the key after "items in" in that
  line (`conventions.md` "Lists wrapped in an object"), else `None`; its `multi_segment` empty; its `api_version`
  `API_VERSION_DEFAULT` and its `accept` `ACCEPT_JSON`.
- AC-4: WHEN a `Paging.LINK` record is called with #28 D8's argv against a host serving two items under its
  `item_key` (one per page where it documents `per_page`), THEN it SHALL exit 0 and print `printed_json` of both.
- AC-5: WHEN a new record outside `GATED_OPERATIONS` is called through `call` with a value for each parameter its
  section documents, THEN it SHALL exit 0 and send one request with the section's method, expanded path, query names
  and body names, reachable or not (#28 D5).
- AC-6: `commands/call.py` `GATED_OPERATIONS` SHALL map to `None` the records whose call writes a branch or creates
  issues: `agent-tasks/create-task-in-repo`, `agent-merge/put-agent-merge-enrollment`,
  `agent-automations/create-repo-automation`, `agent-automations/edit-repo-automation`,
  `agent-automations/create-repo-automation-task`, `codespaces/export-for-authenticated-user`,
  `campaigns/create-campaign`. WHEN `call` is given one, THEN it SHALL exit 2 before any request, logging the ID and
  that no subcommand sends it.

## Unchanged behaviour

- UB-1: The compatibility subcommands and `CASES` SHALL CONTINUE TO behave as they do.
- UB-2: `call` SHALL CONTINUE TO refuse with exit 2 and no request `pulls/merge` and `issues/create`, naming
  `merge-pr` and `create-issue`, #27's seven `None` entries, and an ID no record declares, AC-2's included.
- UB-3: `call` SHALL CONTINUE TO write a non-JSON body unchanged (#28 D3), as `markdown/render`, `meta/get-zen` and
  `meta/get-octocat` answer (DL-002).
- UB-4: Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, imports only from the Python 3.9
  standard library.
- UB-5: `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/families/<module>.py`, the 31 | records in `OPERATIONS`; `PENDING` per AC-2; a docstring describing them |
| F, one per family | new |
| `src/payload/scripts/github_api/commands/call.py` | AC-6's IDs added to `GATED_OPERATIONS`; its comment and the module docstring name issue creation |
| N | step 3 of `test_an_unreachable_call_matches_its_reference_section` drops the declared `billing/update-budget-org` before adding its own |
| `docs/findings-ledger.md` | the Residuals' ledger rows, via `memory_compile.py ledger add` |

Beyond #28 D8's slice table and exceptions row only N is edited; no doc but the ledger.

## Tests

Example tests. F's tables are literal, from the sections its index rows link and `conventions.md`, never from the
records: the family's IDs, its AC-2 IDs, each paged ID with its path and item key, each AC-6 ID with its arguments.
F's tests are #32's three and AC-6's; a parametrized one is absent where its table is empty.

- AC-1 — N `test_every_record_matches_its_reference_section`; V `test_every_operation_is_covered_or_pending`,
  `test_one_module_per_family_holding_only_its_own_ids`.
- AC-2 — F `test_only_the_residual_ids_are_pending`.
- AC-3 — F `test_the_records_follow_the_transcription_rules`: the `Paging.LINK` IDs equal F's paged IDs and every
  other AC-3 field is AC-3's; AC-4's routes judge paged `item_key`s.
- AC-4 — F `test_a_paged_record_prints_every_page`: #28 D8's `GoldenCase` per paged ID via `fx.run_product_case`, one
  request per item where it documents `per_page`, else one.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`,
  `test_an_unreachable_call_matches_its_reference_section`.
- AC-6 — F `test_a_branch_writing_record_is_refused` over its AC-6 IDs, never read from `GATED_OPERATIONS`:
  `registry.lookup` returns the record, the run exits 2 with no request, `fx.assert_log` finds the ID and the refusal.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; AC-2's F test;
  #27's `test_a_branch_writing_record_is_refused`.
- UB-3 — K `test_a_body_that_is_not_json_is_written_unchanged`.
- UB-4 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-5 — `test_wrapper_delivery.py`; the PR diff names neither file.
- E2E — no deployed system; the real-forge check is #10's (`sff-test-*`). N and F run `call` through `main` to the
  API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

TEST-n writes F and IMPL-n edits `src/payload/scripts/github_api/families/<module>.py` for each `<module>` of work
item n; TEST-n validates AC-1 to AC-4, UB-2 and (n ≠ 3) AC-6, IMPL-n AC-1 to AC-5. IMPL-5 edits
`src/payload/scripts/github_api/commands/call.py`; it validates AC-6 and UB-2.

| n | `<module>` |
|---|---|
| 1 | `agent_automations`, `agent_merge`, `agent_tasks`, `agents`, `copilot`, `copilot_spaces` |
| 2 | `codespaces`, `migrations`, `packages`, `projects` |
| 3 | `code_quality`, `code_security`, `dependency_graph`, `oidc`, `private_registries`, `security_advisories` |
| 4 | `api_insights`, `billing`, `campaigns`, `classroom`, `codes_of_conduct`, `credentials`, `emojis`, `gitignore`, `hosted_compute`, `interactions`, `licenses`, `markdown`, `meta`, `pull_request_stacks`, `rate_limit`; TEST-4 also edits N (AC-5) |

Red after TEST: F's pending tests fail, its paged cases exit 2, its AC-6 cases find no record; N passes. Green
after IMPL: F, N, V, K, C, P.

## Residuals

- The `copilot` content-exclusion `PUT` takes a body of any key (`*`), which D4 refuses (#28 Residuals) → ledger.
- Declared, not for #46: the `302` downloads `dependency-graph/fetch-sbom-report`,
  `migrations/download-archive-for-org`, `migrations/get-archive-for-authenticated-user` (#28 D3).
- `gitignore/get-template`, `licenses/get-for-repo` send `ACCEPT_JSON`, not their `raw`/`html` types (#28's
  requirements residual) → ledger.
- Declared, writing no branch: the retired Source Imports records (`…/import…`); `pull-request-stacks/*`;
  `codespaces/publish-for-authenticated-user`, `security-advisories/create-fork`, `projects/create-draft-item-*`,
  `credentials/revoke`, `packages/delete-*` (#28 Security "Destructive operations").
- Secret writes send `encrypted_value` and `key_id` as given (#31 DL-002).
