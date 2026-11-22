# DevOps / IaC review — issue #11 design, iteration 01 (whole artefact)

### C1 — The rate-limit and leftover notes leave out a failed teardown
Severity: C
Location: design.md § Operability (Rate limits, Leftovers)
Defect: "A `429` that outlasts the transport's retries is a `GitLabRateLimitError`, exit 1: the run creates nothing and
deletes nothing" is true only for a 429 at D9 steps 4 to 6. A 429 at a test fails that test. A 429 at the teardown's
deletion, like any other non-zero exit there, raises `ForgeCommandError` (D9 step 8, `delete_ephemeral`) and leaves
this run's project unmarked. Leftovers does not name that leftover: it names only interrupted runs.
Proposed-edit: Rate limits, last sentence: "A `429` that outlasts the transport's retries is a `GitLabRateLimitError`,
exit 1. At the sweep, the group read or the creation, the run fails before it creates its project. At a test, that
test fails. At the teardown, it leaves a leftover (Leftovers)." Leftovers, first clause: "An interrupted run (a
cancelled CI run, a local Ctrl-C), or a teardown whose deletion exits non-zero (D9 step 8), leaves its project
unmarked, ...".

### C2 — D5 no longer says how runs of different refs coexist
Severity: C
Location: design.md § D5
Defect: D5 leaves `concurrency` unchanged, but unlike #10 D5's "Concurrency." bullet it says nothing about runs of
different refs. The group `ci-${{ github.ref }}` lets those runs proceed together against the one test group. The
mechanisms that keep them apart (D4, AC-3.2, D9 `delete_leftover`'s `404`/`400` handling) are not named where the job
is designed.
Proposed-edit: add to D5's bullets: "**Concurrency.** The group `ci-${{ github.ref }}` applies: a superseded
pull-request run is cancelled (Operability, Leftovers), and a run on `main` never is. Runs of different refs proceed
together. Their run ids keep their projects apart (D4), and each sweep spares a project a day old or less (AC-3.2).
When two sweeps select the same leftover, it is marked once, and the later deletion's `404` or `400` counts as handled
(D9 `delete_leftover`)."

### C3 — The token's expiry is named nowhere (residual)
Severity: C
Location: design.md § Residuals; requirements.md AC-9.1
Defect: The service account's personal access token expires. The docs say: "If you do not enter an expiry date, the
expiry date is automatically set to 365 days later than the current date... By default, this date can be a maximum
of 365 days later than the current date" (docs.gitlab.com/user/profile/service_accounts/). From that date every
`forge-gitlab` job fails, and so does every `report`, until `SFF_GITLAB_TEST_TOKEN` and the local file hold a new
token. Neither the Residuals nor AC-9.1's note list names this; #10's Residuals carried the GitHub version.
Proposed-edit: Residuals, add: "The test token expires at most 365 days after its creation
(docs.gitlab.com/user/profile/service_accounts/). An expired token fails every `forge-gitlab` job until
`SFF_GITLAB_TEST_TOKEN` and the local file hold a new one; the setup note does not name the rotation."

### C4 — Limits not in effect yet that concurrent runs would share (residual)
Severity: C
Location: design.md § Operability (Rate limits); § Residuals
Defect: The Rate limits bullet names only the creation limit ("Project creation (`POST /api/v4/projects` and UI) for
a user | 200 requests each day", docs.gitlab.com/user/gitlab_com/rate_limits/), and it is correct. The same page
lists Free limits that are "proposed and not in effect yet": "100 each minute" per user, and "Each Git clone, fetch,
or push counts as one request". Separately, gitlab-org/gitlab `lib/api/projects.rb` checks a per-user
`project_delete_api` limit on `DELETE /projects/:id` behind the `gitlab_com_derisk` flag
`group_and_project_delete_rate_limit` (milestone 19.6, `default_enabled: false`). Concurrent runs of the one service
account would share both limits. The transport retries a REST `429`; D10's `push_branch` and the fixture's fetch do
not.
Proposed-edit: Residuals, add: "gitlab.com lists proposed Free limits not yet in effect (100 requests a minute per
user, git included), and GitLab has a per-user project-deletion limit behind the flag
`group_and_project_delete_rate_limit`. Concurrent runs of the one service account would share both."

### D1 — The workspace residual says "only"
Severity: D
Location: design.md § Residuals (interrupted local run)
Defect: "is removed only by `/close-session`'s temporary-directory sweep" claims more than the design shows. #10
settled on wording that states what this change does not do and where the sweep applies (#10 devops iteration-02 D1
and iteration-03 D1).
Proposed-edit: "Nothing in this change removes the workspace an interrupted local run leaves in the temporary
directory. In a session, whose temporary directory is the scoped `tmp/os-temp`, `/close-session`'s
`reap_agent_temp.py --scoped-temp tmp/os-temp --apply` empties it, as for #10."

Counts: 0 A, 0 B, 4 C, 1 D. CLEAN

Verdict: READY
