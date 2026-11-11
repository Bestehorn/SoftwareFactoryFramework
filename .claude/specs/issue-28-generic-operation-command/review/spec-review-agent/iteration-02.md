# Spec review — spec-review-agent — design iteration 02 (delta)

Fix sites of iteration 01, checked against the worktree code and the pinned reference:

- A1 APPLIED. D2 `query_name`, with `_check_names` comparing a query name through it; D4 "Documented names"; D8
  `registry.py` row. The rule covers the query kind only, so body names and every compatibility call are unchanged.
- B1 APPLIED. D2 `pages` passes `accept`; D8 `transport.py` row; AC-1.2's two `dataclasses.replace` rows. Every
  declared record carries `ACCEPT_JSON` and `API_VERSION_DEFAULT`, so the new default keeps UB-1.1.
- B2 APPLIED. D5's restated rule, run on the pinned `rest/*.md`: `actions/review-custom-gates-for-run` gives
  `environment_name`, `comment`, `state`. `projects/add-field-for-org` gives `issue_field_id`, `name`, `data_type`,
  `single_select_options`, `iteration_configuration`. `pulls/request-reviewers` gives `reviewers` and
  `team_reviewers`. Every `(body)` row has Type `constraint` and drops out (sampled: `issues/update-issue-artifact`,
  `projects/add-item-for-org`, `secret-scanning.md`'s alert update). The two `conditions` constraint rows of
  `actions.md` drop out while their `conditions` object row keeps the name. No field cell opens with a `{…}` label
  that is not followed by `.`. The declared records read equal to their sections under the rule (checked
  `issues/add-assignees`, `issues/update`, `pulls/create-review`, `pulls/merge`), so N passes with no family module
  edited. The only rows the rule reads as `*` are copilot's map body, which Residuals now names. The pin test covers
  numbered and named labels through `projects/add-field-for-org`, which is equivalent to the case I proposed.
- B3 APPLIED. H is `test/test_github_api_call_properties.py` in D8, Testing Strategy, the Mapping and Security
  "Dependencies". V's `scripts_on_path` uses `monkeypatch.syspath_prepend`, and `hypothesis` is in `pyproject.toml`'s
  dev extra.
- C1 to C6 APPLIED. For C2, the only non-`GET` paged sections are `orgs/list-attestations-bulk` and
  `users/list-attestations-bulk`. For C3, each AC-4.1 substring sits on one docstring line, and each line fits in 120
  columns. D1 was left by the conductor.

New text (X4, X6, DL-004), checked:

- `gate_merge_steward.script_call` matches `merge-pr` / `mr merge`, and `API_MERGE_RE` matches a `/pulls/<n>/merge`
  URL. `gate_filing.CREATE_RE` is `(create-issue|issue\s+create)`. None of them matches `call pulls/merge` or
  `call issues/create`. `commands/pulls.py` sends `pulls/merge` for `merge-pr`, and `commands/issues.py` sends
  `issues/create` for `create-issue`.
- `_run_command` returns a handler's integer as the exit code, so a `cmd_call` that returns `EXIT_REFUSED` exits 2.
  `expand` and `_check_names` raise `ValueError` only for what step 4 has already refused, so no `ValueError` leaves
  step 7.
- `issues/remove-label`'s `name` is not `multi_segment` and `_encode_path_value` quotes with `safe=""`, so
  `area%2Fui` and `help%20wanted` hold. `RecordedRequest.path` is the path as sent.
- `registry.lookup` reads each family's `OPERATIONS` on every call, so `monkeypatch.setattr` reaches it.
  `issues/update` documents `title` and `labels` and no query parameter.

Cap: `design.md` is under its 60,000-byte cap. D8's slice table and D5's reader need no further revision before the
slices proceed.

### C1 — "set into" leaves the placement of the AC-1.2 copies open
Severity: C
Location: design.md § Correctness Properties AC-1.2 (the two `API_VERSION_NEXT` rows)
Defect: If a copy is appended beside the original `issues/get` or `issues/list-comments`, `registry.lookup` raises
"is declared 2 times", and `cmd_call` turns that into exit 2.
Proposed-edit: "… set into `github_api.families.issues.OPERATIONS` in place of the originals, with
`monkeypatch.setattr` for the test."

### C2 — The branch-writing residual omits the declared `git/delete-ref`
Severity: C
Location: design.md § Residuals (the bullet on records that write a branch); § Security Considerations "Gates"
Defect: `git/delete-ref` is already a record (`ref` is `multi_segment`), so `call git/delete-ref --path ref=heads/main`
deletes the trunk. `gate_merge_steward` refuses the same deletion when it is spelled as a `git push --delete`. The
compatibility command `delete-remote-branch` already reaches that record and no gate checks it, so this is not a
regression of the "Gates" guarantee.
Proposed-edit: append to the bullet: "`git/delete-ref` is declared already and belongs to the same class;
`delete-remote-branch` reaches it the same way."

### D1 — D8's R row names one of the two registry tests
Severity: D
Location: design.md § D8 This change, row `src/payload/test/test_github_api_registry.py`; § Testing Strategy "Unit
tests"
Defect: Testing Strategy tests both `send` and `path_parameters` in R, but D8 lists only
`test_send_returns_the_response_of_the_record`.
Proposed-edit: "adds `test_send_returns_the_response_of_the_record` and a `path_parameters` test".

Verdict: READY
