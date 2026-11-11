# Best-practice review — design iteration 01 (issue #46)

No MCP documentation server is available in this session, and the project's servers (AWS, IaC/CDK, Strands,
AgentCore) cover none of these technologies; the official documentation below was fetched on 2026-11-11.

### BP-C1 — `read_input` reads the file inside argparse's `type`, which the argparse docs advise against
Severity: C
Location: design.md § D1 — The raw body input, the `--input FILE` bullet
Defect: The argparse docs say `type` "should only be used for simple conversions that can only raise one of the
three supported exceptions. Anything with more interesting error-handling or resource management should be done
downstream after the arguments are parsed", and warn that a file opened at parse time "is not automatically closed"
when a later argument fails; D1 reads the whole file or standard input there and does not say why neither failure
arises.
Material-because: none. Converting `OSError` to `ArgumentTypeError` and using `Path.read_bytes`, which closes the
file before it returns, avoid both documented failures, and #28's `json_member` already parses in `type`. This
finding only asks for a clarifying sentence.
Proposed-edit: after the `OSError` sub-bullet, add: "The read happens while argparse parses, before `cmd_call`'s
refusals. `Path.read_bytes` closes the file before it returns, so no file is left open when a later argument fails
(the argparse docs' warning for `FileType`)."
Source: https://docs.python.org/3/library/argparse.html, § type and § FileType objects.

### BP-D1 — "urllib calls it for every `30x`" is wrong for Python 3.9 and 3.10
Severity: D
Location: design.md § D3 — Where, first bullet
Defect: In CPython 3.9 the class sets `http_error_301 = http_error_303 = http_error_307 = http_error_302`, and only
3.11 and later add `http_error_308` (the 3.14 source: `... = http_error_307 = http_error_308 = http_error_302`). So on
3.9 and 3.10 a `308` never reaches `redirect_request`, and the other `30x` codes never do on any version.
Material-because: wording; the branch handles `307` only, and D3's Python 3.9 bullet already says
`http_error_308` was added in 3.11.
Proposed-edit: replace "urllib calls it for every `30x`" with "urllib calls it for a `301`, `302`, `303` or `307`
(and a `308` from Python 3.11)".
Source: https://raw.githubusercontent.com/python/cpython/3.9/Lib/urllib/request.py and
https://raw.githubusercontent.com/python/cpython/3.14/Lib/urllib/request.py, `HTTPRedirectHandler`.

## Sources checked, no finding

- CPython 3.9 and 3.14 `Lib/urllib/request.py`. `redirect_request` raises `HTTPError` for a `307` to any method but
  `GET` or `HEAD`. `http_error_302` limits the scheme to `http`, `https`, `ftp` or relative, quotes the URL and joins
  it with `urljoin(req.full_url, newurl)`, then opens the request it gets back. `do_request_` adds `Content-length` as
  an unredirected header whenever `data` is not `None`, so it is computed again for the re-sent request and
  `dict(req.headers)` never copies it. `Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False,
  method=None)` is the same on both versions.
- RFC 9110 §15.4.8: a `307` "MUST NOT change the request method". §15.4 lets an agent keep `Authorization` and only
  asks it to "consider removing" the header "where there are security implications". A same-origin re-send that
  keeps the credential and refuses a cross-origin one fits both.
- GitHub "Best practices for using the REST API": for a `307`, "repeat your request to the URL specified by the
  `location` header", and keep the original URL for future requests.
- GitHub "Upload a release asset": `name` is a required query parameter and `label` an optional one; the body is the
  raw binary; "Most libraries will set the required Content-Length header automatically" (urllib does, see above).
  Its use of `upload_url` and the asset's own media type are already listed in the requirements' Residuals.
- GitHub "Render a Markdown document in raw mode": the `Content-Type` is `text/plain` or `text/x-markdown`. The
  docs' example sends `Accept: text/html`, and the page says `application/vnd.github+json` "is recommended", so
  D4's `ACCEPT_JSON` follows the page's own recommendation.
- `gh api`: `--input` is "The file to use as body for the HTTP request (use "-" to read from standard input)", and
  with `--input` the field flags go into the query string; D1 quotes both correctly.
- Python `sys` docs: binary data is read with `sys.stdin.buffer.read()`. argparse docs: a `type` callable may raise
  only `ArgumentTypeError`, `TypeError` or `ValueError` ("Other exception types are not handled"), and `FileType` is
  "Deprecated since version 3.14".
- Python 3.9: `RestOperation`'s new fields come after `accept`, the last field and one without a default, so the
  frozen dataclass stays valid without `kw_only`, which needs 3.10.

Verdict: CLEAN
