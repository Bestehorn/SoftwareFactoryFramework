# Change — issue #29: GitHub wrapper rewrite, part 2 slice: orgs, teams, users, apps families

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn"); its D8 names
what a slice edits. Test files: N, V, K, C, P as #28's mapping; F = `src/payload/test/test_github_api_<family>.py`.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed (aafecbb); #29 selected, `prompt.md` derived from its body; no interview (`qa_log.md`).

## Ask

Issue #29: "Map every pending operation of the `orgs`, `teams`, `users` and `apps` families to a record transcribed
from its `docs/api-reference/github/rest/<category>.md` section, reachable through the generic call of sibling 'GitHub
wrapper rewrite, part 2a: …', with fake-host tests", the four `PENDING` sets empty. DL-002 settles its open questions
(the `apps` records that authenticate as the app; the target index).

## Acceptance criteria

- AC-1: Every ID on the `PENDING` of `families/{orgs,teams,users,apps}.py` at aafecbb SHALL have one `RestOperation` in
  its module's `OPERATIONS` whose method and path are its `operations-index.md` row and whose path, query and body
  names are its section's, as N reads them (#28 D5); the four `PENDING` SHALL be empty.
- AC-2: Every new record SHALL carry:
  - `paging` `Paging.LINK` when its section has a `Paging:` line or a `Link` response header, except
    `orgs/list-attestations-bulk` and `users/list-attestations-bulk` (`POST`, #28 D3); every other record
    `Paging.NONE`;
  - `item_key`, for a `Paging.LINK` record, the one key after "items in" in its `Paging:` line, or `None` where that
    line reads "the response body is the array"; `None` for every `Paging.NONE` record;
  - `multi_segment` exactly the names of its `Parameter` rows with `In` `path` that read "may contain `/`
    (multi-segment path)"; a body `Field` row reading so adds no name;
  - `api_version` `API_VERSION_DEFAULT` and `accept` `ACCEPT_JSON`.
- AC-3: WHEN a `Paging.LINK` record of these families is called as `call <id>` with `--path` for each path parameter
  but `owner` and `repo`, plus `--query per_page=1` where it documents `per_page`, against a host serving two items
  under its `item_key` (one per page where `per_page` is given), THEN it SHALL exit 0 and print `printed_json` of both.
- AC-4: WHEN a new record is called through `call` with a value for each parameter its section documents, THEN it
  SHALL exit 0 and send one request with the section's method, expanded path, query names and body names, reachable
  or not (#28 D5).

## Unchanged behaviour

- UB-1: The compatibility subcommands and `CASES` SHALL CONTINUE TO behave as they do, and `users/get-authenticated`
  SHALL CONTINUE TO be declared as it is.
- UB-2: `call` SHALL CONTINUE TO refuse with exit 2 and no request `pulls/merge` and `issues/create`, naming `merge-pr`
  and `create-issue`, an ID no record declares, and an undocumented name.
- UB-3: Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, and the package to import only the
  Python 3.9 standard library.
- UB-4: `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/families/{orgs,teams,users,apps}.py` | records added to `OPERATIONS`, their IDs removed from `PENDING`; each module docstring describes the records it now holds (`users.py` keeps its `users/get-authenticated` text) |
| F, one per family | new |
| `docs/findings-ledger.md` | the Residuals' ledger rows, via `memory_compile.py ledger add` |

Never edited: #28 D8's "never" row, `commands/call.py` included (no record of these families commits to, creates,
moves or renames a branch, creates an issue or merges), and any other doc (#28 D7).

## Tests

Example tests. F's IDs, paths, item keys and multi-segment names are literal tables transcribed from the sections,
never read from the records.

- AC-1 — F `test_nothing_is_pending`: `PENDING` empty and the `OPERATIONS` IDs equal F's tuple of the family's
  index IDs; N `test_every_record_matches_its_reference_section`; V `test_every_operation_is_covered_or_pending`,
  `test_one_module_per_family_holding_only_its_own_ids`.
- AC-2 — F `test_every_record_sends_the_default_version_and_media_type`;
  `test_the_multi_segment_parameters_are_the_sections` (`{operation_id: multi_segment}` over the records with one
  equals F's table of the path rows reading "may contain `/`", empty for `teams` and `apps`);
  `test_every_list_record_has_a_case` (the family's `Paging.LINK` IDs equal F's case IDs, and every `Paging.NONE`
  record's `item_key` is `None`); the `Paging.LINK` `item_key`s are judged by AC-3's routes.
- AC-3 — F `test_a_list_record_prints_every_item`: #28 D8's one `GoldenCase` per `Paging.LINK` record, run with
  `fx.run_product_case`; the cases of `orgs/list-attestations` and `users/list-attestations` give a `subject_digest`
  holding `/`, routed on the path with it literal.
- AC-4 — N `test_every_record_is_sent_as_its_section_documents`; by #28 D5 the `teams`, `apps` and `{org}` records are
  unreachable, so N is their whole proof.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`; the PR diff edits neither the `users/get-authenticated` record nor `CASES`.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`,
  `test_an_undocumented_parameter_is_refused`.
- UB-3 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-4 — `src/payload/test/test_wrapper_delivery.py`; the PR diff names neither file.
- E2E — no deployed system; the real-forge check is #10's. N calls every record, F every list record, through
  `main`'s argv to the API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests` (`run_checks.py`).

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 to TEST-4, one per family (`orgs`, `teams`, `users`, `apps`) | the family's F | AC-1, AC-2, AC-3 |
| IMPL-1 to IMPL-4, one per family | `src/payload/scripts/github_api/families/<family>.py` | AC-1 to AC-4; IMPL-3 UB-1 |

Red after TEST (`python scripts/run_tests.py` on the four F): F's pending and list-set tests fail and its list cases exit 2.
Green after IMPL: F, N, V, K, C and P.

## Residuals

- `teams/check-permissions-for-repo-in-org` sends `ACCEPT_JSON`, not its named
  `application/vnd.github.v3.repository+json` (a media type per call: #28's requirements Residuals).
- An `apps` record that authenticates as the app (a JWT, or the client ID and secret, `conventions.md`
  "Authentication") goes with the configured token (DL-002); another credential source would break UB-3 → ledger.
- Secret body values (`access_token` of the `apps` token records, webhook `secret`, `config.secret`) show in the
  command line (#28 Residuals); `apps/create-installation-access-token`, `apps/check-token`, `apps/reset-token`,
  `apps/scope-token` print a `token`, `apps/create-from-manifest` the app's `client_secret` and `pem`, on stdout.
- `orgs/create-issue-field` and `orgs/create-issue-type` hold `create-issue`, which the installed
  `gate_filing.CREATE_RE` matches inside a longer word (#32 review C2); #32 DL-005 fixes the product gate.
- `orgs/delete`, `teams/delete-*`, `apps/delete-installation` and the permission grants
  (`teams/add-or-update-repo-permissions-*`, `{owner}`/`{repo}` defaulting to `origin`) are outside the gated class
  (#28 Security "Destructive operations").
- No section here has a non-JSON body, an upload or a `307`: nothing is kept pending for #46.
