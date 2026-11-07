# GitLab REST API (v4): cross-cutting conventions

This page covers everything about the GitLab REST API that is not specific to one endpoint:
where to send requests, how to authenticate, encode, page, upload, download, survive rate limits,
and read errors. The per-endpoint reference is generated separately; see the [README](README.md).
GraphQL mechanics are in `graphql/conventions.md` in the subfolder next to this file.

Basis: GitLab's `doc/api` folder from `gitlab-org/gitlab` at commit `a186442` (master of
2026-11-07, which documents features up to GitLab 19.6), GitLab's partial Swagger 2.0 file
`openapi_v2.yaml`, and the docs.gitlab.com pages named in each `Source:` line, read on 2026-11-07.

Conventions used on this page:

- "(unverified)" marks a statement the sources did not confirm. Treat it as a hypothesis to test.
- "The docs are silent" means none of the pages read say anything about the point.
- Placeholders: `gitlab.example.com`, `PROJECT_ID`, `GROUP_ID`, `ISSUE_IID`, `MR_IID`, `JOB_ID`,
  and the token in `$GITLAB_TOKEN`.

## Hosts and base URLs

Every REST call is `https://HOST/api/v4/<path>`. The documented paths start after `/api/v4` and
write path parameters with a leading colon (`/projects/:id/share/:group_id`); substitute the value
and drop the colon.

| Offering | Base URL | Notes |
|----------|----------|-------|
| GitLab.com | `https://gitlab.com/api/v4` | Multi-tenant SaaS. Rate limits and size limits are fixed by GitLab and partly plan-dependent (see the rate-limit section). |
| GitLab Self-Managed | `https://gitlab.example.com/api/v4` | Administrators configure most limits. |
| GitLab Dedicated | `https://<tenant host>/api/v4` | Single-tenant SaaS. Custom domains are possible through a support ticket; the default hostname pattern is not stated on the pages read (unverified). |

Relative URL roots: an instance can be installed under a sub-path such as
`https://example.com/gitlab`. The relative-URL page explains the server settings but does not spell
out the API path; by construction the API is then `https://example.com/gitlab/api/v4`
(unverified). A client should therefore accept a full base URL, not only a host name.

The GraphQL endpoint is `/api/graphql`, not under `/api/v4`.

GitLab.com traffic is not confined to `gitlab.com`. The GitLab.com settings page lists
`gitlab.com`, `*.gitlab.com`, `*.gitlab-static.net`, `*.gitlab.io` and `*.gitlab.net` as hosts to
allow, plus `*.storage.googleapis.com` and `*.cdn.registry.gitlab-static.net` for the container
registry. Downloads may be redirected to such hosts (see the downloads section).

### How the docs mark tier, offering and status

Each page, and often each section, opens with a details block:

- `Tier:` one or more of Free, Premium, Ultimate. Individual attributes can carry their own note,
  for example "Premium and Ultimate only" on the `job_token` attribute of the artifact endpoints.
- `Offering:` one or more of GitLab.com, GitLab Self-Managed, GitLab Dedicated.
- `Status:` Experiment or Beta, when the feature is not generally available.

A history block below it records "Introduced in GitLab X.Y", "with a feature flag named ...
Disabled by default", "Generally available in X.Y", and deprecations. A feature behind a disabled
flag may not exist on a given instance.

Counts in this snapshot (REST pages only, GraphQL pages excluded):

| Marker | Blocks |
|--------|--------|
| `Offering: GitLab.com, GitLab Self-Managed, GitLab Dedicated` | 203 |
| `Offering: GitLab Self-Managed, GitLab Dedicated` | 50 |
| `Offering: GitLab Self-Managed` | 19 |
| `Offering: GitLab.com` | 11 |
| `Offering: GitLab.com, GitLab Self-Managed` | 9 |
| `Offering: GitLab.com, GitLab Dedicated` | 1 (SCIM API) |
| `Tier: Premium, Ultimate` | 78 |
| `Tier: Ultimate` | 28 |
| `Status: Experiment` | 20 |
| `Status: Beta` | 16 |

GitLab.com-only REST areas: Experiments API, Google Cloud integration API, group enterprise users
API, group SSH certificates API, credentials inventory management (groups API), Google Artifact
Management and Google Cloud IAM integrations (group and project integrations APIs), managing group
member roles (member roles API), and real-time security scan (projects API).

Self-Managed-only examples: group protected branches, group LDAP links, Debian packages, system
hooks, Geo nodes and sites, features (feature flags), the admin data management API.

Tier also affects authentication: project access tokens work on every Self-Managed tier but need
Premium or Ultimate on GitLab.com. Reverting an instance from EE to CE is called out as a breaking
change for API clients.

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/rest/authentication/ ; https://docs.gitlab.com/install/relative_url/ ; https://docs.gitlab.com/administration/dedicated/ ; https://docs.gitlab.com/user/gitlab_com/ ; https://docs.gitlab.com/api/api_resources/ ; https://docs.gitlab.com/api/job_artifacts/

## Authentication

Most endpoints need a token; some return public data without one, and the per-endpoint docs say
when authentication is optional (for example `GET /projects/:id` for a public project).

### Credential types and how to send them

| Credential | How to send it | Notes |
|------------|----------------|-------|
| Personal, project or group access token | `PRIVATE-TOKEN: <token>` header (recommended), or `Authorization: Bearer <token>`. Impersonation tokens and personal tokens also work as the `private_token` query parameter. | Project tokens on GitLab.com need Premium or Ultimate. |
| OAuth 2.0 access token | `Authorization: Bearer <token>` or the `access_token` query parameter. | Sending it in both places returns `400 Bad Request`. Access tokens live for two hours (`expires_in: 7200`); using the refresh token invalidates both the old access token and the old refresh token. |
| CI/CD job token (`CI_JOB_TOKEN`) | `JOB-TOKEN` header (recommended); `token` form field; `job_token` form field or query parameter (query parameter not recommended). For Git over HTTP: user `gitlab-ci-token`, password the job token. | Only the endpoints listed below. Valid only while the job runs; invalid once the job finishes, is erased, or its project is being deleted. Cannot authenticate GraphQL. |
| Session cookie `_gitlab_session` | Set by signing in to the web UI. | Used by the GitLab frontend itself. The API cannot mint one. |
| Deploy token | HTTP Basic (`username:token`) for Git, container registry and package registry; the generic packages page also shows a `DEPLOY-TOKEN` header. | Cannot be used with the general REST API. |
| Impersonation token | Like a personal access token. | Created only by an administrator, acts as a given user. Administrators can switch impersonation off instance-wide. |
| `Sudo` | `Sudo: <user ID or username>` header, or the `sudo` query parameter, on top of an administrator's token that has the `sudo` scope. | Runs the request with the impersonated user's permissions. |

Sudo failure modes: a non-administrator token gets `403` with
`{"message": "403 Forbidden - Must be admin to use sudo"}`; a token without the `sudo` scope gets
`403` with an `insufficient_scope` body naming `sudo`; an unknown user gets `404`
(`"404 User with ID or username '123' Not Found"`).

### Service accounts

Service accounts are non-human users that hold personal access tokens. The service accounts API
manages them at three levels: `/service_accounts` (instance, administrators), `/groups/:id/service_accounts`
and `/projects/:id/service_accounts`, each with `.../:user_id/personal_access_tokens` endpoints to
create and rotate their tokens. Available on all tiers since GitLab 18.11. On Free, GitLab.com
allows 100 service accounts per top-level group and Self-Managed 100 per instance; Premium and
Ultimate are unlimited. For a wrapper that must touch only one project, a project access token or
a project-level service account token is the natural identity.

### Which endpoints accept a CI/CD job token

Rule: a job token works only where GitLab lists it; everything else rejects it. By default only
jobs in the same project can use it; other projects or groups must be added to the target
project's job token allowlist (at most 200 groups and 200 projects). The request also runs with the
permissions of the user who triggered the job. Fine-grained job-token permissions can narrow the
set further. On public or internal projects, some read access works even without membership.

| Resource | Endpoints a job token may call |
|----------|-------------------------------|
| Badges API | all |
| Branches API | `GET /projects/:id/repository/branches` |
| Commits API | `GET /projects/:id/repository/commits/:sha`, `.../:sha/merge_requests`, `.../:sha/refs` (the last one since 19.4) |
| Container registry and its API | all, job's own project only |
| Deployments API, Environments API | all |
| Repository files API | `GET /projects/:id/repository/files/:file_path/raw` |
| Jobs API | `GET /job` only |
| Job artifacts API | download endpoints only |
| Merge requests API | `GET /projects/:id/merge_requests`, `GET /projects/:id/merge_requests/:merge_request_iid` |
| Notes API | `GET .../merge_requests/:merge_request_iid/notes` and `.../notes/:note_id` |
| Packages API, package registry, Terraform module registry | all |
| Pipeline trigger tokens API | `POST /projects/:id/trigger/pipeline` |
| Pipelines API | `PUT /projects/:id/pipelines/:pipeline_id/metadata` |
| Releases API, release links API | all |
| Repositories API | `GET /projects/:id/repository/archive`, `GET /projects/:id/repository/changelog` (since 17.7) |
| Secure files | used through `glab securefile` |
| Tags API | `GET /projects/:id/repository/tags`, `GET /projects/:id/repository/tags/:tag_name` |

Per-endpoint pages add notes as support grows (for example project badges gained job-token support
in 19.1). The artifact endpoints also accept a `job_token` attribute for multi-project pipelines
(Premium and Ultimate).

### Token scopes

A token is accepted when it holds any one of the scopes an endpoint lists. Most endpoints accept
`read_api` only for `GET` and `HEAD`.

| Scope | Allows | Token types |
|-------|--------|-------------|
| `api` | Full read and write API access within the token's reach, including container registry, dependency proxy and package registry. | personal, group, project |
| `read_api` | Read access to the API. | personal, group, project |
| `read_user` | Read-only access to the authenticated user's profile through `/user`. | personal only |
| `read_repository` | Pull over Git-over-HTTP, and read access through the repository files API. | personal, group, project |
| `write_repository` | Pull and push over Git-over-HTTP only. Writing files or commits through REST needs `api`. | personal, group, project |
| `read_registry`, `write_registry` | Pull, push container images. | personal, group, project |
| `read_virtual_registry`, `write_virtual_registry` | Pull (and push or delete) container images through the dependency proxy or virtual registry. | personal, group |
| `create_runner`, `manage_runner` | Create, manage runners. | personal, group, project |
| `self_rotate` | Rotate this same token, nothing else. | personal, group, project |
| `ai_features` | GitLab Duo, Code Suggestions and Duo Chat API actions. | personal, group, project |
| `k8s_proxy` | Kubernetes API calls through the agent for Kubernetes. | personal, group, project |
| `sudo` | Act as any user (administrator token). | personal only |
| `admin_mode` | API actions when Admin Mode is on (administrators). | personal only |
| `read_service_ping` | Download Service Ping payloads (administrators). | personal only |
| `mcp`, `mcp_orbit` | Scopes that OAuth clients request for the MCP server endpoints `/api/v4/mcp` and `/api/v4/orbit/mcp`. | OAuth |

Deploy tokens have their own scope set: `read_repository`, `read_registry`, `write_registry`,
`read_virtual_registry`, `write_virtual_registry`, `read_package_registry`,
`write_package_registry`. By default they do not expire.

Personal access tokens default to an expiry 365 days out; by default the maximum is also 365 days,
and administrators (GitLab 17.6 and later) can change it.

Fine-grained personal access tokens (generally available in GitLab 19.2, all tiers and offerings)
replace broad scopes with per-resource permissions (resource plus action, inside a project, group,
user or instance boundary) for both REST and GraphQL. A request passes only if both the token and
its owner are allowed. A denied request names the permission it needed. Project and group access
tokens are never fine-grained.

### 401 vs 403 vs 404

| Status | Meaning on GitLab | Body |
|--------|-------------------|------|
| `401` | No token, or a token that does not exist, expired or was revoked. Some endpoints also answer 401 for a valid token whose user lacks permission (merging a merge request, listing another user's tokens). | `{"message": "401 Unauthorized"}`, identical in all these cases |
| `403` | Valid token missing a scope (`insufficient_scope`); an action the user may not perform; a feature unavailable on the tier (the epics API answers 403 when epics are not available); a fine-grained token missing a permission; on GitLab.com, a 15-minute ban after 300 failed Git or `/jwt/auth` authentications from one IP in a minute. | For scope errors: `error`, `error_description`, `scope`, plus a `WWW-Authenticate: Bearer realm="Protected by OAuth 2.0", error="insufficient_scope", ..., scope="api read_api"` header listing the scopes that would work. |
| `404` | The resource does not exist or the caller may not see it (private resources are hidden rather than refused, for example a non-member reading a private group's epics); also an un-encoded path parameter that matches no route. | `{"message": "404 ... Not Found"}` |

To tell them apart, call `GET /user` with the same token: `200` means the token is valid and the
original refusal was about permissions; `401` means the token is invalid; `403` means the token is
valid but may not read the user (for example a fine-grained token without that permission). This
check does not work for job tokens.

The MCP endpoints answer scope failures with their own challenge (realm `GitLab`, the `mcp` or
`mcp_orbit` scope, and a `resource_metadata` URL), and use `invalid_token` for expired or revoked
tokens.

Source: https://docs.gitlab.com/api/rest/authentication/ ; https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/oauth2/ ; https://docs.gitlab.com/ci/jobs/ci_job_token/ ; https://docs.gitlab.com/user/profile/personal_access_tokens/ ; https://docs.gitlab.com/security/tokens/access_token_scopes/ ; https://docs.gitlab.com/auth/tokens/fine_grained_access_tokens/ ; https://docs.gitlab.com/user/project/deploy_tokens/ ; https://docs.gitlab.com/api/service_accounts/ ; https://docs.gitlab.com/api/epics/ ; https://docs.gitlab.com/api/project_badges/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/user/gitlab_com/rate_limits/

## Request encoding

### Query string or body

`GET` requests normally carry parameters in the query string; `POST`, `PUT` and `PATCH` normally
carry them in the body. Both work for most endpoints. Bodies can be:

- `application/x-www-form-urlencoded` (curl `--data`),
- `multipart/form-data` (curl `--form`, required when a file is attached),
- JSON with `Content-Type: application/json` (curl `--data` plus that header).

Long query strings fail with `414 Request-URI Too Large`; move the parameters into the body.

The docs are silent on an HTTP method override (`X-HTTP-Method-Override` or `_method`); do not rely
on one.

### `id` versus `iid`

Issues, merge requests, project milestones and some others have both an `id` (unique across the
instance) and an `iid` (unique within the project, the number shown in the UI). Where both exist,
URLs usually take the `iid`: an issue with `id: 46` and `iid: 5` in project 42 is
`GET /projects/42/issues/5`, and `GET /projects/42/issues/46` is wrong. Not every resource follows
this; the per-endpoint page decides. Epics are a special case: the legacy epic ID differs from the
work item ID, only the `iid` matches, and the REST response carries a `work_item_id`.

Integer path parameters are validated: a non-numeric or multi-value input now yields `400 Bad
Request` instead of the old mix of 401, 404 or, rarely, 200.

### URL-encoding path parameters

Anything that can contain `/` must be percent-encoded when used as a path segment:

| Value | Example |
|-------|---------|
| Project or group full path | `GET /api/v4/projects/diaspora%2Fdiaspora` |
| File path | `GET /api/v4/projects/1/repository/files/src%2FREADME.md?ref=master` |
| Branch name | `GET /api/v4/projects/1/branches/my%2Fbranch/commits` |
| Tag name | `GET /api/v4/projects/1/repository/tags/my%2Ftag` |

A segment that is not encoded matches no route and returns `404`. A reverse proxy that decodes `%2F`
before passing the request on causes the same 404 (Apache needs `AllowEncodedSlashes NoDecode` and
`nocanon`). A project's path can differ from its display name; use the path. The raw-file example
in the docs also encodes the dot (`lib%2Fclass%2Erb`); other examples leave dots alone, so encoding
dots is allowed but not required.

In Python, `urllib.parse.quote(value, safe="")` produces these segments; the default `safe="/"`
leaves slashes unencoded and is wrong here (checked against Python 3.14).

Exception seen in the docs: the job artifacts troubleshooting example passes the ref
`refs/merge-requests/123/head` with literal slashes inside
`/jobs/artifacts/:ref_name/raw/...`. Whether the encoded form works on that route is unverified.

### Arrays, hashes and arrays of hashes

| Type | Query string or form | JSON |
|------|----------------------|------|
| `array` | `import_sources[]=github&import_sources[]=bitbucket` | `"import_sources": ["github", "bitbucket"]` |
| `hash` | `override_params[visibility]=private&override_params[some_other_param]=value` | `"override_params": {"visibility": "private"}` |
| array of hashes | `variables[0][key]=VAR1&variables[0][value]=hello&variables[1][key]=VAR2...` (curl needs `--globoff` for the brackets), or the index-free form `actions[][action]=create&actions[][file_path]=foo` used by the commits API | `"variables": [{"key": "VAR1", "value": "hello"}]` |

Some attributes are plain comma-separated strings instead of arrays (for example `exclude_paths`
on the repository archive endpoint, `report_type=sast,dast` on vulnerability findings); the
per-endpoint type column decides. JSON is the least ambiguous choice for nested data. Python's
`urlencode` percent-encodes the brackets (`labels%5B%5D=x`); GitLab's parameter parser is expected
to decode them before parsing (unverified).

JSON bodies are bounded by default: nesting depth 32, at most 50,000 elements per array or hash,
100,000 elements in total; exceeding a bound returns `400`. A few endpoints (Terraform state, npm)
have larger limits.

### `+` in dates and other values

A literal `+` in a query string can be read as a space. Encode it as `%2B`, for example
`2017-10-17T23:11:13.000%2B05:30`. Python's `urlencode` and `quote(..., safe="")` already do this.

### Booleans and `null`

Send `true` or `false`. Do not send `null` for boolean arguments; GitLab treats a `null` boolean as
`false`, and the v5 deprecation list already announces that `null` for `private_profile` will
become a `400`. In form and query encoding, booleans are the strings `true` and `false` (the commits
API example uses `actions[][execute_filemode]=true`). To clear a file attribute such as an avatar,
send it empty (`avatar=`).

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/rest/deprecations/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/api/vulnerability_findings/ ; https://docs.gitlab.com/api/epics/ ; https://docs.gitlab.com/api/job_artifacts/ ; https://docs.gitlab.com/api/projects/ ; https://docs.gitlab.com/administration/instance_limits/

## Responses

- Format: JSON for almost everything. Some endpoints return plain text or binary (raw files, job
  logs, archives, artifacts, uploads). The OpenAPI file declares `produces: application/json` even
  for binary downloads such as `/repository/archive` and `/jobs/:job_id/artifacts`; trust the
  `Content-Type` of the actual response, not the OpenAPI file.
- Success codes: `200` for reads and updates, `201` with the new resource for creates, `204` for
  deletes without a body, `202` when work was only scheduled. A few endpoints answer with a status
  string as the body, for example `{"message": "202 Accepted"}` from `POST /projects/:id/export`
  or `{"message":"201 Created"}` from webhook tests.
- `null` versus `false`: boolean fields can be `null`, which GitLab treats as `false`. Clients
  should map `null` to `false` for booleans.
- Dates are ISO 8601 strings. In the commits API, `created_at` always equals `committed_date`, and
  `authored_date` may differ from `committed_date`.
- Repository file `content` is Base64 of the file converted to UTF-8; `size` is the raw blob size
  and may not match the decoded length. Use the raw endpoint for exact bytes.

### Redirects for moved or renamed projects

After a project or namespace path change, a `GET` to the old path is redirected: the response has
a `Location` header pointing at the project by ID (for example `/api/v4/projects/81`) and a body
saying the resource moved permanently (status `301`). Only `GET` is redirected. `POST`, `PUT`,
`PATCH` and `DELETE` against the old path mostly return `405 Method Not Allowed` with
`{"message": "Non GET methods are not allowed for moved projects"}`. Resolving the project to its
numeric ID once and using the ID afterwards avoids both cases.

Note for Python clients: `urllib` follows redirects automatically only for `GET` and `HEAD` (and
turns `POST` into `GET` on 301, 302 and 303); it raises `HTTPError` for other methods (checked in
the Python 3.14 standard library). Downloads can also redirect to other hosts; see the downloads
section.

### Response headers worth reading

| Header | Meaning |
|--------|---------|
| `x-request-id` | Request identifier; shown in the docs' example response. The pages read do not describe it further; logging it next to errors is useful when asking an administrator or GitLab Support to find the request. |
| `x-runtime` | Server time spent; shown in the same example. |
| `link`, `x-next-page`, `x-page`, `x-per-page`, `x-prev-page`, `x-total`, `x-total-pages` | Offset pagination (next section). |
| `RateLimit-*`, `Retry-After` | Rate limiting (see below). |
| `WWW-Authenticate` | On `insufficient_scope` errors, the scopes that would work. |
| `X-Gitlab-*` (`X-Gitlab-Blob-Id`, `X-Gitlab-Commit-Id`, `X-Gitlab-Content-Sha256`, `X-Gitlab-Encoding`, `X-Gitlab-File-Name`, `X-Gitlab-File-Path`, `X-Gitlab-Last-Commit-Id`, `X-Gitlab-Ref`, `X-Gitlab-Size`, `X-Gitlab-Execute-Filemode`) | File metadata on `HEAD /projects/:id/repository/files/:file_path`. |
| `X-Checksum-SHA256` | SHA-256 of a generic package file on download (absent when the download is redirected to object storage). |

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/project_import_export/ ; https://docs.gitlab.com/api/project_webhooks/ ; https://docs.gitlab.com/user/packages/generic_packages/

## Pagination

Two methods exist. Offset pagination is the default and works on every list endpoint except where
a page says otherwise. Keyset pagination is opt-in on selected endpoints, is faster on large
collections, and its cost does not grow with the collection size; prefer it where available.

### Offset-based

| Parameter | Default | Maximum |
|-----------|---------|---------|
| `page` | `1` | (see offset limit below) |
| `per_page` | `20` | `100` |

What happens when `per_page` exceeds 100 is not stated (unverified; expect the maximum).

Response headers:

| Header | Content |
|--------|---------|
| `link` | URLs with `rel="prev"`, `rel="next"`, `rel="first"`, `rel="last"`. Use these rather than building URLs. |
| `x-next-page` | Index of the next page (empty on the last page; unverified). |
| `x-page` | Current page, starting at 1. |
| `x-per-page` | Items per page. |
| `x-prev-page` | Index of the previous page. |
| `x-total` | Total number of items. |
| `x-total-pages` | Total number of pages. |

When totals are missing:

- When a query matches more than 10,000 records, GitLab drops `x-total`, `x-total-pages` and the
  `rel="last"` link. GitLab.com documents the same rule.
- The commits API never returns `x-total` or `x-total-pages`.
- Runner jobs listed with keyset pagination do not return `X-Total` or `X-Total-Pages`.

Loop on `x-next-page` (or `rel="next"`) until it is absent, never on `x-total-pages`.

Offset depth limit: the instance limit `offset_pagination_limit` (default 50,000) caps how far into
a result set offset pagination may go. It applies only to endpoints that also support keyset
pagination; `0` disables it; Self-Managed administrators can change it. The listing pages restate it:
offset pagination reaches 50,000 projects, and the users endpoint requires keyset pagination beyond
50,000 records since GitLab 17.0. The status code returned when the cap is exceeded is not stated
(unverified).

### Keyset-based

| Parameter | Required | Meaning |
|-----------|----------|---------|
| `pagination` | yes | `keyset` |
| `per_page` | no | default `20`, maximum `100` |
| `order_by` | yes | column to order by (allowed values per resource below) |
| `sort` | yes | `asc` or `desc` |

Navigation is through the `Link` header only: follow its `rel="next"` URL unchanged. The added
cursor parameter differs per resource and order (for example `id_after=42` for projects by ID,
`cursor=<opaque>` for groups by name, `page_token` for repository trees and tags). At the end the
`Link` header disappears and the body is an empty array. The old `Links` header was removed. The
page also mentions `X-NEXT-CURSOR` and `X-PREV-CURSOR` headers carrying the cursor values, while
stating that no other pagination headers exist; the `Link` header is the reliable signal.

Resources with keyset pagination, from the central table:

| Resource | Endpoint | Ordering allowed | Who |
|----------|----------|------------------|-----|
| Group audit events | `GET /groups/:id/audit_events` | `order_by=id`, `sort=desc` | authenticated |
| Groups | `GET /groups` | `order_by=name`, `sort=asc` | unauthenticated only |
| Instance audit events | `GET /audit_events` | `order_by=id`, `sort=desc` | authenticated |
| Package pipelines | `GET /projects/:id/packages/:package_id/pipelines` | `order_by=id`, `sort=desc` | authenticated |
| Project jobs | `GET /projects/:id/jobs` | `order_by=id`, `sort=desc` | authenticated |
| Project audit events | `GET /projects/:id/audit_events` | `order_by=id`, `sort=desc` | authenticated |
| Projects | `GET /projects` | `order_by=id` | both |
| Users | `GET /users` | `order_by` one of `id`, `name`, `username`, `created_at`, `updated_at` | both |
| Registry repository tags | `GET /projects/:id/registry/repositories/:repository_id/tags` | `order_by=name`, `sort=asc` or `desc` | authenticated |
| Repository tree | `GET /projects/:id/repository/tree` | not applicable (uses `page_token`) | both, since 17.1 |
| Project issues | `GET /projects/:id/issues` | `order_by` one of `created_at`, `updated_at`, `title`, `id`, `weight`, `due_date`, `relative_position`; `sort=asc` or `desc` | both, since 18.3 |
| Runner jobs | `GET /runners/:id/jobs` | `order_by=id`, `sort=desc` | authenticated |

Further keyset behaviour found on individual pages but missing from the central table:

| Endpoint | Detail |
|----------|--------|
| `GET /pipelines` (pipelines the current user triggered, across projects, since 19.3) | Keyset only; offset pagination is not supported; `cursor` from the `Link` header; up to 100 per page; only `order_by=created_at`, `sort=desc`. |
| `GET /admin/data_management/:model_name` (Premium/Ultimate, Self-Managed, Experiment) | Keyset on the primary key, `sort=asc` or `desc`. |
| `GET /projects/:id/repository/tags` | `page_token` (tag name to start from) for keyset pagination. |
| `GET /runners/:id/jobs` | The runners page says ascending keyset order was added in 19.4, contradicting the central table's `sort=desc` only. |
| Registry repository tags | Offset pagination is deprecated; on Self-Managed keyset needs the container registry metadata database; `order_by=published_at` (19.5) requires keyset. |
| Audit events (instance, group, project) | Offset pagination deprecated in 17.8, planned for removal in 19.0 (breaking change). |
| `GET /projects/:id/repository/commits` | The OpenAPI file lists `pagination` and `page_token` query parameters, but the commits page documents only `page` and `per_page` (keyset support unverified). |

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/user/gitlab_com/rate_limits/ ; https://docs.gitlab.com/administration/instance_limits/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/api/runners/ ; https://docs.gitlab.com/api/pipelines/ ; https://docs.gitlab.com/api/admin/data_management/ ; https://docs.gitlab.com/api/tags/ ; https://docs.gitlab.com/api/container_registry/ ; https://docs.gitlab.com/api/audit_events/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/api/projects/ ; https://docs.gitlab.com/api/users/ ; https://docs.gitlab.com/api/groups/

## Versioning and deprecations

- One major version, `v4`, in the URL. GitLab says the REST API follows semantic versioning: no
  minor version in the URL, new features land in v4, and incompatible changes need a new major
  version, which would ship together with a major GitLab release.
- The deprecations page notes that some items mention a future v5, but no v5 work is active. In
  practice, deprecated v4 items stay in v4.
- Exempt from the deprecation process, and removable at any time: anything marked Experiment or
  Beta, and fields behind a feature flag that is disabled by default.
- Deprecations are announced in the API docs themselves (history blocks, "(deprecated)" in titles
  and attribute tables, warning boxes) and collected on the REST deprecations page. GitLab-wide
  removals per release are on the deprecations-by-version page.

REST deprecations page, summarized:

| Item | Replacement or change |
|------|-----------------------|
| `geo_nodes` endpoints | `geo_sites` |
| `merged_by` field on merge requests | `merge_user` |
| `merge_status` field on merge requests | `detailed_merge_status` |
| `null` for `private_profile` on users | only `true` or `false` in v5 (`null` becomes 400) |
| Single merge request changes endpoint | list merge request diffs endpoint |
| Managed licenses endpoint | license approval policies |
| `approvers`, `approval_groups` in project approval configuration (already empty arrays) | approval rules endpoint |
| Runner `active` | `paused` |
| Runner `status` values `paused`, `active` | read the boolean `paused` |
| Runner `ip_address` (returns `""` since 17.0) | removed in v5 |
| `default_branch_protection` (groups, application settings) | `default_branch_protection_defaults` |
| `require_password_to_approve` | `require_reauthentication_to_approve` |
| Pull mirroring through the projects API | `projects/:id/mirror/pull` |
| `restrict_user_defined_variables` (projects) | `ci_pipeline_variables_minimum_override_role` |
| `namespace` in project import endpoints (18.7) | `namespace_id` or `namespace_path` |
| Non-numeric IDs on integer path parameters | now `400 Bad Request` |

Other deprecations an automation client will meet, found on endpoint pages:

| Item | Status |
|------|--------|
| Epics REST API | deprecated in 17.0, no new features, removal planned for v5; use the work item GraphQL API |
| Vulnerabilities and vulnerability findings REST APIs | being deprecated, called unstable; use GraphQL |
| `merge_when_pipeline_succeeds` on merge | deprecated in 17.11; use `auto_merge` |
| `wip` filter on merge request lists | deprecated in 19.0; use `draft` |
| Offset pagination on audit events and registry tags | deprecated (see pagination) |
| Offset pagination on users | deprecated in 16.5; keyset enforced above 50,000 records |

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/rest/deprecations/ ; https://docs.gitlab.com/api/epics/ ; https://docs.gitlab.com/api/vulnerabilities/ ; https://docs.gitlab.com/api/vulnerability_findings/ ; https://docs.gitlab.com/api/merge_requests/ ; https://docs.gitlab.com/api/audit_events/ ; https://docs.gitlab.com/api/container_registry/

## Rate limits

### Headers and the 429 response

| Header | Sent | Meaning |
|--------|------|---------|
| `RateLimit-Limit` | on every response | Quota per minute (rescaled if the configured period differs). |
| `RateLimit-Name` | on every response | Name of the throttle that applied. |
| `RateLimit-Observed` | on every response | Requests counted in the current window. |
| `RateLimit-Remaining` | on every response | `RateLimit-Limit` minus `RateLimit-Observed`. |
| `RateLimit-Reset` | on every response | Unix time when the quota resets. |
| `RateLimit-ResetTime` | only on `429` | Reset time as an RFC 2616 date. |
| `Retry-After` | only on `429` | Seconds until the quota resets. |

Caveats: the "every response" wording comes from the user and IP rate limit settings page; when
those throttles are switched off on a Self-Managed instance, the headers are presumably absent
(unverified). GitLab.com states that rate-limited responses from the Projects, Groups and Users APIs
carry no informational headers. For project and group creation the window is 24 hours, so
`Retry-After` can reach 86,400 seconds.

Client rules from the docs: wait `Retry-After` seconds before retrying, back off exponentially if
throttling continues, and slow down when `RateLimit-Remaining` gets low. Endpoint-specific limits
(job cancellation, file blame, vulnerability exports) also answer `429`, the first two with
`Retry-After`.

### GitLab.com limits that matter for an automation client

| Limit | Value |
|-------|-------|
| Authenticated API traffic | 2,000 requests per minute per user |
| Unauthenticated traffic | 500 requests per minute per IP |
| All traffic from one IP | 2,000 requests per minute |
| Issue creation | 200 requests per minute |
| Note creation on issues and merge requests | 60 requests per minute |
| Pipeline creation | 25 requests per minute per project, user and commit; 2,000 per minute per user overall |
| CI Lint | 400 requests per minute per user |
| Raw endpoint (`.../files/:file_path/raw` and similar) | 300 requests per minute per project, commit and file path; 800 per minute per project unauthenticated |
| Repository files API | 500 requests per minute per IP and file path |
| Repository files API, blobs over 10 MB (all offerings) | 5 requests per minute |
| Repository archive | 5 requests per minute |
| Advanced, project or group search | 100 requests per minute per user and per IP |
| Projects list | 2,000 per 10 minutes per user; 400 per 10 minutes per IP unauthenticated |
| Single project / group projects | 400 / 600 requests per minute |
| Groups list / single group | 50 / 400 requests per minute |
| `GET /users/:id` | 300 requests per 10 minutes per user |
| User projects, followers, status, SSH and GPG keys | between 100 and 300 requests per minute per endpoint |
| Project members list | 200 requests per minute per project |
| Project and group creation | 200 per day per user each |
| Package registry | 1,000 requests per minute per IP |
| Protected paths (sign-in, password reset and similar) | 10 POST requests per minute per IP |
| Project and group imports, file-based exports, export downloads | rate limited; the numbers are on the GitLab.com limits page but were not captured here (unverified) |

The same page publishes plan-based sustained and burst limits (Free 5,000 per hour and 100 per
minute burst for an authenticated user, Premium and Ultimate higher, 60 per hour unauthenticated)
as proposed and not yet enforced on 2026-11-07, plus a paid "Advanced Capacity" add-on.

### Self-Managed and Dedicated

All limits are administrator-configurable. User and IP limits are off by default; once enabled,
their defaults are 3,600 requests per hour per IP unauthenticated and 7,200 per hour per user
authenticated, for API and web traffic separately. Other documented defaults:

| Limit | Default |
|-------|---------|
| Search | 30 per minute authenticated, 10 per minute unauthenticated |
| Autocomplete users | 300 per minute authenticated, 100 unauthenticated |
| Project import | 6 per minute per user |
| `GET /projects/:id/jobs` | 600 per minute per user |
| MCP server requests | 600 per minute per user |
| Commits and files API bodies over 20 MB | 3 requests per 30 seconds; bodies over 300 MB rejected with `413` |
| Create tag | 100 per 30 minutes per project |
| File blame | 400 per minute per user and project (since 19.6; `0` disables) |
| GitLab Duo `aiAction` | 160 per 8 hours per user |

Dedicated documents its own "authenticated user rate limits" page; the numbers were not read here
(unverified). An administrator can let trusted traffic bypass throttles with a
`Gitlab-Bypass-Rate-Limiting: 1` header set by the load balancer; clients cannot use it on their
own.

Source: https://docs.gitlab.com/security/rate_limits/ ; https://docs.gitlab.com/user/gitlab_com/rate_limits/ ; https://docs.gitlab.com/administration/settings/user_and_ip_rate_limits/ ; https://docs.gitlab.com/administration/settings/import_export_rate_limits/ ; https://docs.gitlab.com/administration/instance_limits/ ; https://docs.gitlab.com/rate_limits/api/ ; https://docs.gitlab.com/api/rest/authentication/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/api/jobs/ ; https://docs.gitlab.com/api/vulnerability_exports/

## Errors

### Status codes

| Code | Meaning on GitLab |
|------|-------------------|
| `400` | Missing required attribute, failed validation, invalid integer ID, JSON over the size bounds, or (repository files) a commit that failed for a reason GitLab cannot name. |
| `401` | See the authentication section: unauthenticated, and on some endpoints also unauthorized. |
| `403` | Not allowed, or token missing a scope. |
| `404` | Not found or not visible to the caller; un-encoded path parameter. |
| `405` | Method not supported, a merge request that cannot be merged, or a write to a moved project's old path. |
| `409` | Conflict: resource already exists, lock conflict, `sha` not matching the source branch head on merge, rebase could not be enqueued. |
| `412` | Precondition failed, for example `If-Unmodified-Since` on a `DELETE` when the resource changed meanwhile. |
| `413` | Request body too large (commits and files API over 300 MB). |
| `414` | Query string too long; send a body instead. |
| `422` | Unprocessable entity, for example a merge that failed. |
| `429` | Rate limited; wait `Retry-After`. |
| `500` | Server error. |
| `503` | Temporarily overloaded; also used by some endpoints for timeouts. |

### Body shapes

A client has to accept several shapes:

| Shape | Example |
|-------|---------|
| `message` as a string, often prefixed with the status | `{"message": "401 Unauthorized"}`, `{"message": "400 (Bad request) \"title\" not given"}`, `{"message": "404 Project Not Found"}` |
| `message` as a hash of field name to a list of messages (model validation), possibly nested per embedded entity | `{"message": {"bio": ["is too long (maximum is 255 characters)"]}}` |
| `error` as a string (parameter validation and some endpoint errors) | `{"error": "glql_yaml is missing, glql_yaml is empty"}`, `{"error": "400 Bad request - Input exceeds maximum size"}` |
| OAuth-style scope error | `{"error": "insufficient_scope", "error_description": "...", "scope": "sudo"}` |
| Spam detection | `{"message": {"error": "Your snippet has been recognized as spam and has been discarded."}}`, or with CAPTCHA configured `needs_captcha_response: true` plus `spam_log_id` and `captcha_site_key`; resend with `X-GitLab-Captcha-Response` and `X-GitLab-Spam-Log-Id` headers |
| Plain text | for example the 413 from the request-body limit: `RequestBody: upload failed: the upload size ... is over maximum of 314572800 bytes: entity is too large` |

Practical parser: read `message`; if it is a dict, flatten `field: message` pairs; if absent, read
`error` and `error_description`; if the body is not JSON, keep the text.

### Common validation failures

- Required attribute missing: `400` with `"<attr>" not given` or `<attr> is missing`.
- Field too long or invalid: `400` with a field hash.
- Repository files create, update or delete: a non-specific `400` when the path contains `/../`,
  when the new content equals the old (empty commit), or when someone pushed to the branch during
  the edit.
- Merge: `405` (cannot merge), `409` (`SHA does not match HEAD of source branch`), `422` (`Branch
  cannot be merged`).
- Rebase: `403` (cannot push to source branch, source branch missing, force-push protected), `409`
  (`Failed to enqueue the rebase operation`).

Source: https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/rest/authentication/ ; https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/merge_requests/ ; https://docs.gitlab.com/api/glql/ ; https://docs.gitlab.com/administration/instance_limits/

## Uploads and binary request bodies

### Markdown uploads (attach a file to issue, merge request or comment text)

| Step | Detail |
|------|--------|
| Upload | `POST /projects/:id/uploads`, multipart, field `file`. Group variant `POST /groups/:id/uploads` (since 19.0, any role from Guest) for epics and group wikis. |
| Response | `id`, `alt`, `url` (`/uploads/<secret>/<filename>`), `full_path` (`/-/project/<project_id>/uploads/<secret>/<filename>`, or `/-/group/<id>/...`), `markdown` (an image or link reference to the `url`, ready to paste: `![alt]` followed by the `url` in parentheses). |
| Embed | Put the `markdown` string, or a link to `url`, into an issue or merge request description or note body. The relative `/uploads/...` link resolves in the context of the project (or group) it was uploaded to. Whether it renders when pasted into another project is unverified. |
| Manage | `GET /projects/:id/uploads` (list, Maintainer or Owner), `GET` and `DELETE /projects/:id/uploads/:upload_id` (Maintainer or Owner), `GET` and `DELETE /projects/:id/uploads/:secret/:filename` (download: any role from Guest; delete: Maintainer or Owner). Same set under `/groups/:id/uploads`. |
| Pitfalls | GitLab may rename the file on upload (spaces become underscores); take the filename from the returned link. A group-owned file returns `404` from the project endpoint and the other way round. |
| Size | GitLab.com: 100 MiB maximum attachment size. Self-Managed: the administrator's maximum attachment size (default not read, unverified). |

GraphQL has an experimental `uploadCreate` mutation (19.0) for the same purpose.

### Avatars

| Target | Upload | Download | Remove |
|--------|--------|----------|--------|
| Project | `PUT /projects/:id`, multipart field `avatar` (Maintainer or Owner) | `GET /projects/:id/avatar` | `PUT /projects/:id` with `avatar=` |
| Group | `PUT /groups/:id`, multipart field `avatar` | `GET /groups/:id/avatar` | `PUT /groups/:id` with `avatar=` |
| Current user | `PUT /user/avatar` (17.0), multipart field `avatar` | the user's `avatar_url` | not documented on that page |

Limits for project and user avatars: 200 KB, one of `.bmp`, `.gif`, `.ico`, `.jpeg`, `.jpg`,
`.png`, `.tiff`, `.webp`; 192 x 192 pixels is ideal; a larger user avatar is answered with `400`.
The group section states no size limit. `GET /avatar?email=...` only looks up the avatar URL for
an email address. The OpenAPI file also gives `POST /projects`, `POST /groups`, `POST /topics`,
`PUT /topics/:id` and `POST /organizations` an `avatar` file attribute.

### Repository files API

| Operation | Endpoint | Body |
|-----------|----------|------|
| Read with metadata | `GET /projects/:id/repository/files/:file_path?ref=` | Response `content` is Base64 (`encoding: base64`), plus `blob_id`, `last_commit_id`, `content_sha256`, `execute_filemode`, `size`. |
| Metadata only | `HEAD` on the same URL | `X-Gitlab-*` headers. |
| Raw bytes | `GET .../files/:file_path/raw?ref=` (`lfs=true` returns LFS content instead of the pointer) | binary |
| Create, update | `POST` / `PUT .../files/:file_path` | `branch`, `content`, `commit_message`, optional `encoding` (`text` default, or `base64`), `execute_filemode`, `author_email`, `author_name`, `start_branch`; update also takes `last_commit_id` as an optimistic lock. |
| Delete | `DELETE .../files/:file_path` | `branch`, `commit_message`, optional `last_commit_id`. |

Limits: request bodies over 300 MB are rejected (`413`); bodies over 20 MB are limited to 3 requests
per 30 seconds (since 18.7); reading blobs over 10 MB is limited to 5 requests per minute. Use the
commits API to change several files at once. Scopes: `api` for writes; `read_api` or
`read_repository` for reads.

### Commits API with `actions[]`

`POST /projects/:id/repository/commits` creates one commit from several file actions. Required:
`branch`, `commit_message`. Optional: `actions[]`, `start_branch` or `start_sha` (with
`start_project`) to create `branch` from another base, `force` (overwrite the branch history),
`allow_empty` (18.8), `author_email`, `author_name`, `stats`.

| `actions[]` attribute | Notes |
|-----------------------|-------|
| `action` | `create`, `update`, `move`, `delete` or `chmod` |
| `file_path` | target path |
| `previous_path` | source path, `move` only |
| `content` | required except for `delete`, `chmod` and `move`; a `move` without content keeps the content |
| `encoding` | `text` (default) or `base64`, per action |
| `execute_filemode` | `chmod` only |
| `last_commit_id` | optimistic lock for `update`, `move`, `delete` |

Send JSON (clearest), or form fields using the index-free array-of-hashes form
(`actions[][action]=create`, `actions[][file_path]=...`, `actions[][content]=</path/to/file` with
curl's `<` reading a file into a field). Returns `201` with the commit. Same 300 MB and 20 MB limits
as the files API. For binary files use `encoding: base64`.

OpenAPI quirk: the Swagger file describes the commits and repository-files write bodies as a single
`file` parameter "generated by Multipart middleware". That reflects GitLab's front proxy rewriting
large bodies; clients still send JSON or form bodies as documented (interpretation, unverified).

### Generic packages

| Item | Detail |
|------|--------|
| Upload | `PUT /projects/:id/packages/generic/:package_name/:package_version/:file_name`; the file name may include a sub-path (`.../1.0.0/path/to/file.txt`). The body is the raw file bytes (curl `--upload-file`), not multipart. |
| Query attributes | `status` (`default` or `hidden`) and `select=package_file` (return the created package file object instead of a short message). Both come from the OpenAPI file; the user-facing generic packages page does not document them. Exact response shape unverified. |
| Authentication | `PRIVATE-TOKEN` (personal or project access token), `JOB-TOKEN`, `DEPLOY-TOKEN`, or HTTP Basic with the token as password. |
| File names | letters, digits, `.`, `_`, `-`, `+`, `~`, `@`, `/`; no spaces; must not start or end with `~` or `@`. |
| Duplicates | By default a new file with the same package name and version is added to the existing package; group owners can forbid duplicates, with exceptions. |
| Size | Default maximum 5 GB per file (`generic_packages_max_file_size`), 5 GB on GitLab.com. S3-compatible storage caps a single PUT at 5 GB. |
| Download | `GET` on the same path; returns `X-Checksum-SHA256` unless direct object-storage download is enabled, in which case it redirects. |

The OpenAPI file also lists `.../authorize` variants of the upload paths (for generic packages and
for Markdown uploads). They look like internal hand-offs between GitLab's front proxy and the
application; do not call them (unverified).

### Other package formats

These endpoints exist for the package manager clients, are "not meant for manual consumption", and
use authentication methods that differ from the standard API (per format docs). Upload endpoints:

| Format | Upload endpoint | Default max file size (Self-Managed / GitLab.com) |
|--------|-----------------|-----------------------------------------------------|
| Composer | `POST /projects/:id/packages/composer` | not listed |
| Conan v1 / v2 | `PUT` under `/projects/:id/packages/conan/v1/files/...` or `.../conan/v2/.../files/:file_name` | 3 GB / 5 GB |
| Debian (Self-Managed only, under development) | `PUT /projects/:id/packages/debian/:file_name` | 3 GB / not listed |
| Helm | `POST /projects/:id/packages/helm/api/:channel/charts` (field `chart`) | 5 MB / 5 MB |
| Maven | `PUT /projects/:id/packages/maven/*path/:file_name` | 3 GB / 5 GB |
| npm | `PUT /projects/:id/packages/npm/:package_name` (JSON with embedded Base64) | 500 MB / 5 GB |
| NuGet | `PUT /projects/:id/packages/nuget` (and `/v2`), symbols `PUT .../nuget/symbolpackage` | 500 MB / 5 GB |
| PyPI | `POST /projects/:id/packages/pypi` (field `content`) | 3 GB / 5 GB |
| RubyGems (under development) | `POST /projects/:id/packages/rubygems/api/v1/gems` | not listed |
| Terraform modules | `PUT /projects/:id/packages/terraform/modules/:module-name/:module-system/:module-version/file` (multipart `file`) | 1 GB / 1 GB |
| ML model files | `PUT /projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name` | not listed / 10 GB (uploads capped at 5 GB) |
| Go proxy | read-only | not applicable |

### Release asset links

Releases do not store binaries. `POST /projects/:id/releases/:tag_name/assets/links` takes `name`,
`url` (both unique within the release), optional `direct_asset_path` and `link_type` (`other`,
`runbook`, `image`, `package`). Release creation can embed the same links under `assets:links`. A
common pattern is to upload the binary as a generic package and link its download URL; the release
pages do not describe this pairing. Download through
`GET /projects/:id/releases/:tag_name/downloads/:direct_asset_path` (the docs use `--location`) and
`/releases/permalink/latest/...` for the newest release.

### Wiki attachments

`POST /projects/:id/wikis/attachments` (and `POST /groups/:id/wikis/attachments`, Premium and
Ultimate), multipart `file`, optional `branch`. The file is committed into the wiki repository's
`uploads/` folder. The response gives `file_name`, `file_path`, `branch`, and `link.url` plus
`link.markdown` to paste into a wiki page.

### Project and group import, project export to a URL

| Operation | Endpoint | Body |
|-----------|----------|------|
| Import project from file | `POST /projects/import` | multipart `file`, `path`, optional `name`, `namespace_id` or `namespace_path` (`namespace` deprecated), `overwrite`, `override_params[...]` |
| Import project from URL (Beta) | `POST /projects/remote-import` | `url`, `path`, same namespace options; the remote server must return a valid `Content-Length`; maximum 10 GB |
| Import project from S3 | `POST /projects/remote-import-s3` | `access_key_id`, `secret_access_key`, `bucket_name`, `file_key`, `region`, `path` |
| Import project relations | `POST /projects/import-relation` | multipart `file`, `path`, `relation` |
| Import group from file | `POST /groups/import` | multipart `file`, `name`, `path`, optional `parent_id` |
| Export project to a URL | `POST /projects/:id/export` | `upload[url]`, optional `upload[http_method]` (`PUT` default, or `POST`), `description`, `excluded_relations` |

Sizes: Self-Managed `max_import_size` and `max_export_size` default to `0` (unlimited). GitLab.com:
imports up to 5 GiB, remote imports up to 10 GiB, exports up to 40 GiB. When exporting to a URL,
GitLab sends `Content-Type: application/gzip`, so a pre-signed URL must include that header in its
signature, and it must stay valid for the whole export; S3 uploads are limited to 5 GB by a known
issue. Imported groups end up `private` unless imported into a parent group.

### Secure files

`POST /projects/:project_id/secure_files`, multipart `file` (5 MB limit) and `name` (unique within
the project). Download with `GET .../secure_files/:id/download`.

### Everything else in the OpenAPI file that takes a file

The Swagger file declares a `formData` file parameter on 8 operations and a file-typed body
property on 39 more. Beyond the items above:

| Endpoint | File attribute | Note |
|----------|----------------|------|
| `PUT /application/appearance` | `logo`, `pwa_icon`, `header_logo`, `favicon` | administrators |
| `POST /projects/:id/alert_management_alerts/:alert_iid/metric_images` | `file` | incident management |
| `POST /projects/:id/issues/:issue_iid/metric_images` | `file` | incident management |
| `POST /groups/:id/placeholder_reassignments` | `file` | CSV of placeholder-user reassignments |
| `POST` / `PUT /projects/:id/pages/domains[/:domain]` | `certificate`, `key` | Pages custom domains |
| `POST /projects/:id/terraform/state/:name` | `file` | Terraform state backend |
| `POST /jobs/:id/artifacts` | `file`, `metadata` | runner API, uses the runner's job token |
| `POST /projects/import`, `remote-import`, `remote-import-s3` | `override_params[avatar]` | avatar for the imported project |

Source: https://docs.gitlab.com/api/project_markdown_uploads/ ; https://docs.gitlab.com/api/group_markdown_uploads/ ; https://docs.gitlab.com/api/projects/ ; https://docs.gitlab.com/api/groups/ ; https://docs.gitlab.com/api/users/ ; https://docs.gitlab.com/api/avatar/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/user/packages/generic_packages/ ; https://docs.gitlab.com/api/packages/ ; https://docs.gitlab.com/api/packages/npm/ ; https://docs.gitlab.com/api/packages/maven/ ; https://docs.gitlab.com/api/packages/pypi/ ; https://docs.gitlab.com/api/packages/nuget/ ; https://docs.gitlab.com/api/packages/helm/ ; https://docs.gitlab.com/api/packages/conan_v2/ ; https://docs.gitlab.com/api/packages/debian/ ; https://docs.gitlab.com/api/packages/rubygems/ ; https://docs.gitlab.com/api/packages/terraform-modules/ ; https://docs.gitlab.com/api/packages/composer/ ; https://docs.gitlab.com/api/releases/ ; https://docs.gitlab.com/api/releases/links/ ; https://docs.gitlab.com/api/wikis/ ; https://docs.gitlab.com/api/group_wikis/ ; https://docs.gitlab.com/api/project_import_export/ ; https://docs.gitlab.com/api/group_import_export/ ; https://docs.gitlab.com/api/secure_files/ ; https://docs.gitlab.com/administration/instance_limits/ ; https://docs.gitlab.com/user/gitlab_com/ ; https://docs.gitlab.com/api/graphql/reference/mutations/

## Downloads and redirects

| Content | Endpoint | Notes |
|---------|----------|-------|
| Raw file | `GET /projects/:id/repository/files/:file_path/raw?ref=` | `lfs=true` for LFS content; job tokens allowed |
| Raw blob by SHA | `GET /projects/:id/repository/blobs/:sha/raw` | |
| Repository archive | `GET /projects/:id/repository/archive[.format]` | formats `tar.gz` (default), `zip`, `tar`, `tar.bz2`, `bz2`, `tb2`, `tbz`, `tbz2`; attributes `sha`, `path`, `exclude_paths` (comma-separated), `include_lfs_blobs` (default `true`), `ref_type`; GitLab.com: 5 per minute |
| Job artifacts archive by job | `GET /projects/:id/jobs/:job_id/artifacts` | `file_type` (19.4) to fetch a report such as JUnit; reports are not inside the archive |
| Job artifacts archive by ref | `GET /projects/:id/jobs/artifacts/:ref_name/download?job=<name>` | latest successful pipeline for the ref by creation time; `search_recent_successful_pipelines=true` searches up to 100 recent successful pipelines; parent pipeline wins over child on equal job names |
| Single artifact file by job | `GET /projects/:id/jobs/:job_id/artifacts/*artifact_path` | streamed out of the archive |
| Single artifact file by ref | `GET /projects/:id/jobs/artifacts/:ref_name/raw/*artifact_path?job=<name>` | for merge request pipelines use `refs/merge-requests/:iid/head` as the ref |
| Artifact listing | `GET /projects/:id/jobs/:job_id/artifacts/tree` | |
| Job log (trace) | `GET /projects/:id/jobs/:job_id/trace` | `404` when the job or log does not exist; the docs' example uses `--location` |
| Project export | `GET /projects/:id/export/download` | after the export finished |
| Group export | `GET /groups/:id/export/download` | `404` until ready |
| Markdown upload | `GET /projects/:id/uploads/:secret/:filename` or `.../uploads/:upload_id` | |
| Secure file | `GET /projects/:project_id/secure_files/:id/download` | |
| Release asset | `GET /projects/:id/releases/:tag_name/downloads/:direct_asset_path` | |
| Generic package file | `GET /projects/:id/packages/generic/:package_name/:package_version/:file_name` | |

### Redirects to object storage and CDNs

- On GitLab.com, artifact downloads "might redirect through a CDN"; the docs tell curl users to
  pass `--location`.
- On any instance whose object storage has `proxy_download: false` (the default), GitLab answers
  downloads of artifacts, LFS objects, uploads, packages, Terraform state, secure files and similar
  objects with a redirect to a pre-signed, time-limited URL on the storage provider. With `true`,
  GitLab streams the file itself.
- Since 19.4 administrators can set `allowed_download_modes` so that API clients pick proxy or
  direct mode with a query parameter on supported endpoints; the parameter name is not documented
  on the API pages read (unverified).

### Do not forward the token

The redirect target is authorized by its signature, not by your GitLab token, and is usually
another host. Sending the token there leaks it to the storage provider or CDN.

- curl: headers given with `--header` are sent on every request after a redirect, including to
  other hosts. curl strips only `Authorization:` and `Cookie:` headers when a redirect leaves the
  original origin (unless `--location-trusted`). So `--header "PRIVATE-TOKEN: ..."` or `JOB-TOKEN`
  together with `--location` leaks the token; `--header "Authorization: Bearer ..."` with
  `--location` does not (checked against the curl 8.18.0 manual).
- Python `urllib`: on redirect it copies every header except `Content-Length` and `Content-Type`
  into the new request, whatever the host. Headers added with `Request.add_unredirected_header()`
  are not copied (checked in the Python 3.14 standard library).
- Safest pattern for both: do not follow redirects automatically. Read `Location` from the `302`,
  check it, and fetch it with a new request without GitLab credentials.

Source: https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/api/job_artifacts/ ; https://docs.gitlab.com/api/jobs/ ; https://docs.gitlab.com/api/project_import_export/ ; https://docs.gitlab.com/api/group_import_export/ ; https://docs.gitlab.com/api/project_markdown_uploads/ ; https://docs.gitlab.com/api/secure_files/ ; https://docs.gitlab.com/api/releases/ ; https://docs.gitlab.com/user/packages/generic_packages/ ; https://docs.gitlab.com/administration/object_storage/ ; https://docs.gitlab.com/ci/jobs/ci_job_token/

## Asynchronous and long-running behaviour

`202 Accepted` generally means "scheduled, not done". Endpoints that work in the background:

### Project export and import

1. `POST /projects/:id/export` answers `202` with `{"message": "202 Accepted"}`.
2. Poll `GET /projects/:id/export`. `export_status` moves through `none`, `queued`, `started`,
   `finished`, and `regeneration_in_progress` (an older file is downloadable while a new one is
   built). `_links.api_url` and `_links.web_url` appear only when finished. `created_at` there is
   the project's creation time, not the export's.
3. Download with `GET /projects/:id/export/download`.

Import: `POST /projects/import` (or `remote-import`, `remote-import-s3`) returns the project with
`import_status: "scheduled"`. Poll `GET /projects/:id/import`: `none`, `scheduled`, `started`,
`finished`, `failed`. On `failed`, `import_error` holds the message; `failed_relations` lists up to
100 relations that failed (its `id` values identify the failure records, not the relations).
Relation imports report through `GET /projects/:id/relation-imports` with `created`, `started`,
`finished`, `failed`.

Group export: `POST /groups/:id/export` answers `202`; there is no status endpoint, and
`GET /groups/:id/export/download` returns `404` until the archive exists, so poll the download.
Group import status polling is not described on that page (unverified). Direct transfer between
instances has its own API (`POST /bulk_imports`, `GET /bulk_imports/:id/entities`, failures,
cancel).

### Merge request mergeability, merge and rebase

- `merge_status` (`unchecked`, `checking`, `can_be_merged`, `cannot_be_merged`,
  `cannot_be_merged_recheck`) is deprecated in favour of `detailed_merge_status`.
- Mergeability is recomputed asynchronously when a single merge request is fetched; poll
  `GET /projects/:id/merge_requests/:merge_request_iid` until the value settles. `has_conflicts`
  depends on it. List endpoints do not recompute unless `with_merge_status_recheck=true` is passed,
  which only requests a recheck and can be ignored when an instance feature flag restricts it.
- `detailed_merge_status` values that mean "ask again later": `unchecked`, `checking`,
  `preparing`, `approvals_syncing`, `ci_still_running`. The other values name the blocking
  condition: `mergeable`, `conflict`, `need_rebase`, `not_approved`, `requested_changes`,
  `ci_must_pass`, `discussions_not_resolved`, `draft_status`, `not_open`, `commits_status`,
  `merge_request_blocked`, `merge_time`, `status_checks_must_pass`, `security_policy_violations`,
  `security_policy_pipeline_check`, `jira_association_missing`, `locked_paths`,
  `locked_lfs_files`, `title_regex`. (Which values are transient is this page's reading of the
  value descriptions, not a documented classification.)
- Right after creation, `changes_count`, `diff_refs` and similar fields can be empty;
  `prepared_at` is set once diff, pipelines, mergeability check, LFS linking and notifications are
  done.
- Merge: `PUT .../merge`, optionally with `sha` (required where an instance or group demands it) so
  that only the reviewed head is merged; `auto_merge=true` merges once checks pass, and on projects
  with merge trains the request joins the train.
- Rebase: `PUT .../rebase` (optional `skip_ci`) answers `202` with `{"rebase_in_progress": true}`.
  Poll `GET .../merge_requests/:merge_request_iid?include_rebase_in_progress=true` until
  `rebase_in_progress` is `false`, then read `merge_error` (`null` on success).

### Pipelines

`POST /projects/:id/pipeline` (`ref`, optional `variables` array of hashes and `inputs` hash)
returns the created pipeline; its jobs then run asynchronously, so poll the pipeline or its jobs.
GitLab.com allows 25 pipeline creations per minute per project, user and commit. GraphQL's
`pipelineCreate` has an experimental `async: true` mode that returns a `requestId` instead of the
pipeline.

### Deletions and transfers

| Request | Behaviour |
|---------|-----------|
| `DELETE /projects/:id` | Marks the project for deletion; deleted after the retention period (30 days on GitLab.com, instance setting elsewhere). A second call on an already marked project deletes it immediately; on GitLab.com permanent deletion is not available. `POST /projects/:id/restore` undoes the mark. |
| `DELETE /groups/:id` | `202`, schedules deletion. |
| `DELETE /projects/:id/repository/merged_branches` | `202`; protected branches stay. |
| `DELETE /projects/:id/artifacts` | `202`; sets artifacts to expire now, a scheduled cleanup deletes them later. |
| `PUT /projects/:id/transfer` | Asynchronous since 19.4 (GA); the response is the project as it was before the transfer, so poll the project to see the new namespace (inference from the docs). |
| Vulnerability exports | One export per user and project at a time; a second request while one runs returns `429`. |
| Repository storage moves | `202`, scheduled. |

Source: https://docs.gitlab.com/api/project_import_export/ ; https://docs.gitlab.com/api/group_import_export/ ; https://docs.gitlab.com/api/bulk_imports/ ; https://docs.gitlab.com/api/merge_requests/ ; https://docs.gitlab.com/api/rest/deprecations/ ; https://docs.gitlab.com/api/pipelines/ ; https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/projects/ ; https://docs.gitlab.com/api/groups/ ; https://docs.gitlab.com/api/branches/ ; https://docs.gitlab.com/api/job_artifacts/ ; https://docs.gitlab.com/api/vulnerability_exports/ ; https://docs.gitlab.com/api/project_repository_storage_moves/ ; https://docs.gitlab.com/user/gitlab_com/rate_limits/

## Conditional requests and caching

- General REST: the status table lists `304 Not Modified` and `412 Precondition Failed`, but no
  general ETag or `If-None-Match` support is documented, and the example response carries
  `cache-control: no-cache`. Treat REST responses as uncacheable unless an endpoint says otherwise.
- `If-Unmodified-Since` on `DELETE` can produce `412` when the resource changed in between; which
  endpoints honour it is not stated (unverified).
- Documented ETag endpoints in this snapshot:

| Endpoint | Behaviour |
|----------|-----------|
| `GET /glql/schema` (19.3) | Served with an `ETag`; send `If-None-Match` to get `304`. |
| `GET /orbit/skills`, `GET /orbit/skills/:name`, `GET /orbit/skills/:name/*path` (Premium, Ultimate) | `ETag` plus `Cache-Control: private, max-age=0, must-revalidate`; `If-None-Match` returns `304` with no body; `HEAD` gives the headers without a body. |

- Cheap change detection without ETags: `HEAD /projects/:id/repository/files/:file_path` returns
  `X-Gitlab-Blob-Id`, `X-Gitlab-Content-Sha256` and `X-Gitlab-Last-Commit-Id`; `last_commit_id` on
  file updates and commit actions works as an optimistic lock; generic package downloads carry
  `X-Checksum-SHA256`.

Source: https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/glql/ ; https://docs.gitlab.com/api/orbit/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/user/packages/generic_packages/

## curl recipes

Shared setup for all recipes:

```shell
API="https://gitlab.example.com/api/v4"
# GITLAB_TOKEN holds a personal, project or group access token; never echo it.
```

Authenticate, and find out why a request was refused:

```shell
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$API/user"
# Equivalent header form, also accepted:
curl --silent --show-error --header "Authorization: Bearer $GITLAB_TOKEN" "$API/projects/PROJECT_ID"
# 200 = token fine (look at permissions), 401 = token invalid, 403 = valid but may not read /user
```

URL-encoded project path, file path and branch:

```shell
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$API/projects/my-group%2Fmy-subgroup%2Fmy-project/repository/files/src%2Fapp%2Fmain.py/raw?ref=feature%2Flogin"
```

Follow offset pagination through the headers:

```shell
page=1
while [ -n "$page" ]; do
  curl --silent --show-error --fail \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    --dump-header headers.txt \
    --output "issues-$page.json" \
    "$API/projects/PROJECT_ID/issues?state=opened&per_page=100&page=$page"
  # x-next-page is empty (or missing) on the last page; do not rely on x-total-pages
  page=$(grep -i '^x-next-page:' headers.txt | cut -d: -f2 | tr -d ' \r')
done
```

Follow keyset pagination through the `Link` header:

```shell
url="$API/projects?pagination=keyset&per_page=100&order_by=id&sort=asc"
n=0
while [ -n "$url" ]; do
  n=$((n + 1))
  curl --silent --show-error --fail \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    --dump-header headers.txt \
    --output "projects-$n.json" \
    "$url"
  # keep only the rel="next" URL; it is absent on the last page
  url=$(grep -i '^link:' headers.txt | tr -d '\r' | tr ',' '\n' \
        | grep 'rel="next"' | sed -e 's/.*<\(.*\)>.*/\1/')
done
```

Upload a file and reference it in an issue note (uses `jq`):

```shell
markdown=$(curl --silent --show-error --fail \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --form "file=@screenshot.png" \
  "$API/projects/PROJECT_ID/uploads" | jq -r '.markdown')

curl --silent --show-error --fail --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --data-urlencode "body=Failure reproduced, see screenshot: $markdown" \
  "$API/projects/PROJECT_ID/issues/ISSUE_IID/notes"
```

Create a multi-file commit on a new branch, one file Base64-encoded:

```shell
logo_b64=$(base64 < logo.png | tr -d '\n')
cat > commit.json <<JSON
{
  "branch": "docs/update-readme",
  "start_branch": "main",
  "commit_message": "docs: refresh README and logo",
  "actions": [
    {"action": "update", "file_path": "README.md", "content": "# Project\n\nUpdated text.\n"},
    {"action": "create", "file_path": "assets/logo.png", "content": "$logo_b64", "encoding": "base64"},
    {"action": "move", "file_path": "docs/new-name.md", "previous_path": "docs/old-name.md"},
    {"action": "delete", "file_path": "obsolete.txt"}
  ]
}
JSON
curl --silent --show-error --fail --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data @commit.json \
  "$API/projects/PROJECT_ID/repository/commits"
```

Upload a generic package file (raw body, `PUT` implied by `--upload-file`):

```shell
curl --silent --show-error --fail \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --upload-file dist/tool-1.2.3.tar.gz \
  "$API/projects/PROJECT_ID/packages/generic/tool/1.2.3/tool-1.2.3.tar.gz?select=package_file"
# Inside CI: --header "JOB-TOKEN: $CI_JOB_TOKEN" instead of PRIVATE-TOKEN
```

Download job artifacts through a redirect without leaking the token:

```shell
# Step 1: ask GitLab, do not follow redirects. The body lands in the file if there is no redirect.
read -r code location < <(curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --output artifacts.zip \
  --write-out '%{http_code} %{redirect_url}\n' \
  "$API/projects/PROJECT_ID/jobs/JOB_ID/artifacts")

# Step 2: on a redirect, fetch the signed URL with no GitLab credentials at all.
case "$code" in
  301|302|303|307|308)
    curl --silent --show-error --fail --location --output artifacts.zip "$location" ;;
  200) : ;;  # already downloaded
  *) echo "artifact download failed: HTTP $code" >&2; exit 1 ;;
esac

# Alternative: curl does not pass an Authorization header to another origin, so this is also safe:
# curl --location --header "Authorization: Bearer $GITLAB_TOKEN" --output artifacts.zip "$API/..."
# Never combine --location with --header "PRIVATE-TOKEN: ..." or "JOB-TOKEN: ...".
```

Read rate-limit headers and honour `Retry-After`:

```shell
curl --silent --output /dev/null --dump-header - \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$API/projects/PROJECT_ID" \
  | grep -i -E '^(ratelimit-|retry-after)'

# Minimal retry loop for one request:
for attempt in 1 2 3 4 5; do
  code=$(curl --silent --show-error --dump-header headers.txt --output body.json \
    --write-out '%{http_code}' --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$API/projects/PROJECT_ID/issues?per_page=100")
  [ "$code" != "429" ] && break
  wait=$(grep -i '^retry-after:' headers.txt | cut -d: -f2 | tr -d ' \r')
  sleep "${wait:-$((attempt * 10))}"
done
```

Source: https://docs.gitlab.com/api/rest/ ; https://docs.gitlab.com/api/rest/authentication/ ; https://docs.gitlab.com/api/rest/troubleshooting/ ; https://docs.gitlab.com/api/project_markdown_uploads/ ; https://docs.gitlab.com/api/notes/ ; https://docs.gitlab.com/api/commits/ ; https://docs.gitlab.com/user/packages/generic_packages/ ; https://docs.gitlab.com/api/job_artifacts/ ; https://docs.gitlab.com/administration/settings/user_and_ip_rate_limits/
