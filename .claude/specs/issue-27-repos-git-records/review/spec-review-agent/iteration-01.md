# spec-review-agent — iteration 01 (tier S, combined)

### B1 — The upload and the `307` re-send are split out of #27 unrecorded, on a reason that inverts #28 D8
Severity: B
Location: change.md § AC-1; § Residuals (first two bullets); decisions/decision-log.md
Defect: AC-1 keeps `repos/upload-release-asset` pending and Residuals send it and the `307` re-send to a new
DESIGN-OPTIONS issue. But the issue's Done and draft AC-2 require both `PENDING` empty, and its Tier line, `prompt.md`
and DL-001 name tier M for exactly this case. #28 D8's exceptions row and Residuals assign both items to #27, and
`transport.py` already has `Transport.upload` (`UPLOAD_ORIGIN`, byte body, media type). No decision-log entry records
the split.
Material-because: the issue's AC-2 ("Both PENDING sets SHALL be empty") is contradicted with no entry, although
`agent-state-convention.md` §2 rule 4 requires one for a re-tier or split (unmaintainable-by-rule
agent-state-convention.md), and #27's "Both PENDING empty" item can then be neither ticked nor closed over
(`issue-tracking.md` "Closing").
Proposed-edit: append DL-002 — Decision: split `repos/upload-release-asset` and the `307` re-send of `repos/update`,
`repos/delete` into one issue (issue-intake, DESIGN-OPTIONS); record the deferral of #27's "Both PENDING empty" item on
#27. Driver: `call` has no byte-body option, media type or route to `UPLOAD_ORIGIN`; `Transport.upload` exists, but
`call` does not reach it. Alternatives considered: re-tier #27 to M (its Tier line) and build both under #28 D8's
exceptions row. Evidence: issue #27 Tier line; #28 design D8, Residuals; `transport.py` `Transport.upload`. Replace the
first two Residuals bullets with: "- Split by DL-002, deferral recorded on #27: `repos/upload-release-asset` (`call`
has no byte body, media type or upload origin; `Transport.upload` exists) and the `307` re-send of `repos/update`,
`repos/delete` (exit 1, #28 D4)." If the split is rejected, re-tier to M instead, recorded as DL-002.

### B2 — `multi_segment` is tested on two records; every other record's `/` encoding is unchecked
Severity: B
Location: change.md § Tests, AC-3
Defect: N compares names only and uses alphanumeric values. F checks `multi_segment` only on `git/list-matching-refs`
and `repos/list-commit-statuses-for-ref`. Of the 213 new records, 57 have a parameter whose row reads "may contain `/`"
(`repos/get-content` `path`, `repos/get-branch` `branch`, `git/get-ref` `ref`, the branch-protection `branch`
records). On any of the other 55, a missing or extra `multi_segment` name would send `/` as `%2F` (or keep it), and
every test listed would still pass.
Material-because: AC-3 ("exactly the path parameters whose `Parameter` row reads 'may contain `/`'") and the issue's
AC-1 ("multi-segment names") are not tested; wrong-behaviour (the request goes to another path).
Proposed-edit: replace "`multi_segment` by the F cases of `git/list-matching-refs` and
`repos/list-commit-statuses-for-ref` (a `ref` holding `/`), else review." with "F
`test_the_multi_segment_parameters_are_the_sections`: `{operation_id: multi_segment}` of the family's records with one
equals F's table transcribed from the sections' 'may contain `/`' rows; plus the `ref`-holding-`/` cases of
`git/list-matching-refs` and `repos/list-commit-statuses-for-ref`."

### C1 — `repos/create-deployment` fits AC-7's class but is not on its list
Severity: C
Location: change.md § AC-7; § Residuals (fifth bullet)
Defect: `rest/deployments.md` documents `auto_merge` (default `true`). GitHub's docs say it "Attempts to automatically
merge the default branch into the requested ref" and answer `202` "Merged branch". The call therefore commits to a
branch, the class AC-7 states, yet AC-7 does not list it. It never writes the default branch, so the trunk guarantee of
`gate_merge_steward` holds.
Proposed-edit: append to the fifth Residuals bullet: "`repos/create-deployment` (`auto_merge`) merges the default
branch into `ref`, never into the default branch, and stays callable."

### C2 — AC-7's test is falsifiable only if F's gated IDs are literal
Severity: C
Location: change.md § Tests, AC-7
Defect: "over the family's gated IDs" also reads as `GATED_OPERATIONS` filtered by family. Read that way, an ID left out
of the mapping is neither refused nor tested (N calls it, and it passes).
Proposed-edit: "over AC-7's IDs of the family, a literal tuple in F, never read from `GATED_OPERATIONS`:".

### C3 — `refuse_gated` needs a membership test, not only new wording
Severity: C
Location: change.md § Files, `commands/call.py` row
Defect: `refuse_gated` refuses when `GATED_OPERATIONS.get(operation_id) is not None`, so an ID mapped to `None` would be
sent. F catches this at green, but the row names only the wording.
Proposed-edit: "`refuse_gated` refuses every ID in `GATED_OPERATIONS` (membership), worded for `None`".

### C4 — Residual routing and the ledger file
Severity: C
Location: change.md § Residuals (third and fourth bullets); § Files
Defect: the `get-commit`/`compare-commits` bullet has no route. The `git/delete-ref` bullet routes to the ledger, which
needs a `docs/findings-ledger.md` row committed in this change (`issue-filing-discipline.md` "The findings ledger").
The memory search finds no such row, and Files says "Nothing else".
Proposed-edit: end the third bullet with "→ ledger"; Files gains "`docs/findings-ledger.md` | the Residuals' ledger rows,
via `memory_compile.py ledger add`".

### D1 — AC-4's `None` arm for the two records with only a `Link` header
Severity: D
Location: change.md § AC-4
Defect: `git/list-matching-refs` and `repos/list-public` have no `Paging:` line, so "the response body is the array"
appears in none of their lines; their `200` row reads "array of".
Proposed-edit: "or `None` when its `Paging:` line says the response body is the array or its `200` response is an array".

Note: the change is 7,998 B against its 8,000 B cap, so each edit must replace text of the same length. The sibling #32
(`pulls/merge-async` → `merge-pr`, a reworded `refuse_gated`) composes with AC-7's `None` branch, so there is no
semantic conflict. On security: every record is root-relative under `API_ROOT`; the gated set covers every record of
these families that can write the trunk, except `git/delete-ref` (UB-4, #28 Residuals); no credential path changes.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_only_the_upload_is_pending`, `test_nothing_is_pending`; V covered-or-pending, one-module | an ID stays pending or has no record (red now) |
| AC-2 | N `test_every_record_matches_its_reference_section` | method, path or a name differs |
| AC-3 | F default version and media type; `multi_segment`: B2 | another version or media type; B2 |
| AC-4 | F `test_every_list_record_has_a_case` + AC-6 cases | the LINK set or an `item_key` differs from F's transcription |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | a call exits non-0 or sends other names |
| AC-6 | F `test_a_list_record_prints_every_item` | either item is missing (red now: no record) |
| AC-7 | F `test_a_branch_writing_record_is_refused` | a gated ID is sent or exits other than 2 (C2) |
| UB-1 | C golden cases; P fork parity | a subcommand's output or exit changes |
| UB-2 | C credential test; V stdlib test | `environ`/`getenv`, a token option, or a non-stdlib import |
| UB-3 | `test_wrapper_delivery.py`; the PR diff | the shared test fails or a file is touched |
| UB-4 | K gated cases; K json-or-empty (`git/delete-ref` 204) | a refusal loses its subcommand, or `delete-ref` is refused |
| E2E | N, F through `main` up to the API boundary (CI `verify`/`tests`); real-forge check is #10's | — |

Verdict: NOT-READY (0 A, 2 B)
