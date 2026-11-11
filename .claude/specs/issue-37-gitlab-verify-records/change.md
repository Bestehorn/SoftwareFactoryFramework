# Change — issue #37: GitLab wrapper rewrite, part 2 slice: the verify stage group

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"). N,
V, K, C, P as #41's mapping; F = `src/payload/test/test_gitlab_api_verify.py`.

## User Prompts

1. User, 2026-11-10 (`/auto-work`, `.claude/commands/auto-work.md`): "Work this project's open-issue backlog
   AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed (3beba95); #37 selected, `prompt.md` derived from its body; no interview (`qa_log.md`).

## Ask

Issue #37: "each pending key has a `RestOperation` transcribed from its row's `rest/verify.md` attribute table …
reachable through part 2a's generic operation command …, and `verify.PENDING` empty." Open questions (DL-002): the
`*artifact_path` routes stay pending; a download prints its bytes unchanged (#41 D3); the job-token routes are records
like every row (#41 D6).

## Acceptance criteria

- AC-1 Every key on `verify.PENDING` before this change SHALL be mapped by one `RestOperation` whose `operation_id` is
  a Reference of its rows, but for DL-003's: `verify.PENDING` SHALL be exactly the keys of
  `verify#download-a-single-artifact-file-by-job-id`, `verify#download-a-single-artifact-file-by-reference-name` and
  `verify#add-a-merge-request-to-a-merge-train`, and every endpoint but its section's first of `verify#metadata-api-1`,
  `verify#get-the-latest-release` and `verify#list-all-of-a-groups-runners`. `verify#runners-api-1` has no record.
- AC-2 Each new record's `method`, `path` and `Param` names and locations SHALL be its section's as N's
  `reference_sections` reads it: every query and body row; a `not[…]` row with no parent row as its own
  `Location.QUERY` `Param`; no member row (`strategies:name`), which goes inside its parent.
- AC-3 Each new `Param`'s `kind` SHALL be `ARRAY_OF_HASHES` for a Type `array of hashes`, `array of hash` or `array of
  strategy JSON objects`, `ARRAY` for any other Type holding `array`, `HASH` for `hash` or `object`, else `SCALAR`; its
  `required` SHALL be true exactly where Required reads `yes`. Each new record's `body` SHALL be `BodyFormat.JSON` and
  its `fixed` empty.
- AC-4 A new record SHALL be `Paging.OFFSET` when its section is a `GET` whose heading begins with "List", but
  `verify#list-pipelines` `Paging.KEYSET` (`conventions.md`: keyset only) and
  `verify#list-all-scopes-for-a-runner-controller` `Paging.NONE` (it answers one object); every other new record
  `Paging.NONE` (DL-004).
- AC-5 WHEN a new record is called with `call <id>` and a value for every path parameter and `Param`, THE wrapper SHALL
  send one request with the section's method, expanded path, query names and body names, and exit 0 (#41 D5).
- AC-6 WHEN a paged `verify` record is called against a host serving one item on each of two pages, the second asked
  for by `x-next-page` (`OFFSET`) or at its `Link` `rel="next"` URL (`KEYSET`), THE wrapper SHALL exit 0 and print both
  items as one JSON array (`print_json`).

## Unchanged behaviour

- UB-1 `pipeline status`, `log` and `wait` SHALL CONTINUE TO send the part-1 records, unchanged, with the argv, output
  and exit codes their callers use.
- UB-2 `call` SHALL CONTINUE TO write a body that is not JSON as its bytes unchanged, sending no credential to another
  origin (#41 D3).
- UB-3 `call` SHALL CONTINUE TO refuse with exit 2 and no request `ai-coding#merge-a-merge-request` and
  `plan#create-an-issue`, naming `mr merge` and `issue create`, and an ID no record declares,
  `verify#add-a-merge-request-to-a-merge-train` included; `GATED_OPERATIONS` SHALL CONTINUE TO hold only those IDs.
- UB-4 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`; the package imports only the standard library.
- UB-5 `github_wrapper.py`, `github_api/`, their tests and `test_wrapper_delivery.py` SHALL CONTINUE TO be untouched.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_api/families/verify.py` | records in `OPERATIONS`, each under a comment naming its page and section; `PENDING` per AC-1; the docstring describes both |
| F | new |
| K | the `artifacts-after-a-redirect` case drops its synthetic record; `artifacts_record`, `ARTIFACTS_RECORD`, `VERIFY` removed; `OP_DOWNLOAD_ARTIFACTS` leaves the synthetic IDs |
| `docs/findings-ledger.md` | the Residuals' rows, via `memory_compile.py ledger add` |

Nothing else: no file of #41 D8's "never" row (`commands/call.py` included), no `registry.py`, no doc.

## Tests

Example tests. F's IDs, keys, kinds, required names and paging are literal tables from the sections, never read from
the records. C, N, P and V are unedited; K only as Files says.

- AC-1 — F `test_only_the_kept_keys_are_pending`: `verify.PENDING` equals F's key set, and the `OPERATIONS` IDs
  equal F's tuple of the family's index References but AC-1's first three IDs and `verify#runners-api-1`; V
  `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`.
- AC-2 — N `test_every_record_matches_its_reference_section`.
- AC-3 — F `test_every_param_is_typed_as_its_row`: `{operation_id: {name: Kind}}` of every `Param` not `SCALAR`, and
  `{operation_id: required names}`, over the records with any, equal F's tables; every record JSON with no `fixed`.
- AC-4 — F `test_only_the_list_records_are_paged`: `{operation_id: (Paging, paging rows declared)}` of the records
  not `NONE` equals F's table.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`.
- AC-6 — F `test_a_list_record_prints_every_page`, one case per ID of F's paging table, each page scripted at its URL
  (`FakeGitLab.script`) as K `test_a_list_prints_every_page_as_one_array` scripts its OFFSET and KEYSET cases; the sent
  `(method, URL)` list, every answer served, stdout asserted.
- UB-1 — C, every existing case unedited; the PR diff edits no part-1 record.
- UB-2 — K `test_a_body_that_is_not_json_is_written_unchanged`.
- UB-3 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 test; diff.
- UB-4 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-5 — `test_wrapper_delivery.py`; the PR diff names no UB-5 file.
- E2E — no deployed system; the reachable records' (#41 D5) real-instance run is #11's, on an `sff-test-*` project.
  Until then N and F run `call` through `main` to the API boundary in CI job `verify`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 | F | AC-1, AC-3, AC-4, AC-6 |
| TEST-2 | K | UB-2 |
| IMPL-1 | `families/verify.py`, `docs/findings-ledger.md` | AC-1 to AC-6, UB-1, UB-3 |

Red (`python scripts/run_tests.py` on F and K): F's pending, typing and paging tests fail; its new list cases and K's
artifacts case exit 2. Green after IMPL-1: F, K, C, N, V and P.

## Residuals

- Kept pending (DL-003; deferral noted on #37) → ledger: the `*artifact_path` routes (`registry.PLACEHOLDER` and N's
  path-row rule read no `*name`: #41 D8's exceptions row, the issue's tier-M trigger); the merge-train add, which
  merges and no subcommand sends (`refuse_gated` refuses only an ID mapped to one); the later endpoints of AC-1's
  multi-endpoint References (one record per ID, #41 Residuals).
- Secrets (#41 Residuals): variable values and runner, trigger and job tokens are `-f` or `--query` text; a query
  token (`DELETE /runners` `token`, `CI_JOB_TOKEN`, `job_token`) is in the URL the transport's error and `429` retry
  messages log; variable reads and token creates, resets and rotations print secrets → ledger.
- Callable, gated by none (#41 Security): every `DELETE`, job erase, token resets and rotations, deployment approvals,
  environment stops, pipeline, job and schedule runs (their CI can push or merge), and `verify#create-a-release`, which
  creates its tag from `ref`.
