# Test architect — design review, iteration 01

### A1 — UB-2.2's import oracle admits every installed package
Severity: A
Location: design.md § Correctness Properties, UB-2.2
Defect: site-packages lies under `stdlib`/`platstdlib` (project venv: `platstdlib` is `venv\Lib`, `yaml` resolves to `venv\Lib\site-packages\yaml\__init__.py`), so "resolves under `stdlib` or `platstdlib`" passes a third-party import, and it fails `os`, `io`, `codecs`, `stat`, whose `find_spec` origin is `frozen` on the venv's Python 3.14.2.
Material-because: UB-2.2 — a PyYAML import in `github_api/` passes the test, so the test cannot fail for the defect it exists to catch.
Proposed-edit: replace "a built-in, or resolves with `importlib.util.find_spec` under `sysconfig.get_paths()` `stdlib` or `platstdlib`" with "or has a top-level name in `sys.stdlib_module_names` (CI runs Python 3.10, `.github/workflows/ci.yml`)".

### A2 — The parity test runs a `--token-stdin` case the fork accepts
Severity: A
Location: design.md § Testing Strategy (CLI golden tests); § Correctness Properties, UB-1.1
Defect: P runs every non-delivery case against the fork, including the usage case "`--token-stdin` included", but the fork registers `--token-stdin` on `list-issues` and `create-issue` (`_add_stdin_credential_option`) and `main` then calls `_load_stdin_token`, whose `sys.stdin.buffer.read()` raises `OSError` under pytest capture (`_pytest/capture.py` `DontReadFromInput.read`), which `main` does not catch.
Material-because: UB-1.1 — P as specified cannot pass, and that row's golden value is not the fork's output (UB-1.1 drops the option deliberately).
Proposed-edit: Testing Strategy: "minus the delivery verbs" → "minus the delivery verbs and the `--token-stdin` cases (a deliberate deviation, UB-1.1)"; UB-1.1: "(`--token-stdin` included)" → "(`list-issues --token-stdin` and `create-issue --token-stdin` in C only: exit 2, empty stdout, no request recorded)".

### B1 — "Accept the arguments" is proven only for the argv `CASES` holds
Severity: B
Location: design.md § Correctness Properties, UB-1.1
Defect: one golden argv per subcommand leaves the fork's other options untested (`get-logs --failed-only`, `list-issues --assignee`), and no case uses the abbreviation UB-1.1 names, which a caller passes (`clients/kiro/agents/issue-intake-agent.json`: `list-issues … --label`); a parser missing an option or built with `allow_abbrev=False` passes.
Material-because: UB-1.1 (the fork's arguments, prefix abbreviations included).
Proposed-edit: append to UB-1.1: "Parser parity (P): for each caller-used subcommand and nested spelling, the fork's and the product's subparsers have equal option strings, and each action's `dest`, `nargs`, `const`, `default`, `choices`, `required` and mutually exclusive group are equal; `CASES` holds `list-issues --label <name>`."

### B2 — The fake host cannot serve `start-issue` claiming an unclaimed issue
Severity: B
Location: design.md § Testing Strategy (Fake host); § Correctness Properties, UB-1.1
Defect: the fork's `cmd_start_issue` GETs the issue, POSTs label and assignee, then GETs the same URL and requires both; static routes keyed on method, path and query answer both GETs alike, so the exit-0 claim (both spellings) cannot be built, and a product that skips the two writes matches every case that can.
Material-because: UB-1.1 — exit 0 of `start-issue`/`issue start` on an open unclaimed issue, the path callers use, has no case.
Proposed-edit: after "static routes match method, URL path and decoded query" add "; a route may hold responses served in order, the last repeating; each case also holds its expected non-GET requests (method, path, decoded query, JSON body), compared in C and P"; in UB-1.1 add "`start-issue` and `issue start` on an open unclaimed issue (exit 0)".

### B3 — `retry-after` precedence over `x-ratelimit-reset` has no case
Severity: B
Location: design.md § Correctness Properties, AC-3.2
Defect: no example carries both headers, so a transport that waits until `x-ratelimit-reset` whenever it is sent passes.
Material-because: AC-3.2 ("the `retry-after` seconds when present, else until `x-ratelimit-reset`").
Proposed-edit: add "a `403` with `retry-after`, `x-ratelimit-remaining: 0` and a later `x-ratelimit-reset` sleeps the `retry-after` seconds".

### B4 — AC-2.1's example skips `Transport.download`
Severity: B
Location: design.md § Correctness Properties, AC-2.1
Defect: `download` is a REST `GET` (`actions/download-workflow-run-logs`) that passes its own `rest` flag to `_send`, yet the example records only a single call, Link pages and an upload, and the `get-logs` golden case compares stdout only.
Material-because: AC-2.1 ("on every REST request").
Proposed-edit: "a single call, each Link page and an upload" → "a single call, each Link page, an upload and a `download`".

### B5 — AC-5.1's count shares the parser's predicate
Severity: B
Location: design.md § Correctness Properties, AC-5.1
Defect: "one ID per index row whose first cell is an HTTP method" counts with `index_rows`' own predicate, so a method set missing `PATCH` drops those rows from both sides and passes; `graphql_only` is checked for one included row, so reading the header cell or the **In both** table passes.
Material-because: AC-5.1 ("every operation ID", "every capability of the" table).
Proposed-edit: "`index_rows` returns distinct IDs, as many as the number in the index heading `every operation (N)`, including `issues/get`; `graphql_only` includes "Repository discussions" and "Branch protection with wildcard patterns" and excludes "Capability" and every first cell of the **In both** table".

### B6 — AC-5.2's example has no capability gap
Severity: B
Location: design.md § Correctness Properties, AC-5.2
Defect: the synthetic example holds only an ID gap; a `coverage_gaps` that ignores `capabilities` passes it, and AC-5.3's test passes too while every capability is pending.
Material-because: AC-5.2 ("an operation ID or a capability").
Proposed-edit: "an ID neither covered nor pending is returned by name" → "an ID and a capability, each neither covered nor pending, are returned by name, and a covered and a pending item of each kind are not".

### C1 — UB-1.3 oracle and the path separator
Severity: C — the refusal formats the `Path` `CREDENTIALS_FILE` (`credentials\github-pat.txt` on Windows); assert on `str(Path("credentials") / "github-pat.txt")`.

### C2 — What the fake records
Severity: C — record the headers `AbstractHTTPHandler.do_open` sends (`unredirected_hdrs` merged with `headers`), compared case-insensitively (`add_header` stores `key.capitalize()`).

### C3 — Driving the fork
Severity: C — the fork's `main()` takes no `argv` (`_build_parser().parse_args()`); state that P sets `sys.argv`.

### C4 — AC-2.2 end of list with a header present
Severity: C — give the last page of the `prev`/`first`/`last` row a `link` without `next`, so "until a page carries none" is exercised with the header sent.

## Coverage

Tests are the design's § Acceptance Criteria Mapping rows (T, V, C, P as defined there).

| Criterion | Test | Status |
|---|---|---|
| AC-1.1 | inspection D1; T | COVERED |
| AC-1.2 | inspection D2; V | COVERED |
| AC-1.3 | V | COVERED |
| AC-2.1 | T | GAP (B4) |
| AC-2.2 | T | COVERED |
| AC-2.3 | T | COVERED |
| AC-2.4 | T | COVERED |
| AC-3.1 | T | COVERED |
| AC-3.2 | T | GAP (B3) |
| AC-3.3 | T | COVERED |
| AC-3.4 | T | COVERED |
| AC-4.1 | T | COVERED |
| AC-4.2 | T | COVERED |
| AC-4.3 | T | COVERED |
| AC-5.1 | V | GAP (B5) |
| AC-5.2 | V | GAP (B6) |
| AC-5.3 | V | COVERED |
| UB-1.1 | C, P | GAP (A2, B1, B2) |
| UB-1.2 | `test_wrapper_delivery.py`; C | COVERED |
| UB-1.3 | C | COVERED |
| UB-2.1 | C | COVERED |
| UB-2.2 | C | GAP (A1) |
| UB-3.1 | `test_wrapper_delivery.py` in CI `tests`; PR diff | COVERED |
| UB-3.2 | C | COVERED |

Verdict: NOT-CLEAN (2 A, 6 B) — NOT-TEST-READY (18 COVERED, 6 GAP)
