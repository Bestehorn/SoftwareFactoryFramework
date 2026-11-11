# spec-review-agent — iteration 01 (tier S, combined: all lenses)

### A1 — AC-5 pages two object answers and leaves one paginated list unpaged
Severity: A
Location: change.md § Acceptance criteria AC-5; § Tests AC-5
Defect: By heading, `security-factory#list-all-project-security-settings` and
`software-supply-chain-security#list-all-token-associations` are `Paging.OFFSET`, but GitLab answers each with one
object (docs.gitlab.com/api/project_security_settings `{"project_id": 7, …}`, /api/personal_access_tokens
`{"groups": [ …`), so `transport._page_items` raises "not a JSON array" and every real call exits 1.
`security-risk-management#retrieve-project-external-status-check-services` is paginated (gitlab-org/gitlab@a186442
`ee/lib/api/status_checks.rb`: `use :pagination`, `present paginate(…)`) yet `Paging.NONE`, so `call` prints page one
only. N and F answer each record in the shape it declares, so neither fails.
Material-because: wrong-behaviour: two records never succeed against GitLab, one drops every item past page one.
Proposed-edit: AC-5 →
```
- AC-5 A new record SHALL be `Paging.OFFSET` when it is a `GET` whose section heading begins "List" or "Get all", or
  is `#retrieve-project-external-status-check-services`, but not `#list-all-project-security-settings` or
  `#list-all-token-associations`; every other `Paging.NONE`.
```
Tests AC-5: `its "List"/"Get⏎  all" `GET` sections;` → `AC-5's set;`. Append DL-006 superseding DL-004's paging
clause, Evidence the three sources above.

### B1 — The `avatar` of `POST /users` and `PUT /users/:id` is a file; AC-4 makes it `SCALAR`
Severity: B
Location: change.md § AC-4
Defect: `#create-a-user` and `#modify-a-user` list `avatar` with an empty Type and no "file upload" note, so AC-4
types it `SCALAR`; GitLab declares it as it declares `PUT /user/avatar`'s (gitlab-org/gitlab@a186442 `lib/api/users.rb`
`optional_attributes`: `optional :avatar, type: ::API::Validations::Types::WorkhorseFile`; docs: "Image file for user's
avatar"). `--file avatar=…` is refused (exit 2, `KIND_ACCEPTS`); `-f avatar=…` sends a JSON string.
Material-because: issue #42 AC-1 ("one `Param` per query or body attribute with its `Kind`"); wrong-behaviour.
Proposed-edit: AC-4 →
```
- AC-4 Each new `Param`'s `kind` SHALL be `FILE` for a row noted "file upload" and for `avatar` on `PUT /user/avatar`,
  `POST /users` and `PUT /users/:id` (each a `WorkhorseFile`); `ARRAY_OF_HASHES` for an `array` row with `name[].…`
  rows; `HASH` for `object`; `ARRAY` for any other Type naming an array; else `SCALAR`. Its `required` SHALL be true
  exactly where Required reads `yes`.
```
DL-006 also supersedes DL-004's avatar clause.

### B2 — DL-002 and the #42 comment give the administrator sections records; change.md gives them none
Severity: B
Location: change.md § Ask; § Residuals, second bullet; decisions DL-002
Defect: DL-002 decides "the administrator sections get records of their own", and #42 comment 6788677208 repeats it;
the Ask ("join no record") and the Residual ("`#as-an-administrator`, `-1`, `-2` get no record") cite DL-002 for the
opposite. An implementer following DL-002 writes three records that F's AC-1 table refuses.
Material-because: unmaintainable-by-rule `agent-state-convention.md` §2 (a decision changes by a superseding entry)
and `issue-tracking.md` (the issue is the live record).
Proposed-edit: append DL-005, Decision "`#as-an-administrator`, `-1`, `-2` get no record: their keys are mapped and N
refuses their rows (`extern_uid`, `order_by`, `sudo`) on part 1's records; their attributes are a ledger row",
Supersedes DL-002 (its administrator clause); comment the correction on #42. The Ask from "Open" →
```
Open
questions: the administrator sections get no record (DL-005); a download is a plain record printed by #41 D3 (DL-002).
```
Residuals second bullet →
```
- `#as-an-administrator`, `-1`, `-2` get no record (DL-005): their keys are mapped, and N refuses their rows on
  part 1's records → ledger. `#update-application-settings` has no table, so no `Param` → ledger.
```

### C1 — The `DELETE /admin/token` token also reaches standard error
Severity: C
Location: change.md § Residuals, last bullet
Defect: The `token` rides in the `DELETE`'s query; `Transport._send` raises `f"{method} {url} answered …"` with the
whole URL and `_report` logs it, so a 4xx answer writes the token to standard error.
Proposed-edit: "(in the `DELETE`'s query)" → "(the `DELETE`'s URL and error)".

### C2 — `security_governance`'s AC-7 test has no case
Severity: C
Location: change.md § Tests AC-7
Defect: Its one record is a `PUT`; a test parametrized over nothing is SKIPPED (pytest 9.2.0
`get_empty_parameterset_mark`, default `skip`, unset in `pyproject.toml`), which `tests-must-not-fail.md` forbids;
#41 D8 writes the list example only for a family with a paged record.
Proposed-edit: "one case per `Paging.OFFSET` record," → "one case per `Paging.OFFSET` record (four⏎  modules),".

### D1 — Room under the cap
Severity: D
Location: change.md § Files "Nothing else"; § Residuals, first bullet
Defect: change.md is 7,986 B; A1, B1, C1, C2 add bytes.
Proposed-edit: delete "; policy-store policies persist to the database, docs.gitlab.com/api/policy_store" (to a DL-007
"no record is gated") and " (`registry.lookup`)". All edits applied: 7,970 B, Residuals 8 lines; reflow is
byte-neutral.

## Checked, no finding

- **17 keys.** N's reader: 10 multi-endpoint sections leave 15 endpoints (`/projects/:id/` mapped in nine, `PUT` first
  in `#set-your-user-status`), none with a second Reference; plus the `https://HOST` key and the HMAC `PATCH`. AC-1's
  two keys are the only pending keys with two References; no ID gets two records.
- **HMAC.** The `X-Gitlab-*` headers are on a "Request headers:" line (the only one); `Transport.request` takes none.
- **Gating.** No write endpoint is under `repository`, `deploy_keys`, `protected_branches`, `merge` or `issues`;
  job-token-scope records edit allowlists; `status_check_responses` sets a check result, merging nothing.
- **Reading.** No `header` row, no stray path row, no parentless bracket row; members are `granular_scopes[].…` under
  an `array` (four sections); FILE rows: four on `#update-application-appearance`, `#create-a-secure-file` `file`.
- **Secrets.** `POST /admin/token` sends `token` in a JSON body; the stdout bullet covers every token section.
- Every named C, K, P, N, V test exists; no other test names an ID of these families.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_every_key_has_its_record`; V mapped-or-pending, in-its-family | a key unmapped, a wrong ID, an extra record |
| AC-2 | F `test_only_the_unmapped_keys_are_pending` | `PENDING` is not the 17 keys |
| AC-3 | N `test_every_record_matches_its_reference_section` | a method, path, name or location differs |
| AC-4 | F kind and required tables | a non-`SCALAR` kind (B1's `avatar`s) or a required name differs |
| AC-5 | F `test_every_list_record_has_a_case` | the OFFSET set is not AC-5's (A1) |
| AC-6 | N `test_every_record_is_sent_as_its_section_documents` | a call refused, non-0, or other names |
| AC-7 | F `test_a_list_record_prints_every_item` (four modules) | an item or page missing (red: exit 2) |
| UB-1 | C `test_a_subcommand_form`; diff | `issue start`/`assign` output or exit changes |
| UB-2 | K gated, unknown, non-JSON | a gated or undeclared ID sends; bytes altered |
| UB-3 | C config refusals, environment token; P stdlib | an environment read, a non-stdlib import |
| UB-4 | `test_wrapper_delivery.py`; diff | a UB-4 file touched or failing |
| E2E | N, F via `main` to the API boundary (CI `verify`/`tests`); real instance #11 | — |

Verdict: NOT-READY (1 A, 2 B)
