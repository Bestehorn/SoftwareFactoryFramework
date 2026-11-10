# Security review — issue #17 design, iteration 03 (delta)

Iteration-02 findings, verified at their fix sites:

- C1 closed: D3 "Origin (X5)" uses the scheme's default port, 443 for `https` and 80 for `http`, as
  `http.client`'s `default_port`.
- C2 closed: D3 "Redirects" compares the target with `origin(req.full_url)`, never `req.host`. `Request.set_proxy`
  rewrites `host` and leaves `full_url` alone, which iteration 02 measured, so a proxy no longer changes which hops
  keep `Authorization`. The parent `redirect_request` builds a fresh `Request` from the new URL and copies `req.headers`.
  `Authorization` is set with `add_header`, so it is in `req.headers`, and the handler removes it there. A
  `GitHubAPIError` that `origin` raises on a bad `Location` port comes before the next hop is sent.
- C3 closed: D6 `_detect_repo` removes "everything up to the last `@` before the host, a bare token included", on
  stderr only. UB-1.1 (requirements) binds only standard output and exit codes, so this deviation is inside it. The
  compat-only UB-1.1 example tests both `ghp_T@` and `user:secret@`, and P leaves it out.
- D1 closed: "placed in a message or a log line".
- D5 `get-logs` 302: D3 `download` follows the storage-host `302` without the credential. Under D3's rule the storage
  host's origin is not `API_ROOT`'s, so the handler strips `Authorization` at that hop and it stays absent on every
  later hop. The outcome matches the fork's `_NoRedirectHandler`, which strips on every hop. The UB-1.1 carve-out
  names exactly this `302`, and D5's closing sentence says both wrappers follow it without the credential.
- Security Considerations "Where the token goes" matches D3: the pre-send refusal covers origins other than
  `API_ROOT`'s or `UPLOAD_ORIGIN`, and the credential is dropped for the rest of the chain after a cross-origin hop.

### D1 — "No message carries a URL's userinfo" is broader than D3 allows
Severity: D
Location: design.md § Security Considerations, "Credential source"
Defect: D3 "Origin (X5)" makes a non-integer port, including one produced by a `user:password@` part, raise
`GitHubAPIError` "naming the URL". The URL in that message carries userinfo, so the sentence contradicts D3 when read
literally. The URLs that reach `origin` come from the API or its responses (paths, `link`, `upload_url`, `Location`),
never from the user's credential, so the two readings are equally safe.
Proposed-edit: replace "No message carries a URL's userinfo (`_detect_repo`)." with "No message carries the git remote
URL's userinfo (`_detect_repo`)."

CLEAN
