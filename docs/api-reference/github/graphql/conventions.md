# GitHub GraphQL API: cross-cutting conventions

This page covers the mechanics of GitHub's GraphQL API that apply to every
query and mutation: request shape, authentication, IDs, pagination, limits,
errors, schema evolution and how GraphQL relates to the REST API. The
per-type reference generated from the schema is linked from
[README.md](README.md). REST mechanics are in `../conventions.md` (the REST
conventions page one folder up).

Basis of this page (researched 2026-11-07):

- docs.github.com, the pages named in each `Source:` line.
- The pinned public schema `schema.docs.graphql` (1.5 MB, served by
  docs.github.com with `Last-Modified: Fri, 30 Oct 2026`). Every count below
  that says "in the pinned SDL" was computed from that file.
- For the REST comparison: the pinned OpenAPI description of
  `api.github.com` ([github/rest-api-description](https://github.com/github/rest-api-description)
  commit `2f8f80e`).

`OWNER`, `REPO`, `HOST`, `SUBDOMAIN` are placeholders; `$GITHUB_TOKEN` holds a
token. "(unverified)" marks a statement I could not confirm in an official
source.

## Endpoint and request shape

| Deployment | Endpoint |
| --- | --- |
| GitHub.com | `https://api.github.com/graphql` |
| GitHub Enterprise Server | `http(s)://HOST/api/graphql` |
| GHE.com (data residency) | `https://api.SUBDOMAIN.ghe.com/graphql` |

- One endpoint serves every operation. Queries and mutations are sent as
  `POST` with a JSON body; the docs mention `GET` only for introspection.
- Body: `{"query": "...", "variables": {...}}`. `query` is the GraphQL
  document as one JSON string, so newlines and inner quotes must be escaped
  (letting a JSON encoder build the body avoids that). `variables` is a JSON
  object whose keys match the `$name` declarations in the operation, for
  example `query($owner: String!, $name: String!) { ... }`.
- `operationName` selects one operation when a document holds several. It
  is part of the general GraphQL-over-HTTP convention; GitHub's guides do not
  mention it (unverified that GitHub honours it).
- Headers: `Authorization: Bearer TOKEN` (the docs' curl sample writes
  `bearer`). Send `Content-Type: application/json`; the docs' sample omits it
  (unverified whether it is required). The REST rule that a `User-Agent` is
  required is not repeated for GraphQL; send one anyway (unverified).
  `X-GitHub-Api-Version` is documented only for REST; GraphQL changes through
  the schema schedule described below.
- Optional header `X-Github-Next-Global-ID: 1` changes the ID format (see
  Global node IDs).

Source: [Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql), [GHES forming calls](https://docs.github.com/en/enterprise-server@latest/graphql/guides/forming-calls-with-graphql), [GHE.com forming calls](https://docs.github.com/en/enterprise-cloud@latest/graphql/guides/forming-calls-with-graphql), [Introduction to GraphQL](https://docs.github.com/en/graphql/guides/introduction-to-graphql).

## Authentication

| Token type | Works with GraphQL | Notes |
| --- | --- | --- |
| Personal access token (classic) | Yes | Choose scopes for the data you read or write; reading public repos needs `public_repo` at least. |
| Fine-grained PAT | Yes | Always includes read access to public repositories; add permissions such as Issues read for private data. Whether the documented REST gaps (Checks, Packages, user-owned Projects) also apply to GraphQL is not stated (unverified). |
| GitHub App installation token or user access token | Yes | Same grants as for REST. |
| OAuth app token (web or device flow) | Yes | |
| `GITHUB_TOKEN` in Actions | Yes | It has its own GraphQL rate limit (see Limits). |

- If the token lacks a scope or permission, the error message names what
  is missing.
- Bad credentials give HTTP `401` (the introduction page names "Bad
  credentials"); unlike data errors, this one is not wrapped in a `200`.
- Every documented example authenticates. Whether anonymous calls are
  rejected outright is not stated on the pages read (unverified).
- SAML SSO and token types behave as described for REST.

Source: [Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql), [Introduction to GraphQL](https://docs.github.com/en/graphql/guides/introduction-to-graphql), [Rate and query limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), [Managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## Global node IDs

- Every object that implements `Node` has an `id` (type `ID`). The same
  value is the `node_id` field in REST responses, which is how you move
  between the two APIs.
- `node(id: ID!)` fetches any object by ID; use an inline fragment to select
  type-specific fields (`... on Issue { number title }`) and `__typename` to
  learn the type. The pinned SDL also has `nodes(ids: [ID!]!)` for batches;
  its maximum list length is not documented (unverified).
- Two ID formats coexist. Legacy IDs are Base64-looking strings such as
  `MDQ6VXNlcjM0MDczMDM=`; the newer format looks like `U_kgDOADP9xw` (a type
  prefix, an underscore, then an opaque part). Both formats appear in the
  pinned OpenAPI examples (784 legacy-style and 102 new-style `node_id`
  values).
- Header `X-Github-Next-Global-ID: 1` makes every `id` field in the response
  use the new format; `0` (or no header) gives the default, which depends on
  when the object was created. Legacy IDs are still accepted as input, so the
  header can be used to translate stored legacy IDs. The migration guide
  covers GraphQL only; its effect on REST `node_id` is not described
  (unverified).
- Treat IDs as opaque strings. Code that decodes legacy IDs to recover type
  information breaks with the new format. Persist IDs rather than
  rebuilding them.
- Numeric REST IDs appear in GraphQL as `databaseId` (and `fullDatabaseId`
  on types where 64-bit values are needed). The mapping to REST `id` is the
  conventional reading of the field descriptions (unverified). Prefer
  `fullDatabaseId` where it exists: the pinned SDL already deprecates
  `CheckAnnotation.databaseId` (removal 2027-01-01) because it cannot hold
  64-bit values, and the breaking-changes page lists more such removals.
- The SDL directive `@possibleTypes(concreteTypes: [...], abstractType: ...)`
  on ID input fields says which object types a mutation accepts there.

Source: [Using global node IDs](https://docs.github.com/en/graphql/guides/using-global-node-ids), [Migrating GraphQL global node IDs](https://docs.github.com/en/graphql/guides/migrating-graphql-global-node-ids), pinned SDL, pinned OpenAPI file.

## Connections and cursor pagination

- Every connection field needs `first` or `last`, from 1 to 100.
- Forward paging uses `first` with `after: <endCursor>`; backward paging
  uses `last` with `before: <startCursor>`. With `last`, the final page comes
  back first.
- `pageInfo` (type `PageInfo`) has exactly four fields: `hasNextPage`,
  `hasPreviousPage`, `startCursor`, `endCursor`. Stop when `hasNextPage` (or
  `hasPreviousPage` going backwards) is `false`.
- Items are available both as `nodes { ... }` and as
  `edges { cursor node { ... } }`. Use `edges` when you need a cursor per
  item. Many connections also offer `totalCount` (for example
  `IssueConnection`).
- Cursors are opaque; take them from `pageInfo` or `edges.cursor`, never
  build them.
- **Nested pagination.** Only one cursor per connection can be passed per
  request, so you cannot page an inner connection for all parents at once.
  A workable pattern (my recommendation, not a documented procedure): page
  the outer connection; for every parent whose inner `pageInfo.hasNextPage`
  is `true`, send follow-up queries such as
  `node(id: $parentId) { ... on Issue { comments(first: 100, after: $c) { ... } } }`.
  Nesting also multiplies the node count (see Limits).

Source: [Using pagination in the GraphQL API](https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api), [Introduction to GraphQL](https://docs.github.com/en/graphql/guides/introduction-to-graphql), [Rate and query limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), pinned SDL.

## Limits

**Node limit.** A single request may ask for at most 500,000 nodes. Count
them by multiplying the `first`/`last` values down each nesting path and
adding up all paths. Example: `repositories(first: 50)` containing
`issues(first: 10)` is 50 + 50 x 10 = 550 nodes.

**Primary rate limit (points per hour)**

| Caller | Points per hour |
| --- | --- |
| User (PAT, or a GitHub App or OAuth app acting for a user; includes App user access tokens) | 5,000 |
| GitHub App owned by an Enterprise Cloud org acting for a user; OAuth app owned or approved by such an org acting for a member | 10,000 |
| GitHub App installation | 5,000, plus 50 per repository above 20 and 50 per org user above 20, capped at 12,500 |
| GitHub App installation in an Enterprise Cloud org | 10,000 |
| OAuth app with client ID and secret (public data only) | 5,000 (10,000 if owned by an Enterprise Cloud org) |
| `GITHUB_TOKEN` | 1,000 per repository (15,000 for resources of an enterprise account) |

Note that most Enterprise Cloud figures differ from REST (10,000 here,
15,000 there); the `GITHUB_TOKEN` figures are the same.

**How a query is priced.** Count the requests needed to fill every
connection, assuming each `first`/`last` is used to the full, divide by 100
and round to the nearest whole number; the minimum is 1. Example:
`repositories(first: 100) { issues(first: 50) { ... } }` needs 1 request for
the repositories plus 100 for their issues, so 101 / 100 = 1.01, which rounds
to 1 point (and it asks for 100 + 100 x 50 = 5,100 nodes). How mutations are
priced against the primary limit is not explained (unverified).

**Checking the budget.** The headers are the same as REST
(`x-ratelimit-limit`, `-remaining`, `-used`, `-reset`), and
`x-ratelimit-resource` is `graphql`. The docs prefer the headers to querying.
Inside a query, `rateLimit { cost limit nodeCount remaining resetAt used }`
reports the same figures plus this query's cost and node count. The pinned
SDL also gives `rateLimit(dryRun: true)`, which computes the cost without
running the query. `resetAt` is typed `DateTime` (an ISO 8601 string) even
though its description talks about epoch seconds; expect a string
(unverified on the wire).

**Secondary limits** (shared with REST): at most 100 concurrent requests
across REST and GraphQL; at most 2,000 points per minute on the GraphQL
endpoint, where for this purpose a query without mutations costs 1 point
and one with mutations costs 5; no more than 60 s of CPU time per 60 s of
wall time for GraphQL (90 s overall); content creation at most 80 per minute
and 500 per hour. Wait at least 1 s between mutations and do not send them
in parallel.

**Timeouts.** The server stops work after 10 seconds and answers `502` or
`504` with a message that it could not respond in time. A timed-out request
also deducts extra points from the primary limit for the next hour. Queries
that use too many resources in other ways are cut off and return partial
data plus an error.

**When limited.** Primary: status stays `200`, the body has an error, and
`x-ratelimit-remaining` is `0`; wait for `x-ratelimit-reset`. Secondary:
status `200` or `403` with an error naming the secondary limit; honour
`retry-after`, otherwise wait for the reset if `remaining` is `0`, otherwise
wait at least a minute, and back off exponentially.

Source: [Rate limits and query limits for the GraphQL API](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), pinned SDL.

## Errors

A wrapper has to check three layers:

1. **HTTP status.** `401` for bad credentials, `403` for some secondary
   limits, `502`/`504` for timeouts. These carry REST-style bodies (or none),
   not GraphQL `errors` (unverified for `403` and `5xx` bodies).
2. **`errors` in a `200` response.** Schema validation failures, missing
   objects, missing permissions and rate-limit hits come back as HTTP `200`
   with a top-level `errors` array. Each entry has a `message`, usually
   `locations` and `path`, and often a GitHub-specific `type` string.
   GitHub's docs do not list the `type` values. An issue in GitHub's own
   docs repository shows `RATE_LIMITED` for rate-limit hits and an
   `extensions.code` such as `argumentLiteralsIncompatible` on schema
   validation errors; `NOT_FOUND` and `FORBIDDEN` are commonly seen as well.
   All of these are unverified against official documentation; match on
   `type` when present and fall back to `message`.
3. **Partial data.** `data` can be present together with `errors`: fields
   that failed are `null` and the rest is filled in (resource-limit cut-offs
   are documented to do this). Never assume that a non-null `data` means
   success.

Source: [Rate limits and query limits for the GraphQL API](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), [Introduction to GraphQL](https://docs.github.com/en/graphql/guides/introduction-to-graphql), [Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql), [github/docs issue 11071](https://github.com/github/docs/issues/11071) (not official documentation; used only for the unverified `type` examples).

## Schema previews, deprecations and breaking changes

- **Previews.** The pinned SDL defines `directive @preview(toggledBy: String!)`
  but no schema member uses it, so no preview-gated fields exist right now.
  The old schema-previews URL on docs.github.com no longer lists any
  previews.
- **Deprecations.** Members marked `@deprecated(reason: "...")` stay usable
  until removal. The pinned SDL has 1,250 of them, and most reasons end with
  "Removal on YYYY-MM-DD UTC". Counted by date: 1,109 for 2026-04-01 (the
  GraphQL audit log, whose reason says to use the REST API instead), 101
  for 2025-04-01 (mostly Projects classic), and a handful of others dated
  from 2023-01-01 to 2027-01-01. Members past their stated removal date are still present in
  the 30 October 2026 schema, so a date is a deadline to stop using a member,
  not a guarantee that it is already gone.
- **Schedule.** Breaking changes take effect only on the first day of a
  quarter (1 January, 1 April, 1 July, 1 October) and are announced at least
  three months ahead on the breaking-changes page. The page separates
  breaking changes (queries can fail, for example a removed field) from
  dangerous ones (queries still run but behaviour can change, for example a
  new enum value). Code should tolerate unknown enum values.
- Other directives in the SDL: `@possibleTypes` (see Global node IDs) and
  `@docsCategory(name:)`, which groups schema members by the matching REST
  docs section.

Source: [Breaking changes](https://docs.github.com/en/graphql/overview/breaking-changes), [Schema previews (old URL)](https://docs.github.com/en/graphql/overview/schema-previews), pinned SDL.

## Introspection

- Query `__schema` for all types and `__type(name: "Repository")` for one
  type. Introspection is the one documented case where a plain `GET` to the
  endpoint is used; it still needs a token.
- With `Accept: application/vnd.github.v4.idl`, the introspection response
  is the schema in condensed IDL form instead of JSON.
- The same public schema is downloadable as an SDL file,
  `https://docs.github.com/public/fpt/schema.docs.graphql`; the pinned
  `schema.docs.graphql` is that official public SDL. Whether introspection
  counts against the rate limit is not stated (unverified).

Source: [Introduction to GraphQL](https://docs.github.com/en/graphql/guides/introduction-to-graphql), [Public schema](https://docs.github.com/en/graphql/overview/public-schema).

## Mutations

- Shape: `mutation { NAME(input: { ... }) { PAYLOAD_FIELDS } }`, normally
  written with variables: `mutation($input: AddCommentInput!) { addComment(input: $input) { ... } }`.
- In the pinned SDL all 278 mutation fields take exactly one argument,
  `input`, of a dedicated `...Input` type, and return a dedicated
  `...Payload` type. Most object references in inputs are global node IDs
  (`subjectId`, `pullRequestId`, `repositoryId`), so a wrapper usually needs a
  lookup query first.
- `clientMutationId` is an optional string on every one of those 278 input
  types and is echoed back in every payload; use it to correlate requests
  and responses. The docs only call it optional; nothing says GitHub uses it
  to de-duplicate retried mutations, so do not rely on it for idempotency
  (unverified).
- A request containing a mutation counts 5 points against the secondary
  per-minute limit, and mutations that create content also count toward the
  content-creation limits (80 per minute, 500 per hour; which mutations count
  as "content-generating" is not listed, unverified). Send them one at a
  time, at least 1 s apart.

Source: [Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql), [Rate and query limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api), pinned SDL.

## File uploads

GitHub's GraphQL API has no file-upload mechanism: the pinned SDL defines no
`Upload` scalar, no mutation accepts a multipart body, and no mutation
creates releases, release assets or comment attachments. The only way to
send file bytes is `createCommitOnBranch`, whose `fileChanges.additions[]`
carry `path` plus `contents` of type `Base64String` (a Base64 string,
possibly binary). That mutation:

- needs `branch` (a `CommittableBranch`: `repositoryNameWithOwner` plus
  `branchName`, or the Ref's node `id`; the mutation's own description calls
  the name field `refName`, but the input type has `branchName`),
  `expectedHeadOid` (the commit you expect at the branch head before your
  commit, which works as an optimistic lock; the exact failure on mismatch is
  not described, unverified), `message` (`headline`, optional `body`) and
  `fileChanges` (`additions` of `{path, contents}`, `deletions` of `{path}`);
- appends exactly one commit whose parent is the current branch head and
  moves the branch to it;
- always authors the commit as the token's owner, and the schema says
  custom author and committer will never be supported; for that, use the
  REST Git database API;
- signs the commit automatically where possible, so it shows as verified;
- has no documented payload size limit (unverified).

Binary uploads (release assets) and SARIF stay REST-only.

Source: pinned SDL (`createCommitOnBranch`, `FileChanges`, `FileAddition`, `Base64String`), [Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql).

## Only in GraphQL / only in REST

Each row was checked against both pinned files: the SDL for mutation and
field names, the OpenAPI file for paths and operation IDs.

**Only in GraphQL** (no matching operation in the pinned OpenAPI file):

| Capability | GraphQL | REST |
| --- | --- | --- |
| Repository discussions | `Repository.discussions`, `createDiscussion`, `addDiscussionComment`, `markDiscussionCommentAsAnswer`, ... | No path contains "discussion"; even team discussions are gone from this description |
| Create, update, delete, copy or link a Projects v2 project | `createProjectV2`, `updateProjectV2`, `deleteProjectV2`, `copyProjectV2`, `linkProjectV2ToRepository` | The 26 `projectsV2` operations list and get projects and manage fields, items, drafts and views only; Projects classic has no REST paths left |
| Auto-merge on or off | `enablePullRequestAutoMerge`, `disablePullRequestAutoMerge` | The REST PR object exposes `auto_merge` read-only |
| Draft to ready and back | `markPullRequestReadyForReview`, `convertPullRequestToDraft` | `pulls/update` has no `draft` field (only `pulls/create` does) |
| Resolve review threads | `resolveReviewThread`, `unresolveReviewThread`, `PullRequest.reviewThreads` | none |
| Hide comments | `minimizeComment`, `unminimizeComment` | none |
| Move an issue to another repo | `transferIssue` | only `repos/transfer` for whole repos |
| Pin an issue | `pinIssue`, `unpinIssue` | REST pins issue comments only (`issues/pin-comment`) |
| Revert a PR | `revertPullRequest` | none |
| Read a merge queue, remove an entry | `Repository.mergeQueue(branch:)`, `MergeQueue.entries`, `dequeuePullRequest` | REST can only enqueue (below) |
| Sponsors | `createSponsorship`, `createSponsorsTier`, ... | none |
| Multi-file commit in one call | `createCommitOnBranch` | four Git database calls (blob, tree, commit, ref) |
| Branch protection with wildcard patterns | `createBranchProtectionRule(input: { pattern })` | the REST `branch` parameter rejects wildcards and its description points to GraphQL |

**In both** (often assumed to be GraphQL-only):

| Capability | REST (pinned OpenAPI) | GraphQL (pinned SDL) |
| --- | --- | --- |
| Sub-issues | `issues/add-sub-issue`, `issues/list-sub-issues`, `issues/remove-sub-issue`, `issues/reprioritize-sub-issue`; `parent_issue_id` on `issues/create` | `addSubIssue`, `removeSubIssue`, `reprioritizeSubIssue`, `Issue.subIssues`, `Issue.parent` |
| Issue types | `orgs/list-issue-types`, `orgs/create-issue-type`, `orgs/update-issue-type`, `orgs/delete-issue-type`, `repos/list-issue-types`; `type` on issue create and update | `createIssueType`, `updateIssueType`, `deleteIssueType`, `updateIssueIssueType`, `Repository.issueTypes` |
| Issue dependencies | `issues/add-blocked-by-dependency`, `issues/list-dependencies-blocked-by`, `issues/list-dependencies-blocking`, `issues/remove-dependency-blocked-by` | `addBlockedBy`, `removeBlockedBy`, `Issue.blockedBy`, `Issue.blocking` |
| Issue fields | `/orgs/{org}/issue-fields`, `/repos/{owner}/{repo}/issues/{issue_number}/issue-field-values` | `createIssueField`, `setIssueFieldValue`, `Issue.issueFieldValues` |
| Projects v2 items, fields, views | 26 operations under `/orgs/{org}/projectsV2` and `/users/{username}/projectsV2` | `addProjectV2ItemById`, `updateProjectV2ItemFieldValue`, `createProjectV2View`, ... |
| Merge queue: add a PR | `pulls/merge-async` with `merge_action: merge_queue`, result via `pulls/get-merge-async-result` | `enqueuePullRequest` |
| Read file contents | `repos/get-content`, `git/get-blob` | `Repository.object(expression: "BRANCH:path")` returning a `Blob` with `text`, `byteSize`, `isBinary`, `isTruncated` |
| Rate-limit status | `GET /rate_limit` | `rateLimit` |

**Only in REST** (no mutation in the pinned SDL; some objects can still be
read through GraphQL):

| Capability | REST | GraphQL |
| --- | --- | --- |
| Releases and release assets | `repos/create-release`, `repos/upload-release-asset` | `Release` and `ReleaseAsset` are readable; no release mutation |
| Milestones | `issues/create-milestone` and friends | readable (`Repository.milestones`); no milestone mutation |
| Gists | `gists/create` and friends | no gist mutation |
| Webhooks | `repos/create-webhook` and friends | no webhook mutation |
| Actions: dispatch, re-run, cancel, logs, artifacts, secrets, variables | `actions/create-workflow-dispatch`, `actions/re-run-workflow`, `actions/download-artifact`, ... | `WorkflowRun` is readable; the only mutation with "Workflow" in its name is `deleteProjectV2Workflow`, a Projects automation |
| Code scanning SARIF, dependency snapshots | `code-scanning/upload-sarif`, `dependency-graph/create-repository-snapshot` | none |
| Markdown rendering | `markdown/render`, `markdown/render-raw` | none |
| Commits with chosen author, committer or your own signature | `git/create-commit` (`author`, `committer`, `signature`) | `createCommitOnBranch` cannot set them |
| Archives and raw downloads | `repos/download-tarball-archive`, `repos/download-zipball-archive`, raw media types | none |

**Moving between the APIs.** The GraphQL audit log is deprecated, and its
deprecation reason sends users to REST. The `api.github.com` OpenAPI file has
no audit-log paths, so the REST audit log is presumably in the Enterprise
Cloud description (unverified; that description was not checked). Projects
classic is deprecated in GraphQL (95 members with removal date 2025-04-01,
still present) and already absent from REST. Merge-queue enqueueing,
sub-issues, issue types, issue dependencies and issue fields all have REST
operations in the pinned file, so they no longer force a GraphQL code path
(when each one arrived in REST was not checked).

Source: pinned SDL, pinned OpenAPI file, [Comparing the REST and GraphQL APIs](https://docs.github.com/en/rest/about-the-rest-api/comparing-githubs-rest-api-and-graphql-api) (which says only that features occasionally exist in one API but not the other).

## curl recipes

The recipes use bash and `jq`. The GraphQL document sits in a shell variable
(single-quoted, so `$owner` stays literal) and `jq --arg` turns it into a
correctly escaped JSON string.

```sh
G=(-H "Authorization: Bearer $GITHUB_TOKEN"
   -H "Content-Type: application/json"
   -H "User-Agent: OWNER-repo-wrapper")
GQL=https://api.github.com/graphql
```

**A query with variables (and its cost):**

```sh
q='query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) { id nameWithOwner defaultBranchRef { name } }
  rateLimit { cost remaining resetAt }
}'
jq -n --arg q "$q" --arg owner OWNER --arg name REPO \
   '{query: $q, variables: {owner: $owner, name: $name}}' |
  curl -sS "${G[@]}" --data @- "$GQL" | jq .
```

**Page through a connection until `hasNextPage` is false:**

```sh
q='query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, states: OPEN) {
      nodes { number title }
      pageInfo { hasNextPage endCursor }
    }
  }
}'
cursor=null                                   # JSON null on the first page
while :; do
  resp=$(jq -n --arg q "$q" --arg owner OWNER --arg name REPO --argjson after "$cursor" \
            '{query: $q, variables: {owner: $owner, name: $name, after: $after}}' |
         curl -sS "${G[@]}" --data @- "$GQL")
  if echo "$resp" | jq -e '.errors' > /dev/null; then echo "$resp" >&2; break; fi
  echo "$resp" | jq -c '.data.repository.issues.nodes[]'
  [ "$(echo "$resp" | jq -r '.data.repository.issues.pageInfo.hasNextPage')" = true ] || break
  cursor=$(echo "$resp" | jq '.data.repository.issues.pageInfo.endCursor')   # keeps the JSON quotes
done
```

**A mutation with `clientMutationId`** (`SUBJECT_ID` is the node ID of an
issue or PR, for example its REST `node_id`):

```sh
q='mutation($input: AddCommentInput!) {
  addComment(input: $input) { clientMutationId commentEdge { node { url } } }
}'
jq -n --arg q "$q" --arg id SUBJECT_ID --arg body "Posted by the wrapper" \
   '{query: $q, variables: {input: {subjectId: $id, body: $body, clientMutationId: "wrapper-1"}}}' |
  curl -sS "${G[@]}" --data @- "$GQL" | jq .
```

Source: recipes assembled from the mechanisms above; every type and field used (`Repository.issues`, `IssueState.OPEN`, `PageInfo`, `AddCommentInput`, `AddCommentPayload`, `IssueCommentEdge`, `RateLimit`) was checked in the pinned SDL. `jq` is not installed on the machine where this page was written, so the recipes were not executed (unverified).
