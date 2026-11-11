# Security review — issue #40 design, iteration 02 (delta: D5, and the fix sites of iteration 01)

### C1 — "The raw body" rests its one-origin claim on a check that judges only the first URL
Severity: C
Location: design.md § Security Considerations "The raw body", first sub-bullet; § D5 `Transport.request_raw`
Defect: `_send`'s origin check judges the URL it is given, never a redirect's target. The bytes and the token stay on
the configured origin because `CredentialStrippingRedirectHandler.redirect_request` raises the `HTTPError` for any
method outside `FOLLOWED_REDIRECT_METHODS` (`GET`, `HEAD`), and the four raw-body records are `PUT` or `POST` (D4 "The
uploads"). The bullet does not name that reason, and the claim depends on it.
Proposed-edit: after "whose origin check and one credential header are unchanged (D5)" add "; each raw-body record is a
`PUT` or a `POST`, and `CredentialStrippingRedirectHandler` follows a redirect of neither (#13 D4 \"Redirects\"), so a
`3xx` exits 1 and neither the bytes nor the token reach its target".

### C2 — The Git-URL import sub-bullet gives a reason that is not the class test its bullet states
Severity: C
Location: design.md § Security Considerations "Gates", the `openapi-only#import-a-project-from-a-git-url` sub-bullet
Defect: the bullet's lead names #41's class (a record that commits to or merges into a branch, or creates an issue).
This sub-bullet answers with "has no compatibility subcommand that a gate judges", which that class does not test:
GitHub's `GATED_OPERATIONS` refuses records that no subcommand sends (its `None` entries, `github_api/commands/call.py`
on origin/main). What keeps this record outside the class is GitLab's handler of `POST ':id/import/git'`
(`lib/api/project_import.rb`, `master`, read 2026-11-11): `authorize_admin_project`, then
`conflict!('Project already has a repository') if user_project.repository_exists?`. So it writes no branch of a
project that has a repository. The configured project, `call`'s `id` default (`takes_project`), gets `409`, exit 1.
Proposed-edit: replace "fills the repository, and has no compatibility subcommand that a gate judges." with "fills only
a project that has no repository: GitLab answers `409` \"Project already has a repository\" to any other
(`lib/api/project_import.rb`, `POST ':id/import/git'`), so it writes no existing branch, the configured project's
included." In § Sources add "GitLab `lib/api/project_import.rb`, `master`, read 2026-11-11: `POST ':id/import/git'`
runs `conflict!('Project already has a repository') if user_project.repository_exists?`."

### D1 — The group-token rotation claim cites a source the Sources list lacks
Severity: D
Location: design.md § Residuals, the access-token bullet ("(Sources)"); § Sources, the access-token entries
Defect: Sources cite the personal and project access token APIs. The Residual's claim for
`openapi-only#rotate-a-group-access-token` has no source.
Proposed-edit: after the Project access tokens entry add "[Group access tokens API](https://docs.gitlab.com/api/group_access_tokens/):
rotation \"immediately revokes the previous token\", its response holding `token`."

## The dispatch's questions

- Another origin: no. `request_raw` builds the URL with `_rest_url`, the configured `https://<hostname>/api/v4`
  followed by a path that must start with `/`. `_send` refuses any other origin before sending.
- The token or the bytes in a redirect: no (C1 states why).
- Reading beyond the named file: no. `read_input` reads `Path(text)` or standard input's buffer, nothing else. No
  parser in `gitlab_wrapper.py` or `gitlab_api/` sets `fromfile_prefix_chars`.
- A gated route: no. `refuse_gated` runs before `registry.lookup`. `refuse_raw_body` refuses every record without a
  `content_type`, the two `GATED_OPERATIONS` records included. The four raw-body records merge nothing and create no
  issue.
- The `config/gitlab.json` residual: stated, in "The raw body" third sub-bullet and § Residuals "Secrets", matching #41
  Residuals "Secrets in arguments".
- Iteration 01: C1, C2, C3 and D1 read correctly. C3's list is still complete. D4 moves the rows `status` and `select`
  to the query on the raw-body records, and neither carries a token.

CLEAN

Verdict: READY
