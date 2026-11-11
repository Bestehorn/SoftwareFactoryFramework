# devops-iac-reviewer — design iteration 01 — issue #63

### B1 — The deferred real-instance check is routed to #10, which owns GitHub only
Severity: B
Location: requirements.md § header ("the real-forge run (#10)"), § Requirement 8 user story, § E2E, § Residuals
(bullets "Delete image tags by reference" and "Retrieve the token information"); design.md § Testing Strategy "E2E",
§ Residuals (last bullet)
Defect: The spec names "#10's run" as the GitLab real-forge check. But issue #10's Ask is "Correct is §5 as written
(AC-1 to AC-5), GitHub first", and its ACs create GitHub repositories with a GitHub token. Issue #11 keeps the GitLab
check: its work item is "Real-GitLab integration tests (needs a GitLab equivalent of #10)", its open question is "Which
GitLab instance and token do real-forge tests use, given #10 covers GitHub only?", and its 2026-11-10 comment says "The
real-GitLab integration tests item and the GitLab test-target question stay on this issue". Every GitLab slice spec
(#13, #41, #42, #44) already names it "#11's real-instance run".
Material-because: unmaintainable-by-rule `always-test-e2e.md`. The test plan must name what runs the end-to-end
check. Here the three GitLab answers this change defers would become findings-ledger rows (design D12) that point at
an issue that never runs GitLab: the `/tags/reference/` URL, `PRIVATE-TOKEN` on `/oauth/token/info`, and D4 step 2
under a job token.
Proposed-edit: in requirements.md, replace "the real-forge run (#10)" with "the real-instance run (#11)". Replace "As
the owner of #10" with "As the owner of #11". Replace "the real-forge check is #10's run on an ephemeral `sff-test-*`
project" with "the real-instance check is #11's run on an ephemeral `sff-test-*` project". Replace "GitLab's answer is
#10's run" with "GitLab's answer is #11's run", and "whether GitLab answers it is #10's run" with "whether GitLab
answers it is #11's run". In design.md, make the same E2E replacement, and replace "#10's run → one ledger row" with
"#11's run → one ledger row". (`prompt.md` "the real-forge run (#10)" belongs to the conductor, which can restate it
the same way.)

### C1 — D4's "never the answer's body" contradicts `_send` and Operability for an error status
Severity: C
Location: design.md § D4, "AC-5.3." bullet and "`_send(..., destination: Optional[Origin] = None)`" bullet;
§ Operability
Defect: Step 3 goes through `_send`, because the origin check lives there. `transport.Transport._send` raises an
error status as `f"{method} {url} answered {response.status}: {error_text(body=response.text)}"` with
`details=response.text`, and `gitlab_wrapper._report` logs both. Operability says the exit-1 path carries "GitLab's
error text". But "step 3's errors name the URL, which holds the scope, never the answer's body" reads as forbidding
exactly that. The body that must stay out of logs is a success answer's, because it holds `token`.
Proposed-edit: replace "step 3's errors name the URL, which holds the scope, never the answer's body." with "an error
status at step 3 is reported as `_send` reports any, with the URL (which holds the scope) and GitLab's error text; a
success answer whose `token` is absent or not a non-empty string is refused naming the URL and the field, never
quoting its body, which holds the token."

### C2 — AC-5.3's log oracle misses the configured token's new encoding
Severity: C
Location: design.md § Correctness Properties, AC-5.3
Defect: Step 3 sends the configured token as `Authorization: Basic`, the base64 of `<login>:<token>` (RFC 7617). The
oracle "the configured token in no log record" would still pass a log record that holds that base64 value.
Proposed-edit: replace "the configured token in no log record" with "neither the configured token nor the base64 of
`<login>:<token>` in any log record".

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
