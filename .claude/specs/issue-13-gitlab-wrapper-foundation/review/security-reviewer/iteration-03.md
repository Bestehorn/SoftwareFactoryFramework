# Security review — issue #13 design, iteration 03 (delta, lane security-reviewer)

Fix sites checked against CPython 3.14.2's `Lib/urllib/request.py` and `Lib/http/client.py`:

- C7 is fixed. D4 "Constants" spells `CREDENTIAL_HEADERS` as `Private-token`, `Job-token`, `Authorization`.
  `add_header` stores `key.capitalize()`. `redirect_request` copies `req.headers` with the keys as stored and builds
  the new `Request` through `add_header` again. `remove_header` pops exactly that key. The AC-3.1 oracle now compares
  names case-insensitively, so the test catches an implementation that forwards `Private-token`.
- The origin rule opens no leak. It matches `HTTPConnection._get_hostport`: split at `rfind(':')` only when that is
  after `rfind(']')`, `int()` for the port, and an empty port means the default port. `_splittype` lower-cases the
  scheme. `Request._parse` unquotes the host, so the host compared is the host that gets connected to. A probe over
  every code point found one non-ASCII character whose `lower()` is ASCII: U+212A, which becomes `k`. IDNA also encodes
  it as `k`, so a credential kept by the case-folding goes only to the configured host. `http://` and `ftp:` have a
  different scheme, so they are different origins whatever port they get.
- The printable-ASCII refusal opens no leak and closes one. `http.client.putheader` raises
  `ValueError('Invalid header value %r')`, which contains the token, when the value has CR or LF that is not header
  folding. `_send`'s `ValueError` catch could have carried that text into a `GitLabAPIError`. No character from `!` to
  `~` matches `_is_illegal_header_value`, so a token that passes the check never reaches that raise.

### C1 — the UB-2 refusal oracle checks the message but not `details`, which `main` also logs
Severity: C
Location: design.md § Correctness Properties UB-2; § D7 `_load_config`, `main` step 4
Defect: D7 step 4 logs a `GitLabAPIError`'s message and then its `details`. The UB-2 example only says the trailing
newline and zero-width space cases raise "without the value in the message". An implementation that puts the rejected
token in `details` would pass that test and print the token to standard error. D7's "never the value" rules this out,
but no test enforces it.
Proposed-edit: in Correctness Properties UB-2, replace "(the last two without the value in the message)" with "(the
last two: neither the message nor `details` contains the value)".

CLEAN
