# Spec review — issue #41 design, iteration 03 (spec-review-agent, delta)

Iteration 02's B1 (Z3) holds. The restated item reads every section the brief names as written:

- `create#health` (`GET /projects/:id/repository/health`, one `query` row `generate`), `verify#retrieve-the-latest-pipeline` (one `query` row `ref`) and `no-stage-assigned#set-up-asana` (`PUT /groups/:id/integrations/asana`, `body` rows only) have no `path` row, so they show no difference.
- `ai-coding#retrieve-merge-request-dependencies` has only the `path` row `id`, which is a placeholder of its path. The missing `merge_request_iid` row is no difference.
- `create#add-changelog-data-to-file` and `create#get-file-metadata-only` pass the same way.
- D4's check reads `registry.placeholders` of the record, not of the table, so `call` takes `--path merge_request_iid` there.

The fix sites from iteration 02 are applied as proposed:

- C1: `rest/*.md` has two `header` rows. Both are in the two "The NuGet Symbol File Download Endpoint" sections, and both of those are `*name` globs. `name or context` is the only alternation row, and its section also lists `name` and `context` (both `body`), as the new pin says. `In` takes only `body`, `path`, `query`, `form` and `header`, which is the set D5 reads.
- C2, C3 and C4 are applied.
- D1: the first non-empty line under every `###` heading holds at least one `` `METHOD path` `` span.

The rest of the delta holds:

- Z1: with `--path issue_iid=5`, a build without `parse_constant` sends the request and exits 0, so the test can fail. A `-F` usage message names `-F/--field`. The usage text holds no `NaN` or `Infinity`.
- Z2: `not[labels]` is part 1's (`families/plan.py`, `Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY)`). `growth#force-a-variant-assignment` has `context[user]`, `context[namespace]` and `context[project]` and no `context` row.
- ST2-C4: `scripts/api_reference/verify.py` imports `yaml`, and its `anchors` is the restated rule: fenced blocks are dropped, and the suffix counts over every heading. `common.Slugger` exists.
- TA2-C2: the `/geo/proxy` and `/hooks/:hook_id/custom_headers/:key` sections sit on `rest/openapi-only.md`. That page has no Availability line, so only the path arm holds, as AC-3.1's example says.
- TA2-C3: `registry.expand` raises `GitLabAPIError` without `details` (`errors.py`, `details: Any = None`).
- ST2-D2: `_common.print_json(*, value)` is keyword-only, as `print_bytes(*, data)` now is.
- design.md is under its cap. Residuals has 10 lines.

### C1 — The remaining path-row item names only rows that another endpoint of the section holds
Severity: C
Location: design.md § D5 "Reference half", `record_problems`, the path-row item; § D8, the exceptions row
Defect: The endpoint comparison already fixes a record's placeholders. So "an `In` `path` row that is no placeholder of the record's path" fires only where a table lists the rows of several endpoints:
- `fulfillment#delete-an-ldap-group-link-deprecated`: its `…/ldap_group_links/:cn` key lacks `provider`.
- The `/packages/conan/v1/…` key of each Conan section in `rest/package.md` whose table lists `id`, for example `package#verify-availability-of-a-conan-repository`: that key has no `:id`.
- `package#retrieve-a-recipe-snapshot`, on both keys: the index row `/projects/:id/packages/conan/v1/conans/:package_version/:package_username/:package_channel` has no `:package_name`. No record of that Reference passes N, so the package slice must leave the Reference pending even though the record would be correct.

The several-keys Residual routes all of these, so no slice is forced to edit a "never" file. For a `*name`-glob record, the item reads the glob row as no placeholder. The exceptions row's "N's path reading" names `sent_call` and `call_problems`, but not this item.

Proposed-edit:
- In § D5, replace the item with "an `In` `path` row that is a placeholder (`registry.placeholders`) of none of the section's endpoints. A placeholder with no such row, or a row that only another endpoint of the section holds, is no difference: the endpoint comparison already fixes the path, and some tables omit the row (`create#health`) or list the rows of every endpoint (`package#retrieve-a-recipe-snapshot`);".
- In § D8's exceptions row, write "N's path reading (`record_problems`' path-row item, `sent_call`, `call_problems`)".
- Add to the reader pin: "a `create#health` record (`GET /projects/:id/repository/health`, the query `Param` `generate`) has no `record_problems`."

Slices #35–#40 and #42–#44 can proceed by editing only their family module, `graphql_only.py` and their own tests. D8's exceptions route the request forms that part 1 does not build and the gated records. The several-keys Residual routes References that hold more than one key, C1's cases included. No change in this revision contradicts text that an earlier iteration passed.

Verdict: READY
