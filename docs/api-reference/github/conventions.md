# GitHub REST API: cross-cutting conventions

This page covers everything about the GitHub REST API that is not specific to a
single endpoint: hosts, authentication, headers, encoding, pagination, uploads,
downloads, rate limits, caching, errors and asynchronous behaviour. The
per-endpoint reference generated from the OpenAPI description is linked from
[README.md](README.md). GraphQL mechanics live in `graphql/conventions.md`.

Basis of this page (researched 2026-11-07):

- docs.github.com, the pages named in each `Source:` line.
- The pinned OpenAPI 3.0.3 description of `api.github.com` from
  [github/rest-api-description](https://github.com/github/rest-api-description)
  at commit `2f8f80e` (`info.version` 1.1.4, 837 paths, 1,272 operations, 275
  `x-webhooks` entries). Every count below that says "in the pinned OpenAPI
  file" was computed from that file, not taken from the docs.

Conventions used here: `OWNER`, `REPO`, `HOST`, `SUBDOMAIN` are placeholders;
`$GITHUB_TOKEN` holds a token. "(unverified)" marks a statement I could not
confirm in an official source.

## Hosts and base URLs

| Purpose | GitHub.com | GitHub Enterprise Server | GHE.com (data residency) |
| --- | --- | --- | --- |
| REST API | `https://api.github.com` | `https://HOST/api/v3` | `https://api.SUBDOMAIN.ghe.com` |
| Release-asset uploads | `https://uploads.github.com` | `https://HOST/api/uploads` | not documented; use the `upload_url` the API returns (unverified) |
| GraphQL | `https://api.github.com/graphql` | `https://HOST/api/graphql` | `https://api.SUBDOMAIN.ghe.com/graphql` |

- The docs write the GHES forms as `http(s)://HOST/...`; the scheme depends on
  the appliance. The GHE.com docs use `api.octocorp.ghe.com` as their example
  and point to the instance's `GET /meta` endpoint for the full host list.
- Uploads are the only operation with a different origin. In the pinned
  OpenAPI file, `repos/upload-release-asset` is the single operation that
  overrides `servers` (with `https://uploads.github.com`).
- `upload_url` in a release object is an RFC 6570 URI template, for example
  `https://uploads.github.com/repos/octocat/Hello-World/releases/1/assets{?name,label}`.
  Drop the `{?name,label}` part and append your own query string; do not
  rebuild the URL from parts. More generally, every `*_url` field in a
  response is a hypermedia link (often a template) and should be used as
  given rather than parsed.
- 23 operations in the pinned file declare `301 Moved permanently` (for
  example `repos/get`, `repos/get-branch`, `issues/get`), and
  `PATCH`/`DELETE /repos/{owner}/{repo}` declare `307`. The file does not say
  why; renamed or transferred repositories and issues are the usual cause
  (unverified).

Download redirects leave the API host. The `Location` targets below are what
the pinned OpenAPI examples and the runner-networking docs show; treat them as
illustrative, follow whatever `Location` says, and never hard-code them.

| Download | Redirect host seen | Evidence |
| --- | --- | --- |
| `tarball`/`zipball` archives | `codeload.github.com` (URL carries a `token=` query parameter) | OpenAPI `Location` example |
| Actions job/run logs | `pipelines.actions.githubusercontent.com` | OpenAPI `Location` example |
| Actions artifacts, logs, caches | `results-receiver.actions.githubusercontent.com`, `*.blob.core.windows.net` | runner domain list (purpose stated, endpoint mapping unverified) |
| Release assets (`Accept: application/octet-stream`) | `release-assets.githubusercontent.com` | runner domain list (endpoint mapping unverified) |
| Raw file via `download_url` of the contents API | `raw.githubusercontent.com` | OpenAPI response examples |
| Raw gist files | `gist.githubusercontent.com` | OpenAPI response examples |

Source: [Getting started with the REST API](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api), [GHE.com getting started](https://docs.github.com/en/enterprise-cloud@latest/rest/using-the-rest-api/getting-started-with-the-rest-api), [GHES getting started](https://docs.github.com/en/enterprise-server@latest/rest/using-the-rest-api/getting-started-with-the-rest-api), [GHES release assets](https://docs.github.com/en/enterprise-server@latest/rest/releases/assets), [GHE.com network details](https://docs.github.com/en/enterprise-cloud@latest/admin/data-residency/network-details-for-ghecom), [Self-hosted runner domains](https://docs.github.com/en/actions/reference/runners/self-hosted-runners), [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), pinned OpenAPI file.

## Authentication

**Header forms.** Send `Authorization: Bearer TOKEN`; `Authorization: token TOKEN`
also works for most token kinds, but a GitHub App JWT must use `Bearer`.
Username/password Basic auth is not supported. A few OAuth-app and GitHub-App
endpoints take Basic auth with the app's client ID and client secret instead;
those credentials identify the app, not a user. Some endpoints answer without
any credentials; such calls are limited per IP address (see Rate limits).

| Token type | What it can reach | Lifetime | Notes for a repo-scoped wrapper |
| --- | --- | --- | --- |
| Personal access token (classic) | Everything the user can reach, in every org and personal repo, narrowed only by OAuth scopes | Set at creation; GitHub deletes tokens unused for a year | Coarse. Must be separately authorized for each SAML SSO org. Only classic PATs can write to public repos the user does not own. |
| Fine-grained PAT | One resource owner (a user or an org); all repos, selected repos, or public repos read-only; per-permission read/write | Set at creation; org or enterprise policy may cap it | The natural fit for "one token, one repo". Documented gaps: no Checks API, no Packages, no Projects owned by a user, no repos where the user is an outside collaborator, no contributing to public repos the user is not a member of, no multi-org access. |
| GitHub App JWT | Only app-level endpoints such as `POST /app/installations/{installation_id}/access_tokens` | `exp` at most 10 minutes ahead; set `iat` about 60 s in the past | Signed RS256 with the app's private key; `iss` is the client ID or app ID. |
| GitHub App installation token | What the installation was granted, optionally narrowed per token to a permission subset and up to 500 repositories | 1 hour | Acts as the app, not a user. |
| GitHub App user access token | The intersection of the app's permissions and the user's access | 8 hours (refresh token 6 months) when expiry is enabled | Actions are attributed to the user. |
| OAuth app token | The user's access, narrowed by scopes | Not covered here | GitHub recommends GitHub Apps over OAuth apps; orgs can block OAuth app access. |
| `GITHUB_TOKEN` (Actions) | The repository that holds the workflow, with the permissions set by the `permissions` key | Expires when the job ends or at its maximum lifetime | It is an installation token. Events it causes mostly do not start new workflow runs; `workflow_dispatch` and `repository_dispatch` do, and `pull_request` opened/synchronize/reopened runs wait for approval. |

**Discovering what a call needs.** Responses carry headers that tell you which
grants matter:

| Header | Sent for | Meaning |
| --- | --- | --- |
| `X-OAuth-Scopes` | classic PATs, OAuth tokens | Scopes the token has |
| `X-Accepted-OAuth-Scopes` | classic PATs, OAuth tokens | Scopes this endpoint checks for |
| `X-Accepted-GitHub-Permissions` | GitHub Apps, fine-grained PATs | Permissions the endpoint needs. Commas join permissions that are all required; semicolons separate alternative sets, for example `pull_requests=read,contents=read; issues=read,contents=read`. |

Scopes only restrict what a user can already do; they never add access. When
an App or fine-grained token lacks a permission, the error message reads
"Resource not accessible by integration" or "... by personal access token".
The per-endpoint permission tables are on the fine-grained permissions page;
in the pinned OpenAPI file 1,024 operations are flagged
`x-github.enabledForGitHubApps: true` and 243 `false`.

**SAML SSO.** A classic PAT that is not authorized for an SSO-enforcing org
gets `403` with an `X-GitHub-SSO` header containing a URL to authorize it; that
URL expires after one hour. When a list spans several
orgs, the header instead names the orgs that still need authorization, for
example `X-GitHub-SSO: partial-results; organizations=21955855,20582480`.
Fine-grained PATs are authorized during creation, and tokens created by apps
are authorized automatically.

**404 instead of 403.** For private resources GitHub answers `404` when the
caller is unauthenticated or lacks access, so that it does not reveal that
the resource exists. A `404` on something you know exists usually means a
token problem. Separately, a burst of requests with bad credentials makes the
API reject all authentication for that user, valid tokens included, with
`403` for a while.

Source: [Authenticating to the REST API](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api), [Permissions required for fine-grained PATs](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens), [Managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), [Scopes for OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps), [Generating a JWT](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app), [Installation access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app), [Refreshing user access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens), [Acting on behalf of a user](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user), [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token), [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api), [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), pinned OpenAPI file.

## Headers, media types and API versions

**Request headers every call should send**

| Header | Value | Why |
| --- | --- | --- |
| `Accept` | `application/vnd.github+json` | The documented default media type; `application/json` is also accepted. What the server assumes when `Accept` is missing is not stated (unverified). |
| `X-GitHub-Api-Version` | `2022-11-28` or `2026-03-10` | Pins the response shape (below). |
| `User-Agent` | Your app or user name | Required. A missing or invalid value gets `403`. curl sends `curl/VERSION` by default, which satisfies the rule. |
| `Authorization` | See Authentication | |

The response header `X-GitHub-Media-Type` echoes what was applied (the docs'
sample shows `github.v3; format=json`).

**Custom media types.** Pass them in `Accept`. Only endpoints whose
description lists a type honour it. The table is derived from the operation
descriptions in the pinned OpenAPI file.

| Media type | Effect | Where documented |
| --- | --- | --- |
| `application/vnd.github.raw+json` | Markdown bodies come back as `body` (the default for issues, PRs and comments); for files and blobs the response is the raw bytes instead of JSON | issues, issue comments, pulls, review-related pulls endpoints, `repos/get-content`, `git/get-blob`, `repos/get-readme`, `repos/get-readme-in-directory`, `licenses/get-for-repo`, `gitignore/get-template`, gists and gist comments (43 operations) |
| `application/vnd.github.text+json` | Adds a plain-text rendering, `body_text` | issues, issue comments, pulls (30 operations) |
| `application/vnd.github.html+json` | Adds `body_html`; for contents, README and license it returns rendered HTML | issues, pulls, `repos/get-content`, READMEs, `licenses/get-for-repo` (34 operations) |
| `application/vnd.github.full+json` | `body`, `body_text` and `body_html` together | issues, pulls (30 operations) |
| `application/vnd.github-commitcomment.{raw,text,html,full}+json` | Same four variants, but with a different prefix | commit comments, PR review comments, PR reviews (19 operations) |
| `application/vnd.github.diff` | Unified diff text | `repos/get-commit`, `repos/compare-commits`, `pulls/get` |
| `application/vnd.github.patch` | `git format-patch` style text | `repos/get-commit`, `repos/compare-commits`. The getting-started page also names pull requests; `pulls/get` lists only `diff` in the pinned file (unverified for PRs). |
| `application/vnd.github.sha` | Only the commit SHA as text; combine with `If-None-Match` to test whether a ref moved | `repos/get-commit` |
| `application/vnd.github.object+json` | Always an object, even for directories | `repos/get-content` |
| `application/vnd.github.star+json` | Adds `starred_at` to each entry | stargazers, starred-repo lists (3 operations) |
| `application/vnd.github.text-match+json` | Adds `text_matches` to search results | search endpoints |
| `application/vnd.github.v3.repository+json` | Returns the repository with the team's permissions | `teams/check-permissions-for-repo-in-org` |
| `application/octet-stream` | Binary download (`200`, or `302` to storage) | `repos/get-release-asset` |
| `application/sarif+json` | SARIF instead of JSON | `code-scanning/get-analysis` (2026-03-10 fixed the `Content-Type` from `application/json+sarif`) |

On `repos/get-commit` the diff, patch and sha types disable pagination, and
large diffs can time out with a `5xx`.

**API versions.** The `X-GitHub-Api-Version` header selects a dated version.

| Version | Status (per docs on 2026-11-07) |
| --- | --- |
| `2026-03-10` | Current, released 10 March 2026, end of support not scheduled |
| `2022-11-28` | Still supported until 10 March 2028; **the default when the header is omitted** |

- A version string the server does not recognise gets `400 Bad Request`
  (troubleshooting page); a version that has been retired gets `410 Gone`
  (versions page).
- When a new version ships, the previous one stays supported for at least 24
  months. As end of support approaches, responses carry `Deprecation` and
  `Sunset` headers (HTTP dates).
- Additive changes (new operations, optional parameters, response fields,
  headers, enum values) appear in all supported versions. Breaking changes
  (removals, renames, type changes, new required parameters, removed enum
  values, changed auth) only ship in a new dated version, announced with a
  per-version changelog on the breaking-changes page.
- The pinned OpenAPI file describes the `2022-11-28` shapes and attaches
  `x-github-breaking-changes` patches (all tagged `2026-03-10`) to 21
  operations. A generator that renders `2026-03-10` must apply those patches.
- docs.github.com examples now often send `X-GitHub-Api-Version: 2026-03-10`.
  A wrapper should always send the header explicitly.

The 2026-03-10 changes that matter most for a repository wrapper:

| Change | Effect on a client |
| --- | --- |
| Workflow dispatch returns `200` with run details | `return_run_details` is gone; the body now carries the run ID and URLs |
| Singular `assignee` removed from issues and PRs | Use `assignees` (array) in requests and responses |
| `merge_commit_sha` removed from PR payloads | Take the merge commit from the `sha` that `pulls/merge` returns, or from `pulls/get-merge-async-result` |
| Directory listings report submodules as `"submodule"` | No longer `"file"` |
| `rate` removed from `GET /rate_limit` | Read `resources.core` |
| `use_squash_pr_title_as_default` and `has_downloads` removed from repositories | Use `squash_merge_commit_title` |
| Trade-control blocks return `451` | Instead of `403` or `422` on several endpoints |
| Deleting an installation returns `202` | Instead of `204`; deletion runs in the background |
| `beta` media type dropped | Affects some email and repository fields |

Source: [Getting started](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api), [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions), [Breaking changes](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes), [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api), [Search](https://docs.github.com/en/rest/search/search), [Dependency submission](https://docs.github.com/en/rest/dependency-graph/dependency-submission), pinned OpenAPI file. (There is no separate "media types" page; the old `.../media-types` URL appears to serve the getting-started page.)

## Request encoding

**JSON bodies.** Send `Content-Type: application/json` and a JSON object.
Invalid JSON gets `400` "Problems parsing JSON"; valid JSON that is not an
object, where an object is expected, gets `400` "Body should be a JSON object".
In the pinned OpenAPI file, 364 operations take `application/json`.
Exceptions and edge cases:

- Bare arrays are accepted (as an alternative to an object) by
  `issues/add-labels`, `issues/set-labels`, `users/add-email-for-authenticated-user`,
  `users/delete-email-for-authenticated-user`, and the branch-protection
  `required_status_checks/contexts` and `restrictions/teams` add/set/remove
  operations.
- `DELETE` can carry a JSON body. 20 operations define one, including
  `repos/delete-file` (needs `message` and `sha`), `issues/remove-assignees`,
  `pulls/remove-requested-reviewers` and `issues/remove-sub-issue`. A wrapper
  must not drop the body on `DELETE`.
- 32 `PUT` operations have no body at all. Several of them (for example
  `activity/star-repo-for-authenticated-user`, `users/follow`, `issues/lock`
  without parameters, `repos/add-collaborator` without parameters,
  `gists/star`) say you must send `Content-Length: 0`.
- Only two operations take a non-JSON body: `markdown/render-raw`
  (`text/plain` or `text/x-markdown`) and `repos/upload-release-asset`
  (`application/octet-stream`). See Uploads. (Code scanning SARIF is gzip and
  Base64 inside a JSON field, so it counts as JSON.)

**Path parameters.**

- The pinned OpenAPI file marks 68 parameter uses with `x-multi-segment: true`:
  `ref`, `branch`, `path` (contents API), `commit_sha`, `basehead`, `tree_sha`,
  `dir`, `tag`, `sha` and `subject_digest`. Their values may contain `/` and the
  slash stays literal, for example
  `GET /repos/OWNER/REPO/git/ref/heads/feature/login`,
  `GET /repos/OWNER/REPO/branches/feature/login`,
  `PUT /repos/OWNER/REPO/contents/docs/guide/intro.md`.
  Percent-encode each segment (spaces, `#`, `?`, non-ASCII) but not the slashes
  between segments.
- Other parameters are single segments. `environment_name` is documented as
  needing URL encoding, with `/` written as `%2F`. Label names in
  `/labels/{name}` are not multi-segment, so encode `/` there too (unverified
  server behaviour).
- `ref` in the Git refs endpoints omits the `refs/` prefix (`heads/main`,
  `tags/v1.0`), whereas the body of `git/create-ref` needs the full
  `refs/heads/...` name with at least two slashes. `commits/{ref}` takes a SHA,
  a branch name, `heads/BRANCH` or `tags/TAG`.
- `basehead` is `BASE...HEAD`; across forks it is `USER:BASE...USER:HEAD`.
- `owner` and `repo` are not case sensitive; `repo` is given without `.git`.
- A trailing slash on a path gives `404`. `branch` cannot contain wildcards;
  the branch descriptions send you to GraphQL for wildcard patterns.

**Query strings.**

- Arrays: repeat the name with `[]` appended, for example
  `?repository_ids[]=1&repository_ids[]=2`. Only 11 query parameters are typed
  `array` in the pinned file; many "list" filters are plain strings with
  comma-separated values, for example `labels=bug,ui,@high` on
  `issues/list-for-repo`. Check each parameter's type.
- Booleans: 35 query parameters are typed `boolean`; send `true` or `false`
  (the docs do not spell out the accepted spellings; unverified). Some flags
  are presence-only: `recursive` on `git/get-tree` turns recursion on for any
  value, including `0` and `false`, so omit it to turn it off.

**Timestamps and time zones.** Responses use UTC ISO 8601
(`YYYY-MM-DDTHH:MM:SSZ`). For requests that create data with a timestamp
(commits through the contents API, for example), the time zone is chosen in
this order: an explicit offset in a timestamp you supply (for example
`2014-02-27T15:05:06+01:00`), then a `Time-Zone` header with an Olson name
(`Time-Zone: Europe/Amsterdam`), then the user's last known time zone for
authenticated calls, then UTC.

**Identifiers.** Some numeric IDs are 64-bit (for example `job_id` is typed
`int64`). Keep them as integers, never as floating point. The `node_id` field
is the GraphQL global ID of the same object (see the GraphQL conventions).

Source: [Getting started](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api), [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api), [Timezones and the REST API](https://docs.github.com/en/rest/using-the-rest-api/timezones-and-the-rest-api), [Git references](https://docs.github.com/en/rest/git/refs), pinned OpenAPI file.

## Pagination

**Link header.** Paginated responses carry a `link` header with up to four
relations: `next`, `prev`, `first` and `last`, for example
`<https://api.github.com/repositories/1300192/issues?page=4>; rel="next"`.
The header is absent when the endpoint does not paginate or everything fit on
one page. Follow the URLs exactly as given; the query parameters inside them
differ between endpoints.

**Three paging styles.** Every paginated endpoint uses one of these:

| Style | Parameters | Notes |
| --- | --- | --- |
| Page number | `page` (from 1), `per_page` | The most common style |
| Cursor | `before` / `after` (opaque strings from the `link` header), `per_page` | 36 operations in the pinned file, e.g. Dependabot, code scanning, secret scanning, advisories, attestations, `repos/list-activities`, Projects v2 lists. Four of them (code scanning and secret scanning alerts, repo and org) accept `page` as well. |
| ID cursor | `since` (an ID; only higher IDs are returned) | `users/list`, `orgs/list`, `repos/list-public`, `migrations/get-commit-authors` |

`before` is not always a cursor: on `activity/list-notifications-for-authenticated-user`,
`activity/list-repo-notifications-for-authenticated-user` and
`repos/list-for-authenticated-user` it is an ISO 8601 timestamp filter.

**`per_page`.** The default is 30 and the maximum 100 for most endpoints. A
value above the maximum is silently reduced, with no error. Without paging you
get only the first page (30 items). The pinned OpenAPI file has these
departures from 30/100 (284 operations take `per_page`):

| Operations | Default | Maximum |
| --- | --- | --- |
| `activity/list-notifications-for-authenticated-user` | 50 | 50 |
| `activity/list-public-events` | 15 | 100 |
| `copilot/list-copilot-seats` | 50 | 100 |
| `billing/get-all-budgets-org` | 10 | 100 |
| Actions and agents variable lists (`actions/list-repo-variables`, `actions/list-org-variables`, `actions/list-environment-variables`, `actions/list-repo-organization-variables` and the `agents/` equivalents) | 10 | 30 |
| `activity/get-stargazer-history-for-repo` | 30 | 30 |

**Result caps.** Search endpoints return at most 1,000 results per query
(more pages do not help; narrow the query instead) and look at no more than
4,000 matching repositories. `actions/list-workflow-runs` and
`actions/list-workflow-runs-for-repo` also cap at 1,000 results when filtered
by `actor`, `branch`, `check_suite_id`, `created`, `event` and similar
parameters.

**Lists wrapped in an object.** Most paginated endpoints return a JSON array.
Some return an object that holds the array under a key, usually next to
`total_count`. In the pinned OpenAPI file, 286 operations take `per_page`,
`before` or `after`; 192 return an array and the 94 below return an object.
"Item key" is the property that holds the paged list.

| operationId | Method | Path | Item key | `total_count` |
| --- | --- | --- | --- | --- |
| `agent-automations/list-repo-automations` | GET | `/agents/repos/{owner}/{repo}/automations` | `automations` | yes |
| `agent-automations/list-automation-revisions` | GET | `/agents/repos/{owner}/{repo}/automations/{automation_id}/revisions` | `revisions` | no |
| `agent-automations/list-repo-automation-tasks` | GET | `/agents/repos/{owner}/{repo}/automations/{automation_id}/tasks` | `tasks` | no |
| `agent-tasks/list-tasks-for-repo` | GET | `/agents/repos/{owner}/{repo}/tasks` | `tasks` | no |
| `agent-tasks/list-tasks` | GET | `/agents/tasks` | `tasks` | no |
| `dependabot/repository-access-for-enterprise` | GET | `/enterprises/{enterprise}/dependabot/repository-access` | `accessible_repositories` | no |
| `apps/list-repos-accessible-to-installation` | GET | `/installation/repositories` | `repositories` | yes |
| `billing/get-all-budgets-org` | GET | `/organizations/{org}/settings/billing/budgets` | `budgets` | yes |
| `actions/get-actions-cache-usage-by-repo-for-org` | GET | `/orgs/{org}/actions/cache/usage-by-repository` | `repository_cache_usages` | yes |
| `actions/list-hosted-runners-for-org` | GET | `/orgs/{org}/actions/hosted-runners` | `runners` | yes |
| `actions/list-selected-repositories-enabled-github-actions-organization` | GET | `/orgs/{org}/actions/permissions/repositories` | `repositories` | yes |
| `actions/list-selected-repositories-self-hosted-runners-organization` | GET | `/orgs/{org}/actions/permissions/self-hosted-runners/repositories` | `repositories` | yes |
| `actions/get-org-actions-policies` | GET | `/orgs/{org}/actions/policies` | `policies` | yes |
| `actions/list-self-hosted-runner-groups-for-org` | GET | `/orgs/{org}/actions/runner-groups` | `runner_groups` | yes |
| `actions/list-github-hosted-runners-in-group-for-org` | GET | `/orgs/{org}/actions/runner-groups/{runner_group_id}/hosted-runners` | `runners` | yes |
| `actions/list-repo-access-to-self-hosted-runner-group-in-org` | GET | `/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories` | `repositories` | yes |
| `actions/list-self-hosted-runners-in-group-for-org` | GET | `/orgs/{org}/actions/runner-groups/{runner_group_id}/runners` | `runners` | yes |
| `actions/list-self-hosted-runners-for-org` | GET | `/orgs/{org}/actions/runners` | `runners` | yes |
| `actions/list-org-secrets` | GET | `/orgs/{org}/actions/secrets` | `secrets` | yes |
| `actions/list-selected-repos-for-org-secret` | GET | `/orgs/{org}/actions/secrets/{secret_name}/repositories` | `repositories` | yes |
| `actions/list-org-variables` | GET | `/orgs/{org}/actions/variables` | `variables` | yes |
| `actions/list-selected-repos-for-org-variable` | GET | `/orgs/{org}/actions/variables/{name}/repositories` | `repositories` | yes |
| `agents/list-org-secrets` | GET | `/orgs/{org}/agents/secrets` | `secrets` | yes |
| `agents/list-selected-repos-for-org-secret` | GET | `/orgs/{org}/agents/secrets/{secret_name}/repositories` | `repositories` | yes |
| `agents/list-org-variables` | GET | `/orgs/{org}/agents/variables` | `variables` | yes |
| `agents/list-selected-repos-for-org-variable` | GET | `/orgs/{org}/agents/variables/{name}/repositories` | `repositories` | yes |
| `orgs/list-attestations-bulk` | POST | `/orgs/{org}/attestations/bulk-list` | `attestations_subject_digests` (object keyed by digest, values are arrays) | no |
| `orgs/list-attestations` | GET | `/orgs/{org}/attestations/{subject_digest}` | `attestations` | no |
| `codespaces/list-in-organization` | GET | `/orgs/{org}/codespaces` | `codespaces` | yes |
| `codespaces/list-org-secrets` | GET | `/orgs/{org}/codespaces/secrets` | `secrets` | yes |
| `codespaces/list-selected-repos-for-org-secret` | GET | `/orgs/{org}/codespaces/secrets/{secret_name}/repositories` | `repositories` | yes |
| `copilot-spaces/list-for-org` | GET | `/orgs/{org}/copilot-spaces` | `spaces` | no |
| `copilot/list-copilot-seats` | GET | `/orgs/{org}/copilot/billing/seats` | `seats` | no |
| `copilot/list-copilot-coding-agent-selected-repositories-for-organization` | GET | `/orgs/{org}/copilot/coding-agent/permissions/repositories` | `repositories` | yes |
| `dependabot/repository-access-for-org` | GET | `/orgs/{org}/dependabot/repository-access` | `accessible_repositories` | no |
| `dependabot/list-org-secrets` | GET | `/orgs/{org}/dependabot/secrets` | `secrets` | yes |
| `dependabot/list-selected-repos-for-org-secret` | GET | `/orgs/{org}/dependabot/secrets/{secret_name}/repositories` | `repositories` | yes |
| `orgs/list-app-installations` | GET | `/orgs/{org}/installations` | `installations` | yes |
| `codespaces/get-codespaces-for-user-in-org` | GET | `/orgs/{org}/members/{username}/codespaces` | `codespaces` | yes |
| `private-registries/list-org-private-registries` | GET | `/orgs/{org}/private-registries` | `configurations` | yes |
| `orgs/get-immutable-releases-settings-repositories` | GET | `/orgs/{org}/settings/immutable-releases/repositories` | `repositories` | yes |
| `hosted-compute/list-network-configurations-for-org` | GET | `/orgs/{org}/settings/network-configurations` | `network_configurations` | yes |
| `actions/list-artifacts-for-repo` | GET | `/repos/{owner}/{repo}/actions/artifacts` | `artifacts` | yes |
| `actions/get-actions-cache-list` | GET | `/repos/{owner}/{repo}/actions/caches` | `actions_caches` | yes |
| `actions/list-concurrency-groups-for-repository` | GET | `/repos/{owner}/{repo}/actions/concurrency_groups` | `concurrency_groups` | yes |
| `actions/list-repo-organization-secrets` | GET | `/repos/{owner}/{repo}/actions/organization-secrets` | `secrets` | yes |
| `actions/list-repo-organization-variables` | GET | `/repos/{owner}/{repo}/actions/organization-variables` | `variables` | yes |
| `actions/get-repo-actions-policies` | GET | `/repos/{owner}/{repo}/actions/policies` | `policies` | yes |
| `actions/list-self-hosted-runners-for-repo` | GET | `/repos/{owner}/{repo}/actions/runners` | `runners` | yes |
| `actions/list-workflow-runs-for-repo` | GET | `/repos/{owner}/{repo}/actions/runs` | `workflow_runs` | yes |
| `actions/list-workflow-run-artifacts` | GET | `/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts` | `artifacts` | yes |
| `actions/list-jobs-for-workflow-run-attempt` | GET | `/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs` | `jobs` | yes |
| `actions/list-concurrency-groups-for-workflow-run` | GET | `/repos/{owner}/{repo}/actions/runs/{run_id}/concurrency_groups` | `concurrency_groups` | yes |
| `actions/list-jobs-for-workflow-run` | GET | `/repos/{owner}/{repo}/actions/runs/{run_id}/jobs` | `jobs` | yes |
| `actions/list-repo-secrets` | GET | `/repos/{owner}/{repo}/actions/secrets` | `secrets` | yes |
| `actions/list-repo-variables` | GET | `/repos/{owner}/{repo}/actions/variables` | `variables` | yes |
| `actions/list-repo-workflows` | GET | `/repos/{owner}/{repo}/actions/workflows` | `workflows` | yes |
| `actions/list-workflow-runs` | GET | `/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs` | `workflow_runs` | yes |
| `agents/list-repo-organization-secrets` | GET | `/repos/{owner}/{repo}/agents/organization-secrets` | `secrets` | yes |
| `agents/list-repo-organization-variables` | GET | `/repos/{owner}/{repo}/agents/organization-variables` | `variables` | yes |
| `agents/list-repo-secrets` | GET | `/repos/{owner}/{repo}/agents/secrets` | `secrets` | yes |
| `agents/list-repo-variables` | GET | `/repos/{owner}/{repo}/agents/variables` | `variables` | yes |
| `repos/list-attestations` | GET | `/repos/{owner}/{repo}/attestations/{subject_digest}` | `attestations` | no |
| `checks/list-for-suite` | GET | `/repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs` | `check_runs` | yes |
| `codespaces/list-in-repository-for-authenticated-user` | GET | `/repos/{owner}/{repo}/codespaces` | `codespaces` | yes |
| `codespaces/list-devcontainers-in-repository-for-authenticated-user` | GET | `/repos/{owner}/{repo}/codespaces/devcontainers` | `devcontainers` | yes |
| `codespaces/list-repo-secrets` | GET | `/repos/{owner}/{repo}/codespaces/secrets` | `secrets` | yes |
| `repos/get-commit` | GET | `/repos/{owner}/{repo}/commits/{ref}` | `files` (pages the changed files; `parents` is not paged) | no |
| `checks/list-for-ref` | GET | `/repos/{owner}/{repo}/commits/{ref}/check-runs` | `check_runs` | yes |
| `checks/list-suites-for-ref` | GET | `/repos/{owner}/{repo}/commits/{ref}/check-suites` | `check_suites` | yes |
| `repos/get-combined-status-for-ref` | GET | `/repos/{owner}/{repo}/commits/{ref}/status` | `statuses` | yes |
| `repos/compare-commits` | GET | `/repos/{owner}/{repo}/compare/{basehead}` | `commits` (`files` is sent on the first page only) | no |
| `dependabot/list-repo-secrets` | GET | `/repos/{owner}/{repo}/dependabot/secrets` | `secrets` | yes |
| `repos/get-all-environments` | GET | `/repos/{owner}/{repo}/environments` | `environments` | yes |
| `repos/list-deployment-branch-policies` | GET | `/repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies` | `branch_policies` | yes |
| `repos/list-custom-deployment-rule-integrations` | GET | `/repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/apps` | `available_custom_deployment_protection_rule_integrations` | yes |
| `actions/list-environment-secrets` | GET | `/repos/{owner}/{repo}/environments/{environment_name}/secrets` | `secrets` | yes |
| `actions/list-environment-variables` | GET | `/repos/{owner}/{repo}/environments/{environment_name}/variables` | `variables` | yes |
| `issues/get-issue-artifact` | GET | `/repos/{owner}/{repo}/issues/{issue_number}/artifacts/{artifact_number}` | `versions` | yes |
| `repos/get-all-topics` | GET | `/repos/{owner}/{repo}/topics` | `names` | no |
| `search/code` | GET | `/search/code` | `items` | yes |
| `search/commits` | GET | `/search/commits` | `items` | yes |
| `search/issues-and-pull-requests` | GET | `/search/issues` | `items` | yes |
| `search/labels` | GET | `/search/labels` | `items` | yes |
| `search/repos` | GET | `/search/repositories` | `items` | yes |
| `search/topics` | GET | `/search/topics` | `items` | yes |
| `search/users` | GET | `/search/users` | `items` | yes |
| `codespaces/list-for-authenticated-user` | GET | `/user/codespaces` | `codespaces` | yes |
| `codespaces/list-secrets-for-authenticated-user` | GET | `/user/codespaces/secrets` | `secrets` | yes |
| `apps/list-installations-for-authenticated-user` | GET | `/user/installations` | `installations` | yes |
| `apps/list-installation-repos-for-authenticated-user` | GET | `/user/installations/{installation_id}/repositories` | `repositories` | yes |
| `users/list-attestations-bulk` | POST | `/users/{username}/attestations/bulk-list` | `attestations_subject_digests` (object keyed by digest, values are arrays) | no |
| `users/list-attestations` | GET | `/users/{username}/attestations/{subject_digest}` | `attestations` | no |
| `copilot-spaces/list-for-user` | GET | `/users/{username}/copilot-spaces` | `spaces` | no |

**Documented hard caps on list sizes** (from operation descriptions in the
pinned OpenAPI file unless noted):

| Endpoint | Cap |
| --- | --- |
| `repos/compare-commits` | Without `page`/`per_page`, 250 commits. With paging, `files` appears on the first page only and holds at most 300 files for the whole comparison. |
| `repos/get-commit` | Above 300 changed files, the file list is paginated, up to 3,000 files in total |
| `pulls/list-commits` | 250 commits; use `repos/list-commits` for more |
| `pulls/list-files` | 3,000 files (30 per page by default) |
| `repos/get-content` (directory) | 1,000 entries; use the Git trees API for more |
| `git/get-tree` with `recursive` | 100,000 entries or 7 MB; `truncated: true` when exceeded |
| `checks/list-for-ref` | Considers only the 1,000 most recent check suites on the ref |
| `gists/list-public` | 3,000 gists reachable by paging |
| `gists/get` | 300 files listed; file content truncated above 1 MB (use `raw_url`), clone above 10 MB (gists docs) |
| `repos/create-commit-status` | 1,000 statuses per `sha` and `context` |
| `repos/list-contributors` | Only the first 500 author emails map to GitHub users |
| Search | 1,000 results per query; code search only covers the default branch and files under 384 KB (search docs) |

Source: [Using pagination in the REST API](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api), [Search](https://docs.github.com/en/rest/search/search), [Gists](https://docs.github.com/en/rest/gists/gists), [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api), pinned OpenAPI file.

## Uploads and binary request bodies

**Release assets** (`repos/upload-release-asset`,
`POST /repos/{owner}/{repo}/releases/{release_id}/assets`):

- Host `uploads.github.com` (GHES: `https://HOST/api/uploads`). Take the URL
  from the release's `upload_url` template.
- Query: `name` (required), `label` (optional).
- Body: the raw file bytes, not JSON. `Content-Type` is required and is the
  asset's own media type (for example `application/zip`, or
  `application/octet-stream`). `Content-Length` is required; most clients set
  it. The client must support SNI.
- `201` on success. Uploading a name that already exists gives `422`; delete
  the old asset first. An upstream failure gives `502` and can leave an empty
  asset in state `starter`, which is safe to delete. Names with special
  characters, or leading or trailing dots, are renamed by GitHub; read the
  real name back from the response or the asset list.
- Limits (releases docs): each file under 2 GiB, at most 1,000 assets per
  release, no limit on the total size of a release or on bandwidth.

**Contents API** (`repos/create-or-update-file-contents`,
`PUT /repos/{owner}/{repo}/contents/{path}`; `repos/delete-file`,
`DELETE` on the same path):

- JSON body: `message`, `content` (the file, Base64-encoded), optional
  `branch` (defaults to the default branch), optional `committer` and `author`
  (`name` and `email` both required when given; defaults to the
  authenticated user).
- Updating or deleting needs `sha`, the blob SHA of the file being replaced.
  Get it from `GET .../contents/{path}?ref=BRANCH`. The operation declares
  `409` and `422`; which one a stale `sha` produces is not documented
  (unverified).
- `201` when a file is created, `200` when updated. Do not run this endpoint
  and "Delete a file" in parallel; concurrent calls conflict.
- Writing under `.github/workflows/` needs the `workflow` scope for classic
  PATs and OAuth tokens. The fine-grained equivalent is the "Workflows"
  repository permission (unverified).
- Each call is one commit for one file. On an empty repository this is the
  way to make the first commit, because the Git database API returns `409`
  on empty repositories.
- Read-side size limits: up to 1 MB everything works; 1 MB to 100 MB only the
  `raw` or `object` media types work (with `object`, `content` is empty and
  `encoding` is `"none"`); above 100 MB the endpoint is unsupported. The
  write-side maximum is not documented (unverified).

**Git database** (blobs, trees, commits, refs) is the route for multi-file or
atomic commits and for full control over author and committer:

1. `POST /repos/{owner}/{repo}/git/blobs` with `content` and `encoding`
   (`utf-8`, the default, or `base64`). Returns the blob `sha`.
2. `POST .../git/trees` with `base_tree` (the current commit's tree) and a
   `tree` array of changed entries (`path`, `mode`, `type`, and either `sha`
   or inline `content`).
3. `POST .../git/commits` with `message`, `tree`, `parents`, and optionally
   `author`, `committer` and `signature`.
4. `PATCH .../git/refs/heads/BRANCH` with the new `sha` (`force` defaults to
   `false`, so a non-fast-forward is refused).

`git/get-blob` serves blobs up to 100 MB (Base64 in JSON, or raw bytes with
`application/vnd.github.raw+json`). The GraphQL mutation `createCommitOnBranch`
does the same in one call, but the author is always the token's owner and
cannot be set (see the GraphQL conventions).

**Gists** (`gists/create`, `gists/update`): JSON with
`files: {"NAME": {"content": "..."}}`. In an update, `null` for a file deletes
it and `filename` renames it.

**Code scanning SARIF** (`code-scanning/upload-sarif`,
`POST /repos/{owner}/{repo}/code-scanning/sarifs`): a JSON body whose `sarif`
field is the SARIF file gzip-compressed and then Base64-encoded
(`gzip -c file.sarif | base64 -w0`), plus `commit_sha` and the full `ref`
(`refs/heads/BRANCH` or `refs/pull/N/merge`). The compressed file may be at
most 10 MB; there are per-object maximums (for example 20 runs per file,
25,000 results per run, of which only the top 5,000 are kept). Answer: `202`
with an `id`; poll `GET .../code-scanning/sarifs/{sarif_id}` for processing
status. `413` if `sarif` is too large. Limited to 1,000 requests per hour per
user or installation.

**Dependency snapshots** (`dependency-graph/create-repository-snapshot`,
`POST /repos/{owner}/{repo}/dependency-graph/snapshots`): plain JSON
(`version`, `job` with `id` and `correlator`, `sha`, `ref`, `detector`,
`scanned`, `manifests`, optional `metadata` of at most 8 scalar keys);
`201` on success. It has its own rate-limit bucket, `dependency_snapshots`.

**Markdown rendering**: `POST /markdown` takes JSON (`text`, `mode` of
`markdown` or `gfm`, optional `context` repository); `POST /markdown/raw`
takes the Markdown itself as a `text/plain` or `text/x-markdown` body, at most
400 KB, rendered like a README (no GFM). Both answer `text/html`.

**Issue artifacts** (new in the pinned file: `issues/create-issue-artifact`
and friends under `/repos/{owner}/{repo}/issues/{issue_number}/artifacts`)
are text, not files: JSON with `name`, `body` and `type` (`generic`, `link`,
`plan` or `embedded_html`). Writes can be throttled with `429` and a
`Retry-After` header.

**No public REST upload exists for:**

- Attachments (images, videos, files) in issue, PR and discussion comments.
  The attachments docs describe browser upload only, and the pinned OpenAPI
  file has no such operation. Link to content hosted elsewhere, for example a
  release asset or a file committed to the repo.
- Actions artifacts. The artifacts REST API lists, downloads and deletes; it
  has no upload operation.

Source: [Release assets](https://docs.github.com/en/rest/releases/assets), [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), [Repository contents](https://docs.github.com/en/rest/repos/contents), [Git database guide](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database), [Git blobs](https://docs.github.com/en/rest/git/blobs), [Git refs](https://docs.github.com/en/rest/git/refs), [Gists](https://docs.github.com/en/rest/gists/gists), [Code scanning](https://docs.github.com/en/rest/code-scanning/code-scanning), [SARIF support](https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support), [Dependency submission](https://docs.github.com/en/rest/dependency-graph/dependency-submission), [Markdown](https://docs.github.com/en/rest/markdown/markdown), [Artifacts](https://docs.github.com/en/rest/actions/artifacts), [Attaching files](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files), pinned OpenAPI file.

## Downloads and redirects

The pinned OpenAPI file declares `302` on 14 operations:

| Operation | Lifetime of the `Location` URL |
| --- | --- |
| `actions/download-artifact` (`zip` only) | 1 minute; `410` once the artifact has expired |
| `actions/download-job-logs-for-workflow-run` | 1 minute |
| `actions/download-step-logs-for-workflow-run-job` | 1 minute |
| `actions/download-workflow-run-logs` | 1 minute |
| `actions/download-workflow-run-attempt-logs` | 1 minute |
| `repos/download-tarball-archive`, `repos/download-zipball-archive` | 5 minutes for private repos (the `zipball` of an empty repo gives `404` after the redirect) |
| `repos/get-release-asset` with `Accept: application/octet-stream` | Not stated; the server either redirects or streams the bytes with `200`, so handle both |
| `repos/get-content` | Not stated (unverified when it redirects) |
| `dependency-graph/fetch-sbom-report` | A temporary URL; `202` while the SBOM is still being built |
| `code-scanning/get-codeql-database` | Not stated |
| `migrations/download-archive-for-org`, `migrations/get-archive-for-authenticated-user` | Not stated |
| `orgs/check-membership-for-user` | Not a download: `302` with a `Location` when the requester is not an org member (target not described) |

**Do not forward the token.** The redirect target is a pre-signed URL on
another host (see Hosts), and the signature is the credential. Sending your
`Authorization` header there leaks the token to a third-party storage host
and adds nothing. GitHub's docs do not state this rule outright; it follows
from the signed-URL design. Client behaviour:

- curl: `-L` does not send credentials to a different host (only
  `--location-trusted` does), per curl's own help text (checked with curl
  8.18). The safest pattern is still the two-step one: read `Location`
  without following, then fetch it with no auth header (see the curl
  recipes).
- Python `urllib.request`: the default redirect handler copies every header
  set through `Request(headers=...)` or `add_header()` to the redirected
  request, whatever the host (checked in the CPython 3.14 source,
  `HTTPRedirectHandler.redirect_request`). Use
  `Request.add_unredirected_header("Authorization", ...)` or turn redirects
  off and fetch `Location` yourself. The same handler follows `307`/`308`
  only for `GET`/`HEAD`, and turns a redirected `POST` into a `GET`, so the
  `307` on `PATCH`/`DELETE /repos/{owner}/{repo}` surfaces as an `HTTPError`
  that the wrapper has to retry against `Location`.

**Redirects in general.** Assume any request can be redirected; a redirect
is not an error. For `301`, use the new URL from then on (a renamed repo,
for example). For `302` and `307`, follow it this time and keep the original
URL.

Source: [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), [Artifacts](https://docs.github.com/en/rest/actions/artifacts), [Repository contents](https://docs.github.com/en/rest/repos/contents), [Release assets](https://docs.github.com/en/rest/releases/assets), pinned OpenAPI file; client behaviour from the local curl help output and the CPython standard library source.

## Rate limits

**Primary limits (per hour)**

| Caller | REST limit |
| --- | --- |
| Unauthenticated | 60, per originating IP |
| User (classic or fine-grained PAT, OAuth user token, GitHub App user token) | 5,000, shared across all of that user's tokens and apps; 15,000 for requests made on the user's behalf by a GitHub App or OAuth app owned by an Enterprise Cloud org |
| GitHub App installation | 5,000, plus 50 per repository above 20 and 50 per org user above 20, capped at 12,500 |
| GitHub App installation in an Enterprise Cloud org | 15,000 |
| OAuth app with client ID and secret | 5,000 (15,000 for Enterprise Cloud) |
| `GITHUB_TOKEN` | 1,000 per repository (15,000 per repository for Enterprise Cloud resources) |

Some families have their own buckets. The `resources` object of
`GET /rate_limit` in the pinned file lists `core`, `search`, `code_search`,
`graphql`, `integration_manifest`, `dependency_snapshots`, `dependency_sbom`,
`actions_runner_registration`, `source_import` (no longer used), `scim`,
`code_scanning_autofix` and `copilot_usage_records`. Search allows 30
requests per minute authenticated (code search 10, unauthenticated 10).
SARIF upload allows 1,000 per hour.

**Response headers**

| Header | Meaning |
| --- | --- |
| `x-ratelimit-limit` | Requests allowed in the window |
| `x-ratelimit-remaining` | Requests left |
| `x-ratelimit-used` | Requests used |
| `x-ratelimit-reset` | Window end, UTC epoch seconds |
| `x-ratelimit-resource` | Bucket the request counted against (`core`, `search`, ...) |

**Secondary limits.** These are not announced in headers ahead of time.
Exceeding them gives an error that says a secondary rate limit was hit:

| Limit | Value |
| --- | --- |
| Concurrent requests | 100, shared by REST and GraphQL |
| Points per minute for one REST endpoint | 900 (`GET`, `HEAD`, `OPTIONS` cost 1 point; `POST`, `PATCH`, `PUT`, `DELETE` cost 5) |
| CPU time | 90 s per 60 s of wall time (at most 60 s of it for GraphQL) |
| Content creation | 80 content-generating requests per minute and 500 per hour; some endpoints have lower limits |
| OAuth token requests | 2,000 per hour |

There is also an unquantified limit on requests that use a lot of compute.

**When limited.** Status is `403` or `429` for both primary and secondary
limits. Handling, in this order: if `retry-after` is present, wait that many
seconds; else if `x-ratelimit-remaining` is `0`, wait until
`x-ratelimit-reset`; else wait at least one minute. Back off exponentially if
it keeps happening and give up after a fixed number of tries. Keeping on
while limited can get the integration banned. To stay below the limits: send
requests one at a time, wait at least 1 s between mutating requests, honour
`x-poll-interval` where an endpoint sends it, and prefer webhooks to polling.

**`GET /rate_limit`** does not count against the primary limit (it can count
against secondary limits). Its numbers can differ from the headers; trust the
headers. In `2026-03-10` the top-level `rate` object is gone; read
`resources.core`.

**What does not count:** a conditional request answered with `304`, when it
was correctly authorized.

Source: [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), [Search](https://docs.github.com/en/rest/search/search), [Code scanning](https://docs.github.com/en/rest/code-scanning/code-scanning), pinned OpenAPI file.

## Conditional requests and caching

- Most responses carry an `etag` header (often a weak validator, `W/"..."`),
  and many carry `last-modified`.
- Repeat a `GET` with `If-None-Match: <etag>` or
  `If-Modified-Since: <last-modified>`. An unchanged resource gives
  `304 Not Modified` with no body, and the call does not count against the
  primary limit if it was correctly authorized. 160 operations in the pinned
  file declare a `304`.
- Conditional `POST`, `PUT`, `PATCH` and `DELETE` are not supported unless an
  endpoint documents them. In the pinned file only the secret-scanning
  custom-pattern update and bulk-delete operations declare
  `412 Precondition Failed`.
- `application/vnd.github.sha` with `If-None-Match: "<local sha>"` on
  `repos/get-commit` is a cheap way to ask whether a ref still points at a
  commit you already have.
- Store the validator per URL, including the query string and `Accept`,
  because different representations have different ETags (unverified, but
  standard HTTP behaviour).
- `Cache-Control` values are not documented for the API (unverified).

Source: [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), [Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [Getting started](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api), pinned OpenAPI file.

## Errors

| Status | Meaning on GitHub |
| --- | --- |
| `200`, `201`, `204` | OK, created, no content |
| `202` | Accepted; the work continues in the background (see next section) |
| `205` | Reset content: notifications marked as read |
| `207` | Partial success (cluster deployment records with `partial_success`) |
| `301`, `302`, `303`, `307` | Redirects: renamed repo, download, existing deployment branch policy, repo `PATCH`/`DELETE` |
| `304` | Conditional request, not modified |
| `400` | Malformed JSON, body not an object, unrecognised API version |
| `401` | Invalid credentials (a missing token on a private resource gives `404` or `403` instead) |
| `403` | Missing permission, rate limit, missing `User-Agent`, SSO authorization needed, too many failed logins |
| `404` | Missing, or private and not visible to you; also an unsupported method or a trailing slash |
| `405` | `pulls/merge` when the PR cannot be merged; PR creation-cap endpoints |
| `406` | "Unacceptable", declared only on `pulls/get`; the cause is not described (unverified) |
| `409` | Conflict: empty repository (Git database), stale `sha` (contents, merge), concurrent edits |
| `410` | Gone: issues disabled or deleted, artifact expired, retired API version |
| `412` | Precondition failed (secret-scanning custom patterns) |
| `413` | Payload too large (SARIF upload, Copilot content exclusion) |
| `422` | Validation failed, or "the endpoint has been spammed" (the wording of the shared OpenAPI response) |
| `429` | Rate limited, or heavy server load (`repos/list-commits`, `repos/get-commit`), throttled issue-artifact writes |
| `451` | Blocked by trade controls (since `2026-03-10` on several endpoints) |
| `500`, `502`, `503`, `504` | Server errors; `502` also for a failed release-asset upload |

A request that takes the server more than 10 seconds is cut off with a
timeout and a "Server Error" message.

**Body shapes** (component schemas in the pinned OpenAPI file):

```json
{"message": "Not Found", "documentation_url": "https://docs.github.com/rest/...", "status": "404"}
```

- `basic-error`: `message`, `documentation_url`, optional `url` and `status`
  (`status` is a string). Used for 403, 404, 409, 410 and most others.
- `validation-error` (`422`): `message`, `documentation_url` and
  `errors[]`, each with `code` (required) and optional `resource`, `field`,
  `message`, `index`, `value`.
- `validation-error-simple`: `errors` is an array of strings.
- `503`: `code`, `message`, `documentation_url`.
- SCIM endpoints: `application/scim+json` with `detail`, `status`, `scimType`
  and `schemas`.

**`errors[].code` values**

| Code | Meaning |
| --- | --- |
| `missing` | The resource does not exist |
| `missing_field` | A required parameter was not sent |
| `invalid` | A parameter is badly formatted |
| `already_exists` | Another resource already has this unique value |
| `unprocessable` | The parameters cannot be processed |
| `custom` | Read `message` for the details |

**Request ID.** Responses carry `X-GitHub-Request-Id` (it appears in the
docs' sample headers). Log it with every failure; GitHub Support can use it
to find the request (unverified: the docs do not describe the header's
purpose).

Source: [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api), [Getting started](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api), [Breaking changes](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes), [Git database guide](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database), pinned OpenAPI file.

## Asynchronous and eventually consistent behaviour

**202 Accepted.** The pinned file declares `202` on 40 operations. The ones a
repository wrapper is likely to meet:

| Operation | What `202` means and what to do |
| --- | --- |
| `repos/get-code-frequency-stats`, `repos/get-commit-activity-stats`, `repos/get-contributors-stats` | Statistics are not cached yet; a background job started. Retry shortly until `200`. The cache is keyed to the default branch SHA, so a push resets it. Code frequency refuses repos with 10,000 or more commits (`422`); contributor stats show zero additions and deletions there. The statistics docs present the 202 behaviour as general for the statistics endpoints; the pinned file declares it only on these three. |
| `repos/create-fork` | The fork is created asynchronously; Git objects can lag. The docs suggest contacting Support if it takes more than 5 minutes. |
| `repos/transfer` | The transfer continues asynchronously; the response still shows the original `owner`. A transfer to another user must be accepted by them. |
| `pulls/merge-async` | New in the pinned file. Merges in the background or adds the PR to a merge queue; returns a UUID, and `pulls/get-merge-async-result` reports `pending`, `merged`, `enqueued` or `failed`. Results are kept for 24 hours. `409` if another request is pending; `200` if the PR is already merged or queued. |
| `pulls/update-branch` | The merge of the base branch into the PR branch was accepted, not yet done |
| `actions/cancel-workflow-run`, `actions/force-cancel-workflow-run` | Cancellation requested, not yet done |
| `code-scanning/upload-sarif` | Poll the SARIF status endpoint |
| `repos/create-deployment` | `202` means GitHub merged the base branch into the topic branch instead of creating a deployment (when `auto_merge` is on, the branch is behind, and there are no conflicts); repeat the call |
| `activity/mark-notifications-as-read`, `activity/mark-repo-notifications-as-read` | `202` when marking runs in the background, `205` when it is done |
| `repos/get-pages-health-check` | The health check is still running |
| `apps/delete-installation` | `202` in `2026-03-10` (was `204`) |

**`mergeable: null`.** Fetching, creating or editing a PR starts a background
job that builds a test merge commit. While it runs, `mergeable` is `null`;
fetch the PR again after a short wait. `mergeable_state` is in the same
payload.

**Workflow dispatch** (`actions/create-workflow-dispatch`): with
`2022-11-28`, `204` and no body by default, or `200` with the workflow run
ID and URLs when `return_run_details: true` is sent. With `2026-03-10`, always
`200` with the run details. `inputs` may have at most 25 properties.

**Events API lag.** The events endpoints are not meant for real-time use;
latency ranges from 30 seconds to 6 hours depending on the time of day.

**Search index lag.** New or changed content shows up in search after a
delay; the REST docs do not give a figure (unverified). Do not use search to
read back something you have just written; read the resource itself.

Source: [Repository statistics](https://docs.github.com/en/rest/metrics/statistics), [Forks](https://docs.github.com/en/rest/repos/forks), [Git database guide](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database), [Breaking changes](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes), pinned OpenAPI file (operation descriptions of `pulls/get`, `pulls/merge-async`, `actions/create-workflow-dispatch` and the `activity/list-*-events` family).

## Webhooks

Webhooks are outside the scope of the wrappers. The pinned OpenAPI file
carries their payload schemas under the top-level `x-webhooks` key (275
entries, one per event and action). Webhook configuration (`/repos/{owner}/{repo}/hooks`
and similar) is ordinary REST and follows the rules on this page.

Source: pinned OpenAPI file.

## curl recipes

The recipes use bash and `jq`. Shared headers:

```sh
H=(-H "Accept: application/vnd.github+json"
   -H "Authorization: Bearer $GITHUB_TOKEN"
   -H "X-GitHub-Api-Version: 2022-11-28"
   -H "User-Agent: OWNER-repo-wrapper")
API=https://api.github.com
```

**Check what the token may do** (classic tokens show scopes; fine-grained
tokens and Apps show required permissions):

```sh
curl -sS -o /dev/null -D - "${H[@]}" "$API/repos/OWNER/REPO" |
  grep -iE '^x-(oauth-scopes|accepted-oauth-scopes|accepted-github-permissions|ratelimit-[a-z]+):'
```

**Follow `link` pagination to the end:**

```sh
url="$API/repos/OWNER/REPO/issues?state=all&per_page=100"
: > issues.jsonl
while [ -n "$url" ]; do
  curl -sS -D headers.txt "${H[@]}" "$url" | jq -c '.[]' >> issues.jsonl
  url=$(tr -d '\r' < headers.txt |
        sed -n 's/^[Ll]ink:.*<\([^>]*\)>; rel="next".*/\1/p')
done
```

For a wrapped list, change the `jq` filter to the item key from the table,
for example `jq -c '.workflow_runs[]'`.

**Upload a release asset:**

```sh
upload_url=$(curl -sS "${H[@]}" "$API/repos/OWNER/REPO/releases/tags/v1.2.3" | jq -r .upload_url)
curl -sS "${H[@]}" -H "Content-Type: application/zip" --data-binary @dist.zip \
  "${upload_url%%\{*}?name=dist.zip&label=Build%20output"
```

**Create or update a file through the contents API:**

```sh
path=docs/notes.md branch=main
sha=$(curl -sS "${H[@]}" "$API/repos/OWNER/REPO/contents/$path?ref=$branch" | jq -r '.sha // empty')
jq -n --arg m "Update notes" --arg c "$(base64 -w0 notes.md)" --arg b "$branch" --arg s "$sha" \
   '{message: $m, content: $c, branch: $b} + (if $s == "" then {} else {sha: $s} end)' |
  curl -sS "${H[@]}" -X PUT --data @- "$API/repos/OWNER/REPO/contents/$path"
```

(`base64 -w0` is GNU coreutils; on macOS use `base64 -i notes.md`.)

**Download an artifact without sending the token to the storage host:**

```sh
loc=$(curl -sS "${H[@]}" -o /dev/null -w '%{redirect_url}' \
      "$API/repos/OWNER/REPO/actions/artifacts/ARTIFACT_ID/zip")
curl -sS -o artifact.zip "$loc"   # no Authorization: the URL is pre-signed and lives about 1 minute
```

**Conditional request:**

```sh
curl -sS "${H[@]}" -D h.txt -o issue.json "$API/repos/OWNER/REPO/issues/1"
etag=$(tr -d '\r' < h.txt | sed -n 's/^[Ee][Tt][Aa][Gg]: //p')
curl -sS "${H[@]}" -H "If-None-Match: $etag" -o /dev/null -w '%{http_code}\n' \
  "$API/repos/OWNER/REPO/issues/1"    # 304 = unchanged, did not count against the limit
```

**Rate-limit check:**

```sh
curl -sS "${H[@]}" "$API/rate_limit" | jq '.resources | {core, search, graphql}'
```

Source: recipes assembled from the mechanisms above. The `sed` expressions and the `upload_url` expansion were tested offline against sample headers; the requests themselves were not sent, and `jq` was not available on the machine where this page was written (unverified end to end).
