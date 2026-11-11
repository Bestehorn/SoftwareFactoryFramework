# Change — issue #36: GitLab wrapper rewrite, part 2 slice: the no-stage-assigned group

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"); its D8
names what a slice edits. Test files: N, V, K, C, P as #41's mapping; F =
`src/payload/test/test_gitlab_api_no_stage_assigned.py`.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed (3beba95); #36 selected, `prompt.md` derived from its body; no interview (`qa_log.md`).

## Ask

Issue #36: "Done: each pending key has a `RestOperation` from its row's `rest/no-stage-assigned.md` attribute table,
reachable through the generic call of the sibling child … (this slice is blocked by it), with fake-host tests, and
`PENDING` empty." Its open questions: every table row is a `Param`, "in OpenAPI only" rows included (DL-002); a secret
value is `-f` text like any other string (DL-003).

## Acceptance criteria

- AC-1 Every key on the `PENDING` of `families/no_stage_assigned.py` at 3beba95 SHALL have one `RestOperation` in its
  `OPERATIONS` whose `operation_id` is its `operations-index.md` row's Reference (`no-stage-assigned#<anchor>`) and
  whose `method` and `path` are that row's, verbatim (the `GET …/integration/google-cloud-platform-…` paths included);
  `PENDING` SHALL be empty.
- AC-2 Each new record SHALL declare one `Param` per row of its section's table as N's `reference_sections` reads it,
  "in OpenAPI only" and deprecated rows included: its row's `In` as its location, `required=True` exactly where
  Required reads `yes`, `Kind.ARRAY` for an `array of strings` row and `Kind.SCALAR` for every other. A section without
  a table declares none. Every new record SHALL have `body` `BodyFormat.JSON` and no `fixed` pairs.
- AC-3 `no-stage-assigned#list-all-active-integrations` and `no-stage-assigned#list-all-active-integrations-1` SHALL be
  `Paging.OFFSET` (DL-004), and every other new record `Paging.NONE`.
- AC-4 WHEN a new record is called with `call <id>` and a value for each path parameter and `Param`, THE wrapper SHALL
  exit 0 and send one request with its section's method, expanded path and body names (#41 D5).
- AC-5 WHEN a record of AC-3 is called against a fake host serving two pages, the second asked for by `x-next-page`,
  THE wrapper SHALL exit 0 and print the items of both as one JSON array; the group record, given `--path id=g/sub`,
  SHALL request `/groups/g%2Fsub/integrations`, and the project record, given no `id`,
  `/projects/<project_id>/integrations`.
- AC-6 WHEN `no-stage-assigned#set-up-jira-issues` is called with `-f url=…`, `-F jira_auth_type=1`,
  `-F use_inherited_settings=true` and `-F 'project_keys=["A"]'`, THE wrapper SHALL send one `PUT` whose JSON body
  equals those four values.

## Unchanged behaviour

- UB-1 Every compatibility subcommand SHALL CONTINUE TO accept the argv and return the exit codes its callers use.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `ai-coding#merge-a-merge-request` and
  `plan#create-an-issue`, naming `mr merge` and `issue create`, and an ID no record declares; `GATED_OPERATIONS` SHALL
  CONTINUE TO hold only those two IDs (no record here commits to or merges into a branch, or creates an issue).
- UB-3 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`, and the package to import only the Python 3.9
  standard library.
- UB-4 `src/payload/scripts/github_wrapper.py`, `github_api/` and their tests SHALL CONTINUE TO be untouched, and
  `src/payload/test/test_wrapper_delivery.py` to pass.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_api/families/no_stage_assigned.py` | the records in `OPERATIONS`, each under a comment naming its page and section; `PENDING` empty; both typed as part 1's modules type them; the module docstring describes the records |
| F | new |
| `docs/findings-ledger.md` | the Residuals' ledger row, via `memory_compile.py ledger add` |

Nothing else: no file of #41 D8's "never" row, `commands/call.py` included (UB-2), and no other doc.

## Tests

Example tests. F's IDs, `ARRAY` names, required names and paged IDs are literal tables transcribed from the sections,
never read from the records. C, K, N, P and V are unedited.

- AC-1 — F `test_nothing_is_pending` (`PENDING` empty; the `OPERATIONS` IDs equal F's tuple of the family's index
  References); V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`.
- AC-2 — N `test_every_record_matches_its_reference_section` (names and `In`); F `test_every_param_is_typed_as_its_row`
  (`{operation_id: {name: Kind}}` of every `Param` not `SCALAR`, and `{operation_id: required names}`, over the
  records with any, equal F's tables: the `array of strings` rows as `ARRAY`, and the `yes` rows; every record
  JSON-bodied with no `fixed`).
- AC-3 — F `test_only_the_list_records_are_paged` (the `Paging.OFFSET` IDs equal F's pair; every other record `NONE`).
- AC-4 — N `test_every_record_is_sent_as_its_section_documents`.
- AC-5 — F `test_a_list_record_prints_every_page`, one case per AC-3 record (#41 D8): each page scripted at its URL
  (`FakeGitLab.script`) and the sent `(method, URL)` list asserted (K `test_a_list_prints_every_page_as_one_array`).
- AC-6 — F `test_a_settings_write_sends_its_typed_body`: the recorded request's method, path and `json()`.
- UB-1 — C, every existing case unedited; the PR diff edits no part-1 record.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; the PR diff.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option`; P
  `test_standard_library_only`.
- UB-4 — `src/payload/test/test_wrapper_delivery.py`; the PR diff names no UB-4 file.
- E2E — no deployed system. Every record here is reachable (#41 D5); the real-instance run is #11's, on an
  `sff-test-*` project. Until then N calls every record, and F the list and write cases, through `main`'s argv to the
  API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 | F | AC-1, AC-2, AC-3, AC-5, AC-6 |
| IMPL-1 | `src/payload/scripts/gitlab_api/families/no_stage_assigned.py`, `docs/findings-ledger.md` | AC-1 to AC-6, UB-1, UB-2 |

Red after TEST-1 (`python scripts/run_tests.py` on F): its pending, typing and paging tests fail and its calls exit 2.
Green after IMPL-1: F, N, V, K, C and P.

## Residuals

- Secret values (`api_key`, `token`, `password`, `app_store_private_key`, `service_account_key`, …) are `-f` text
  and show in the command line; `call` logs names only (#41 D4), and `--file` takes only a `FILE` attribute (#41
  Residuals "Secrets in arguments") → ledger (DL-003).
- The docs pages name no paging for the two lists (DL-004): a one-page answer prints as one array; whether GitLab pages
  them is #11's real-instance run.
- Callable, gated by none (#41 Security "Destructive operations"): every `DELETE` and every `PUT`; a `/projects/:id`
  record acts on the configured project when `id` is not given.
- Nothing stays pending: no section here has a glob or optional path segment, a `header` row, or a raw or file body.
