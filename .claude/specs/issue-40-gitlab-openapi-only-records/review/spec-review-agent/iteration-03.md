# spec-review-agent — design review, iteration 03, delta (issue #40, tier M)

Scope: the iteration-02 fix sites. In `requirements.md` these are AC-1.3 and the Residuals' job-token line. In
`design.md` they are D4 "The uploads", D5 `prepare_call` step 1, Correctness Properties AC-1.3 and AC-3.2 (G),
Security "The raw body" and "Gates", and Sources.

How the iteration-02 items stand:
- **B1 is closed.** F's `REQUIRED` now reads "the `yes` rows that name no path parameter, a raw-body record's `file`
  row excepted". That matches the `KINDS` bullet, AC-1.3 and AC-3.2. `upload-job-artifacts` keeps its required `file`,
  because it is not a raw-body record.
- **C1 is closed.** D5 step 1's message now says that a raw-body record's attributes are given with `--query`.
  `OPTION_QUERY = "--query"` exists in `commands/call.py`.
- **D1 is closed.** AC-1.3 is restated as proposed. Its exclusions (a path parameter, a raw-body `file` row) and its
  location rule (`form` → `BODY`, raw-body → `QUERY`) match D4's `params` and `Param.location` rows.
- **Standards B1 is closed.** The G sketch now reads `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=…))`.
  `origin/main:src/payload/test/test_github_api_call.py` builds the same keyword form. The venv interpreter accepts it
  and returns the raw bytes from `.buffer.read()`.

The other iteration-02 edits are consistent and verified:
- **Security C1 (redirect).** `CredentialStrippingRedirectHandler.redirect_request` raises `HTTPError` for any method
  outside `FOLLOWED_REDIRECT_METHODS` (`GET`, `HEAD`).
  - `_attempt` turns that error into a `Response`.
  - `_succeeded` accepts only 2xx, so `_send` raises `GitLabAPIError` (exit 1).
  - All four raw-body records are `PUT` or `POST`, as the Introduction states.
- **Security C2 (Git-URL import).** GitLab `lib/api/project_import.rb` (master) runs `post ':id/import/git'`, and that
  route contains `conflict!('Project already has a repository') if user_project.repository_exists?`.
  - `lib/api/helpers.rb` defines `conflict!` as `render_api_error!(message || '409 Conflict', 409)`.
  - The entry is `rest/openapi-only.md` "Import a project from a Git URL", `POST /projects/:id/import/git`.
- **Security D1.** docs.gitlab.com Group access tokens API says rotation "immediately revokes the previous token and
  creates a new token". Its example response carries `token`.
- **Practice C1.** Workhorse `artifacts_uploader.go` `ProcessFile` refuses any `formName` other than `"file"` and
  writes the generated metadata fields itself.
  - The entry's `metadata` row (`form`, `file`, not required) remains a `FILE` `Param` under AC-1.3.
  - That `Param` is counted in F's `KINDS` and not in `REQUIRED`. Nothing contradicts D4.
- **Practice C2.** Workhorse `internal/api/api.go` `newRequest` builds the authorize request with no body, and it
  deletes `Content-Type` and `Content-Length`.
  - `TokenType.JOB` sends `JOB-TOKEN` (`transport.py` `TOKEN_HEADERS`).
  - Security "The credential" ("sent where its record puts it") does not contradict the residual.
- **Caps.** `requirements.md` is 14,749 B (cap 20,000) and `design.md` is 56,530 B (cap 60,000). Each Residuals
  section is 10 lines.

### C1 — K's both-bodies oracle does not pin the sentence D5 step 1 added
Severity: C
Location: design.md § Correctness Properties AC-3.2, K `test_a_raw_body_the_call_cannot_send_is_refused`, first case
Defect: D5 step 1's message now also names `--query`. The oracle still checks only for `--input`, `-f/--raw-field` and
`-F/--field`, so the added sentence has no test.
Proposed-edit: "a log record names `--input`, `-f/--raw-field` and `-F/--field`" becomes "a log record names
`--input`, `-f/--raw-field`, `-F/--field` and `--query`".

CLEAN

Verdict: READY
