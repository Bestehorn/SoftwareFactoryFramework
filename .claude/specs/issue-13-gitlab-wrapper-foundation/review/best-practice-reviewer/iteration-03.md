# Best-practice review — iteration 03 (delta) — issue #13 design

Sources read 2026-11-10: CPython 3.9 `Lib/http/client.py` (https://raw.githubusercontent.com/python/cpython/3.9/Lib/http/client.py),
the installed CPython 3.14.2 `urllib/request.py` and `http/client.py`, Hypothesis 6.170.15 (installed). No documentation
MCP server covers CPython, Hypothesis or GitLab.

Fix sites verified. C7: D4 "URLs and origin" matches 3.9 `_get_hostport` (`int(host[i+1:])`; an empty port takes
`self.default_port`; anything else raises `InvalidURL("nonnumeric port")`, which the design pre-empts with
`GitLabAPIError`). C8: `secrets.token_hex(16)`. C9: D7 `_load_config()` and Security "Token placement" both read `!` to
`~`. C10: `exclude_categories=("Cs",)` is a parameter of the installed `st.characters`, and `pyproject.toml` lists
`hypothesis` unpinned. Redirect wording: `origin(req.full_url)` is right, because `Request.set_proxy` ends
`self.host = host` and leaves `full_url` alone.

The #17 gap does not apply here. A `%20` host survives `Request._parse` (`unquote` gives `host`
`'gitlab.example evil'`), and `HTTPConnection.__init__` raises `InvalidURL` from `_validate_host` (`[\x00-\x20\x7f]`)
before `do_open`'s `OSError` wrapper. `InvalidURL` subclasses `http.client.HTTPException` (3.9 source and the installed
MRO), which D4 "Errors" already catches.

### C11 — `origin` has no default port for a scheme other than `http`/`https`
Severity: C
Location: design.md § D4 "URLs and origin"; § Security Considerations "The credential reaches the configured origin only"
Defect: The text gives a default port for `https` and `http` only, but Security refuses a `file:` or `ftp:` next URL, so
`origin` must return a value for those schemes (`Request(url="file:///etc/passwd")` has `type` `'file'` and `host` `''`;
`ftp://h/x` has `'ftp'` and `'h'`). A lookup keyed on the two named schemes would raise `KeyError` instead of the AC-2.6
`GitLabAPIError`.
Proposed-edit: after "(443 for `https`, 80 for `http`: `http.client`'s `default_port`)" insert "; any other scheme has
none (`None`), so its origin never equals the configured one".

### C12 — urllib also raises a `ValueError` while opening a redirect target
Severity: C
Location: design.md § D4 "Errors (AC-3.5)"
Defect: `Request._parse` unquotes a `Location` host written as percent-encoded non-Latin-1 text
(`https://%E6%97%A5%E6%9C%AC.example/`), and `http.client`'s `latin-1` header encoding inside `h.request` then raises
`UnicodeEncodeError`, a `ValueError` ("'latin-1' codec can't encode characters"). `do_open` does not wrap it, and no
socket is opened (checked with the installed CPython). This happens while urllib opens the target, not while it resolves
the `Location`, so the text names only one of the two places the `_send` catch covers.
Proposed-edit: replace "a `ValueError` raised while urllib resolves a redirect's `Location`" with "a `ValueError`
raised while urllib resolves or opens a redirect's `Location`".

Verdict: CLEAN
