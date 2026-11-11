# Design — issue #43: GitLab wrapper rewrite, part 2 slice: the package stage group

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-4.4, UB-1..UB-4, frozen). Builds on
`.claude/specs/issue-13-gitlab-wrapper-foundation/design.md` ("#13 Dn"),
`.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn") and #40's approved design,
`.claude/specs/issue-40-gitlab-openapi-only-records/design.md` ("#40 Dn"). #40 D1 (the glob, the optional group, the
escaped parenthesis), D2 (`call`'s optional path parameter), D3 (N's path reading) and D5 (the raw body) are used by
reference and not restated; this branch rebases onto `origin/main` once #40's PR has merged, before its implementation
waves (DL-001). The test files are named in the legend under Correctness Properties.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #43, "GitLab wrapper rewrite, part 2 slice:
   the package stage group", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Overview

`families/package.py` gets one record per pending key but those AC-1.2 and AC-1.3 keep, transcribed by D6's rules. Two
path forms are added for them:

- **the hyphenated name**: #40's `registry.PLACEHOLDER` lets a name continue past a `-` that a name character follows,
  so `:module-name` is one parameter (D1);
- **the route prefix**: a record whose path starts with `/<route-prefix>/` lists its page's prefix values in
  `RestOperation.route_prefixes`; `registry.route` writes the value a call names, and `call` takes it with
  `--route-prefix` and refuses any other (D2, D3).

N reads each page's `<route-prefix>` line, names a record whose values differ, and sends each prefix record under its
page's first value (D4). Each upload is sent in the form GitLab Workhorse reads on its route: a raw body through #40's
`call --input` where Workhorse stores the request body, multipart through `--file` elsewhere (D5). D7 names the tests,
D8 the files.

## Design

### D1 — The hyphenated name (AC-3.1, UB-4)

On #40's base, `PLACEHOLDER` is `(?P<sigil>[:*])(?P<name>[A-Za-z_][A-Za-z0-9_]*)`. Only its `name` group changes:

```python
# A path parameter: `:name`, sent as ONE segment, at a segment start (`/projects/:id`) or inside one
# (`binary-:architecture`); or `*name`, a glob whose value keeps its `/` (#40 D1). A name continues past a `-` that a
# name character follows (`:module-name`); `:name-/` still ends before its `-`.
PLACEHOLDER = re.compile(pattern=r"(?P<sigil>[:*])(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*)")
```

- `(?:...)` is "a non-capturing version of regular parentheses" (Python docs, `re`), so `sigil` and `name` stay the
  pattern's only groups and every `match.group(GROUP_NAME)` reads the whole hyphenated name.
- Every reader of `placeholders`, `required_placeholders` and `expand` (#40 D1) then reads `:module-name` as
  `module-name`: `call`'s documented and missing path parameters (`documented_names`, `missing_path_parameters`,
  `documented_text`), `encode`'s skip of path names (`_declared_values`) and `_segment`'s value. `call --path
  module-name=infra` names it, as `assignment` splits at the first `=` (#41 D2). No other line of `registry.py` or
  `commands/call.py` changes for the name.
- N's `PATH_PLACEHOLDER` widens its `name` group the same way (D4).
- **UB-4.** The "Upload module" key is the only path of `operations-index.md` in which a `:name` or `*name` is followed
  by `-` and a name character. Every other path holds the names it holds on #40's base, the in-segment forms
  (`binary-:architecture`, `:package_name$:sha`, `:module_version.info`, `:file_name.tgz`) included.
  `test_only_the_upload_module_path_holds_a_hyphenated_name` (D7) proves it over every row.

### D2 — The route prefix in `registry` (AC-2.1 to AC-2.4)

**The record.** `RestOperation` gains `route_prefixes: Tuple[str, ...] = ()`, after #40's `content_type`: on a record
whose path starts with `/<route-prefix>/`, the prefix values of its page's `<route-prefix>` line, verbatim, in the
line's order; on any other record, empty.

**The constant and the test.** `ROUTE_PREFIX = "/<route-prefix>"`. `takes_route_prefix(*, path) -> bool` is whether
`path` starts with `ROUTE_PREFIX` followed by `/`.

**`route(*, operation: Operation, prefix: Optional[str]) -> Operation`** (new):

| The record | `prefix` | Result |
|---|---|---|
| a REST record whose path `takes_route_prefix` | equal, as text, to one of its `route_prefixes` | `dataclasses.replace(operation, path=<that value> + operation.path[len(ROUTE_PREFIX):])` |
| the same | `None`, or any other text | `ValueError` naming the ID, the text given (`json.dumps`, as `check_parameters` renders a caller's name) and each of the record's `route_prefixes` |
| any other record, a GraphQL record included | `None` | the record itself |
| the same | any text | `ValueError` naming the ID and saying it takes no route prefix |

- The text written into the path is the value the record holds; the caller's text only selects it. So no text a
  caller gives becomes template text, and no prefix but the page's is sent.
- On the routed record every reader of `operation.path` sees the value written in. `placeholders` names its `:id`,
  `encode` skips it as a path value, and `expand` writes it as one percent-encoded segment (`_segment`). So
  `/groups/:id/-/packages/npm` with `id=my-group/sub` is written `/groups/my-group%2Fsub/-/packages/npm`, and
  `call`'s `takes_project` gives a path under `/projects/:id/` the configured project (AC-2.3, D3).
- A `:name` that a path holds twice (`/<route-prefix>/symbolfiles/:file_name/:signature/:file_name`) takes its one
  value at both places, as `expand` writes every match by its name (UB-4).
- `dataclasses.replace` "creates a new object of the same type as obj, replacing fields with values from changes"
  (Python docs, `dataclasses`). The routed record is a value of the call; no family declares it.

**`send(transport, operation_id, *, values=None, data=None, prefix=None)`.** After `lookup` and its GraphQL refusal,
the record is `route(operation=..., prefix=prefix)`. #40 D5's `data` check, `encode`, `expand` and the transport then
run on the routed record. `registry.call` reaches a REST record through `send` with no prefix, so `route` refuses a
prefix record there.

**`expand`** raises `ValueError` for a path that `takes_route_prefix`, before writing anything: a prefix record is
expanded only once `route` has written its prefix. `pages` takes no prefix and is otherwise unchanged; no prefix record
is paged (D6), and this refusal keeps `pages` from sending a prefix path unrouted.

**Docstrings.** The module docstring gains a `route` bullet, and its `expand` and `send` bullets state the two rules
above; so do the docstrings of `expand`, `send` and `route`.

### D3 — `call --route-prefix` (AC-2.1, AC-2.3, AC-2.4)

**The option.** The grammar ends `[--file NAME=PATH]... [--input FILE] [--route-prefix PREFIX]`.

- The constants are `OPTION_ROUTE_PREFIX` (`--route-prefix`), `ARG_ROUTE_PREFIX` (`route_prefix`, default `None`) and
  `METAVAR_PREFIX` (`PREFIX`). The option takes one value, stored as given; a repeated option keeps its last (argparse
  `store`).
- PREFIX is one of the record's prefix values, verbatim (`/groups/:id/-/packages/npm`). Each `:name` of it is a path
  parameter of the call, given with `--path` (`--path id=7`).
- Its help text: "the <route-prefix> of a protocol route: one of the values its page lists, e.g.
  /projects/:id/packages/npm".

**`prepare_call`.** Right after `registry.lookup` and #40's `refuse_raw_body`, the step
`operation = registry.route(operation=operation, prefix=args.route_prefix)`. Every later step reads the routed record:

| Step | What the routed record decides |
|---|---|
| `call_values` → `path_values` | the configured project as the `id` of a value starting `/projects/:id` that the call gives no `id` (AC-2.3, #41 AC-1.8) |
| `check_parameters` | `--path id` is documented under a value holding `:id`, and refused as undocumented under `/packages/npm` (AC-2.4, as #41 AC-2.2); `id` left without a value under `/groups/:id/…` is refused as #41 AC-2.3 refuses it |
| `registry.encode` | `id` skipped as a path value |

- `route`'s `ValueError` is a refusal of steps 1 to 5 like any other (#41 D4): logged, exit 2, nothing sent. Its
  message is AC-2.4's, naming the record's prefix values.
- `PreparedCall` gains `prefix: Optional[str] = None`; `send_call` passes it to `registry.send` as `prefix`.
- No option string contains `token` (UB-2).

**Docstrings and usage.**

- The module docstring states the grammar and a `--route-prefix` bullet. Its refusal paragraph gains "a route prefix
  that none of the record's values equals, none for a record whose path starts with `/<route-prefix>/`, or one for any
  other record (`registry.route`)".
- The entry script's `call` usage lines (#41 D7) name `--route-prefix PREFIX` and that refusal; the map's `gitlab_api/`
  bullet names the option.

**Why #41 D8's "never" row yields.** The `/<route-prefix>` paths are a request form part 1 does not build; the issue's
Tier line names them. The call chooses the prefix, so the choice is an option of `call`, as #40 D5's `--input` is. The
usage lines and the map name the option as they name `--input`.

### D4 — N's readings (AC-1.5, AC-3.1, AC-4.3)

`test/test_gitlab_wrapper_contract.py`, on #40's base:

| Reading | The edit |
|---|---|
| `PATH_PLACEHOLDER` | its `name` group widens as `registry.PLACEHOLDER`'s (D1), so `expanded_path` and `call_problems`' path names read `:module-name` whole |
| #40 D3's skip in `record_problems`' rule for a row the record lacks | it skips a row whose name is any name `PATH_PLACEHOLDER` matches in `record.path`, either sigil (AC-1.5: "whatever its `In`"), in place of the `*` names only; `glob_names` becomes `path_names` |
| the page reader | `Section` gains `route_prefixes: Tuple[str, ...] = ()`. `page_sections` reads, under a `##` heading, the line starting `` `<route-prefix>` on this page is one of: `` and gives every section of that page the backticked values after the colon, in order |
| `record_problems` | gains `prefix_problems(*, record, section)`. It names a record whose `route_prefixes` differ from the section's `route_prefixes` when the record's path starts with `/<route-prefix>/`, and from `()` otherwise, naming both tuples |
| the call half | `call_prefix(*, record, section)` is a prefix record's section's first value, else `None`. `record_call` gains `prefix=None`: given one, the argv gains `--route-prefix <prefix>`, and its path names are `registry.placeholders` of the record's path with `/<route-prefix>` replaced by it. `routed_section(*, section, prefix)` is the section with each endpoint path's `/<route-prefix>` replaced by the prefix. |

- **The send test.** `test_every_record_is_sent_as_its_section_documents` computes the prefix with `call_prefix`,
  passes it to `record_call`, and passes `routed_section(...)` to `sent_record_problems`. So the sent path is judged
  with the call's prefix value written in. No assertion of N changes.
- **The oracle.** N writes the prefix with its own replacement and never calls `registry.route`, so it does not share
  the code it judges (#40 D3).
- **Raw bodies.** #40 D5's `documented_raw_body` needs no edit: every raw-body record of D5 calls its file row `file`
  (`RAW_BODY_ROW`), or has no file row.
- **Why #41 D8's exceptions row is reached past in N.** The row admits N's path reading for a request form part 1
  does not build, and the route prefix is one (D3). AC-4.3 needs N to read the page's prefix values and send a prefix
  record under one, so four edits reach past the row, as #40 D3 and D5 name theirs: the page reader
  (`Section.route_prefixes`, `page_sections`), which reads a page line, not a path; `prefix_problems` in
  `record_problems`; the call half (`call_prefix`, `record_call`'s `prefix`, `routed_section` and the send test's
  loop); and #40's skip in `record_problems`, widened from `*name` to every path name (AC-1.5). Beside them,
  `PATH_PLACEHOLDER` (the row's path reading), D7's two tests and the module docstring, no line of N changes.

### D5 — The uploads (AC-4.2; #40 D5)

GitLab Workhorse fixes each upload's form by its route (`routes.go`, Sources). `requestBodyUploader` is
`upload.RequestBody`, which "will store the request body to a location" and forwards the request "without the original
request body" (`body_uploader.go`, as #40 D5 cites it). A multipart envelope sent to such a route would be stored as
the file. So each upload record takes the form its route reads:

| Record | Workhorse route → handler | Form |
|---|---|---|
| `package#upload-a-recipe-file`, `package#upload-a-package-file` (Conan v1, the instance endpoint) | `` apiPattern+`v4/packages/conan/` `` → `requestBodyUploader` | raw body |
| `package#upload-a-recipe-file-1`, `package#upload-a-package-file-1` (Conan v2) | `` apiProjectPattern+`/packages/conan/` `` → `requestBodyUploader` | raw body |
| `package#upload-a-package-file-2` (Debian) | `` `/packages/debian/` `` → `requestBodyUploader` | raw body |
| `package#upload-a-package-file-3` (Maven) | `` `/packages/maven/` `` → `requestBodyUploader` | raw body |
| `package#upload-a-package-file-4` (npm) | `` `/packages/npm/.*` `` → `requestBodyUploader` | raw body, JSON |
| `package#create-or-update-a-dist-tag` (npm) | project: `` apiProjectPattern+`/packages/npm/-/package/[^/]+/dist-tags/[^/]+` `` → `proxy`; group and instance: the catch-all `proxy`; Rails reads the version as the whole body (`version = env['api.request.body']`) | raw body, JSON: the version as a JSON string (`"1.0.0"`), as `npm dist-tag add` sends it |
| `package#upload-a-gem` (Ruby gems) | `` `/packages/rubygems/` `` → `requestBodyUploader` | raw body |
| `package#upload-module` (Terraform) | `` `/packages/terraform/modules/` `` → `requestBodyUploader` | raw body |
| `package#upload-a-package-file-5` (NuGet v3) | `` apiProjectPattern+`/packages/nuget/` `` needs the `/` after `nuget` that the row's path lacks: the catch-all `proxy` | `--file package=…` |
| `package#upload-a-symbol-package-file` (NuGet) | `` apiProjectPattern+`/packages/nuget/` `` → `mimeMultipartUploader` | `--file package=…` |
| `package#upload-a-package-1` (PyPI) | `` `/packages/pypi` `` → `mimeMultipartUploader` | `--file content=…` |
| `package#upload-a-chart` (Helm) | `` `/packages/helm/api/[^/]+/charts\z` `` → `mimeMultipartUploader` | `--file chart=…` |
| `package#upload-a-package` (Maven virtual registry) | no route of its own: the catch-all `proxy` | `--file file=…` |

- **A raw body** is #40 D5 unchanged: the record sets `content_type`; `call --input FILE` (or `-`) gives the bytes;
  `registry.send` sends them through `Transport.request_raw`; `refuse_both_bodies` and `refuse_raw_body` refuse a body
  the call cannot send; N reads the section through `documented_raw_body`.
  - The record has no `Param` for its `file` row, and each of its other `Param`s is `Location.QUERY` (D6). So `--file`
    given to it is refused by #41's checks, exit 2.
  - Its `content_type` is `CONTENT_TYPE_OCTET_STREAM`, but npm's two records', which are `CONTENT_TYPE_JSON`; both are
    imported from `gitlab_api.transport`. docs.gitlab.com's npm example sends `--header "Content-Type:
    application/json" --data @./path/to/metadata/file.json`; its Conan, Debian, Maven, Ruby gems and Terraform examples
    send `--upload-file`.
  - Debian's example gives `distribution` and `component` in the query (`…/debian/myother.deb?distribution=sid&
    component=main`), where D6 puts them. npm's `versions` and `version` rows are query `Param`s by the same rule; the
    publish document and the version are the `--input` bodies.
- **Multipart** is #41 D2's `--file`: each `FILE` attribute is a part of a `multipart/form-data` body, and every other
  body attribute a form field.

### D6 — Transcription rules (AC-1.1 to AC-1.6, AC-2.1)

Each record of `families/package.py` is written from its index row and its `rest/package.md` entry.

| Field | Rule |
|---|---|
| `operation_id` | `package#<anchor>`: the row's Reference without `rest/` and `.md`, verbatim, a `-1`, `-2` … suffix included (`package#upload-a-package-file-3`) |
| `method`, `path` | the row's, verbatim: `*name`, `/<route-prefix>`, `$` and `:module-name` as the row writes them. Of an entry listing more than one endpoint, the endpoint it lists first (AC-1.2) |
| `params` | one `Param` per `query`, `body` or `form` row of the entry, in table order. None for a row whose name is a path parameter of the record's path, whatever its `In` (AC-1.5), nor for a raw-body record's `file` row (D5) |
| `Param.name` | the backticked cell, verbatim (`Symbolchecksum`, `terraform-get`) |
| `Param.location` | `query` → `Location.QUERY`; `body` and `form` → `Location.BODY`; on a raw-body record, every `Param` → `Location.QUERY` (#40 D4) |
| `Param.kind` | `array of string` and `string array` → `ARRAY`; `object` → `HASH`; `array of object` → `ARRAY_OF_HASHES`; `file` → `FILE`; every other Type (`string`, `integer`, `integer (int32)`, `boolean`) → `SCALAR`, the default |
| `Param.required` | `True` where Required reads `yes` |
| `body`, `fixed` | the defaults: `BodyFormat.JSON` and no `fixed` pair. A `FILE` value makes the body multipart (#13 AC-2.4). |
| `content_type` | D5's, on a raw-body record; else `None` |
| `paging` | `Paging.OFFSET` for a `GET` record whose entry has the `query` rows `page` and `per_page`, which it declares as any other row; else `Paging.NONE` |
| `route_prefixes` | on a path starting `/<route-prefix>/`, its page's constant: `DEBIAN_ROUTE_PREFIXES` (`/projects/:id/packages/debian`, `/groups/:id/-/packages/debian`), `NPM_ROUTE_PREFIXES` (`/packages/npm`, `/projects/:id/packages/npm`, `/groups/:id/-/packages/npm`) or `NUGET_ROUTE_PREFIXES` (`/groups/:id/-/packages/nuget`, `/projects/:id/packages/nuget`); else `()` |

**The kept keys** (`PENDING`, AC-1.2, AC-1.3): the `/projects/:id/packages/conan/v1/…` key of every Conan v1 entry;
`("PUT", "/projects/:id/packages/nuget/v2")` of NuGet "Upload a package file"; the two keys whose path starts with
`/http(s)://${CI_REGISTRY}`; and `("PUT", "/projects/:id/")` (AC-1.3).

**The paged records** (AC-1.6): `package#within-a-project`, `package#within-a-group`,
`package#list-all-registry-repository-tags-in-a-project`, `package#list-all-upstream-registries-for-a-top-level-group`,
`package#list-upstream-registry-cache-entries`, `package#list-all-debian-distributions-in-a-group`,
`package#list-all-debian-distributions-in-a-project`, `package#list-all-upstream-registries`,
`package#list-all-upstream-registry-cache-entries`, `package#for-a-project`, `package#for-a-group`,
`package#list-package-files` and `package#list-package-pipelines`. No prefix record is among them.

**Module layout.** As `families/no_stage_assigned.py`:

- `OPERATIONS: Tuple[RestOperation, ...]` holds the records in the page order of the reference, each under a comment
  naming its `##` and `###` headings;
- `PENDING: FrozenSet[Tuple[str, str]]` holds the kept keys;
- the three prefix constants are `Tuple[str, ...]`, each under a comment naming its page;
- the module docstring states D6's rules in prose, which uploads take `--file` and which `--input`, and that a record
  whose path starts with `/<route-prefix>/` takes `--route-prefix`.

`GATED_OPERATIONS` is unchanged (UB-4; Security Considerations "Gates").

### D7 — Tests

**F, `src/payload/test/test_gitlab_api_package.py`** (new; #41 D8's module for a family with a paged record). It is
built as `test_gitlab_api_no_stage_assigned.py` is: the fake host and the socket guard autouse, `config/gitlab.json`
in `tmp_path`, each call `main(argv=["call", …])` through `fixtures.run_main`, the family module imported inside each
test. Every expected ID, key, `Kind`, required name, prefix value, paged ID, media type, URL and body is a literal table
transcribed from the index and the entries, never read from the records. Its tests:

- `test_nothing_is_pending_but_the_kept_keys`;
- `test_a_two_endpoint_entry_maps_its_first_endpoint`;
- `test_every_param_is_typed_as_its_row`;
- `test_no_param_names_a_path_parameter`;
- `test_only_the_list_records_are_paged`;
- `test_a_list_record_prints_every_page`;
- `test_a_prefix_record_is_sent_under_each_of_its_values`;
- `test_the_hyphenated_names_are_sent_as_one_segment_each`;
- `test_a_glob_record_is_sent_with_its_slashes`;
- `test_an_upload_sends_the_file_as_its_part`;
- `test_a_raw_upload_sends_the_bytes_as_its_body`.

**Additions to existing modules** (no existing test or assertion edited):

- R gains `test_a_hyphenated_name_is_one_placeholder`, `test_route_writes_the_chosen_prefix` and
  `test_a_prefix_record_is_sent_only_under_a_prefix`.
- K gains `test_a_route_prefix_the_record_does_not_list_is_refused` and
  `test_a_hyphenated_name_is_documented_and_required`.
- P gains the property `test_route_accepts_only_the_records_prefixes`: AC-2.4 quantifies over every value a call can
  name. P's module docstring gains one sentence naming it.
- N gains `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written`, which pins D4's readings, and
  `test_only_the_upload_module_path_holds_a_hyphenated_name` (UB-4).

Correctness Properties gives each test's oracle.

### D8 — Files

| D | File | Change |
|---|---|---|
| D1, D2 | `src/payload/scripts/gitlab_api/registry.py` | `PLACEHOLDER`'s `name` group; `RestOperation.route_prefixes`; `ROUTE_PREFIX`, `takes_route_prefix`, `route`; `send` takes `prefix`; `expand` refuses a path that takes a route prefix; the module docstring's bullets and the docstrings of `placeholders`, `expand`, `send` and `route` |
| D3 | `src/payload/scripts/gitlab_api/commands/call.py` | `OPTION_ROUTE_PREFIX`, `ARG_ROUTE_PREFIX`, `METAVAR_PREFIX`, the `--route-prefix` option, `prepare_call`'s `route` step, `PreparedCall.prefix`, `send_call`'s `prefix`; the module docstring |
| D3 | `src/payload/scripts/gitlab_wrapper.py` | the module docstring's `call` usage lines name `--route-prefix PREFIX` and its refusal |
| D5, D6 | `src/payload/scripts/gitlab_api/families/package.py` | the records; the three prefix constants; `PENDING` the kept keys; both typed; the docstring |
| D4 | `test/test_gitlab_wrapper_contract.py` | `PATH_PLACEHOLDER`'s `name` group; `path_names` in #40's skip; `Section.route_prefixes` and its reading in `page_sections`; `prefix_problems` in `record_problems`; `call_prefix`, `record_call`'s `prefix`, `routed_section` and their use in the send test's loop; D7's two tests; the module docstring names the route prefix |
| D7 | `src/payload/test/test_gitlab_api_package.py` (F) | new |
| D7 | `src/payload/test/test_gitlab_api_registry.py` (R), `src/payload/test/test_gitlab_api_call.py` (K) | D7's additions |
| D7 | `test/test_gitlab_api_properties.py` (P) | D7's property and its docstring sentence |
| D3 | `docs/forLLMConsumption.md` | the `gitlab_api/` bullet's option list names `--route-prefix` |
| — | `docs/findings-ledger.md` | the Residuals' rows, written with `python scripts/memory_compile.py ledger add` |

**Not edited:** `gitlab_api/transport.py` (the raw body is #40's), `commands/_common.py` and every other line of
`commands/*`, `gitlab_wrapper_fixtures.py`, V, C and T.

### Sources

- `docs/api-reference/gitlab/rest/package.md`: the `<route-prefix>` lines under "Debian API", "npm API" and "NuGet
  API"; the entries the records name. `operations-index.md`: the References. `conventions.md`: "Offset-based",
  "Generic packages", "Other package formats".
- GitLab Workhorse, `gitlab-org/gitlab` `master`, `workhorse/internal/upstream/routes.go`, read 2026-11-11:
  - ``apiProjectPattern = apiPattern + `v4/projects/[^/]+` ``;
  - ``u.route("PUT", newRoute(apiProjectPattern+`/packages/maven/`, "projects_api_packages_maven", railsBackend),
    requestBodyUploader)``; `requestBodyUploader` also for the `PUT` patterns `` `/packages/npm/.*` ``,
    `` apiPattern+`v4/packages/conan/` ``, `` apiProjectPattern+`/packages/conan/` ``, `` `/packages/debian/` `` and
    `` `/packages/terraform/modules/` ``, and the `POST` pattern `` `/packages/rubygems/` ``;
  - `mimeMultipartUploader` for the `PUT` patterns `` `/packages/nuget/` `` and `` `/packages/nuget/v2` ``, and the
    `POST` patterns `` `/packages/pypi` `` and `` `/packages/helm/api/[^/]+/charts\z` ``;
  - `` apiProjectPattern+`/packages/npm/-/package/[^/]+/dist-tags/[^/]+` `` (`projects_api_packages_npm_dist_tags`) →
    `proxy`, before the npm upload route;
  - no route names `virtual_registries`; the last route an `/api/` path reaches is
    `u.route("", newRoute(apiPattern, "api", railsBackend), proxy)`.
- `workhorse/internal/upload/body_uploader.go` `RequestBody`, as #40 D5's Sources quote it.
- `gitlab-org/gitlab` `master`, read 2026-11-11: `lib/api/concerns/packages/npm_endpoints.rb` dist-tags `put`,
  `version = env['api.request.body']`; `lib/api/nuget_project_packages.rb` `requires :package, type:
  ::API::Validations::Types::WorkhorseFile`; `ee/lib/api/virtual_registries/packages/maven/endpoints.rb` `post
  'upload'`, `require_gitlab_workhorse!`; `authenticate_with` `sent_through(:http_basic_auth)` in
  `debian_package_endpoints.rb`, `helm_packages.rb`, `nuget_project_packages.rb` (and `API_KEY_HEADER`) and
  `rubygem_packages.rb` (and `:http_token`); `helpers/packages/conan/api_helpers.rb` `access_token_from_request` (a
  Conan JWT or HTTP Basic); `conan/shared_endpoints.rb` `unauthorized! unless token`.
- npm/cli `latest`, `lib/commands/dist-tag.js` `add`: `method: 'PUT'`, `body: JSON.stringify(version)`,
  `'content-type': 'application/json'`.
- docs.gitlab.com, read 2026-11-11: [Maven API](https://docs.gitlab.com/api/packages/maven/), [Debian
  API](https://docs.gitlab.com/api/packages/debian/), [Ruby gems API](https://docs.gitlab.com/api/packages/rubygems/),
  [Conan v1 API](https://docs.gitlab.com/api/packages/conan_v1/), [Conan v2
  API](https://docs.gitlab.com/api/packages/conan_v2/) and [Terraform Module Registry
  API](https://docs.gitlab.com/api/packages/terraform-modules/) upload with `--upload-file`; Debian's adds
  `?distribution=sid&component=main`; [npm API](https://docs.gitlab.com/api/packages/npm/) "Upload a package file":
  `--header "Content-Type: application/json" --data @./path/to/metadata/file.json`; [Project pull
  mirroring API](https://docs.gitlab.com/api/project_pull_mirroring/): "use the API to configure pull mirroring when
  creating or updating a project"; [Pull mirroring](https://docs.gitlab.com/user/project/repository/mirror/pull/):
  "Overwrite diverged branches" will "always update your local branches with remote versions, even if they have
  diverged from the remote".
- Python 3.9 [`re`](https://docs.python.org/3.9/library/re.html) `(?:...)`; [`dataclasses`
  ](https://docs.python.org/3.9/library/dataclasses.html) `replace`.

## Testing Strategy

- **Fake host.** `src/payload/test/gitlab_wrapper_fixtures.py`, unedited (#13, #41 D8). F and K judge a request by
  `FakeGitLab.requests`: the method, `url` as sent, the body bytes and its headers. They judge a refusal by `caplog`
  and "no request recorded", and read stdout with `capsys`.
- **Registry examples.** R works on synthetic `RestOperation`s, each built on one reference path.
- **Property.** P puts `src/payload/scripts` on `sys.path` and carries `@settings(deadline=None)`, as its existing
  properties do. Hypothesis stays in `test/`; the shipped suites stay pytest-only.
- **Contract and coverage.** N, as in D4; V, unedited. Both find the new records by discovery.
- **Regression.** C and the existing tests of K, R, T, P, N and V run unedited.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-forge check is #11's real-instance run on an ephemeral `sff-test-*` project (requirements Out of
  scope). Until it exists, N calls every record of this change, and F the prefix, hyphenated, glob, list and upload
  forms, through `main`'s argv against the fake host, up to the API boundary, in CI's `verify` job, leg `tests`. For a
  record #41 D5 calls unreachable (the three Debian pages, Go Proxy, Ruby gems, Protected packages), N's two tests are
  the whole proof (AC-4.3).

## Correctness Properties

Test files: F = `src/payload/test/test_gitlab_api_package.py` (new); R = `src/payload/test/test_gitlab_api_registry.py`;
K = `src/payload/test/test_gitlab_api_call.py`; T = `src/payload/test/test_gitlab_api_transport.py`;
C = `src/payload/test/test_gitlab_wrapper_compat.py`; P = `test/test_gitlab_api_properties.py`;
N = `test/test_gitlab_wrapper_contract.py`; V = `test/test_gitlab_wrapper_coverage.py`. Each entry gives the test's
kind and its oracle. "The configured project" is F's and K's `project_id` in `config/gitlab.json`; "the bytes" are a
file's bytes holding `\r\n` and `\xff`, which a text-layer read would translate or fail to decode.

- **AC-1.1**
  - Example, F `test_nothing_is_pending_but_the_kept_keys`. `package.PENDING` equals F's literal `KEPT`, and the sorted
    IDs of `package.OPERATIONS` equal F's literal `OPERATION_IDS`, each once: every `rest/package.md` Reference of the
    index but those of the two registry-host keys and of `("PUT", "/projects/:id/")`.
  - Structural, V `test_every_declared_key_is_in_its_family`: each record's method and path, verbatim, are on a row
    that carries its Reference.
- **AC-1.2** — Example, F `test_a_two_endpoint_entry_maps_its_first_endpoint`. For each ID of F's literal
  `FIRST_ENDPOINTS` (every Conan v1 entry, and `package#upload-a-package-file-5`), the record's `(method, path)` equals
  the entry's first endpoint and the entry's other key is in `package.PENDING`: `package#upload-a-package-file-5` is
  `PUT /projects/:id/packages/nuget`, and `("PUT", "/projects/:id/packages/nuget/v2")` is pending.
- **AC-1.3** — Example, F `test_nothing_is_pending_but_the_kept_keys`: both `/http(s)://${CI_REGISTRY}` keys and
  `("PUT", "/projects/:id/")` are in `package.PENDING`, and no record's path starts with `/http(s)://` or is
  `/projects/:id/`.
- **AC-1.4**
  - Structural, N `test_every_record_matches_its_reference_section`. Each `Param` matches its row by name and `In`
    (a raw-body record's section read through `documented_raw_body`), and every `query` and `body` row is declared.
  - Example, F `test_every_param_is_typed_as_its_row`:
    - `{operation_id: {name: kind name}}` over every non-`SCALAR` `Param` equals F's literal `KINDS`: the `string array`
      rows `components` and `architectures` of the Debian distribution create and update entries, the `array of
      string` and `object` rows, and the `file` rows but a raw-body record's;
    - `{operation_id: frozenset(required names)}` over the records with any equals F's `REQUIRED`;
    - `{operation_id: content_type}` over the records whose `content_type` is set equals F's `RAW_BODIES`, D5's raw-body
      records, and every `Param` of those is `Location.QUERY`;
    - every record has `body is BodyFormat.JSON` and `fixed == ()`.
- **AC-1.5**
  - Structural, F `test_no_param_names_a_path_parameter`: `package.OPERATIONS` is not empty, no `Param` name of any
    record is in `registry.placeholders(path=record.path)`, and `package#upload-module` has no `Param`.
  - Example, N `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written`: `record_problems` returns nothing for
    `package#upload-module` built with no `Param` and its `content_type`, though its entry has the `body` rows
    `module-name`, `module-system` and `module-version`.
- **AC-1.6** — Example, F `test_only_the_list_records_are_paged`: the IDs whose `paging` is `Paging.OFFSET` equal D6's
  paged records; each of those declares `Param(name="page", location=Location.QUERY)` and
  `Param(name="per_page", location=Location.QUERY)`; every other record is `Paging.NONE`.
- **AC-1.7** — F `test_nothing_is_pending_but_the_kept_keys`; on the merged tree, V
  `test_every_index_row_is_mapped_or_pending` and `test_every_declared_key_is_in_its_family`.
- **AC-2.1**
  - Structural, N `test_every_record_matches_its_reference_section` through `prefix_problems`: every record's
    `route_prefixes` equal its page's line, or `()` off a prefix path.
  - Example, N `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written`. The reader gives
    `package#list-all-dist-tags`, `package#download-a-distribution-release-file` and `package#search-for-packages` the
    npm, Debian and NuGet values in line order. `prefix_problems` names `package#list-all-dist-tags` built without
    `/packages/npm`, and `package#upload-a-package-file-4` built with the npm values.
  - Example, F `test_a_prefix_record_is_sent_under_each_of_its_values`: those three records' `route_prefixes` equal
    F's literal tuples.
- **AC-2.2, AC-2.3, AC-2.5 (sends)** — Parametrized example, F `test_a_prefix_record_is_sent_under_each_of_its_values`,
  one row per prefix value of one record of each prefix page. Oracle: exit 0, and the fake host's one recorded
  `(method, url)` equals the row's.

  | `call` argv after `call` | Sent |
  |---|---|
  | `package#list-all-dist-tags --path package_name=pkg --route-prefix /packages/npm` | `GET /api/v4/packages/npm/-/package/pkg/dist-tags` |
  | the same with `--route-prefix /groups/:id/-/packages/npm --path id=7` | `GET /api/v4/groups/7/-/packages/npm/-/package/pkg/dist-tags` |
  | the same with `--route-prefix /groups/:id/-/packages/npm --path id=my-group/sub` | `GET /api/v4/groups/my-group%2Fsub/-/packages/npm/-/package/pkg/dist-tags` |
  | the same with `--route-prefix /projects/:id/packages/npm`, no `id` | `GET /api/v4/projects/<project_id>/packages/npm/-/package/pkg/dist-tags` |
  | `package#download-a-distribution-release-file --path distribution=stable --route-prefix /projects/:id/packages/debian` | `GET /api/v4/projects/<project_id>/packages/debian/dists/stable/Release` |
  | the same with `--route-prefix /groups/:id/-/packages/debian --path id=7` | `GET /api/v4/groups/7/-/packages/debian/dists/stable/Release` |
  | `package#search-for-packages --query q=pkg --route-prefix /groups/:id/-/packages/nuget --path id=7` | `GET /api/v4/groups/7/-/packages/nuget/query?q=pkg` |
  | the same with `--route-prefix /projects/:id/packages/nuget`, no `id` | `GET /api/v4/projects/<project_id>/packages/nuget/query?q=pkg` |

  - Example, R `test_route_writes_the_chosen_prefix`, on a synthetic record on
    `/<route-prefix>/-/package/:package_name/dist-tags` with the npm values: each value gives a record whose path is
    the value followed by `/-/package/:package_name/dist-tags`; a record with no route prefix and `prefix=None` is
    returned itself.
- **AC-2.4, AC-2.5 (refusals)**
  - Parametrized example, K `test_a_route_prefix_the_record_does_not_list_is_refused`. Each case exits 2 with no
    request recorded:
    - `package#list-all-dist-tags --path package_name=pkg` with no `--route-prefix`: a log record names
      `/packages/npm`, `/projects/:id/packages/npm` and `/groups/:id/-/packages/npm`;
    - the same with `--route-prefix` `/projects/:id/packages/debian`, `/packages/npm/`, `/groups/7/-/packages/npm`
      and `C:/Program Files/Git/packages/npm`: a log record names the text given and the three values;
    - the same with `--route-prefix /packages/npm --path id=7`: a log record names `"id"` given with `--path` (as #41
      AC-2.2);
    - the same with `--route-prefix /groups/:id/-/packages/npm` and no `id`: a log record says `id` has no value;
    - `plan#retrieve-a-project-issue --path issue_iid=5 --route-prefix /packages/npm`, and K's synthetic
      `graphql#syntheticProject` with that option: a log record names the ID.
  - Property, P `test_route_accepts_only_the_records_prefixes`. The synthetic record of R's test; `prefix` drawn from
    `st.text() | st.sampled_from(elements=<the npm values>)`. A declared value gives the path of R's oracle; any other
    text raises `ValueError`. `@example` cases: `/packages/npm/`, `//packages/npm`, `https://other.example/packages/npm`
    and `""`.
  - Example, R `test_a_prefix_record_is_sent_only_under_a_prefix`. `expand` of the synthetic record unrouted raises
    `ValueError`. `send` with no `prefix` raises `ValueError` and records no request. `send` with
    `prefix="/groups/:id/-/packages/npm"` and `id=7`, `package_name=pkg` records one
    `GET …/api/v4/groups/7/-/packages/npm/-/package/pkg/dist-tags`.
- **AC-3.1**
  - Example, R `test_a_hyphenated_name_is_one_placeholder`. `placeholders` of
    `/projects/:id/packages/terraform/modules/:module-name/:module-system/:module-version/file` gives `("id",
    "module-name", "module-system", "module-version")`, and `expand` with `id=1`, `module-name=infra`,
    `module-system=aws` and `module-version=1.0.0` gives `/projects/1/packages/terraform/modules/infra/aws/1.0.0/file`.
    `/a/:name-/b` gives `("name",)` and `/a/:a-b-c` gives `("a-b-c",)`.
  - Example, F `test_the_hyphenated_names_are_sent_as_one_segment_each`: `call package#upload-module --path
    module-name=infra --path module-system=aws --path module-version=1.0.0 --input <the bytes>` sends one
    `PUT /api/v4/projects/<project_id>/packages/terraform/modules/infra/aws/1.0.0/file` whose body is the bytes.
  - Example, K `test_a_hyphenated_name_is_documented_and_required`. The same call without `--path module-system` exits
    2 with no request; its log record says `module-system` has no value and lists `id`, `module-name`,
    `module-system` and `module-version` as the path parameters. `--path module=infra` added is named undocumented.
  - Example, N `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written`: with every path value `v1`,
    `call_problems` returns nothing for `PUT /projects/v1/packages/terraform/modules/v1/v1/v1/file` on
    `package#upload-module`, and no "given but not sent" problem for `module-name`.
- **AC-3.2** — Example, F `test_a_glob_record_is_sent_with_its_slashes`:
  - `package#download-a-package-file-for-a-project --path path=com/example/app/1.0 --path file_name=app-1.0.jar` sends
    `GET /api/v4/projects/<project_id>/packages/maven/com/example/app/1.0/app-1.0.jar`;
  - the Debian rows of AC-2.2 are the glob under a prefix;
  - `--path path=com/../app` in place of the first `path` exits 1 with no request, a log record naming `*path` (#40
    AC-2.2);
  - the first call without `--path path` exits 2 with no request, a log record saying `path` has no value (#40 AC-2.4).
- **AC-3.3** — F `test_the_hyphenated_names_are_sent_as_one_segment_each` (the hyphenated names) and
  `test_a_glob_record_is_sent_with_its_slashes` (a glob without a prefix, and the Debian release file under one).
- **AC-4.1**
  - Structural, N `test_every_record_is_sent_as_its_section_documents` calls every record of this change, a prefix
    record under its page's first value.
  - Examples: the rows of AC-2.2 and AC-3.2 without `--path id` send to the configured project. The output rules are
    #41's, held by K's existing tests unedited.
- **AC-4.2**
  - Parametrized example, F `test_an_upload_sends_the_file_as_its_part`, over D5's `--file` records. Each is called
    with its path values, `--file <its FILE attribute>=<the bytes in tmp_path>` and each required body attribute with
    `-f`. Oracle: the row's method and URL; `Content-Type` `multipart/form-data`; the part named by the attribute
    carries a `filename` and the bytes; each `-f` attribute is a part with no `filename`, holding its text.
  - Parametrized example, F `test_a_raw_upload_sends_the_bytes_as_its_body`, over D5's raw-body records. Each is
    called with its path values and `--input <the bytes in tmp_path>`; `package#upload-a-package-file-2` with
    `--path file_name=mypkg.deb --query distribution=sid --query component=main`; `package#create-or-update-a-dist-tag`
    with `--path package_name=pkg --path tag=stable --route-prefix /projects/:id/packages/npm`, sent as
    `PUT /api/v4/projects/<project_id>/packages/npm/-/package/pkg/dist-tags/stable`. Oracle: exit 0; one recorded
    request with the row's method and URL, query included
    (`…/packages/debian/mypkg.deb?distribution=sid&component=main`); `Content-Type` `application/octet-stream`,
    `application/json` for `package#upload-a-package-file-4` and
    `package#create-or-update-a-dist-tag`; a body equal to the bytes. `package#upload-a-package-file-3` given
    `--file file=<the bytes>` in place of `--input` exits 2 with no request.
  - Held unedited from #40: K `test_a_raw_body_the_call_cannot_send_is_refused` (the third bullet's refusals) and
    `src/payload/test/test_gitlab_api_deploy.py` `test_the_upload_sends_the_bytes_as_its_body` (`--input -`); F's
    `RAW_BODIES` fixes which records of this change take `--input`.
- **AC-4.3**
  - Structural: N `test_every_record_matches_its_reference_section` and
    `test_every_record_is_sent_as_its_section_documents` over every record, the unreachable ones included.
  - Example, N `test_a_route_prefix_and_a_hyphenated_name_are_read_as_written`. On
    `routed_section(section=<package#list-all-dist-tags>, prefix="/groups/:id/-/packages/npm")` with every value `v1`,
    `call_problems` returns nothing for `GET /groups/v1/-/packages/npm/-/package/v1/dist-tags`, and names the path for
    `/<route-prefix>/-/package/v1/dist-tags` and for `/projects/v1/packages/npm/-/package/v1/dist-tags`. The
    `prefix_problems` cases are AC-2.1's.
- **AC-4.4** — Parametrized example, F `test_a_list_record_prints_every_page`, one case per paged record of D6.
  - Pages are scripted with `FakeGitLab.script` at the record's expanded URL: the first with `per_page=MAX_PER_PAGE`,
    answering an `x-next-page`; the second with `page` set to that value, answering an empty one.
  - Oracle: stdout equals `print_json` of both pages' items in order; every scripted response was served; exit 0.
- **UB-1** — C passes with every existing case unedited, and the PR diff changes no line of C.
- **UB-2**
  - P `test_standard_library_only` scans the entry script and the package, `registry.py`, `commands/call.py` and
    `families/package.py` among them.
  - C `test_load_config_refusals` and `test_environment_token_ignored`, K `test_call_takes_no_token_option` (which
    reads `--route-prefix` too), and T `test_next_url_on_another_origin_is_refused` and
    `test_cross_origin_redirect_drops_credentials` pass unedited.
  - P `test_route_accepts_only_the_records_prefixes`: no text but a declared value reaches the path.
- **UB-3** — `src/payload/test/test_github_api_*.py` and `src/payload/test/test_wrapper_delivery.py` pass in CI's
  `tests` leg, and the PR diff names no file of UB-3.
- **UB-4**
  - Example, N `test_only_the_upload_module_path_holds_a_hyphenated_name`. For every row of `operations-index.md`,
    `registry.placeholders(path=row.path)` equals the names that the test's literal copy of #40's pattern,
    `[:*](?P<name>[A-Za-z_][A-Za-z0-9_]*)`, finds in the path; the row of `package#upload-module` instead gives `("id",
    "module-name", "module-system", "module-version")`.
  - Example, R `test_a_hyphenated_name_is_one_placeholder`: `binary-:architecture` holds `architecture`,
    `:package_name$:sha` holds `package_name` and `sha`, and `:module_version.info` holds `module_version`.
  - Example, R `test_route_writes_the_chosen_prefix`: `/<route-prefix>/symbolfiles/:file_name/:signature/:file_name`
    under `/projects/:id/packages/nuget`, with `id=1`, `file_name=a.pdb` and `signature=s`, expands to
    `/projects/1/packages/nuget/symbolfiles/a.pdb/s/a.pdb`.
  - Every existing test of `src/payload/test/test_gitlab_*.py`, P, N and V passes; the PR diff edits no existing
    assertion and no `GATED_OPERATIONS` entry.

## Security Considerations

- **The route prefix cannot redirect the request.**
  - The path is written from the prefix value the record holds, chosen by exact text equality with the call's
    `--route-prefix`. Any other text, the empty text and a URL included, is refused with nothing sent (D2, D3).
  - Each `:id` of the value is then one percent-encoded segment (`_segment`, `quote(safe="")`), so a value cannot add
    a `/`, `?` or `#`, and `.` and `..` are refused (#13 AC-2.2).
  - The URL is `https://<hostname>/api/v4` followed by the root-relative path (`Transport._rest_url`), and `_send`
    refuses any other origin (#13 D4). No prefix and no path value changes the host.
- **The hyphenated name** is template text only: the pattern reads where a name ends, and its value is written as
  before. The `-` and the name characters it admits are the template's, never a value's.
- **The raw body** is #40 D5's, unchanged: `request_raw` sends through `_send`, whose origin check and one credential
  header are unchanged; each raw-body record is a `PUT` or a `POST`, and `CredentialStrippingRedirectHandler` follows
  a redirect of neither (#13 D4 "Redirects"). #40's Residual on an `--input` naming `config/gitlab.json` holds here.
- **The credential** comes from `config/gitlab.json` only and travels in its header (UB-2). No option contains
  `token`. The upstream-registry `password` rows (container and Maven virtual registries: create, update and test an
  upstream) are body values given with `-f`. They show in the command line, as #41 Residuals "Secrets in arguments"
  records, and travel in the JSON body, never in the URL that an error quotes.
- **What stays callable**, gated by none, as #41 Security "Destructive operations" makes running one the caller's
  decision:
  - every `DELETE`: packages and package files, registry repositories and their tags
    (`package#delete-registry-repository-tags-in-bulk` among them), protection rules, Debian distributions, virtual
    registries, upstreams and their caches, `package#purge-the-dependency-proxy-for-a-group`, Conan recipes, npm
    dist-tags and NuGet packages;
  - `package#create-an-authentication-token` and `…-1`: Conan reads only its JWT or HTTP Basic, so with the
    configured header GitLab answers 401 and issues no token (Sources);
  - the routes of the Debian, Go Proxy, Ruby gems and Protected packages pages, whose `Offering:` lacks GitLab.com; an
    instance that does not offer one answers it with an HTTP error, which exits 1 (#41 D4).
- **Gates.** `GATED_OPERATIONS` and the hooks are unchanged. #41's gated class is a record that commits to or merges
  into a branch, or creates an issue; no record of this change commits, merges or creates an issue. The project-update
  key `PUT /projects/:id/`, which can configure a pull mirror that overwrites the trunk, stays pending (AC-1.3).
- **Dependencies.** None added. The shipped code stays Python 3.9 standard library, with no subprocess.

## Operability

The GitLab wrapper is not installed in this repository: `config/toolchain.json` `not_installed` lists
`src/payload/scripts/gitlab_wrapper.py`, "the repository is on GitHub", so no session here runs these records. They
reach a project through the setup prompts' copy of `gitlab_api/` (#13 D2). Nothing deploys, and no configuration or
migration changes. A route prefix the record does not list, none for a prefix record, or one for any other record is
refused as #41 refuses an undocumented parameter: logged to standard error naming the record's values, exit 2, nothing
sent. A shell that rewrites an argument delivers a value no record lists, and the call is refused the same way: Git
Bash on Windows rewrites `/packages/npm`, which holds no `:`, into `C:/Program Files/Git/packages/npm`, while the
values holding `:id` reach the wrapper unchanged (Residuals).

## Residuals

- The `requirements.md` Residuals stand; its first three are one findings-ledger row each (D8).
- Git Bash on Windows rewrites `--route-prefix /packages/npm` into a Windows path, so the npm instance prefix is
  refused from it (Operability) → one findings-ledger row.
- `package#upload-a-package-file-5` and `package#upload-a-package` reach Rails through Workhorse's catch-all `proxy`
  (D5), so GitLab refuses their `WorkhorseFile` part, and `package#upload-a-package` is Workhorse-only
  (`require_gitlab_workhorse!`). The records stand for AC-1.1, but no `call` uploads through them → one
  findings-ledger row.
- The Conan, Debian, NuGet, Helm and Ruby gems routes read no header the transport sends (only HTTP Basic, a Conan
  JWT, `X-NuGet-ApiKey` or a bare `Authorization` token), so their calls are unauthenticated and a write is refused;
  an HTTP Basic credential form is outside this change (UB-2) → one findings-ledger row.
