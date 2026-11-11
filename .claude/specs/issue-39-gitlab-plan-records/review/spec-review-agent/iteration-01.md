# Spec review — issue #39, tier S combined pass, iteration 01

Reviewed: `change.md` at HEAD 3beba95, against `rest/plan.md`, `operations-index.md`, `conventions.md`, the
reference README, `families/plan.py`, `registry.py`, `transport.py`, `commands/call.py`, N, V, K and #41's design.
All five edits below together take `change.md` from 7,935 B to 7,969 B; Residuals stay 10 lines.

### C1 — F's AC-1 oracle asks for a record of `plan#promote-an-issue-to-an-epic`, which AC-1 does not map
Severity: C
Location: change.md § Tests, AC-1
Defect: "F's tuple of the family's index References but the two kept IDs" includes `plan#promote-an-issue-to-an-epic`.
  That is the Reference of the index row `POST /projects/:id/issues/:issue_iid/notes`, whose key is not on
  `PENDING` because part 1's `plan#create-an-issue-note` maps it (its comment in `families/plan.py`). So TEST-1,
  transcribing the index, expects one more record than IMPL-1, following AC-1, writes.
Material-because: a risk. TEST-1 and IMPL-1 are written separately and disagree at Green. No AC breaks as written.
Proposed-edit: replace "but the two kept IDs; V `test_every_index_row_is_mapped_or_pending`,\n
  `test_every_declared_key_is_in_its_family`." with "but the two kept IDs and `plan#promote-an-issue-to-an-epic`; V\n
  `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`."

### C2 — The required-attribute test's table can omit the `form` rows that AC-3 makes required
Severity: C
Location: change.md § Tests, AC-3 (`test_the_required_attributes_are_the_sections`)
Defect: F's table is defined as "Required `yes` query and body rows". The `file` rows of
  `plan#upload-a-file-to-a-group`, `plan#create-an-upload`, `plan#upload-a-metric-image-for-an-incident` and both
  "Upload an attachment to the wiki repository" sections are In `form` and Required `yes`. AC-3 sets `required`
  "exactly where its row's Required reads `yes`". N reads `form` as body, but F's literal table has no such rule.
Material-because: a clarification. A test author who reads "body" as the In column would leave these rows'
  `required` untested.
Proposed-edit: replace "F's Required `yes` query and body rows" with "F's Required `yes` non-path rows".

### C3 — A new callable record runs `/clone`, which creates an issue, and the Residuals name only part 1's note record
Severity: C
Location: change.md § Residuals, fourth item
Defect: `plan#update-an-issue-note` (`PUT /projects/:id/issues/:issue_iid/notes/:note_id`, `body`) becomes callable.
  GitLab runs quick actions on an edited note:
  - the GitLab 17.0 quick-actions page says "Quick actions are executed from both new comments and description, and
    when you edit existing ones";
  - `app/services/notes/update_service.rb` calls `QuickActionsService#execute`;
  - `/clone` (Issue) creates an issue.
  The ledger row as written covers `plan#create-an-issue-note` only. This is the class #41 left callable for part 1,
  so it is not a new gap. Checked and not a defect: `plan#update-a-merge-request-note` cannot merge. `/merge` needs
  `merge_request_diff_head_sha` (`lib/gitlab/quick_actions/merge_request_actions.rb`:
  `next unless params[:merge_request_diff_head_sha].present?`). The update service does not pass it, and the section
  does not document it, so DL-003's kept set covers every merge path.
Material-because: a risk worth one sentence. As written, the ledger row understates how issues can be created.
Proposed-edit: replace the item with "- `/clone` runs from any saved issue note or description: part 1's records and
  `plan#update-an-issue-note` → ledger." (one line, 116 columns).

### D1 — K's Files row does not mention the comment above `OP_PENDING_ONLY`
Severity: D
Location: change.md § Files, K row
Defect: K's comment above the constant reads "The Reference of the index row `POST /projects/:id/uploads`, a key only
  on plan's PENDING". That is wrong once the constant names `plan#clone-an-issue`. DL-004's restatement is otherwise
  minimal and keeps the case's meaning ("an id only on a pending list").
Proposed-edit: replace the K row's change cell with "`OP_PENDING_ONLY` and its comment name `plan#clone-an-issue`,
  which AC-1 keeps pending (DL-004)". This also removes 16 B.

### D2 — The Red line expects part 1's two OFFSET cases to fail
Severity: D
Location: change.md § Tasks, Red
Defect: AC-4's test sets the module's OFFSET IDs equal to F's case IDs. So F's list cases include
  `plan#list-all-project-issues` and `plan#list-all-project-labels`. Both are declared before IMPL-1 and pass at Red.
Proposed-edit: replace "fail and its list\n  cases exit 2" with "fail and its\n  new list cases exit 2".

Verified, no finding:
- The kept set: 12 keys. No other plan section commits to or merges into a project branch or creates an issue. The
  wiki writes and attachments commit to the wiki repository.
- AC-1's multi-endpoint rule: the four emoji sections and the two notification sections are the only ones.
- AC-4's heading rule: every GET section headed "List" or "Get all" is a list. Every other GET section returns one
  object or, for the four upload downloads, a file. No GET section has a body row.
- AC-3: all nine `form` rows and the Types `array`, `Hash` and `object` are covered. No `header` row and no array of
  hashes exists. Part 1's kinds and required flags agree with the rule.
- AC-5: every effective Offering names GitLab.com, and no path is under `/admin/`, `/geo/` or `/hooks/`.
- Every named test exists.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_only_the_kept_keys_are_pending`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | a key is left unmapped; `PENDING` differs from F's set; a record sits on a wrong key |
| AC-2 | N `test_every_record_matches_its_reference_section` | a method, path, `Param` name or location differs; a query or body row is undeclared |
| AC-3 | F `test_the_typed_attributes_are_the_sections`, `test_the_required_attributes_are_the_sections`, `test_every_body_is_json_with_no_fixed_pairs` | a kind, required flag, body format or `fixed` pair differs from F's literal tables |
| AC-4 | F `test_every_list_record_has_a_case` | the OFFSET set differs from F's case IDs; any record is KEYSET |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | a refusal; not exactly one request; a sent method, path or name differs |
| AC-6 | F `test_a_list_record_prints_every_item` | the second page is not requested; a scripted page is left unserved; stdout is not `print_json` of both items |
| UB-1 | C, every existing test; the PR diff | a part-1 request, argv, output or exit code changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F AC-1 test | a gated or undeclared ID sends a request or exits other than 2 |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | a token is read from the environment; a non-stdlib import is added |
| UB-4 | `test_wrapper_delivery.py`; the PR diff | a UB-4 file is touched or fails |
| E2E | N, F through `main` in CI `verify`/`tests`; #11's real-instance run | as AC-5 and AC-6 |

No criterion quantifies over an input domain, so the example tests fit and no property test is owed.

Verdict: READY
