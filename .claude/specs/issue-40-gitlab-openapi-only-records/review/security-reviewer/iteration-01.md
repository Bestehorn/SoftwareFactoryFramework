# Security review — issue #40 design, iteration 01

### C1 — The Gates bullet checks a narrower class than the one #41 routes to this slice
Severity: C
Location: design.md § Security Considerations "Gates"; § D4, its last line
Defect: #41 routes "a record that commits to or merges into a branch, or creates an issue" to the slice that adds it
(#41 design.md D8 exceptions row, Residuals). The design checks only "merges a merge request or creates an issue". So
it never names this change's two records that commit, or the slash-command triggers that can create an issue:
- `POST /projects/:id/create_ci_config` "creates a merge request including ci config file" (gitlab-org/gitlab!111353);
- `POST /geo/proxy_git_ssh/receive_pack` is a git push. Its entry requires the body attribute `secret_token`;
- the two `mattermost_slash_commands/trigger` routes and `POST /slack/trigger` run chat commands, and creating an issue
  is one of them (gitlab-org/gitlab#569345).
None of them is reachable as a gate bypass. The first merges nothing. `config/gitlab.json` holds no `secret_token`
(`templates/config/gitlab.json.template`). Each trigger record lacks a name the command needs: the Mattermost entries
declare only `token`, so `call` refuses `text`; the Slack entry declares only `text`, so `call` refuses the
verification `token` (!118289's example sends both). The text should say this.
Proposed-edit: replace the Gates bullet with "**Gates.** `GATED_OPERATIONS` and the hooks are unchanged. #41's gated
class is a record that commits to or merges into a branch, or creates an issue. No record of this change merges.
`openapi-only#create-a-ci-configuration-merge-request` commits only into the merge request it opens.
`openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push` needs the `secret_token` its entry requires,
which `config/gitlab.json` does not hold. The slash-command triggers cannot carry an issue-creating command through
`call`: the Mattermost records declare no `text`, and `/slack/trigger`'s declares no `token`. None is gated."

### C2 — The self-rotation residual leaves out the zero-argument case
Severity: C
Location: design.md § Residuals, the personal-access-token bullet; § Security Considerations "The routes that stay
callable", last sub-bullet
Defect: the residual and its ledger row name only the two `/personal_access_tokens/self` records, but
`templates/config/gitlab.json.template` names a project or group access token as a supported configured credential.
`POST /projects/:id/access_tokens/self/rotate` "immediately revokes the previous token and creates a new token", and
the response holds the new `token` (GitLab docs, Project access tokens API). `call`'s `takes_project` gives this path
the configured `id`, so `call openapi-only#rotate-a-project-access-token` with no option revokes the credential in
`config/gitlab.json` and prints its replacement on standard output. `openapi-only#rotate-a-group-access-token` does
the same once `--path id` is given.
Proposed-edit: in the Residuals bullet, replace "`openapi-only#revoke-a-personal-access-token` revokes the token that
authenticates the request, and `openapi-only#rotate-a-personal-access-token` \"revokes the previous token and creates a
new token\", whose value its response holds" with "`openapi-only#revoke-a-personal-access-token` revokes the token that
authenticates the request. `openapi-only#rotate-a-personal-access-token`, `openapi-only#rotate-a-project-access-token`
and `openapi-only#rotate-a-group-access-token` each revoke that token and create a new one, whose value the response
holds. The project record needs no option, because its `id` defaults to the configured project". In the Security
sub-bullet, add the two records to the "among them" list.

### C3 — A runner or job token given in the query reaches standard error on any error
Severity: C
Location: design.md § Security Considerations "The credential"
Defect: three entries take `token` `In` `query`: `DELETE /runners/managers` (required), `GET /jobs/:id/artifacts` and
`GET /jobs/:id/runtime_environment_key`. `Transport._rest_url` puts the query into the URL. `_send`'s
`GitLabAPIError` text, `_attempt`'s "got no response" text and `_wait`'s 429 warning all quote that URL, and the
entry script logs the message. So an HTTP error writes that token to standard error. The bullet names only the command
line, which in a CI job script shows a variable reference, not the expanded value.
Proposed-edit: after "Like any text value it shows in the command line (#41 Residuals \"Secrets in arguments\")" add
"; a `token` given with `--query` (`/runners/managers`, `/jobs/:id/artifacts`, `/jobs/:id/runtime_environment_key`)
is also in the URL that an error or a 429 warning quotes on standard error".

### D1 — "Steps 1 and 2 read the template alone" overstates step 1
Severity: D
Location: design.md § D1 "The functions", `expand`
Defect: step 1 also reads whether each group parameter has a value. It reads presence, not text, and the security
argument depends on that distinction.
Proposed-edit: replace "Steps 1 and 2 read the template alone." with "Steps 1 and 2 read the template's text alone;
of a value, step 1 reads only whether it is given."

CLEAN

Verdict: READY
