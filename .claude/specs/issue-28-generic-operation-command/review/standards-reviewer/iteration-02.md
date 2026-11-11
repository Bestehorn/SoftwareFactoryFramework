# Standards review — design iteration 02, delta (issue #28)

## Fix sites of iteration 01

- S-A1 — APPLIED. D2 "Registry additions" `query_name`; D4 "Documented names" (each query name compared through
  `registry.query_name(name=...)`); D8 `registry.py` row. No Parameter row of `docs/api-reference/github/rest/*.md`
  has a query name ending in `[]`, so the stripped comparison matches every documented name.
- S-B1 — APPLIED. H is named in Testing Strategy, Correctness Properties AC-1.3, the mapping list and the AC-1.3 row,
  D8, and Security "Dependencies". `hypothesis` is already in `pyproject.toml` `[project.optional-dependencies] dev`,
  so there is no dependency change (`dependencies.md`). The sketch's keywords match the installed
  `hypothesis/strategies/_internal/core.py` (`recursive(base, extend, *, …)`, `lists(elements, *, …)`,
  `dictionaries(keys, values, *, …)`). See S2-C1.
- S-C1 — APPLIED. D8 "A slice" lead.
- S-C2 — APPLIED. D4 "How a refusal is written": `EXIT_REFUSED` lives in `_common.py` (review-latest ST-C2) and the
  catch is in `cmd_call` (DL-004).
- S-C3 — APPLIED. AC-4.1, its mapping row, D8's C row, Testing Strategy "Docstring test", UB-1.1 "Verification".
- S-D1 — APPLIED. D4 "Documented names".

## New in the delta

### S2-C1 — "as V does" leaves open how H requests the path fixture
Severity: C
Location: design.md § Testing Strategy "Unit tests" (H)
Defect: V applies `scripts_on_path`, a function-scoped `monkeypatch` fixture, through
`@pytest.mark.usefixtures("scripts_on_path")`. The installed `_hypothesis_pytestplugin.py` checks only the fixtures in
a `@given` test's signature and calls `fail_health_check(..., HealthCheck.function_scoped_fixture)` for a
function-scoped one. So H fails if it takes `scripts_on_path` as a parameter, and passes only through `usefixtures`.
Proposed-edit: replace "which puts `src/payload/scripts` on `sys.path` as V does" with "which puts
`src/payload/scripts` on `sys.path` as V does, through `@pytest.mark.usefixtures(\"scripts_on_path\")` (a `@given`
test that takes a function-scoped fixture as a parameter fails Hypothesis's `function_scoped_fixture` health check)".

### S2-C2 — Two lower-layer changes are tested only through `call`'s suite
Severity: C
Location: design.md § Testing Strategy "Unit tests"; § D8 "This change"
Defect: Two lower-layer changes are proven only by K's AC-1.2 rows: `registry.query_name`, with `_check_names`
comparing through it (X1), and the `accept` of `Transport.pages` (X2). testing.md item 3 has a test module cover its
source module, and the design already places `send` and `path_parameters` in R. D8 has no row for
`src/payload/test/test_github_api_transport.py`, the module holding `test_link_pages_are_followed_as_given`.
Proposed-edit: in Testing Strategy replace "The registry's `send` and `path_parameters` are tested in
`test_github_api_registry.py` (R), using its synthetic family." with "The registry's `send`, `path_parameters` and
`query_name` are tested in `test_github_api_registry.py` (R), using its synthetic family, with `send` and `pages`
accepting a query name ending in `[]`. `Transport.pages` sending its `accept` on every page is tested in
`src/payload/test/test_github_api_transport.py`." In D8, make the R row "adds `test_send_returns_the_response_of_the_record`
and cases for `path_parameters` and a `[]` query name", and add the row
"`src/payload/test/test_github_api_transport.py` | adds a case: `pages(accept=...)` sends it on every page".

### S2-D1 — A positional call in the property's oracle
Severity: D
Location: design.md § Correctness Properties AC-1.3
Defect: `json.dumps(value)` is written positionally (coding-standards.md item 4), where `_common.print_json` writes
`json.dumps(obj=value, indent=JSON_INDENT)`.
Proposed-edit: `body_of(members=[json_member(text=f"{name}={json.dumps(obj=value)}")]) == {name: value}`.

Verdict: CLEAN
