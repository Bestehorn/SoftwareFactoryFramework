# Best-practice review — issue #17 design — iteration 02 (delta)

No MCP documentation server covers GitHub or the Python standard library; sources fetched 2026-11-10: CPython 3.9
`Lib/urllib/request.py` and `Lib/http/client.py` (raw.githubusercontent.com/python/cpython/3.9), `Lib/urllib/parse.py`
(the local 3.14 stdlib, same `_splithost`/`_splittype`), [Release assets](https://docs.github.com/en/rest/releases/assets).

Fix sites of iteration 01: BP-C1 (D5 bullet, requirements residual) and BP-C2 (D3 "Failures, in `_send`") read as
proposed and match CPython 3.9 `HTTPRedirectHandler.redirect_request` / `http_error_302`. Checked, no finding:
`UPLOAD_ORIGIN` `https://uploads.github.com` (Release assets: the endpoint is on `uploads.github.com`, reached through
`upload_url`); the `_send` origin refusal before sending; the WARNING before each wait; the `.`/`..` refusal (`quote`
never encodes `.` and always encodes `%`, so a literal check catches every dot segment `expand` can emit); `origin()`
reading `Request(url).type` and `.host` (`_splittype` lower-cases the scheme, `Request._parse` unquotes the host, the
values `do_open` connects with).

### C1 — `origin()` copies a port split that raises `http.client.InvalidURL` for a `user:password@` part or any non-numeric port, and D3 converts no `InvalidURL`
Severity: C
Location: design.md § D3 "Origin (X5)", "Failures, in `_send`"
Defect: `Request(url).host` keeps the userinfo (`_splithost` matches `//([^/#?]*)`), so for
`https://user:pw@api.github.com/` the last `:` outside `[...]` leaves the port text `pw@api.github.com`, for which <!-- pragma: allowlist secret -->
`HTTPConnection._get_hostport` — the split `origin()` copies — raises `InvalidURL("nonnumeric port: …")`, an
`HTTPException` that is neither the `ValueError` nor the `URLError` D3 converts; a `link` `next`, an `upload_url` or a
redirect `Location` naming such a URL ends in a traceback, not the `GitHubAPIError` refusal that "a URL carrying
userinfo never matches the API's" and the AC-2.2/AC-2.4 other-origin examples describe.
Material-because: a risk worth one sentence — nothing is sent and the exit stays non-zero, so no criterion breaks.
Source: CPython 3.9 `Lib/http/client.py` `HTTPConnection._get_hostport`, `class InvalidURL(HTTPException)`,
`class HTTPException(Exception)`; `Lib/urllib/request.py` `Request._parse`, `HTTPRedirectHandler.http_error_302`
(`redirect_request` runs before `self.parent.open(new)`), `AbstractHTTPHandler.do_open` (`http_class(host, …)` runs
before its `try`, so an unraised `origin()` still meets `InvalidURL` there).
Proposed-edit: in "Origin (X5)" replace "so a URL carrying userinfo never matches the API's." with "so a URL carrying
userinfo never matches the API's. A port that is not an integer — which the last `:` of a `user:password@` part also
yields; an empty port is the default, as `HTTPConnection`'s — raises `GitHubAPIError` naming the URL, where
`HTTPConnection` raises `http.client.InvalidURL`, which is no `ValueError`."

### C2 — "443 when no port is given" is not the port urllib connects to for an `http` URL
Severity: C
Location: design.md § D3 "Origin (X5)"; review-latest.md X5 (the rule shared with #13)
Defect: `HTTPConnection.default_port` is 80 and only `HTTPSConnection.default_port` is 443, so `origin()` as written
makes `http://host/` and `http://host:443/` one origin although urllib connects to port 80 for the first and 443 for
the second, contradicting the paragraph's "the scheme and authority urllib's `AbstractHTTPHandler.do_open` connects
with"; X5 states the same rule for both wrappers.
Material-because: a risk worth one sentence — in this change every allowed origin is `https`, so an `http` target
never matches `API_ROOT`'s or `UPLOAD_ORIGIN`'s origin and AC-3.1's `http://` example still holds.
Source: CPython 3.9 `Lib/http/client.py` `HTTPConnection.default_port = HTTP_PORT` (80),
`HTTPSConnection.default_port = HTTPS_PORT` (443), `_get_hostport` (`port = self.default_port`).
Proposed-edit: in "Origin (X5)" replace "and uses 443 when no port is given" with "and uses the scheme's default
port when none is given (`HTTPSConnection.default_port` 443 for `https`, `HTTPConnection.default_port` 80 for
`http`)".

Verdict: CLEAN
