# DevOps / IaC review — issue #43, design iteration 01

Lane: devops-iac-reviewer. Subject: `requirements.md`, `design.md` (Testing Strategy, Operability, D8).

No IaC, no deploy, no configuration or migration change. The new tests F, R, K (`src/payload/test/`) and P, N
(`test/`) are inside `pyproject.toml` `testpaths`, which CI's `verify` leg `tests` runs through
`scripts/run_checks.py --group tests`. `hypothesis` is in the `dev` extra that CI installs. No file of D8 is in
`config/toolchain.json` `files`. `src/payload/scripts/gitlab_wrapper.py` is `not_installed` ("the repository is on
GitHub"), and no `scripts/gitlab*` exists. A route-prefix refusal takes `call_operation`'s path: `logger.error`
to standard error, `EXIT_REFUSED`, nothing sent. The E2E statement is accurate. #11 is open, and its work item
"Real-GitLab integration tests" is unticked. This repository has no GitLab instance (`not_installed`
`templates/config/*`: "no GitLab"). So the automated check stops at the API boundary in CI with no human step, as
`always-test-e2e.md` allows. The Operability claim about Git Bash holds on this host. A native Python received
`/packages/npm` as `'C:/Program Files/Git/packages/npm'` and `--route-prefix=/packages/npm` rewritten the same
way, while `/projects/:id/packages/npm`, `/groups/:id/-/packages/npm`, `/projects/:id/packages/debian` and
`/groups/:id/-/packages/nuget` arrived unchanged.

### C1 — The #40 ordering statement does not say "merged"
Severity: C
Location: requirements.md § header ("Depends on #40"); design.md § header ("this branch rebases onto #40")
Defect: Both artefacts say the branch "rebases onto #40 before its implementation waves". `prompt.md` says "once #40
  lands". On GitHub, #43's only recorded blocker is #41, which is closed (`get-issue-dependencies 43`), and the wrapper
  has no subcommand that adds a dependency. That leaves this text as the only record of the ordering. As written, it
  also allows a rebase onto #40's unmerged branch, which today holds only spec commits (43c7a18). That would put #40's
  commits into #43's PR, and merging #43 would then land #40's code before #40's own verification.
Proposed-edit: in requirements.md, replace "the branch rebases onto #40 before its implementation waves (DL-001)" with
  "the branch rebases onto `origin/main` once #40's PR has merged, before its implementation waves (DL-001)". In
  design.md, replace "this branch rebases onto #40 before its implementation waves (DL-001)" with "this branch rebases
  onto `origin/main` once #40's PR has merged, before its implementation waves (DL-001)".

CLEAN

Verdict: READY
