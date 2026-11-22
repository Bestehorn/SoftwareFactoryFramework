# Best-practice review — iteration 02 (delta, c6cb2ad..5e04f25)

Lens: the delta's claims about gitlab.com, git, GitHub Actions, pytest and the Python standard library, checked against
the live pages and gitlab-org/gitlab `master` source, fetched 2026-11-22. No MCP documentation server covers these
technologies, so the official web documentation and source were used.

Fix sites:
- B1 is closed. The F:records `test_the_merge_request_records` row now runs `wait_until_checked` before reading the
  commits, and the Overview "Deviations" sentence names the preparation. The source confirms that waiting past
  `preparing` is enough:
  - `app/services/merge_requests/create_service.rb` `after_create` calls `issuable.mark_as_preparing` before the
    creation answers.
  - `app/services/merge_requests/after_create_service.rb` `execute` runs `ensure_merge_request_diff` before
    `check_mergeability` calls `mark_as_unchecked`.
  - `app/models/merge_request_diff.rb` `after_create :save_git_content` saves the commits along with the diff.
- C1 is applied. `app/graphql/types/project_type.rb` `field :work_items` has `experiment: { milestone: '15.1' }` and no
  `deprecated:`, which matches the new Residuals bullet.

I checked every new citation in the delta, and each one matches:
- `lib/api/entities/project.rb`: `expose :marked_for_deletion_at, as: :marked_for_deletion_on, documentation: {...}`,
  with no `if:`. `lib/api/groups.rb` `present_projects` uses `Entities::Project` unless `simple` is set, and D9 does not
  send `simple`.
- docs.gitlab.com/user/gitlab_com/rate_limits/ says three things the residual relies on:
  - "The limits in this section are proposed and are not in effect yet".
  - The limits "apply for each user and for each top-level group".
  - They "apply to API requests, web requests, and authenticated Git over HTTPS requests".
- `lib/api/projects.rb` `delete ":id"`: `if Feature.enabled?(:group_and_project_delete_rate_limit, current_user)`, then
  `check_rate_limit!(project_delete_rate_limit_key, scope: { user: current_user })`.
- The keyword forms the design uses are valid:
  - pytest `src/_pytest/monkeypatch.py`: `def setitem(self, dic: Mapping[K, V], name: K, value: V)`, so
    `setitem(dic=..., name=..., value=...)` binds.
  - `json.dumps(obj=...)` and `subprocess.run(args=[...])` both ran in the project venv.
- `docs/api-reference/gitlab/operations-index.md`: `openapi-only#the-nuget-symbol-file-download-endpoint` is
  `GET /groups/:id/-/packages/nuget/symbolfiles/...`, a group record, and `...-endpoint-1` is the project record. Both
  are marked "source: `openapi_v2.yaml` only".
- `.github/workflows/ci.yml` has `group: ci-${{ github.ref }}` and
  `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`, as the D5 bullet says. The bullet's claim about
  `main` is C1 below.

### C1 — The D5 concurrency bullet says a run on `main` is never cancelled; GitHub cancels a pending one
Severity: C
Location: design.md § D5, the "Concurrency" bullet
Defect: `cancel-in-progress: false` spares only a running run. GitHub's default still cancels a waiting one: "By
default, any existing `pending` job or workflow in the same concurrency group will be canceled and the new queued job
or workflow will take its place." So a pending `main` run is replaced by the run of a newer push.
Source: docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
(2026-11-22). The page also says the `queue` property defaults to `single`: "At most one job or workflow run can be
`pending`".
Material-because: clarification only. A pending run has not started, so it creates no project, and the Leftovers
reasoning still holds.
Proposed-edit: replace "cancels a superseded pull-request run (Operability, Leftovers), never a run on `main`." with
"cancels a superseded running pull-request run (Operability, Leftovers), never a running one on `main`; a pending run
that a newer one replaces has not started, so it creates nothing (docs.github.com "Control workflow concurrency")."

CLEAN

Verdict: READY — A 0, B 0, C 1, D 0
