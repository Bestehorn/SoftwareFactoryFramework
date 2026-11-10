# Best-practice review — issue #17 design — iteration 03 (delta)

No MCP documentation server covers CPython or GitHub; fetched 2026-11-10: CPython 3.9 `Lib/http/client.py` and
`Lib/urllib/request.py` (raw.githubusercontent.com/python/cpython/3.9), the local 3.14 stdlib,
[Py_Main](https://docs.python.org/3.9/c-api/veryhigh.html),
[repository redirects](https://gist.github.com/jasonrudolph/56388a4ff51b4f721cac).

Checked, no finding: the scheme's default port (`HTTPConnection.default_port` 80, `HTTPSConnection` 443); the
non-integer port and the empty port (`_get_hostport`: `int(host[i+1:])`, `""` gives `default_port`, else
`InvalidURL`); `origin(req.full_url)` (`set_proxy` rewrites `host`, never `_full_url`); D5's first bullet
(`redirect_request` follows `307` only for `GET`/`HEAD`, a `POST` only on `301`/`302`/`303`; GitHub answers a
non-GET on a renamed repository with `307`); `get-logs` without the credential on both wrappers.

### C1 — the redirect path still meets an `InvalidURL` that D3 does not convert
Severity: C
Location: design.md § D3 "Origin (X5)", "Failures, in `_send`"
Defect: `http_error_302` percent-encodes a space in `Location` and `Request._parse` unquotes the host, so a target
`https://a%20b.example/` passes `origin()` as another origin and `parent.open(new)` reaches
`HTTPConnection.__init__`'s `_validate_host`, which raises `http.client.InvalidURL` for `[\x00-\x20\x7f]` before
`do_open`'s `try` — neither a `URLError` nor a `ValueError`, so a traceback.
Material-because: a risk worth one sentence — no connection is made, the credential is already removed, the exit
is non-zero.
Source: CPython 3.9 `HTTPRedirectHandler.http_error_302` (`quote(..., safe=string.punctuation)`), `Request._parse`
(`unquote(self.host)`), `HTTPConnection.__init__` (`self._validate_host(self.host)`), `AbstractHTTPHandler.do_open`.
Proposed-edit: in "Failures, in `_send`" replace "and a `ValueError` raised while urllib resolves a redirect's
`Location`," with "and a `ValueError` or an `http.client.InvalidURL` raised while urllib resolves or opens a
redirect's `Location`,".

### C2 — "none of UB-1.1's listed exit codes" is not the exit status of an uncaught exception
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged", closing paragraph
Defect: the fork's `main` catches only `GitHubAPIError`, so `HTTPConnection._validate_path`'s `InvalidURL` (a space
matches `[\x00-\x20\x7f]`) leaves `sys.exit(main())` and the interpreter exits 1 — a listed code, as the list's
heading "Visible only where the fork exited 1" says.
Material-because: a risk worth one sentence — no golden case builds the state.
Source: Python 3.9 C API `Py_Main` ("1 if the interpreter exits due to an exception"); CPython 3.9
`HTTPConnection._validate_path`; `scripts/github_wrapper.py` `main`.
Proposed-edit: replace "The unencoded-value case is an uncaught crash on the fork, none of UB-1.1's listed exit
codes;" with "The unencoded-value case is an uncaught `http.client.InvalidURL` on the fork — exit 1 with a
traceback, not the `GitHubAPIError` that UB-1.1's exit 1 names;".

Verdict: CLEAN
