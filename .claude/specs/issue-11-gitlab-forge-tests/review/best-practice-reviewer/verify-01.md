# Best-practice review — VERIFY pass 01 (delta, 83a1415..HEAD, `src test .github docs`)

Lens: how the implemented code uses gitlab.com REST and GraphQL, git, `subprocess`, pytest and GitHub Actions, checked
against the official docs and gitlab-org/gitlab `master` source, all fetched 2026-11-22. No MCP documentation server
covers these technologies, so I used the official web pages and source.

Checked and matching. Each of these is a fact from a source, not a finding:
- Project creation (`ephemeral.py` `_creation_arguments`): `namespace_id`, `initialize_with_readme` and
  `auto_devops_enabled` are body attributes of the create operation (`docs/api-reference/gitlab/rest/tenant-scale.md`).
  The wrapper's `-F` parses each value with `json.loads` (`commands/call.py` `json_member`), so it sends an integer and
  booleans. The project path in `config/gitlab.json` is encoded `group%2Fproject` (`registry.py`, `quote(..., safe="")`).
- Deletion: docs.gitlab.com/api/projects/ "Delete a project" says it "Marks a project for deletion", says "On GitLab.com,
  projects are retained for 30 days" and gives the prerequisite "You must be an administrator or have the Owner role
  for the project.". Those match `docs/forge-suite.md` and the table it carries.
- Mergeability (`UNDECIDED_MERGE_STATUSES`): `app/services/merge_requests/mergeability/detailed_merge_status_service.rb`
  returns `:preparing`, `:checking` and `:unchecked` before the checks. It returns `:approvals_syncing` only when the
  failed check is `:not_approved`, which a project without approval rules does not raise. Once those are past, a
  project with no pipeline gets `:mergeable`. So `test_a_merge_request_round_trip`'s `mergeable` assertion holds.
- The `sha` of a newly created merge request: `app/models/merge_request.rb` `diff_head_sha` falls back to
  `source_branch_head.try(:sha)` until the diff is persisted. So the creation answers the pushed commit.
- `mr merge` answering `merged`: `lib/api/merge_requests.rb` runs the immediate merge through
  `MergeRequests::MergeService...execute(merge_request)` synchronously, then calls `present merge_request`.
- Emoji reactions on `POST`/`GET /projects/:id/merge_requests/:merge_request_iid/award_emoji`, `name=thumbsup` and
  `awardable_type` `MergeRequest` match docs.gitlab.com/api/emoji_reactions/.
- Archive: docs.gitlab.com/api/repositories/ gives `GET /projects/:id/repository/archive[.format]`, lists `zip` among
  the formats and documents `sha`. The gitlab.com limit of "5 requests per minute" is not reached by the suite's one
  call per run.
- `Project.workItems`: in `docs/api-reference/gitlab/graphql/objects-i-p.md` the field is an experiment since 15.1.
  The fields the test reads (`iid` `String!`, `state` `OPEN`) match `objects-p-x.md` and `enums.md`.
- GitHub Actions:
  - `needs.forge-gitlab.result`, dereferenced with a hyphenated job id, evaluated to `failure` in run 45033382186
    (`evidence/regress/ci-45033382186-c389d46.txt`, the line `forge-gitlab job: failure`).
  - The secret is passed through one step's `env:`, and the checkout uses `persist-credentials: false`.
- pytest:
  - `scripts/run_tests.py` `build_command` adds no `-n` for `--workers 1`, so `worker_id` is `master`.
  - It adds no `-c`, so `test/forge_gitlab/pytest.ini` is the configfile, the same layout as `test/forge/pytest.ini`.
- `subprocess.run(args=..., stdin=DEVNULL, capture_output=True, timeout=..., check=False)` is valid.
  `-X sff_test_marker` and `sys._xoptions` follow the CPython command-line docs.
- `docs/forge-suite.md` setup steps against docs.gitlab.com/user/profile/service_accounts/:
  - The page tier reads "Free, Premium, Ultimate". Its path reads "In the left sidebar, select **Settings** > **Service
    accounts**", followed by **Add service account**.
  - The page says "Service accounts have limited access until you add them as members", which matches step 2.
  - The token is created with the vertical ellipsis, then **Manage access tokens**, then **Add new token**.
  - "By default, this date can be a maximum of 365 days later than the current date" matches "365 days ahead, GitLab's
    default maximum".
  - The Owner sentence is quoted word for word.
  - Both `api` quotes match docs.gitlab.com/security/tokens/access_token_scopes/, including the footnote "For a personal
    access token, `api` also grants complete read and write access to the registry and repository through
    Git-over-HTTP."

### C1 — The group read sends `with_projects`, a parameter GitLab has deprecated
Severity: C
Location: `test/forge_gitlab/ephemeral.py` § `read_test_group` / `WITH_PROJECTS_PARAMETER`
Defect: docs.gitlab.com/api/groups/ "Retrieve a group" lists `with_projects` as "(Deprecated, scheduled for removal in
API v5. To get the details of all projects in a group, use the list a group's projects endpoint.)". The code does not
say this.
Material-because: clarification only. On API v4 the parameter still keeps the answer free of the projects' details.
Grape ignores an undeclared parameter, and `id` and `full_path` are read either way, so no behaviour depends on it.
Proposed-edit: in the comment above `GROUP_READ`, after "(docs.gitlab.com/api/groups/, "Get a single group")", add
"; `with_projects=false` keeps its answer free of the projects' details on API v4, where GitLab has deprecated the
parameter for removal in v5".

### C2 — The new job pins actions that the runner reports as Node 20 deprecated (residual)
Severity: C
Location: `.github/workflows/ci.yml` § `forge-gitlab`
Defect: Run 45033382186 logs "Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to
run on Node.js 24: actions/checkout@v4, actions/setup-python@v5". github.blog changelog 2025-09-19 says Node 20 is
removed from the runner on 2026-09-23.
Material-because: residual outside the ask. The job copies the pins of `verify`, `forge` and `report`. The actions still
run, forced onto Node 24, and the job's checkout and setup steps succeeded in that run. Bumping the pins is a
workflow-wide change.
Proposed-edit: none in this change. Record it under `## Residuals` as one findings-ledger row: "ci.yml pins
checkout@v4/setup-python@v5/upload- and download-artifact@v4, which the runner reports as Node 20 deprecated".

### D1 — The F:graphql docstring repeats the misreading that iteration 01 C1 corrected in the design
Severity: D
Location: `test/forge_gitlab/forge_graphql.py` § module docstring, the "The reference's Notes for `Project.workItems`"
sentence
Defect: The Notes cell does read "**deprecated** in 15.9; experiment since 15.1". But the deprecation belongs to the
argument `requirementLegacyWidget`, not to the field (design.md Residuals after iteration 01).
Proposed-edit: replace "The reference's Notes for ``Project.workItems`` read "**deprecated** in 15.9; experiment since
15.1": GitLab may change it" with "``Project.workItems`` is an experiment since 15.1 (the "**deprecated** in 15.9" of
the reference's Notes belongs to its argument ``requirementLegacyWidget``): GitLab may change it".

CLEAN

Verdict: READY — A 0, B 0, C 2, D 1
