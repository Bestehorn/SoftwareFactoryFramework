# Design — issue #41: GitLab wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-6.3, UB-1.1..UB-3.1, frozen). Builds on
`.claude/specs/issue-13-gitlab-wrapper-foundation/design.md` ("#13 Dn"). The parity source is the GitHub sibling's
approved design, `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn"); its decisions hold except
where "Differences from #28" says.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #15 re-assessed after part 1 landed and split into children; selected issue #41, "GitLab wrapper
   rewrite, part 2a: generic operation command, coverage-proof method, docs", and derived `prompt.md` from the issue
   body; no interview (see `qa_log.md`).
3. The operator's request quoted on #15 (relayed from #11): "I would like to file two issues for the respective github
   and gitlab wrappers, so that we can start implementing these with the complete set of API features for both repo
   hosts."

## Overview

A new command module, `src/payload/scripts/gitlab_api/commands/call.py`, adds the subcommand `call`. It sends any
record that a family module or `graphql_only.py` declares, named by its operation ID, with path values, attributes (a
file included) and GraphQL variables from the command line, and prints the response by its `Content-Type`. Other
modules gain the additions D8 lists.

A contract test in `test/` proves every declared REST record, and one unreachable operation, against its section of
`docs/api-reference/gitlab/rest/*.md` (D5). The coverage test gains the AC-5.3 checks and the GraphQL-only capability
rule (D6).

## Design

### D1 — How a record reaches the command line: a mix (AC-1.1)

| Part | Serves | Where |
|---|---|---|
| Compatibility commands, unchanged | UB-1.1's caller-used subcommands on the records of #13 D6's table. They are the only path to `ai-coding#merge-a-merge-request` (`mr merge`) and `plan#create-an-issue` (`issue create`). | `commands/pipeline.py`, `issue.py`, `label.py`, `mr.py`, `branch.py` |
| `call <operation-id>` | every other `RestOperation` in the `OPERATIONS` of every family module, and every `GraphQLOperation` in `graphql_only.OPERATIONS` | `commands/call.py` |

- `gitlab_wrapper.command_modules` finds `call.py` in the directory, and `build_parser` calls its
  `register(subparsers=...)` (#13 D2).
- `call.py`'s `GATED_OPERATIONS` maps `mr.OP_MERGE_MR` (`ai-coding#merge-a-merge-request`) to `mr merge` and
  `issue.OP_CREATE_ISSUE` (`plan#create-an-issue`) to `issue create`, imported from those modules. `call` refuses
  those IDs (D4; Security Considerations "Gates").

### D2 — The `call` grammar, and how it sends (AC-1.2, AC-1.3, AC-1.8, AC-1.9)

```
python scripts/gitlab_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
    [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]... [--file NAME=PATH]...
```

**The arguments:**

- **`<operation-id>`** (positional): a record's ID. That is `<stem>#<anchor>` for a REST record (#13 D5) and
  `graphql#<field>` for a GraphQL record (D8).
- **`--path NAME=VALUE`**: a path parameter, as text.
  - `registry.expand` writes it as one percent-encoded segment (`quote(..., safe="")`, #13 AC-2.2).
  - **The `id` default.** Take a record whose path is `/projects/:id` or starts with `/projects/:id/`. When the call
    gives no `id`, the value is the handler's `project`: the `project_id` of `config/gitlab.json`, as
    `commands/_common.PATH_PROJECT` is filled for every compatibility command (AC-1.8). No other `:id` has a default.
- **`--query NAME=VALUE`**: an attribute that the record declares with `Location.QUERY`, as text.
  - The values of one name are collected in the order given.
  - When the record declares the attribute `Kind.ARRAY`, the value is that list, even with one value.
  - For any other `Kind` the value is the one string. A repeated name becomes a list, which D4's shape check refuses.
- **`-f/--raw-field NAME=TEXT`**: an attribute of either location, with the string TEXT as its value.
  `registry.encode` places it where the record's `Param.location` says.
- **`-F/--field NAME=JSON`**: an attribute of either location, with the value `json.loads` parses: a number, a
  boolean, an array, an object or a quoted string.
  - Text that is not JSON is refused with exit 2. The call is `json.loads(s=TEXT, parse_constant=...)`, its
    `parse_constant` raising `ValueError`, so `NaN`, `Infinity` and `-Infinity`, which plain `json.loads` takes
    "outside the JSON spec" (Python docs, `json`), are such text.
  - `null` for a REST attribute is accepted but not sent, because `registry.encode` skips `None` (requirements
    Residuals); a GraphQL variable sends it.
- **`--file NAME=PATH`**: a `Kind.FILE` attribute, with `pathlib.Path(PATH)` as its value.
  - The transport reads the file when it builds the request (`transport._file_part`).
  - The body is then `multipart/form-data`, and every other body attribute is a form field in it (`registry.encode`,
    `transport.multipart_body`; #13 AC-2.4).
- **GraphQL records.** For a GraphQL record, `-f` and `-F` give its variables; any other option is refused (D4).

**Parsing:**

- Each option uses `action="append"` with default `None`; `-f` and `-F` share one `dest`, so their values keep their
  command-line order. `NAME=VALUE` splits at the first `=`.
- No `=`, an empty name, and `-F` text that `json.loads` refuses raise `argparse.ArgumentTypeError`: argparse's usage
  error, exit 2, before `_run` reads the config (Python docs, argparse `type` and `ArgumentParser.error`). `json_member`
  converts every `ValueError` of `json.loads`, the plain one `parse_constant` raises included. The message names the
  option and the text before the first `=`, rendered with `json.dumps`; it never holds a value.
- A path name, or an attribute given by `-f` or `-F`, given twice keeps its last value. A `-f` or `-F` value replaces
  the `--query` values of the same name, and `--file` replaces both.
- No option string contains `token` (UB-2.1).

**`call_operation(*, transport, project, in_progress_label, args)`** is a handler of #13 D6's contract. Its steps:

1. An ID in `GATED_OPERATIONS` is refused, naming its subcommand.
2. `registry.lookup(operation_id=...)`.
3. It builds the values: the path values (with the `id` default above) and the attributes, or, for a GraphQL record,
   the variables.
4. It runs D4's parameter check.
5. It runs the shape check:
   - A `Paging.NONE` REST record runs `registry.encode(operation=..., values=...)`. Its `ValueError` is AC-2.4's
     refusal.
   - A paged record calls `registry.pages(...)`, which runs its own look-up, encoding, GET-only check and `expand`.
     It returns the generator `Transport.pages` builds, and that generator sends nothing until it is read.
6. It sends, and the output is as in D3:
   - a `Paging.NONE` record through `registry.send(...)`;
   - a paged record by reading the generator of step 5;
   - a GraphQL record through `registry.call(...)`. That is `Transport.graphql`, or, for a record with a
     `connection`, `Transport.graphql_nodes`.

**Registry additions** (`gitlab_api/registry.py`):

- **`GraphQLOperation.capability: str`**, placed after `operation_id`: the first cell of the "Only in GraphQL" row the
  record serves, verbatim. No record exists yet, so no call site changes.
- **`attribute_name(*, name) -> str`**: `name` without one trailing `[]`, so `iids[]` names the `Param` `iids`
  (`Kind.ARRAY` writes the suffix, `_pairs`). `call_operation` applies it to every attribute name given, and the
  contract test (D5) to every table name.
- **`variables(*, operation) -> Tuple[str, ...]`**: the name of every `$name` followed, after any white space, by `:`
  in the record's `document`, in order (GraphQL `VariableDefinition : Variable : Type`).
  - For a record with a `connection`, it leaves out the cursor variable `transport.FIELD_AFTER` (imported inside the
    function, as `_declarations` imports `graphql_only`), which `graphql_nodes` sets on every page (#13 AC-4.2).
- **`send(transport, operation_id, *, values=None) -> Response`**: what `call` does for a REST record (`lookup`,
  `encode`, `expand`, `Transport.request`), returning the `Response`.
  - A GraphQL record raises `ValueError`.
  - `call` becomes `send(...).value` for a REST record, so it behaves as before.

**Transport addition:** `Response.is_json` is `headers.get_content_type() == CONTENT_TYPE_JSON`. `Response.value`
reads it in place of its own comparison.

### D3 — What prints (AC-1.4 to AC-1.7, AC-1.9)

- **A `Paging.OFFSET` or `Paging.KEYSET` record.** The items come as `Transport.pages` reads them (#13 AC-2.5, AC-2.6).
  - The items are collected, and `print_json(value=items)` prints them once the last page has arrived. A failure on
    any page prints nothing.
  - A page that is not a JSON array raises `GitLabAPIError` (`transport._page_items`, exit 1).
- **A `Paging.NONE` record.** The `Response` from `registry.send` prints as follows:

  | Response | Standard output |
  |---|---|
  | empty body | nothing |
  | `Response.is_json` | `print_json(value=response.value)` |
  | anything else | the body's bytes unchanged, through `_common.print_bytes`. It flushes `sys.stdout`, then calls `sys.stdout.buffer.write` (Python docs, `sys.stdout`), with no line end added. |

  Every row exits 0.
- **The test is on `Content-Type`, not on the body** (`conventions.md` "Responses"). `get_content_type()` lower-cases
  the type and drops its parameters, so `application/json; charset=utf-8` is JSON, and returns `text/plain` with no
  header (Python docs). A JSON `Content-Type` whose body does not parse raises `Response.value`'s `GitLabAPIError`
  (exit 1).
- **A GraphQL record.** `print_json` prints `data`, or the one array of nodes of every page.
- **Errors.** A `GitLabAPIError` from the handler, `GitLabRateLimitError` and `GitLabGraphQLResponseError` included,
  goes to `main` unchanged. `_report` logs its message, then any details, to standard error and returns 1 (AC-1.7).

### D4 — Refusals and exit codes (AC-2)

| Condition | Exit | Standard error names |
|---|---|---|
| no operation ID; a malformed `NAME=VALUE`; `-F` text that is not JSON | 2 | argparse's usage message |
| `config/gitlab.json` refused | 1 | `_load_config`'s refusal (#13 D7) |
| an ID in `GATED_OPERATIONS` | 2 | the ID and the subcommand to use (`mr merge`, `issue create`) |
| an ID that no record declares, whether only on a pending list or not in the reference; an ID declared twice (`registry.lookup`'s `ValueError`) | 2 | the ID (AC-2.1) |
| a path parameter or attribute the REST record does not document; for a GraphQL record, a variable it does not declare, or any `--path`, `--query` or `--file`; a path parameter with no value after the `id` default | 2 | one message: each undocumented name with its option (`--path`, `--query`, `-f/-F`, `--file`), each missing path parameter, then the record's documented parameters (AC-2.2, AC-2.3) |
| a value of a shape its `Kind` does not take (`registry.KIND_ACCEPTS`) | 2 | `registry.encode`'s message: the attribute and its `Kind` (AC-2.4) |
| a paged record given body values (`registry.pages`' `ValueError`) | 2 | the ID |
| an empty, `.` or `..` path value | 1 | `registry.expand`'s `GitLabAPIError` |
| a `--file` that cannot be read | 1 | `transport._file_part`'s `GitLabAPIError`, raised before anything is sent |
| a job token on a GraphQL record | 1 | `Transport.graphql`'s refusal, raised before anything is sent |
| an HTTP error, spent `429` retries, no response, GraphQL `errors` | 1 | AC-1.7 |

**What D4's parameter check reads as documented:**

- path parameters: `registry.placeholders(path=record.path)`;
- a `--query` name: the `Param`s with `Location.QUERY`;
- a `-f`, `-F` or `--file` name: every `Param`;
- a GraphQL variable: `registry.variables(operation=record)`.

These are the sets `registry.encode` accepts, `--query` narrowing them to one location. So no name that passes the
check is refused by the registry. The message lists every documented parameter, each attribute with its location and
`Kind`.

**How a refusal is written.**

- Every refusal of `call_operation`'s steps 1 to 5 is a `ValueError`: `registry.lookup`'s own, the gated refusal,
  D4's check (one message), `registry.encode`'s shape check and `registry.pages`' own.
- `call_operation` catches `ValueError` around those steps only. It logs the error with `logger.error`, and the script's
  `__main__` sends log records to standard error (#13 D7). Then it returns `_common.EXIT_REFUSED`.
- `call.py` renders every name the caller supplied with `json.dumps`, and `registry.encode` renders it with `repr`.
  Both escape control characters.

**No exit-2 row sends a request.** argparse decides the first row before the config is read. The handler decides the
other exit-2 rows before step 6, once `config/gitlab.json` has loaded: a refused config exits 1 first (`_run`).

### D5 — Proving a call no test project can reach (AC-3)

**The rule.** An operation is *unreachable* when either of these holds:

- its index row's path starts with `/admin/`, `/geo/` or `/hooks/`;
- the effective `Offering:` of its section does not name `GitLab.com`. The effective `Offering:` is the one on the
  section's own `- Availability:` line, else the one on its page's `Docs page: … · Availability:` line. A section
  carries the line only where it differs from its page (`docs/api-reference/README.md` "GitLab REST specifics"). A
  section with no `Offering:` on either line counts as offered on GitLab.com.

Every other operation is *reachable*.

- The rule takes #11's test project to be an `sff-test-*` project created with `POST /projects`
  (`docs/reports/self-hosting-proposal-2026-11-07.md` §5) on GitLab.com, by a token that does not administer the
  instance. The instance, administration, Geo and Dedicated pages carry an `Offering:` without GitLab.com
  (`conventions.md` "How the docs mark tier, offering and status"); the path arm adds the administrator, Geo and
  system-hook paths of `rest/openapi-only.md`, whose sections carry no Availability line.
- `is_unreachable(*, path, section)` in the contract module states the rule as code.

**The method: two halves**, both in `test/test_gitlab_wrapper_contract.py` (N, a reader of the reference, #13 D8).

**Reference half.** `reference_sections(*, rest_dir) -> Dict[str, Section]` reads every `rest/<stem>.md` once. It keys
each section by `<stem>#<anchor>`, the ID scheme of the index's Reference links.

- **The anchor**, computed in N by the rule of `scripts/api_reference/verify.py` `anchors`, restated; N imports neither
  `verify.py` (PyYAML) nor the generator's `common.Slugger`:
  1. Lines inside fenced code blocks are not headings. The heading's backticks, `**` and link markup are removed, and
     the text is lower-cased.
  2. Characters other than word characters, `-` and space are removed, and spaces become `-`.
  3. A slug that repeats on the page gets `-1`, `-2`, … in page order, counted over every heading of the page.
- **A section** runs from its `###` heading to the next heading:
  - `endpoints`: every `` `METHOD path` `` span of the first non-empty line under the heading, which can hold several,
    comma-separated.
  - `attributes`: the rows of its `| Attribute | In | Type |…` table. A name is the backticked text up to a ` (` or
    `[^` (an annotation, a footnote), then `registry.attribute_name`; a name read twice is one attribute.
    - A row whose name is another row's name followed by `[` or `:` (`position[base_sha]`, `actions[].action`,
      `strategies:name`) is part of that attribute, never a row a record lacks; its value goes inside the parent's
      (`-F 'position={"base_sha": "…"}'`; `create#create-a-commit`, multipart when its `file` is given, sends
      `actions` by `registry._pairs`).
    - A bracketed body row with no parent row is declared in a FORM-body record, whose pair GitLab reads as the hash
      member (`conventions.md` "Arrays, hashes and arrays of hashes").
    - `In` is `path`, `query` or `body`; `form`, a multipart part, is read as `body`. An `In` `header` row is a request
      form part 1 does not build (`Transport.request` takes no header); such rows sit in `*name`-glob sections
      (`rest/openapi-only.md` "The NuGet Symbol File Download Endpoint"), pending by requirements Residuals.
    - An alternation row (`name or context`) is not an attribute; its alternatives are, as their own rows.
  - `offering`: the effective `Offering:` above.
- **`record_problems(*, record, section)`** names every difference:
  - a record with no section;
  - a `(method, path)` that is not among the section's endpoints;
  - an `In` `path` row that is a placeholder (`registry.placeholders`) of none of the section's endpoints;
  - a `Param` that matches no row by name;
  - a `Param` whose location differs from its row's `In`;
  - a `Param` whose name holds `[` or `:` and is not a `parent[key]` name of a `Location.QUERY` `Param` or of a
    `BodyFormat.FORM` record (part 1's `not[labels]`);
  - a query or body row that the record lacks;
  - a `fixed` name that is not a query row.
- **Paging parameters.** `PAGING_PARAMETERS` holds `page` and `per_page` for `Paging.OFFSET`, and `pagination`,
  `per_page`, `order_by` and `sort` for `Paging.KEYSET` (`conventions.md` "Offset-based", "Keyset-based"). For a
  paged record they are documented query names: a record declares them or not, a sent one is no difference, and none
  is a row a record lacks.

**Call half.**

- **`sent_call(*, request)`** reads a request the fake host recorded: its method, its path after `/api/v4`, the names
  of its decoded query pairs, and the names of its body members.
  - Body members are the top-level keys of a JSON body, the pairs of a form body, or the parts of a multipart body:
    each part's `Content-Disposition` `name`, read with `email.parser.BytesParser`.
  - A query pair, form pair or multipart part name is read as the longest documented attribute name that it equals or
    that it continues with `[`. So `assignee_username[]` is `assignee_username`, `not[labels][]` is `not[labels]` and
    `actions[0][action]` is `actions`. A name that matches none is kept up to its first `[`.
- **`call_problems(*, section, values, sent)`** names:
  - a method other than the section's;
  - a path other than the section's, with each `:name` replaced by its value;
  - a sent query or body name that the section does not document in that place;
  - a given attribute that is missing from the place the section documents it in.
- The test values are alphanumeric, so expanding the path needs no encoding.

**Applied to every declared record:**

- **`test_every_record_matches_its_reference_section`** applies the reference half to every REST record that
  `discover_families` yields.
- **`test_every_record_is_sent_as_its_section_documents`** uses one temporary project and one fake host
  (`src/payload/test/gitlab_wrapper_fixtures.py`, with D8's helpers).
  - It covers each REST record outside `GATED_OPERATIONS`. For each one it runs a `call` through the product's `main`,
    giving a value for every path parameter and `Param` of the record, typed by its `Param.kind`:

    | Attribute | Given as |
    |---|---|
    | a path parameter | `--path NAME=v1` |
    | a `SCALAR` query attribute | `--query NAME=v1` |
    | a `SCALAR` body attribute | `-f NAME=v1` |
    | an `ARRAY` | `-F NAME=["v1"]` |
    | a `HASH` | `-F NAME={"k": "v1"}` |
    | an `ARRAY_OF_HASHES` | `-F NAME=[{"k": "v1"}]` |
    | a `FILE` | `--file NAME=<a file in tmp_path>` |

  - The host answers the request through `FakeGitLab.script_next`: `[]` for a paged record and `{}` for any other.
  - The test expects exit 0, treats a refusal as a problem, and applies the call half.
- Both tests find the records by discovery, so a record a slice declares is proven without editing N. For an
  unreachable operation these two halves are the whole proof. A reachable operation also gets #11's real-instance run.
- **`test_a_section_is_read_as_the_reference_writes_it`** pins the reader and the records `record_problems` passes:
  - `software-supply-chain-security#as-a-regular-user` is `GET /users`, and `…#as-a-regular-user-1` is `GET /user`.
  - `plan#list-all-project-issues` has the path parameter `id`, the query attributes `iids` (from `iids[]`) and `not`,
    and `not[labels]` as part of `not`.
  - `create#create-a-commit` has the body attribute `actions` and no `actions[].action` to compare;
    `ai-coding#update-approval-configuration-for-a-project` has `approvals_before_merge`.
  - `create#add-changelog-data-to-file` has the body attributes `version` and `from` (footnoted `[^…]`), and
    `create#set-commit-pipeline-status` has `name` and `context` and no attribute `name or context`.
  - `plan#upload-a-file-to-a-group` reads its `form` row `file` as `body`.
  - `record_problems` returns nothing for a record built as:
    - `create#health` (`GET /projects/:id/repository/health`, the QUERY `Param` `generate`), though its table has no
      `id` row;
    - `growth#force-a-variant-assignment`, `BodyFormat.FORM`, with the BODY `Param`s `variant`, `context[user]`,
      `context[namespace]` and `context[project]`;
    - `fulfillment#delete-an-ldap-group-link-deprecated` on `DELETE /groups/:id/ldap_group_links/:cn`, with no
      `Param`, though its table has the `path` row `provider`;
    - `package#retrieve-a-recipe-snapshot` on its `GET /projects/:id/…` endpoint, with no `Param`, though its table
      has the `path` row `package_name`.
  - `gitlab-dedicated#list-all-system-hooks` has the offering `GitLab Self-Managed` from its page line.
    `tenant-scale#transfer-a-project-to-a-group` has `GitLab Self-Managed, GitLab Dedicated` from its own line.
  - Every row of `operations-index.md` names, by its Reference, a section whose endpoints hold the row's method and
    path.

**AC-3.2's tests.**

- **`test_an_unreachable_call_matches_its_reference_section`** uses `gitlab-dedicated#update-a-geo-site`
  (`PUT /geo_sites/:id`), which is unreachable by the Offering arm. Its steps:
  1. Build the record as a slice writes it (`rest/gitlab-dedicated.md` "Update a Geo site"):
     path `/geo_sites/:id`, and every body row of its table as a `SCALAR` `Param`, but the `array` rows
     `selective_sync_shards` and `selective_sync_namespace_ids` as `ARRAY`.
  2. Assert that `record_problems` returns nothing.
  3. Add the record to `gitlab_api.families.gitlab_dedicated.OPERATIONS` with `monkeypatch.setattr`, for this test
     only.
  4. Run `call gitlab-dedicated#update-a-geo-site --path id=7` with a typed value for every attribute
     (`-F enabled=true`, `-F files_max_capacity=10`, `-F 'selective_sync_shards=["default"]'`, `-f name=site2`, …)
     through the product's `main`, against the fake host.
  5. Assert that `call_problems` returns nothing, that the sent JSON body equals the typed values, and that the exit
     code is 0.
- **`test_the_method_rejects_a_call_that_differs`** is parametrized, with five cases on that section and one on
  another:
  - a sent shape with the method `PATCH`;
  - a sent shape with the path `/geo_site/7`;
  - a sent body member `site_name` in place of `name`;
  - `name` sent in the query rather than the body;
  - the record with `name` declared `Location.QUERY`, which `record_problems` checks;
  - a record built as a slice writes `software-supply-chain-security#create-an-application` (`POST /applications`:
    the BODY `Param`s `name`, `redirect_uri`, `scopes`, `confidential` and the `ARRAY_OF_HASHES` `granular_scopes`),
    plus the BODY `Param` `granular_scopes[].access`; its one problem, from `record_problems`, names
    `granular_scopes[].access`.

  Each case returns a problem that names the method, the path or the attribute.

### D6 — Target revision, regeneration and the coverage rule (AC-5, AC-6)

**Target.** The slices target `docs/api-reference/gitlab/` as generated from `gitlab-org/gitlab@a186442, 2026-11-07`,
the pin that the banner of `operations-index.md` carries. The full commit is
`a186442025b6dce8288ae4556470a5ab3c6201aa` (`docs/api-reference/gitlab/README.md` "Sources").

**The coverage rule** (Requirement 6) is one rule, with no exclusion (DL-001).

- **REST.** Every index row is mapped by a record or pending in its key's family. That covers the
  `/<route-prefix>/...` rows, which `families/package.py` already holds as pending. `coverage_gaps` is unchanged.
- **GraphQL.** Every first cell of the table under `### Only in GraphQL` in `graphql/conventions.md` is either served
  by a `graphql_only` record's `capability` or held in `graphql_only.PENDING_CAPABILITIES`, experimental or not.
  - This change puts every first cell on `PENDING_CAPABILITIES`, verbatim.
  - `graphql_only.py`'s docstring states the rule and says that a record of a `Status: Experiment` query or mutation
    says so in its comment.

**Additions to `test/test_gitlab_wrapper_coverage.py`** (V):

- **`family_problems(*, rows, families)`** names, per family module:
  - a `PENDING` key that no row carries, or whose family (`key_families`) is another module;
  - a record whose operation ID is the Reference of no row;
  - a record whose `(method, path)` is on none of the rows carrying its Reference. A Reference can carry several keys.
- **`only_in_graphql(*, path)`** reads the first cells of the table under the `### Only in GraphQL` heading, up to
  the table's end.
- **`capability_problems(*, capabilities, module)`** names each capability that is neither served nor pending, and
  each `PENDING_CAPABILITIES` entry or record `capability` that the table lacks.

**How a regeneration reaches the tests.** V and N read the reference when they run, so a commit that reruns
`scripts/api_reference/build.py` meets them in CI's `tests` leg.

| In the regenerated reference | Fails, naming the key or ID | What brings the modules back in line |
|---|---|---|
| a key added (a changed method or path is a removal plus an addition) | V `test_every_index_row_is_mapped_or_pending`; the gap report names the family module, a new one included | the key added to its family's `PENDING`; for a new stem, a new module with `FAMILY`, an empty `OPERATIONS` and its `PENDING` |
| a pending key removed, or moved to another family | V `test_every_declared_key_is_in_its_family` | the key removed from `PENDING` (and listed by its new family) |
| a record's row given another method or path, or removed; its anchor renamed | V `test_every_declared_key_is_in_its_family`, naming the ID and its rows' keys | the record's `method`, `path` or `operation_id`. Deleting or renaming a record that a compatibility command sends is a design change for its own issue. |
| an attribute of a record's operation added, removed, renamed or moved | N `test_every_record_matches_its_reference_section`, naming the record and the attribute; also N `test_every_record_is_sent_as_its_section_documents` when the record lacks it | the record's `params` |
| an "Only in GraphQL" row added, renamed or removed | V `test_every_graphql_only_capability_is_served_or_pending` | `PENDING_CAPABILITIES`, or a record's `capability` |
| an attribute of a pending operation changed | nothing | nothing to do |

- **Which change fixes it.** A regeneration is its own change. It reruns `build.py` and `verify.py`, and in the same
  change it fixes every module that the failures name. A slice never regenerates. A slice that lands after a
  regeneration covers the regenerated reference.
- **AC-5.3's test.** `test_a_regenerated_index_names_each_changed_key` feeds `coverage_gaps` and `family_problems` a
  synthetic index and families package (`SyntheticFamily`, `write_package`).

### D7 — The usage docstring and the map (AC-4)

**The usage docstring.** These lines go into the usage list of `src/payload/scripts/gitlab_wrapper.py`, after
`check-landed`:

```
    python scripts/gitlab_wrapper.py call plan#retrieve-a-project-issue --path issue_iid=5   # any record, by its id
        # --path NAME=VALUE (id defaults to project_id on a /projects/:id path); --query NAME=VALUE (a query
        # attribute as text; repeat it for each item of an array); -f/--raw-field NAME=TEXT (an attribute, a string);
        # -F/--field NAME=JSON (an attribute: a number, boolean, array, object or quoted string); --file NAME=PATH
        # (a file attribute, sent multipart). A GraphQL record takes its variables with -f and -F.
        # A list prints as one JSON array of every page's items, a JSON response as indented JSON, an empty body as
        # nothing, any other body as its bytes unchanged. An unknown operation, an undocumented parameter, a missing
        # path parameter, a value of the wrong shape, and ai-coding#merge-a-merge-request and plan#create-an-issue
        # (use mr merge and issue create) are refused before any request: exit 2.
```

- The "Exit codes" paragraph's "2 a usage error" becomes "2 a usage error or a refused `call`".
- The last paragraph's "the subcommands in gitlab_api/commands/" gains "(`commands/call.py` calls any record by its
  id)".

**The map.** The `src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md` gains, before its closing
sentence: "The product wrapper calls any declared record by its operation ID: `python scripts/gitlab_wrapper.py call
plan#retrieve-a-project-issue --path issue_iid=5` (`--path`, `--query`, `-f/--raw-field`, `-F/--field`, `--file`; a
GraphQL record's variables with `-f`/`-F`; a refusal exits 2). `test/test_gitlab_wrapper_contract.py` checks each
record against its `rest/<stage>.md` section." The closing sentence stays last.

**`commands/call.py`.** Its module docstring states D2's grammar and D3's print forms. No file of the package contains
the text `os.environ` or `getenv` (UB-2.2's scan reads docstrings too).

### D8 — Files: this change's, and a slice's (AC-1.1)

**This change:**

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_api/commands/call.py` | new: `register`, `call_operation`, `GATED_OPERATIONS`, the argparse type functions (`assignment`, `json_member`, `file_member`), `call_values` and D4's `check_parameters` |
| `src/payload/scripts/gitlab_api/commands/_common.py` | adds `EXIT_REFUSED` and `print_bytes(*, data)`, keyword-only as `print_json` is; its module docstring names both output forms and `EXIT_REFUSED` |
| `src/payload/scripts/gitlab_api/registry.py` | adds `GraphQLOperation.capability`, `attribute_name`, `variables` and `send`; `call` reaches a REST record through `send` |
| `src/payload/scripts/gitlab_api/transport.py` | adds `Response.is_json`, which `Response.value` reads |
| `src/payload/scripts/gitlab_api/graphql_only.py` | adds `PENDING_CAPABILITIES` and the docstring of D6 |
| `src/payload/scripts/gitlab_wrapper.py` | the module docstring only (D7) |
| `src/payload/test/gitlab_wrapper_fixtures.py` | adds `FakeGitLab.script_next(*, status=200, headers=(), body=None)`, a response served to the next request that matches no scripted method and URL (recorded as usual); `load_wrapper(*, module_name)`, `write_config(*, root, config)` and `run_main(*, wrapper, argv)` (the return value or the `SystemExit` code), for K and N; C keeps its own `load_wrapper`, `write_json` and `main_exit_code` unedited (UB-1.1) |
| `src/payload/test/test_gitlab_api_call.py` | new (K) |
| `src/payload/test/test_gitlab_api_registry.py` | adds `test_send_returns_the_response_of_the_record`, `test_attribute_name_drops_one_trailing_bracket_pair` and `test_variables_are_the_documents_definitions` |
| `src/payload/test/test_gitlab_api_transport.py` | adds `test_is_json_reads_the_content_type` |
| `src/payload/test/test_gitlab_wrapper_compat.py` | adds `test_the_usage_names_the_operation_call` |
| `test/test_gitlab_api_call_properties.py` | new: AC-1.3's property (H) |
| `test/test_gitlab_wrapper_contract.py` | new (D5, N) |
| `test/test_gitlab_wrapper_coverage.py` | D6's functions and tests |
| `docs/forLLMConsumption.md` | the `gitlab_api/` bullet (D7) |
| `gitlab_api/families/<family>.py` | a part-1 record that N finds differing from its section, corrected |

**A slice** (#35–#40, #42–#44). This table replaces #13 D2's "What a family's change edits" for these slices:

| File | Edited when |
|---|---|
| `gitlab_api/families/<family>.py` | always: each record added to `OPERATIONS` and its key removed from `PENDING`. Each `Param` is named, and a row that is part of another is carried, as D5 reads the table. |
| `gitlab_api/graphql_only.py` | for a capability: its records (ID `graphql#<field>`, the field as the table or the reference names it, such as `graphql#workItemCreate` or `graphql#Project.branchRules`; `capability` = the row's first cell). The capability leaves `PENDING_CAPABILITIES` with its first record. |
| `src/payload/test/test_gitlab_api_<family>.py` | new, when the family has a paged record: one example per paged record through `call`, with two pages and stdout as one JSON array of both. Every other REST record is proven by D5's two tests alone. |
| `src/payload/test/test_gitlab_api_graphql_only.py` | for a capability (new with the first): one example per record through `call`, judged by the fake host's `GRAPHQL_URL` request |
| never | `gitlab_wrapper.py`, `commands/*` (but `GATED_OPERATIONS`), `families/__init__.py`, `gitlab_wrapper_fixtures.py`, `test_gitlab_wrapper_coverage.py`, and `test_gitlab_wrapper_contract.py` outside the exceptions |
| the exceptions, each named by its slice | `transport.py`, `registry.py` and N's path reading (`record_problems`' path-row rule, `sent_call`, `call_problems`) for a request form that part 1 does not build (requirements Residuals); `commands/call.py` `GATED_OPERATIONS` or the hook gates for a record that commits to or merges into a branch, or creates an issue (Residuals) |

### Differences from #28

| Point | GitLab (this change) | #28 | Reason |
|---|---|---|---|
| Operation ID | `<stem>#<anchor>`, the section's heading anchor; `graphql#<field>` | GitHub `operationId`, the section's operationId line | the GitLab index and sections have no operation IDs (#13 D5) |
| Path values | `:name`, each one segment; `id` defaults to `project_id` on `/projects/:id` paths | `{name}`, `multi_segment`; `owner`/`repo` default to `origin` | AC-1.8; the project comes from `config/gitlab.json` |
| Attributes | each `Param` has a location and a `Kind`. `-f`/`-F` give either location; `--query` names the query; arrays and hashes typed with `-F`; `[]` through `attribute_name` | name sets; `-f`/`-F` are body members; `--query` sends each value | GitLab tables give `In` and `Type`; `registry.encode` writes the brackets (#13 AC-2.3) |
| Bodies | JSON, form or multipart (`--file`) | JSON only | `BodyFormat`, `Kind.FILE` (#13 AC-2.3, AC-2.4) |
| Shape refusal | AC-2.4, by `registry.encode` | none | `KIND_ACCEPTS` |
| Paging | `OFFSET`, `KEYSET` through `Transport.pages` | `LINK` | #13 AC-2.5, AC-2.6 |
| Output test | `Content-Type` (`Response.is_json`) | the body | AC-1.5, AC-1.6; `conventions.md` "Responses" |
| GraphQL | `graphql_only` records through `call`; `-f`/`-F` as variables | not in #28 | AC-1.9 |
| Gated IDs | `ai-coding#merge-a-merge-request` → `mr merge`; `plan#create-an-issue` → `issue create` | `pulls/merge`, `issues/create` | the GitLab spellings the hook gates match |
| Config refusal | exit 1 | exit 2 | #13 D7 |
| Unreachable rule | `/admin/`, `/geo/`, `/hooks/`, or no GitLab.com offering | `{enterprise}`/`{org}`; `apps`, `billing`, `teams` | the glossary's classes, as the reference marks them |
| Coverage | keys, plus D6's family and capability checks | IDs and capabilities | #13 D8 counts keys; AC-5.3 and AC-6.2 add the rest |

### Sources

- `docs/api-reference/gitlab/conventions.md`: "Hosts and base URLs", "How the docs mark tier, offering and status",
  "Request encoding" ("URL-encoding path parameters", "Arrays, hashes and arrays of hashes"), "Responses",
  "Pagination" ("Offset-based", "Keyset-based"), "Uploads and binary request bodies", "Downloads and redirects".
- `docs/api-reference/gitlab/graphql/conventions.md`: "Connections and cursor pagination", "Only in GraphQL".
- `docs/api-reference/gitlab/README.md`: "Sources". `docs/api-reference/README.md`: "GitLab REST specifics".
- Python 3.9 [`argparse`](https://docs.python.org/3.9/library/argparse.html): `type`, `ArgumentParser.error`,
  `action='append'`, and a `dest` shared by two options.
- Python 3.9 [`json`](https://docs.python.org/3.9/library/json.html): `parse_constant` "will be called with one of the
  following strings: '-Infinity', 'Infinity', 'NaN'. This can be used to raise an exception if invalid JSON numbers
  are encountered".
- Python 3.9 [`sys.stdout`](https://docs.python.org/3.9/library/sys.html#sys.stdout): "to write bytes to `stdout`, use
  `sys.stdout.buffer.write(b'abc')`".
- Python 3.9 [`Message.get_content_type`](https://docs.python.org/3.9/library/email.compat32-message.html): "coerced
  to lower case of the form maintype/subtype"; with no Content-Type header, "the default type" (`text/plain`) "will be
  returned".
- [GraphQL, October 2021](https://spec.graphql.org/October2021/#sec-Language.Variables): `VariableDefinition :
  Variable : Type DefaultValue? Directives?`; "Variables must be defined at the top of an operation".
- [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html): `recursive`,
  `lists`, `dictionaries`.

## Testing Strategy

- **Fake host.** `src/payload/test/gitlab_wrapper_fixtures.py`, as #13's Testing Strategy describes it, plus D8's
  additions. The suites load it by path.
- **Property test.** AC-1.3's property is in H, `test/test_gitlab_api_call_properties.py`. It puts
  `src/payload/scripts` on `sys.path` and carries `@settings(deadline=None)`, as P does. A Hypothesis test lives in
  `test/` (#17 X1, #28 X3); the shipped suites stay pytest-only.
- **CLI tests, in K.**
  - Each test writes `config/gitlab.json` into `tmp_path` (`hostname` the fixture's `HOST`) and runs
    `main(argv=["call", …])` through D8's helpers.
  - Requests are judged by the fake host's records, and refusals by `caplog` (argparse's by `capsys`) plus "no request
    recorded". Non-JSON output is read with `capsysbinary`.
  - A synthetic record (a FORM body, a `FILE` attribute, `fixed` pairs, a KEYSET copy, a `/groups/:id` path,
    `GET /projects/:id`, `verify#download-job-artifacts-by-job-id`, the GraphQL records) is set into a family
    module's `OPERATIONS` or `graphql_only.OPERATIONS` with `monkeypatch.setattr`, for the test only.
- **Contract tests.** N, as in D5. **Coverage tests.** V, as in D6. Its existing tests are unchanged.
- **Regression.** C with no existing test edited, P `test_standard_library_only`, and
  `src/payload/test/test_wrapper_delivery.py`, unchanged.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project (requirements
  Residuals). Until it exists, `call` is exercised up to the API boundary through `main`'s argv by K and N; C
  `test_script_usage_error_exits_2` (unchanged) runs the script by path, so its parser holds `call.py`.

## Correctness Properties

Each entry gives the test kind and its oracle. The mapping's legend names the test files.

- **AC-1.1**
  - Inspection: D1 names both parts and what each serves; D8 names the files a slice edits.
  - Structural: N `test_every_record_is_sent_as_its_section_documents` calls every discovered REST record outside
    `GATED_OPERATIONS` through `call`.
  - Example, K `test_a_gated_operation_names_its_subcommand`. `call ai-coding#merge-a-merge-request --path
    merge_request_iid=1` and `call plan#create-an-issue -f title=T` each exit 2 with no request. The first log record
    names the ID and `mr merge`; the second names the ID and `issue create`.
- **AC-1.2** — Example table, K `test_an_operation_call_sends_its_record`:
  - `plan#retrieve-a-project-issue --path issue_iid=5` sends one `GET …/projects/<project_id>/issues/5`, with no body
    and no `Content-Type`.
  - `create#delete-repository-branch --path branch=feature/x` sends `DELETE …/repository/branches/feature%2Fx`.
  - `plan#update-an-issue --path issue_iid=5 -f title=T -F 'assignee_ids=[1, 2]'` sends a `PUT` with the JSON body
    `{"title": "T", "assignee_ids": [1, 2]}`.
  - `plan#list-all-project-issues --query state=opened --query assignee_username=a --query assignee_username=b
    --query iids[]=3` sends `state=opened&assignee_username[]=a&assignee_username[]=b&iids[]=3`, then the
    `per_page` that `Transport.pages` adds (`MAX_PER_PAGE`).
  - A synthetic FORM-body record sends `application/x-www-form-urlencoded` pairs.
  - A record with `fixed` pairs sends them after the attributes.
  - A config with `token_type` `bearer` sends `Authorization: Bearer` and neither `PRIVATE-TOKEN` nor `JOB-TOKEN`.

  Oracle: the recorded method, the URL as sent, the body and its `Content-Type`, and the credential headers. R
  `test_send_returns_the_response_of_the_record`: a `204`'s `Response` is returned; a GraphQL ID raises `ValueError`
  with no request.
- **AC-1.3**
  - Property, H `test_any_json_value_becomes_the_attribute_value`. For a name drawn from `[a-z_][a-z0-9_]*` and a
    value drawn from its `Kind`'s domain:
    - `json_member(text=f"{name}={json.dumps(obj=value)}") == (name, value)`;
    - `registry.encode` on a JSON record whose BODY `Param` of that `Kind` is given the value sends
      `json_body == {name: value}`.

    Hypothesis sketch:

    ```python
    scalars = st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text()
    json_values = st.recursive(
        base=st.none() | scalars,
        extend=lambda inner: st.lists(elements=inner) | st.dictionaries(keys=st.text(), values=inner),
    )
    kind_values = {
        "SCALAR": scalars,
        "ARRAY": st.lists(elements=json_values),
        "HASH": st.dictionaries(keys=st.text(), values=json_values),
        "ARRAY_OF_HASHES": st.lists(elements=st.dictionaries(keys=st.text(), values=json_values)),
    }
    ```
  - Example, K `test_an_attribute_carries_its_kind`, parametrized:
    - each `Kind` in a JSON body (native);
    - each `Kind` in a query and in a form body (`registry.encode`'s bracket pairs, read with `parse_qsl`);
    - a `--file` attribute beside two body attributes, sent as `multipart/form-data`. The file part's bytes equal the
      file's, and the other attributes are form fields.
  - Example, K `test_a_field_that_is_not_json_is_refused`: `call plan#update-an-issue --path issue_iid=5 -F
    title=NaN`, and the same with `title=Infinity` and `title=-Infinity`, each exit 2 with no request. Standard error
    holds argparse's usage message naming `-F/--field` and `"title"`, and not the text after the first `=` (D2).
  - Example, R `test_attribute_name_drops_one_trailing_bracket_pair`: `iids[]` is `iids`, `a[][]` is `a[]`, and
    `not[labels]` is unchanged.
- **AC-1.4** — Example, K `test_a_list_prints_every_page_as_one_array`:
  - `plan#list-all-project-labels` (OFFSET) over two pages, the second asked for by `x-next-page`;
  - a KEYSET copy of `plan#list-all-project-issues` over two pages, the second asked for at its `Link` `rel="next"` URL
    as given.

  Oracle: stdout equals `print_json` of every item in order, and every scripted response was served.
- **AC-1.5** — Example, K `test_a_json_or_empty_body_prints_as_documented`. A body sent as
  `application/json; charset=utf-8` prints `print_json` of it. `create#delete-repository-branch` answering `204`
  prints nothing. Both exit 0. T `test_is_json_reads_the_content_type`: true for `application/json; charset=utf-8`,
  false for `text/plain` and with no header.
- **AC-1.6** — Parametrized example, K `test_a_body_that_is_not_json_is_written_unchanged`:
  `verify#retrieve-a-log-file-for-a-job` answering `text/plain`; bytes that are not UTF-8 as
  `application/octet-stream`; JSON text with no `Content-Type`; a record built as
  `verify#download-job-artifacts-by-job-id` answering `302` to `https://storage.example.com/a.zip`, whose route serves
  zip bytes and receives no credential header. Oracle: the stdout bytes equal the body bytes; exit 0.
- **AC-1.7** — Example, K `test_an_api_error_exits_1_with_its_details`: a `404`; `429` answers with `Retry-After: 0`
  until the retries are spent (`GitLabRateLimitError`); a GraphQL `errors` answer at `200`; `--path id=..` on
  `plan#list-all-project-labels` (`registry.expand` inside step 5) and `--path issue_iid=..` on
  `plan#retrieve-a-project-issue` (step 6). Oracle: exit 1, stdout empty, and the log records hold the message and
  then any details (the two path errors carry none); for the two path cases, no request is recorded and the message
  names the path parameter.
- **AC-1.8** — Example, K `test_a_project_path_takes_the_configured_project`.
  - `plan#retrieve-a-project-issue --path issue_iid=5` sends to `/projects/<project_id>/…`.
  - With `--path id=group/project` added, it sends to `/projects/group%2Fproject/…`.
  - A synthetic `GET /projects/:id` record without `--path id` sends to `/projects/<project_id>`.
  - A synthetic `/groups/:id/labels` record without `--path id` is refused as in AC-2.3.
- **AC-1.9** — Example, K `test_a_graphql_record_sends_its_document`, on two synthetic `graphql_only` records:
  - Without a connection: `-f fullPath=g/p -F first=2` sends one `POST` to `GRAPHQL_URL`. Its JSON body is
    `{"query": <document>, "variables": {"fullPath": "g/p", "first": 2}}` and it carries `Authorization: Bearer`.
    Stdout is `print_json` of `data`.
  - With a connection over two pages: the second request's `after` is the first page's `endCursor`. Stdout is one
    array of both pages' nodes.

  Both exit 0.
- **AC-2.1** — Parametrized, K `test_an_unknown_operation_is_refused`. Two cases: `plan#create-an-upload` (only on
  `plan`'s `PENDING`) and `plan#no-such-operation`. Oracle: exit 2, no request, and a log record that names the ID.
- **AC-2.2** — Parametrized, K `test_an_undocumented_parameter_is_refused`. Six cases:
  - `plan#retrieve-a-project-issue --path issue_iid=5 --path number=5`
  - `plan#update-an-issue --path issue_iid=5 --query title=T` (a body attribute given as query)
  - `plan#update-an-issue --path issue_iid=5 -f colour=red`
  - all three names in one call, where one log record names `number`, `title` and `colour`, each with its option
  - a GraphQL record given `-f unknown=1 --query x=1`
  - a connection record given `-f after=c`

  Oracle: exit 2, no request, and a log record that names each parameter and the record's documented parameters. R
  `test_variables_are_the_documents_definitions`: `query Q($fullPath: ID!, $first : Int = 2) { project(fullPath:
  $fullPath) { id } }` gives `("fullPath", "first")`, and a connection record's `$after` is left out.
- **AC-2.3** — Example, K `test_a_missing_path_parameter_is_refused`: `call plan#retrieve-a-project-issue` names
  `issue_iid` and the path parameters `id` and `issue_iid`; the `/groups/:id/labels` record names `id`. Both exit 2
  with no request.
- **AC-2.4** — Parametrized, K `test_a_value_of_the_wrong_shape_is_refused`, on `plan#update-an-issue` and
  `plan#list-all-project-issues`: `-f assignee_ids=1` (a string for an ARRAY), `-F 'title={"a": 1}'` (an object for
  a SCALAR), `--file title=<file>` (a path for a SCALAR), `--query not=x` (a string for a HASH). Oracle: exit 2, no
  request, and a log record that names the attribute and its `Kind`.
- **AC-3.1**
  - Inspection: D5's rule and method.
  - Example, N `test_the_unreachable_rule_has_two_arms`. `is_unreachable` is false for `plan#retrieve-a-project-issue`
    and true for:
    - `gitlab-dedicated#update-a-geo-site` (the Offering arm, from its page line);
    - `tenant-scale#transfer-a-project-to-a-group` (the Offering arm, from its own line under a page that names
      GitLab.com);
    - `openapi-only#restart-a-batched-background-operation` (`/admin/`),
      `openapi-only#determine-if-a-geo-site-should-proxy-requests` (`/geo/`) and `openapi-only#update-a-custom-header`
      (`/hooks/`), by the path arm only.
- **AC-3.2** — Examples:
  - N `test_an_unreachable_call_matches_its_reference_section` passes.
  - Every case of `test_the_method_rejects_a_call_that_differs` names its difference.
  - N `test_a_section_is_read_as_the_reference_writes_it` pins the reader and the records `record_problems` passes.
- **AC-4.1** — Static, C `test_the_usage_names_the_operation_call`. The entry script's `__doc__` holds
  `call plan#retrieve-a-project-issue`, `--path`, `--query`, `-f/--raw-field`, `-F/--field`, `--file`, `variables`,
  `JSON array`, `indented JSON`, `empty body`, `bytes unchanged` and `exit 2`.
- **AC-4.2**
  - Inspection of the map bullet (D7).
  - `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes.
- **AC-5.1** — Inspection: D6 names the pin.
- **AC-5.2** — Inspection: D6's table and its "Which change fixes it" item.
- **AC-5.3** — Parametrized example, V `test_a_regenerated_index_names_each_changed_key`, on a synthetic index and
  package. Five cases:
  - an added key is returned by `coverage_gaps`;
  - a pending key that the index lacks is named by `family_problems`;
  - a record whose Reference no row carries (its row removed) is named by `family_problems`, by its ID;
  - a record whose Reference's row has another path is named by `family_problems`;
  - a record whose Reference's row has another method and the same path is named by `family_problems`.
- **AC-6.1** — Example, V `test_a_route_prefix_key_is_held_to_the_rule`. The synthetic `gamma` without `RELEASE_FILE`
  on its `PENDING` makes `coverage_gaps` return that row.
- **AC-6.2** — Examples:
  - V `test_a_capability_neither_served_nor_pending_is_named`, on a synthetic capability list and module. It covers a
    served capability, a pending one, an unlisted one, and a pending entry that the table lacks.
  - V `test_the_only_in_graphql_table_is_read_whole`: the first cell `Work items` and the last cell
    `Query cost introspection` are read, and nothing of the header or of "Only in REST".
- **AC-6.3** — On the merged tree, V `test_every_graphql_only_capability_is_served_or_pending`,
  `test_every_index_row_is_mapped_or_pending` and `test_every_declared_key_is_in_its_family` pass.
- **UB-1.1** — C passes with every existing case and assertion unedited; the PR diff changes no existing line of C;
  `call` is a new top-level subcommand that no UB-1 argv uses.
- **UB-2.1** — C `test_load_config_refusals` and `test_environment_token_ignored` pass, unchanged; K
  `test_call_takes_no_token_option`: no option string of the `call` subparser contains `token`.
- **UB-2.2** — P `test_standard_library_only`, unchanged, scans every module under the package, `commands/call.py`
  included.
- **UB-3.1** — `src/payload/test/test_wrapper_delivery.py` passes in CI's `tests` leg, and the PR diff names no file
  of UB-3.1.

## Security Considerations

- **Credential.** The source is unchanged: `_load_config` reads `config/gitlab.json` only (UB-2.1), and `call` adds no
  token option. The token travels in the one configured header to the configured origin only (`Transport._send`); a
  cross-origin redirect drops it (`CredentialStrippingRedirectHandler`, #13 AC-3.1); a job token never reaches GraphQL
  (`Transport.graphql`).
- **Command-line input.** Path values are one percent-encoded segment each, and `registry.expand` refuses an empty,
  `.` or `..` value. The URL is `https://<hostname>/api/v4` plus a record's root-relative path, so no value changes
  the host. Query and form values are encoded by `join_pairs`, a JSON body by `json.dumps`, multipart names by
  `multipart_name`. An exit-2 refusal holds names only, escaped (D4).
- **Files.** `--file` sends whatever file the caller names, as that attribute's part, to the configured origin only.
- **Response bytes.** A non-JSON body reaches stdout unchanged (AC-1.6), including any terminal-escape bytes it holds.
  Error details go to standard error through `logging`.
- **Gates.** The `merge-steward` gate (`gate_merge_steward.script_call`) refuses the wrapper's `mr merge` by its
  words, and its `API_MERGE_RE` judges only a `curl`, `wget` or `Invoke-RestMethod` command; the `issue-filing-gate`
  (`gate_filing.CREATE_RE`) judges `issue create`. Neither sees `call ai-coding#merge-a-merge-request` or
  `call plan#create-an-issue`, so `call` refuses both IDs (`GATED_OPERATIONS`, D4) and reaches no endpoint that a
  gate refuses under its compatibility spelling. The hooks are unchanged.
- **Destructive operations.** `call` sends whatever a declared record allows, without asking for confirmation; whether
  to run one is the caller's decision under `continuous-work.md` Exception 1. No permission prompt comes first:
  `prompts/setup-claude.txt` allow-lists `python scripts/gitlab_wrapper.py` as a whole. A `/projects/:id` record acts
  on the configured project when `id` is not given (AC-1.8).
- **Dependencies.** The shipped code gains no dependency and no subprocess. H's Hypothesis is already in the `dev`
  extra.

## Operability

Not applicable: nothing deploys.

## Acceptance Criteria Mapping

Test files:

- K = `src/payload/test/test_gitlab_api_call.py`
- R = `src/payload/test/test_gitlab_api_registry.py`
- T = `src/payload/test/test_gitlab_api_transport.py`
- H = `test/test_gitlab_api_call_properties.py`
- N = `test/test_gitlab_wrapper_contract.py`
- V = `test/test_gitlab_wrapper_coverage.py`
- C = `src/payload/test/test_gitlab_wrapper_compat.py`
- P = `test/test_gitlab_api_properties.py`

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1, D8; `commands/call.py`, `GATED_OPERATIONS` | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` |
| AC-1.2 | `call_operation`, `registry.send`, `Transport.request` | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record` |
| AC-1.3 | `json_member`, `call_values`, `registry.attribute_name`, `registry.encode` | H `test_any_json_value_becomes_the_attribute_value`; K `test_an_attribute_carries_its_kind`, `test_a_field_that_is_not_json_is_refused`; R `test_attribute_name_drops_one_trailing_bracket_pair` |
| AC-1.4 | `call_operation` → `registry.pages`, `print_json` | K `test_a_list_prints_every_page_as_one_array` |
| AC-1.5 | `call_operation`, `Response.is_json`, `print_json` | K `test_a_json_or_empty_body_prints_as_documented`; T `test_is_json_reads_the_content_type` |
| AC-1.6 | `call_operation`, `_common.print_bytes` | K `test_a_body_that_is_not_json_is_written_unchanged` |
| AC-1.7 | `main`, `_report` (unchanged); `registry.expand` | K `test_an_api_error_exits_1_with_its_details` |
| AC-1.8 | `call_values`, `_common.PATH_PROJECT` | K `test_a_project_path_takes_the_configured_project` |
| AC-1.9 | `call_operation` → `registry.call`, `Transport.graphql`, `graphql_nodes` | K `test_a_graphql_record_sends_its_document` |
| AC-2.1 | `call_operation` (D4), `registry.lookup` | K `test_an_unknown_operation_is_refused` |
| AC-2.2 | `check_parameters`, `registry.variables` | K `test_an_undocumented_parameter_is_refused`; R `test_variables_are_the_documents_definitions` |
| AC-2.3 | `check_parameters`, `registry.placeholders` | K `test_a_missing_path_parameter_is_refused` |
| AC-2.4 | `call_operation` → `registry.encode` (`KIND_ACCEPTS`) | K `test_a_value_of_the_wrong_shape_is_refused` |
| AC-3.1 | D5; `is_unreachable` | design review; N `test_the_unreachable_rule_has_two_arms` |
| AC-3.2 | `reference_sections`, `record_problems`, `sent_call`, `call_problems` | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` |
| AC-4.1 | entry script docstring (D7) | C `test_the_usage_names_the_operation_call` |
| AC-4.2 | `docs/forLLMConsumption.md` (D7) | design review; `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` |
| AC-5.1 | D6 | design review |
| AC-5.2 | D6 | design review |
| AC-5.3 | `coverage_gaps`, `family_problems` | V `test_a_regenerated_index_names_each_changed_key`, `test_every_declared_key_is_in_its_family` |
| AC-6.1 | `coverage_gaps` (unchanged) | V `test_a_route_prefix_key_is_held_to_the_rule`, `test_every_index_row_is_mapped_or_pending` |
| AC-6.2 | `only_in_graphql`, `capability_problems`, `GraphQLOperation.capability` | V `test_a_capability_neither_served_nor_pending_is_named`, `test_the_only_in_graphql_table_is_read_whole` |
| AC-6.3 | `graphql_only.PENDING_CAPABILITIES`, the family modules | V `test_every_graphql_only_capability_is_served_or_pending`, `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` |
| UB-1.1 | `commands/*`, `build_parser`, `_run`, `main` (all unchanged) | C, every existing test; PR diff |
| UB-2.1 | `_load_config`; `call`'s options | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option` |
| UB-2.2 | `commands/call.py`, `registry.py`, `transport.py`, `_common.py`, `graphql_only.py` | P `test_standard_library_only` |
| UB-3.1 | none (the files are untouched) | `src/payload/test/test_wrapper_delivery.py`; PR diff |

## Residuals

- **Several keys under one Reference** (`create#generate-changelog-data`, `software-supply-chain-security`,
  `plan#list-all-emoji-reactions-for-a-resource`) keep all but one key pending, as `registry.lookup` takes one record
  per ID; a slice whose issue asks for an empty `PENDING` records them as its residual.
- **A record that commits to or merges into a branch, or creates an issue,** is gated by its slice (D8 exceptions).
- **D5 compares names and `In` only;** `Kind`, `required`, `paging` and `fixed` rest on a slice's examples and review.
- **Secrets in arguments:** a text value shows in the command line, and `--file` sends `config/gitlab.json` or a
  `credentials/` file like any path; guarding them is outside this change (`issue-filing-discipline.md`).
- **`HEAD` records** print nothing (AC-1.5); printing response headers is outside this ask.
- **The test instance** is #11's: its fixture settles which reachable operations rest on D5 alone, and a self-managed
  instance makes #11 restate D5's two arms.
