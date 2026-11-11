# Best-practice review — issue #63 design, iteration 01

No MCP documentation server covers GitLab or the Python standard library. Sources: `docs/api-reference/gitlab/`
first, then docs.gitlab.com, `gitlab-org/gitlab` `master` and docs.python.org/3.9, all read 2026-11-11.

### C1 — Under `token_type` `job`, D4 step 2 calls an endpoint GitLab documents as refused
Severity: C
Location: design.md § D4 "The container registry" step 2; design.md § Residuals (the job-token clause)
Defect: `conventions.md` "Which endpoints accept a CI/CD job token" says "a job token works only where GitLab lists
it; everything else rejects it" and its table has no Projects API row (docs.gitlab.com `ci/jobs/ci_job_token` has none
either). So `GET /projects/<project>` with `JOB-TOKEN` is refused, and every container-registry call under a job
token exits 1 at step 2. The residual calls this an open question for #10, but the reference already answers it.
Material-because: risk worth one sentence; the behaviour stays AC-5.3's (exit 1, nothing sent to the registry), so
no criterion breaks.
Proposed-edit: in design.md § Residuals replace "whether GitLab answers step 2 for a job token is #10's run" with "a
job token is refused at step 2's `GET /projects/:id` (`conventions.md` "Which endpoints accept a CI/CD job token" lists
no Projects API endpoint), so a container-registry call under `job` exits 1 (AC-5.3)".

### C2 — GitLab's source settles the token-information residual
Severity: C
Location: requirements.md § Residuals ("Retrieve the token information"); design.md § D4 "The host root"
Defect: `app/controllers/oauth/token_info_controller.rb` answers only a Doorkeeper token. `config/initializers/
doorkeeper.rb` `access_token_methods` reads that token from `from_access_token_param`, `from_bearer_authorization`
and `from_bearer_param` and nowhere else. So under `private` (`PRIVATE-TOKEN`) or `job` (`JOB-TOKEN`) GitLab answers
`401` `invalid_token` and the call exits 1. Only a `bearer` OAuth token gets the token information.
Material-because: risk worth one sentence; AC-5.1 requires the configured header, and the design sends it as written.
Proposed-edit: in requirements.md § Residuals replace "and whether GitLab answers it is #10's run" with "and GitLab
reads only an OAuth token there (`Oauth::TokenInfoController`, Doorkeeper `access_token_methods`), so under `private`
or `job` the call exits 1 with GitLab's `401`".

### C3 — `/jwt/auth` accepts an OAuth token with any login
Severity: C
Location: requirements.md § Residuals ("A `bearer` token has no documented registry login"); design.md § Residuals
(`token_type` `bearer`)
Defect: `lib/gitlab/auth.rb` `git_client_checks` runs `oauth_access_token_check(password)`, which checks no login
(as `personal_access_token_check(password, project)` checks none). So refusing `bearer` follows the registry page's
list of credential types, not a refusal by GitLab. The ledger row should say so, so that #10's run knows to check it.
Material-because: residual outside the ask; keeping to the documented credential list is the conservative choice and
stays.
Proposed-edit: in design.md § Residuals replace "the registry's authentication page lists no OAuth login, so" with
"the registry's authentication page lists no OAuth credential (though `lib/gitlab/auth.rb` `oauth_access_token_check`
accepts an OAuth token as the Basic password under any login), so".

### C4 — A header given twice is sent once, with its last value
Severity: C
Location: design.md § D5 `encode` and "The transport"
Defect: the Python 3.9 `Request.add_header` docs say "there cannot be more than one header with the same name, and
later calls will overwrite previous calls in case the key collides". So a name given twice with `--header` reaches
GitLab only with its last value, but D5 says only "each given header value … in the caller's order".
Material-because: clarification; the outcome matches the base's "given twice keeps its last value" (`commands/call.py`
module docstring), so no criterion breaks.
Proposed-edit: in D5 `encode` replace "each given header value as `_text` writes it, under its declared name, in the
caller's order" with "each given header value as `_text` writes it, under its declared name, in the caller's order; a
name given twice keeps its last value, as a path name or an attribute does and as `Request.add_header` stores one value
per name".

CLEAN
Verdict: READY
