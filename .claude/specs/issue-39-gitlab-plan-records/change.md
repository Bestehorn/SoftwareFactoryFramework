# Change — issue #39: GitLab wrapper rewrite, part 2 slice: the plan stage group

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"); its D8
names what a slice edits.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed (3beba95); #39 selected, `prompt.md` derived from its body; no interview (`qa_log.md`).

## Ask

Issue #39: "each pending key has a `RestOperation` transcribed from its row's `rest/plan.md` attribute table, reachable
through the generic call of the sibling child … with fake-host tests, and the module's `PENDING` empty." Open questions
(DL-002): the deprecated epic APIs get records like every row (#41 D6); N's two tests are each record's fake-host
proof, and F adds the paged examples (#41 D8).

## Acceptance criteria

- AC-1 Every key on the `PENDING` of `families/plan.py` before this change SHALL be mapped by one `RestOperation` of its
  `OPERATIONS`, but for DL-003's: `plan.PENDING` SHALL be exactly the keys of `plan#clone-an-issue` and
  `plan#create-a-merge-request-note`, and, of each section with several endpoints, every endpoint but its record's,
  which is its first endpoint under `/projects/:id/`.
- AC-2 Each new record's `method`, `path` and `Param` names and locations SHALL be its section's as N's
  `reference_sections` reads it: every query and body row; a member row (`not[labels]`) also as its own
  `Location.QUERY` `Param`, as `plan#list-all-project-issues` declares it; the emoji rows
  `issue_iid/merge_request_iid/snippet_id` as written.
- AC-3 Each new `Param`'s `kind` SHALL be `FILE` for an `In` `form` row, `ARRAY` for a Type holding `array`, `HASH`
  for `Hash` or `object`, else `SCALAR`; its `required` SHALL be true exactly where its row's Required reads `yes`.
  Each new record's `body` SHALL be `BodyFormat.JSON` and its `fixed` empty.
- AC-4 A new record SHALL be `Paging.OFFSET` when its section is a `GET` whose heading begins with "List" or "Get all",
  else `Paging.NONE`; none SHALL be `Paging.KEYSET`, no plan list being keyset-only (`conventions.md` "Keyset-based";
  #13 D5).
- AC-5 WHEN a new record is called with `call <id>` and a value for every parameter its section documents, THE wrapper
  SHALL send one request with the section's method, expanded path, query names and body names, and exit 0 (#41 D5).
- AC-6 WHEN a `Paging.OFFSET` record of `plan` is called against a host serving one item on each of two pages, THE
  wrapper SHALL exit 0 and print both items as one JSON array (`print_json`).

## Unchanged behaviour

- UB-1 The `issue` and `label` subcommands SHALL CONTINUE TO send the part-1 records, unchanged, with the argv, output
  and exit codes their callers use.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `plan#create-an-issue` and
  `ai-coding#merge-a-merge-request`, naming `issue create` and `mr merge`, and an ID no record declares,
  `plan#clone-an-issue` and `plan#create-a-merge-request-note` included.
- UB-3 Credentials SHALL CONTINUE TO come only from `config/gitlab.json`, and the package to import only the Python 3.9
  standard library.
- UB-4 `src/payload/scripts/github_wrapper.py`, its tests and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE
  TO be untouched and to pass.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_api/families/plan.py` | records added to `OPERATIONS`, keys removed from `PENDING` per AC-1; the module docstring describes the records it now holds |
| F: `src/payload/test/test_gitlab_api_plan.py` | new |
| K: `src/payload/test/test_gitlab_api_call.py` | `OP_PENDING_ONLY` and its comment name `plan#clone-an-issue`, which AC-1 keeps pending (DL-004) |
| `docs/findings-ledger.md` | the Residuals' rows, via `memory_compile.py ledger add` |

Nothing else: #41 D8's "never" row, `commands/call.py` included (Residuals), and no doc (#41 D7).

## Tests

Example tests. F's IDs, keys, paths, kinds and required names are literal tables transcribed from the sections, never
read from the records. C = `src/payload/test/test_gitlab_wrapper_compat.py`; in `test/`: N =
`test_gitlab_wrapper_contract.py`, V = `test_gitlab_wrapper_coverage.py`, P = `test_gitlab_api_properties.py`. C, N,
V, P unedited; K only as Files says.

- AC-1 — F `test_only_the_kept_keys_are_pending`: `plan.PENDING` equals F's key set, and the `OPERATIONS` IDs F's tuple
  of the family's index References but the two kept IDs and `plan#promote-an-issue-to-an-epic`; V
  `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`.
- AC-2 — N `test_every_record_matches_its_reference_section`.
- AC-3 — F `test_the_typed_attributes_are_the_sections` (`{(id, name): kind}` over the module's non-`SCALAR` `Param`s
  equals F's table from the `In` and Type columns), `test_the_required_attributes_are_the_sections` (the `(id, name)`
  pairs with `required` equal F's Required `yes` non-path rows), `test_every_body_is_json_with_no_fixed_pairs`.
- AC-4 — F `test_every_list_record_has_a_case`: the module's `Paging.OFFSET` IDs equal F's case IDs, and no record is
  `Paging.KEYSET`.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`. Every plan section offers GitLab.com and no path is
  under `/admin/`, `/geo/` or `/hooks/`, so every record is reachable (#41 D5).
- AC-6 — F `test_a_list_record_prints_every_item`, per case: `--path` for each placeholder of F's literal path; two
  pages chained by `x-next-page`, scripted as K `test_a_list_prints_every_page_as_one_array` scripts them; stdout is
  `print_json` of both items, and every scripted response was served.
- UB-1 — C, every existing test; the PR diff edits no part-1 record.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F's AC-1 test.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-4 — `test_wrapper_delivery.py`; the PR diff names no file of UB-4.
- E2E — no deployed system; the real-instance check is #11's, on an `sff-test-*` project. N and F run `call` through
  the product's `main` to the API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

- TEST-1 — F. Files: `src/payload/test/test_gitlab_api_plan.py`. Validates: AC-1, AC-3, AC-4, AC-6.
- TEST-2 — K's pending case. Files: `src/payload/test/test_gitlab_api_call.py`. Validates: UB-2.
- Red: `python scripts/run_tests.py` on F and K: F's pending, list-set, typed and required tests fail and its
  new list cases exit 2; K passes.
- IMPL-1 — Files: `src/payload/scripts/gitlab_api/families/plan.py`. Validates: AC-1 to AC-6, UB-1.
- Green: F, K, C, N, V and P.

## Residuals

- Kept pending (DL-003), the deferral recorded on #39: `plan#clone-an-issue` creates an issue, and
  `plan#create-a-merge-request-note` merges by `/merge` (its `merge_request_diff_head_sha` row); no subcommand sends
  either, and `refuse_gated` refuses an ID only on `GATED_OPERATIONS.get(...) is not None` → ledger.
- One record per Reference (#41 Residuals) keeps the emoji sections' merge-request and snippet keys and the
  `/groups/:id/notification_settings` keys pending → ledger.
- The emoji `issue_iid/merge_request_iid/snippet_id` row is the path parameter, its `In` inferred; the record declares
  it as written, so giving it sends a stray attribute → ledger.
- `/clone` runs from any saved issue note or description: part 1's records and `plan#update-an-issue-note` → ledger.
- Callable (#41 Security "Destructive operations"): `plan#move-an-issue`, which moves an issue; the epic creates; the
  wiki writes and attachments, which commit to the wiki repository, never to the project's.
