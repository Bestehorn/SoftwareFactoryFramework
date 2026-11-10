# Design review, iteration 01, lane spec-review-agent (issue #13, tier M)

### B1 — The "Differences from #17" table omits five structural divergences
Severity: B
Location: design.md § Differences from the GitHub sibling #17; § Overview ("same structure, differences listed below")
Defect: Unrecorded against #17's design.md: (1) one `commands.py` with the parser in the entry script, #17 a discovered `commands/` package whose modules `register`; (2) exceptions in `errors.py`, #17's in `transport.py` with `RateLimitError`, `GraphQLResponseError`; (3) `Transport.call(operation=<record>)` on imported records, #17 `registry.call(transport, operation_id)` via `lookup`; (4) no GraphQL record type in part 1, #17 has `GraphQLOperation`; (5) test seams `handlers=` on `Transport` and `main`, #17 patches `HTTPSHandler.https_open` and injects `sleep`/`clock`.
Material-because: unmaintainable-by-rule `design-principles.md` (established patterns): DL-001 binds both wrappers to one structure and the design asserts every difference is listed, so #15's and #14's workers inherit two layouts with no record of which is intended.
Proposed-edit: Add rows: `Commands | one commands.py, parser in gitlab_wrapper.py | commands/ package, discovered`; `Exceptions | errors.py: GitLabAPIError, ClaimError | transport.py: GitHubAPIError, RateLimitError, GraphQLResponseError`; `Record call | Transport.call(operation=…) | registry.call(transport, operation_id)`; `GraphQL records | none in part 1 | GraphQLOperation`; `Test seams | handlers= on Transport and main | https_open patched, sleep and clock injected` — each GitLab cell ending with its reason; where no forge reason exists, adopt #17's form.

### B2 — `pipeline log` text output fails on Windows piped stdout
Severity: B
Location: design.md § Entry script and subcommands ("Results go to standard output as JSON (the job traces of `pipeline log` as text)")
Defect: Python docs (`sys.stdout`): on Windows "pipes use the system locale encoding (i.e. the ANSI codepage)", so a trace character outside cp1252 raises `UnicodeEncodeError` — the crash `scripts/github_wrapper.py` `_force_utf8_output` records (issue #299) and #17 D6 step 1 prevents.
Material-because: wrong-behaviour — UB-1 fixes exit 0 for `pipeline log`; on the project's platform this path ends in a traceback and exit 1.
Proposed-edit: Replace the sentence with "Before parsing, `main` reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with `errors=\"replace\"` where the stream has `reconfigure` (#17 D6); results go to standard output as JSON (the job traces of `pipeline log` as text)."

### B3 — `registry.py` is marked never edited by a family worker, yet the Residuals edit it
Severity: B
Location: design.md § Layout, "Shared files (AC-1.3)" row `gitlab_api/registry.py`, `errors.py`, the two `__init__.py`; § Residuals
Defect: The row says "no", while the Residuals send a raw-bytes body and GraphQL multipart to "the family needing one" and "Only in GraphQL" records to `families/graphql_only.py`; these need a `BodyFormat`/`Kind` member and a GraphQL record type, defined only in `registry.py`.
Material-because: AC-1.2 / AC-1.3 — the table misstates which shared file a part-2 family edits, leaving those edits without the landed-first rule the `transport.py` row gives.
Proposed-edit: Split the row: `gitlab_api/registry.py | record types and discovery | only when a family needs a record type, field or enum member part 1 lacks (Residuals: raw-bytes body, GraphQL multipart, GraphQL records); that edit is its own commit, landed before the family's`; keep `errors.py` and the two `__init__.py` at "no".

### B4 — The UB-2 standard-library test needs Python 3.10 in a shipped suite
Severity: B
Location: design.md § Correctness Properties, UB-2
Defect: The AST scan uses `sys.stdlib_module_names` (Python 3.10+) inside `src/payload/test/test_gitlab_transport.py`, a shipped suite.
Material-because: unmaintainable-by-rule `tech-stack.md` (shipped `src/payload/` stays Python 3.9-compatible; `requires-python = ">=3.9"`): on 3.9 the test raises `AttributeError`.
Proposed-edit: Replace "modules in `sys.stdlib_module_names` (CI runs Python 3.10, <link>)" with "built-in modules and modules whose `importlib.util.find_spec` origin lies under `sysconfig.get_paths()` `stdlib` or `platstdlib` (#17 UB-2.2)".

### C1 — The owner of a key two families share is undecided
Severity: C
Location: design.md § Layout, "Endpoint family"
Defect: Five index keys span two families (`GET /projects`, `DELETE /projects/:id/share/:group_id`; three `ml_models` file paths in deploy and openapi-only); "mapped once, by either family" lets two parallel workers both map it or both drop it from `PENDING`.
Proposed-edit: "A key that rows of two families share belongs to the family whose module name sorts first: only that module lists it in `PENDING` and maps it; the coverage test matches by key, so the other family's rows count as covered."

### C2 — Origin comparison is not normalised
Severity: C
Location: design.md § Transport, "URLs"
Defect: "scheme, host and port" leaves host case and an absent default port open, yet `Link` and redirect targets are compared with it to decide whether the credential is sent; #17 D3 states both.
Proposed-edit: "…the scheme, the lower-cased host and the port (443 when absent); a URL's origin is computed the same way."

### C3 — Residual missing: an unbounded `Retry-After`
Severity: C
Location: design.md § Residuals
Defect: `conventions.md` "Headers and the 429 response": `Retry-After` can reach a day (project and group creation), so one AC-3.2 sleep outlasts a caller's bounded timeout; #17 records the analogue.
Proposed-edit: Add "A `Retry-After` can outlast a caller's bounded timeout; AC-3.2 sets no cap → findings ledger if observed."

### C4 — The promotion residual names the wrong action for this repository
Severity: C
Location: design.md § Residuals, "Promotion"
Defect: `config/toolchain.json` `not_installed` names only `src/payload/scripts/gitlab_wrapper.py` and origin/main `scripts/toolchain_manifest.py` LAYOUT maps all of `src/payload/`, so promotion installs `scripts/gitlab_api/` and the GitLab suites without the entry script.
Proposed-edit: Append "; here the promotion names `src/payload/scripts/gitlab_api/*` and the new GitLab files of `src/payload/test/` under `not_installed`."

### C5 — The transport suite's import of `gitlab_api` is unstated
Severity: C
Location: design.md § Testing Strategy, "Transport and records"
Defect: `--import-mode=importlib` (`pyproject.toml` `addopts`) adds nothing to `sys.path`; the other two suites say how `gitlab_api` resolves, this one does not.
Proposed-edit: Append "It puts `Path(__file__).resolve().parents[1] / \"scripts\"` on `sys.path` before importing `gitlab_api`."

### D1 — requirements.md: the `Authorization: Bearer` residual is stale
Severity: D
Location: requirements.md § Residuals, second item
Proposed-edit: Replace "→ conductor to route" with "→ closed by design.md 'Redirects (AC-3.1)'; no criterion added".

### D2 — UB-1 names the wrapper's own function as a caller
Severity: D
Location: requirements.md § UB-1, row `pipeline wait`
Proposed-edit: Delete "`pipeline_wait`; " from the Callers cell.

### D3 — Test module names differ from #17's scheme
Severity: D
Location: design.md § Layout
Proposed-edit: Rename to `gitlab_wrapper_fixtures.py`, `test_gitlab_api_transport.py`, `test_gitlab_wrapper_compat.py`, `test_gitlab_api_<family>.py` (#17's pattern), or list the names in the Differences table.

NOT-CLEAN (0 A, 4 B)
