# Best-practice review — iteration 01 (whole-artefact)

Lens: the change's external technology choices checked against the official docs: gitlab.com REST and GraphQL, git
credential helpers, GitHub Actions contexts and secrets, pytest configuration. Sources: `docs/api-reference/gitlab/`,
then the live pages and gitlab-org/gitlab `master` source, all fetched 2026-11-22. No MCP documentation server covers
GitLab, git, GitHub Actions or pytest, so official web documentation was the source.

Quote check: the three quotes the author did not fetch match the live pages word for word. These are the
personal-access-token username rule (docs.gitlab.com/user/profile/personal_access_tokens/), the service-account Owner
sentence (docs.gitlab.com/user/profile/service_accounts/, page tier "Free, Premium, Ultimate", up to 100 per top-level
group on gitlab.com) and "Project creation (`POST /api/v4/projects` and UI) for a user | 200 requests each day"
(docs.gitlab.com/user/gitlab_com/rate_limits/). Every other quote I checked also matches:
- the delete-a-project text, the 30-day retention, `permanently_remove` "Disabled on GitLab.com and Dedicated";
- `namespace_id`, `initialize_with_readme` and `auto_devops_enabled`;
- the `active` listing attribute and the mergeability sentences;
- the `api` scope, the slug rule, gitrepository-layout, `needs.<job_id>.result` and dereference syntax;
- pytest's configfile precedence and Python's `surrogateescape`.

The source matches too:
- `suffixed_identifier` and "has already been marked for deletion" are in `mark_for_deletion_base_service.rb`;
- `lib/api/projects.rb` `delete_project` returns 400 with that message for a project that is already marked;
- `lib/api/entities/project.rb` always exposes `marked_for_deletion_on`, with no `if:`.

### B1 — The merge-request records test reads the commits list before GitLab has created the merge request diff
Severity: B
Location: design.md § D6, table row F:records `test_the_merge_request_records`
Defect: The row asserts "one item, `id` the pushed commit" from `call ai-coding#retrieve-merge-request-commits` right
after `mr create`. GitLab builds the merge request diff that this endpoint lists only after the creation has answered.
So on a correct wrapper the answer can be an empty list.
Source:
- docs.gitlab.com/api/merge_requests/ (2026-11-22) lists `preparing` as "Merge request diff is being created" and says
  `diff_refs` is "Empty when the merge request is created, and populates asynchronously". Its "Preparation steps" begin
  "Create the diff".
- gitlab-org/gitlab `app/services/merge_requests/create_service.rb`: `before_create` sets
  `merge_request.skip_ensure_merge_request_diff = true`, and `after_create` queues `NewMergeRequestWorker`.
- `lib/api/merge_requests.rb`: the commits endpoint reads `merge_request.merge_request_diff.commits(...)`.
- `app/models/merge_request.rb`: `merge_request_diff` falls back to `MergeRequestDiff.new(merge_request_id: id)` while
  no diff is saved.
Material-because: AC-8.3 (the Merge requests API record "asserted" against "what the test knows in advance", AC-8.1).
Failure class: wrong-behaviour. The GitLab forge job fails intermittently with no regression in the wrapper, and the
AC-5.4 verdict turns red.
Proposed-edit: in that row, replace "`push_branch`, `mr create` (setup);" with "`push_branch`, `mr create`,
`wait_until_checked` (setup: GitLab creates the merge request diff, which the commits record lists, after the creation
answers — `preparing`, docs.gitlab.com/api/merge_requests/);". In Overview "Deviations", replace "the merge-request
test waits for GitLab's asynchronous mergeability check (D6)" with "the merge-request tests wait for GitLab's
asynchronous preparation and mergeability check (D6)". The edit reuses D10 `wait_until_checked` unchanged. That helper
already waits past `preparing`.

### C1 — The `Project.workItems` residual names a deprecation the field does not have
Severity: C
Location: design.md § Residuals, the `graphql#Project.workItems` bullet
Defect: The field is not deprecated. It is an experiment.
Source:
- gitlab-org/gitlab `app/graphql/types/project_type.rb` defines `field :work_items, ... experiment: { milestone: '15.1' }`
  with no `deprecated:` (2026-11-22).
- The "**deprecated** in 15.9" in the reference's Notes cell belongs to one argument of the field,
  `requirementLegacyWidget: RequirementLegacyFilterInput (**deprecated** in 15.9)`
  (`docs/api-reference/gitlab/graphql/objects-i-p.md`, the `Project` `workItems` row).
Material-because: clarification only. The real exposure is the field's experiment status, and experiments "can change
or disappear without notice" (`docs/api-reference/gitlab/graphql/conventions.md`).
Proposed-edit: replace the bullet with "`graphql#Project.workItems` is an experiment since 15.1 (gitlab-org/gitlab
`app/graphql/types/project_type.rb`), which GitLab may change without notice; a change would fail F:graphql until the
record follows it." The same misreading sits in a comment in `gitlab_api/graphql_only.py`, which this change does not
edit. It is a findings-ledger row, not part of this spec.

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY — A 0, B 1, C 1, D 0
