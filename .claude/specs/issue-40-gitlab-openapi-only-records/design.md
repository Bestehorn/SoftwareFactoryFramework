# Design — issue #40: GitLab wrapper rewrite, part 2 slice: the OpenAPI-only operations

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-3.4, UB-1..UB-4, frozen). Builds on
`.claude/specs/issue-13-gitlab-wrapper-foundation/design.md` ("#13 Dn") and
`.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"). #41 D8 names what a slice edits; D2,
D3 and D5 name where this slice edits past it, and why. The test files are named in the mapping's legend.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #40, "GitLab wrapper rewrite, part 2 slice:
   the OpenAPI-only operations", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Overview

`gitlab_api/registry.py` learns the three path forms of the pending paths: the `*name` glob, the optional `(…)` group
and the escaped parenthesis (D1). `commands/call.py` lets a call leave an optional group's parameter out (D2). The
contract test N reads a glob row as its path parameter and writes the forms when it compares a sent path (D3). With
those in place, `families/openapi_only.py` and `families/deploy.py` get one record per pending key, transcribed by D4's
rules, and both `PENDING` sets are empty. Four uploads send the raw body `call --input` gives (D5). D6 names the
tests, D7 the files.

## Design

### D1 — The path forms in `registry` (AC-2.1 to AC-2.5; reusable by #43)

**Representation.** A record's `path` stays its index row's text, verbatim (#13 D5). No record field is added for the
forms: they are read from the path by three patterns.

```python
# A path parameter: `:name`, sent as ONE segment, at a segment start (`/projects/:id`) or inside one
# (`binary-:architecture`); or `*name`, a glob whose value keeps its `/` (`/packages/npm/*package_name`).
PLACEHOLDER = re.compile(pattern=r"(?P<sigil>[:*])(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_SIGIL = "sigil"
GLOB_SIGIL = "*"
GLOB_SEPARATOR = "/"
# An optional group: an unescaped `(`, text with no parenthesis, an unescaped `)` — `(*path/)`.
OPTIONAL_GROUP = re.compile(pattern=r"(?<!\\)\((?P<inner>[^()]*)(?<!\\)\)")
GROUP_INNER = "inner"
# A parenthesis the path writes escaped, `\(` or `\)` (`Packages\(\)`), sent without its backslash.
ESCAPED_PARENTHESIS = re.compile(pattern=r"\\(?P<parenthesis>[()])")
GROUP_PARENTHESIS = "parenthesis"
```

`(?<!\\)` is a negative lookbehind: it matches where the position "is not preceded by a match for" the backslash
(Python docs, `re`). So `\(` never opens a group.

**The functions.**

- **`placeholders(*, path)`.** Its body is unchanged. With the new `PLACEHOLDER` it names every `:name` and `*name`,
  without the sigil, in path order, inside an optional group or not. Every reader of it therefore treats a glob or
  group parameter as a path parameter:
  - `call`'s documented `--path` names and its refusal message (`documented_names`, `documented_text`; AC-2.4);
  - `encode`'s skip of path names (`_declared_values`);
  - N's path-row rule and N's `record_call` (D3).
- **`required_placeholders(*, path) -> Tuple[str, ...]`** (new). It is `placeholders` of the path with every
  `OPTIONAL_GROUP` removed: the parameters a call must give.
- **`_glob(*, name, values) -> str`** (new). It writes the value of `*name` with each `/` kept:
  - `str(value)` is split at `/`;
  - each part is checked against `REFUSED_SEGMENTS` and written with `quote(string=part, safe="")`, as `_segment`
    writes one segment;
  - the parts are joined with `/`.

  A part in `REFUSED_SEGMENTS` raises `GitLabAPIError` naming `*name`, the value and the part. No value raises
  `ValueError`, as `_segment` does. `_segment` itself is unchanged.
- **`expand(*, operation, values)`** writes the path in three steps:
  1. Each `OPTIONAL_GROUP` is written as its `inner` when every name `placeholders` finds in `inner` has a value other
     than `None`. Otherwise it is written as nothing.
  2. Each `ESCAPED_PARENTHESIS` is written as its parenthesis.
  3. Each `PLACEHOLDER` is written by `_segment` (sigil `:`) or by `_glob` (sigil `*`).

  Steps 1 and 2 read the template's text alone; of a value, step 1 reads only whether it is given. Step 3 writes the
  values, each segment or part encoded by `quote(safe="")`, which leaves no character but letters, digits and `_.-~`
  unencoded (Python docs, `urllib.parse.quote`). So no value is read as a group, an escape or a parameter, and no
  value adds a parenthesis or a backslash to the path. A path with only `:name` parameters and no parenthesis passes
  steps 1 and 2 unchanged and step 3 as before (UB-4).

**Examples** (AC-2.1, AC-2.3, AC-2.5):

| Path | Values | Written |
|---|---|---|
| `/projects/:id/packages/maven/*path/:file_name/authorize` | `id=1`, `path=a/rc 1`, `file_name=x.jar` | `/projects/1/packages/maven/a/rc%201/x.jar/authorize` |
| `…/generic/:package_name/*package_version/(*path/):file_name` | `package_name=pkg`, `package_version=1.0`, `path=a/b`, `file_name=file.txt` | `…/generic/pkg/1.0/a/b/file.txt` |
| the same | the same without `path` | `…/generic/pkg/1.0/file.txt` |
| `…/v2/Packages\(Id='*package_name',Version='*package_version'\)` | `package_name=N`, `package_version=1.0` | `…/v2/Packages(Id='N',Version='1.0')` |
| `…/v2/Packages\(\)` | none | `…/v2/Packages()` |

- An empty string given for a group's parameter is a value. Step 3 refuses it as an empty part (AC-2.2), so a group is
  either written whole or left out, and never leaves `//` behind.
- `send` and `pages` call `expand` as before. Nothing else in the module changes for the forms but three docstrings:
  the module's `expand` bullet, `placeholders`', and `expand`'s, which states the three steps and that a group whose
  parameter has no value is left out.
- **Reuse.** The glob keys still pending in `package`, `verify` and `orbit` (`*distribution`, `*artifact_path`,
  `*path`, `*id`) are written by the same three steps with no further edit. The `/<route-prefix>/` and
  `http(s)://${CI_REGISTRY}` forms stay #43's (Residuals).

### D2 — `call` and an optional path parameter (AC-2.3, AC-2.4; DL-004)

**The edit.** In `commands/call.py`, `missing_path_parameters` reads
`registry.required_placeholders(path=operation.path)` in place of `registry.placeholders(path=operation.path)`.
Nothing else in `call`'s code changes for the group (D5 adds `--input`). `documented_names`, `documented_text`,
`path_values` with its `id` default, and `GATED_OPERATIONS` keep reading what they read.

| The call | What `call` does | Decided by |
|---|---|---|
| gives a glob or a group's parameter with `--path` | accepts it as documented; D1 writes it | `documented_names` → `registry.placeholders` |
| leaves a glob outside a group out | exit 2, naming it (AC-2.4, as #41 AC-2.3) | `missing_path_parameters` → `registry.required_placeholders` |
| leaves a group's parameter out | accepts the call; D1 leaves the group out (AC-2.3) | the same |

With D1 alone, the last row would be refused as a missing path parameter.

**Why #41 D8's "never" row yields.**

- The "never" row keeps `commands/*` out of a slice, `GATED_OPERATIONS` excepted. Its exceptions row lets a slice edit
  `registry.py`, `transport.py` and N's path reading for a request form part 1 does not build.
- The optional group is such a form. One of its rules does not live in `registry`: which path parameters a call must
  give. That is #41 D4's "a path parameter with no value" refusal, which `call.py` computes from
  `registry.placeholders`.
- `placeholders` cannot leave the group's parameter out. The same set is what `--path` may name (AC-2.4) and what
  `encode` skips. So "must give" needs a second function, and its one reader in `call.py` changes.
- The exception therefore reaches that one call site and the docstring sentences that state the rule. No other line of
  `commands/*` changes for it, and #41's refusals stay as they are (UB-4).

**The docstrings.**

- The module docstring's `--path` bullet becomes: "a path parameter, as text: a `:name` written by `registry.expand` as
  ONE percent-encoded segment, a `*name` with each `/` kept and each part between them one such segment; the parameter
  of an optional `(…)` group may be left out, and the group is then not sent."
- Its refusal paragraph's "a path parameter left without a value" becomes "a path parameter outside an optional group
  left without a value".
- Its `GitLabAPIError` list's "an empty, `.` or `..` path value" gains "or glob part".
- `missing_path_parameters`' docstring states the same rule.

### D3 — N's path reading (AC-1.4, AC-3.3)

**The path-row rule needs no edit.** `endpoint_problems` names an `In` `path` row that is a placeholder of none of the
section's endpoints. It reads `registry.placeholders`, which D1 extends. So `rest/deploy.md`'s `path` row, `In`
`path` and the parameter of `(*path/)`, is a placeholder of its endpoint.

**Three other readings** of `test/test_gitlab_wrapper_contract.py` assume `:name` only. Each would fail a record of
this change for a difference the reference does not have. Each gets the smallest edit that removes the false
difference. The first two are `call_problems`' path reading, #41 D8's exception. The third reaches past it, into
`record_problems`' rule for a row the record lacks: AC-1.4 reads a `query`, `body` or `form` row as a path parameter,
and the path-row rule never sees such a row. `test_a_path_form_is_read_and_sent_as_written` pins all three.

| Reading | What fails without the edit | The edit |
|---|---|---|
| `PATH_PLACEHOLDER`, which `expanded_path` and `call_problems`' path names read | a glob given as a path value whose row is `In` `query` or `body` (the NPM routes' `package_name`) is "given but not sent in the query" | the pattern takes the sigil `[:*]` in a `sigil` group, as `registry.PLACEHOLDER` does |
| `expanded_path`, which `route_problems` reads | the section's path keeps `*name`, `(`, `)` and `\(`, so no sent path equals it | after its value check, the section's path drops each unescaped `(` and `)`, then the backslash of each `\(` and `\)`, then has each `:name` and `*name` replaced by its value |
| `record_problems`' rule for a row the record lacks | a `query`, `body` or `form` row naming a `*name` of the record's path is "not declared by the record", though AC-1.4 makes it no `Param` | the rule skips a row whose name is in `glob_names(*, path=record.path)`: the names that N's `PATH_PLACEHOLDER` matches with the sigil `*` |

- **`expanded_path` writes every group.** N gives every path parameter a value, because `record_call` reads
  `registry.placeholders`. N restates the forms with its own patterns and never calls `registry.expand`, so the
  oracle does not share the code it judges. The test values are alphanumeric, so the written path needs no encoding
  (#41 D5).
- **The skip is limited to `*name`.** In this change every group parameter is a glob (`(*path/)`), so the skip covers
  both kinds that AC-1.4 names. A row naming a `:name` is held as before.
- **`sent_call` is unchanged.** `urlsplit` returns the path as sent: "% escapes are not expanded" (Python docs,
  `urllib.parse`).

### D4 — Transcription rules (AC-1.1 to AC-1.6, AC-3.2)

Each record of `families/openapi_only.py` is written from its index row and its `rest/openapi-only.md` section. Each
record of `families/deploy.py` is written from its row and its `rest/deploy.md` section.

| Field | Rule |
|---|---|
| `operation_id` | the row's Reference without `rest/` and `.md`, verbatim, a `-1` or `-2` suffix included: `openapi-only#npm-registry-metadata-endpoint-2`, `deploy#send-the-file` |
| `method`, `path` | the row's, verbatim: `*name`, `(…)`, `\(`, `\)`, `$`, `'`, `,` and `=` as the row writes them; a `\` is `\\` in the Python literal, as `PENDING` spells it |
| `params` | one `Param` per `query`, `body` or `form` row of the section, in table order. No `Param` for a row naming a `*name` of the record's path, inside an optional group or not (AC-1.4), nor for a `header` row (requirements Residuals), nor for a raw-body record's `file` row (AC-3.2). |
| `Param.name` | the backticked cell, verbatim (`$filter`, `terraform-get`, `ID`) |
| `Param.location` | `query` → `Location.QUERY`; `body` and `form` → `Location.BODY`; on a raw-body record, every `Param` → `Location.QUERY`, where it is sent (`Location`: "Where a declared attribute is sent"; AC-3.2) |
| `Param.kind` | `array of string` → `ARRAY`; `object` → `HASH`; `array of object` → `ARRAY_OF_HASHES`; `file` → `FILE`; every other Type (`string`, `string (date)`, `integer (int32)`, `boolean`) → `SCALAR`, the default |
| `Param.required` | `True` where Required reads `yes` |
| `body`, `fixed` | the defaults: `BodyFormat.JSON` and no `fixed` pair. A `FILE` value makes the body multipart (#13 AC-2.4). |
| `content_type` | `CONTENT_TYPE_OCTET_STREAM` on a raw-body record (D5), else `None`, the default |
| `paging` | `Paging.OFFSET` for a `GET` record whose section has the `query` rows `page` and `per_page`, else `Paging.NONE`, the default |

**The paged records.** They are `openapi-only#list-all-emoji-reactions-for-an-epic`,
`openapi-only#list-all-emoji-reactions-for-an-epic-comment`,
`openapi-only#list-all-emoji-reactions-for-a-merge-request-comment`,
`openapi-only#list-all-emoji-reactions-for-a-snippet-comment`, `openapi-only#retrieve-all-limit-exclusions`,
`openapi-only#list-all-offline-transfer-exports`, `openapi-only#list-all-bridge-jobs-by-pipeline` and
`openapi-only#list-runners-projects`. Each declares its `page` and `per_page` rows as it declares any other row.

**The uploads** (AC-3.2) are the five sections with a `file` row, each in the form Workhorse gives its route
(`routes.go`; requirements Introduction):

- multipart through `--file`: `openapi-only#upload-job-artifacts` (`file`; Workhorse generates `metadata` and refuses
  any other file part, `artifacts_uploader.go` `ProcessFile`), routed to `upload.Artifacts`. `call` sends each `FILE`
  attribute as a part of a `multipart/form-data` body, and every other body attribute as a form field (#41 D2);
- a raw body through `--input` (D5), each routed to `requestBodyUploader`:
  - `openapi-only#upload-package-file`, whose `status` and `select` are query `Param`s (`conventions.md` "Generic
    packages": "Query attributes");
  - `openapi-only#upload-terraform-module-package-file` (its `module_version` row is the glob);
  - `openapi-only#create-or-update-a-terraform-state`;
  - `deploy#send-the-file`: docs.gitlab.com's "Send the file" example sends `--form "file=@model.pkl"`, but
    `PUT …/packages/ml_models/` is a `requestBodyUploader` route, which stores the body unparsed (requirements
    Residuals).

**`deploy`.** Its records are:

- `deploy#authorize-the-upload` (`PUT …/files/(*path/):file_name/authorize`);
- `deploy#download-a-machine-learning-model-package-file` (`GET …/files/(*path/):file_name`);
- `deploy#send-the-file` (`PUT …/files/(*path/):file_name`), a raw-body record.

Each section's `path` row is `In` `path`, so no record of the three has a `Param`. No record declares an
`openapi-only#` ID of those three keys (AC-1.2).

**Module layout.** Both modules follow `families/no_stage_assigned.py`:

- `OPERATIONS: Tuple[RestOperation, ...]` holds the records in the page order of the reference, each under a comment
  naming its `##` and `###` headings;
- `PENDING: FrozenSet[Tuple[str, str]] = frozenset()`;
- the module docstring states D4's rules in prose. `openapi_only.py`'s also says that the three `ml_models` file keys
  are `deploy`'s, and which uploads take `--file` and which `--input`.

`GATED_OPERATIONS` is unchanged (UB-4; Security Considerations "Gates").

### D5 — The raw body (AC-3.2; DL-007)

The model is GitHub's `call --input` (#46, `.claude/specs/issue-46-github-call-raw-bodies/design.md` D1 and D2, merged
in PR #57), with GitLab's one origin and no `root`.

**The record.** `RestOperation` gains `content_type: Optional[str] = None`, after `fixed`: the media type of a body
that is the bytes `call --input` gives. The four raw-body records set it to the existing `CONTENT_TYPE_OCTET_STREAM`,
imported from `gitlab_api.transport`, as GitHub's `families/repos.py` imports it from `github_api.transport`.

**`registry.send`** gains `data: Optional[bytes] = None`.

- A record whose `content_type` is `None` goes through `transport.request`, as today. A `data` value for it raises
  `ValueError` before anything is sent.
- Any other record goes through `transport.request_raw(method=..., path=..., query=encoded.query, data=data,
  content_type=operation.content_type)`. Its `Param`s are all `Location.QUERY` (D4), so `encode` gives it query pairs
  only.
- `call` and `pages` are unchanged. The module docstring's `send` bullet and `send`'s docstring state the two paths.

**`Transport.request_raw(*, method, path, query=None, data=None, content_type) -> Response`** (new).

- The URL is `_rest_url(path=path, query=...)`, as for `request`.
- It returns `_send(method=..., url=..., data=data, content_type=content_type, credential=self._credential)`:
  - `_send` refuses a URL on another origin before sending (#13 D4);
  - `_build_request` adds `Accept`, the `Content-Type` only when `data` is not `None`, and the one credential header;
  - `data` goes out unchanged, with no envelope and no encoding.
- The module docstring's body bullet names it.

**`call --input FILE`** (`commands/call.py`).

- The grammar ends `[--file NAME=PATH]... [--input FILE]`. The constants are `OPTION_INPUT` (`--input`),
  `ARG_RAW_BODY` (`raw_body`, default `None`), `METAVAR_FILE` (`FILE`) and `STDIN_INPUT` (`-`). The option's `type`
  is `read_input`.
- **`read_input(text) -> bytes`.** For `-` it returns `sys.stdin.buffer.read()`, the binary buffer the Python docs
  name for binary data; for any other text, `Path(text).read_bytes()`. An `OSError` is raised again as
  `argparse.ArgumentTypeError` naming the path rendered with `json.dumps`. argparse catches only `ArgumentTypeError`,
  `TypeError` and `ValueError`, so the call is refused as a usage error, exit 2, before the config is read.
- **`prepare_call`** gains two steps. Each refusal is a `ValueError`, logged, exit 2, with nothing sent:
  1. first, `refuse_both_bodies(raw_body=..., args=...)` refuses a raw body beside any `-f` or `-F` value. The message
     names `--input`, `-f/--raw-field` and `-F/--field`, and says a raw-body record's attributes are given with
     `--query`;
  2. after `registry.lookup`, `refuse_raw_body(operation=..., raw_body=...)` refuses a raw body for any record but a
     `RestOperation` with a `content_type`. The message names the ID and `--input`, and says the body is given with
     `-f`, `-F` or `--file`.
- `--input` beside `--file` needs no refusal of its own. A raw-body record declares no `FILE` `Param`, so #41's checks
  refuse any `--file` given to it (D4's name check, or `registry.encode`'s shape check), and step 2 refuses `--input`
  for any other record.
- `PreparedCall` gains `raw_body: Optional[bytes] = None`, and `send_call` passes it to `registry.send` as `data`.
- A raw-body record called without `--input` sends no body and no `Content-Type`. GitLab answers it, and an error
  status exits 1 (#41 D4).
- No option string contains `token` (UB-2). The module docstring states the grammar, an `--input` bullet and the two
  refusals.

**N.** `documented_raw_body(*, section, record) -> Section` (new), beside `documented_paging`:

- for a record whose `content_type` is set, it returns the section without its `file` row (`RAW_BODY_ROW`), every
  other `body` row read as `query`;
- for any other record, it returns the section unchanged;
- `record_problems` reads the section through it, and so does `sent_record_problems`, before `documented_paging`;
- N calls a raw-body record without `--input`, so `body_members` reads no body.

**Why #41 D8 yields again.**

- The raw body is a request form part 1 does not build: the issue's Tier line names "the glob, optional-segment and
  raw-body forms part 1 left to #15". So `registry.py` and `transport.py` change under D8's exceptions row.
- Three edits reach past that row, beside D2's and D3's:
  - `call`'s `--input` is the option that gives the body, as #46 D1 adds it to GitHub's `call`;
  - `documented_raw_body` reads a body, not a path;
  - the entry script's `call` usage lines name `--input FILE` (#41 D7), as the map's `gitlab_api/` bullet does.

### D6 — Tests

**The two new family test modules.**

- F, `src/payload/test/test_gitlab_api_openapi_only.py`, is the module #41 D8 asks of a family with a paged record.
- G, `src/payload/test/test_gitlab_api_deploy.py`, is the family test module for `families/deploy.py` (`testing.md`
  item 3). Deploy has no paged record, but its tables and its path-form calls need a module beside its family.
- Both are built as `test_gitlab_api_no_stage_assigned.py` is. The fake host and the socket guard are autouse;
  `config/gitlab.json` is written in `tmp_path`; each call runs `main(argv=["call", …])` through `fixtures.run_main`;
  the family module is imported inside each test.
- Every expected ID, `Kind`, required name, paged ID, media type, URL and body is a literal table transcribed from the
  index and the sections, never read from the records.

**F's tests:**

- `test_nothing_is_pending`;
- `test_every_param_is_typed_as_its_row`;
- `test_no_param_names_a_path_parameter`;
- `test_only_the_list_records_are_paged`;
- `test_a_list_record_prints_every_page`;
- `test_a_path_form_is_sent_as_the_route_declares`;
- `test_a_glob_part_that_is_no_segment_sends_nothing`;
- `test_the_job_artifacts_upload_sends_the_file_as_its_part`;
- `test_a_raw_upload_sends_the_bytes_as_its_body`;
- `test_a_token_attribute_is_the_value_given`.

**G's tests:**

- `test_nothing_is_pending`;
- `test_no_record_declares_an_openapi_only_model_id`;
- `test_every_param_is_typed_as_its_row`;
- `test_the_optional_group_is_sent_only_when_given`;
- `test_the_upload_sends_the_bytes_as_its_body`.

**Additions to existing modules** (no existing test or assertion edited):

- R gains `test_placeholders_name_every_path_form`, `test_a_glob_value_keeps_its_slashes`,
  `test_a_glob_part_that_is_no_segment_is_refused`, `test_an_optional_group_is_written_only_when_given`,
  `test_an_escaped_parenthesis_is_sent_without_its_backslash` and `test_send_sends_a_raw_record_its_bytes`.
- K gains `test_a_missing_path_parameter_is_refused_unless_optional` (the two cases of Correctness Properties AC-2.3
  and AC-2.4) and `test_a_raw_body_the_call_cannot_send_is_refused`.
- T, `src/payload/test/test_gitlab_api_transport.py`, gains `test_a_raw_body_is_sent_unchanged`.
- P gains the properties `test_glob_value_keeps_each_slash` and `test_a_glob_value_with_a_refused_part_is_refused`.
  AC-2.1 and AC-2.2 quantify over every value, so each gets a property beside the existing
  `test_path_value_is_one_segment`. P's module docstring gains one sentence naming them.
- N gains `test_a_path_form_is_read_and_sent_as_written`, which pins D3's three edits and `documented_raw_body`.

Correctness Properties gives each test's oracle.

### D7 — Files

| D | File | Change |
|---|---|---|
| D1 | `src/payload/scripts/gitlab_api/registry.py` | `PLACEHOLDER` with its `sigil` group; the constants `GROUP_SIGIL`, `GLOB_SIGIL`, `GLOB_SEPARATOR`, `OPTIONAL_GROUP`, `GROUP_INNER`, `ESCAPED_PARENTHESIS` and `GROUP_PARENTHESIS`; `required_placeholders` and `_glob`; `expand`'s three steps; the module docstring's `expand` bullet and the docstrings of `placeholders` and `expand` |
| D5 | `src/payload/scripts/gitlab_api/registry.py` | `RestOperation.content_type`; `send` takes `data`; the module docstring's `send` bullet and `send`'s docstring |
| D5 | `src/payload/scripts/gitlab_api/transport.py` | `Transport.request_raw`; the module docstring's body bullet |
| D2 | `src/payload/scripts/gitlab_api/commands/call.py` | `missing_path_parameters` reads `registry.required_placeholders`; its docstring and the module docstring's D2 sentences |
| D5 | `src/payload/scripts/gitlab_api/commands/call.py` | `OPTION_INPUT`, `ARG_RAW_BODY`, `METAVAR_FILE`, `STDIN_INPUT`, `read_input`, `refuse_both_bodies`, `refuse_raw_body`, `PreparedCall.raw_body`; `prepare_call`'s two steps; `send_call`'s `data`; the `--input` option; the module docstring |
| D5 | `src/payload/scripts/gitlab_wrapper.py` | the module docstring's `call` usage lines name `--input FILE` |
| D3 | `test/test_gitlab_wrapper_contract.py` | `PATH_PLACEHOLDER` with the sigil, `glob_names`, `expanded_path`, `record_problems`' rule for a row the record lacks, and `test_a_path_form_is_read_and_sent_as_written`; the docstrings of `expanded_path` and `route_problems`; the module docstring names the forms |
| D5 | `test/test_gitlab_wrapper_contract.py` | `RAW_BODY_ROW`, `documented_raw_body`, read by `record_problems` and `sent_record_problems` |
| D4 | `src/payload/scripts/gitlab_api/families/openapi_only.py` | the records; `PENDING` empty; both typed; the docstring |
| D4 | `src/payload/scripts/gitlab_api/families/deploy.py` | the three records; `PENDING` empty; both typed; the docstring |
| D6 | `src/payload/test/test_gitlab_api_openapi_only.py` (F) | new |
| D6 | `src/payload/test/test_gitlab_api_deploy.py` (G) | new |
| D6 | `src/payload/test/test_gitlab_api_registry.py` (R), `test_gitlab_api_call.py` (K), `test_gitlab_api_transport.py` (T) | D6's additions |
| D6 | `test/test_gitlab_api_properties.py` (P) | D6's two properties and their docstring sentence |
| D5 | `docs/forLLMConsumption.md` | the `gitlab_api/` bullet's option list names `--input` |
| — | `docs/findings-ledger.md` | the Residuals' rows, written with `python scripts/memory_compile.py ledger add` |

**Not edited:** `commands/_common.py` and every other line of `commands/*`, `gitlab_wrapper_fixtures.py`, V and C.

### Sources

- `docs/api-reference/gitlab/conventions.md`: "URL-encoding path parameters" (`quote(value, safe="")`), "Offset-based",
  "Generic packages".
- `docs/api-reference/gitlab/rest/openapi-only.md`, its preamble: "Parentheses mark optional path segments".
  `rest/deploy.md`: "Model registry API". `operations-index.md`: the References.
- Python 3.9 [`urllib.parse`](https://docs.python.org/3.9/library/urllib.parse.html):
  - `quote`: "Letters, digits, and the characters `'_.-~'` are never quoted"; the default of `safe` is `'/'`;
  - `urlparse`: "% escapes are not expanded".
- Python 3.9 [`re`](https://docs.python.org/3.9/library/re.html):
  - `(?<!...)` "Matches if the current position in the string is not preceded by a match for `...`", whose pattern
    "must only match strings of some fixed length";
  - a function `repl` "is called for every non-overlapping occurrence of pattern".
- [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986):
  - §2.2 `sub-delims = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "="`;
  - §3.3 `pchar = unreserved / pct-encoded / sub-delims / ":" / "@"`;
  - §5.2.4 `remove_dot_segments`, the reason for `REFUSED_SEGMENTS`.
- [GitLab docs, Personal access tokens API](https://docs.gitlab.com/api/personal_access_tokens/): rotation "revokes the
  previous token and creates a new token"; `self` revokes "the same personal access token you used to authenticate the
  request". [Project access tokens API](https://docs.gitlab.com/api/project_access_tokens/): rotation "immediately
  revokes the previous token and creates a new token", its response holding `token`.
  [Group access tokens API](https://docs.gitlab.com/api/group_access_tokens/): rotation "immediately revokes the
  previous token", its response holding `token`.
- GitLab `lib/api/project_import.rb`, `master`, read 2026-11-11: `POST ':id/import/git'` runs
  `conflict!('Project already has a repository') if user_project.repository_exists?`; `lib/api/helpers.rb` `conflict!`
  renders that message with status `409`.
- GitLab Workhorse, `gitlab-org/gitlab` `master`, read 2026-11-11:
  - `workhorse/internal/upstream/routes.go`: `requestBodyUploader := upload.RequestBody(api, signingProxy, preparer)`
    serves `PUT …/packages/generic/`, `…/packages/ml_models/` and `…/packages/terraform/modules/`, and
    `POST …/terraform/state/.*`; `POST …v4/jobs/[0-9]+/artifacts\z` goes to `upload.Artifacts`;
  - `workhorse/internal/upload/body_uploader.go` `RequestBody`: "It will store the request body to a location … It then
    forwards the request to gitlab-rails without the original request body".
- [GitLab docs, Model registry API](https://docs.gitlab.com/api/model_registry/) "Send the file":
  `--form "file=@model.pkl"`.
- Python 3.9 [`argparse`](https://docs.python.org/3.9/library/argparse.html) `type`: "If the function raises
  `ArgumentTypeError`, `TypeError`, or `ValueError`, the exception is caught … No other exception types are handled."
- Python 3.9 [`sys.stdin`](https://docs.python.org/3.9/library/sys.html): "To write or read binary data from/to the
  standard streams, use the underlying binary `buffer` object."

## Testing Strategy

- **Fake host.** `src/payload/test/gitlab_wrapper_fixtures.py`, unedited (#13, #41 D8). F and G judge a request by
  `FakeGitLab.requests`: the method, `url` as sent, the body bytes and its headers. They judge a refusal by `caplog`
  and by "no request recorded", and read stdout with `capsys`.
- **Registry examples.** R works on synthetic `RestOperation`s, each built on one reference path.
- **Properties.** P puts `src/payload/scripts` on `sys.path` and carries `@settings(deadline=None)`, as its existing
  properties do. Hypothesis stays in `test/`; the shipped suites stay pytest-only.
- **Contract and coverage.** N, as in D3 and D5; V, unedited. Both find the new records by discovery.
- **Regression.** C, `src/payload/test/test_gitlab_api_no_stage_assigned.py` and the existing tests of K, T, R, P, N and
  V run unedited.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project. Until it exists, N
  calls every record of this change, and F and G the path forms, lists and uploads, through `main`'s argv against the
  fake host, up to the API boundary, in CI's `verify` job, leg `tests`. For an unreachable record (#41 D5: the
  `/admin/`, `/geo/` and `/hooks/` keys) N's two tests are the whole proof (AC-3.3).

## Correctness Properties

Each entry gives the test's kind and its oracle. "The configured project" is F's and G's `project_id` in
`config/gitlab.json`.

- **AC-1.1**
  - Example, F `test_nothing_is_pending`. `openapi_only.PENDING` is empty, and the sorted IDs of
    `openapi_only.OPERATIONS` equal F's literal `OPERATION_IDS`, each once. `OPERATION_IDS` holds every
    `rest/openapi-only.md` Reference of the index but the three `ml_models` file anchors.
  - Structural: V `test_every_declared_key_is_in_its_family`. Each record's method and path, verbatim, are on a row
    that carries its Reference.
- **AC-1.2**
  - Example, G `test_nothing_is_pending`. `deploy.PENDING` is empty, and the IDs are the three of D4.
  - Example, G `test_no_record_declares_an_openapi_only_model_id`. `registry.lookup` raises `ValueError` for each of
    `openapi-only#download-an-ml_model-package-file`, `openapi-only#workhorse-upload-model-package-file` and
    `openapi-only#workhorse-authorize-model-package-file`.
- **AC-1.3**
  - Structural: N `test_every_record_matches_its_reference_section`. Each `Param` matches its row by name and `In`,
    and every `query` and `body` row is declared.
  - Example, F `test_every_param_is_typed_as_its_row`:
    - `{operation_id: {name: kind name}}` over every non-`SCALAR` `Param` equals F's literal `KINDS`, the rows typed
      `array of string`, `object`, `array of object` and `file` but a raw-body record's `file` row;
    - `{operation_id: frozenset(required names)}` over the records with any equals F's `REQUIRED`, the `yes` rows that
      name no path parameter, a raw-body record's `file` row excepted;
    - `{operation_id: content_type}` over the records whose `content_type` is set equals F's `RAW_BODIES`, the three
      `openapi-only#` raw-body records with `CONTENT_TYPE_OCTET_STREAM`, and every `Param` of those is
      `Location.QUERY`;
    - every record has `body is BodyFormat.JSON` and `fixed == ()`.
  - Example, G `test_every_param_is_typed_as_its_row`. No record of the three has a `Param`.
    `deploy#send-the-file`'s `content_type` is `CONTENT_TYPE_OCTET_STREAM`, the other two's `None`. All three are
    JSON-bodied, with no `fixed` pair, and `Paging.NONE`.
- **AC-1.4**
  - Structural, F `test_no_param_names_a_path_parameter`: `openapi_only.OPERATIONS` is not empty (as N's
    `assert records`), and no `Param` name of any `openapi_only` record is in `registry.placeholders(path=record.path)`.
    G's typing test pins it for `deploy`.
  - Example, N `test_a_path_form_is_read_and_sent_as_written`. `record_problems` returns nothing for
    `openapi-only#download-package-file` built with no `Param`: its `query` rows `package_version` and `path` are read
    as its path parameters. It also returns nothing for `deploy#download-a-machine-learning-model-package-file` built
    with no `Param`. For `openapi-only#upload-package-file` built as D4 writes it but without `status`, it names
    `status` and nothing of `file`: the skip leaves every other row held, and `documented_raw_body` reads `file` as the
    body.
- **AC-1.5** — Example, F `test_only_the_list_records_are_paged`: the IDs whose `paging` is `Paging.OFFSET` equal D4's
  paged records; each paged record's `params` holds `Param(name="page", location=Location.QUERY)` and
  `Param(name="per_page", location=Location.QUERY)`. Every other record of both modules is `Paging.NONE` (F, and G's
  typing test).
- **AC-1.6** — F and G `test_nothing_is_pending`; on the merged tree, V `test_every_index_row_is_mapped_or_pending`
  and `test_every_declared_key_is_in_its_family`.
- **AC-2.1**
  - Property, P `test_glob_value_keeps_each_slash`. The domain is any list of one or more parts, each a non-surrogate
    text without `/` other than `""`, `.` and `..`. `expand` of `/projects/*glob/issues`, the parts joined by `/`,
    gives a middle whose split at `/` has one piece per part; no piece holds `?` or `#`, and each unquotes to its part.
    `@example(parts=["1.0", "rc 1"])`.
  - Example, R `test_a_glob_value_keeps_its_slashes`: `1.0/rc 1` is written `1.0/rc%201`, `@scope/pkg`
    `%40scope/pkg`, `a?b#c` `a%3Fb%23c`, and `%2e%2e/x` `%252e%252e/x`.
- **AC-2.2**
  - Property, P `test_a_glob_value_with_a_refused_part_is_refused`. `""`, `.` or `..` inserted at any position of such
    a list makes `expand` raise `GitLabAPIError`.
  - Example, R `test_a_glob_part_that_is_no_segment_is_refused`. `a//b`, `/a`, `a/`, `a/./b`, `a/../b`, `""`, `.` and
    `..` each raise `GitLabAPIError` naming `*path`. No value raises `ValueError`.
  - Example, F `test_a_glob_part_that_is_no_segment_sends_nothing`.
    `call openapi-only#workhorse-authorize-the-maven-package-file-upload --path file_name=x.jar`, with
    `--path path=a//b`, `--path path=/a` or `--path path=a/../b`. Oracle: exit 1, no request recorded, and a log record
    naming `*path`.
- **AC-2.3**
  - Example, R `test_an_optional_group_is_written_only_when_given`. AC-2.3's example is written both ways; `path`
    absent and `path=None` both leave the group out; `path=""` raises `GitLabAPIError`.
  - Example, F `test_a_path_form_is_sent_as_the_route_declares`, its "group given" and "group left out" rows.
  - Example, G `test_the_optional_group_is_sent_only_when_given`, with `--path model_version_id=3` and
    `--path file_name=model.bin` and the configured project:
    - `deploy#download-a-machine-learning-model-package-file` with `--path path=dir/sub` sends
      `GET …/projects/<project_id>/packages/ml_models/3/files/dir/sub/model.bin`;
    - the same without `path` sends `…/files/model.bin`;
    - `deploy#authorize-the-upload` without `path` sends `PUT …/files/model.bin/authorize`.
  - Example, K `test_a_missing_path_parameter_is_refused_unless_optional`. `openapi-only#download-package-file` given
    `package_name` and `package_version` but no `file_name` and no `path` exits 2 with no request. Its log record says
    `file_name` has no value, says nothing of `path` having none, and lists `path` among the path parameters.
- **AC-2.4**
  - Example, K `test_a_missing_path_parameter_is_refused_unless_optional`. `call
    openapi-only#npm-registry-metadata-endpoint-2` with no `--path package_name` exits 2 with no request. Its log record
    says `package_name` has no value and lists `id` and `package_name` as the path parameters.
  - Example, R `test_placeholders_name_every_path_form`:
    - the generic-package path gives `("id", "package_name", "package_version", "path", "file_name")` for
      `placeholders`, and the same without `path` for `required_placeholders`;
    - the OData path `Packages\(Id='*package_name',Version='*package_version'\)` gives
      `("project_id", "package_name", "package_version")` for both;
    - the Debian path `…/dists/*distribution/:component/binary-:architecture/Packages` gives
      `("id", "distribution", "component", "architecture")`;
    - `/projects/:id/repository/branches/:branch` gives `("id", "branch")`, as before.
- **AC-2.5**
  - Example, R `test_an_escaped_parenthesis_is_sent_without_its_backslash`:
    - AC-2.5's example;
    - `FindPackagesById\(\)` is written `FindPackagesById()`;
    - `Packages\(\)` is written `Packages()` with no value given, so it is not read as a group;
    - `/projects/:id/packages/nuget/v2/$metadata` is unchanged but for `:id`;
    - a glob value `a(b)'` is written `a%28b%29%27`.
  - Examples, F `test_a_path_form_is_sent_as_the_route_declares`: the NuGet rows below.
- **AC-2.6** — Parametrized example, F `test_a_path_form_is_sent_as_the_route_declares`. Each row runs `call <id>`
  through `main`. Oracle: exit 0, and the fake host's one recorded `(method, url)` equals the row's.

  | Form | `<id>` and options | Sent |
  |---|---|---|
  | a glob holding `/` | `openapi-only#workhorse-authorize-the-maven-package-file-upload --path path=a/rc 1 --path file_name=x.jar` | `PUT …/projects/<project_id>/packages/maven/a/rc%201/x.jar/authorize` |
  | group given | `openapi-only#download-package-file --path package_name=pkg --path package_version=1.0 --path path=a/b --path file_name=file.txt` | `GET …/projects/<project_id>/packages/generic/pkg/1.0/a/b/file.txt` |
  | group left out | the same without `--path path=a/b` | `GET …/projects/<project_id>/packages/generic/pkg/1.0/file.txt` |
  | escaped, with globs | `openapi-only#the-nuget-v2-feed-single-package-metadata-endpoint --path project_id=7 --path package_name=N --path package_version=1.0` | `GET …/projects/7/packages/nuget/v2/Packages(Id='N',Version='1.0')` |
  | escaped, empty | `openapi-only#the-nuget-v2-feed-enumerate-packages-endpoint --path project_id=7 --query $filter=x` | `GET …/projects/7/packages/nuget/v2/Packages()?%24filter=x` |
  | escaped, beside a query `id` | `openapi-only#the-nuget-v2-feed-find-packages-by-id-endpoint --path project_id=7 --query id=N` | `GET …/projects/7/packages/nuget/v2/FindPackagesById()?id=N` |
  | `$metadata` | `openapi-only#the-nuget-v2-feed-package-metadata-endpoint-1` | `GET …/projects/<project_id>/packages/nuget/v2/$metadata` |

  The refused glob part is AC-2.2's F test.
- **AC-3.1**
  - Structural: N `test_every_record_is_sent_as_its_section_documents` calls every record of this change.
  - Examples: AC-2.6's rows without `--path id` send to the configured project. The output rules are #41's, held by
    K's existing tests unedited.
- **AC-3.2** — "The bytes" are a file's bytes holding `\r\n` and `\xff`, which a text-layer read would translate or
  fail to decode.
  - Example, F `test_the_job_artifacts_upload_sends_the_file_as_its_part`: `call openapi-only#upload-job-artifacts
    --path id=5 --file file=<a file in tmp_path> -f artifact_type=archive`. Oracle:
    - the recorded method and URL;
    - `Content-Type` `multipart/form-data`;
    - the part named `file` carries a `filename` and the file's bytes;
    - the `-f` attribute is a part with no `filename`, holding its text.
  - Parametrized example, F `test_a_raw_upload_sends_the_bytes_as_its_body`, over the three `openapi-only#` raw-body
    records of D4. Each is called with its path values and `--input <the bytes in tmp_path>`;
    `openapi-only#upload-package-file` also gets `--query status=hidden --query select=package_file`. Oracle: exit 0;
    one recorded request with the row's method and URL, query included; `Content-Type` `application/octet-stream`; a
    body equal to the bytes; the configured credential header.
  - Example, G `test_the_upload_sends_the_bytes_as_its_body`: `call deploy#send-the-file --path model_version_id=3
    --path path=dir --path file_name=model.bin --input -`, `sys.stdin` monkeypatched to
    `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=<the bytes>))`, as #46's `test_github_api_call.py` builds it.
    Oracle: one
    `PUT …/projects/<project_id>/packages/ml_models/3/files/dir/model.bin`, `Content-Type` `application/octet-stream`,
    the bytes as its body.
  - Example, K `test_a_raw_body_the_call_cannot_send_is_refused`. Each case exits 2 with no request recorded:
    - `--input <a file>` beside `-f status=hidden`, and beside `-F status="hidden"`, on
      `openapi-only#upload-package-file`: a log record names `--input`, `-f/--raw-field`, `-F/--field` and `--query`;
    - `--input <a file>` on `plan#retrieve-a-project-issue --path issue_iid=5` and on K's synthetic
      `graphql#syntheticProject`: a log record names the ID and `--input`;
    - `--input <a missing file>`: standard error holds `argument --input:` and the path rendered with `json.dumps`.
  - Example, R `test_send_sends_a_raw_record_its_bytes`. A synthetic record with a `content_type`, sent with `data`,
    records one request whose body is `data` and whose `Content-Type` is the record's. The same `data` for a record
    whose `content_type` is `None` raises `ValueError`, and no request is recorded.
  - Example, T `test_a_raw_body_is_sent_unchanged`, for each `TokenType`. `request_raw(method="PUT",
    path="/projects/1/packages/generic/p/1.0/f.bin", query=(("select", "package_file"),), data=<the bytes>,
    content_type=CONTENT_TYPE_OCTET_STREAM)` records one request to the configured origin. Its URL ends
    `?select=package_file`, its body equals the bytes, it carries that `Content-Type` and the token type's one
    credential header. `data=None` sends no body and no `Content-Type`.
- **AC-3.3**
  - Structural: N `test_every_record_matches_its_reference_section` and
    `test_every_record_is_sent_as_its_section_documents` over every record, the `/admin/`, `/geo/` and `/hooks/` ones
    included.
  - Example, N `test_a_path_form_is_read_and_sent_as_written`, with every path value `v1`:
    - `call_problems` returns nothing for `GET /projects/v1/packages/generic/v1/v1/v1/v1` on
      `openapi-only#download-package-file`, and no "given but not sent" problem for its `query` row `package_version`;
    - it names the path for `/projects/v1/packages/generic/v1/v1/(v1/)v1`, and for
      `/projects/v1/packages/generic/v1/v1/v1`, where the group was left out though `path` was given;
    - it returns nothing for `GET /projects/v1/packages/nuget/v2/Packages(Id='v1',Version='v1')`, and names the path
      for the same written with `\(` and `\)`;
    - the `record_problems` cases are those of AC-1.4.
- **AC-3.4** — Parametrized example, F `test_a_list_record_prints_every_page`, one case per paged record of D4.
  - Pages are scripted with `FakeGitLab.script` at the record's expanded URL: the first with
    `per_page=MAX_PER_PAGE`, answering an `x-next-page`; the second with `page` set to that value, answering an empty
    one.
  - Oracle: stdout equals `print_json` of both pages' items in order; every scripted response was served; exit 0.
- **UB-1** — C passes with every existing case unedited, and the PR diff changes no line of C.
- **UB-2**
  - P `test_standard_library_only` scans the entry script and the package, `transport.py`, `registry.py`,
    `commands/call.py` and the family modules among them.
  - C `test_load_config_refusals` and `test_environment_token_ignored`, and K `test_call_takes_no_token_option`, pass
    unedited.
  - Example, F `test_a_token_attribute_is_the_value_given`. `call openapi-only#request-a-job -f token=runner-token`
    sends one `POST …/jobs/request` whose JSON body is `{"token": "runner-token"}` and whose `Private-token` header is
    the configured token. The configured token appears in no body.
- **UB-3** — `src/payload/test/test_github_api_*.py` and `src/payload/test/test_wrapper_delivery.py` pass in CI's
  `tests` leg, and the PR diff names no file of UB-3.
- **UB-4**
  - R `test_project_path_is_encoded` and `test_empty_and_dot_segments_are_refused`, and P
    `test_path_value_is_one_segment`, pass unedited.
  - Every K test passes, `test_a_gated_operation_names_its_subcommand` and `test_a_missing_path_parameter_is_refused`
    included.
  - The existing tests of N and V pass. The PR diff edits no existing assertion and no `GATED_OPERATIONS` entry.

## Security Considerations

- **Traversal through a glob.**
  - Each part of a glob value is refused when it is empty, `.` or `..`, the segments RFC 3986 §5.2.4 removes or merges.
  - Each part is written with `quote(safe="")`, which leaves no character but letters, digits and `_.-~` unencoded. So
    a part cannot carry `?`, `#`, `\`, a parenthesis or a raw `%`, and a value `%2e%2e` is sent as `%252e%252e`, which
    one decoding turns into the text `%2e%2e`, never into `..`.
  - The `/` between parts is the only unencoded character a value adds, and it is what a glob means.
- **Optional groups.** A group is left out only when its parameter is not given. A given empty value is a refused
  part, so no group yields `//`.
- **Literal characters.** `(`, `)`, `$`, `'`, `,` and `=` are the template's own characters, never a value's (D1 steps
  1 and 2). They are `sub-delims`, which `pchar` admits in a path segment (RFC 3986 §2.2, §3.3).
- **The host.** The URL is `https://<hostname>/api/v4` followed by the expanded root-relative path
  (`Transport._rest_url`), and `_send` refuses any other origin (#13 D4). No path value changes the host.
- **The credential.** It comes from `config/gitlab.json` only and travels in its header (UB-2). A runner's or job's
  `token` attribute (`/jobs/request`, `/jobs/:id/artifacts`) is a value the caller gives, sent where its record puts
  it. Like any text value it shows in the command line (#41 Residuals "Secrets in arguments"); a `token` given with
  `--query` (`/runners/managers`, `/jobs/:id/artifacts`, `/jobs/:id/runtime_environment_key`) is also in the URL that
  an error or a 429 warning quotes on standard error (Residuals).
- **The raw body.**
  - `--input` reads the named file, or standard input, whole when the arguments are parsed. Its bytes go unchanged to
    the configured origin only: `request_raw` sends through `_send`, whose origin check and one credential header are
    unchanged (D5); each raw-body record is a `PUT` or a `POST`, and `CredentialStrippingRedirectHandler` follows a
    redirect of neither (#13 D4 "Redirects"), so a `3xx` exits 1 and neither the bytes nor the token reach its target.
  - None of it is logged: an error quotes the method, the URL and the response, and argparse's error names only the
    path, rendered with `json.dumps`. A call that D5's steps refuse has read the body and sends none of it.
  - A caller who names `config/gitlab.json` uploads the token as a package file or a state, as `--file` sends it
    today (#41 Residuals "Secrets in arguments"); no guard refuses it (Residuals).
- **The routes that stay callable**, gated by none (#41 Security "Destructive operations": running one is the caller's
  decision):
  - the Workhorse `authorize` routes, which `conventions.md` "Generic packages" advises not to call ("unverified";
    requirements Residuals);
  - the runner routes (`/jobs/request`, `/jobs/:id` and its sub-paths);
  - the `/admin/`, `/geo/` and `/hooks/` routes. GitLab answers them for an administrator or a Geo site only; any
    other token gets an HTTP error, which exits 1 (#41 D4);
  - every `DELETE`, `PUT` and `POST`, among them `openapi-only#revoke-a-personal-access-token`,
    `openapi-only#rotate-a-personal-access-token`, `openapi-only#rotate-a-project-access-token` and
    `openapi-only#rotate-a-group-access-token`, which act on the configured token (Residuals).
- **Gates.** `GATED_OPERATIONS` and the hooks are unchanged. #41's gated class is a record that commits to or merges
  into a branch, or creates an issue. No record of this change merges.
  - `openapi-only#create-a-ci-configuration-merge-request` commits only into the merge request it opens.
  - `openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push` needs the `secret_token` its entry
    requires, which `config/gitlab.json` does not hold.
  - The slash-command triggers cannot carry an issue-creating command through `call`: the Mattermost records declare
    no `text`, and `/slack/trigger`'s declares no `token`.
  - `openapi-only#import-a-project-from-a-git-url` fills only a project that has no repository: GitLab answers `409`
    "Project already has a repository" to any other (`lib/api/project_import.rb`, `POST ':id/import/git'`), so it
    writes no existing branch, the configured project's included.

  None is gated; running one is the caller's decision.
- **Dependencies.** None added. The shipped code stays Python 3.9 standard library, with no subprocess.

## Operability

The GitLab wrapper is not installed in this repository. `config/toolchain.json` `not_installed` lists
`src/payload/scripts/gitlab_wrapper.py`, "the repository is on GitHub", so no session here runs these records. They
reach a project through the setup prompts' copy of `gitlab_api/` (#13 D2). Nothing deploys, and no configuration or
migration changes. A refused glob part is logged to standard error with `registry.expand`'s message (exit 1). A glob
outside an optional group given no value, and D5's two `--input` refusals, are refused as #41 refuses a missing path
parameter: logged, exit 2, nothing sent (D2, D5).

## Acceptance Criteria Mapping

Test files:

- F = `src/payload/test/test_gitlab_api_openapi_only.py` (new)
- G = `src/payload/test/test_gitlab_api_deploy.py` (new)
- R = `src/payload/test/test_gitlab_api_registry.py`
- K = `src/payload/test/test_gitlab_api_call.py`
- T = `src/payload/test/test_gitlab_api_transport.py`
- C = `src/payload/test/test_gitlab_wrapper_compat.py`
- P = `test/test_gitlab_api_properties.py`
- N = `test/test_gitlab_wrapper_contract.py`
- V = `test/test_gitlab_wrapper_coverage.py`

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D4; `families/openapi_only.py` | F `test_nothing_is_pending`; V `test_every_declared_key_is_in_its_family` |
| AC-1.2 | D4; `families/deploy.py` | G `test_nothing_is_pending`, `test_no_record_declares_an_openapi_only_model_id` |
| AC-1.3 | D4; both family modules; D5 `documented_raw_body` | N `test_every_record_matches_its_reference_section`; F and G `test_every_param_is_typed_as_its_row` |
| AC-1.4 | D4; D3 `glob_names`, `record_problems` | F `test_no_param_names_a_path_parameter`; G `test_every_param_is_typed_as_its_row`; N `test_a_path_form_is_read_and_sent_as_written` |
| AC-1.5 | D4 | F `test_only_the_list_records_are_paged`; G `test_every_param_is_typed_as_its_row` |
| AC-1.6 | both `PENDING` sets | F and G `test_nothing_is_pending`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` |
| AC-2.1 | D1 `PLACEHOLDER`, `_glob`, `expand` | P `test_glob_value_keeps_each_slash`; R `test_a_glob_value_keeps_its_slashes`; F `test_a_path_form_is_sent_as_the_route_declares` |
| AC-2.2 | D1 `_glob`, `REFUSED_SEGMENTS` | P `test_a_glob_value_with_a_refused_part_is_refused`; R `test_a_glob_part_that_is_no_segment_is_refused`; F `test_a_glob_part_that_is_no_segment_sends_nothing` |
| AC-2.3 | D1 `OPTIONAL_GROUP`, `expand`; D2 `missing_path_parameters`, `required_placeholders` | R `test_an_optional_group_is_written_only_when_given`; F `test_a_path_form_is_sent_as_the_route_declares`; K `test_a_missing_path_parameter_is_refused_unless_optional`; G `test_the_optional_group_is_sent_only_when_given` |
| AC-2.4 | D1 `placeholders`, `required_placeholders`; D2; `check_parameters`, `documented_text` (unchanged) | K `test_a_missing_path_parameter_is_refused_unless_optional`; R `test_placeholders_name_every_path_form` |
| AC-2.5 | D1 `ESCAPED_PARENTHESIS`, `OPTIONAL_GROUP` | R `test_an_escaped_parenthesis_is_sent_without_its_backslash`; F `test_a_path_form_is_sent_as_the_route_declares` |
| AC-2.6 | D1, D2 through `main` | F `test_a_path_form_is_sent_as_the_route_declares`, `test_a_glob_part_that_is_no_segment_sends_nothing`; G `test_the_optional_group_is_sent_only_when_given` |
| AC-3.1 | `call_operation`, `registry.send`, `registry.pages` (unchanged); D1 | N `test_every_record_is_sent_as_its_section_documents`; F `test_a_path_form_is_sent_as_the_route_declares` |
| AC-3.2 | D4 uploads; D5 `RestOperation.content_type`, `registry.send`, `Transport.request_raw`, `read_input`, `refuse_both_bodies`, `refuse_raw_body`; `registry.encode`, `transport.request_body` (unchanged) | F `test_the_job_artifacts_upload_sends_the_file_as_its_part`, `test_a_raw_upload_sends_the_bytes_as_its_body`, `test_every_param_is_typed_as_its_row`; G `test_the_upload_sends_the_bytes_as_its_body`; K `test_a_raw_body_the_call_cannot_send_is_refused`; R `test_send_sends_a_raw_record_its_bytes`; T `test_a_raw_body_is_sent_unchanged` |
| AC-3.3 | D3; D5 `documented_raw_body` | N `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents`, `test_a_path_form_is_read_and_sent_as_written` |
| AC-3.4 | D4 paged records; `Transport.pages` (unchanged) | F `test_a_list_record_prints_every_page` |
| UB-1 | `commands/*` but D2's and D5's edits; `gitlab_wrapper.py` but its usage lines | C, every existing test; PR diff |
| UB-2 | `_load_config`; `call`'s options; the package's imports | P `test_standard_library_only`; C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option`; F `test_a_token_attribute_is_the_value_given` |
| UB-3 | none (the files are untouched) | `src/payload/test/test_github_api_*.py`, `test_wrapper_delivery.py`; PR diff |
| UB-4 | D1 `_segment` (unchanged), `expand`; `GATED_OPERATIONS` (unchanged) | R `test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused`; P `test_path_value_is_one_segment`; K, every test; N and V, their existing tests; PR diff |

## Residuals

- The `requirements.md` Residuals stand, each one findings-ledger row (D7).
- `openapi-only#revoke-a-personal-access-token` revokes the token that authenticates the request.
  `openapi-only#rotate-a-personal-access-token`, `openapi-only#rotate-a-project-access-token` and
  `openapi-only#rotate-a-group-access-token` each revoke that token and create a new one, whose value the response
  holds; the project record needs no option, its `id` defaulting to the configured project (Sources). `call` prints
  that response and gates none of them (#41 Security "Destructive operations") → one findings-ledger row.
- Secrets: a `--query` `token` is in the URL an error or a 429 warning quotes, and no guard refuses an `--input` naming
  `config/gitlab.json` (Security Considerations) → one findings-ledger row each.
- #38 is left with no key: these three records are the whole of `rest/deploy.md` (DL-001) → the conductor routes #38.
- #43's `http(s)://${CI_REGISTRY}` keys: D1 step 1 writes `(s)`, a group with no parameter, as `s`; #43 decides it.
