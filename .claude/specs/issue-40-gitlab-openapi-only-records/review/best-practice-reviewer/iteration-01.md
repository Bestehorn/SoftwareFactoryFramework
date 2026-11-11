# Best-practice review, design iteration 01, issue #40

Sources, fetched 2026-11-11: GitLab `gitlab-org/gitlab@master` (`workhorse/internal/upstream/routes.go`,
`workhorse/internal/upload/body_uploader.go`, `lib/api/generic_packages.rb`, `lib/api/helpers/packages/npm.rb`);
docs.gitlab.com `api/packages/npm/`, `api/packages/terraform-modules/`, `api/model_registry/`; Mustermann `main`
(`mustermann/lib/mustermann/ast/compiler.rb`, `pattern.rb`, `README.md`); CPython `3.9` `Lib/http/client.py`. No MCP
documentation server covers GitLab or the Python standard library, so the official web sources were used.

## Findings

### A1 — Four upload records send multipart where Workhorse stores the raw request body as the file
Severity: A
Location: requirements.md § AC-3.2, § Introduction (the raw-body paragraph), § Residuals "Raw-bytes body"; design.md
§ D4 "The uploads", § D5 G's tests, § Correctness Properties AC-3.2
Defect: AC-3.2 sends the `file` of `openapi-only#upload-package-file`, `openapi-only#upload-terraform-module-package-file`,
`openapi-only#create-or-update-a-terraform-state` and `deploy#send-the-file` as a `multipart/form-data` part. GitLab
Workhorse routes `PUT …/packages/generic/`, `PUT …/packages/ml_models/`, `PUT …/packages/terraform/modules/` and
`POST …/terraform/state/.*` to `requestBodyUploader := upload.RequestBody(api, signingProxy, preparer)` (`routes.go`).
That handler "will store the request body … [and] forwards the request to gitlab-rails without the original request
body", through `destination.Upload(r.Context(), r.Body, r.ContentLength, "upload", opts)`. It has no Content-Type check
and no multipart parsing (`body_uploader.go`).
Material-because: wrong-behaviour (data-loss class). GitLab answers such a call 2xx, but the package file, model file or
Terraform state it stores is the whole multipart body (boundaries, part headers, the `status` and `select` parts), and
`status` and `select` never reach Rails. F `test_an_upload_sends_the_file_as_its_part` and G
`test_the_upload_sends_the_file_as_its_part` would pin that form as correct against the fake host.
Proposed-edit:
- requirements AC-3.2 → "WHEN a call gives `openapi-only#upload-job-artifacts` its `file` or `metadata` with `--file`,
  the wrapper SHALL send the file's bytes as the `multipart/form-data` part named by that attribute, every other body
  attribute a form field, as #41 AC-1.3 sends any `FILE` attribute." (Workhorse does read that route as multipart:
  `POST apiPattern+v4/jobs/[0-9]+/artifacts\z` → `upload.Artifacts`.)
- requirements Introduction, last sentence of the raw-body paragraph → "The job-artifacts record sends its entry's
  `file` row that way; the four uploads Workhorse reads as a raw body are Residuals."
- requirements Residuals, the "Raw-bytes body" bullet → "Raw-bytes body: GitLab Workhorse stores the whole request body
  as the file on `PUT …/packages/generic/`, `…/packages/ml_models/`, `…/packages/terraform/modules/` and
  `POST …/terraform/state/` (`workhorse/internal/upstream/routes.go`, `upload.RequestBody`). A `--file` call of
  `openapi-only#upload-package-file`, `openapi-only#upload-terraform-module-package-file`,
  `openapi-only#create-or-update-a-terraform-state` or `deploy#send-the-file` therefore stores the multipart body, not
  the file. These records are not working uploads until a raw body form exists in `registry.py`, `transport.py` and
  `call`, with its proof in N."
- design D4 "The uploads" → `openapi-only#upload-job-artifacts` is the one multipart upload; the other four are named
  with the restated Residual. The `openapi_only.py` docstring sentence on `--file` names the job-artifacts record only.
- design Correctness Properties AC-3.2 → F's parametrization covers `openapi-only#upload-job-artifacts` only (with
  `-f artifact_type=archive`); delete G `test_the_upload_sends_the_file_as_its_part` from D5, from Correctness
  Properties and from the AC-3.2 mapping row. G's typing test still pins the `file` `Param` (AC-1.3).

Why the design's sources do not settle this. The entry's "file upload (multipart/form-data)" note is how the OpenAPI
file renders a Workhorse file parameter. The Workhorse handler decides what the body means. Two documents agree with it:
docs.gitlab.com "Upload module" sends `--upload-file path/to/file.tgz`, and `conventions.md` "Generic packages" says "The
body is the raw file bytes (curl `--upload-file`), not multipart". The model-registry page's "Send the file" example
sends `--form "file=@model.pkl"`. Workhorse stores that body unparsed, so the example does not establish the multipart
form either.

The issue asked the raw-body question itself (requirements Introduction). Whether this change takes a raw body instead
of the restatement above is the ask owner's decision, not a reviewer's.

## Residuals (C, not gating)

- C1: `docs/api-reference/gitlab/conventions.md` "Other package formats" says Terraform modules upload as "(multipart
  `file`)". docs.gitlab.com ("Upload module", `--upload-file`) and Workhorse (`upload.RequestBody`) contradict it. This
  is a correction to the reference, outside this spec, so it goes in a findings-ledger row.

## The dispatch question: a glob value with each `/` kept and each part encoded

No finding: D1's form is what GitLab's routes expect.

- GitLab writes glob values with literal slashes. npm "Retrieve metadata" is `…/projects/1/packages/npm/@myscope/my-pkg`
  and the dist-tags example is `…/npm/-/package/@myscope/my-pkg/dist-tags` (docs.gitlab.com `api/packages/npm/`). The
  model-registry download is `…/ml_models/2/files/my_dir/foo.txt`. Generic packages use `…/1.0.0/path/to/file.txt`
  (`conventions.md`). The generic route is `':package_name/*package_version/(*path/):file_name'`, with
  `NO_SLASH_URL_PART_REGEX` on `package_name` and `file_name` only (`lib/api/generic_packages.rb`).
- Encoding each part is accepted. Grape matches routes with Mustermann, whose `uri_decode` option defaults to `true`
  ("characters in the pattern will also match the URI encoded version"). Mustermann's `Splat` is "always non-greedy",
  `'.*?'`, so a glob spans `/`. Each captured value passes through `map_param` → `unescape` → `@@uri.unescape`
  (`pattern.rb`). So `%40scope/pkg` and `1.0/rc%201` reach the endpoint as `@scope/pkg` and `1.0/rc 1`. The literal `(`,
  `'`, `,` and `=` of the OData paths match both as written and encoded.
- The only scoped-npm form GitLab's docs write with `%2f` is the upload `PUT <prefix>/:package_name`, a `:name`
  parameter, which `_segment` already encodes that way. It is outside this change.
- The client sends the path unaltered. `urllib.request.Request` does not re-quote it. CPython 3.9 `http.client`
  `_validate_path` refuses only `[\x00-\x20\x7f]`, which `quote(safe="")` has already encoded.
- The design's other citations check out:
  - RFC 3986 §3.3: `pchar` includes the sub-delims, §5.2.4 removes dot segments;
  - Python 3.9 `quote`: "Letters, digits, and the characters `'_.-~'` are never quoted", and `safe` defaults to `'/'`;
  - `re`: `(?<!…)` is a fixed-width negative lookbehind, and `(?P<name>…)` is a named group;
  - `urlsplit` does not expand `%` escapes.

NOT-CLEAN (1 A, 0 B)

Verdict: NOT-READY
