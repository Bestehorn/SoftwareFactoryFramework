# spec-review-agent — design review, iteration 01 (issue #40, tier M)

Lane: completeness, consistency, traceability. Read: requirements.md, design.md, DL-001..DL-006, prompt.md, the
issue body (wrapper `get-issue 40`), `registry.py`, `commands/call.py`, both family modules, N, V, `rest/openapi-only.md`,
`rest/deploy.md`, `conventions.md`. Checked against the reference: 270 index rows, one Reference each. Every `*name`
has a row. No `query`/`body`/`form` row names a `:name` of its path. The eight paged IDs of D4 and the five FILE rows of
D4 "The uploads" match the tables. Every ID the design cites is a Reference of the index. No existing record path holds
`*`, `(` or `\` (UB-4). #43 can reuse the glob form: its pending `*id`, `*distribution` and `*path` keys need no further edit.

### A1 — Three upload records are specified as multipart, but GitLab stores the whole request body of those routes as the file
Severity: A
Location: requirements.md § AC-3.2; design.md § D4 "The uploads"; design.md § Correctness Properties AC-3.2
(F `test_an_upload_sends_the_file_as_its_part`)
Defect: AC-3.2 sends `--file` as a `multipart/form-data` part for `openapi-only#upload-package-file`,
`openapi-only#upload-terraform-module-package-file` and `openapi-only#create-or-update-a-terraform-state`. GitLab
Workhorse sends those routes through `requestBodyUploader`, which saves the raw request body as the file and passes no
body fields to Rails. A call as specified therefore stores the multipart envelope (boundary lines, part headers, the
file) as the package file or the Terraform state, and drops `-f status=…` and `-f select=…`. F's oracle would lock that
behaviour in.
Material-because: wrong-behaviour and data-loss. Evidence:
- `gitlab-org/gitlab` `workhorse/internal/upstream/routes.go` routes `PUT …/packages/generic/`,
  `PUT …/packages/terraform/modules/` and `POST …/terraform/state/.*` (state lock and unlock have their own route) to
  `requestBodyUploader`.
- `workhorse/internal/upload/body_uploader.go` `RequestBody`: "store the request body to a location … then forwards the
  request to gitlab-rails without the original request body".
- `conventions.md` "Generic packages": "The body is the raw file bytes (curl `--upload-file`), not multipart".
- GitLab docs, Terraform module registry: `--upload-file path/to/file.tgz`.
- `POST /jobs/:id/artifacts` goes to `upload.Artifacts`, a multipart handler, so `openapi-only#upload-job-artifacts` is
  right as specified.

The requirements Residual records the conflict, but AC-3.2 resolves it in the direction GitLab does not accept.
Proposed-edit: the issue already names this form. Its Tier line reads "a design choice (the glob, optional-segment and
raw-body forms part 1 left to #15)", and its first work item is "the glob, optional-segment and raw-body request forms".
So the edit carries out the ask; it adds nothing beyond it. Replace AC-3.2 with:
"AC-3.2 WHEN a call gives `openapi-only#upload-job-artifacts` a `FILE` attribute with `--file`, the wrapper SHALL send
it as the `multipart/form-data` part that attribute names, with every other body attribute as a form field (#41 AC-1.3).
WHEN a call gives `--file file=PATH` to `openapi-only#upload-package-file`,
`openapi-only#upload-terraform-module-package-file` or `openapi-only#create-or-update-a-terraform-state`, the wrapper
SHALL send the file's bytes as the whole request body, with no multipart envelope."
Then:
- delete the Residual "Raw-bytes body" and DL-004's rejected alternative;
- design D4 "The uploads" names the two groups, and D1/D6 name the body form that `registry.encode` and
  `transport.request_body` read;
- F `test_an_upload_sends_the_file_as_its_part` gets one oracle per group: for the raw group, the body equals the file's
  bytes and carries no boundary.

If the conductor keeps AC-3.2 frozen, the fallback is:
- restrict AC-3.2, D4 "The uploads" and F's multipart oracle to `openapi-only#upload-job-artifacts`;
- state in `families/openapi_only.py`'s docstring and in Residuals that `call --file` on the other three stores the
  multipart envelope (Workhorse `requestBodyUploader`);
- route that, with this evidence, as one issue rather than a ledger row.

### C1 — `deploy#send-the-file`: the sources disagree on the body form
Severity: C
Location: requirements.md § AC-3.2; design.md § Correctness Properties AC-3.2 (G
`test_the_upload_sends_the_file_as_its_part`)
Defect: Workhorse routes `PUT …/packages/ml_models/` to `requestBodyUploader` (`routes.go`). GitLab's Model registry API
page shows the opposite: `curl --request PUT … --form "file=@model.pkl"`. G pins multipart.
Proposed-edit: add one Residuals line: "`deploy#send-the-file` follows `rest/deploy.md` (multipart `file`); Workhorse
routes `/packages/ml_models/` through its request-body uploader, so the multipart form is unproven until #11's
real-instance run."

### C2 — The gating check covers less than #41's delegated class
Severity: C
Location: requirements.md § UB-4; design.md § D4 last paragraph and § Security Considerations "Gates"
Defect: #41 design.md Residuals delegates to each slice "A record that commits to or merges into a branch, or creates an
issue". UB-4 and D4 check only "merges a merge request or creates an issue". The design takes no position on
`openapi-only#create-a-ci-configuration-merge-request` (`POST /projects/:id/create_ci_config`; its heading names a
merge request it opens) or on `openapi-only#import-a-project-from-a-git-url`.
Proposed-edit: add to "Gates": "No record of this change merges into a branch. `create-a-ci-configuration-merge-request`
opens a merge request on a new branch, and `import-a-project-from-a-git-url` fills the repository. Neither has a
compatibility subcommand that a gate judges, so neither is in `GATED_OPERATIONS`; running one is the caller's decision
(#41 Security 'Destructive operations')."

### D1 — `expand`'s own docstring is missing from the change list
Severity: D
Location: design.md § D1 "Nothing else in the module changes but two docstrings"; § D6 row D1
Defect: `expand`'s docstring says "every `:name` replaced by its value as ONE percent-encoded segment". D6 names only
the module's bullet and `placeholders`' docstring, so this one would go stale.
Proposed-edit: in D1 and D6, replace "two docstrings: the module's `expand` bullet and `placeholders`'" with "three
docstrings: the module's `expand` bullet, `expand`'s and `placeholders`'".

### D2 — The reuse list leaves out `*id`
Severity: D
Location: design.md § D1 "Reuse"
Defect: `package`'s pending `/virtual_registries/…/cache_entries/*id` keys are glob keys too.
Proposed-edit: "(`*distribution`, `*artifact_path`, `*path`, `*id`)".

1 A, 0 B: NOT-CLEAN (1 A, 0 B).

Verdict: NOT-READY
