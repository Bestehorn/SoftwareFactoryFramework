# Design — issue #30: GitHub wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-4.2, UB-1.1..UB-3.1, frozen). Builds on
`.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn") and
`.claude/specs/issue-17-github-wrapper-foundation/design.md` ("#17 Dn"). The GitLab twin's
`.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn") is the parity source where it applies.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed (aafecbb) and unblocked the slices; selected issue #30, "GitHub wrapper rewrite, part 2
   slice: the GraphQL-only capabilities", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Overview

`graphql_only.py` declares one `GraphQLOperation` per mutation and per query that serves an "Only in GraphQL" row
(D1). Each record carries a new `operation_id`, `graphql/<member>` (D2). `call` sends a record whose ID has that prefix
through a GraphQL branch of `cmd_call`: `-f`/`-F` give the document's variables, `registry.graphql_call` sends it over
`Transport.graphql` or `Transport.graphql_nodes`, and `print_json` prints the data or the nodes (D3). A mutation takes
one `$input` whose node IDs the caller supplies (D4). `GATED_OPERATIONS` refuses AC-3.1's mutations (D5). A new
contract test reads every document against `docs/api-reference/github/graphql/`, and a new fake-host suite calls every
record through `main` (D6). The REST path of `call`, the transport, the fixtures and every compatibility command stay
as they are.

## Design

### D1 — One record per operation (AC-1.1, AC-1.2, AC-1.3)

**The rule.**

- Each mutation a row names gets its own record.
- The field members of a row get one query record, which selects them along one path; its `connection` names the
  connection it pages.
- "Repository discussions" also gets `graphql/Repository.discussionCategories`, the only source of
  `createDiscussion`'s `categoryId` (D4).
- Every record's `capability` is its row's first cell, verbatim. `PENDING_CAPABILITIES` becomes `frozenset()`.

**Query records.** The discussions record's document shows the shape:

```graphql
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 100, after: $after) { nodes { id number title } pageInfo { hasNextPage endCursor } }
  }
}
```

`first` is the maximum `conventions.md` "Connections and cursor pagination" allows. `$after` is the cursor
`Transport.graphql_nodes` sets. `$owner` and `$name` are `String!`, the `repository` arguments of `queries.md`.

| ID | Capability | Caller's variables | `connection` | Path below `repository`, and the nodes' fields |
|---|---|---|---|---|
| `graphql/Repository.discussions` | Repository discussions | `owner`, `name` | `("repository", "discussions")` | `discussions`; `id number title` |
| `graphql/Repository.discussionCategories` | Repository discussions | `owner`, `name` | `("repository", "discussionCategories")` | `discussionCategories`; `id name` |
| `graphql/PullRequest.reviewThreads` | Resolve review threads | `owner`, `name`, `number` (`Int!`) | `("repository", "pullRequest", "reviewThreads")` | `pullRequest(number: $number) { reviewThreads }`; `id isResolved path` |
| `graphql/Repository.mergeQueue` | Read a merge queue, remove an entry | `owner`, `name`, `branch` (`String`) | `("repository", "mergeQueue", "entries")` | `mergeQueue(branch: $branch) { entries }`; `id position state pullRequest { id number }` |

**Mutation records.** Each document is `mutation($input: <I>!) { <m>(input: $input) { clientMutationId <selection> } }`.

- `<I>` is the input type that `mutations.md`'s signature line names for `<m>`: `pinIssue(input: PinIssueInput!)`.
- The record's ID is `graphql/<m>` and its `connection` is `()`. The caller's one variable is `input`.

| Capability | Mutations `<m>`, each with its selection |
|---|---|
| Repository discussions | `createDiscussion` `discussion { id number }`; `addDiscussionComment` `comment { id }`; `markDiscussionCommentAsAnswer` `discussion { id }` |
| Create, update, delete, copy or link a Projects v2 project | `createProjectV2` and `copyProjectV2` `projectV2 { id number }`; `updateProjectV2` and `deleteProjectV2` `projectV2 { id }`; `linkProjectV2ToRepository` `repository { id }` |
| Auto-merge on or off | `enablePullRequestAutoMerge` (refused, D5) and `disablePullRequestAutoMerge` `pullRequest { id }` |
| Draft to ready and back | `markPullRequestReadyForReview` and `convertPullRequestToDraft` `pullRequest { id isDraft }` |
| Resolve review threads | `resolveReviewThread` and `unresolveReviewThread` `thread { id isResolved }` |
| Hide comments | `minimizeComment` `minimizedComment { isMinimized minimizedReason }`; `unminimizeComment` `unminimizedComment { isMinimized }` |
| Move an issue to another repo | `transferIssue` (refused) `issue { id number }` |
| Pin an issue | `pinIssue` and `unpinIssue` `issue { id }` |
| Revert a PR | `revertPullRequest` (refused) `revertPullRequest { id number }` |
| Read a merge queue, remove an entry | `dequeuePullRequest` `mergeQueueEntry { id }` |
| Sponsors | `createSponsorship` `sponsorship { id }`; `createSponsorsTier` `sponsorsTier { id }` |
| Multi-file commit in one call | `createCommitOnBranch` (refused) `commit { id }` |
| Branch protection with wildcard patterns | `createBranchProtectionRule` `branchProtectionRule { id }` |

Each selected name is a field of the table it is read from: a payload table of `mutations.md`, a type of
`objects-a-p.md` or `objects-p-w.md`, or `interfaces.md` `Minimizable`. Q proves it (D6).

**Alternatives:**

- **One record per capability** (the issue's estimate). Rejected. A mutation document runs every root field it selects
  ("This selection set should be executed serially", GraphQL spec §6.2.2), so a single "Auto-merge on or off" record
  would enable and disable in one call.
- **One record per named member, field members included.** Rejected: `MergeQueue.entries` is reached only through
  `Repository.mergeQueue(branch:)`, so a record of its own would repeat that record's document.

**The coverage test (V).** `_capability_problems` reports "a capability declared N times", and per-operation records
break that (AC-1.5). The minimal change applies #17's "no ID is declared twice" to the new ID:

- the duplicate check reads `record.operation_id`;
- an ID that is an operation ID of the index is reported too (AC-1.4). The index is passed in from
  `test_one_module_per_family_holding_only_its_own_ids`.

`coverage_gaps`, `_covered_and_pending` (which reads `capability`) and every other test of V stay as they are.

### D2 — The operation ID (AC-1.1, AC-1.4)

- **Registry change.** `GraphQLOperation` gains `operation_id: str` as its first field, and `connection` gets the
  default `()`. No record exists before this change, so no call site changes.
- **The ID** is `graphql/` plus the member as the row names it, without its arguments: the mutation's name
  (`graphql/pinIssue`), or `<Type>.<field>` for a query record (`graphql/Repository.mergeQueue`).
  - The ID has the `<family>/<name>` shape of the index's IDs, as #41 D2's `graphql#<field>` has the
    `<stem>#<anchor>` shape of GitLab's.
  - `operations-index.md` holds no ID of family `graphql`, so no GraphQL ID is an index ID. If a regenerated index
    gains one, V reports it (D1).
  - `call` reads the prefix to choose the GraphQL branch (D3).
- **`connection`.** A record that pages nothing has `connection` `()`. `registry.graphql_call` then sends it through
  `Transport.graphql` and returns `data`.
- **Alternatives:**
  - the capability text as the ID. Rejected: a capability has several records, and its text holds spaces and commas.
  - `graphql#<field>`. Rejected: no GitHub operation ID contains `#`. The parity with #41 is in the shape, not the
    character.

### D3 — The GraphQL call (AC-2.1 to AC-2.5)

```
python scripts/github_wrapper.py call graphql/<member> [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]...
```

- `-f` and `-F` give variables. They are parsed as #28 D2 parses body members (`assignment`, `json_member`; a name
  given twice keeps its last value). The variables are `body_of(members=...) or {}`. No option is added.
- **`cmd_call`**, for an ID that starts with `registry.GRAPHQL_ID_PREFIX`:
  1. `refuse_gated` (D5), unchanged.
  2. `registry.graphql_lookup(operation_id=...)`.
  3. `check_graphql_call(*, operation, path_names, query_names, variable_names)` raises one `ValueError`. It names
     each `--path` or `--query` name given (a GraphQL record documents none: #28 D4's undocumented-parameter rule),
     then each variable outside `registry.declared_variables(operation=...)`, then those variables.
  4. A refusal in steps 1 to 3 is logged and returns `EXIT_REFUSED` before any request, as #28 D4 does.
  5. `print_json(value=registry.graphql_call(...))`.

  Any other ID takes #28 D2's steps, unchanged (UB-1.2). `main` still reads the credential and `origin` first (#28 D4,
  second row). A GraphQL record takes no default from them, so its variables are exactly the ones given (AC-2.1).
- **Registry additions:**
  - `GRAPHQL_ID_PREFIX = "graphql/"`.
  - `graphql_lookup(*, operation_id) -> GraphQLOperation`: the one record of `graphql_only.OPERATIONS` with that ID.
    It raises `ValueError` naming the ID when no record declares it, or more than one does. `graphql_only` is imported
    inside the function, because it imports `GraphQLOperation` from the registry (as #41 D2's `_declarations` does).
  - `declared_variables(*, operation) -> Tuple[str, ...]`: each `$name` in the document that is followed, after any
    white space, by `:`, in order (GraphQL `VariableDefinition : Variable : Type`).
    - For a record with a `connection`, it leaves out `transport.FIELD_AFTER`, which `Transport.graphql_nodes` sets
      on every page. Step 3 therefore refuses a caller's `after` on such a record (#41 D2).
  - `graphql_call(transport, operation_id, *, variables) -> Any`:
    - looks the record up with `graphql_lookup`;
    - refuses an undeclared name with `ValueError`, as `_check_names` does;
    - for a record with a `connection`, returns
      `list(transport.graphql_nodes(document=..., variables=..., connection=...))`;
    - for any other record, returns `transport.graphql(document=..., variables=...)`.
  - `lookup`, `send`, `call` and `pages` are unchanged.
- **Why a prefix and a second look-up**, not #41 D2's `lookup` over both kinds: `send`, `pages`, `call` and the
  compatibility commands read a `RestOperation`'s fields from `lookup`. Widening its return type would make each of
  them narrow it. The prefix leaves the REST path as #28 built it.
- **One `$input` per mutation** (`conventions.md` "Mutations": every mutation takes one `input` argument of its own
  `…Input` type). The caller gives the whole object with `-F input=<JSON object>`.
  - Alternative: one variable per input field. Rejected: each record would have to restate its input type's fields
    and their types, which `mutations.md` already gives, and a regenerated input field would mean editing the record.
- **Output.** `print_json` writes `data` (AC-2.3), or every node of every page (AC-2.2). The nodes are collected
  before anything is printed, so a failure on any page prints nothing (AC-2.4).
- **Errors.** `Transport` raises `GitHubAPIError` for each condition of AC-2.4 (in `_graphql_data`, `_send` and
  `_connection_page`). `_run_command` logs the message and `Details:` and exits 1 (#28 D3), unchanged. A `mergeQueue`
  that is `null` (a branch with no queue) counts as a page without its connection, so it exits 1.

### D4 — Node IDs: the caller supplies them (AC-1.1)

A mutation's `input` takes global node IDs (`conventions.md` "Mutations"). The caller gives them inside
`-F input=…`; no record looks one up. A REST response's `node_id` is the object's GraphQL `id` (`conventions.md`
"Global node IDs").

| Input field (with the type `mutations.md` names it the ID of) | Where the caller reads it |
|---|---|
| `repositoryId` (Repository) | `node_id` of `call repos/get` |
| `pullRequestId`; `dequeuePullRequest`'s `id` (PullRequest) | `node_id` of `call pulls/get --path pull_number=N`; for a queued pull request, `pullRequest.id` of `graphql/Repository.mergeQueue` |
| `issueId` (Issue) | `node_id` of `call issues/get --path issue_number=N` |
| `subjectId` (any `Minimizable`) | `node_id` of `call issues/list-comments --path issue_number=N`; `comment.id` printed by `graphql/addDiscussionComment` |
| `ownerId` (Organization, User) | `owner.node_id` of `call repos/get` (the repository's owner, an Organization or a User); `node_id` of `call users/get-authenticated` (the token's user) |
| `projectId` (ProjectV2) | `projectV2.id` printed by `graphql/createProjectV2` or `graphql/copyProjectV2` |
| `categoryId` (DiscussionCategory) | a node `id` of `graphql/Repository.discussionCategories` |
| `discussionId` (Discussion) | a node `id` of `graphql/Repository.discussions` |
| `markDiscussionCommentAsAnswer`'s `id` (DiscussionComment) | `comment.id` printed by `graphql/addDiscussionComment` |
| `threadId` (PullRequestReviewThread) | a node `id` of `graphql/PullRequest.reviewThreads` |
| `sponsorableId`, `sponsorId` | not needed: `sponsorableLogin` and `sponsorLogin` take a login (`CreateSponsorshipInput`, `CreateSponsorsTierInput`) |

Every REST record named here is declared in its family module on the trunk.

**Alternatives:**

- **A look-up query inside each mutation call.** Rejected: a GraphQL operation is either a query or a mutation, so
  this takes a second request, and a second request path to prove, for every record, with names in place of IDs.
- **A `--resolve` option.** Rejected: the requirements ask for no such mechanism.

### D5 — Refusals (AC-3.1, AC-3.2)

- `GATED_OPERATIONS` gains these entries:
  - `graphql/enablePullRequestAutoMerge` → `"merge-pr"`;
  - `graphql/createCommitOnBranch`, `graphql/revertPullRequest` and `graphql/transferIssue` → `None`.
- **The shape** is #27's `Mapping[str, Optional[str]]`, in which `None` makes `refuse_gated` say that no subcommand
  sends the operation. It is on the trunk: PR #47 merged as `f374b3d`, an ancestor of `origin/main`. This branch starts
  at `aafecbb`, before that merge, so it rebases onto the trunk before the first implementation wave.
- `refuse_gated` is unchanged.
  - Its message names the ID, which holds the mutation's name (AC-3.1's log), and either `merge-pr` or "no subcommand
    sends it" (AC-3.2).
  - Step 1 runs before the look-up, so a refused record is never sent.
- #32 (branch `issue-32-issues-pulls-records`, not on the trunk) adds `GATED_NOT_SENT`: the gated IDs that their
  subcommand does not send, whose refusal leaves out "which sends it". `graphql/enablePullRequestAutoMerge` joins it
  once the rebased trunk has it (Residuals).
- The refused records stay declared (DL-002): they are covered and documented, but never sent.

### D6 — Proving the calls (AC-1.1, AC-1.3, AC-2.6, AC-3.3)

**The fake host needs no addition.**

- `StaticRouteSpec(method="POST", url="/graphql", replies=...)` answers the pages in order.
- Through `run_product_case` (`NonGetRequest.of`), `GoldenCase.writes` compares each `POST`'s method, its path and its
  JSON body (`query`, `variables`).
- `test_github_api_transport.py` `test_graphql_follows_page_info_cursors` already routes GraphQL pages this way.
- `github_wrapper_fixtures.py` stays as #28 left it.

**G: the calls through `main`** (`src/payload/test/test_github_api_graphql_only.py`).

- `test_every_record_is_called_through_main` covers each record of `graphql_only.OPERATIONS` whose ID is not one of
  AC-3.1's four, which G holds as a constant that `test_a_refused_mutation_sends_nothing` also iterates; it fails when
  it calls no record. It finds them by iterating the module, so a later record is proven without editing G.
  - Argv: `call <id>`, with `-F input={"clientMutationId": "k"}` for `input` and `-f <name>=v-<name>` for any other
    variable.
  - A record without a connection is answered with a `data` object. A record with one is answered with two pages,
    nested at its `connection` path: the first has `hasNextPage` `true` and `endCursor` `"c1"`.
  - Oracle: exit 0. Each `POST` to `/graphql` carries the record's document as `query` and the given variables; for
    a connection, `after` is `null` on the first page and `"c1"` on the second. Stdout is `printed_json` of `data`,
    or of both pages' nodes in order.
- G's examples and refusals are listed under Correctness Properties.

**Q: the documents against the reference** (`test/test_github_graphql_contract.py`). It lives in `test/` because it
reads `docs/api-reference/github/` (#17 X1).

- `reference_schema(*, graphql_dir)` reads each type's fields, with their types and arguments, as the reference
  writes them:
  - `Query`: each section of `queries.md`, from its signature line `` `name(arg: Type, …)` `` and the type after `→`;
  - `Mutation`: each section of `mutations.md`, from its signature line, and its payload type's fields from the
    `| Payload field | Type | Notes |` table;
  - each type section of `objects-a-p.md`, `objects-p-w.md` and `interfaces.md`, from its
    `| Field | Type | Arguments | Notes |` rows. An Arguments cell lists `` `name: Type` `` spans, with any default
    after `=`.

  A field's type is the link text of its Type cell; the type the walk enters is that text with `[`, `]` and `!`
  removed. `queries.md`'s signature line gives the return type as a link, `mutations.md`'s as a code span. A name that
  no table defines is a leaf (a scalar or an enum).
- `read_document(*, document)` reads the subset the records use: one `query` or `mutation` with `$name: Type`
  definitions; fields with arguments whose values are a `$variable` or an integer; nested selections. Commas count as
  white space ("Insignificant Commas", GraphQL spec). The reader reports any other token as a problem.
- `document_problems(*, record, schema)` walks the selection from the root type and names:
  - a field that its parent type lacks (`__typename` aside), or an argument that the field lacks;
  - a `$variable` argument that is not declared, or whose declared type is neither the argument's type nor that type
    with `!` added (`AreTypesCompatible`, GraphQL spec §5.8.5); a declared variable that is never used;
  - a leaf with a selection, or an object or interface without one;
  - for a record with a `connection`: a path of selected fields that differs from it; and, only on a path that matches
    it, a last field without `after: $after`, a selection without both `nodes` and `pageInfo { hasNextPage endCursor }`,
    or a `$after` that is not declared `String`;
  - for a mutation: more than one root field, an `input` argument that is not `$input`, or an `operation_id` other than
    `graphql/` followed by that root field's name (D2), so the ID `GATED_OPERATIONS` refuses is the mutation the
    document runs (AC-3.1).
- `selected_members(*, record, schema)` gives `<Type>.<field>` for every field the walk visits, and the bare name of a
  root mutation field.
- `row_members(*, conventions)` gives the code spans in each "Only in GraphQL" row's GraphQL cell, each cut at its
  first `(`. A `...` is not a member.

**What an `sff-test-*` repository cannot exercise.** The fixture creates a private repository owned by the token's
user (`POST /user/repos`, `docs/reports/self-hosting-proposal-2026-11-07.md` "One repository per test run").

| Records | Why | What proves the call |
|---|---|---|
| `graphql/Repository.mergeQueue`, `graphql/dequeuePullRequest` | "Pull request merge queues are available in any public repository owned by an organization, or in private repositories owned by organizations using GitHub Enterprise Cloud" (GitHub Docs, `reusables/gated-features/merge-queue`) | Q and G |
| `graphql/createSponsorsTier`, `graphql/createSponsorship` | a tier is "a new payment tier for your GitHub Sponsors profile", and a sponsorship's `amount` is "The amount to pay to the sponsorable in US dollars" (GitHub GraphQL reference, "Sponsors"). Both need a Sponsors profile and a payment, which the fixture does not create. | Q and G |
| `graphql/createBranchProtectionRule` | "Protected branches are also available in public and private repositories with GitHub Pro, GitHub Team, …" (GitHub Docs, `reusables/gated-features/protected-branches`). On a private repository it depends on the token's account. | Q and G; #10's run where the account has such a plan |
| `graphql/disablePullRequestAutoMerge` | it needs a pull request with auto-merge on, which `call` never turns on (D5) | Q and G |
| AC-3.1's records | refused, never sent | G `test_a_refused_mutation_sends_nothing`; Q |

Every other record is proven by Q and G in CI's `tests` leg, and by #10's real-forge run once its fixture exists
(requirements "Out of scope").

### D7 — The usage docstring and the map (AC-4)

**The usage docstring.** These lines go into the usage list of `src/payload/scripts/github_wrapper.py`, after the
`call issues/get` entry:

```
    python scripts/github_wrapper.py call graphql/pinIssue -F 'input={"issueId": "<node id>"}'   # a GraphQL record
        # -f NAME=TEXT and -F NAME=JSON give the document's variables; a mutation takes one, input, its input object,
        # whose IDs are a REST response's node_id or an id a GraphQL record printed. A connection prints as one
        # JSON array of every page's nodes, any other result as its data, both as indented JSON. --path, --query and a
        # variable the document does not declare (after, on a connection) are refused: exit 2.
        # The "Only in GraphQL" capabilities and their records:
        #   Repository discussions: graphql/Repository.discussions graphql/Repository.discussionCategories ...
        # graphql/enablePullRequestAutoMerge (use merge-pr), graphql/createCommitOnBranch, graphql/revertPullRequest
        # and graphql/transferIssue are refused before any request: exit 2.
```

The capability lines hold one line per capability, in D1's order: the capability verbatim, a `:`, then the IDs of its
records, wrapped onto further `#     ` lines at 120 columns. The closing sentence of the docstring ("a refused `call`
exits 2") already covers the refusals.

**The map.** The `src/payload/scripts/github_api/` bullet of `docs/forLLMConsumption.md` gains, before its closing
sentence: "A GraphQL-only capability is a record of `graphql_only.py`, called the same way: `python
scripts/github_wrapper.py call graphql/pinIssue -F 'input={"issueId": "<node id>"}'` (`-f`/`-F` give the document's
variables). `test/test_github_graphql_contract.py` checks each document against `graphql/`."

**Module docstrings.**

- `commands/call.py`'s docstring adds the GraphQL grammar and print forms. It and the `GATED_OPERATIONS` comment name,
  beside a record that commits to, creates, moves or renames a branch, a record that moves an issue into another
  repository (D5).
- `graphql_only.py`'s docstring states the ID scheme, the two document shapes, and that a refused record is declared
  but never sent.
- `registry.py`'s docstring describes a `GraphQLOperation` as one operation serving a capability.
- No file of the package contains `environ` or `getenv` (UB-2.1's scan reads docstrings too).

### D8 — Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/registry.py` | `GraphQLOperation.operation_id` (first field) and the `connection` default `()`; `GRAPHQL_ID_PREFIX`, `graphql_lookup`, `declared_variables` and `graphql_call`; the docstring |
| `src/payload/scripts/github_api/graphql_only.py` | D1's records in `OPERATIONS`; `PENDING_CAPABILITIES` empty; the docstring |
| `src/payload/scripts/github_api/commands/call.py` | D5's `GATED_OPERATIONS` entries (and the `GATED_NOT_SENT` entry once on the trunk); `cmd_call`'s GraphQL branch; `check_graphql_call`; the docstring |
| `src/payload/scripts/github_wrapper.py` | the module docstring only (D7) |
| `src/payload/test/test_github_api_graphql_only.py` | new (G) |
| `src/payload/test/test_github_api_registry.py` | adds `test_variables_are_the_documents_definitions` and `test_graphql_lookup_finds_one_record` |
| `test/test_github_graphql_contract.py` | new (Q) |
| `test/test_github_wrapper_coverage.py` | `_capability_problems` (D1) and `test_a_graphql_record_id_is_its_own` |
| `docs/forLLMConsumption.md` | the `github_api/` bullet (D7) |

#28 D8's "never" row:

- `github_wrapper.py` is edited because AC-4.1 asks for its docstring.
- `test_github_wrapper_coverage.py` is edited because AC-1.5 requires it to pass with D1's records.
- `commands/call.py` is #28 D8's own exception for "a GraphQL call (#30)".
- `families/*`, `transport.py`, `_common.py`, `github_wrapper_fixtures.py`, `test_github_wrapper_contract.py`,
  `test_github_api_call.py` and `test_github_wrapper_compat.py` stay untouched.

### Sources

- `docs/api-reference/github/graphql/conventions.md`: "Endpoint and request shape", "Global node IDs", "Connections
  and cursor pagination", "Errors", "Mutations", "Only in GraphQL / only in REST".
- `docs/api-reference/github/graphql/`: `queries.md` (`repository`); `mutations.md` (each D1 mutation's signature,
  input and payload tables); `objects-a-p.md`, `objects-p-w.md` (`Repository`, `PullRequest`,
  `PullRequestReviewThread`, `MergeQueue`, `MergeQueueEntry`, `Discussion`, `DiscussionCategory`, `ProjectV2`,
  `Issue`); `interfaces.md` (`Minimizable`). `docs/api-reference/github/operations-index.md`: no `graphql/` ID.
- `docs/reports/self-hosting-proposal-2026-11-07.md`: "One repository per test run".
- [GitHub REST, "Get a repository"](https://docs.github.com/en/rest/repos/repos#get-a-repository): `owner` is a Simple
  User whose `node_id` is required (D4).
- GitHub Docs source, [`data/reusables/gated-features/merge-queue.md`](https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/merge-queue.md)
  and [`protected-branches.md`](https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/protected-branches.md),
  rendered on "Managing a merge queue" and "About protected branches".
- [GitHub GraphQL reference, Sponsors](https://docs.github.com/en/graphql/reference/sponsors): `createSponsorsTier`,
  `createSponsorship` and `CreateSponsorshipInput.amount`.
- [GraphQL, October 2021](https://spec.graphql.org/October2021/): §6.2.2 "Mutation"; §2.10 `VariableDefinition`;
  "Insignificant Commas"; §5.8.5 `AreTypesCompatible` ("If locationType is a non-null type: If variableType is NOT a
  non-null type, return false").
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259#section-7) §7: in a JSON string, "the control characters (U+0000
  through U+001F)" must be escaped.
- [Python, `json.dump`](https://docs.python.org/3/library/json.html#json.dump), `ensure_ascii`: "If `True` (the
  default), the output is guaranteed to have all incoming non-ASCII and non-printable characters escaped."

## Testing Strategy

- **G** (`src/payload/test/`, pytest only, shipped) runs every call through the product's `main` against the
  unchanged fake host (D6). It reads refusals with `caplog`. It does not read the reference.
- **Unit tests in R** cover `declared_variables` and `graphql_lookup`, setting a synthetic `graphql_only.OPERATIONS`
  with `monkeypatch.setattr`.
- **Q** and **V** run in `test/`, because they read the reference. Q's tests find the records by iteration.
- **The value domain of AC-2.1** is #28's property H `test_any_json_value_becomes_the_body_member`, unchanged, on the
  same `json_member` and `body_of`. G's example proves that the variables carry those values. No new property test is
  needed.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-forge check is #10's fixture on an ephemeral `sff-test-*` repository (requirements "Out of
  scope"). Until it exists, G runs each call through `main` up to the API boundary in CI's `tests` leg, and Q proves
  each document against the reference.

## Correctness Properties

Each entry gives the test kind and its oracle.

- **AC-1.1** — Inspection: D1 (granularity), D2 (the ID and `connection`), D4 (node IDs), and D6 (the unreachable
  records and what proves them).
- **AC-1.2**
  - Structural, Q `test_every_capability_has_a_record`: every capability the table lists is the `capability` of a
    record, and `PENDING_CAPABILITIES == frozenset()`.
  - V `test_every_operation_is_covered_or_pending` and `test_one_module_per_family_holding_only_its_own_ids` (every
    record's capability is in the table) pass.
- **AC-1.3** — Structural, Q `test_every_member_a_row_names_is_selected`. For each row, `row_members` is a subset of
  the union of `selected_members` over that capability's records. A failure names the row and the member.
- **AC-1.4**
  - Example, V `test_a_graphql_record_id_is_its_own`, on a synthetic module. Two records that share a capability give
    no problem. Two that share an ID give one problem naming the ID, and so does a record whose ID is an index ID.
  - On the merged tree, V `test_one_module_per_family_holding_only_its_own_ids` passes.
- **AC-1.5** — V's two tests pass on the merged tree.
- **AC-2.1**
  - Parametrized example, G `test_a_variable_holds_the_given_json_value`: `call graphql/pinIssue` with `-f input=text`,
    and with `-F input=` followed by `5`, `true`, `["a"]`, `{"issueId": "I_1"}` and `null`. Oracle: one `POST` to
    `/graphql` whose `query` is the record's document and whose `variables` are `{"input": <the value>}`, compared by
    `json.dumps(sort_keys=True)`, as K's `test_a_body_member_holds_the_given_json_value` compares.
  - Structural: G `test_every_record_is_called_through_main`.
- **AC-2.2**
  - Structural: G's test above, on every record with a connection, across two pages.
  - Example, G `test_a_merge_queue_prints_every_entry`: `graphql/Repository.mergeQueue -f owner=o -f name=r -f
    branch=main`. Oracle: two `POST`s with `after` `null` then `"c1"`, and stdout `printed_json` of both entries.
- **AC-2.3** — Structural: G's test above, on every record without a connection; stdout is `printed_json` of `data`.
- **AC-2.4** — Parametrized, G `test_a_graphql_failure_exits_1_with_its_details`, with these cases:
  - `{"errors": [...]}`, and `{"data": {...}, "errors": [...]}`, both at `200`;
  - HTTP `502`;
  - `403` with `retry-after: 0` on every answer (a spent rate limit);
  - no response (`FakeGitHub.answer` patched for the test to raise `urllib.error.URLError`);
  - `{"data": {"repository": {"mergeQueue": null}}}`;
  - a first page, then `502` on the second.

  Oracle: exit 1, stdout empty, a log record holding the message, and for `errors` a `Details:` record holding the
  `errors` array.
- **AC-2.5**
  - Parametrized, G `test_an_undeclared_variable_is_refused`, with these cases:
    - `graphql/pinIssue -f issue=1`;
    - `graphql/pinIssue -F input={} --path issue_number=1 --query state=open`;
    - `graphql/Repository.discussions -f owner=o -f name=r -f after=c` (D3, DL-004: a paging record's `$after` is
      set by the transport).

    Oracle: exit 2, no request, and one log record naming each refused name and the record's variables (`["input"]`,
    `["owner", "name"]`).
  - Unit, R `test_variables_are_the_documents_definitions`: `query Q($owner: String!, $name : String, $after: String)
    { repository(owner: $owner, name: $name) { discussions(first: 100, after: $after) { … } } }` gives
    `("owner", "name", "after")`, and with a `connection` gives `("owner", "name")`.
  - Unit, R `test_graphql_lookup_finds_one_record`: a declared ID is found; an undeclared ID and an ID declared twice
    each raise `ValueError` naming the ID.
- **AC-2.6** — Structural: G `test_every_record_is_called_through_main`.
- **AC-3.1, AC-3.3** — Parametrized, G `test_a_refused_mutation_sends_nothing`, over AC-3.1's IDs with `-F input={}`.
  Oracle: exit 2, no request, and a log record naming the ID.
- **AC-3.2** — The same test: the record for `graphql/enablePullRequestAutoMerge` names `merge-pr`; each other record
  holds "no subcommand sends it".
- **Q's method** (AC-1.1's proof; for AC-3.1, that a refused ID is the mutation its document runs):
  - Structural, `test_every_record_matches_the_reference`: `document_problems` is empty for every record; it fails
    when it finds no record.
  - Parametrized, `test_the_method_rejects_a_document_that_differs`, on copies made with `dataclasses.replace`. Each
    case gives at least one problem, and one of them names what differs:
    - `pullRequest { id isDraftt }` in `graphql/markPullRequestReadyForReview`;
    - `since:` in place of `after:` in `graphql/Repository.discussions`;
    - `$number: String!` in `graphql/PullRequest.reviewThreads`;
    - `$input: UnpinIssueInput!` in `graphql/pinIssue`;
    - an unused `$extra: String`;
    - `connection=("repository", "mergeQueue")` on `graphql/Repository.mergeQueue`;
    - the document of `graphql/enablePullRequestAutoMerge` in `graphql/disablePullRequestAutoMerge`.
  - Example, `test_the_reference_is_read_as_written`:
    - `Query.repository` has the arguments `owner`, `name` and `followRenames`;
    - `Repository.mergeQueue` has the argument `branch` and the type `MergeQueue`;
    - `MergeQueue.entries` has the type `MergeQueueEntryConnection`;
    - `Mutation.pinIssue`'s `input` is `PinIssueInput!`, and `PinIssuePayload` has `clientMutationId` and `issue`;
    - `row_members` gives `{Repository.mergeQueue, MergeQueue.entries, dequeuePullRequest}` for "Read a merge queue,
      remove an entry", `{Repository.discussions, createDiscussion, addDiscussionComment,
      markDiscussionCommentAsAnswer}` for "Repository discussions", and `{createBranchProtectionRule}` for "Branch
      protection with wildcard patterns";
    - `selected_members` of `graphql/pinIssue` holds `pinIssue` and not `unpinIssue`; that of
      `graphql/Repository.discussions` holds `Repository.discussions` and not `Repository.discussionCategories`.
- **AC-4.1** — Static, G `test_the_usage_names_every_graphql_record`. The GraphQL entry of the entry script's
  `__doc__` (its `call graphql/` usage line and the `#` lines under it, up to the next usage line) holds:
  - every capability, followed by the IDs of its records before the next capability;
  - `-F NAME=JSON`, `input`, `JSON array`, `data` and `exit 2`;
  - each of AC-3.1's IDs, and `merge-pr`.
- **AC-4.2** — Static, Q `test_the_map_names_the_graphql_call`: `docs/forLLMConsumption.md` holds `call graphql/`;
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes.
- **UB-1.1** — C, and P `test_the_fork_produces_the_golden_case` and `test_the_parsers_match_option_by_option`, pass
  unedited. The PR diff changes no line of `CASES`, C or P.
- **UB-1.2** — K and N pass unchanged, as do R's existing tests. `cmd_call`'s REST steps run as before.
- **UB-2.1** — C `test_the_credential_comes_only_from_the_file`, unchanged, scans the edited modules. No option is
  added.
- **UB-2.2** — V `test_the_wrapper_imports_only_the_standard_library`, unchanged, scans `graphql_only.py`,
  `registry.py` and `commands/call.py`.
- **UB-3.1** — `src/payload/test/test_wrapper_delivery.py` passes in CI's `tests` leg, and the PR diff names neither
  file.

## Security Considerations

- **Credential.** The source is unchanged (`_load_token`, UB-2.1), and no token option is added. A GraphQL call posts
  only to `GRAPHQL_URL`, and `_send`'s origin check holds for it as for REST.
- **What can be sent.** The document is the record's constant. A caller sets variables only, so no GraphQL the caller
  writes reaches GitHub. Variables are encoded by `json.dumps` inside the body. A refusal names the caller's names with
  `json.dumps` and never a value.
- **Output.** A GraphQL result prints only through `print_json`. `print_json`'s `json.dumps` keeps its default
  `ensure_ascii=True`, which escapes every character outside ASCII, and RFC 8259 §7 escapes U+0000 to U+001F, so,
  unlike #28 D3's raw bytes, a GraphQL result cannot write a terminal escape.
- **Gates.** D5 refuses the mutations that write a branch, arrange a merge, or move an issue into another repository
  (requirements Requirement 3). The hooks are unchanged.
- **Destructive or costly operations.** `deleteProjectV2`, `createSponsorship` (a payment) and
  `createBranchProtectionRule` (it sets `allowsForcePushes` for any `pattern`) can be called (requirements Residuals).
  Whether to run one is the caller's decision under `continuous-work.md` Exception 1. `conventions.md` "Mutations" asks
  for mutations one at a time, spaced apart; each `call` sends one.
- **Dependencies.** None are added, and no subprocess is started.

## Operability

Not applicable. Nothing deploys, and a session here runs the product wrapper only after a release is promoted
(`config/toolchain.json` deviation for `scripts/github_wrapper.py`).

## Acceptance Criteria Mapping

Test files:

- G = `src/payload/test/test_github_api_graphql_only.py`
- R = `src/payload/test/test_github_api_registry.py`
- Q = `test/test_github_graphql_contract.py`
- V = `test/test_github_wrapper_coverage.py`
- K = `src/payload/test/test_github_api_call.py`
- N = `test/test_github_wrapper_contract.py`
- C = `src/payload/test/test_github_wrapper_compat.py`
- P = `test/test_github_wrapper_fork_parity.py`

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1, D2, D4, D6 | design review; Q `test_every_record_matches_the_reference` |
| AC-1.2 | `graphql_only.OPERATIONS`, `PENDING_CAPABILITIES` | Q `test_every_capability_has_a_record`; V `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` |
| AC-1.3 | the records' documents; `selected_members`, `row_members` | Q `test_every_member_a_row_names_is_selected` |
| AC-1.4 | `GraphQLOperation.operation_id`; `_capability_problems` | V `test_a_graphql_record_id_is_its_own`, `test_one_module_per_family_holding_only_its_own_ids` |
| AC-1.5 | `_capability_problems` | V `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` |
| AC-2.1 | `cmd_call`, `registry.graphql_call`, `Transport.graphql` | G `test_a_variable_holds_the_given_json_value`, `test_every_record_is_called_through_main` |
| AC-2.2 | `registry.graphql_call` → `Transport.graphql_nodes`, `print_json` | G `test_every_record_is_called_through_main`, `test_a_merge_queue_prints_every_entry` |
| AC-2.3 | `registry.graphql_call` → `Transport.graphql`, `print_json` | G `test_every_record_is_called_through_main` |
| AC-2.4 | `Transport` (unchanged), `_run_command` (unchanged) | G `test_a_graphql_failure_exits_1_with_its_details` |
| AC-2.5 | `check_graphql_call`, `registry.declared_variables`, `registry.graphql_lookup` | G `test_an_undeclared_variable_is_refused`; R `test_variables_are_the_documents_definitions`, `test_graphql_lookup_finds_one_record` |
| AC-2.6 | G | G `test_every_record_is_called_through_main` |
| AC-3.1 | `GATED_OPERATIONS`, `refuse_gated` | G `test_a_refused_mutation_sends_nothing`; Q `test_every_record_matches_the_reference` |
| AC-3.2 | `GATED_OPERATIONS` | G `test_a_refused_mutation_sends_nothing` |
| AC-3.3 | G | G `test_a_refused_mutation_sends_nothing` |
| AC-4.1 | entry script docstring (D7) | G `test_the_usage_names_every_graphql_record` |
| AC-4.2 | `docs/forLLMConsumption.md` (D7) | Q `test_the_map_names_the_graphql_call`; `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` |
| UB-1.1 | `commands/*` but `call.py`, `_build_parser`, `main`, `CASES` (unchanged) | C; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; PR diff |
| UB-1.2 | `cmd_call`'s REST steps, `registry.lookup`, `send`, `pages` | K; N; R (existing tests) |
| UB-2.1 | `_load_token`; `call`'s options (unchanged) | C `test_the_credential_comes_only_from_the_file` |
| UB-2.2 | `registry.py`, `graphql_only.py`, `commands/call.py` | V `test_the_wrapper_imports_only_the_standard_library` |
| UB-3.1 | none (the files are untouched) | `src/payload/test/test_wrapper_delivery.py`; PR diff |

## Residuals

- **The `merge-pr` refusal's wording.** If this change lands before #32, `graphql/enablePullRequestAutoMerge`'s
  refusal reads #27's "use the merge-pr subcommand, which sends it"; whichever lands second adds it to `GATED_NOT_SENT`.
- **Objects this wrapper did not create.** A discussion comment or a Projects v2 project that this wrapper did not
  create has no ID source among the records: the REST `projects/get-for-*` and `projects/list-for-*` records are
  pending, and selecting `comments` or `ProjectV2` connections is outside the rows' members.
- **Partial mutation results.** A mutation answered with `errors` and partial `data` exits 1 and prints only the
  `errors` (AC-2.4), though its effect may have applied (`conventions.md` "Errors"); check before running it again.
- **What Q and #10 leave.** Q compares names and types along each selection, not what an `input` object holds, which
  GitHub validates (exit 1, AC-2.4); #10's fixture settles which reachable records its account can exercise (the
  branch-protection plan, Discussions on a private repository).
