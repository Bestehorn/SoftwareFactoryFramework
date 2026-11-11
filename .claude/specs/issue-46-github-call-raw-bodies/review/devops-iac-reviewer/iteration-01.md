# Design review — devops-iac-reviewer — iteration 01

### C1 — The automatic re-send of a PATCH or DELETE leaves no trace on standard error, and a 307 that ends a call reads the same whatever ended it
Severity: C
Location: design.md § D3 "Once." and "Another origin: refused"
Defect: After D3, every `PATCH` and `DELETE` gets the re-send, the compatibility subcommands' included (D3 "Every
  entry point", DL-002). So a write request can be sent twice to a URL the caller never named, and nothing says so.
  The transport already logs its other automatic repeat, the rate-limit retry (`logger.warning` in `Transport._send`).
  Also, a cross-origin refusal and AC-3.2's second-hop `307` both end in `_http_failure` naming only the original
  URL, so the stderr line "failed: HTTP 307" cannot tell the two apart.
Proposed-edit: in D3 "Once.", append the bullet: "The re-send is logged once with `logger.info`, naming the method and
  both URLs rendered with `render_url`, as `_send` logs a rate-limit retry; no header or body is logged." If the
  conductor counts the log line as scope, add instead under design.md § Residuals: "The same-origin `307` re-send
  is not logged, and a `307` that ends a call names only the original URL."

Verdict: CLEAN
