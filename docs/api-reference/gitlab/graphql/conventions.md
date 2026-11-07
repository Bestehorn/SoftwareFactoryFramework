# GitLab GraphQL API: cross-cutting conventions

This page covers how to talk to the GitLab GraphQL API: the endpoint, authentication, identifiers,
pagination, limits, errors, lifecycle markers, introspection, mutations and file uploads, and what
exists only in GraphQL or only in REST. The per-type reference is generated separately; see the
[README](README.md). REST mechanics are in `conventions.md` one folder up.

Basis: GitLab's `doc/api/graphql` folder (including the generated reference) from
`gitlab-org/gitlab` at commit `a186442` (master of 2026-11-07, documenting features up to GitLab
19.6), plus the docs.gitlab.com pages named in each `Source:` line, read on 2026-11-07.

"(unverified)" marks statements the sources did not confirm. Placeholders: `gitlab.example.com`,
`group/project` for a project full path, `ISSUE_IID`, and the token in `$GITLAB_TOKEN`.

## Endpoint and request shape

| Item | Value |
|------|-------|
| Endpoint | `POST https://HOST/api/graphql` (GitLab.com: `https://gitlab.com/api/graphql`). Not under `/api/v4`. |
| Body | JSON with `Content-Type: application/json`: `{"query": "<document>", "variables": {...}}`. |
| Interactive explorer | `https://HOST/-/graphql-explorer` (GraphiQL, uses the browser session). |
| Versioning | None. One evolving schema; see the deprecation section. |
| Preview without deprecated items | Add `remove_deprecated=true` as a query parameter, for example `https://gitlab.com/api/graphql?remove_deprecated=true`. |

Details the docs do not settle:

- `operationName` in the body is standard GraphQL-over-HTTP but not mentioned on GitLab's pages
  (unverified).
- `GET` requests with the query in the URL are not documented (unverified); use `POST`.
- An instance under a relative URL root presumably serves `https://example.com/gitlab/api/graphql`
  (unverified).
- Batching: GitLab says it supports multiplexing several queries in one request and links to the
  graphql-ruby multiplex documentation, but does not show the HTTP shape. Sending a JSON array of
  `{query, variables}` objects is the usual convention for such servers (unverified for GitLab),
  and how complexity is counted across a batch is not stated (unverified).

Pass values through `variables` instead of splicing them into the query text: it avoids escaping
problems in shell and JSON, keeps queries under the size limit, and lets one query text be reused.

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/getting_started/

## Authentication, scopes and authorization

### Credentials

| Credential | Accepted | How |
|------------|----------|-----|
| Personal access token (legacy or fine-grained) | yes | `Authorization: Bearer <token>`, or `private_token=<token>` URL parameter |
| Project or group access token | yes | same as personal |
| OAuth 2.0 access token | yes | `Authorization: Bearer <token>`, or `access_token=<token>` URL parameter |
| Session cookie `_gitlab_session` | yes | browser and GraphiQL only |
| CI/CD job token | no | job tokens cannot authenticate GraphQL requests |
| Deploy token | not listed (presumably no; unverified) | |

The GraphQL pages show only the `Authorization: Bearer` header; whether the REST-style
`PRIVATE-TOKEN` header also works on `/api/graphql` is not stated (unverified). Prefer the header
over URL parameters, since URLs end up in logs.

### Scopes

| Scope | Enough for |
|-------|------------|
| `read_api` | queries |
| `api` | queries and mutations (mutations require it) |

Fine-grained personal access tokens (generally available in 19.2) work with GraphQL too; the
reference carries a `granularScope` directive that records which granular permissions a field or
type needs and its boundary (project, group, user or instance).

### What works without authentication

Some queries work anonymously (public projects, groups, users and similar data). Mutations always
require authentication. Anonymous requests get a lower complexity budget (200 instead of 250).

An invalid token gets HTTP `401` with `{"errors":[{"message":"Invalid token"}]}`.

### How missing permissions show up

- Query fields the caller may not see come back as `null`, with no entry in `errors`. GitLab does
  this on purpose so that "forbidden" and "does not exist" look the same.
- For connection fields the two cases are distinguishable: `"field": null` means no permission,
  `"field": {"nodes": []}` means permitted but nothing matched.
- Mutations report authorization failures in the top-level `errors` array (message along the lines
  of "does not exist or you don't have permission"), with the mutation's `data` entry `null`.
- An unexpected `null` usually means a missing scope, a role below the documented minimum, or a
  tier, feature or add-on not enabled on the instance.

Mutations can be flagged as spam like REST requests; the CAPTCHA flow uses the same
`X-GitLab-Captcha-Response` and `X-GitLab-Spam-Log-Id` request headers.

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/ci/jobs/ci_job_token/ ; https://docs.gitlab.com/auth/tokens/fine_grained_access_tokens/ ; https://docs.gitlab.com/api/graphql/reference/directives/

## Global IDs and other identifiers

### Global IDs

A field or argument named `id` is almost always a global ID, a string of the form
`gid://gitlab/<ModelClass>/<record id>`:

| Part | Meaning |
|------|---------|
| `gid://gitlab` | fixed root |
| `<ModelClass>` | the Rails model class, possibly namespaced: `Issue`, `Project`, `User`, `Ci::Pipeline`, `Ci::Runner`, `Achievements::Achievement`, `WorkItems::Decision` |
| `<record id>` | the database ID of the record |

The schema has one typed scalar per class (`IssueID`, `ProjectID`, `CiPipelineID`, `NoteableID`,
`WorkItemID`, and many more), all encoded as strings, plus a generic `GlobalID`.

Mapping to REST: the trailing number is the database ID, which is what REST returns as `id`, not
`iid`. An issue that REST shows as `id: 46`, `iid: 5` is `gid://gitlab/Issue/46`. Converting is
string work: take the text after the last `/` for REST, prepend `gid://gitlab/<Class>/` for
GraphQL. Knowing the class name for a given REST resource is the hard part; the scalar
descriptions in the reference give an example GID for each.

Caveats:

- Global IDs can change; the old form is then deprecated and kept through one deprecation cycle.
  Do not cache GIDs for longer than that.
- `WorkItemID` currently also accepts `IssueID` values such as `gid://gitlab/Issue/1`; this
  transitional behaviour can be removed without notice.
- Epics: an epic's ID differs from the ID of the work item that now represents it; only the `iid`
  is shared. The REST epics API returns `work_item_id`, which becomes `gid://gitlab/WorkItem/<id>`.

### Paths and IIDs

Not everything takes a global ID. As a rule of thumb, which GitLab itself calls historically
inconsistent:

| Object | Identified by | GraphQL type |
|--------|---------------|--------------|
| Project, group, namespace | full path, `project(fullPath: "group/project")` | `ID` |
| Object with an IID (issue, merge request, ...) | parent full path plus `iid`, `project(fullPath: ...) { issue(iid: "2") { ... } }`, or `issueSetLocked(input: {projectPath: ..., iid: "1", ...})` | IID is `String` |
| Everything else | global ID, `runner(id: "gid://gitlab/Ci::Runner/1")` | typed GID scalar |

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/reference/scalars/ ; https://docs.gitlab.com/api/graphql/epic_work_items_api_migration_guide/ ; https://docs.gitlab.com/api/epics/

## Connections and cursor pagination

Lists are Relay-style connections. Every connection has:

| Field | Content |
|-------|---------|
| `nodes` | the items of the current page |
| `edges` | the same items wrapped as `{ node, cursor }` |
| `pageInfo` | `hasNextPage`, `hasPreviousPage` (both non-null booleans), `startCursor`, `endCursor` (strings) |

Every connection field accepts the optional arguments `first`, `last`, `after`, `before`. Some
connections add fields, for example `IssueConnection.count` (which reports limit + 1 when the real
count exceeds its limit) and `weight`.

| Rule | Value |
|------|-------|
| Default page size | 100 records |
| Maximum page size | 100 for most connections; `subscriptionUsage.usersUsage.users` allows 20 |
| Asking for more than the maximum | silently returns the maximum, no error |
| Forward paging | `first: N, after: <previous pageInfo.endCursor>` while `hasNextPage` is true |
| Backward paging | `last: N, before: <previous pageInfo.startCursor>` while `hasPreviousPage` is true |

Cursors are opaque strings; do not build them. Each nested connection pages on its own, so to walk
a nested list completely, page the inner connection in separate queries anchored on the parent.
Nested connections also add to the complexity score quickly. Sorting is per field through a `sort`
argument with field-specific enum values (for example `issues(sort: created_asc)`).

Source: https://docs.gitlab.com/api/graphql/reference/objects/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/

## Limits

| Limit | Value |
|-------|-------|
| Page size | 100 nodes per page by default and at most (exceptions per connection) |
| Query complexity | 250 authenticated, 200 unauthenticated |
| Query size | 10,000 characters per query or mutation; use variables and fragments, strip whitespace as a last resort |
| Request timeout | 30 seconds |
| Blob data | When a query asks for the content of more than one blob path, the total is limited to 20 MB; larger blobs must be fetched one at a time. Ask for `size` first to plan. |
| Query depth | not documented (unverified) |
| Rate limiting | GraphQL points to the GitLab.com rate limit page, which has no GraphQL-specific row. That page counts the GraphQL calls made by the web UI as web traffic; how scripted GraphQL calls are counted is not stated (unverified). Self-Managed: administrator-configured. |

Field-level limits found in the docs:

- `RepositoryBlob.blame` shares the REST blame rate limits (since 19.6); each blob in a query counts
  as one request, and going over yields a GraphQL error instead of HTTP 429.
- The `aiAction` mutation is limited to 160 calls per 8 hours per user.

Complexity: each field usually adds 1, some fields and arguments add more. A query over the limit
gets an error response (exact message format unverified). Check before running a heavy query:

```graphql
query {
  queryComplexity { score limit }
  project(fullPath: "group/project") { name }
}
```

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/user/gitlab_com/rate_limits/ ; https://docs.gitlab.com/api/repository_files/ ; https://docs.gitlab.com/security/rate_limits/

## Errors and partial data

A GraphQL response can contain `data`, `errors`, or both.

| Situation | What you get |
|-----------|--------------|
| Invalid token | HTTP `401`, `{"errors":[{"message":"Invalid token"}]}` |
| Syntax, validation, complexity, authorization failure on a mutation, spam | top-level `errors` entries with `message`, `locations` (line and column), `path`, and sometimes `extensions` (for spam: `spam: true`, or `needsCaptchaResponse`, `captchaSiteKey`, `spamLogId`) |
| Some fields failed | partial data: the failed fields are `null` in `data`, and `errors` says why |
| Query field the caller may not see | `null`, with no error at all |
| Mutation rejected by business rules | the mutation's own `errors: [String!]!` field lists messages; top-level `errors` may be absent |
| Successful mutation | payload `errors` is `[]` |

HTTP status: only the `401` case is documented. For other errors the pages read do not state the
status; GraphQL servers conventionally answer `200` with an `errors` array (unverified for
GitLab). A client should therefore always inspect `errors`, never only the status code, and should
treat a `null` field as "absent or forbidden".

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/reference/mutations/

## Deprecation, experiment and beta markers

### Process

- Breaking changes (removing or renaming fields, arguments and other schema parts) go through a
  deprecation cycle: the item stays available for at least six releases after deprecation and is
  removed at the next major release (`XX.0`). The docs' example: items deprecated in 15.7 and 16.6
  were both removed in 17.0.
- Exempt: anything labelled experiment, fields behind a disabled-by-default feature flag, and
  urgent fixes for critical security or performance problems.
- Reverting a Self-Managed instance from EE to CE removes schema parts.

### Where the markers appear

| Marker | Where |
|--------|-------|
| `@deprecated(reason: "...")` | Schema directive on field definitions, arguments, enum values and input fields; visible through introspection. The reason usually names the replacement. |
| "Deprecated in GitLab X.Y. <reason>" | Text in the reference tables (472 occurrences in this snapshot), for example `Group.epics`: deprecated in 17.5, replaced by the `WorkItem` type. |
| `Status: Experiment` details block | On whole queries and mutations in the reference (449 blocks). |
| "Introduced as an experiment in GitLab X.Y" | In field and argument descriptions (2,506 occurrences). Experiments can change or disappear without notice. |
| "**Status**: Beta." | In a few descriptions (4 occurrences), for example the DevOps adoption namespaces query. |
| "Introduced in GitLab X.Y" | Rare in the reference (1 occurrence); history blocks use the experiment form above. |
| `@gl_introduced(version: "X.Y.Z")` | A directive the client puts on fields or inline fragments. When the tagged version is the server's current milestone or later and the field is missing from the server's schema, the field resolves to `null` instead of failing. Useful for one client against several GitLab versions; behaviour for older version tags is not described (unverified). |
| GitLab-wide deprecations page | Lists deprecations per version and is linked from release posts. |

To find out early whether a query will survive the next major release, run it against
`/api/graphql?remove_deprecated=true`.

### Removed items

The removed-items page lists:

| Release | Removed | Replacement |
|---------|---------|-------------|
| 17.0 | `CiRunner` fields `architectureName`, `executorName`, `ipAddress`, `platformName`, `revision`, `version` | the same fields on the runner `manager` object |
| 16.0 | `PipelineSecurityReportFinding.name` and `.confidence`, `ReleaseAssetLink.external`, `CiRunnerStatus` values `PAUSED` and `ACTIVE`; mutations `vulnerabilityFindingDismiss`, `apiFuzzingCiConfigurationCreate`, `CiCdSettingsUpdate` | `title`; none; none; `CiRunner.paused`; `vulnerabilityDismiss` or `securityFindingDismiss`; (listed as `todos`); `ProjectCiCdSettingsUpdate` |
| 15.0 | mutation `clusterAgentTokenDelete`, field `pipelines`, type field `defaultMergeCommitMessageWithDescription` | `clusterAgentTokenRevoke`; none; a merge commit template plus `defaultMergeCommitMessage` |

The page has no entries for 18.0 or 19.0. The epic migration guide says the epic GraphQL API is
planned for removal in 19.0, yet this 19.6-era reference still documents `Epic`, `Group.epic` and
`Group.epics` (marked deprecated since 17.5).

Source: https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/removed_items/ ; https://docs.gitlab.com/api/graphql/reference/directives/ ; https://docs.gitlab.com/api/graphql/reference/objects/ ; https://docs.gitlab.com/api/graphql/reference/queries/ ; https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/graphql/epic_work_items_api_migration_guide/

## Introspection

- Standard introspection queries (`{ __schema { ... } }`, `__type`) are accepted.
- On production instances they are not executed against the live schema. Every introspection query
  gets the same static document, whatever the method or parameters: the full schema, or the schema
  without deprecated items when the body contains `"remove_deprecated": true`. The static document
  is regenerated to match the current schema. Development and test environments run introspection
  live.
- A consequence (inferred, unverified): a narrow `__type(name: "Issue")` query on a production
  instance returns the whole static schema, so cache it once instead of issuing many small
  introspection calls.
- The static files are `public/-/graphql/introspection_result.json` and
  `public/-/graphql/introspection_result_no_deprecated.json` in the GitLab installation; whether
  they can be fetched over HTTP at `/-/graphql/...` is unverified.
- GitLab advises against using introspection to fetch data in production.

Source: https://docs.gitlab.com/api/graphql/getting_started/

## Mutations

Shape:

```graphql
mutation($id: NoteableID!, $body: String!) {
  createNote(input: { noteableId: $id, body: $body }) {
    note { id body }
    errors
  }
}
```

| Element | Rule |
|---------|------|
| Arguments | Exactly one argument, `input`, of type `<MutationName>Input` (for example `CreateNoteInput`). Pass the whole object as one variable if convenient: `mutation($input: CreateNoteInput!) { createNote(input: $input) { errors } }`. Arguments ending in `!` are required unless they have a default. |
| `clientMutationId` | Optional string accepted by every mutation and returned unchanged in the payload; use it to match responses to requests. Not repeated in each mutation's reference entry. |
| Payload `errors` | Every mutation returns `errors: [String!]!`. Always select it. |
| Other payload fields | The changed or created object (for example `note`); `null` after a delete. |
| Input objects with `@oneOf` | exactly one field must be set, and not to `null` |
| Authentication | Always required; scope `api`. |

Mutations can be asynchronous in places, for example `pipelineCreate(input: {..., async: true})`
(experiment since 17.8) returns a `requestId` instead of a pipeline; `Project.ciPipelineCreationRequest`
(experiment since 17.9) reports on it.

Source: https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/reference/directives/ ; https://docs.gitlab.com/api/graphql/reference/objects/

## File uploads

Arguments of type `Upload` take files. Requests follow the GraphQL multipart request specification
(https://github.com/jaydenseric/graphql-multipart-request-spec) as `multipart/form-data` with three
kinds of parts:

| Part | Content |
|------|---------|
| `operations` | JSON with `query` and `variables`; every file variable is set to `null` |
| `map` | JSON mapping a part name to the variable paths it fills, for example `{"0": ["variables.file"]}` or `{"0": ["variables.files.0"], "1": ["variables.files.1"]}` |
| one part per file | named after the `map` keys (`0`, `1`, ...) |

Upload mutations cannot be run from GraphiQL; use curl or a client library.

Mutations with an `Upload` argument in this snapshot:

| Mutation | Argument | Status |
|----------|----------|--------|
| `achievementsCreate`, `achievementsUpdate` | `avatar: Upload` | no status marker |
| `designManagementUpload` | `files: [Upload!]!` (designs on an issue, by `projectPath` and `iid`) | no status marker |
| `organizationCreate`, `organizationUpdate`, `organizationDelete` | `avatar: Upload` | Experiment (`organizationDelete` since 19.1) |
| `uploadCreate` | `file: Upload!`, with `projectPath` or `groupPath`; returns `markdown`, `url`, `fullPath`, `alt`, `upload` | Experiment since 19.0 |
| `workItemsCsvImport` | `file: Upload!` (CSV) | Experiment |

Size limits for GraphQL uploads are not stated on the GraphQL pages; the instance attachment limits
presumably apply (unverified).

Source: https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/graphql/reference/scalars/

## Only in GraphQL / only in REST

Each row was checked against the local reference and REST pages of this snapshot.

### Only in GraphQL

| Capability | GraphQL | REST situation |
|------------|---------|----------------|
| Work items | `workItem`, `workItemsByReference`, `Project.workItems`, `Group.workItems`, `Namespace.workItems`; `workItemCreate`, `workItemUpdate`, `workItemDelete`, `workItemExport` and more | No work items API under `doc/api`. Note: the `workItem` query and `workItemCreate` still carry `Status: Experiment`, although the epic migration guide says the API would leave experiment status before 19.0. |
| Epics with new features (assignees, health status, links to other item types) | `WorkItem` with widgets | Epics REST API deprecated since 17.0, no new features; the guide says new features need the `WorkItem` GraphQL API. |
| Branch rules | `Project.branchRules`; `branchRuleCreate`, `branchRuleUpdate`, `branchRuleDelete`, squash options, external status checks, approval project rules | No branch rules API in REST; REST has protected branches only. |
| Group-wide and instance-wide vulnerability lists | `Group.vulnerabilities`, `Query.vulnerabilities` (instance security dashboard), `Query.vulnerability` | REST lists only per project (`GET /projects/:id/vulnerabilities`) and acts on single vulnerabilities; both REST pages say they are being deprecated and point to GraphQL. |
| Design uploads | `designManagementUpload` | No designs API in REST. |
| Asynchronous pipeline creation | `pipelineCreate(async: true)` plus `Project.ciPipelineCreationRequest` (experiments) | `POST /projects/:id/pipeline` is synchronous. |
| Work item CSV import | `workItemsCsvImport` (experiment) | No CSV import endpoint found under `doc/api`. |
| Query cost introspection | `queryComplexity { score limit }` | not applicable |

### Only in REST

| Capability | REST | GraphQL situation |
|------------|------|-------------------|
| CI/CD job token authentication | `JOB-TOKEN` on listed endpoints | Job tokens cannot authenticate GraphQL. |
| Full job log | `GET /projects/:id/jobs/:job_id/trace` | `CiJob.trace` is a `CiJobTrace` with only `htmlSummary` (experiment). |
| Artifact bytes | `GET .../jobs/:job_id/artifacts` and siblings | `CiJobArtifact` gives `downloadPath`, a URL to fetch over HTTP. |
| Repository archives | `GET /projects/:id/repository/archive[.format]` | `Repository` has no archive field. |
| Package uploads (generic and all formats) | `PUT`/`POST` under `/projects/:id/packages/...` | No package mutation takes an `Upload`; GraphQL can delete packages and files (`destroyPackage`, `destroyPackageFile`, ...). |
| File-based project and group export and import | `/projects/:id/export`, `/projects/import`, `/groups/:id/export`, `/groups/import` | No such mutations; import-related mutations cover placeholder-user reassignment (`importSourceUser...`) and Jira import only. |
| Project, group and user avatars | `PUT /projects/:id`, `PUT /groups/:id`, `PUT /user/avatar` with `avatar` | `Upload` arguments exist only for achievements and organizations. |
| Wiki pages and wiki attachments | `/projects/:id/wikis`, `/wikis/attachments` | Only `wikiPageSubscribe` exists as a wiki mutation. |
| Secure files | `/projects/:id/secure_files` | No secure-file mutations. |
| Markdown uploads, generally available | `POST /projects/:id/uploads`, `POST /groups/:id/uploads` | `uploadCreate` exists but is an experiment (19.0). |

### Available in both (do not assume "only")

Releases and release links (`releaseCreate`, `releaseAssetLinkCreate`), multi-file commits
(`commitCreate` with `actions`, `startBranch`, `startSha`, `allowEmpty`), merging
(`mergeRequestAccept`), mergeability (`MergeRequest.detailedMergeStatus`, `rebaseInProgress`),
notes (`createNote`), pipeline creation (`pipelineCreate`), personal access tokens
(`personalAccessTokenCreate`, `...Revoke`, `...Rotate`), CI/CD job token allowlists
(`ciJobTokenScopeAddGroupOrProject` and the REST job token scopes API).

Source: https://docs.gitlab.com/api/graphql/reference/queries/ ; https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/graphql/reference/objects/ ; https://docs.gitlab.com/api/graphql/epic_work_items_api_migration_guide/ ; https://docs.gitlab.com/api/graphql/branch_rules/ ; https://docs.gitlab.com/api/epics/ ; https://docs.gitlab.com/api/vulnerabilities/ ; https://docs.gitlab.com/api/project_vulnerabilities/ ; https://docs.gitlab.com/api/jobs/ ; https://docs.gitlab.com/api/job_artifacts/ ; https://docs.gitlab.com/api/repositories/ ; https://docs.gitlab.com/api/project_import_export/ ; https://docs.gitlab.com/api/group_import_export/ ; https://docs.gitlab.com/api/wikis/ ; https://docs.gitlab.com/api/secure_files/ ; https://docs.gitlab.com/api/project_markdown_uploads/ ; https://docs.gitlab.com/api/project_job_token_scopes/ ; https://docs.gitlab.com/ci/jobs/ci_job_token/

## curl recipes

Shared setup:

```shell
GQL="https://gitlab.example.com/api/graphql"
# GITLAB_TOKEN: personal, project or group access token (read_api for queries, api for mutations)
```

A query with variables (the JSON body is kept in a file to avoid shell quoting trouble):

```shell
cat > query.json <<'JSON'
{
  "query": "query($path: ID!, $iid: String!) { project(fullPath: $path) { issue(iid: $iid) { id iid title state } } }",
  "variables": {"path": "group/project", "iid": "ISSUE_IID"}
}
JSON
curl --silent --show-error --request POST \
  --header "Authorization: Bearer $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data @query.json \
  "$GQL"
# Always check the "errors" key in the response, not only the HTTP status.
```

Paging a connection in a loop (uses `jq`):

```shell
cursor=null
page=0
while :; do
  page=$((page + 1))
  jq -n --arg path "group/project" --argjson after "$cursor" '{
    query: "query($path: ID!, $after: String) { project(fullPath: $path) { issues(first: 100, after: $after, sort: created_asc) { pageInfo { hasNextPage endCursor } nodes { id iid title } } } }",
    variables: {path: $path, after: $after}
  }' > body.json
  curl --silent --show-error --fail --request POST \
    --header "Authorization: Bearer $GITLAB_TOKEN" \
    --header "Content-Type: application/json" \
    --data @body.json "$GQL" > "issues-$page.json"
  if jq -e '.errors' "issues-$page.json" > /dev/null; then
    jq '.errors' "issues-$page.json" >&2; exit 1
  fi
  [ "$(jq -r '.data.project.issues.pageInfo.hasNextPage' "issues-$page.json")" = "true" ] || break
  cursor=$(jq '.data.project.issues.pageInfo.endCursor' "issues-$page.json")   # JSON string
done
```

A mutation with `clientMutationId` and the payload's `errors`:

```shell
cat > mutation.json <<'JSON'
{
  "query": "mutation($input: CreateNoteInput!) { createNote(input: $input) { clientMutationId note { id body } errors } }",
  "variables": {
    "input": {
      "noteableId": "gid://gitlab/Issue/ISSUE_ID",
      "body": "Posted through GraphQL.",
      "clientMutationId": "wrapper-0001"
    }
  }
}
JSON
curl --silent --show-error --request POST \
  --header "Authorization: Bearer $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data @mutation.json \
  "$GQL"
# ISSUE_ID is the issue's REST "id" (not its iid).
```

A multipart upload (`uploadCreate` is an experiment; `designManagementUpload` works the same way
with `files: [Upload!]!` and `map` entries `variables.files.0`, `variables.files.1`, ...):

```shell
curl --silent --show-error --request POST \
  --header "Authorization: Bearer $GITLAB_TOKEN" \
  --form 'operations={"query": "mutation($path: ID!, $file: Upload!) { uploadCreate(input: {projectPath: $path, file: $file}) { markdown url fullPath errors } }", "variables": {"path": "group/project", "file": null}}' \
  --form 'map={"0": ["variables.file"]}' \
  --form '0=@screenshot.png' \
  "$GQL"
```

Checking the complexity budget before a heavy query:

```shell
curl --silent --show-error --request POST \
  --header "Authorization: Bearer $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"query": "query { queryComplexity { score limit } currentUser { username } }"}' \
  "$GQL"
```

Source: https://docs.gitlab.com/api/graphql/getting_started/ ; https://docs.gitlab.com/api/graphql/ ; https://docs.gitlab.com/api/graphql/reference/mutations/ ; https://docs.gitlab.com/api/graphql/reference/objects/
