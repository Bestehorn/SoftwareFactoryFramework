# DevOps / IaC review — issue #44, design iteration 01

No IaC, no deploy, no CI configuration and no toolchain file in D9's list; the new suites run in `.github/workflows/ci.yml`
`verify`, leg `tests`. The E2E deferral to #11 is tracked by #11's open work item "Real-GitLab integration tests" and
involves no human step.

### C1 — Operability says a promotion makes sessions here run the GitLab wrapper; it is never installed here
Severity: C
Location: design.md § Operability
Defect: "a session here runs the product wrapper only after a release is promoted" does not hold for this wrapper:
`config/toolchain.json` `not_installed` lists `src/payload/scripts/gitlab_wrapper.py` ("the repository is on GitHub"),
and `docs/forLLMConsumption.md` says the same ("Not installed here: the repository is on GitHub"), so no promotion
installs it in this repository.
Proposed-edit: replace the section's sentence with "Not applicable — nothing deploys, and `gitlab_wrapper.py` is not
installed in this repository (`config/toolchain.json` `not_installed`: the repository is on GitHub); the change reaches a
GitLab project only when that project installs a release."

CLEAN

Verdict: READY
