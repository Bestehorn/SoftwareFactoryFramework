# Security review — issue #13 design, iteration 01 (lane security-reviewer)

Sound as written: `add_unredirected_header` keeps the token out of urllib's redirect copy (`redirect_request` copies
only `req.headers`), non-`GET`/`HEAD` redirects are refused, the job token is refused before any GraphQL request, and
credentials come from `config/gitlab.json` only. Probes ran on the venv's Python 3.14.2.

### C1 — The origin comparison is unpinned, and its test passes a leaking implementation
Severity: C
Location: design.md § Transport "Credentials (AC-2.1)", "Redirects (AC-3.1)"; § Correctness Properties AC-3.1
Defect: "has the configured origin" does not say how origins are compared. The AC-3.1 oracle (one `302` to another
host) also passes `url.startswith("https://<host>")`, which sends the credential to `https://<host>.evil.example/`, and
a `urlsplit` check, which disagrees with the host urllib connects to. The `https`→`http` claim in Security
Considerations has no test.
Evidence: probe — for `https://gitlab.example@evil.example/x`, `Request(...).host` is `gitlab.example@evil.example` and
`urlsplit(...).hostname` is `evil.example`; for `https://evil.example\@gitlab.example/x`, `Request(...).host` is
`evil.example\@gitlab.example` and `urlsplit(...).hostname` is `gitlab.example`.
Proposed-edit: after "The configured origin is the scheme, host and port of that base." add "A URL has it when
`urllib.request.Request(url)` gives `type` `https` and a `host` equal, case-insensitively, to `hostname` (the parse urllib
connects by), never a string prefix and never a second parser." In Correctness Properties AC-3.1, replace "a `302` to
another host" with "a `302` to each of `https://<host>.evil.example/`, `https://<host>@evil.example/`, `http://<host>/`,
`https://<host>:8443/`, for each token type".

### C2 — A redirect chain that has left the origin gets the credential back when it returns
Severity: C
Location: design.md § Transport "Redirects (AC-3.1)"
Defect: the re-add checks only the target. A foreign hop, such as the object-storage or CDN host a download redirects
to (`conventions.md` "Redirects to object storage and CDNs"), can therefore send the client back to any
configured-origin path it chooses. The client then sends a credentialed `GET` there, and the subcommand prints the
response as the resource it asked for.
Proposed-edit: replace "re-adds the configured credential only when the target has the configured origin" with
"re-adds the configured credential only when both the redirected request (`req.full_url`) and the target have the
configured origin".

### C3 — A `Link` next URL is fetched on any scheme and host
Severity: C
Location: design.md § Transport "Pagination (AC-2.5, AC-2.6)"; § Security Considerations "Credential reaches the
configured origin only"
Defect: redirects are limited to `http`, `https`, `ftp` and relative URLs (`HTTPRedirectHandler.http_error_302`).
A next URL is not limited: it is opened directly by an opener that holds `FileHandler`, `FTPHandler` and `DataHandler`
(probe: the `build_opener()` handler list). So `Link: <file:///…>; rel="next"` puts a local file into the command's
output, and a next URL on a foreign origin is fetched without the credential, its items returned as the list's next
page.
Proposed-edit: replace "A next URL is sent through `_authorize`, so one on another origin carries no credential." with
"A next URL without the configured origin raises `GitLabAPIError` naming it and is not fetched; one with it goes
through `_authorize`." (AC-2.6's "unchanged" is kept for every URL that is followed.)

### C4 — A token containing CR or LF is printed in full in a traceback
Severity: C
Location: design.md § Entry script `_load_config`; § Transport "Credentials" ("the token never enters … an exception
message")
Defect: `http.client` `putheader` raises `ValueError('Invalid header value %r' % …)` with the whole header value.
urllib's `do_open` wraps only `OSError`, and `main` catches only `GitLabAPIError`. A `token` ending in `\n`, as in a
config written from a file read without stripping, therefore reaches standard error verbatim: the agent transcript or
a job log. The skeleton has the same path; the design's claim that the token never enters an exception message makes
it this change's.
Evidence: probe — `putheader('Private-token', 'glpat-EXAMPLEVALUE\n')` raised
`ValueError: Invalid header value b'glpat-EXAMPLEVALUE\n'`.
Proposed-edit: in `_load_config`'s checks, after "a `PASTE_` placeholder in `hostname`, `project_id` or `token`", add
"; a `token` containing whitespace or a control character → `GitLabAPIError` naming the key, never the value".

### C5 — `.`, `..` and the empty string are not one path segment
Severity: C
Location: design.md § Transport "Path parameters (AC-2.2)"; § Security Considerations "Input"; § Correctness
Properties AC-2.2
Defect: `quote(v, safe="")` returns `..`, `.` and the empty string unchanged (probe). So `delete-branch ..` sends
`…/repository/branches/..`, which RFC 3986 §5.2.4 dot-segment removal resolves to its parent. The WHATWG URL Standard
also counts `%2e%2e` as `..` (https://url.spec.whatwg.org/, "double-dot URL path segment"), so encoding the dots, which
`conventions.md` "URL-encoding path parameters" allows, does not close this. The "every value is one segment" claim
does not hold for these values, and `..` satisfies the AC-2.2 property. Graded C because no GitLab hop is shown to
resolve dot segments.
Proposed-edit: after "A missing placeholder value raises `GitLabAPIError`." add "so does an empty value, `.` or `..`";
in Correctness Properties AC-2.2, replace "for any non-surrogate text `v`" with "for any non-surrogate text `v` other
than `.` and `..`, which are examples that raise".

### C6 — The multipart boundary source and part-header escaping are not stated
Severity: C
Location: design.md § Transport "Multipart (AC-2.4)"
Defect: "a random boundary" names no source, and the file's name goes into `Content-Disposition` unescaped. A
`Path.name` containing `"` (legal on POSIX) then adds a second `name=` to the part. This is the multipart tampering of
CVE-2024-22049 (https://github.com/advisories/GHSA-5pq7-52mg-hr42). Graded C because part 1 has no FILE caller.
Proposed-edit: replace "with a random boundary" with "with a boundary from `secrets.token_hex(16)`", and after "with the
file's name" add "(it and each field name with `"`, CR and LF written as `%22`, `%0D`, `%0A`, the HTML
`multipart/form-data` encoding algorithm, https://html.spec.whatwg.org/#multipart-form-data)".

CLEAN
