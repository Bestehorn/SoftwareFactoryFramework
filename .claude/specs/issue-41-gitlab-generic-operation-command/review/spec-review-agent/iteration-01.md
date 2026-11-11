# Spec review — issue #41 design, iteration 01 (spec-review-agent)

Every symbol claim checked holds. That covers `registry`, `transport`, `_common.PATH_PROJECT`, `gitlab_wrapper._run`/`_report`, `gate_merge_steward.script_call`/`API_MERGE_RE`, `gate_filing.CREATE_RE`, `verify.py` `anchors`, the pin, the "Only in GraphQL" table and the `/<route-prefix>/` keys on `package.PENDING`. `family_problems`' rules find nothing on today's tree. #28 X1–X4 and X6 do not recur; X5 does (B1).

### B1 — The reference reader takes every table name for an attribute name (#28 X5 recurs)
Severity: B
Location: design.md § D5 "Reference half" (`attributes`); § D8 "A slice", the "never" row
Defect: D5 reads each row's name through `registry.attribute_name` only. The pinned reference also writes member rows (`actions[].action`, `strategies:name`, `files:content`), annotated and footnoted names (`approvals_before_merge (deprecated)`, `version[^version-attribute-include]` beside a second `version` row), alternations (`name or context`) and `In` `header` rows. `record_problems` then demands a `Param` of each literal name, so a slice either declares `approvals_before_merge (deprecated)`, which `call` sends as that body key, or edits N, which D8 forbids.
Evidence: `rest/create.md` "Create a commit", "Add changelog data to file"; `rest/ai-coding.md` "Update approval configuration for a project"; `rest/verify.md` "Create a feature flag"; `rest/openapi-only.md` "The NuGet Symbol File Download Endpoint"; slice #35 AC-5 (every create and ai-coding record proven by this method).
Material-because: AC-1.1 — D8's list of the files a slice edits is false for #35; and wrong-behaviour — a record transcribed to pass N sends a key GitLab does not read.
Proposed-edit: in D5 `attributes`, replace "Each name passes through `registry.attribute_name`. `In` is `path`, `query` or `body`; `form`, a multipart part, is read as `body`." with "A name is the backticked text up to a ` (` or `[^` (an annotation, a footnote), then `registry.attribute_name`; a name read twice is one attribute. A row named as another name followed by `[].` or `:` (`actions[].action`, `strategies:name`) describes a member of that attribute and is not compared. `In` is `path`, `query` or `body`; `form`, a multipart part, is read as `body`. An `In` `header` row and an alternation (`name or context`) are request forms part 1 does not build (requirements Residuals), and their keys stay pending." Add to `test_a_section_is_read_as_the_reference_writes_it`: "`create#create-a-commit` has the body attribute `actions` and no `actions[].action`; `ai-coding#update-approval-configuration-for-a-project` has `approvals_before_merge`."

### B2 — D8 bars files that a request-form slice and a gating slice must edit
Severity: B
Location: design.md § D8 "A slice", rows "never" and "the exceptions"
Defect: The exceptions row lets a slice change `transport.py` and `registry.py` for a request form part 1 does not build. But N compares paths "with each `:name` replaced" and reads "its path after `/api/v4`". So a `*name` glob, a `<route-prefix>` segment or an `https://HOST` path also needs N changed, and the "never" row forbids that. The same row forbids `commands/*`, which holds the exception's `GATED_OPERATIONS`.
Evidence: `rest/package.md` "Download a distribution Release file" (`GET /<route-prefix>/dists/*distribution/Release`, whose `In` `path` row `distribution` has no `:` placeholder); requirements Residuals ("stay with the slice whose family needs one"); D1/D8 put `GATED_OPERATIONS` in `commands/call.py`.
Material-because: AC-1.1 ("SHALL name every file a slice edits").
Proposed-edit: exceptions row → "`transport.py`, `registry.py` and N's path reading (`call_problems`, `sent_call`) for a request form that part 1 does not build (requirements Residuals); `commands/call.py` `GATED_OPERATIONS` or the hook gates for a record that writes a branch or creates an issue (Residuals)". "never" row → "`gitlab_wrapper.py`, `commands/*` (but `GATED_OPERATIONS`), `families/__init__.py`, `gitlab_wrapper_fixtures.py`, `test_gitlab_wrapper_coverage.py`, and N outside the exceptions".

### C1 — Paging parameters: required or only allowed?
Severity: C
Location: design.md § D5 "Paging parameters"
Defect: "count as query rows in both halves" has two readings. In the first, they are rows a record lacks: `plan#list-all-project-labels` and `software-supply-chain-security#as-a-regular-user` then need `page`/`per_page` Params their sections do not list, and a KEYSET record with a `fixed` `pagination` sends it twice in N's call half. In the second, they are names that are only allowed.
Proposed-edit: "For a paged record they are documented query names: a record declares them or not, a sent one is no difference, and none is a row a record lacks."

### C2 — Several endpoints on one line
Severity: C
Location: § D5 "A section", `endpoints`
Defect: The design reads "each `` `METHOD path` `` line", but a section can list several endpoints, comma-separated, on one line (`rest/software-supply-chain-security.md` "List all access requests for a group or project", `rest/verify.md` "Runners API"). Read one per line, the whole-index pin fails.
Proposed-edit: "`endpoints`: every backticked `` `METHOD path` `` on the line under the heading; one line can hold several, comma-separated."

### C3 — openapi-only.md's Geo and system-hook paths count as reachable
Severity: C
Location: § D5 "The rule"
Defect: `/geo/...` (`rest/openapi-only.md` "geo") and `/hooks/:hook_id/custom_headers/:key` carry no `Offering:` and no `/admin/`. The rule therefore calls them reachable, though the glossary's Geo and administrator classes name them.
Proposed-edit: first arm → "its index row's path starts with `/admin/`, `/geo/` or `/hooks/` (the administrator, Geo and system-hook APIs)".

### C4 — A refused config comes before the AC-2 refusals
Severity: C
Location: § D4 table
Defect: `_run` reads `config/gitlab.json` before any handler runs. With a refused config, `call plan#no-such-operation` therefore exits 1, while AC-2.1–AC-2.4 state exit 2 with no condition.
Proposed-edit: under the table: "The handler's refusals apply once `config/gitlab.json` loads; a refused config exits 1 first (`_run`)."

### C5 — AC-5.3: no case removes a record's row
Severity: C
Location: § Correctness Properties, AC-5.3
Defect: The four cases change a record's row but none removes it. The branch for "a record whose operation ID is the Reference of no row" has no oracle.
Proposed-edit: add the case "a record whose Reference no row carries is named by `family_problems`".

### C6 — No test is named for a capability slice
Severity: C
Location: § D8 "A slice"
Defect: D5 proves REST records only (requirements Residuals), and the slice table names a test module only for paged REST records. A `graphql_only` record is therefore proven by nothing beyond K's synthetic records.
Proposed-edit: add the row "`src/payload/test/test_gitlab_api_graphql_only.py` | new, for a capability: one example per record through `call`, judged by the fake host's `GRAPHQL_URL` request".

### D1 — Data flow repeats D2 and D3
Severity: D
Location: § Data flow
Proposed-edit: delete the section. D2's steps and D3's table already carry it, and the design is near its cap.

### D2 — Which option gave a name
Severity: D
Location: § D4 table, the undocumented-parameter row
Defect: `-f` and `-F` share one `dest`, so the message can name `-f/-F` but not which of the two.
Proposed-edit: "each undocumented name with its option (`--path`, `--query`, `-f/-F`, `--file`)".

Verdict: NOT-READY (0 A, 2 B)
