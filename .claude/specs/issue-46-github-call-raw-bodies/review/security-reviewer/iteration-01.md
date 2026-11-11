# Security review — issue #46 design, iteration 01

Lane: security-reviewer. Subject: `design.md` against `requirements.md` (frozen) and `decisions/decision-log.md`.

## Findings

### C1 — The credential-file sentence understates the upload case
Severity: C
Location: design.md § Security Considerations, "Input"
Defect: "A caller who names `credentials/github-pat.txt` sends the token to GitHub as a body" leaves out two cases. On `repos/upload-release-asset` the token is published as a release asset, readable by anyone who can read the release. On `markdown/render-raw` the rendered token comes back on standard output.
Material-because: a clarification only. The exposure is the caller's own choice, and `--body-file` on `comment-issue` publishes it as a comment in the same way.
Proposed-edit: replace the bullet with "A caller who names `credentials/github-pat.txt` sends the token to GitHub as a body: the upload publishes it as a release asset, and `render-raw` prints it back on standard output. That is the same exposure as `--body-file` on `comment-issue`, which publishes it as a comment (Residuals)."

### C2 — `request_raw`'s URL does not name the root-relative path check
Severity: C
Location: design.md § D2, `Transport.request_raw`, "The URL is `root` + `path` + the urlencoded query"
Defect: the bullet does not say the URL is built by `_api_url`. D7 gives `_api_url` a `root` parameter, but D2 never ties the two together, so the text alone does not apply `_api_url`'s refusal of a path that is not root-relative to raw requests. If the URL were concatenated directly, a path starting `.evil`, `@evil` or `:8443` would move the authority. `_send`'s `origin(url) != origin(allowed_origin)` check still refuses all three, so this is defence in depth, not an exploitable gap. Record paths are code constants, and `registry.expand` encodes every value.
Material-because: a clarification of which check applies.
Proposed-edit: replace that bullet with "The URL is `_api_url(root=root, path=path, query=query)`, so a path that is not root-relative is refused as it is for `request`."

### C3 — The raw body is read whole, at parse time, even when the call is then refused
Severity: C
Location: design.md § D1, `read_input`; § Security Considerations, "Input"
Defect: `Path(text).read_bytes()` and `sys.stdin.buffer.read()` run as the argparse `type`, so the whole body is in memory before `cmd_call` steps 1 and 4 can refuse it. A refused `--input -` with `-f` has already drained standard input. Nothing read is sent or logged, and AC-1.3 holds. `conventions.md` "Uploads and binary request bodies" allows assets up to its documented per-file limit, and urllib needs a bytes `data` to set `Content-Length`.
Material-because: a clarification of an accepted resource cost to the local caller. No trust boundary is involved.
Proposed-edit: append to Security Considerations "Input": "The body is held in memory whole, read when the arguments are parsed, so a call that steps 1 or 4 refuse has already read all of it; none of it is sent."

## Reviewed with no defect

- Where `Authorization` goes. `_build_request` adds it with `add_header`, and `_send` refuses any URL off `allowed_origin`. `request_raw` passes `allowed_origin=root` with `root` in `REST_ROOTS`, and only a record with a `content_type` reaches it. `origin` is a record field, never a call option (D2 alternatives), so the upload origin receives the token only on `repos/upload-release-asset` (AC-2.2). The upload `POST` makes no other request. If it is answered 301/302/303, urllib re-sends it as a `GET`, and the existing strip removes the credential when the target is on another origin.
- The `307` branch. urllib's `redirect_request` raises for every redirect of `PATCH`/`DELETE` (CPython source, checked under 3.14.2), so the request that receives the `307` is always the first one `_send` built, already on `allowed_origin`. The branch compares `origin(newurl)` with `origin(req.full_url)`: scheme, lower-cased host and defaulted port, parsed as urllib connects. An `http` downgrade, another port, a host suffix, userinfo, the upload origin, a trailing dot or a percent-encoded host all compare unequal, so the default raises and nothing is sent. `ResentRequest` stops a second re-send. `dict(req.headers)` carries `Content-type` and `Authorization`, and urllib recomputes `Host` and `Content-length` from the unredirected headers. A rate-limit retry rebuilds the request at the original URL. UB-2.2 holds: a cross-origin `307` sends no further request at all.
- `--input` reads only the named path or standard input. The caller runs at its own privilege, so there is no traversal boundary. It is not a credential source (UB-2.1), and no option string contains `token`.
- Refusal ordering. An `OSError` becomes `ArgumentTypeError` in `_parse`, before `_load_token` in `main`. Steps 1 and 4 run after the credential is loaded but before any request, as #28 D4's refusals do. Nothing is sent and the token is not logged.
- Logging. No new log line names the body. Refusals name options and a declared operation ID, argparse's error names the path through `json.dumps`, and failures render URLs through `render_url`.
- Dependencies. None new in shipped code (UB-3.1), and Hypothesis stays in `test/`.

## Residuals

- A guard that refuses an `--input` path resolving to `credentials/github-pat.txt` would close C1's exposure for `call`. It is a new mechanism the acceptance criteria do not call for, so it goes to the findings ledger, not into this change.

Verdict: CLEAN
