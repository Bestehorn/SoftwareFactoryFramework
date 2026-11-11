# Security review — design iteration 01 (issue #41)

Checked, no finding (the dispatch's questions):

- Gated IDs. `cmd_call` step 1 refuses `ai-coding#merge-a-merge-request` and `plan#create-an-issue` before
  `registry.lookup`. `lookup` compares the ID exactly, so a variant in case or spacing is unknown (exit 2). The index
  has one row for `PUT /projects/:id/merge_requests/:merge_request_iid/merge` and one for `POST /projects/:id/issues`.
  V `family_problems` requires a record's key to sit on a row that carries the record's own Reference, so no second ID
  can map either key. No other record declared in `families/*.py` merges or creates an issue.
- GraphQL. `mergeRequestAccept` and `commitCreate` sit under "Available in both", not "Only in GraphQL"
  (`graphql/conventions.md`), so D8's rule (`capability` = the row's first cell) gives them no record. The routes that
  create issues are `workItemCreate` and `workItemsCsvImport`. C1 covers them.
- Path values. They are encoded with `quote(safe="")`, and `REFUSED_SEGMENTS` stops an empty, `.` or `..` value. The
  record fixes the method. `_send` refuses any other origin, and a `Link` next URL is one of the URLs it checks.
- Credential. The handling is unchanged: `_load_config`; one header to the configured origin; and
  `CredentialStrippingRedirectHandler`, which strips the credential on a cross-origin hop and raises on a redirect of
  anything but GET or HEAD, so a PUT or DELETE follows no redirect. Refusal texts hold names only (D2 "Parsing", D4).
- `--file`. The caller is the principal that can already read any file, so a traversal or a symlink crosses no
  boundary. See C4.
- Tests. `FakeGitLab` patches `https_open`, and `install_socket_guard` refuses `connect`. So N's call of every
  declared record, DELETE records included, reaches no network.

### C1 — The gated-records residual leaves out three trunk writers and two routes that create issues
Severity: C
Location: design.md § Residuals "Gated records"
Defect: These records are missing from the list a slice reads:
- Three trunk writers. `create#cherry-pick-a-commit` (`POST /projects/:id/repository/commits/:sha/cherry_pick`),
  `create#revert-a-commit` (`…/revert`) and `create#update-a-submodule-reference`
  (`PUT /projects/:id/repository/submodules/:submodule`) each commit to the required `branch` body attribute, the
  trunk included (`rest/create.md`).
- Two routes that create issues. `plan#move-an-issue` creates an issue in `to_project_id`. `workItemsCsvImport`
  ("Work item CSV import", "Only in GraphQL") creates them in bulk.

This is graded C because all of them are pending, so `call` reaches none of them in this change.
Proposed-edit: replace "Such records include `verify#add-a-merge-request-to-a-merge-train`, the multi-file commit and
repository-file writes of `create`, `plan#clone-an-issue`, and a GraphQL work-item creation." with "Such records
include `verify#add-a-merge-request-to-a-merge-train`; the multi-file commit, the repository-file writes,
`create#cherry-pick-a-commit`, `create#revert-a-commit` and `create#update-a-submodule-reference`, each of which commits
to the `branch` it is given; `plan#clone-an-issue` and `plan#move-an-issue`; and the GraphQL `workItemCreate` and
`workItemsCsvImport`."

### C2 — The residual says `create#delete-repository-branch` can delete the trunk, which GitLab refuses
Severity: C
Location: design.md § Residuals "Gated records", last sentence
Defect: The GitLab Branches API says this of "Delete repository branch": "Cannot delete the default branch or protected
branches." (https://docs.gitlab.com/api/branches/#delete-repository-branch). The generated `rest/create.md` section
carries no such note. "It deletes any branch, the trunk included" was carried over from #28's `git/delete-ref`, where
it is true, and it overstates this record's reach.
Proposed-edit: replace that sentence with "`create#delete-repository-branch`, declared since #13, deletes any branch
except the default and protected ones (Branches API: "Cannot delete the default branch or protected branches"),
through `call` as through `delete-branch`."

### C3 — "Destructive operations" leaves out #28's sentence about the permission prompt
Severity: C
Location: design.md § Security Considerations "Destructive operations"
Defect: `prompts/setup-claude.txt` allow-lists `Bash(python scripts/gitlab_wrapper.py:*)`, so a DELETE or PUT through
`call` runs with no permission prompt. #28's bullet says so. This design drops it, and "Differences from #28" names no
difference on this point.
Proposed-edit: after "whether to run one is the caller's decision under `continuous-work.md` Exception 1." insert "No
permission prompt comes first: the settings allow-list the wrapper as a whole."

### C4 — Residual: `--file` sends the wrapper's own credential file like any other path
Severity: C
Location: design.md § Security Considerations "Files"; § Residuals
Defect: `--file NAME=config/gitlab.json` passes D4, and `transport._file_part` then sends the bytes of the token file
as the part. Once a slice declares an upload record (`POST /projects/:id/uploads`, "Markdown uploads"), the token is
stored on the forge as an upload of the project. Refusing that path would be a guard outside the ask. The same reach
exists today through a Read followed by `-f`.
Proposed-edit: Residuals gains "**The credential file as a `--file`.** `call` sends `config/gitlab.json` or a
`credentials/` file like any other path. Refusing them is a guard outside this change, routed per
`issue-filing-discipline.md`."

Verdict: CLEAN
