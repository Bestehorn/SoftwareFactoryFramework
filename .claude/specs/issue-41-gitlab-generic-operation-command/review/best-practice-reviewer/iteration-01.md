# Best-practice review — design.md, iteration 01

Sources, read 2026-11-11: Python 3.9 `json` (https://docs.python.org/3.9/library/json.html) and `argparse`
(https://docs.python.org/3.9/library/argparse.html); GitLab REST (https://docs.gitlab.com/api/rest/);
`docs/api-reference/gitlab/conventions.md`, `graphql/conventions.md`, `docs/api-reference/README.md`, `rest/*.md`. No
documentation MCP server covers Python or GitLab, so official web docs were used.

Checked and found consistent with the documentation, so no finding: the `call` grammar under argparse. `ArgumentTypeError`
gives exit 2 with the exception's own text and no value. An ambiguous abbreviation (`--fi`) is an error, not a silent
match. `append` with a shared `dest` behaves as the documented `append_const` example does. Also consistent: the
`sys.stdout.buffer` write after a flush, `get_content_type()` and its `text/plain` default, offset paging (`Link`, then
`x-next-page`) and keyset paging (`Link` only), the three credential headers and the job-token refusal on GraphQL,
`$name:` as the variable definition, the cursor variable `after`, and the effective `Offering:` taken from the
section's line or else the page's.

### B1 — A hash's or array-of-hashes' member rows become top-level JSON keys
Severity: B
Location: design.md § D5 "Reference half" (`attributes`, `record_problems`); § D8 slice table, `gitlab_api/families/<family>.py` row
Defect: D5 reads every table row as an attribute of its own and reports "a query or body row that the record lacks",
and D8 names one `Param` per row. So a member row must become a `Param`: `position[base_sha]` under the `hash` row
`position` (`rest/ai-coding.md` "Create a draft note"), or `actions[].action` under `actions[]` (`rest/create.md`
"Create a commit"). In a JSON body, `registry.encode` sends that name as a literal top-level key
(`{"position[base_sha]": "…"}`), and in a form as `actions[].action=…`. The call half compares names only, so it passes
that request.
Material-because: wrong-behaviour. GitLab documents a hash member in JSON as a nested object
(`"override_params": {"visibility": "private"}`; `{"variables": [{"key": "VAR1", "value": "hello"}]}`), and in a query
or form as `override_params[visibility]=` or `actions[][action]=` (`conventions.md` "Arrays, hashes and arrays of
hashes"; docs.gitlab.com/api/rest/). A slice that follows D8 therefore declares records whose calls send neither
spelling, and D5 certifies them. The reference holds such body or form rows on six pages: `ai-coding`, `create`, `verify`,
`software-supply-chain-security`, `gitlab-dedicated` and `growth`. The other choice, a correct record with only `position`, fails
`record_problems` once for every member row.
Proposed-edit: in D5 `attributes`, after "Each name passes through `registry.attribute_name`.", insert: "A row whose
name is another row's name followed by `[key]` or `[].key` (`position[base_sha]` under `position`, `actions[].action`
under `actions[]`) is a member of that row. `record_problems` does not report it when the record declares the parent.
In a record with a JSON body it is never a `Param` of its own: its value goes inside the parent's value
(`-F 'position={"base_sha": "…"}'`), which `registry.encode` sends nested in JSON and as `position[base_sha]` pairs in a
query or form. A query or form record may still declare it (part 1's `not[labels]`)." In D8's family-module row,
append: "A member row is carried by its parent's `HASH` or `ARRAY_OF_HASHES` `Param` (D5)." In
`test_a_section_is_read_as_the_reference_writes_it`, add: "`ai-coding#create-a-draft-note` reads `position[base_sha]`
as a member of `position`."

### B2 — `-F` accepts `NaN` and `Infinity`, which are not JSON
Severity: B
Location: design.md § D2 "The arguments" (`-F/--field`); § D4, first row
Defect: D2 takes the value of `-F` from plain `json.loads`. That function "understands `NaN`, `Infinity`, and
`-Infinity` as their corresponding `float` values, which is outside the JSON spec" (Python 3.9 `json`). So `-F x=NaN`
is not refused with exit 2, as D2 and D4 state. The value passes `KIND_ACCEPTS` as a `SCALAR` and is sent: as
`{"x": NaN}` by `json.dumps`, whose default `allow_nan` writes it ("not JSON specification compliant"), as `x=nan` in a
query or form, and as a `NaN` variable for a GraphQL record.
Material-because: wrong-behaviour. A call that D4 says exits 2 with no request instead sends GitLab a body that is not
JSON: the RFC does not permit NaN or infinite numbers, as the same Python page states.
Proposed-edit: in D2's `-F/--field` bullet, replace "with the value `json.loads` parses" with "with the value
`json.loads(s=TEXT, parse_constant=…)` parses, its `parse_constant` raising `ValueError`. `NaN`, `Infinity` and
`-Infinity`, which plain `json.loads` accepts outside the JSON specification, are therefore text that is not JSON".

### C1 — A `HEAD` record's result is its headers, and `call` prints nothing for it
Severity: C
Location: design.md § D3 table; requirements.md AC-1.5
Defect: `HEAD` records such as `create#get-file-metadata-only` (`HEAD /projects/:id/repository/files/:file_path`)
answer with an empty body and carry their result in the `X-Gitlab-*` headers (`conventions.md` "Response headers worth
reading"). AC-1.5 prints nothing for an empty body, so `call` returns nothing of such a record's result.
Proposed-edit: under design.md `## Residuals`, add: "A `HEAD` record's result is its response headers. `call` prints
nothing for it (AC-1.5), and printing the headers is outside this ask."

Verdict: NOT-CLEAN (0 A, 2 B)
