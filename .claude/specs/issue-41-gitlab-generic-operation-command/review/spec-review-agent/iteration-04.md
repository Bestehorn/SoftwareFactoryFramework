# Spec review — issue #41 design, iteration 04 (spec-review-agent, delta, the cap)

Iteration 03's C1 is applied at all three sites:

- § D5's path-row item reads "an `In` `path` row that is a placeholder (`registry.placeholders`) of none of the
  section's endpoints".
- § D8's exceptions row names "`record_problems`' path-row rule, `sent_call`, `call_problems`".
- The reader pin holds the `create#health` record.

The author cut the second sentence of my proposed edit, and the rule loses nothing by it. The item list names only
differences, and "a query or body row that the record lacks" leaves path rows out, so a placeholder with no row is no
difference.

I re-ran the restated rule against the reference:

- `fulfillment#delete-an-ldap-group-link-deprecated` has the endpoints `DELETE /groups/:id/ldap_group_links/:cn` and
  `…/:provider/:cn`, and the path rows `id`, `cn` and `provider`. Every row is a placeholder of the second endpoint, so
  the record of neither index key gets a problem.
- `package#verify-availability-of-a-conan-repository` has the endpoints `GET /packages/conan/v1/ping` and
  `GET /projects/:id/packages/conan/v1/ping`, and the path row `id`. `id` is a placeholder of the second endpoint, so
  the `/packages/conan/v1/ping` record gets none.
- `package#retrieve-a-recipe-snapshot`: `package_name` is a placeholder of its first endpoint and `id` of its second.
  So a record on either index key (`operations-index.md` holds both paths under this Reference) gets none.
- `create#health` has no `path` row, so the item is silent. `generate` is its one row, a query row, and its anchor is
  unique on `rest/create.md`.
- Across every `###` section of `rest/*.md`, the rule still reports `In` `path` rows in only two kinds of section: the
  ones whose endpoint is a `*name` glob, and the ones whose endpoint has a `(*path/)` segment (`deploy`, `orbit`,
  `package`, `verify`). requirements Residuals names both as request forms part 1 does not build, so D8's exceptions
  row routes them.

The test lane's iteration-03 B1 fix:

- No part-1 record is flagged by the new arm. The only part-1 `Param` names that hold `[` or `:` are the eleven `not[…]`
  names of `plan#list-all-project-issues` (`families/plan.py`). Each one is a `Location.QUERY` `parent[key]` name, and
  each one is a row of `rest/plan.md` "List all project issues". No family module sets `BodyFormat.FORM`.
- `software-supply-chain-security#create-an-application` is `POST /applications`, the first of the page's two "Create
  an application" headings, and the index links it as `#create-an-application`. Its table has the `body` rows
  `granular_scopes` and `granular_scopes[].access`. The case's `Param` matches its row by name and location, so only
  the new arm can report it. `[].access` is no `parent[key]` name in a record of any `BodyFormat`
  (`RestOperation.body` defaults to `BodyFormat.JSON`).
- `gitlab-dedicated#update-a-geo-site` has no bracketed row, so `test_an_unreachable_call_matches_its_reference_section`
  is unaffected.

The rest of the delta:

- design.md is under its cap, and Residuals has 10 lines.
- AC-3.2's Correctness Properties entry ("pins the reader and the path-row rule they use") matches the test's own
  description.
- No change contradicts text that an earlier iteration passed.

### C1 — The bracket arm's "unless" can be read as exempting the whole item
Severity: C
Location: design.md § D5 "Reference half", `record_problems`, the `Param` item
Defect: The sentence "…, or whose name holds `[` or `:`, unless it is a `parent[key]` name of a `Location.QUERY`
  `Param` or of a `BodyFormat.FORM` record" can be read two ways:
  - The "unless" covers only the bracket arm. This is the reading the test lane's proposed "and is not a `parent[key]`
    name …" fixed.
  - The "unless" covers the whole item. Then a query `parent[key]` `Param` that matches no row passes, for example
    `not[foo]` on `plan#list-all-project-issues`, and so does one in the wrong location.
  No case in `test_the_method_rejects_a_call_that_differs` or in the pin list tells the two readings apart.
Proposed-edit: split the item into three: "a `Param` that matches no row by name; a `Param` whose location differs
  from its row's `In`; a `Param` whose name holds `[` or `:` and is not a `parent[key]` name of a `Location.QUERY`
  `Param` or of a `BodyFormat.FORM` record (part 1's `not[labels]`);".

### C2 — No case tells the restated path-row rule from the rule it replaced
Severity: C
Location: design.md § D5 `test_a_section_is_read_as_the_reference_writes_it`, the `create#health` pin
Defect: `create#health` has no `path` row. It passes under the restated rule and under the replaced "no placeholder of
  the record's path" rule alike, so a build of the replaced rule passes every named case. The first slice to declare
  `package#retrieve-a-recipe-snapshot` would then have to edit N's path reading, because each of its keys lacks one
  row's placeholder. D8's exceptions row allows that edit only for a request form part 1 does not build.
Proposed-edit: append to the pin: "A record built as `package#retrieve-a-recipe-snapshot` on
  `GET /projects/:id/packages/conan/v1/conans/:package_version/:package_username/:package_channel`, with no `Param`,
  gets no problem either, though its table has the path row `package_name`."

### C3 — The sixth case leaves the record's other `Param`s open
Severity: C
Location: design.md § D5 `test_the_method_rejects_a_call_that_differs`, the `create-an-application` case
Defect: "a record built as `software-supply-chain-security#create-an-application` with the BODY `Param`
  `granular_scopes[].access`" does not say which other `Param`s the record has. Built with that one `Param` only, the
  record already gets problems for the rows it lacks (`name`, `redirect_uri`, `scopes`, `confidential`,
  `granular_scopes`). So an oracle of "any problem" passes without the bracket arm.
Proposed-edit: "a record built as a slice writes `software-supply-chain-security#create-an-application`
  (`POST /applications`, a BODY `Param` for each row, with `granular_scopes` carrying its `granular_scopes[].…` rows),
  plus the BODY `Param` `granular_scopes[].access`. Its one problem names `granular_scopes[].access`, and
  `record_problems` checks it."

Slices #35–#40 and #42–#44 can proceed by editing only their family module, `graphql_only.py` and their own tests.
D8's exceptions row routes the request forms part 1 does not build (the glob rows above included) and the gated
records. The several-keys Residual routes the References that hold more than one key.

Verdict: READY
