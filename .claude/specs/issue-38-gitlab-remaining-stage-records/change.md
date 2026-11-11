# Change — issue #38: GitLab wrapper rewrite, part 2 slice: the remaining stage groups

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"). N, V,
K, C, P as #41's mapping; F = `src/payload/test/test_gitlab_api_<module>.py`, one per module.

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed (3beba95); #38 selected, `prompt.md` from its body; no interview (`qa_log.md`).

## Ask

Issue #38: each pending key gets a record from its `rest/<stage>.md` table, reachable through `call`, with fake-host
tests, and the `PENDING` sets empty. Open questions: deploy's keys go to #40, one cycle (DL-001); N's two halves prove
the Self-Managed-only sections (#41 D5).

## Acceptance criteria

The modules (`families/`): `tenant_scale`, `gitlab_dedicated`, `analytics`, `runtime`, `fulfillment`, `growth`,
`gitlab_delivery`, `orbit`, `data_access`, `developer_experience`, `agent_foundations`, `facilitated_functionality`,
`ai_clients`.

- AC-1 Every key on their `PENDING` at 52403f8, but AC-2's, SHALL be mapped: each index Reference of its rows gets one
  new `RestOperation` in the key's module (V `key_families`), its `method` and `path` a row's of that Reference; of
  several endpoints, the first `/projects/:id/…` one in its section, else the section's first.
- AC-2 `PENDING` SHALL then hold exactly every other endpoint of such a section, the four
  `/groups/:id/manage/…_access_tokens/:id…` keys, `("GET", "/orbit/skills/:name/*path")`, and the keys of
  `agent-foundations#trigger-a-flow`, `#restart-a-flow`, `gitlab-dedicated#import-project-resources`,
  `#import-a-project-from-a-local-archive`, `#import-a-project-from-a-remote-archive`,
  `#import-a-project-from-an-aws-s3-bucket`.
- AC-3 Each new record's `Param` names and locations SHALL be its section's as N's `reference_sections` reads it: one
  per query or body row (`form` read as body); a member row (`configuration[url]`, `upload[url]`) carried by its
  parent; a bracketed row without one (`not[author_username]`, `context[user]`) its own.
- AC-4 A new `Param`'s `kind` SHALL be `FILE` for a row whose Notes begin "file upload"; `ARRAY_OF_HASHES` for Type
  `array of object(s)` and `entities` of `gitlab-dedicated#start-a-group-or-project-migration`; `HASH` for `hash`,
  `Hash`, `object`; `ARRAY` for any other Type holding `array` or `Array`; else `SCALAR`; `required` true exactly where
  Required reads `yes`. A new record's `body` SHALL be `BodyFormat.JSON`, but `growth#force-a-variant-assignment`'s
  `FORM` (#41 D5); `fixed` empty.
- AC-5 A new record SHALL be `Paging.OFFSET` when it is a `GET` headed "List…" or with a `page` row, but not the lists
  answering one object: every `gitlab-delivery#` and `orbit#` list, `analytics#list-all-non-sql-metrics`,
  `#list-all-service-ping-sql-queries`, `agent-foundations#list-all-agent-privileges`,
  `data-access#list-pending-migrations`; every other `Paging.NONE`; none `KEYSET` (opt-in, `conventions.md`).
- AC-6 WHEN a new record is called with `call <id>` and a value for every path parameter and `Param`, THE wrapper SHALL
  send one request with its section's method, expanded path, query and body names and exit 0, reachable or not (#41 D5).
- AC-7 WHEN a `Paging.OFFSET` record is called against a host serving one item on each of two pages, the first
  answering `x-next-page: 2`, THE wrapper SHALL exit 0 and print `print_json` of both items as one array.
- AC-8 WHEN `tenant-scale#download-snapshot-of-a-git-repository`, `gitlab-dedicated#download-a-project-export` or
  `agent-foundations#get-workflow-trace-as-jsonl` answers non-UTF-8 bytes as `application/octet-stream`, THE wrapper
  SHALL exit 0 and write those bytes unchanged.

## Unchanged behaviour

- UB-1 Every compatibility subcommand SHALL CONTINUE TO accept the argv and return the exit codes its callers use.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `ai-coding#merge-a-merge-request` and
  `plan#create-an-issue`, naming `mr merge` and `issue create`, and an ID no record declares, AC-2's included;
  `GATED_OPERATIONS` SHALL CONTINUE TO hold only those two.
- UB-3 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`; imports only from the 3.9 standard library.
- UB-4 `github_wrapper.py`, `github_api/`, their tests SHALL CONTINUE TO be untouched, `test_wrapper_delivery.py` green.

## Files

- The modules: records in `OPERATIONS`, each under a comment naming its section; `PENDING` per AC-1, AC-2; docstrings.
- F: new.
- N: `test_an_unreachable_call_matches_its_reference_section` puts its record in place of the declared
  `gitlab-dedicated#update-a-geo-site`, not beside it; docstring to match, assertions unchanged.
- `docs/findings-ledger.md`: the Residuals' rows (`memory_compile.py ledger add`).

Nothing else: no other file of #41 D8's "never" row, `commands/call.py` included (UB-2); no doc.

## Tests

Example tests; F's tables are literal, from the sections and the index.

- AC-1 — F `test_every_reference_has_its_record`: `OPERATIONS` as `{operation_id: (method, path)}` equals F's table,
  the family's References but AC-2's; V `test_every_index_row_is_mapped_or_pending`,
  `test_every_declared_key_is_in_its_family`.
- AC-2 — F `test_only_the_kept_keys_are_pending`.
- AC-3, AC-6 — N `test_every_record_matches_its_reference_section`,
  `test_every_record_is_sent_as_its_section_documents`.
- AC-4 — F `test_every_param_is_typed_as_its_row`: `{(operation_id, name): kind}` of the non-`SCALAR` `Param`s,
  `{operation_id: required names}`, bodies, `fixed`.
- AC-5 — F `test_only_the_list_records_are_paged`.
- AC-7 — F `test_a_list_record_prints_every_page`, a case per `OFFSET` record, as K
  `test_a_list_prints_every_page_as_one_array`.
- AC-8 — F `test_a_download_is_written_unchanged` (`capsysbinary`).
- UB-1 — C.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 test.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-4 — `test_wrapper_delivery.py`; the PR diff.
- E2E — no deployed system; the real-instance run is #11's (`sff-test-*`). N and F run `call` through `main` in
  `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 | F of `tenant_scale` | AC-1, AC-2, AC-4, AC-5, AC-7, AC-8 |
| TEST-2 | F of `gitlab_dedicated`; N | AC-1, AC-2, AC-4 to AC-8 |
| TEST-3 | F of the other eleven modules | AC-1, AC-2, AC-4, AC-5, AC-7, AC-8 |
| IMPL-1 | `families/tenant_scale.py`, `docs/findings-ledger.md` | AC-1 to AC-8, UB-1, UB-2 |
| IMPL-2 | `families/gitlab_dedicated.py` | AC-1 to AC-8, UB-1, UB-2 |
| IMPL-3 | the other eleven modules | AC-1 to AC-8, UB-1, UB-2 |

Red after the TESTs: F fails, its calls exit 2; N passes. Green after the IMPLs: F, N, C, K, V, P.

## Residuals

- Kept (AC-2), deferral on #38: one record per ID (#41 Residuals); `:id` twice in a path (as #35's);
  `override_params[…][…]` rows, refused by N `is_member_name_allowed` → ledger; glob → #40.
- Branch-writing or issue-creating, sent by no subcommand: a flow writes code, merge requests and issues;
  `import-project-resources` imports issues into an existing project; `overwrite` replaces one → ledger.
- Paging no docs page names (the Geo lists, `fulfillment#retrieve-scim-identities-for-a-group`) is #11's run.
- In argv (#36 DL-003): hook `token`, `signing_token`, importer tokens, `import_url`, `license`,
  `configuration[access_token]`; on stdout `runners_token` → ledger.
- Callable, gated by none (#41 Security): deletes, transfers, `export-a-project`'s `upload[url]`; example keys that
  address project `1`, `diaspora/diaspora`.
