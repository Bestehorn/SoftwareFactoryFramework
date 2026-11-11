# Spec review — spec-review-agent — design iteration 01

### A1 — An array query name (`NAME[]`) passes D4's check, then `registry.send`/`registry.pages` refuse it
Severity: A
Location: design.md § D2 (`--query`; Registry additions, `send`), § D4 Documented names; § Correctness Properties AC-1.2 (`--query state[]=open`)
Defect: D4 checks a `[]` name without the `[]`, but D2 hands the name as written to `registry.send`/`registry.pages`, whose `_check_names` compares it with `query_params`, which hold the bare name (no query row of `rest/*.md` is spelled with `[]`), so a `ValueError` leaves the handler (`_run_command` catches only `GitHubAPIError`) and nothing is sent.
Material-because: AC-1.2 — a documented array query parameter in the spelling `conventions.md` "Query strings" requires is never sent, and K's own `state[]` example fails.
Proposed-edit: D2 Registry additions, append: "`_check_names` compares a query name with one trailing `[]` removed, so `send`, `pages` and `call` accept the array spelling D4 accepts."

### B1 — A `Paging.LINK` record is sent with `ACCEPT_JSON`, not its `accept`
Severity: B
Location: design.md § D2 Registry additions ("The request is therefore exactly AC-1.2's"), § D3 `Paging.LINK`, § D8 This change
Defect: `registry.pages` calls `Transport.pages(path, query, item_key, api_version)` and `Transport._page_items` sends `Accept: ACCEPT_JSON` on every page, so the record's `accept` never reaches a list request; D2's claim holds for `registry.send` only.
Material-because: AC-1.2 ("the record's `api_version` and `accept`") is contradicted for any list record declared with another media type, and the fix then lands in `registry.py`/`transport.py`, which D8 does not give a slice.
Proposed-edit: D2 Registry additions, add: "`pages` passes `accept=operation.accept` to `Transport.pages`, which gains `accept=ACCEPT_JSON` and sends it on every page." D8 This change, add the row "`src/payload/scripts/github_api/transport.py` | `pages` takes `accept`".

### B2 — The reference reader misreads named-variant and constraint rows, so a slice must edit N
Severity: B
Location: design.md § D5 Reference half (body parameters), § D8 A slice (row "never")
Defect: Only a leading `{variant N}` is removed: a named-variant row (`{review-custom-gates-state-required}.state`, `{single_select}.single_select_options`; `docs/api-reference/README.md` "`a{name}.b`") cuts to the empty name and is dropped, and a `(body)` row of Type `constraint` is kept as the name `(body)`. On the pinned reference `actions/review-custom-gates-for-run` reads as having no body parameter, `projects/add-field-for-org` loses `single_select_options` and `iteration_configuration`, and fifteen sections (`pulls/request-reviewers` among them) gain `(body)`.
Material-because: AC-1.1 — a slice covering those operations passes N only by editing `test_github_wrapper_contract.py`, which D8 lists as never edited, or by leaving documented body parameters undeclared, which D4 then refuses (AC-1.2).
Proposed-edit: D5, replace the field-path sentence with "Take each field path, remove a leading variant label (`{variant N}` or a named `{<shape>}`) and the `.` after it, and cut before the first `.`, `[` or `{`; a row whose Type cell is `constraint` names no field." Add to `test_a_section_is_read_as_the_reference_writes_it`: "`actions/review-custom-gates-for-run` gives `environment_name`, `comment` and `state`; `pulls/request-reviewers` gives `reviewers` and `team_reviewers`."

### B3 — A Hypothesis property in a shipped suite
Severity: B
Location: design.md § Testing Strategy (Unit tests), § Correctness Properties AC-1.3 (K `test_any_json_value_becomes_the_body_member`), § Acceptance Criteria Mapping AC-1.3
Defect: The property is placed in K, `src/payload/test/test_github_api_call.py`; #17's cross-wrapper decision X1 (`issue-17-github-wrapper-foundation/review/review-latest.md`, #17 D7) puts any Hypothesis property test in `test/` and keeps `src/payload/test/` pytest-only.
Material-because: regression — a project that installs K without Hypothesis fails at collection; unmaintainable-by-rule `tech-stack.md` ("only the test suites need pytest") as X1 applies it.
Proposed-edit: in all three places, move `test_any_json_value_becomes_the_body_member` to N (`test/test_github_wrapper_contract.py`, which loads the product package); K keeps `test_a_body_member_holds_the_given_json_value`.

### C1 — D4's checks run before `{owner}`/`{repo}` are supplied
Severity: C
Location: design.md § D2 `cmd_call` steps 1–2; § Data flow step 2
Defect: As ordered, the missing-path-parameter check precedes the owner/repo default, so `call issues/get --path issue_number=5` is refused; Correctness Properties AC-1.2 and AC-2.3 assume the reverse.
Proposed-edit: order the steps lookup, path values with the owner/repo default, then D4's checks; add "a defaulted `{owner}` or `{repo}` has a value for AC-2.3".

### C2 — D3's statement about paged sections is false as worded
Severity: C
Location: design.md § D3 `Paging.LINK`, third bullet
Defect: Many paged `GET` sections name no `Link` header (`repos/get-combined-status-for-ref`, `search/code`); the conclusion holds because the two bulk-list `POST`s are the only paged sections that are not a `GET`.
Proposed-edit: "Every paged section is a `GET` except the two `POST …/attestations/bulk-list` operations, which page by cursor without a `Link` header. So `registry.pages` sending no body loses nothing."

### C3 — D7's usage text splits `JSON array` across two lines
Severity: C
Location: design.md § D7 usage block; § Correctness Properties AC-4.1
Defect: "one JSON" ends a line and "array" opens the next after `# `, so the `JSON array` substring K asserts is absent from the docstring as written.
Proposed-edit: rewrap the block so "one JSON array" sits on one line.

### C4 — The slice's list case omits path parameters
Severity: C
Location: design.md § D8 A slice, row `src/payload/test/test_github_api_<family>.py`
Defect: "argv `call <id>`, plus `--query per_page=1`" is refused by AC-2.3 for a record with a path parameter other than `owner`/`repo` (`{issue_number}`, `{org}`).
Proposed-edit: "argv `call <id>` with `--path NAME=VALUE` for each path parameter other than `owner` and `repo`, plus `--query per_page=1` …".

### C5 — AC-5.3's "another method" has no case
Severity: C
Location: design.md § Correctness Properties AC-5.3
Defect: The cases change a record's path only; AC-5.3 names "another method or path".
Proposed-edit: add the case "a record whose index row has another method is named by `_family_problems`".

### C6 — Residual: a body documented as a map
Severity: C
Location: design.md § Residuals
Defect: `copilot/set-copilot-content-exclusion-for-organization` documents its body as `*` (any key); D4 refuses every name not documented, so `call` cannot send it.
Proposed-edit: add to Residuals: "A body documented as a map of any key (`*`, `copilot/set-copilot-content-exclusion-for-organization`) is not callable through `call`; the slice covering `copilot` routes it per `issue-filing-discipline.md`."

### D1 — prompt.md carries counts the slices invalidate
Severity: D
Location: prompt.md § Goal
Defect: "23 records and 1,249 pending operation ids" and "13 pending capabilities" are record counts (`proportionality.md` "Specs state behaviour, not measurements").
Proposed-edit: "one family module per index family holding its records and its pending list, `graphql_only.py` with its pending capabilities".

Verdict: NOT-READY (1 A, 3 B)
