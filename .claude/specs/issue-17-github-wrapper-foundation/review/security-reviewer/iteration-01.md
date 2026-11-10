# Security review — issue #17 design, iteration 01

### B1 — Response-supplied `link` and `upload_url` targets receive the PAT on any https origin
Severity: B
Location: design.md § D3 Transport (`_send`, `pages`, `upload`); § Security Considerations "Where the token goes"
Defect: `_send`'s only URL guard is the `https://` prefix, so a `rel="next"` target or an `upload_url` naming any https
host is sent `Authorization: Bearer <token>` as a fresh request (the redirect handler never sees it); the fork refuses
both (`next_page_path` outside `API_BASE`, `_expand_upload_url` outside `UPLOAD_HOST_PREFIX`, both documented there as
"server-supplied and this request carries a credential").
Material-because: security — a server-supplied URL that leaves GitHub's API and upload origins carries the credential,
which AC-3.1's "so that no credential reaches a storage host" excludes and which the fork's existing controls prevent.
Proposed-edit: D3 `_send` bullet: replace "It refuses a URL not starting `https://` (the fork's `_api_request` guard)"
with "It refuses, before sending, a URL whose origin — scheme, lower-cased host, port with the scheme's default,
compared by equality as the redirect handler compares — is not `API_ROOT`'s or, for `upload`, `UPLOAD_ORIGIN`'s
(`https://uploads.github.com`): the fork's `next_page_path` and `_expand_upload_url` guards (a prefix test would admit
`https://api.github.com.evil.test`)." Add `UPLOAD_ORIGIN` to **Constants**. Security Considerations "Where the token
goes": replace "the `link` and `upload_url` targets the API returns" with "`link` targets on the `API_ROOT` origin and
`upload_url` targets on `UPLOAD_ORIGIN`; any other origin raises `GitHubAPIError` with nothing sent". Correctness
Properties AC-2.2 and AC-2.4: append one example each — a `rel="next"` / `upload_url` on another origin raises
`GitHubAPIError` and the fake host records no request to it.

### B2 — `_detect_repo` writes an origin URL's embedded credential to stderr
Severity: B
Location: design.md § D6 "Kept by name, with the fork's bodies" (`_detect_repo`), step 4; § Security Considerations
"Credential source"
Defect: The fork's `_detect_repo` raises `Could not parse GitHub owner/repo from origin URL: {url}` with the URL
verbatim, and its pattern `([^/.]+)(?:\.git)?/?$` refuses every repository name holding a `.` — measured:
`re.search` on `https://ghp_EXAMPLE@github.com/owner/socket.io.git` returns `None` — so a token embedded in such a
remote, or in any non-GitHub remote, is logged by D6 step 4.
Material-because: security — a git credential reaches the stderr that agent transcripts capture, against
`use-git-wrapper-scripts.md` "NEVER echo credential contents into chat, logs, or commit messages".
Proposed-edit: D6: replace "`_detect_repo` (the fork's missing-`origin` refusal)" with "`_detect_repo` (the fork's
parsing and missing-`origin` refusal; its unparseable-URL message names `.git/config` and the URL with any
`user:password@` part removed, never the URL verbatim — stderr only, so UB-1.1's stdout and exit code 2 are
unchanged)". Security Considerations "Credential source": append "no message carries a URL's userinfo".

### C1 — Dot segments pass through `expand`
Severity: C
Location: design.md § D4 `expand`; § Security Considerations "Paths"
Defect: `quote` never encodes `.`, so a single-segment value `.` or `..`, and any `..` segment of a `multi_segment`
value, reach the request target unchanged — measured, `quote("heads/../../../../r", safe="/")` returns it as is, so
`delete-remote-branch ../../../../r` builds `DELETE /repos/o/r/git/refs/heads/../../../../r`; urllib sends the path as
built, and whether GitHub's edge resolves dot segments is unverified (the fork's `REPO_SLUG_PATTERN` and
`ASSET_PART_PATTERN` refuse them on that ground). Not a regression: the fork interpolates `args.branch` unencoded.
Proposed-edit: D4 `expand`: append "a value that is `.` or `..`, or for a `multi_segment` name has such a segment,
raises `ValueError`". Security Considerations "Paths": append "; `.` and `..` segments refused".

### C2 — Response values placed in exception messages are logged unescaped
Severity: C
Location: design.md § D3 "Failures" (`RateLimitError` naming `x-ratelimit-resource`), `graphql` (the first error's
`message`); § Security Considerations "Untrusted output"
Defect: Only `details` passes `json.dumps`; these response-supplied strings go into the message, which D6 step 6 logs
raw, while the fork renders such values with `_render_untrusted` because a raw header value was measured carrying
`0x1b` and other C0 controls (its docstring).
Proposed-edit: D3: "each response-supplied value placed in a message (the bucket name, the GraphQL error message) is
rendered with `json.dumps`". Security Considerations "Untrusted output": replace "error `details` go to stderr through
`json.dumps`" with "error `details` and every response value inside a message go to stderr through `json.dumps`".

### C3 — The parity test's working directory is unstated
Severity: C
Location: design.md § Testing Strategy, CLI golden tests (`test/test_github_wrapper_fork_parity.py`)
Defect: The compat test names its temporary project; the parity test does not, and the fork reads
`credentials/github-pat.txt` relative to the working directory, so run from this repository's root it puts the real
PAT into `FakeGitHub`'s recorded headers and any assertion diff that prints them.
Proposed-edit: "…runs the same `CASES`, minus the delivery verbs, against the installed fork
`scripts/github_wrapper.py` in the same temporary project and fixture token as the compat test, …".

### C4 — The AC-3.1 property has no port case
Severity: C
Location: design.md § Correctness Properties AC-3.1
Defect: D3 strips on a port difference, but the examples vary host and scheme only, so a `(scheme, host)` comparison
passes every listed example.
Proposed-edit: append to AC-3.1: "; a target on another port of the API host (`https://api.github.com:8443/`)
carries none; `https://api.github.com:443/` keeps it".

NOT-CLEAN (0 A, 2 B)
