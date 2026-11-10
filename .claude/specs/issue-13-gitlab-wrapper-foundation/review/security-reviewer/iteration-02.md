# Security review — issue #13 design, iteration 02 (delta, lane security-reviewer)

Sound as written: the `add_header` + `remove_header` mechanism (D4 "Redirects") holds. I tested it with a probe on the
venv's Python 3.14.2: the design's handler, a fake `https_open`/`http_open`, and `remove_header` given `Private-token`,
`Job-token` and `Authorization`. For each token type, no credential header reached `cdn.example` on a
host → `cdn.example` → host chain, and none came back on the return hop. A same-origin `301` to
`https://GITLAB.EXAMPLE:443/` kept `Private-token`. All four AC-3.1 hostile targets got no credential. Through
`ProxyHandler({"https": "http://proxy.example:3128"})` the hop's `req.host` was `proxy.example:3128`, while
`origin(req.full_url)` was `('https', 'gitlab.example', 443)` and the same-origin `301` kept the credential. So
`req.full_url` is the right input and `req.host` is not. In CPython 3.9 `Lib/urllib/request.py`:
`redirect_request` copies only `req.headers`; `add_header` stores `key.capitalize()`; `remove_header` is
`self.headers.pop(header_name, None)` plus the same pop on `unredirected_hdrs`; `set_proxy` rewrites `host`.

Iteration-01 fix sites, all present:
- C1: D4 "URLs and origin" and the four AC-3.1 targets.
- C2: D4 "Redirects" ("stays absent on every later hop") and the AC-3.1 return hop.
- C3: `_send` refuses another origin; AC-2.6 refusal example.
- C4: D7 `_load_config`; UB-2 trailing-newline example.
- C5: D5 `expand`; AC-2.2 property and examples.
- C6: D4 "Multipart"; AC-2.4 `%22` example.

X5's "443 when absent" for `http` puts no credential at risk: `http://<host>/` differs by scheme, and the probe
dropped the credential.

### C7 — `CREDENTIAL_HEADERS` is spelled in a form `remove_header` does not match
Severity: C
Location: design.md § D4 "Constants", "Redirects (AC-3.1)"; § Correctness Properties AC-3.1
Defect: the constant holds `PRIVATE-TOKEN` and `JOB-TOKEN`. `remove_header` pops the exact key, and `Request` stores
`Private-token` and `Job-token`. So `for name in CREDENTIAL_HEADERS: new.remove_header(name)` removes only
`Authorization` and forwards the private and job tokens on every cross-origin hop. The design avoids this only by
naming the capitalised spelling in a parenthesis. The AC-3.1 oracle ("carries none of the three credential headers")
does not say whether header names are compared with or without case. A check that uses the constant's spelling as a
key of the recorded headers, which are stored as `Private-token`, is therefore always true and passes the leaking
implementation for two of the three token types.
Evidence: same probe with `remove_header` given `PRIVATE-TOKEN`, `JOB-TOKEN`, `Authorization`. For `private` it sent
`Private-token` to `https://cdn.example/obj` and again to `https://gitlab.example/api/v4/back`; `job` behaved the same
with `Job-token`; `bearer` sent nothing past the first hop. With the capitalised names, no token type sent a
credential past the first hop.
Proposed-edit: in D4 "Constants", replace "`CREDENTIAL_HEADERS` (`PRIVATE-TOKEN`, `JOB-TOKEN`, `Authorization`)" with
"`CREDENTIAL_HEADERS` (`Private-token`, `Job-token`, `Authorization`: the spelling `Request.add_header` stores and
`Request.remove_header` matches exactly)". In D4 "Redirects", replace "(both header maps; by the capitalised names
`Request` stores: `Private-token`, `Job-token`, `Authorization`)" with "(both header maps)". In Correctness
Properties AC-3.1, after "carries none of the three credential headers" add "(names compared case-insensitively)".

CLEAN
