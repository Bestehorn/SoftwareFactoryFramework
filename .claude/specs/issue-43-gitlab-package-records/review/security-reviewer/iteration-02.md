# Security review — issue #43 design, iteration 02 (security-reviewer, delta only)

No findings.

## Iteration-01 findings: closed
- B1 (`PUT /projects/:id/` pull mirror). requirements.md AC-1.3 keeps `("PUT", "/projects/:id/")` pending, and AC-4.2
  no longer names `avatar`. The Residuals hand the key to tenant-scale's "Update a project". design.md D5 has no
  `change-the-visibility-of-the-container-registry` row, D6 "The kept keys" lists the key, and "What stays callable"
  dropped its bullet. "Gates" states that the key stays pending. The AC-1.1 and AC-1.3 oracles exclude it. In
  `rest/package.md`, every `mirror`, `mirror_overwrites_diverged_branches`, `import_url` and `default_branch` row sits
  inside the one entry "Change the visibility of the container registry". No other package entry's endpoint is a bare
  `PUT`/`POST`/`PATCH /projects/:id` or `/groups/:id`. No record of this change can write a branch.
- C1 (upstream passwords). "The credential" now names the container and Maven virtual-registry upstream `password` rows
  and points them at #41's "Secrets in arguments" residual.

## The iteration-01 edits: no new risk
- npm "Create or update a dist-tag" as a raw JSON body. The bytes go through #40 D5's `request_raw`/`_send`, so the
  origin check and the one credential header are unchanged. The record is a `PUT`, which
  `CredentialStrippingRedirectHandler` does not follow. Its prefix is still chosen by exact text before `refuse_raw_body`'s
  routed record is sent (D2, D3). A caller-supplied body reaches only the configured host's Rails.
- NuGet v3 "Upload a package file" moved to the proxy residual. The record keeps #41's multipart form, its path, and
  the configured origin. GitLab refuses an un-rewritten `WorkhorseFile` part, so the change is an HTTP error, exit 1,
  and the credential goes nowhere new.
- The unauthenticated families (Conan, Debian, NuGet, Helm, Ruby gems). No credential form is added: no HTTP Basic, and
  no `X-NuGet-ApiKey`. The transport still sends one configured header (`TOKEN_HEADERS`: `PRIVATE-TOKEN` or
  `Authorization: Bearer`) to one origin only (UB-2).
- I verified the claim that Conan issues no token against gitlab-org/gitlab `master`:
  - `lib/api/helpers/packages/conan/api_helpers.rb`: `access_token_from_request` is
    `find_personal_access_token_from_conan_jwt || find_password_from_basic_auth`, and `token` falls through to
    `ConanToken.from_job(find_job_from_token)`.
  - `lib/gitlab/conan_token.rb`: `from_job` begins `return unless job&.running?`.
  - So `token` is `nil`, and the endpoint answers `unauthorized! unless token` with a 401. Nothing prints a token, which
    is why the iteration-01 Conan-token residual can go.

Verdict line: CLEAN

Verdict: READY
