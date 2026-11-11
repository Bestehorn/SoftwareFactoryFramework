# Design — issue #44: GitLab wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-5.2, UB-1.1..UB-3.1, frozen). Builds on
`.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn") and
`.claude/specs/issue-13-gitlab-wrapper-foundation/design.md` ("#13 Dn"). The model is the GitHub twin's approved
`.claude/specs/issue-30-github-graphql-capabilities/design.md` ("#30 Dn", branch
`issue-30-github-graphql-capabilities`); "Differences from #30" says where this design departs from it.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #44, "GitLab wrapper rewrite, part 2 slice:
   the GraphQL-only capabilities", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Overview

`graphql_only.py` declares one `GraphQLOperation` per mutation and per field member of an "Only in GraphQL" row (D1),
each called by a `graphql#<member>` ID (D2) through the path #41 built: `registry.lookup` finds the record and
`registry.call` sends it (D3). An `Upload` variable takes its file with `--file`, and `Transport.graphql` sends the call
as the multipart request of `conventions.md` "File uploads" (D4). Global IDs are ones other records print (D5).
`GATED_OPERATIONS` refuses `workItemCreate` and `workItemsCsvImport`, saying that no subcommand sends them (D6). A
contract test reads every document against `docs/api-reference/gitlab/graphql/`, and a fake-host suite calls every
record through `main` (D7). The usage docstring and the map name the call (D8).

## Design

### D1 — One record per operation (AC-1.1, AC-1.2, AC-1.3)

**The rule.**

- Each mutation a row names gets its own record. A mutation document runs every root field it selects, serially
  (GraphQL spec §6.2.2), so one record per capability would update and delete in one call.
- Each field member gets its own query record. Row 1's field members sit under different roots (`workItem`,
  `workItemsByReference`, `project`, `group`, `namespace`), and a record pages one connection (`connection` is one key
  path), so no record serves two.
- Row 2's `WorkItem` with its `widgets` gets `graphql#WorkItem.widgets`.
- Every record's `capability` is its row's first cell, verbatim. `PENDING_CAPABILITIES` becomes `frozenset()`.
- A record whose reference section carries `Notes: experiment` or `Notes: **deprecated**` says so in its comment.

**Query records.** `graphql#Project.workItems` shows the shape of a paging record:

```graphql
query($fullPath: ID!, $state: IssuableState, $types: [IssueType!], $after: String) {
  project(fullPath: $fullPath) {
    workItems(state: $state, types: $types, first: 100, after: $after) {
      nodes { id iid title state webUrl workItemType { id name } }
      pageInfo { hasNextPage endCursor }
    }
  }
}
```

- `first` is the maximum page size of `conventions.md` "Connections and cursor pagination". `$after` is the cursor
  `Transport.graphql_nodes` sets.
- A variable the caller leaves out leaves its argument out: "Let hasValue be true if variableValues provides a value
  for the name variableName" (GraphQL spec §6.4.1 `CoerceArgumentValues`).

W is `id iid title state webUrl workItemType { id name }`; U is `id title severity state reportType detectedAt project
{ fullPath }`. `fullPath` is `ID!` and `id` the type the root's signature names.

| ID | Capability | Caller's variables | `connection` | Below the root; fields read |
|---|---|---|---|---|
| `graphql#workItem` | Work items | `id` (`WorkItemID!`) | `()` | `workItem(id: $id)`; W |
| `graphql#workItemsByReference` | Work items | `refs` (`[String!]!`), `contextNamespacePath` (`ID`) | `("workItemsByReference",)` | `workItemsByReference(refs: $refs, contextNamespacePath: $contextNamespacePath, first: 100, after: $after)`; W |
| `graphql#Project.workItems` | Work items | `fullPath`, `state` (`IssuableState`), `types` (`[IssueType!]`) | `("project", "workItems")` | the document above |
| `graphql#Group.workItems` | Work items | as above | `("group", "workItems")` | `group(fullPath: $fullPath)`, then as above |
| `graphql#Namespace.workItems` | Work items | as above | `("namespace", "workItems")` | `namespace(fullPath: $fullPath)`, then as above |
| `graphql#WorkItem.widgets` | Epics with new features (assignees, health status, links to other item types) | `id` | `()` | `workItem(id: $id) { id iid title workItemType { id name } widgets { type ... on WorkItemWidgetAssignees { assignees { nodes { id username } } } ... on WorkItemWidgetHealthStatus { healthStatus } ... on WorkItemWidgetLinkedItems { linkedItems { nodes { linkType workItem { id } } } } } }` |
| `graphql#Project.branchRules` | Branch rules | `fullPath` | `("project", "branchRules")` | `branchRules(first: 100, after: $after)`; `id name isDefault isProtected matchingBranchesCount` |
| `graphql#Group.vulnerabilities` | Group-wide and instance-wide vulnerability lists | `fullPath` | `("group", "vulnerabilities")` | `vulnerabilities(first: 100, after: $after)`; U |
| `graphql#Query.vulnerabilities` | Group-wide and instance-wide vulnerability lists | none | `("vulnerabilities",)` | `vulnerabilities(first: 100, after: $after)`; U |
| `graphql#Query.vulnerability` | Group-wide and instance-wide vulnerability lists | `id` (`VulnerabilityID!`) | `()` | `vulnerability(id: $id)`; U |
| `graphql#Project.ciPipelineCreationRequest` | Asynchronous pipeline creation | `fullPath`, `requestId` (`String!`) | `()` | `ciPipelineCreationRequest(requestId: $requestId) { id status error pipelineId pipeline { id iid status } }` |
| `graphql#queryComplexity` | Query cost introspection | none | `()` | `queryComplexity`; `score limit` |

**Mutation records.** Each selects `errors`, which `conventions.md` "Mutations" says every payload returns ("Always
select it") and `transport.graphql_error_messages` reads (AC-2.4). Two shapes:

- `mutation($input: <I>!) { <m>(input: $input) { <selection> errors } }`, `<I>` being the input type of `<m>`'s
  signature line (`workItemUpdate(input: WorkItemUpdateInput!)`); the caller's one variable is `input`.
- The input object written into the document, each of its fields a variable, for the two mutations that take an
  `Upload` (D4) and for `pipelineCreate`, whose row asks for `async: true`.

| ID | Capability | Input | Selection besides `errors` |
|---|---|---|---|
| `graphql#workItemCreate` (refused, D6) | Work items | `$input` | `workItem { id iid webUrl }` |
| `graphql#workItemUpdate` | Work items | `$input` | `workItem { id iid title state }` |
| `graphql#workItemDelete` | Work items | `$input` | `namespace { fullPath }` |
| `graphql#workItemExport` (deprecated in 18.0; the reference also documents `workItemsCsvExport` with the same input) | Work items | `$input` | `message` |
| `graphql#branchRuleCreate`, `graphql#branchRuleUpdate`, `graphql#branchRuleDelete` | Branch rules | `$input` | `branchRule { id name }` |
| `graphql#designManagementUpload` | Design uploads | `input: {projectPath: $projectPath, iid: $iid, files: $files}`; `$projectPath: ID!`, `$iid: ID!`, `$files: [Upload!]!` | `designs { id filename } skippedDesigns { id filename }` |
| `graphql#pipelineCreate` | Asynchronous pipeline creation | `input: {projectPath: $projectPath, ref: $ref, variables: $variables, inputs: $inputs, mergeRequestIid: $mergeRequestIid, async: true}`; `$projectPath: ID!`, `$ref: String!`, `$variables: [CiVariableInput!]`, `$inputs: [CiInputsInput!]`, `$mergeRequestIid: String` | `requestId pipeline { id iid status }` |
| `graphql#workItemsCsvImport` (refused) | Work item CSV import | `input: {projectPath: $projectPath, file: $file}`; `$projectPath: ID!`, `$file: Upload!` | `message` |

An input-object field whose variable is not given is left out: `{ a: $var, b: 123 }` with variables `{}` coerces to
`{ b: 123 }` (GraphQL spec §3.10 "Input Coercion"). Every name is read from a table of the reference; Q proves it (D7).

**Alternatives:**

- **One record per capability.** Rejected: §6.2.2 above.
- **The `$input` shape for the three mutations above.** Rejected: `--file` names an `Upload` variable (D4), and
  AC-1.3 asks for `async: true` in the document.

**The coverage test (V) needs no change.** `capability_problems` collects the records' capabilities into a set, so
several records of one capability give no problem, and an empty `PENDING_CAPABILITIES` passes its pending checks. An ID
declared twice, by two records or by a record and a family module, is `registry.lookup`'s refusal, which AC-1.4's test
applies to every record (D7). (#30 D1 changed GitHub's check because it reported a capability declared twice.)

### D2 — The operation ID (AC-1.1)

- **The ID** is `graphql#` plus the member as the row's code span writes it, without arguments or selection: a
  mutation (`graphql#branchRuleCreate`), a root field (`graphql#workItem`; `graphql#Query.vulnerabilities`, as row 4
  writes it), or `<Type>.<field>` (`graphql#Project.branchRules`). Row 2's is `graphql#WorkItem.widgets`: the type it
  names and the field AC-1.3 adds. This is #41 D8's slice scheme ("such as `graphql#workItemCreate` or
  `graphql#Project.branchRules`"), which `commands/call.py`'s docstring already states.
- No REST ID starts with `graphql#`: a REST ID's stem is a `rest/<stem>.md` page, and no page is `rest/graphql.md`.
- **`GraphQLOperation`'s fields are unchanged.** It already has `operation_id`, `capability`, `document` and
  `connection` with the default `()` (#41 D2). A record with `connection` `()` goes through `Transport.graphql` and
  prints `data`.
- Q ties each ID to its document (D7), so a refused ID names the mutation its document runs (D6).

### D3 — The GraphQL call (AC-2.1 to AC-2.5)

```
python scripts/gitlab_wrapper.py call graphql#<member> [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]...
    [--file NAME=PATH]...
```

`call_operation`'s steps are #41 D2's, unchanged but where D4 and D6 say:

1. `refuse_gated` (D6).
2. `registry.lookup` finds the record over every family module and `graphql_only`.
3. `call_values`: the `-f`/`-F` values as variables, a name given twice keeping its last value; then D4's files.
4. `check_parameters` refuses, in one message and before any request, every `--path` and `--query` name, every
   `-f`/`-F` name outside `registry.variables` (a paging record's `after` included), and every `--file` name outside
   `registry.upload_variables` (D4): exit 2 (#41 D4).
5. `send_call` → `registry.call` → `Transport.graphql_nodes` for a record with a `connection`, else
   `Transport.graphql`; `print_json` of the nodes of every page, collected before anything prints, or of `data`
   (#41 D3).

- **No default.** No variable takes a value from `config/gitlab.json`, so the variables are exactly those given
  (AC-2.1); the caller gives `fullPath`.
- **Errors.** `Transport` raises `GitLabAPIError` for every condition of AC-2.4 (`graphql`, `graphql_nodes`,
  `_connection`, `_send`, `_attempt`, `_file_part`), and `_report` logs its message and details and returns 1 (#41
  D3), unchanged. `graphql_error_messages` reads payload `errors` for a document that starts with `mutation`
  (`MUTATION_DOCUMENT`), as every mutation record does.

### D4 — An `Upload` value (AC-1.1, AC-3.1, AC-3.2)

**On the command line.** `--file NAME=PATH` names a declared variable whose type is `Upload` (`$file: Upload!`) or a
list of them (`$files: [Upload!]!`).

- For a list, each `--file` of that name is one item, in command-line order, a single one included; for one `Upload`,
  a name given twice keeps its last file.
- A `--file` replaces a `-f`/`-F` value of the same name, as #41 D2 has it for REST.

```
python scripts/gitlab_wrapper.py call graphql#designManagementUpload -f projectPath=group/project -f iid=5 \
    --file files=a.png --file files=b.png
```

**`commands/call.py`.** `documented_names` gives a GraphQL record's `ARG_FILES` the names of
`registry.upload_variables`. `call_values` puts each `--file` value into the values: a list of `pathlib.Path` for a
name `upload_variables` maps to `True`, else the one `Path`, a name outside `upload_variables` included, which D3's
step 4 then refuses with exit 2 before anything is sent.

**`registry.py`.**

- `upload_variables(*, operation) -> Dict[str, bool]`: each declared variable whose type, with `[`, `]`, `!` and white
  space removed, is `Upload`, mapped to whether the type is a list (it begins with `[`). The types are read from the
  `$name: Type` definitions where `variables` reads the names.
- `split_uploads(*, values) -> Tuple[Dict[str, Any], Tuple[Tuple[str, Path], ...]]`: the variables with each `Path`
  value, and each `Path` item of a list, replaced by `None`; and the files in that order, each with the operations
  path it fills, `variables.<name>` or `variables.<name>.<index>`.
- `call` sends a record without a `connection` as
  `transport.graphql(document=..., variables=..., files=...)` from `split_uploads`. No record with a `connection`
  declares an `Upload` variable.

**`transport.py`.** `Transport.graphql` gains `files: Sequence[Tuple[str, Path]] = ()`, each pair an operations path
and its file (not a part name, as in `request`). Without files it sends the JSON body it sends now. With files, the
body and its `Content-Type` are what `request_body(form=..., json_body=None, files=...)` returns, the multipart branch
a REST `--file` call takes:

- the form pair `operations`: `json.dumps` of `{"query": document, "variables": variables}`;
- the form pair `map`: `json.dumps` of the object mapping each file's part name to a list holding its path,
  `{"0": ["variables.files.0"], "1": ["variables.files.1"]}`; the i-th file's part name is `str(i)`;
- one file part per file (`_file_part`): its bytes unchanged, `path.name` as its file name.

Its `multipart_body` writes the form pairs before the files, the order the spec sets: "the fields are ordered: 1.
`operations` … 2. `map` … 3. File fields". The job-token refusal, `Authorization: Bearer`, the URL, `_send` (origin
check, `429` retries) and the reading of `data` and `errors` are as they are now. A file that cannot be read raises
`_file_part`'s `GitLabAPIError` before anything is sent.

**AC-1.1's answer:** `Transport.graphql` builds Requirement 3's request from what `registry.split_uploads` gives it.

**Alternatives:**

- **`--file files.0=a.png`, the map path as the name.** Rejected: the caller would number the items, and a skipped
  number would send a `null` item.
- **A record field naming its `Upload` variables.** Rejected: the document's `$name: Type` already says it.
- **A separate `Transport.graphql_upload`.** Rejected: it would repeat `graphql`'s refusal, send and error reading.

### D5 — Global IDs: the caller supplies them (AC-1.1)

A global ID is `gid://gitlab/<ModelClass>/<record id>`, and "Knowing the class name for a given REST resource is the
hard part"; "`WorkItemID` currently also accepts `IssueID` values … this transitional behaviour can be removed without
notice" (`conventions.md` "Global IDs"). So no record builds one: the caller gives the ID another record printed.

| Variable or input field (type) | Where the caller reads it |
|---|---|
| `id` of `graphql#workItem` and `graphql#WorkItem.widgets`; `input.id` of `graphql#workItemUpdate` and `graphql#workItemDelete` (`WorkItemID`) | a node `id` of `graphql#Project.workItems`, `graphql#Group.workItems`, `graphql#Namespace.workItems` or `graphql#workItemsByReference`; an epic is a node of `graphql#Group.workItems` with `-F 'types=["EPIC"]'` |
| `input.workItemTypeIds` of `graphql#workItemExport`; `input.workItemTypeId` of the refused `graphql#workItemCreate` (`WorkItemsTypeID`) | `workItemType.id` of any work-item node above |
| `input.id` of `graphql#branchRuleUpdate` and `graphql#branchRuleDelete` (`ProjectsBranchRuleID`) | a node `id` of `graphql#Project.branchRules`; `branchRule.id` printed by `graphql#branchRuleCreate` |
| `id` of `graphql#Query.vulnerability` (`VulnerabilityID`) | a node `id` of `graphql#Group.vulnerabilities` or `graphql#Query.vulnerabilities` |
| `requestId` of `graphql#Project.ciPipelineCreationRequest` | `requestId` printed by `graphql#pipelineCreate` |
| `fullPath`, `projectPath`, `contextNamespacePath`, `input.namespacePath` (`ID`, a path) | the full path itself, `group/project` (`conventions.md` "Paths and IIDs") |
| `iid` of `graphql#designManagementUpload` (`ID!`) | the issue's `iid`, as `issue list` and `issue show` print it |

**Alternatives:** a look-up query inside each mutation call (rejected: a GraphQL operation is a query or a mutation, so
it takes a second request per call); a `gid://` built from a REST `id` (rejected: the quotes above).

### D6 — Refusals (AC-1.1, AC-4.1 to AC-4.3)

- `graphql_only` defines `OP_WORK_ITEM_CREATE = "graphql#workItemCreate"` and
  `OP_WORK_ITEMS_CSV_IMPORT = "graphql#workItemsCsvImport"`. `GATED_OPERATIONS` becomes `Mapping[str,
  Optional[str]]` and maps each to `None`; its two entries stay as they are.
- `refuse_gated` tests membership, not the value. For `None` it raises `ValueError` ending ": no subcommand sends it";
  for a subcommand, today's message, unchanged. This is #27's GitHub shape (`github_api/commands/call.py`
  `refuse_gated`).
- **Why `None` for both (AC-1.1's answer).** `issue create` sends `plan#create-an-issue`, never `workItemCreate`, which
  creates a work item of any type (`workItemTypeId`), and no subcommand imports a CSV. GitHub maps its issue-creating
  `campaigns/create-campaign` to `None` the same way.
- **The log** names the ID, which holds the mutation's name; Q fails a mutation record whose ID is not `graphql#` plus
  its one root field (D7).
- Step 1 runs before `registry.lookup`, so nothing is sent. Both records stay declared, so row 7 is served and
  `PENDING_CAPABILITIES` is empty (DL-002).
- The branch-rule mutations are not refused (DL-002; Residuals). The `GATED_OPERATIONS` comment names its class: a
  record that commits to or merges into a branch, or that creates an issue or another work item (#41 D8).

### D7 — Proving the calls (AC-1.1, AC-1.3, AC-2.5, AC-3.2, AC-4.3)

**The fake host needs no addition.** `FakeGitLab.script_next` answers each `POST` to `GRAPHQL_URL` in order, and
`RecordedRequest` keeps the body. G reads a multipart body with `email.parser.BytesParser`, its `Content-Type` header
prefixed, as N's `sent_call` does: each part's `Content-Disposition` `name` and `filename`, and its bytes.
`gitlab_wrapper_fixtures.py` stays as #41 left it.

**G: the calls through `main`** (`src/payload/test/test_gitlab_api_graphql_only.py`, #41 D8's slice file).

- `test_every_record_is_called_through_main` covers each record of `graphql_only.OPERATIONS` whose ID is not in G's
  constant `REFUSED_IDS` (D6's two IDs, which `test_a_refused_mutation_sends_nothing` also iterates). It finds the
  records by iterating the module, and fails when it calls none.
  - Argv: `call <id>`; `--file NAME=<a file in tmp_path>` per `Upload` variable, twice for a list; `-f NAME=v-NAME`
    for every other name of `registry.variables`.
  - A record without a `connection` is answered with a `data` object; one with a `connection` with two pages nested at
    its path, the first with `hasNextPage` `true` and `endCursor` `"c1"`.
  - Oracle: exit 0. Each `POST` to `GRAPHQL_URL` carries the document as `query` and the given variables (`after`
    `null`, then `"c1"`), or, for an `Upload` record, AC-3.1's parts. Stdout is `print_json`'s text of `data`, or of
    both pages' nodes in order.
- Its other tests are under Correctness Properties.

**Q: the documents against the reference** (`test/test_gitlab_graphql_contract.py`; in `test/` because it reads
`docs/api-reference/gitlab/`, as N does).

- `reference_schema(*, graphql_dir)` reads each type's fields with their types and arguments:
  - `Query`: each `##` section of `queries.md`, from its signature line `` `name(arg: Type, …)` → [`Type`](…) ``;
  - `Mutation`: each section of `mutations-a-j.md` and `mutations-j-w.md`, from its signature line; its
    `` Input `I`: `` table (`| Input field | Type | Default | Notes |`) as `I`'s fields and its `` Payload `P`: ``
    table (`| Payload field | Type | Notes |`) as `P`'s;
  - each section of `objects-*.md` and `interfaces.md`: its `- Implements:` names and its
    `| Field | Type | Arguments | Notes |` rows. An Arguments cell lists `` `name: Type` `` spans, each cut at ` (`
    (`` `licenses: [String!] (experiment since 19.2)` ``).

  A Type cell's link text is the type; the walk enters it with `[`, `]` and `!` removed. A name no section defines is
  a leaf.
- `read_document(*, document)` reads the subset the records use: one `query` or `mutation`, with or without `$name:
  Type` definitions; fields whose argument values are a `$variable`, an integer, `true`, `false`, or an object
  `{name: value, …}` of these; nested selections; inline fragments `... on T { … }`. Commas are white space
  ("Insignificant Commas"). Any other token is a problem.
- `document_problems(*, record, schema)` walks from the root type and names:
  - a field its parent type lacks; an argument its field lacks; an input-object field its input type lacks;
  - a `$variable` that is not declared, or whose declared type is neither the location's type nor that type with `!`
    added (§5.8.5 `AreTypesCompatible`); a declared variable never used; `true` or `false` where the type is not
    `Boolean`, an integer where it is not `Int`;
  - a leaf with a selection, an object or interface without one; a fragment type whose `Implements:` lacks the field's
    type;
  - for a record with a `connection`: a selected path that differs from it; and, on the path that matches it, a last
    field without `after: $after`, a selection without `nodes` and `pageInfo { hasNextPage endCursor }`, or a `$after`
    not declared `String`;
  - for a mutation: more than one root field, no `errors` in its selection, or an ID other than `graphql#` plus its
    root field; for a query: an ID whose member (D2) is not among its `selected_members`.
- `selected_members(*, record, schema)`: `<Type>.<field>` for every field the walk visits (a fragment's under its
  type), each root field bare and as `Query.<field>` (a mutation's bare), and every type the walk enters.
- `row_members(*, conventions)`: per "Only in GraphQL" row, each code span of its GraphQL cell as a name (up to its `(`
  or ` {`), the `name: literal` pairs inside its `( )`, and the names inside its `{ }`. Row 2 also holds
  `WorkItem.widgets` (AC-1.3), a constant of Q.
- `member_problems(*, row, records, schema)`: each member of the row that no record of its capability selects; with
  pairs, that no such record passes each pair at that field, as an argument or as a field of its input object; with
  names, that no such record selects each directly under it.

**What #11's test project cannot exercise.** #11's fixture creates one private project with `POST /projects`
(`docs/reports/self-hosting-proposal-2026-11-07.md` "One repository per test run"), and `namespace_id` "If not
provided, defaults to the current user's personal namespace" (GitLab REST "Create a project").

| Records | Why | What proves the call |
|---|---|---|
| `graphql#Group.workItems`, `graphql#Group.vulnerabilities` | the project sits in a personal namespace; no group exists | Q and G |
| `graphql#Query.vulnerabilities` (row 4's instance-wide list) | it reads the token user's instance security dashboard (`conventions.md` row 4), now the security center: "Tier: Ultimate"; "The security center is empty by default. You must add one or more projects that have been configured with at least one security scanner" (GitLab Docs "Security center") | Q and G |
| `graphql#Query.vulnerability` | its `id` comes from a vulnerability list, and the vulnerability report is "Tier: Ultimate" (GitLab Docs "Security dashboards") and needs a scanner's findings | Q and G |
| `graphql#workItemCreate`, `graphql#workItemsCsvImport` | refused, never sent (D6) | G `test_a_refused_mutation_sends_nothing`; Q |

Every other record is proven by Q and G in CI's `tests` leg; #11's real-instance run proves each one its fixture
provides for (Residuals "What Q and #11 leave").

### D8 — The usage docstring and the map (AC-5.1, AC-5.2)

**The usage docstring.** These lines go into the usage list of `src/payload/scripts/gitlab_wrapper.py`, after the
`call plan#retrieve-a-project-issue` entry:

```
    python scripts/gitlab_wrapper.py call graphql#Project.workItems -f fullPath=group/project   # a GraphQL record
        # -f NAME=TEXT and -F NAME=JSON give the document's variables; a mutation takes its input object as one,
        # input, but graphql#designManagementUpload, graphql#pipelineCreate and graphql#workItemsCsvImport take each
        # field; --file NAME=PATH gives an Upload variable's file, once per item of a list, in one multipart request.
        # A global ID is an id another GraphQL record printed. A connection prints as one JSON array of every page's
        # nodes, any other result as its data. The "Only in GraphQL" capabilities and their records:
        #   Work items: graphql#workItem graphql#workItemsByReference graphql#Project.workItems ...
        # graphql#workItemCreate and graphql#workItemsCsvImport are refused before any request: exit 2.
```

One capability line per capability, in the table's order: `#   `, the capability verbatim, `:`, the IDs of its records,
wrapped onto `#     ` lines at 120 columns.

**The map.** The `src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md` gains, before "Not installed
here": "A GraphQL-only capability is a record of `graphql_only.py`, called the same way:
`python scripts/gitlab_wrapper.py call graphql#Project.workItems -f fullPath=group/project` (`-f`/`-F` give the
document's variables, `--file NAME=PATH` an `Upload` variable's file). `test/test_gitlab_graphql_contract.py` checks
each document against `graphql/`."

**Module docstrings.**

- `graphql_only.py`: the ID scheme, the query and the two mutation shapes, that a refused record is declared but never
  sent, and the comment rule of D1.
- `commands/call.py`: a GraphQL record's `--file`, and the "no subcommand sends it" refusal.
- `registry.py` names `upload_variables` and `split_uploads`. Its module docstring and `GraphQLOperation`'s say a
  record is one query or mutation of a capability, and that several records may serve one capability (D1).
  `transport.py` names the multipart GraphQL request.
- No file of the package contains `os.environ` or `getenv` (P `test_standard_library_only`, UB-2.2, reads the
  docstrings too).

### D9 — Files

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_api/graphql_only.py` | D1's records in `OPERATIONS`; `OP_WORK_ITEM_CREATE`, `OP_WORK_ITEMS_CSV_IMPORT`; `PENDING_CAPABILITIES` empty; the docstring |
| `src/payload/scripts/gitlab_api/registry.py` | `upload_variables`, `split_uploads`; `call` passes the files; the module and `GraphQLOperation` docstrings |
| `src/payload/scripts/gitlab_api/transport.py` | `Transport.graphql`'s `files` and its multipart body; the docstring |
| `src/payload/scripts/gitlab_api/commands/call.py` | `GATED_OPERATIONS`' type and entries; `refuse_gated`; `documented_names` and `call_values` for `--file`; the docstring |
| `src/payload/scripts/gitlab_wrapper.py` | the module docstring only (D8) |
| `src/payload/test/test_gitlab_api_graphql_only.py` | new (G) |
| `src/payload/test/test_gitlab_api_registry.py` | adds `test_upload_variables_are_the_documents_upload_definitions`, `test_split_uploads_puts_null_where_each_file_goes` |
| `src/payload/test/test_gitlab_api_transport.py` | adds `test_graphql_sends_files_as_one_multipart_request` |
| `test/test_gitlab_graphql_contract.py` | new (Q) |
| `docs/forLLMConsumption.md` | the `gitlab_api/` bullet (D8) |

#41 D8's slice table, its "never" row and its exceptions:

- `transport.py` and `registry.py` are its exception for "a request form that part 1 does not build".
- `commands/call.py` beyond `GATED_OPERATIONS`: `refuse_gated` because AC-4.2 asks for a refusal with no subcommand;
  `documented_names` and `call_values` because AC-3.1's file reaches a GraphQL record only through `--file`.
- `gitlab_wrapper.py`, because AC-5.1 asks for its docstring.
- `families/*`, `_common.py`, `gitlab_wrapper_fixtures.py`, `test_gitlab_wrapper_coverage.py`,
  `test_gitlab_wrapper_contract.py`, `test_gitlab_api_call.py` and `test_gitlab_wrapper_compat.py` stay untouched.

### Differences from #30

| Point | GitLab (this change) | #30 | Reason |
|---|---|---|---|
| ID | `graphql#<member>` | `graphql/<member>` | #41 D2 and D8 |
| Call path | #41's `registry.lookup` and `registry.call`, unchanged | a prefix branch, `graphql_lookup`, `graphql_call` | #41 AC-1.9 already sends a GraphQL record |
| Coverage test | unchanged | `_capability_problems` reads IDs | GitLab's never counted capabilities (D1) |
| Mutations | `$input`, but three that write their input object | `$input` only | D4; AC-1.3's `async: true` |
| Payload | `errors` selected | `clientMutationId` selected | `conventions.md` "Mutations": payloads list `errors`, not `clientMutationId` |
| Uploads | `--file`, one multipart request | none | Requirement 3 |
| Refusals | two IDs to `None` | `merge-pr` and `None` | DL-002 |

### Sources

- `docs/api-reference/gitlab/graphql/conventions.md`: "Endpoint and request shape", "Global IDs and other
  identifiers", "Connections and cursor pagination", "Errors and partial data", "Mutations", "File uploads", "Only in
  GraphQL".
- `docs/api-reference/gitlab/graphql/`: `queries.md` (`workItem`, `workItemsByReference`, `project`, `group`,
  `namespace`, `vulnerabilities`, `vulnerability`, `queryComplexity`); `mutations-a-j.md` (`branchRule*`,
  `designManagementUpload`); `mutations-j-w.md` (`pipelineCreate`, `workItem*`, `workItemsCsvImport`); `objects-*.md`
  (`Project`, `Group`, `Namespace`, `WorkItem`, `WorkItemType`, `WorkItemWidget*`, `BranchRule`, `Vulnerability`,
  `CiPipelineCreationRequest`, `QueryComplexity`); `interfaces.md` (`WorkItemWidget`); `enums.md` (`IssueType`).
- `docs/reports/self-hosting-proposal-2026-11-07.md`: "One repository per test run".
- [GraphQL multipart request spec](https://github.com/jaydenseric/graphql-multipart-request-spec): `operations` "with
  files replaced with `null`"; `map` "the key is the file multipart form field name and the value is an array of
  operations paths"; the field order quoted in D4.
- [GraphQL, October 2021](https://spec.graphql.org/October2021/): §6.2.2 "Mutation"; §6.4.1 `CoerceArgumentValues`;
  §3.10 "Input Coercion"; §5.8.5 `AreTypesCompatible`; "Insignificant Commas".
- [GitLab REST, Projects](https://docs.gitlab.com/api/projects/), "Create a project", `namespace_id`.
- [GitLab Docs, Security center](https://docs.gitlab.com/user/application_security/security_center/) and
  [Security dashboards](https://docs.gitlab.com/user/application_security/security_dashboard/).
- [GitLab Docs, Design management](https://docs.gitlab.com/user/project/issues/design_management/): "Git Large File
  Storage (LFS) must be enabled"; deprecated in 18.6.
- [GitLab Docs, CI/CD variables](https://docs.gitlab.com/ci/variables/), "Use pipeline variables": they "can override
  variables with the same name defined in the project, group, or instance settings"; "Restrict pipeline variables".

## Testing Strategy

- **G** (`src/payload/test/`, pytest only, shipped) runs every call through the product's `main` against the unchanged
  fake host. It reads refusals with `caplog` and multipart bodies with `email.parser`. It does not read the reference.
- **R** and **T** add unit tests of `upload_variables`, `split_uploads` and `Transport.graphql`'s multipart body.
- **Q** runs in `test/`, because it reads the reference; it finds the records by iteration.
- **Property tests.** AC-2.1's value domain is #41's H `test_any_json_value_becomes_the_attribute_value` on
  `json_member`, unchanged; the GraphQL branch passes the parsed value on as it is, which G's example per JSON kind
  proves. No other criterion quantifies over a domain; no new property test.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-instance check is #11's fixture on an ephemeral `sff-test-*` project (requirements "Out of
  scope"). Until it exists, G runs each call through `main` up to the API boundary in CI's `tests` leg, and Q proves
  each document against the reference.

## Correctness Properties

Each entry gives the test kind and its oracle. Letters as in the mapping's legend.

- **AC-1.1** — Inspection: D1 (granularity, connections), D2 (IDs), D4 (the file, the request's builder), D5 (global
  IDs), D6 (the refusal's text), D7 (the unreachable records). Q's method below proves the documents.
- **AC-1.2** — Structural, Q `test_every_capability_has_a_record`: every first cell of the table is the `capability`
  of a record, and `PENDING_CAPABILITIES == frozenset()`. V `test_every_graphql_only_capability_is_served_or_pending`
  passes unchanged.
- **AC-1.3** — Structural, Q `test_every_member_a_row_names_is_selected`: `member_problems` is empty for every row; a
  failure names the row and the member. It fails when the capabilities of `row_members` differ from the table's first
  cells, or when a row has no member.
- **AC-1.4** — Structural, G `test_every_record_id_is_looked_up_once`: for every record,
  `registry.lookup(operation_id=record.operation_id) is record`; it fails on an empty `OPERATIONS`.
- **AC-2.1**
  - Parametrized, G `test_a_variable_holds_the_given_json_value`: `call graphql#workItemUpdate` with `-f input=text`,
    and with `-F input=` and `5`, `true`, `["a"]`, `{"id": "gid://gitlab/WorkItem/1"}`, `null`. Oracle: one `POST`
    to `GRAPHQL_URL` with `Authorization: Bearer <token>`, whose `query` is the document and whose `variables`, by
    `json.dumps(sort_keys=True)`, are `{"input": <the value>}`.
  - Structural: G `test_every_record_is_called_through_main`.
- **AC-2.2** — Structural: G's test above on every paging record. Example, G `test_a_work_item_list_prints_every_node`:
  `graphql#Project.workItems -f fullPath=g/p` over two pages. Oracle: two `POST`s, `after` `null` then `"c1"`;
  stdout `print_json`'s text of both pages' nodes; exit 0.
- **AC-2.3** — Structural: G's test above on every record without a connection; stdout is `print_json`'s text of
  `data`.
- **AC-2.4** — Parametrized, G `test_a_graphql_failure_exits_1_with_its_details`, cases:
  - `{"errors": […]}` and `{"data": {…}, "errors": […]}` at `200`; a payload's `{"errors": ["…"]}` on
    `graphql#workItemUpdate`;
  - HTTP `502`; `429` with `Retry-After: 0` on every answer; no response (the fake's `https_open` patched to raise
    `urllib.error.URLError`); a body `[]`;
  - `{"data": {"project": null}}` on `graphql#Project.workItems`; a first page with `hasNextPage` `true` and no
    `endCursor`;
  - a `token_type` `job`, and a `--file` path that does not exist, each with no request recorded.

  Oracle: exit 1, stdout empty, a log record holding the message and, where the error has details, one holding them.
- **AC-2.5** — Structural: G `test_every_record_is_called_through_main` (D7).
- **AC-3.1** — Parametrized, G `test_a_design_upload_sends_each_file_as_a_part`: `graphql#designManagementUpload -f
  projectPath=g/p -f iid=5` with one `--file files=…`, and with two files of distinct bytes, each file holding a byte
  that is not UTF-8 and a CRLF. Oracle: one `POST` to
  `GRAPHQL_URL`, `Authorization: Bearer`, `multipart/form-data` with a boundary; parts in the order `operations`,
  `map`, `0`, …; `operations` is `{"query": <document>, "variables": {"projectPath": "g/p", "iid": "5", "files":
  [null, …]}}`; each file part holds the file's bytes and its name; stdout `print_json`'s text of `data`. Unit, T
  `test_graphql_sends_files_as_one_multipart_request` (the same parts from `Transport.graphql`, and a job token raising
  before the file is read); R `test_upload_variables_are_the_documents_upload_definitions` (`$files : [Upload!]!` and
  `$file: Upload` found, a list and not; `$n: [Int!]` not found) and `test_split_uploads_puts_null_where_each_file_goes`
  (`variables.files.0`, `variables.files.1`, `variables.file`, in order, each value `None`).
- **AC-3.2** — The two-file case: `map` is `{"0": ["variables.files.0"], "1": ["variables.files.1"]}`.
- **AC-4.1** — Parametrized, G `test_a_refused_mutation_sends_nothing`, over `REFUSED_IDS` (`-F input={}`; `-f
  projectPath=g/p --file file=…`). Oracle: exit 2, no request recorded, a log record naming the ID. Q
  `test_every_record_matches_the_reference` ties each ID to its mutation.
- **AC-4.2** — The same test: each record holds "no subcommand sends it" and not "which sends it". K
  `test_a_gated_operation_names_its_subcommand` passes unchanged.
- **AC-4.3** — The same test fails when an ID of `REFUSED_IDS` names no record of `graphql_only.OPERATIONS`.
- **AC-5.1** — Static, G `test_the_usage_names_every_graphql_record`, on the GraphQL entry of the entry script's
  `__doc__` (its `call graphql#` usage line and the `#` lines under it), its lines joined with one space, each
  stripped of its indentation and `#`. It holds every capability followed by the IDs of its records before the next
  capability, each ID matched whole: not followed by a letter, digit or `_`, nor by `.` and a letter
  (`graphql#workItem` is not found in `graphql#workItemsByReference`); `-f NAME=TEXT`, `-F NAME=JSON`,
  `--file NAME=PATH`, `JSON array`, `data`, `exit 2`; and each refused ID. It fails when `graphql_only.OPERATIONS`
  holds no record.
- **AC-5.2** — Static, Q `test_the_map_names_the_graphql_call`: the `src/payload/scripts/gitlab_api/` bullet of
  `docs/forLLMConsumption.md` holds `call graphql#`, `--file NAME=PATH` and `Upload` (D8's sentence);
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes.
- **Q's method** (AC-1.1, AC-1.3, AC-4.1):
  - Structural, `test_every_record_matches_the_reference`: `document_problems` is empty for every record; it fails on
    an empty `OPERATIONS`.
  - Parametrized, `test_the_method_rejects_a_document_that_differs`, on `dataclasses.replace` copies; each case gives
    at least one problem, and one names what differs:
    - `workItem { id iidd }` in `graphql#workItem`; `since:` for `after:` in `graphql#Project.workItems`;
    - `$fullPath: String!` in `graphql#Project.branchRules`; `$input: WorkItemDeleteInput!` in
      `graphql#workItemUpdate`; an unused `$extra: String`; `async: 1` in `graphql#pipelineCreate`;
    - `projectPaht:` in `graphql#designManagementUpload`'s input object; `... on WorkItemType { id }` in
      `graphql#WorkItem.widgets`;
    - `connection=("project",)` on `graphql#Project.workItems`; `errors` left out of `graphql#branchRuleDelete`;
      `graphql#workItemCreate`'s document in `graphql#workItemUpdate`;
    - for `member_problems`: `async: false` in `graphql#pipelineCreate`, naming `async`.

    Each case is a record ID and a change; the copy is made inside the test.
  - Example, `test_the_reference_is_read_as_written`: `Query.workItem` takes `id: WorkItemID!`;
    `Project.workItems` is `WorkItemConnection` with `state`, `types` and `after`; `Mutation.designManagementUpload`
    takes `DesignManagementUploadInput!`, whose `files` is `[Upload!]!`; `DesignManagementUploadPayload` has
    `designs`, `skippedDesigns`, `errors`; `WorkItemWidgetAssignees` implements `WorkItemWidget`;
    `Vulnerability.dependencies` has `licenses: [String!]`; `row_members` gives `pipelineCreate` with `async: true`
    and `Project.ciPipelineCreationRequest` for row 6, and `queryComplexity` with `score` and `limit` for row 8;
    `selected_members` of `graphql#WorkItem.widgets` holds `WorkItem`, `WorkItem.widgets` and
    `WorkItemWidgetHealthStatus.healthStatus`.
- **UB-1.1** — C passes with no case, spelling or assertion edited; the PR diff changes no line of C.
- **UB-1.2** — K, N and R's existing tests pass unchanged. Example, G
  `test_a_file_for_a_variable_that_is_no_upload_is_refused`: `graphql#designManagementUpload -f iid=5 --file
  projectPath=<file>` exits 2 with no request, its log naming `"projectPath" given with --file`.
- **UB-2.1** — C `test_load_config_refusals` and `test_environment_token_ignored`, and K
  `test_call_takes_no_token_option`, pass unchanged; no option is added.
- **UB-2.2** — P `test_standard_library_only`, unchanged, scans every edited module of the package.
- **UB-3.1** — The PR diff names no file of UB-3.1; their suites pass in CI's `tests` leg.

## Security Considerations

- **Credential.** The source is unchanged (`_load_config`, UB-2.1), and no option is added. A multipart call goes
  through `_send` with `Authorization: Bearer` to `GRAPHQL_URL_TEMPLATE`'s host only, under the origin check; a job
  token is refused before a file is read.
- **What can be sent.** The documents are constants; the caller sets variables only. Variables are encoded by
  `json.dumps`, part names by `multipart_name`. `--file` sends whatever file the caller names, to the configured
  origin only (#41 "Files").
- **Output.** A result prints only through `print_json`, whose `json.dumps` keeps `ensure_ascii=True`.
- **Gates.** `issue-filing-gate` (`gate_filing.CREATE_RE`) judges `issue create` by its words and never sees `call
  graphql#workItemCreate`, so D6 refuses the two mutations that create work items (#41 Security Considerations
  "Gates"). The hooks are unchanged.
- **Destructive or costly operations.** `workItemDelete`, `branchRuleUpdate` and `branchRuleDelete` (they change a
  branch's protection), and `pipelineCreate` (it runs CI) can be called (requirements Residuals, DL-002); whether to
  run one is the caller's decision under `continuous-work.md` Exception 1. `pipelineCreate`'s `variables` override the
  project's CI/CD variables of the same name, so a call on the default branch sets what its jobs read, the delivery
  template's `MERGE_STEWARD` included; the project's `ci_pipeline_variables_minimum_override_role` decides who may set
  them (GitLab Docs "CI/CD variables"; the REST `docs/api-reference/gitlab/conventions.md` "Versioning and
  deprecations" names the projects attribute).
- **Dependencies.** None are added; `email.parser` is used by G only.

## Operability

Not applicable — nothing deploys, and `gitlab_wrapper.py` is not installed in this repository (`config/toolchain.json`
`not_installed`: the repository is on GitHub); the change reaches a GitLab project only when that project installs a
release.

## Acceptance Criteria Mapping

Test files: G = `src/payload/test/test_gitlab_api_graphql_only.py`; R = `src/payload/test/test_gitlab_api_registry.py`;
T = `src/payload/test/test_gitlab_api_transport.py`; Q = `test/test_gitlab_graphql_contract.py`;
V = `test/test_gitlab_wrapper_coverage.py`; K = `src/payload/test/test_gitlab_api_call.py`;
N = `test/test_gitlab_wrapper_contract.py`; C = `src/payload/test/test_gitlab_wrapper_compat.py`;
P = `test/test_gitlab_api_properties.py`.

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1, D2, D4, D5, D6, D7 | design review; Q `test_every_record_matches_the_reference` |
| AC-1.2 | `graphql_only.OPERATIONS`, `PENDING_CAPABILITIES` | Q `test_every_capability_has_a_record`; V `test_every_graphql_only_capability_is_served_or_pending` |
| AC-1.3 | the documents; `selected_members`, `row_members`, `member_problems` | Q `test_every_member_a_row_names_is_selected` |
| AC-1.4 | `registry.lookup` (unchanged) | G `test_every_record_id_is_looked_up_once` |
| AC-2.1 | `call_values`, `registry.call`, `Transport.graphql` | G `test_a_variable_holds_the_given_json_value`, `test_every_record_is_called_through_main` |
| AC-2.2 | `registry.call` → `Transport.graphql_nodes`, `print_json` | G `test_every_record_is_called_through_main`, `test_a_work_item_list_prints_every_node` |
| AC-2.3 | `registry.call` → `Transport.graphql`, `print_json` | G `test_every_record_is_called_through_main` |
| AC-2.4 | `Transport`, `_report` (unchanged) | G `test_a_graphql_failure_exits_1_with_its_details` |
| AC-2.5 | G | G `test_every_record_is_called_through_main` |
| AC-3.1 | `call_values`, `documented_names`, `registry.upload_variables`, `split_uploads`, `Transport.graphql` | G `test_a_design_upload_sends_each_file_as_a_part`; T `test_graphql_sends_files_as_one_multipart_request`; R `test_upload_variables_are_the_documents_upload_definitions`, `test_split_uploads_puts_null_where_each_file_goes` |
| AC-3.2 | as AC-3.1 | G `test_a_design_upload_sends_each_file_as_a_part` |
| AC-4.1 | `GATED_OPERATIONS`, `refuse_gated` | G `test_a_refused_mutation_sends_nothing`; Q `test_every_record_matches_the_reference` |
| AC-4.2 | `refuse_gated` | G `test_a_refused_mutation_sends_nothing`; K `test_a_gated_operation_names_its_subcommand` |
| AC-4.3 | G | G `test_a_refused_mutation_sends_nothing` |
| AC-5.1 | entry script docstring (D8) | G `test_the_usage_names_every_graphql_record` |
| AC-5.2 | `docs/forLLMConsumption.md` (D8) | Q `test_the_map_names_the_graphql_call`; `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` |
| UB-1.1 | the compatibility commands, `build_parser`, `main` (unchanged) | C; PR diff |
| UB-1.2 | `call_operation`'s REST steps, `check_parameters` | K; N; R (existing); G `test_a_file_for_a_variable_that_is_no_upload_is_refused` |
| UB-2.1 | `_load_config`; `call`'s options (unchanged) | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` |
| UB-2.2 | `registry.py`, `transport.py`, `graphql_only.py`, `commands/call.py` | P `test_standard_library_only` |
| UB-3.1 | none (untouched) | PR diff; the GitHub suites in CI's `tests` leg |

## Residuals

- **Branch rules stay callable (DL-002).** `branchRuleUpdate` and `branchRuleDelete` can lift the protection of the
  trunk the merge steward alone writes, where `gate_merge_steward` stays the enforcement; refusing them is its own
  change.
- **Partial mutation results.** `errors` beside partial `data` exits 1 and prints nothing, though the effect may have
  applied (`conventions.md` "Errors and partial data"); check before running it again.
- **Nested connections** a record selects (`assignees`, `linkedItems`) print their first page;
  `graphql#WorkItem.widgets` prints three widgets' data and every other widget's `type`.
- **What Q and #11 leave.** Q compares names and types, not what an `input` object holds, which GitLab validates (exit
  1). #11's fixture settles what its account exercises: a CI configuration for `graphql#pipelineCreate` and
  `graphql#Project.ciPipelineCreationRequest`, Git LFS for `graphql#designManagementUpload`, work items in a personal
  namespace.
- **Design management** is deprecated in 18.6; a regeneration that drops `designManagementUpload` fails Q.
- **`workItemExport` is deprecated in 18.0.** A regeneration that drops it fails Q, as for design management.
