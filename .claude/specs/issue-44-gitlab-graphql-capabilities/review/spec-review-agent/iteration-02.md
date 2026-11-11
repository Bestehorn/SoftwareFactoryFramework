# Design review — iteration 02 (delta) — lane spec-review-agent

Delta reviewed: `design.md` against `review/review-latest.md` B1–B3 and its C/D list, with DL-006.

Closed. B1: the `gitlab_api/` bullet of `docs/forLLMConsumption.md` holds none of `call graphql#`, `--file NAME=PATH`,
`Upload` today, so AC-5.2's test is red before D8's sentence and green after it. B2: the whole-ID rule rejects
`graphql#workItem` inside `graphql#workItemsByReference` and `graphql#Query.vulnerability` inside
`graphql#Query.vulnerabilities`, and accepts an ID before a space, a comma or a sentence-ending `.`. B3:
`transport.request_body` takes `form: Sequence[Pair]`, `json_body` and `files: Sequence[Tuple[str, Path]]` (part
names), and with files returns `multipart_body` (form parts, then one `_file_part` per file) under a fresh boundary
with `multipart/form-data; boundary=…`, so D4's `operations`/`map` pairs and `str(i)` part names fit it as written; the
job-token check in `Transport.graphql` stays ahead of it, and `_file_part`'s `GitLabAPIError` exits 1 (AC-2.4). DL-006
supersedes only DL-004's body clause. All fifteen C/D edits are present. `call_values` already branches on
`GraphQLOperation`, so spec C1's text leaves a REST `--file` as it is (UB-1.2). `workItemsCsvExport`'s input fields
equal `workItemExport`'s (`mutations-j-w.md`). `ci_pipeline_variables_minimum_override_role` is the name GitLab Docs
"CI/CD variables" "Restrict pipeline variables" gives. `config/toolchain.json` `not_installed` names
`gitlab_wrapper.py`. The AC mapping is unchanged and complete.

### C1 — D8's environment-text rule names a string that the tree and D9 contradict
Severity: C
Location: design.md § D8 "Module docstrings", last bullet
Defect: "No file of the package contains `environ` or `getenv`" is false of the tree: `transport.py`'s module
docstring holds "environment" and `families/verify.py` holds `/protected_environments` paths, and D9 keeps `families/*`
untouched. The text P scans for is `os.environ` and `getenv` (`ENVIRONMENT_READS`). It matches `environ` only as an AST
name. The D1 fix bound this sentence to P, so it now credits P with a check P does not make.
Proposed-edit: "No file of the package contains `os.environ` or `getenv` (P `test_standard_library_only`, UB-2.2,
reads the docstrings too)."

### D1 — D7's citation of the Residuals does not match the Residuals
Severity: D
Location: design.md § D7 "What #11's test project cannot exercise", closing sentence; § Residuals "What Q and #11
leave"
Defect: D7 cites the Residuals for "a CI configuration for `graphql#pipelineCreate` and
`graphql#Project.ciPipelineCreationRequest`, Git LFS for `graphql#designManagementUpload`". The Residuals bullet names
`graphql#pipelineCreate` only, and it adds "work items in a personal namespace", which D7 leaves out.
Proposed-edit: in D7, replace "(Residuals \"What Q and #11 leave\": a CI configuration for `graphql#pipelineCreate` and
`graphql#Project.ciPipelineCreationRequest`, Git LFS for `graphql#designManagementUpload`)" with "(Residuals \"What Q
and #11 leave\")". In the Residuals bullet, replace "a CI configuration for `graphql#pipelineCreate`" with "a CI
configuration for `graphql#pipelineCreate` and `graphql#Project.ciPipelineCreationRequest`".

### D2 — Security Considerations cites the wrong `conventions.md`
Severity: D
Location: design.md § Security Considerations "Destructive or costly operations"
Defect: Everywhere else, the design's `conventions.md` means `docs/api-reference/gitlab/graphql/conventions.md`
(Sources), and that file does not hold `ci_pipeline_variables_minimum_override_role`. The REST
`docs/api-reference/gitlab/conventions.md` does, in "Versioning and deprecations", as the replacement of
`restrict_user_defined_variables`.
Proposed-edit: replace "`conventions.md` names the projects attribute" with
"`docs/api-reference/gitlab/conventions.md` \"Versioning and deprecations\" names the projects attribute".

CLEAN
Verdict: READY
