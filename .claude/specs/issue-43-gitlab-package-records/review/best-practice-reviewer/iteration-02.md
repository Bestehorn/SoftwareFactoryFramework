# Best-practice review — issue #43 design, iteration 02 (delta)

No documentation MCP server covers GitLab. Sources: GitLab `master` (`workhorse/internal/upstream/routes.go`,
`lib/api/concerns/packages/npm_endpoints.rb`, `lib/api/npm_{project,group,instance}_packages.rb`,
`lib/api/nuget_project_packages.rb`, `lib/api/api.rb`), Grape `master` `lib/grape/middleware/formatter.rb`, npm/cli
`latest` `lib/commands/dist-tag.js`, docs.gitlab.com npm API, all read 2026-11-11.

## Iteration 01 findings: closure

- **A1 closed.** D5's new row, AC-4.2's raw-body list and F's raw-upload row now make npm "Create or update a dist-tag"
  a raw JSON body. The source supports each part of the fix:
  - Rails reads the version as the whole parsed body. The `put` in `namespace 'dist-tags/:tag'` does
    `version = env['api.request.body']` and answers `bad_request_missing_attribute!('Version') if version.blank?`.
    Its `params` block declares only `requires :tag`.
  - Grape's `read_rack_input` sets `env[API_REQUEST_BODY] = parser.call(body, env)` and merges the result into the
    params only `if parsed.is_a?(Hash)`. So the JSON string `"1.0.0"` becomes the version and never becomes a param.
  - The GitLab API declares `format :json` and `content_type :json, 'application/json'` (`api.rb`), and
    `body_format` throws 415 for a media type it has no format for. `application/json` is therefore the right media
    type, and `CONTENT_TYPE_OCTET_STREAM` would have been refused. npm/cli sends the same request:
    `body: JSON.stringify(version)`, `'content-type': 'application/json'`.
  - The routing in D5 matches `routes.go`. The project route
    `` apiProjectPattern+`/packages/npm/-/package/[^/]+/dist-tags/[^/]+` `` goes to `proxy` and is registered before
    `` apiProjectPattern+`/packages/npm/.*` `` → `requestBodyUploader`.
  - Group and instance PUTs match no package route: `` apiPattern+`v4/groups/[^/]+\z` `` is anchored. They reach
    `u.route("", newRoute(apiPattern, "api", railsBackend), proxy)`, so no route stores the body.
  - The prefixed path is valid at every level, because all three npm APIs `include ::API::Concerns::Packages::NpmEndpoints`.
  - The project route's `[^/]+` holds a scoped name, because `expand` writes `@scope/pkg` as one percent-encoded segment.
- **Query `version`: no new error.** AC-1.4 and #40's `documented_raw_body` turn the `body` row `version` into a
  query `Param`. GitLab declares no `version` param and does not read it. `Param.required` is metadata only: nothing
  in `call.py` or `registry.py` reads it, on this base or on #40's. So F's dist-tag call with no `--query version`
  exits 0 with the oracle URL as written. This matches the npm publish `versions` row that iteration 01 accepted.
- **B1 closed.** `nuget_project_packages.rb` declares the v3 publish as `put urgency: :low do` in
  `namespace '/nuget'`, so its path is `PUT /projects/:id/packages/nuget` with no trailing `/`.
  - Workhorse routes only `` apiProjectPattern+`/packages/nuget/` `` and `` …`/packages/nuget/v2` `` to
    `mimeMultipartUploader`, and the `^/api/` patterns need that `/`. The record therefore reaches the `api` `proxy`
    route, and `requires :package, type: ::API::Validations::Types::WorkhorseFile` refuses its part.
  - D5's split row states this correctly. The new Residual keeps the record for AC-1.1 and routes the refusal to one
    ledger row, which is the edit `review-latest.md` B2 called for.
  - `package#upload-a-symbol-package-file` (`put 'symbolpackage'`) does match `/packages/nuget/` and stays multipart,
    which is correct.
- **C1 applied.** The design Residual now names `package#upload-a-package-file-5`, `package#upload-a-package` and the
  Workhorse-only `require_gitlab_workhorse!`, as proposed. The `avatar` clause is gone along with the pending
  `PUT /projects/:id/` (DL-006).
- **C2 applied.**
  - The Security Considerations Conan bullet now says the endpoint answers 401 and issues no token.
  - The Residual names Conan, Debian, NuGet, Helm and Ruby gems with their accepted credential forms.
  - npm is rightly absent from the list: the npm APIs declare no `authenticate_with` and use only
    `route_setting :authentication, job_token_allowed: true, deploy_token_allowed: true`, so they keep the default
    finders.

## Delta findings

### D1 — Sources call the `api` route "the last" route
Severity: D
Location: design.md § Sources (the `routes.go` bullet "no route names `virtual_registries`; the last is …")
Defect: in `routes.go`, `u.route("", newRoute(apiPattern, "api", railsBackend), proxy)` is followed by the `^/assets/`,
uploads, OAuth, `^/-/` and `default` routes. It is the last route an `/api/` request can match, which is the catch-all
that D5's new dist-tag and NuGet rows rely on.
Proposed-edit: replace "the last is" with "the last route an `/api/` path reaches is".

Note: docs.gitlab.com's "Create or update a dist-tag" example sends no body. The design rightly follows the Rails
source and npm/cli instead, and does not cite that example.

CLEAN

Verdict: READY
