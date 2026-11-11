# Security review — design iteration 01 (issue #44)

Checked, no finding:

- `--file NAME=PATH`. A name outside `registry.upload_variables` is refused by `check_parameters` (step 4) before any
  request (UB-1.2's G test). Part names are `str(i)`. The file name is `path.name` through `multipart_name`, which
  escapes `"`, CR and LF, so no header is injected. The boundary is `secrets.token_hex`. The multipart POST goes through
  `_send`'s origin check, and `CredentialStrippingRedirectHandler` follows no POST redirect. A `-f`/`-F` value for an
  `Upload` variable is sent as JSON and is never read as a path. That a caller can send any local file to the
  configured origin is #41's routed residual "Secrets in arguments".
- Variables from argv. Documents are constants, and `-f`/`-F` names are limited to `registry.variables`. Values go
  through `json.dumps`. No subcommand in `gitlab_wrapper.py` or `gitlab_api/commands/` takes a document, so no GraphQL
  the caller writes reaches GitLab. Refusal messages render names only (`_split`, `check_parameters`).
- Refusal of `workItemCreate`/`workItemsCsvImport`. `refuse_gated` runs before `registry.lookup`, and nothing before
  `call_operation` sends a request (`gitlab_wrapper._run`). D6 makes membership, not `.get`, the test, which a `None`
  value requires. Another record that runs `workItemCreate` must carry the ID `graphql#workItemCreate` (Q's mutation
  rule), and a duplicate ID is `lookup`'s refusal; an alias is a token `read_document` rejects. `WorkItemUpdateInput`
  and `WorkItemWidgetHierarchyUpdateInput` (`childrenIds`, `parentId`) only edit or link existing items. No declared
  REST record creates an issue except the gated `plan#create-an-issue`: `/issues/:issue_iid/clone` and `/move` are on
  `plan.PENDING`.
- Credentials. `_load_config` is unchanged and no option is added. `Transport.graphql` refuses a job token before the
  body is built, which T asserts happens before the file is read. Only `Authorization: Bearer` carries the token.
  `GitLabAPIError` text holds the URL and the body, never the token.
- Gates. `gate_filing.CREATE_RE` does not match `call graphql#…`, and D6 closes that gap. `gate_merge_steward` refuses
  `mr merge` and trunk pushes by their words, whatever protection the host has. So the branch-rule mutations DL-002
  keeps callable open no trunk write the gate does not judge. No record in this change merges or commits to a branch.
- Output. `print_json` keeps `ensure_ascii=True`.

### C1 — D6 narrows the gated class #41 set for `GATED_OPERATIONS`
Severity: C
Location: design.md § D6, last bullet
Defect: D6 has the `GATED_OPERATIONS` comment name its class as "a record that merges, or that creates an issue or
another work item". That drops "commits to" from #41's class: "a record that commits to or merges into a branch, or
creates an issue" (#41 design D8 exceptions row and Residuals, worded by #41 security iteration-02 C1). A later
`create`-family slice that adds a commit or file-write record will read the narrower comment.
Proposed-edit: replace "a record that merges, or that creates an issue or another work item" with "a record that
commits to or merges into a branch, or that creates an issue or another work item (#41 D8)".

### C2 — `pipelineCreate`'s `variables` override the project's CI/CD variables, and Security Considerations does not say so
Severity: C
Location: design.md § Security Considerations "Destructive or costly operations"; § D1 mutation table
`graphql#pipelineCreate`
Defect: The record passes `$variables: [CiVariableInput!]`. GitLab Docs "CI/CD variables" says pipeline variables "can
override variables with the same name from project, group or instance settings and from `.gitlab-ci.yml`". So a call
on the default branch sets what trusted jobs read. In `templates/ci/gitlab-delivery.gitlab-ci.yml.template`, for
example, `MERGE_STEWARD == "redeploy"` on the default branch admits the deploy jobs and `delivery-verdict`. "It runs
CI" does not convey this. GitLab's control is `pipeline_variables_minimum_override_role`, and that defaults to
`no_one_allowed` only for new projects in new namespaces on GitLab.com.
Proposed-edit: append to the bullet: "`pipelineCreate`'s `variables` are pipeline variables, which take precedence over
the project's CI/CD variables (GitLab Docs "CI/CD variables"): a call on the default branch sets what its jobs read,
the delivery template's `MERGE_STEWARD` included. The project's `pipeline_variables_minimum_override_role` is the
control."

### D1 — The residual says `gate_merge_steward` relies on branch protection
Severity: D
Location: design.md § Residuals "Branch rules stay callable (DL-002)"
Defect: The `gate_merge_steward` docstring says "on a host plan that cannot enforce branch protection this gate is the
enforcement". The gate refuses trunk pushes by their words and does not rely on the branch's protection.
Proposed-edit: replace "the branch `gate_merge_steward` relies on" with "the trunk the merge steward alone writes".

CLEAN

Verdict: READY
