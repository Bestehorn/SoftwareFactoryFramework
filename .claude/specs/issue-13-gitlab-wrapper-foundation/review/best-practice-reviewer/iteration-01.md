# Best-practice review — iteration 01 — issue #13 design

Sources: official web documentation read 2026-11-10 (no documentation MCP server covers GitLab or the Python
standard library).

### A1 — The UB-2 oracle uses a Python 3.10-only API in a suite that ships to Python 3.9 projects
Severity: A
Location: design.md § Correctness Properties, UB-2
Defect: `sys.stdlib_module_names` is "Added in version 3.10" (https://docs.python.org/3/library/sys.html#sys.stdlib_module_names), but `test_standard_library_only` sits in `src/payload/test/test_gitlab_transport.py`. That suite ships: design § Residuals sends "the new suites" to the promotion, and `prompts/setup-claude.txt` copies `src/payload/test/*` into projects. Its floor is Python 3.9 (`pyproject.toml` `requires-python = ">=3.9"`, `tech-stack.md`).
Material-because: wrong-behaviour — on Python 3.9 the UB-2 test raises `AttributeError`, so a project on the declared floor gets a red suite from the wrapper's own proof.
Proposed-edit: replace "and modules in `sys.stdlib_module_names` (CI runs Python 3.10, https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names)" with "and the standard-library top-level names of an allow-list the test declares (`sys.stdlib_module_names` exists only from Python 3.10; the suite ships to Python 3.9 projects)".

### B1 — The GraphQL payload-error rule also fires on query results that carry an `errors` field
Severity: B
Location: design.md § Transport "GraphQL (AC-4.1–AC-4.3)"; requirements.md AC-4.3
Defect: The design raises for "any top-level `data` value that is an object whose `errors` list is non-empty", but AC-4.3 names only a mutation payload. The schema has a query root field whose result object holds `errors` as data: `Query.ciConfig` → `CiConfig.errors`, the linting errors (`docs/api-reference/gitlab/graphql/queries.md` `ciConfig`, `objects-a-c.md` `CiConfig`; deprecated in 18.1 and still in the 19.6 schema).
Material-because: wrong-behaviour — a successful query that reports content errors (a lint of an invalid CI file) raises `GitLabAPIError`, and its data cannot be reached. That contradicts AC-4.3's scope.
Proposed-edit: replace "or any top-level `data` value that is an object whose `errors` list is non-empty (a mutation payload)" with "or, when the document's operation type is `mutation`, any top-level `data` value whose `errors` list is non-empty (the mutation payload)".

### C1 — Name the no-response exception set: failures in `getresponse()` are not `URLError`
Severity: C
Location: design.md § Transport "Errors (AC-3.5)"
Defect: CPython 3.9 `AbstractHTTPHandler.do_open` wraps only `h.request(...)` in `URLError`, and `h.getresponse()` sits outside that wrap (https://github.com/python/cpython/blob/3.9/Lib/urllib/request.py). So a timeout while waiting for the response (`socket.timeout`, `TimeoutError` from 3.10), `RemoteDisconnected` and a body-read `http.client.IncompleteRead` reach the caller unwrapped, and `main` prints a traceback instead of the logged error.
Proposed-edit: replace "(`URLError`, a timeout at `REQUEST_TIMEOUT_SECONDS`)" with "(`OSError` — `URLError`, `TimeoutError`, `ConnectionError` — or `http.client.HTTPException`, caught after `HTTPError`)".

### C2 — FakeHost replaces only `HTTPSHandler`
Severity: C
Location: design.md § Testing Strategy "Transport and records"
Defect: `build_opener` keeps every default class that the given handlers do not subclass (https://docs.python.org/3/library/urllib.request.html `build_opener`). So `HTTPHandler` stays, and a redirect to an `http://` target (the downgrade case in Security Considerations) opens a real socket. Also, `HTTPErrorProcessor.http_response` reads `response.code, response.msg, response.info()`, and `urllib.response.addinfourl` has no `msg` (CPython 3.9 `urllib/request.py`, `urllib/response.py`).
Proposed-edit: after "an `HTTPSHandler` subclass whose `https_open` serves scripted `(status, headers, body)` responses" insert "(it also serves `http_open`, so a downgrade redirect stays off the network; each response carries `code`, `msg` and `info()`)".

### C3 — A 308 is followed only from Python 3.11
Severity: C
Location: design.md § Transport "Redirects (AC-3.1)"
Defect: `HTTPRedirectHandler.http_error_308` is "Added in version 3.11" (https://docs.python.org/3/library/urllib.request.html), and the 3.9 source has no `http_error_308`. On 3.9 and 3.10 (CI) a `308` reaches `http_error_default` and raises; on 3.11+ a `GET` 308 is followed. A redirect test written with 308 gives a different verdict depending on the interpreter.
Proposed-edit: append to the paragraph: "A `308` is followed only on Python 3.11+ (`http_error_308`); the redirect tests use `301` and `302`."

### C4 — The AC-2.3 property oracle drops blank values
Severity: C
Location: design.md § Correctness Properties, AC-2.3
Defect: `urllib.parse.parse_qsl` ignores blank values unless `keep_blank_values=True` (https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qsl). So "for any list of strings" fails on `""`, and a lone surrogate makes `quote` raise.
Proposed-edit: replace "`parse_qsl` of the encoded query" with "`parse_qsl(encoded, keep_blank_values=True)`, over non-surrogate text as in AC-2.2,".

### C5 — How the origin is compared
Severity: C
Location: design.md § Transport "URLs"
Defect: An origin is the scheme, the lower-cased host and the port, with the scheme's default port when none is given (RFC 6454 §4, https://www.rfc-editor.org/rfc/rfc6454#section-4). If raw `netloc` text is compared, a `Link` or redirect URL that differs only in host case or in an explicit `:443` loses the credential, and the next page answers `401`.
Proposed-edit: replace "The configured origin is the scheme, host and port of that base." with "The configured origin is the scheme, host and port of that base, compared as `urlsplit` `scheme`, `hostname` and `port` (443 when absent)."

### C6 — Hypothesis enters a shipped suite (for the standards lane)
Severity: C
Location: design.md § Testing Strategy "Transport and records"
Defect: No module under `src/` imports `hypothesis` today. The design adds it to `src/payload/test/test_gitlab_transport.py`, a suite that is copied into projects, and `dependencies.md` rule 1 requires a third-party import under `src/payload/` to be flagged as a dependency change.
Proposed-edit: append to the bullet: "Hypothesis becomes a test dependency of a shipped suite (`dependencies.md`), flagged for the promotion."

Verdict: NOT-CLEAN (1 A, 1 B)
