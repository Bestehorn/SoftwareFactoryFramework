# Security review — issue #17 design, iteration 02 (delta)

Iteration-01 findings, verified at their fix sites:

- B1 closed: D3 `_send` refuses, before sending, any origin other than `allowed_origin` (`API_ROOT`'s, `UPLOAD_ORIGIN`
  for `upload`); `UPLOAD_ORIGIN` is in Constants; Security Considerations "Where the token goes" is restated; AC-2.2
  and AC-2.4 carry the other-origin examples.
- The author's correction stands. The fork's `next_page_path` tests `f"{API_BASE}{PATH_ROOT}"` and `UPLOAD_HOST_PREFIX`
  is `"https://uploads.github.com/"`. Both end in `/`, and urllib's `_splithost` ends the authority at the first `/`.
  The fork's own `PATH_ROOT` comment limits the `api.github.com.evil.test` admission to the slash-less
  `startswith(API_BASE)`. My iteration-01 parenthetical was wrong about the fork. B1's defect, the design's
  `https://`-only guard, did not rest on it.
- X5 has no bypass that sends the credential to another host. `origin` reads the same `Request.host` that `do_open`
  hands to `http.client`, and its port split mirrors `HTTPConnection._get_hostport` (the Python 3.9 source is
  identical). Measured on the venv's Python 3.14.2:
  - `https://ghp_T@api.github.com/` gives host `ghp_T@api.github.com`, never equal to the API's.
  - `https://api.github.com@evil.test/` gives `api.github.com@evil.test`.
  - `https://api.github%2Ecom/` gives `api.github.com`; `Request` unquotes it, and urllib connects there.
  - `HTTPS://` gives `https`.
  - `:` and `:0443` both connect to port 443, so either reading of them is equal or stricter.
- B2 closed: D6 `_detect_repo` strips the userinfo, and "Credential source" says no message carries a URL's userinfo.
  See C3 on its wording.
- Applied: C1 (a dot segment raises `GitHubAPIError`; AC-1.1 example; R test), C2 (response values in messages go
  through `json.dumps`), C3 (the parity test runs in the temporary project with the fixture token), C4 (`:8443` and
  `:443` cases in AC-3.1).

### C1 — X5 gives an `http` URL without a port the port 443
Severity: C
Location: design.md § D3 Origin (X5)
Defect: "uses 443 when no port is given" holds for `https` only. `http.client.HTTPConnection.default_port` is 80, so
under X5 `http://h/` and `http://h:443/` are one origin while urllib connects to ports 80 and 443. This is not
exploitable in this change: `_send` admits only `https` origins, and a hop to `http` has already dropped the credential
(AC-3.1's same-host `http://` example). X5 is shared with #13.
Proposed-edit: replace "and uses 443 when no port is given" with "and uses the scheme's default port when none is given
(443 for `https`, 80 for `http`: `http.client`'s `default_port`)".

### C2 — The origin of the request that received the redirect must come from its URL, not its `host`
Severity: C
Location: design.md § D3 Origin, Redirects
Defect: `origin` reads a `Request`'s `type` and `host`, and Redirects compares against "the request that received the
redirect" without saying which URL stands for that request. With a proxy configured, `build_opener`'s `ProxyHandler`
calls `Request.set_proxy`, which rewrites that request's `host` (measured: `host 'proxy.corp:8080'`, `full_url
'https://api.github.com/x'`). Taking its attributes would strip `Authorization` on every same-origin hop and keep it on
a hop to the proxy's own address.
Proposed-edit: Redirects: replace "differs from `origin` of the request that received the redirect" with "differs from
`origin(req.full_url)` of the request that received the redirect (never its `host`, which `ProxyHandler` rewrites to
the proxy's)".

### C3 — D6 strips `user:password@`, narrower than the measured case
Severity: C
Location: design.md § D6 `_detect_repo`; § Correctness Properties UB-1.1
Defect: The remote iteration 01 measured was `https://ghp_EXAMPLE@github.com/owner/socket.io.git`, a bare token with no
`:`. Read literally, a strip of "any `user:password@` part" (my iteration-01 wording) leaves that token in the message.
The intended rule is "Credential source"'s "no message carries a URL's userinfo", and no example tests it.
Proposed-edit: D6: replace "the URL with any `user:password@` part removed" with "the URL with its userinfo (everything
up to the last `@` before the host, a bare token included) removed". UB-1.1: append "In C only (the fork prints the
URL verbatim): an unparseable `origin` `https://ghp_T@github.com/o/socket.io.git` exits 2 with empty stdout, and its
stderr does not hold `ghp_T`."

### D1 — The rate-limit WARNING is a log line, not a message
Severity: D
Location: design.md § D3 "Failures, in `_send`"
Defect: The WARNING added for DO-C2 names the bucket, a response-supplied value, but the `json.dumps` sentence says
"placed in a message", which reads as the exception message only.
Proposed-edit: replace "placed in a message" with "placed in a message or a log line".

CLEAN
