# Security review — issue #63 design, iteration 01 (security-reviewer)

### C1 — The step-2 answer that names the registry origin may come from another origin
Severity: C
Location: design.md § D4 "The container registry" step 2; § Security Considerations "The registry token"
Defect: Step 2 is a `GET` through `_send`, and `CredentialStrippingRedirectHandler` follows a `GET` redirect to another
origin (it strips the credential, it does not refuse the hop), so the `container_registry_image_prefix` that decides
where step 4 sends a GitLab-minted, delete-scoped token is read from whatever origin the redirect chain ended on; "the
origin GitLab's own `container_registry_image_prefix` names" holds only when the configured origin served the answer.
Reaching it needs a cross-origin redirect from the configured instance's `/api/v4/projects/<id>`.
Proposed-edit: Security Considerations "The registry token": replace "It goes only to the origin GitLab's own
`container_registry_image_prefix` names" with "It goes only to the origin named by the `container_registry_image_prefix`
of step 2's answer, which, like every `GET`, may follow a redirect (#13 D4)"; add to `## Residuals`: "Steps 1 and 2
accept an answer reached through a cross-origin `GET` redirect; refusing a response whose final URL is off the
configured origin before step 3 → one ledger row."

### C2 — `transport.origin` accepts registry authorities that are not `host[:port]`
Severity: C
Location: design.md § D4 table step 2 ("the text of `container_registry_image_prefix` before its first `/`"); § D4
"AC-5.3"
Defect: `origin` refuses only a URL urllib cannot open and a non-integer port; on `252c21e` the prefix `""` gives
`https://:443`, `registry.example.com#` gives the selector `''`, `registry.example.com?x` the selector
`/?x/v2/group/project/...`, and `a@registry.example.com` the host `a@registry.example.com` — none refused, so "an
authority `transport.origin` refuses" lets step 4's `DELETE` reach the registry's `/` (with `#`) or carry its route in
the query (with `?`). The token still reaches only a host the answer names, or none.
Proposed-edit: D4 step 2 "Yields" cell: "the registry origin: `https://` and the text of `container_registry_image_prefix`
before its first `/`, which must be non-empty and hold none of `@`, `?`, `#`, `\` or white space; any other raises
`GitLabAPIError` before step 3"; F:package `test_no_registry_token_sends_nothing_to_the_registry` gains the prefixes
`/group/project`, `registry.example.com#/x` and `user@registry.example.com/x`.

### C3 — The transport's refused header names omit the urllib-owned names D7 lists
Severity: C
Location: design.md § D5 "The transport"; § Security Considerations "Headers"
Defect: `_build_request` would accept a caller header named `Host`, `Content-Length`, `Transfer-Encoding` or
`User-Agent`, and Python 3.9 `AbstractHTTPHandler.do_request_` adds its own of each only when `has_header` is false, so
the caller's would be sent in its place; D7's `SentCall.headers` already names these "the transport's and urllib's",
and Security Considerations says the transport refuses "a name it owns". No section declares one (AC-6.1's four
names), so only a future record reaches it.
Proposed-edit: D5 "The transport": "A name equal, ignoring case, to `Accept`, `Content-Type`, `Content-Length`,
`Transfer-Encoding`, `Host`, `User-Agent` or a `TOKEN_HEADERS` name, and a value holding CR, LF or NUL, raise
`ValueError` before anything is sent."; T `test_a_request_header_is_sent_beside_the_transport_headers` adds `Host` and
`Content-Length` to its refused names.

### C4 — No oracle holds the registry token out of the logs
Severity: C
Location: design.md § Correctness Properties AC-5.2, AC-5.3; § D4 "`_send(..., destination ...)`"
Defect: D4 states the registry token "enters no URL, log record or exception message", but only the configured token is
asserted absent from the logs (AC-5.3), in cases where no registry token was ever issued; `gitlab_wrapper._report` logs
a `GitLabAPIError`'s `details` at ERROR, so an implementation that passes step 3's body as `details` (as
`Response.value` does for a JSON-typed body it cannot parse) logs the token with every listed test green.
Proposed-edit: Correctness Properties AC-5.2, F:package `test_a_registry_record_is_sent_to_the_registry_with_its_token`:
append "With the registry answering `404` to step 4: exit 1, and neither the configured token nor the scripted registry
token in any log record."; AC-5.3 Oracle: "the configured token and the scripted registry token in no log record".

### C5 — "What stays callable" omits the destructive F1 keys
Severity: C
Location: design.md § Security Considerations "What stays callable"
Defect: The bullet names the F2 records, the registry tag delete and `_catalog`, but D8's F1 records also add ungated
deletes (`operations-index.md`): `DELETE /groups/:id/access_requests/:user_id`, `/groups/:id/custom_attributes/:key`,
`/users/:id/custom_attributes/:key`, `/groups/:id/invitations/:email`, `/groups/:id/ldap_group_links/:provider/:cn` and
the Conan v1 "Delete a recipe and package".
Proposed-edit: replace the bullet's list with "every record of D8, none gated (#41 Security "Destructive operations"):
the F1 `DELETE` keys (access-request deny, custom-attribute deletes, invitation delete, the LDAP link delete, the Conan
v1 recipe-and-package delete), the F2 revoke and rotate records and the SSH-certificate delete; the registry tag
delete; `_catalog`, which GitLab answers for an administrator."

CLEAN
Verdict: READY
