# Change — issue #42: GitLab wrapper rewrite, part 2 slice: software-supply-chain-security and security stage groups

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn").

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed (3beba95); #42 selected, `prompt.md` from its body; no interview (`qa_log.md`).

## Ask

Issue #42: "Done: each pending key has a record transcribed from its row's `rest/<stage>.md` attribute table,
reachable through the generic call of part 2a (#41 …), with fake-host tests, and the five `PENDING` empty." Open
questions: the administrator sections get no record (DL-005); a download is a plain record printed by #41 D3 (DL-002).

## Acceptance criteria

The five modules: `families/<module>.py` for `software_supply_chain_security`, `security_risk_management`,
`security_platform`, `security_factory`, `security_governance`.

- AC-1 Every key on their `PENDING` at 3beba95, except AC-2's, SHALL be mapped by one new `RestOperation` in its
  module's `OPERATIONS`, its ID the Reference of one of the key's rows: `PUT /application/appearance` by
  `#update-application-appearance`, `GET /users/:id` by `#retrieve-a-single-user-as-a-regular-user`. A section with
  several endpoints SHALL map its `/projects/:id/…` endpoint, else its first.
- AC-2 `PENDING` SHALL then hold exactly every other endpoint of such a section (one record per ID, #41 Residuals),
  `("GET", "https://HOST/oauth/token/info")` and
  `("PATCH", "/projects/:id/compliance_external_controls/:external_control_id/status")` (DL-003).
- AC-3 Each new record's method, path and `Param` names and locations SHALL be its section's as N's
  `reference_sections` reads it: one `Param` per query or body row (`form` read as body), a `name[]…` row carried by
  its parent; `body` `BodyFormat.JSON`, no `fixed`.
- AC-4 Each new `Param`'s `kind` SHALL be `FILE` for a row noted "file upload" and for `avatar` on `PUT /user/avatar`,
  `POST /users` and `PUT /users/:id` (each a `WorkhorseFile`); `ARRAY_OF_HASHES` for an `array` row with `name[].…`
  rows; `HASH` for `object`; `ARRAY` for any other Type naming an array; else `SCALAR`. Its `required` SHALL be true
  exactly where Required reads `yes`.
- AC-5 A new record SHALL be `Paging.OFFSET` when it is a `GET` whose section heading begins "List" or "Get all", or
  is `#retrieve-project-external-status-check-services`, but not `#list-all-project-security-settings` or
  `#list-all-token-associations`; every other `Paging.NONE`.
- AC-6 WHEN a record of the five families is called with `call <id>` and a value for every path parameter and `Param`,
  THE wrapper SHALL send one request with its section's method, expanded path, query names and body names and exit 0,
  reachable or not (#41 D5).
- AC-7 WHEN a `Paging.OFFSET` record of these families is called against a host serving one item on each of two pages,
  the first answering `x-next-page: 2`, THE wrapper SHALL exit 0 and print `print_json` of both items as one array.

## Unchanged behaviour

- UB-1 `issue start`, `issue assign` and every compatibility subcommand SHALL CONTINUE TO accept their argv and return
  their exit codes, on part 1's `#as-a-regular-user` and `#as-a-regular-user-1`, unedited.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `ai-coding#merge-a-merge-request` and
  `plan#create-an-issue`, naming `mr merge` and `issue create`, and an ID no record declares; and to print a non-JSON
  body as its bytes unchanged, a redirect followed without the credential.
- UB-3 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`, imports only from the Python 3.9 standard
  library.
- UB-4 `src/payload/scripts/github_wrapper.py`, its tests and `src/payload/test/test_wrapper_delivery.py` SHALL
  CONTINUE TO be untouched and to pass.

## Files

| File | Change |
|---|---|
| the five modules under `src/payload/scripts/gitlab_api/` | records added to `OPERATIONS`, keys removed from `PENDING` per AC-1, AC-2; each module docstring describes its records |
| F: `src/payload/test/test_gitlab_api_<module>.py`, one per module | new |
| `docs/findings-ledger.md` | the Residuals' ledger rows, via `memory_compile.py ledger add` |

Nothing else: no file of #41 D8's "never" row, `commands/call.py` included (no record here commits to or merges into
a branch or creates an issue), no other doc.

## Tests

Example tests. F's keys, IDs, kinds, required names and list IDs are literal tables transcribed from the sections,
never read from the records. In `src/payload/test/`: C = `test_gitlab_wrapper_compat.py`, K = `test_gitlab_api_call.py`.
N = `test/test_gitlab_wrapper_contract.py`, V = `test/test_gitlab_wrapper_coverage.py`,
P = `test/test_gitlab_api_properties.py`; C, K, N, V, P unedited.

- AC-1 — F `test_every_key_has_its_record` (`{(method, path): operation_id}` over the module's new records equals F's
  table); V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`.
- AC-2 — F `test_only_the_unmapped_keys_are_pending` (`PENDING` equals F's set; empty in three modules).
- AC-3 — N `test_every_record_matches_its_reference_section`.
- AC-4 — F `test_every_kind_is_its_rows_type` (`{(operation_id, name): kind}` over the non-`SCALAR` `Param`s equals
  F's table of AC-4's rows), `test_the_required_attributes_are_the_sections` (`{operation_id: names}` over the records
  with a required `Param` equals F's table of the `yes` rows).
- AC-5 — F `test_every_list_record_has_a_case` (the module's `Paging.OFFSET` IDs equal F's case IDs, AC-5's set;
  none is `Paging.KEYSET`).
- AC-6 — N `test_every_record_is_sent_as_its_section_documents`, an unreachable record's whole proof (#41 D5).
- AC-7 — F `test_a_list_record_prints_every_item`: one case per `Paging.OFFSET` record (four modules), run with
  `fixtures.run_main`.
- UB-1 — C `test_a_subcommand_form` (its `issue start` and `issue assign` cases); the PR diff edits neither record.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`,
  `test_a_body_that_is_not_json_is_written_unchanged`.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-4 — `test_wrapper_delivery.py`; the PR diff names none of UB-4's files.
- E2E — no deployed system; the real-instance run is #11's. N and F run `call` through `main` to the API boundary in
  CI job `verify`, leg `tests`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 to TEST-5, one per module | the module's F | AC-1, AC-2, AC-4, AC-5, AC-7 |
| IMPL-1 to IMPL-5, one per module | `src/payload/scripts/gitlab_api/families/<module>.py` | AC-1 to AC-7, UB-1 |

Red after TEST (`python scripts/run_tests.py` on the five F): F's mapping and pending tests fail, its list cases exit 2.
Green after IMPL: F, C, K, N, V, P.

## Residuals

- AC-2's keys stay pending (DL-003), the deferral recorded on #42: a several-endpoint section's other keys need one
  record per key under one ID; `https://HOST` paths and the external control's required `X-Gitlab-*` request
  headers are forms #41 does not build → ledger.
- `#as-an-administrator`, `-1`, `-2` get no record (DL-005): their keys are mapped, and N refuses their rows on
  part 1's records → ledger. `#update-application-settings` has no table, so no `Param` → ledger.
- On stdout: the token of every token-creating or rotating record, an application `secret`, a runner token, a
  Support PIN, the Secrets Manager JWT. In argv: the `/admin/token` `token` (the `DELETE`'s URL and error), `password`,
  `shared_secret` (#41 Residuals). Moderation and deletes run unconfirmed (#41 Security "Destructive operations").
