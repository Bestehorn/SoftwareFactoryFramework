# Best-practice review — iteration 02 (delta) — issue #13 design

Sources read 2026-11-10: CPython 3.9 `Lib/urllib/request.py` (https://raw.githubusercontent.com/python/cpython/3.9/Lib/urllib/request.py),
the installed CPython 3.14.2 `urllib/request.py`, `http/client.py` and `secrets.py`, the Python docs, Hypothesis 6.170.15
(installed) and its strategies reference. No documentation MCP server covers GitLab, CPython or Hypothesis.

Fix sites: A1 is closed by X1 (the scan and the properties live in `test/`, CI's Python 3.10, `.github/workflows/ci.yml`;
`__future__`, `secrets`, `http`, `urllib` and `pkgutil` are all in `sys.stdlib_module_names`). B1 is closed (D4 "GraphQL",
AC-4.3 examples with `ciConfig` and `errors: []`). C1 to C4 are applied as proposed, C5 as X5 except its port default
(C7), and C6 is closed by X1. The new choices are consistent with the sources: `add_header` + `remove_header` by the
capitalised keys (3.9 `redirect_request` copies `req.headers` only, `remove_header` pops both maps); the origin taken from
`Request.type` and `.host` (`_parse` keeps userinfo in `host`, so `<host>@evil.example` is another origin); the 308 note
(3.9 has no `http_error_308`, and its `redirect_request` accepts 301/302/303/307 only); the `.`/`..` refusal (`quote`
never encodes `.`); the HTML multipart escapes; the whitespace refusal (`putheader` raises
`ValueError('Invalid header value %r')`, which would carry the token).

### C7 — The origin's default port is the scheme's, not always 443
Severity: C
Location: design.md § D4 "URLs and origin"; review-latest.md X5
Defect: urllib connects to port 80 for an `http` URL that has no port (`http.client.HTTPConnection.default_port =
HTTP_PORT`, `HTTPSConnection.default_port = HTTPS_PORT`; RFC 6454 §4 uses the scheme's default port), so "443 when
absent" makes `http://h/` and `http://h:443/` one origin although urllib connects to two ports, which contradicts the
paragraph's own "the parse urllib connects by". No credential reaches an `http` hop in this design (every credentialed
request starts on the `https` base, and a dropped credential stays dropped), so there is no leak.
Proposed-edit: replace "(443 when absent)" with "(the scheme's default when absent: 443 for `https`, 80 for `http`)".

### C8 — Give `secrets.token_hex` the boundary size
Severity: C
Location: design.md § D4 "Multipart (AC-2.4)"
Defect: With no argument, `token_hex` uses `DEFAULT_ENTROPY` (32 bytes, so 64 hex digits). The docs say "That default is
subject to change at any time, including during maintenance releases" (https://docs.python.org/3.9/library/secrets.html).
A multipart boundary is at most 70 characters (RFC 2046 §5.1.1, https://www.rfc-editor.org/rfc/rfc2046#section-5.1.1),
so a default above 35 bytes would make the body invalid.
Proposed-edit: replace "a boundary from `secrets.token_hex()`" with "a boundary from `secrets.token_hex(16)` (32 hex
digits; RFC 2046 limits a boundary to 70 characters)".

### C9 — The token refusal lets a non-Latin-1 character reach `http.client`
Severity: C
Location: design.md § D7 `_load_config()`; § Security Considerations "Token placement"
Defect: `HTTPConnection.putheader` encodes each str value with `encode('latin-1')`, and 3.9 `do_open` wraps only an
`OSError` from `h.request` in `URLError`. A pasted token that holds U+200B passes the check: it is not whitespace for
`str.isspace`, and its category is `Cf`, not `Cc` (checked with the installed CPython). It then raises
`UnicodeEncodeError`, a `ValueError`. `_send` catches `OSError` and `HTTPException`, and `main` catches `GitLabAPIError`,
so neither catches it, and the user sees a traceback instead of the logged message.
Proposed-edit: replace "a `token` containing whitespace or a control character raises" with "a `token` holding any
character outside printable ASCII other than the space (`!` to `~`) raises", and use the same wording in Security
Considerations.

### C10 — `blacklist_categories` is a deprecated Hypothesis alias
Severity: C
Location: design.md § Correctness Properties, AC-2.2
Defect: The documented `st.characters` signature names `exclude_categories`, not `blacklist_categories`
(https://hypothesis.readthedocs.io/en/latest/reference/strategies.html). The installed 6.170.15 keeps the old name only
under "these arguments are deprecated aliases for backwards compatibility" (`hypothesis/strategies/_internal/core.py`
`characters`), and `pyproject.toml` does not pin `hypothesis`.
Proposed-edit: replace `blacklist_categories=("Cs",)` with `exclude_categories=("Cs",)`.

Verdict: CLEAN
