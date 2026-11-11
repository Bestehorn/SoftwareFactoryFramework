# Combined review (tier S), iteration 01 — issue #29

### C1 — The bulk-list residual says `call` cannot print the next cursor; it does
Severity: C
Location: change.md § Residuals, first bullet
Defect: The bullet sends to the ledger "the next page's cursor is in the `link` header, which `call` does not print". `rest/orgs.md` and `rest/users.md` "List attestations by bulk subject digests" list no `Link` header on the `200` (#28 D3: "page by cursor without a `Link` header"); the pinned OpenAPI gives that `200` no headers and a body `page_info.next`, "The cursor to the next page". A `Paging.NONE` record prints the body (`commands/call.py` `print_body`) and `after` is a documented query name, so nothing is left out and the ledger row would record a limitation that does not exist.
Proposed-edit: delete the first Residuals bullet ("The two `…/attestations/bulk-list` records print one page; … → ledger.").

### C2 — The stdout-secret residual names one of five records (security lens)
Severity: C
Location: change.md § Residuals, fourth bullet
Defect: Pinned OpenAPI: `apps/check-token`, `apps/reset-token` and `apps/scope-token` answer the `authorization` schema, whose `token` is required; `apps/create-from-manifest` answers `client_secret`, `webhook_secret` and `pem` (the app's private key), all required. `call` prints each on stdout as it prints `apps/create-installation-access-token`, the only one the bullet names.
Proposed-edit: replace "`apps/create-installation-access-token` prints its `installation-token` on stdout." with "`apps/create-installation-access-token`, `apps/check-token`, `apps/reset-token`, `apps/scope-token` print a `token`, `apps/create-from-manifest` the app's `client_secret` and `pem`, on stdout."

### C3 — The issue's refusal of an undocumented name is not traced
Severity: C
Location: change.md § Unchanged behaviour UB-2; § Tests UB-2
Defect: Issue #29's draft AC-3 also asks that the call "SHALL refuse an undocumented name before any request". The behaviour holds: K `test_an_undocumented_parameter_is_refused` (present, unedited) proves the check, and AC-1 makes each record's names its section's. But no criterion or test line of the change names it, so the proof gate has nothing to cite.
Proposed-edit: UB-2 "and an ID no record declares." → "an ID no record declares, and an undocumented name."; Tests UB-2, append "`test_an_undocumented_parameter_is_refused`".

### D1 — Not every structural test is red after TEST
Severity: D
Location: change.md § Tasks, red line
Defect: `test_every_record_sends_the_default_version_and_media_type` holds over no records (`orgs`, `teams`, `apps`) and over `users/get-authenticated`, which already carries the defaults. `test_the_multi_segment_parameters_are_the_sections` holds for `teams` and `apps`, where both sides are empty. `test_nothing_is_pending` and `test_every_list_record_has_a_case` fail in all four.
Proposed-edit: "F's structural tests fail" → "F's pending and list-set tests fail".

### D2 — "in that order" reads as sequential dispatch
Severity: D
Location: change.md § Tasks, IMPL row
Defect: The four IMPL tasks own disjoint files and are dispatched together (`parallel-by-default.md` "Implementation waves").
Proposed-edit: "IMPL-1 to IMPL-4, in that order" → "IMPL-1 to IMPL-4, one per family".

With all five edits applied, change.md measures 7,983 B (cap 8,000).

## Checked, no defect

- **Bulk `POST`s as `Paging.NONE` (AC-2).** They are the only paged non-`GET` sections of the four files. `Transport._page_items` sends every page as `GET` with no body, and `registry.pages` takes none, so `Paging.LINK` would send the wrong method. Their `Paging:` lines name no item key. N's call half and F `test_every_list_record_has_a_case` each fail on that error.
- **`multi_segment` (AC-2).** Five path rows read "may contain `/`", all `subject_digest`: `orgs/list-artifact-storage-records`, `orgs/delete-attestations-by-subject-digest`, `orgs/list-attestations`, `users/delete-attestations-by-subject-digest` and `users/list-attestations`. `teams.md` and `apps.md` have none. AC-2's "`In` `path`" wording excludes the other hits: the body `Field` rows (`version`, `deployments[].version`) and the `query` `ref` of `repos/get-org-rule-suites`. The `subject_digest` of `orgs/list-artifact-deployment-records` does not read so.
- **Gating.** None of the 222 sections commits to, creates, moves or renames a branch, merges, or creates an issue. The `branch`/`merge`/`commit` hits in `rest/orgs.md` are ruleset bodies of `repos/*`, and `orgs/create-issue-field`/`-type` create organisation metadata. So `commands/call.py` stays untouched.
- **Paging lines, keys and rows.**
  - Every `Paging:` line names `per_page` and either "items in `<key>`" or "the response body is the array", except the two bulk lines. The keys agree with `conventions.md` "Lists wrapped in an object".
  - Each `Link`-header section of these families has a `Paging:` line. The two that lack one in `rest/orgs.md` are `hosted-compute/*`.
  - All 223 sections match their index row in method, path and placeholders.
  - There is no non-JSON body, upload or `307`.
- **Fixture.** `ListRoute` matches the path as sent, so a `subject_digest` sent as `%2F` is unrouted: AC-3's `/` cases can fail.
- **Security.** Every record is root-relative under `API_ROOT`, so the PAT reaches the app-authenticated paths only on `api.github.com` (DL-002). UB-3's check, `\b(?:environ|getenv)\b`, does not match body names such as `logical_environment`.
- **Siblings.** Nothing conflicts with #27 (`GATED_OPERATIONS` typing) or #32 (K's pending case, `CREATE_RE`). No test outside F names an ID of these families as pending.

## Coverage

| Criterion | Test | Fails when | Red after TEST |
|---|---|---|---|
| AC-1 | F `test_nothing_is_pending`; N record test; V covered-or-pending, one-module | an ID pending, missing or extra; a method, path or name differs | F yes; N, V no |
| AC-2 paging | F `test_every_list_record_has_a_case` | the LINK set differs from F's case IDs (a bulk `POST` as LINK) | yes |
| AC-2 item_key | AC-3 routes; F `Paging.NONE` → `None` | a wrong or missing key exits 1 | yes (exit 2) |
| AC-2 multi_segment | F `test_the_multi_segment_parameters_are_the_sections` | a name missing, extra or on the wrong record | orgs, users yes; teams, apps no |
| AC-2 version, accept | F `test_every_record_sends_the_default_version_and_media_type` | another version or media type | no (D1) |
| AC-3 | F `test_a_list_record_prints_every_item` | an item missing; `/` sent as `%2F` | yes (exit 2) |
| AC-4 | N `test_every_record_is_sent_as_its_section_documents` | exit not 0; method, path or names differ | no |
| UB-1 | C golden cases; P parity; PR diff | a subcommand's output, exit or parser changes; `users/get-authenticated` edited | n/a |
| UB-2 | K gated, unknown (plus undocumented, C3) | a gated, undeclared or undocumented call sends | n/a |
| UB-3 | C credential; V stdlib | `environ`/`getenv`, a token option, a non-stdlib import | n/a |
| UB-4 | `test_wrapper_delivery.py`; PR diff | either file touched or failing | n/a |
| E2E | N and F through `main` to the API boundary (CI `verify`/`tests`); the real forge is #10's | — | — |

Verdict: READY
