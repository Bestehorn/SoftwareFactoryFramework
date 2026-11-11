# Change — issue #35: GitLab wrapper rewrite, part 2 slice: the create and ai-coding stage groups

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"). N, V,
K, C, P as #41's mapping; F = `src/payload/test/test_gitlab_api_<family>.py`.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed; #35 selected, `prompt.md` derived from its body; no interview (`qa_log.md`).

## Ask

Issue #35: each pending key gets a `RestOperation` from its section's attribute table, reachable through `call` (#41),
with fake-host tests, and both `PENDING` sets empty. Open questions: `archive[.format]` stays pending (Residuals);
binary downloads need no bytes path (#41 D3; AC-7).

## Acceptance criteria

- AC-1 Every key on the `PENDING` of `families/create.py` and `families/ai_coding.py` before this change SHALL be
  mapped by a `RestOperation`, one per index Reference (both of `GET /keys`), but for the kept set: `ai_coding.PENDING`
  SHALL be exactly the key of `ai-coding#rebase-a-merge-request`; `create.PENDING` exactly
  `GET /projects/:id/repository/changelog.txt` (`create#generate-changelog-data` takes its first endpoint) and the keys
  of the `create#` IDs `create-repository-branch`, `create-a-commit`, `cherry-pick-a-commit`, `revert-a-commit`,
  `add-changelog-data-to-file`, `create-a-file-in-a-repository`, `update-a-file-in-a-repository`,
  `delete-a-file-in-a-repository`, `update-a-submodule-reference`, `apply-a-suggestion`, `apply-multiple-suggestions`,
  `start-the-pull-mirroring-process-for-a-project`, `retrieve-file-archive-from-a-repository` and
  `delete-a-group-ssh-certificate`.
- AC-2 Each new record's `method`, `path` and `Param` names and locations SHALL be its section's as N's
  `reference_sections` reads it: every query and body row; a query member row (`not[labels]`) also as its own `QUERY`
  `Param` (as `plan#list-all-project-issues`); a body member row (`position[base_sha]`, `files:content`) never.
- AC-3 A new `Param`'s `kind` SHALL be `ARRAY_OF_HASHES` for a Type `array of hashes` and for the `files` of
  `create#retrieve-multiple-blobs-in-a-single-request`; `ARRAY` for any other Type holding `array` or `Array`; `HASH`
  for `hash`, `Hash` or `object`; else `SCALAR` (every `In` `form` row is a kept record's); its `required` true exactly
  where Required reads `yes`. A new record's `body` SHALL be `BodyFormat.JSON`, its `fixed` empty.
- AC-4 A new record SHALL be `Paging.OFFSET` when it is a `GET` whose heading begins with "List" or whose table has a
  `page` row, or one of the `ai-coding#` IDs `retrieve-merge-request-participants`, `retrieve-merge-request-reviewers`,
  `retrieve-merge-request-dependencies` and `retrieve-blocked-merge-requests`, else `Paging.NONE`; none SHALL be
  `Paging.KEYSET` (opt-in, `conventions.md` "Keyset-based").
- AC-5 WHEN a new record is called with `call <id>` and a value for every parameter its section documents, THE wrapper
  SHALL send one request with the section's method, expanded path, query names and body names, and exit 0 (#41 D5).
- AC-6 WHEN a new `Paging.OFFSET` record is called against a host serving one item on each of two pages, the second
  asked for by `x-next-page`, THE wrapper SHALL exit 0 and print both items as one JSON array.
- AC-7 WHEN `create#retrieve-raw-blob-content` is answered with non-UTF-8 bytes as `application/octet-stream`, THE
  wrapper SHALL exit 0 and write those bytes unchanged.

## Unchanged behaviour

- UB-1 The `mr` and `delete-branch` subcommands SHALL CONTINUE TO send the unedited part-1 records, with the argv,
  output and exit codes their callers use.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `ai-coding#merge-a-merge-request` and
  `plan#create-an-issue`, naming `mr merge` and `issue create`, and an ID no record declares, AC-1's kept IDs included;
  `GATED_OPERATIONS` SHALL CONTINUE TO hold only those two IDs.
- UB-3 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`, the package to import only the Python 3.9
  standard library.
- UB-4 `github_wrapper.py`, `github_api/`, their tests and `test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and
  to pass.

## Files

- `src/payload/scripts/gitlab_api/families/create.py`, `ai_coding.py`: records in `OPERATIONS`, each under a comment
  naming its section; `PENDING` per AC-1; module docstrings.
- F: new, one per family.
- `docs/findings-ledger.md`: the Residuals' rows (`memory_compile.py ledger add`).

Nothing else (#41 D8 "never", `commands/call.py` included; no doc, #41 D7).

## Tests

Example tests. F's tables are literal, transcribed from the sections and the index, never read from the records.

- AC-1 — F `test_only_the_kept_keys_are_pending` (`PENDING` equals F's keys; the `OPERATIONS` IDs F's tuple of the
  family's index References but the kept IDs); V `test_every_index_row_is_mapped_or_pending`,
  `test_every_declared_key_is_in_its_family`.
- AC-2 — N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` (members).
- AC-3 — F `test_every_param_is_typed_as_its_row`: `{operation_id: {name: Kind}}` of every non-`SCALAR` or member
  `Param`, and `{operation_id: required names}`, over the records with any, equal F's tables; every body JSON, no
  `fixed`.
- AC-4 — F `test_only_the_list_records_are_paged`: the `OFFSET` IDs equal F's set; none is `KEYSET`.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`.
- AC-6 — F `test_a_list_record_prints_every_page`, one case per AC-4 record (#41 D8), each page scripted at its URL
  (`FakeGitLab.script`) and asserted as in K `test_a_list_prints_every_page_as_one_array`.
- AC-7 — F `test_a_raw_download_is_written_unchanged`, stdout read with `capsysbinary`.
- UB-1 — C; the PR diff edits no part-1 record.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 tests.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-4 — `test_wrapper_delivery.py`; the PR diff.
- E2E — no deployed system; the real-instance run is #11's, on an `sff-test-*` project; N alone proves the unreachable
  (#41 D5). N and F run `call` through `main` in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 | F (create) | AC-1 to AC-4, AC-6, AC-7 |
| TEST-2 | F (ai-coding) | AC-1 to AC-4, AC-6 |
| IMPL-1 | `families/create.py`, `docs/findings-ledger.md` | AC-1 to AC-7, UB-1, UB-2 |
| IMPL-2 | `families/ai_coding.py` | AC-1 to AC-6, UB-1, UB-2 |

Red after the TESTs (`python scripts/run_tests.py` on F): pending, typing and paging tests fail, new cases exit 2.
Green after the IMPLs: F, N, V, K, C and P.

## Residuals

- Kept pending (AC-1), deferral recorded on #35: the IDs that commit to, create or rewrite a branch have no gating
  subcommand (#39's kept set) → ledger.
- Forms part 1 lacks: `archive[.format]`, sent literally by `registry.expand`; `/groups/:id/ssh_certificates/:id`, one
  `id` value for both; `changelog.txt`, one record per Reference → ledger.
- Quick actions run from a saved note or description: `/clone` (issue threads) creates an issue, `/rebase` (MR threads
  and descriptions) rewrites the source branch; `/merge` needs `merge_request_diff_head_sha`, on no row here → ledger.
- Callable, gated by none (#41 Security): deleting branches, merged branches and tags; tags, protection, push rules,
  mirrors, commit statuses, snippets; `ai-coding#merge-to-default-merge-ref-path`.
- `auth_password` of `create#update-project-pull-mirroring-settings` shows in the command line (#36 DL-003) → ledger.
