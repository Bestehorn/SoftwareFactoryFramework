# Design — issue #13: GitLab wrapper rewrite, part 1 (foundation)

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (frozen once review opens). Parent #11, part 2 #15, GitHub sibling
#17: the same structure; every remaining difference is a row of "Differences from #17" with its forge reason.

## Overview

The skeleton `src/payload/scripts/gitlab_wrapper.py` becomes a thin entry script beside a standard-library package,
`src/payload/scripts/gitlab_api/`: one transport for REST v4 and GraphQL that applies
`docs/api-reference/gitlab/conventions.md` and `graphql/conventions.md`, a registry of declarative operation records
looked up by id, one module per endpoint family holding that family's records and pending list, and discovered command
modules that serve exactly UB-1's subcommands from those records. The setup prompts copy the package with the entry
script. A framework test reads `docs/api-reference/gitlab/operations-index.md` and fails for every row that no record
maps and its family's pending list does not name. Callers keep invoking `scripts/gitlab_wrapper.py`;
`src/payload/test/test_wrapper_delivery.py` is not edited.

## Design

### D1 — The operation layer is a mix (AC-1.1)

| Part | Serves | Where |
|---|---|---|
| Generic, reference-driven: one frozen record per mapped row (`RestOperation`; `GraphQLOperation` for GraphQL), written from the row's `rest/<stage>.md` attribute table and looked up by id through `registry` | every mapped row — in part 1 exactly the rows UB-1's subcommands use (D6); part 2 (#15) adds the rest as records | `gitlab_api/registry.py`, `gitlab_api/families/<family>.py`, `gitlab_api/graphql_only.py`, `gitlab_api/transport.py` |
| Hand-written compatibility subcommands | exactly UB-1's set: the docstring's subcommands and the caller-used forms marked † in `requirements.md` UB-1; each handler composes records and owns its argv, output and exit code | `gitlab_api/commands/`; the delivery verbs stay `steward_delegate` in the entry script |

Why: the reference tables already give method, path, attribute location and type, so a record is transcription, and
the encoding, paging, credential and error rules are written once (part 2 is then data entry); UB-1's subcommands are
multi-call workflows with caller-fixed argv and exit codes (`issue start` verifies a claim, `claim-check` exits 3,
`pipeline wait` exits 10/11), which no record expresses. #17 makes the same split, so the two wrappers are one design.

### D2 — Layout (AC-1.2, AC-1.3)

```
src/payload/scripts/
  gitlab_wrapper.py              entry: usage docstring, import bootstrap, _load_config, main, steward_delegate and
                                 the delivery constants; installs as scripts/gitlab_wrapper.py
  gitlab_api/
    __init__.py
    errors.py                    GitLabAPIError, GitLabRateLimitError, GitLabGraphQLResponseError, GitLabClaimError
    transport.py                 config-key constants, TokenType, origin, CredentialStrippingRedirectHandler, Transport
    registry.py                  Param, Kind, BodyFormat, Paging, RestOperation, GraphQLOperation; discover_families,
                                 lookup, expand, encode, call, pages
    graphql_only.py              OPERATIONS of GraphQLOperation records (empty in part 1)
    families/__init__.py
    families/<family>.py         FAMILY, OPERATIONS, PENDING — one per family of operations-index.md
    commands/__init__.py
    commands/_common.py          JSON output, shared argument helpers, shared FIELD_* keys (not a command module)
    commands/{pipeline,issue,label,mr,branch}.py   register(subparsers) + handlers (D6)
src/payload/test/
  gitlab_wrapper_fixtures.py     FakeGitLab; loaded by path, not collected
  test_gitlab_api_transport.py   transport.py
  test_gitlab_api_registry.py    registry.py
  test_gitlab_wrapper_compat.py  commands/ and the entry script
test/
  test_gitlab_wrapper_coverage.py        the AC-5 coverage test (the index exists only in this repository)
  test_gitlab_api_properties.py          the AC-2.2 and AC-2.3 Hypothesis properties, the UB-2 import scan
  test_setup_prompts_gitlab_wrapper.py   the install path below
```

**Install path (product text, edited in this change).** `prompts/setup-claude.txt` Part 5.3 and
`prompts/setup-kiro.txt` Part 6.2 copy `src/payload/scripts/gitlab_wrapper.py` together with the directory
`src/payload/scripts/gitlab_api/` into `scripts/`, and each prompt's "Shipped Python" list names `scripts/gitlab_api/`
beside `scripts/gitlab_wrapper.py`; `test/test_layout.py` `test_every_framework_path_named_in_a_live_file_exists`
resolves the new path, and `test/test_setup_prompts_gitlab_wrapper.py` pins both copy steps and both lists (each
section cut from its heading to the next `###` heading, as `test/test_setup_prompts_gitignore.py` cuts PART 3). In the
same parts the GitLab text is restated, as #17 D8 restates the GitHub text:

- The "skeletons" sentence (Part 5.3 "The wrapper templates are skeletons; implement the subcommands the project's
  agents invoke."; Part 6.2 "The template wrapper scripts are skeletons. The agent should extend them … (see the
  docstring in each template)") no longer covers GitLab: the GitLab wrapper serves the minimum set below except the
  issue metadata and the checklist toggle, which arrive in a later framework release; a project that needs them sooner
  adds a module of `scripts/gitlab_api/commands/` defining `register(subparsers)`. The GitHub half of the sentence is
  #17's.
- Part 5.3's pointers to "the expanded docstrings" name `src/payload/scripts/gitlab_api/` for GitLab (the endpoints
  are its records; `commands/mr.py`'s docstring carries the own-MR approval caveat); the checklist bullet's "(See the
  wrapper docstrings.)" stays true, those notes being kept in the entry script (D7). Part 6.2's "the template
  docstrings specify them" (the blocking wait, the delivery verbs) stays true: the usage docstring keeps those notes.
- The setup-kiro APPENDIX "Standard directory structure" lists `gitlab_api/  # if GitLab` beside `gitlab_wrapper.py`
  under `scripts/`.

The `_comment` of `templates/config/gitlab.json.template` documents `token_type` (D7); its keys are unchanged.

**Family module contract.** A row's family is the file stem of its Reference link with `-` replaced by `_`
(`rest/ai-coding.md#…` → `families/ai_coding.py`, `rest/openapi-only.md#…` → `families/openapi_only.py`) — the slices
#11's work items name. `FAMILY` is the stem (`ai-coding`); the file name is `FAMILY` with `-` replaced by `_`. Every
stem the index links has a module, also when it has no record. `OPERATIONS` holds that family's records; `PENDING`
(a frozenset) holds the `(method, path)` keys of its rows that no record maps — the per-family file of AC-5.2. A key
whose rows link to two families (`GET /projects` under `developer-experience` and `tenant-scale`) belongs to the
family whose module name sorts first: only that module maps it or lists it in `PENDING`, and the coverage test treats
it as that family's for every row carrying the key.

**Discovery, not a list.** `registry.discover_families(*, package=gitlab_api.families)` walks
`pkgutil.iter_modules(package.__path__)` in sorted name order, imports each as `package.__name__ + "." + name`, and
caches per package (the AC-1.2 test passes a synthetic package from `tmp_path`); the entry script discovers
`gitlab_api.commands` the same way, skipping `_`-prefixed modules and calling each module's `register`
(https://docs.python.org/3.9/library/pkgutil.html#pkgutil.iter_modules; the pattern of `src/hooks/hooks.py`
`discover_gates`, which finds a `gate_*.py` by its being there and declaring its names). No file lists the families or
the command modules. Every package directory has an `__init__.py`, so mypy (`run_checks.py` `types`, `mypy src`) names
the modules `gitlab_api.…` and they cannot collide with #17's `github_api`.

**What a family's change edits (AC-1.2, AC-1.3):**

| File | Edited when | Why it is shared |
|---|---|---|
| `gitlab_api/families/<family>.py` | always: its records, its `PENDING` | not shared |
| `src/payload/test/test_gitlab_api_<family>.py` | always: one test module per family (part 2) | not shared |
| `gitlab_api/graphql_only.py` | a GraphQL-only capability gets a record (#15) | the capabilities belong to no family |
| `gitlab_api/transport.py` | a family needs a request form part 1 does not build (Residuals), with its tests in `test_gitlab_api_transport.py`; one commit, landed before the family's | one request path is AC-2's purpose |
| `gitlab_api/registry.py` | a family needs a record type, field or enum member part 1 lacks (a raw-bytes body, GraphQL multipart), with its tests in `test_gitlab_api_registry.py`; one commit, landed first | one set of record types is what `lookup` and the coverage test read |
| `gitlab_api/errors.py` | a family needs an error type the module lacks; own commit, landed first | one exception hierarchy under `GitLabAPIError` |
| `gitlab_api/commands/_common.py` | a command module needs a printing or `FIELD_*` helper it lacks; own commit, landed first | the JSON printing and the shared keys exist once |
| `src/payload/test/gitlab_wrapper_fixtures.py` | a family's test needs a fake-host behaviour the module lacks; own commit, landed first | every suite installs the one fake host |
| never: `gitlab_wrapper.py`, the three `__init__.py`, the existing `commands/<group>.py` modules, `test/test_gitlab_wrapper_coverage.py` | — | discovery by scan; UB-1's groups are fixed and a command-line path to other records is a new `commands/` module (#15 AC-4); the coverage test reads the union |

### D3 — Import bootstrap

`python scripts/gitlab_wrapper.py` puts `scripts/` first on `sys.path`; a test loading the file with
`importlib.util.spec_from_file_location` (`test_wrapper_delivery.py` `load`) does not. The entry script inserts
`Path(__file__).resolve().parent` at the front of `sys.path` when absent, then imports `gitlab_api` absolutely, those
imports marked `# noqa: E402`. Precedent: `src/hooks/hooks.py` and `src/hooks/supervisor.py` bootstrap the same way.
Imports follow a statement because the shipped scripts are copied, not installed (`pyproject.toml`
`[tool.setuptools] packages = []`). Loading the module has no other effect: no config read, no request, no logging
set-up. `gitlab_wrapper.GitLabAPIError` stays importable. Shipped code stays Python 3.9: no `match`, no
`dataclass(slots=…, kw_only=…)`; `from __future__ import annotations` for `X | None` annotations.

### D4 — Transport (`gitlab_api/transport.py`; AC-2, AC-3, AC-4)

**Exceptions (`errors.py`).** `GitLabAPIError(message, status_code=0, details=None)` — the skeleton's signature — with
`GitLabRateLimitError` (AC-3.4), `GitLabGraphQLResponseError` (AC-4.3) and `GitLabClaimError` (`issue start`) as
subclasses (`coding-standards.md` items 5, 6 and 9).

**Constants.** The config keys (`FIELD_HOSTNAME`, `FIELD_PROJECT_ID`, `FIELD_TOKEN`, `FIELD_TOKEN_TYPE`,
`FIELD_IN_PROGRESS_LABEL`), `CREDENTIAL_HEADERS` (`Private-token`, `Job-token`, `Authorization`: the spelling
`Request.add_header` stores and `Request.remove_header` matches exactly), `MAX_PER_PAGE`
(the documented maximum, `conventions.md` "Offset-based"), `RATE_LIMIT_MAX_RETRIES`, `BACKOFF_BASE_SECONDS`,
`REQUEST_TIMEOUT_SECONDS`.

**URLs and origin.** REST is `https://<hostname>/api/v4<path>`; GraphQL is `https://<hostname>/api/graphql`
(`conventions.md` "Hosts and base URLs"). `origin(url)` builds `Request(url=url)` and takes its `type` and `host` —
the scheme and authority urllib's `AbstractHTTPHandler.do_open` connects with — splits the port after the last `:`
outside `[...]` as `http.client.HTTPConnection` does, lower-cases scheme and host, and uses the scheme's default port
when none is given (443 for `https`, 80 for `http`: `http.client`'s `default_port`; any other scheme has none,
`None`, so its origin never equals the configured one); an empty port counts as absent,
and a port that is not an integer raises `GitLabAPIError` naming the URL. The configured origin is `origin` of the
REST base. Two URLs share an origin only when the three parts are equal: never a string prefix, never a second parser
(`https://<host>@evil.example/` has `host` `<host>@evil.example`, another origin).

**`Transport(*, host, token, token_type, opener=None, sleep=time.sleep, clock=time.monotonic)`**;
`Transport.from_config(*, config)` reads the config keys. `opener` defaults to
`urllib.request.build_opener(CredentialStrippingRedirectHandler())`, the module's only opener factory.

- **`_send(method, url, data, headers)`** is the one send. A URL whose origin is not the configured one raises
  `GitLabAPIError` naming it, before anything is sent. It sets `Accept: application/json`, `Content-Type` when there
  is a body, and the credential (below) with `Request.add_header`, so the redirect handler decides on every hop.
- **Credentials (AC-2.1).** `TokenType` maps `token_type` to one header: `private` (the default, UB-2) →
  `PRIVATE-TOKEN: <token>`, `bearer` → `Authorization: Bearer <token>`, `job` → `JOB-TOKEN: <token>`
  (`conventions.md` "Credential types and how to send them"). The token never enters a URL, argv, a log record or an
  exception message.
- **`request(method, path, *, query=(), json_body=None, form=None, files=None) -> Response`.** `query` and `form` are
  name–value pairs (D5 `encode` builds them), joined by `urllib.parse.urlencode(pairs, safe="[]",
  quote_via=urllib.parse.quote)`, so brackets stay literal and `+` is sent as `%2B` (`conventions.md` "Arrays, hashes
  and arrays of hashes", "`+` in dates"; `safe` and `quote_via`: https://docs.python.org/3.9/library/urllib.parse.html).
  `json_body` is sent with `json.dumps` and `Content-Type: application/json`. `Response` holds status, headers and
  body; its value is JSON when the `Content-Type` is JSON, text otherwise (the job trace), `None` when empty
  (`conventions.md` "Responses").
- **Multipart (AC-2.4).** With `files`, the body is `multipart/form-data` with a boundary from `secrets.token_hex(16)`
  (inside RFC 2046 §5.1.1's boundary length limit, which the argument-less default is not guaranteed to respect):
  each file part under its field name with the file's name and `application/octet-stream`, and every `form` pair as a
  field (`conventions.md` "Query string or body": multipart is "required when a file is attached"). Field names and
  file names are written with `"`, CR and LF as `%22`, `%0D`, `%0A` (the HTML `multipart/form-data` encoding
  algorithm, https://html.spec.whatwg.org/#multipart-form-data).
- **`pages(path, *, query=(), paging)`** — a generator yielding the items of each page's JSON array in page order,
  fetching a page only when the previous one is exhausted. OFFSET (AC-2.5) sends `per_page=MAX_PER_PAGE` unless the
  query already holds `per_page`; after each page it follows the `Link` header's `rel="next"` URL as given, else
  re-issues the first request with `page=<x-next-page>`; it stops when both are absent or empty and never reads
  `x-total-pages` (`conventions.md`: "Loop on `x-next-page` (or `rel="next"`) until it is absent, never on
  `x-total-pages`"). KEYSET (AC-2.6) follows only `Link` `rel="next"`, unchanged, until none is sent
  (`conventions.md` "Keyset-based": "follow its `rel="next"` URL unchanged … At the end the `Link` header
  disappears"). The `rel` is read with the pattern `<([^>]*)>\s*;\s*rel="([^"]*)"`, so a comma inside a URL does not
  split it. A next URL on another origin is refused by `_send` and never fetched.
- **Redirects (AC-3.1).** `CredentialStrippingRedirectHandler(urllib.request.HTTPRedirectHandler)` overrides
  `redirect_request`: a method other than `GET` or `HEAD` is not followed (the `HTTPError` stands, so a `POST` never
  becomes a `GET`); otherwise it calls the parent and, when `origin` of the target differs from `origin(req.full_url)`
  of the request that received the redirect (never its `host`, which `ProxyHandler` rewrites to the proxy's), removes
  every `CREDENTIAL_HEADERS` name with `Request.remove_header` (both header maps). The parent copies headers from
  the hop it follows, so a credential removed on one hop stays absent on every later hop, back on the configured host
  too; a same-origin hop (a moved project's `301`, `conventions.md` "Redirects for moved or renamed projects") keeps
  it. Sources: Python docs `HTTPRedirectHandler.redirect_request`, `Request.remove_header`
  (https://docs.python.org/3.9/library/urllib.request.html); `conventions.md` "Do not forward the token" (urllib copies
  every header but `Content-Length` and `Content-Type`). Dropping `Authorization` as well closes the requirements'
  `Authorization: Bearer` residual by the same mechanism. A `308` is followed only on Python 3.11+
  (`http_error_308`); the redirect tests use `301` and `302`.
- **`429` (AC-3.2–AC-3.4).** `_send` retries a `429` up to `RATE_LIMIT_MAX_RETRIES` consecutive times: with an
  integer `Retry-After` it sleeps that many seconds; without one it sleeps `BACKOFF_BASE_SECONDS * 2 ** (n - 1)` for
  the n-th consecutive `429`. Each retry logs one WARNING with the status and the sleep in seconds, never a request
  header. When the retries are spent it raises `GitLabRateLimitError` with `status_code` 429. Sources: `conventions.md`
  "Headers and the 429 response" ("wait `Retry-After` seconds … back off exponentially"); "Rate limiting responses for
  the Projects, Groups, and Users APIs do not include informational headers"
  (https://docs.gitlab.com/user/gitlab_com/rate_limits/).
- **Errors (AC-3.5).** An `HTTPError` (a response with `code`, `headers` and a readable body,
  https://docs.python.org/3.9/library/urllib.error.html) becomes `GitLabAPIError(message, status_code=code,
  details=<raw body text>)`. `error_text(body)` builds the message for each `conventions.md` "Body shapes" entry:
  `message` string → itself; `message` hash (validation, the spam hash) → `field: message` pairs, lists joined, nested
  hashes flattened with dotted names; `error` with optional `error_description` (the OAuth scope error adds its
  `scope`) → `error: description`; a GraphQL `errors` list → its messages; a non-JSON body → the text. A redirect the
  handler does not follow raises the same way with its 3xx status. A failure without a response — `OSError`
  (`URLError`, `TimeoutError`, `ConnectionError`), `http.client.HTTPException`, or a `ValueError` raised while urllib
  resolves or opens a redirect's `Location`, all caught after `HTTPError` — raises `GitLabAPIError` with
  `status_code` 0.
- **GraphQL (AC-4.1–AC-4.3).** `graphql(document, variables)` POSTs `{"query": document, "variables": variables}` as
  JSON to the GraphQL URL (`graphql/conventions.md` "Endpoint and request shape") through `_send`, so origin, redirects,
  `429` and HTTP errors behave as for REST. The credential is always `Authorization: Bearer <token>`, the only header
  the GraphQL pages document; a `job` token raises `GitLabAPIError` before sending ("job tokens cannot authenticate
  GraphQL requests", `graphql/conventions.md` "Credentials"). A non-empty top-level `errors`, or — when the document's
  operation type is `mutation` — any top-level `data` value whose `errors` list is non-empty (the mutation payload),
  raises `GitLabGraphQLResponseError` with the joined messages, the HTTP status and the body as `details`, whatever the
  status and whether `data` is present (`graphql/conventions.md` "Errors and partial data"); otherwise it returns
  `data`. `graphql_nodes(document, variables, connection)` (`connection`: the key path under `data`) sends
  `after: null`, then `after` = `pageInfo.endCursor` while `pageInfo.hasNextPage` is true, and returns the `nodes` of
  every page in order (`graphql/conventions.md` "Connections and cursor pagination"); a `null` connection raises
  `GitLabAPIError` ("absent or forbidden").

### D5 — Registry and records (`gitlab_api/registry.py`)

```python
@dataclass(frozen=True)
class Param:
    name: str                    # the attribute as the reference table spells it
    location: Location           # QUERY or BODY (path parameters come from the path template)
    kind: Kind = Kind.SCALAR     # SCALAR, ARRAY, HASH, ARRAY_OF_HASHES, FILE — the table's Type column
    required: bool = False

@dataclass(frozen=True)
class RestOperation:
    operation_id: str            # the row's Reference target without `rest/` and `.md`: `plan#update-an-issue`
    method: str                  # the row's Method
    path: str                    # the row's Path, verbatim: `/projects/:id/issues/:issue_iid`
    params: Tuple[Param, ...] = ()
    body: BodyFormat = BodyFormat.JSON        # JSON or FORM; multipart whenever a FILE value is passed
    paging: Paging = Paging.NONE              # NONE, OFFSET, or KEYSET (only where the endpoint offers keyset only)
    fixed: Tuple[Tuple[str, str], ...] = ()   # query values the endpoint requires on every call

@dataclass(frozen=True)
class GraphQLOperation:
    operation_id: str            # for a GraphQL-only capability (#15)
    document: str
    connection: Tuple[str, ...] = ()          # key path to a paged connection under `data`, or empty
```

- `(method, path)` of a `RestOperation` is the key the coverage test matches. `Kind` separates a documented array or
  hash from a comma-separated string (`labels` is `string`, `assignee_username` is `string array`; `rest/plan.md`
  "List all project issues"; `conventions.md`: "the per-endpoint type column decides").
- `lookup(operation_id)` over every family's `OPERATIONS` and `graphql_only.OPERATIONS`, raising `ValueError` for an
  unknown or twice-declared id.
- `expand(operation, values)` (AC-2.2) replaces each `:name` with `urllib.parse.quote(str(value), safe="")`, so
  `group/project` becomes `group%2Fproject` (`conventions.md` "URL-encoding path parameters", which names
  `quote(value, safe="")` and warns that the default `safe="/"` is wrong). An empty value, `.` or `..` raises
  `GitLabAPIError` (each would not be one segment once dot segments are resolved); a missing value raises `ValueError`.
- `encode(operation, values)` (AC-2.3) turns QUERY and FORM values into pairs by `Kind` — SCALAR `name=v` (booleans
  `true`/`false`), ARRAY `name[]=a`, `name[]=b`, HASH `name[k]=v`, ARRAY_OF_HASHES `name[0][k]=v` — adds `fixed`,
  gives JSON BODY values as a native `dict`, and FILE values (`pathlib.Path`) as `files`. A value whose name is neither
  a path placeholder nor a declared `Param` raises `ValueError` before any request.
- `call(transport, operation_id, *, values=None)` — a `RestOperation` → `transport.request(...).value`; a
  `GraphQLOperation` → `transport.graphql` or, with a `connection`, `transport.graphql_nodes`, `values` as variables.
  `pages(transport, operation_id, *, values=None)` → the generator `transport.pages(..., paging=operation.paging)`.

### D6 — Compatibility commands (`gitlab_api/commands/`; UB-1)

Each command module's `register(subparsers)` adds its argv group with argparse's defaults; its handlers take
`(*, transport, project, in_progress_label, args)` and return `None` (exit 0) or an exit code. `_common.py` holds
the JSON printing (`json.dumps(..., indent=2)` to standard output) and the shared argument helpers. Records are named
by id; `:id` is always `project`.

| Argv (module) | Records | Requests | Output; exit |
|---|---|---|---|
| `pipeline status [--count N]` (`pipeline`) | `verify#list-project-pipelines` | `order_by=id`, `sort=desc`, `per_page=N` (default 1); the first N items | the pipelines; 0 |
| `pipeline log` | `verify#list-project-pipelines`, `verify#list-all-jobs-by-pipeline`, `verify#retrieve-a-log-file-for-a-job` | the latest pipeline; its jobs with `scope[]=failed`; each such job's trace | per failed job a header line and its trace, or one line saying none failed or no pipeline exists; 0 |
| `pipeline wait <id> --timeout-seconds N` | `verify#retrieve-a-single-pipeline` | `pipeline_wait` polls every `interval_seconds` (`transport.sleep`) until a status in `PIPELINE_TERMINAL_STATUSES` or the deadline (`transport.clock`) | the skeleton's summary line; 0, `EXIT_WAIT_NOT_SUCCESS`, `EXIT_WAIT_TIMEOUT` |
| `issue list [--state S] [--assignee A] [--labels L]` (`issue`) | `plan#list-all-project-issues` | `state=S`; `A` `*` → `assignee_id=Any`, `none` → `assignee_id=None`, else `assignee_username[]=A`; `labels=L`; every page | the issues; 0 |
| `issue show <iid>` | `plan#retrieve-a-project-issue` | — | the issue; 0 |
| `issue create --title T [--description D] [--labels L]` | `plan#create-an-issue` | `title`, `description`, `labels` | the issue; 0 |
| `issue comment <iid> --body B` | `plan#create-an-issue-note` | `body` | the note; 0 |
| `issue start <iid>` | `plan#retrieve-a-project-issue`, `software-supply-chain-security#as-a-regular-user-1` (`GET /user`), `plan#update-an-issue` | `GitLabClaimError`, no PUT, when not `opened` or assigned to another user; one PUT `add_labels=<label>`, `assignee_ids=[me]`; re-read; `GitLabClaimError` with the observed labels and assignees unless the label is present and `me` is assigned | the verified issue; 0, else 1 |
| `issue claim-check <iid>` | `plan#retrieve-a-project-issue` | read only | `{iid, state, claimed}`; 0 when not `opened` or the label or any assignee is present, else `EXIT_CLAIM_UNCLAIMED` (3) |
| `issue release <iid>` | `plan#update-an-issue` | `remove_labels=<label>`, `assignee_ids=[0]` | the issue; 0 |
| `issue label-add <iid> --labels L` / `issue label-remove <iid> --labels L` | `plan#update-an-issue` | `add_labels=L` / `remove_labels=L` — never `labels` | the issue; 0 |
| `issue assign <iid> --me` \| `--user U` \| `--unassign` (one required) | `software-supply-chain-security#as-a-regular-user-1`, `software-supply-chain-security#as-a-regular-user` (`GET /users`, `username=U`; no match → `GitLabAPIError`), `plan#update-an-issue` | `assignee_ids=[id]`, or `[0]` | the issue; 0 |
| `issue close <iid>` | `plan#update-an-issue` | `state_event=close` | the issue; 0 |
| `issue reopen <iid>` | `plan#retrieve-a-project-issue`, `plan#update-an-issue` | an `opened` issue is printed with no PUT; else `state_event=reopen` | the issue; 0 |
| `label list` (`label`) | `plan#list-all-project-labels` | every page | the labels; 0 |
| `label create --name N --color C [--description D]` | `plan#create-a-project-label` | `name`, `color`, `description` (`name`, `color` required: `rest/plan.md` "Create a project label") | the label; 0 |
| `mr create --source B --target T --title X` (`mr`) | `ai-coding#create-a-merge-request` | `source_branch`, `target_branch`, `title`, `remove_source_branch=true` | the MR; 0 |
| `mr get <iid>` / `mr checks <iid>` | `ai-coding#retrieve-a-merge-request` / `ai-coding#list-merge-request-pipelines` | — / every page | the MR / its pipelines; 0 |
| `mr approve <iid>` | `ai-coding#approve-merge-request` | — | the approval; 0; a refusal (own MR, the caveat `commands/mr.py`'s docstring carries) is a `GitLabAPIError` → 1 |
| `mr merge <iid>` | `ai-coding#merge-a-merge-request` | `should_remove_source_branch=true` | the MR; 0 |
| `delete-branch <branch>` (`branch`) | `create#delete-repository-branch` | the branch as one encoded segment | `{branch, deleted: true}`; 0 |

Body values go as JSON (`assignee_ids` is an integer array, `rest/plan.md` "Update an issue", where `0` unassigns).
These are the only records part 1 declares; every other row of the index is on its family's `PENDING`.

### D7 — Entry script (`gitlab_wrapper.py`; UB-1, UB-2)

- **`_load_config()`** keeps its checks — a missing file, or an empty or `PASTE_` value in `hostname`, `project_id`
  or `token`, raises `GitLabAPIError` — and adds: a `token` holding any character outside `!` to `~` (printable
  ASCII without the space) raises `GitLabAPIError` naming the key, never the value; `in_progress_label` defaults to
  `in-progress`; `token_type` is optional (`private`, `bearer`, `job`; absent → `private`; another value →
  `GitLabAPIError`). It reads `config/gitlab.json` only, with the key constants of `transport.py`; nothing reads an
  environment variable, and `token` stays the key `merge_steward.read_token` reads. The template's `_comment` and the
  usage docstring document `token_type` as the `_comment` already does `in_progress_label`.
- **Kept unchanged:** `STEWARD_SCRIPT`, `DELIVERY_CONFIG`, `DELIVERY_VERBS`, `EXIT_DELIVERY_ELSEWHERE`,
  `steward_delegate`. **Removed:** `_api_request`, the skeleton's `pipeline_wait` (rebuilt in `commands/pipeline.py`
  with the same exit constants and output), its field constants, and its implementation-notes comment block except
  the issue-metadata and checklist-toggle notes (due date, time spent, parent link, `toggle_checklist_item`), which
  stay as a comment in the entry script until #15 builds those subcommands. The usage docstring lists UB-1's whole set,
  keeps the skeleton's exit-code notes for `pipeline wait` and the delivery verbs, and its SSO sentence names
  `gitlab_api/transport.py` as the extension point.
- **`main(argv=None) -> int`** (`None` reads `sys.argv[1:]`):
  1. Reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with `errors="replace"` where the stream has `reconfigure`
     (on Windows a pipe uses the ANSI code page, so a job trace could not be printed otherwise).
  2. A first argument in `DELIVERY_VERBS` → `steward_delegate(verb=…, args=<the rest of argv, unparsed>, token=…,
     host="gitlab")` with the token from `_load_config()`; its code is returned.
  3. Otherwise parses with a parser holding every discovered command module (a usage error exits 2 through argparse),
     loads the config, builds `Transport.from_config(config=…)` and calls the handler; `None` → 0.
  4. A `GitLabAPIError` (any subclass) logs its message, then `details`, and returns 1.
- `__main__` calls `logging.basicConfig(...)` (diagnostics to standard error) and `sys.exit(main())`.

### D8 — Coverage test (`test/test_gitlab_wrapper_coverage.py`; AC-5, AC-1.2)

It lives in `test/` because only this repository has `docs/api-reference/`; it puts `src/payload/scripts` on
`sys.path` and imports `gitlab_api.registry`.

- `index_rows(path)` — every row of the `operations-index.md` table whose first cell is an HTTP method, as
  `(method, path, reference)`; a table line it cannot parse fails the test.
- `coverage_gaps(rows, mapped, pending)` — a pure function returning, sorted, every row whose key is neither a
  record's `(method, path)` nor in the `PENDING` of the key's family (D2); the failure message groups the gaps by family
  module as `PENDING` tuple literals.
- The real test reads `discover_families()`; a synthetic families package in `tmp_path` (on `sys.path` by
  `monkeypatch.syspath_prepend`, passed as `package=`), under a package name unique to the test, with one
  `discover_families` call per package after its files are written, tests discovery and `coverage_gaps`. A
  `socket.socket.connect` guard is installed for every test of the module.

### Data flow

`python scripts/gitlab_wrapper.py issue start 7` → `main` (UTF-8 streams) → parser (the `issue` module registered
the group) → `_load_config` → `Transport.from_config` → handler →
`registry.call(transport=transport, operation_id="plan#retrieve-a-project-issue", values=…)`
→ `expand`/`encode` → `Transport.request` → `_send` (origin check, credential header, `429` retry) → opener with
`CredentialStrippingRedirectHandler` → `HTTPError` → `GitLabAPIError` | decoded value → handler → JSON on standard
output → exit code.

### Existing patterns followed

`GitLabAPIError(message, status_code, details)` and the exit-1 mapping of the skeleton's `__main__`; `FIELD_*`
constants for every JSON key, each defined once: the config keys in `transport.py` (the entry script imports them), a
response key in the one module that reads it, and a key more than one command module reads in `commands/_common.py`
(`coding-standards.md` item 1); named arguments at every call site (`coding-standards.md` item 4); the
skeleton's wait exit constants and output; `steward_delegate` unchanged; loading a script by path in tests
(`test_wrapper_delivery.py` `load`); discovery by declared names (`hooks.discover_gates`); the import bootstrap of
`hooks.py`. `merge_steward.http_json`/`GitLabAPI` is not reused: it pages until a short page, retries only 5xx and
always sends `PRIVATE-TOKEN`, which AC-2.1, AC-2.5 and AC-3.2–AC-3.4 contradict, and the steward ships as an
independent file this change leaves untouched. Deviation: a multi-file wrapper where one file was copied (D2's install
path).

### Differences from the GitHub sibling #17

| Point | GitLab (this) | GitHub (#17) | Forge reason |
|---|---|---|---|
| Family key, record id | the row's `rest/<stage>.md` stem; id `<stem>#<anchor>` from the Reference link | operation-ID prefix; `operationId` | the GitLab index has no operation IDs |
| Coverage unit | method-and-path key | operation IDs and the "Only in GraphQL" capabilities | GitLab AC-5.1 reads `operations-index.md` only |
| `graphql_only.py` | `OPERATIONS` only, empty in part 1 | with `PENDING_CAPABILITIES` | same |
| Paging | `NONE`, `OFFSET` (`Link` or `x-next-page`), `KEYSET` (`Link` only) | `NONE`, `LINK` | GitLab offset pages also signal by `x-next-page`; AC-2.6's keyset-only endpoints |
| Parameters | `Param` with a `Kind` | name sets, `multi_segment` | GitLab documents bracket encodings (AC-2.3); glob path forms are #15's |
| Request bodies | `json_body`, `form`, `files` keywords | one `body` | GitLab bodies are form or multipart as well (AC-2.3, AC-2.4) |
| Command modules | a family never edits an existing `commands/<group>.py` | `commands/<group>.py` edited when a covered operation joins a group | #15 AC-4 reaches mapped records through one new module; UB-1's groups are fixed |
| Credential | `config/gitlab.json`; three header types | `credentials/github-pat.txt`; `Authorization` | AC-2.1 |
| Rate limit | `429`: `Retry-After`, else exponential back-off | `403`/`429`: `retry-after`, `x-ratelimit-*` | each forge's documented limit |
| Version, files | `v4` in the URL; multipart (AC-2.4) | `X-GitHub-Api-Version`; release-asset upload | each forge's conventions |
| Delivery verbs | all six passed unparsed | three parsed with the fork's arguments | GitLab has no fork whose arguments to keep |
| Config refusal exit | 1 | 2 | UB-1: a `GitLabAPIError` exits 1; the GitHub fork exits 2 |
| Handler context; output | `project`, `in_progress_label`; JSON of the result | `owner`, `repo`; the fork's output | config versus remote; no GitLab fork is installed, so there is no parity test either |

## Testing Strategy

- **Fake host** — `src/payload/test/gitlab_wrapper_fixtures.py`, loaded by path as `test_wrapper_delivery.load` loads
  a wrapper. `FakeGitLab` is installed with `monkeypatch` over `urllib.request.HTTPSHandler.https_open` and
  `urllib.request.HTTPHandler.http_open`, so every opener in the process reaches it and no socket opens. It serves
  scripted `(status, headers, body)` responses per method and URL in order, as `urllib.response.addinfourl` objects
  with `msg` set and an `http.client.HTTPMessage` (`HTTPErrorProcessor.http_response` reads `code`, `msg`, `info()`),
  so urllib's error processor and redirect machinery and the wrapper's handler run unchanged. It records each request
  (method, URL, headers, body), and an unscripted request is recorded and then raises `AssertionError` (not an
  `OSError`, which `_send` converts). Every shipped suite (T, R and C) installs `FakeGitLab` and a
  `socket.socket.connect` guard as autouse fixtures.
- **Transport and registry** — `src/payload/test/test_gitlab_api_transport.py` (`transport.py`) and
  `src/payload/test/test_gitlab_api_registry.py` (`registry.py`) put `Path(__file__).resolve().parents[1] / "scripts"`
  on `sys.path` before importing `gitlab_api`; `Transport` gets a recording `sleep` and a fixed `clock` and keeps
  `opener` at its default, so the redirect tests exercise the opener `from_config` builds.
- **Subcommands** — `src/payload/test/test_gitlab_wrapper_compat.py`: `config/gitlab.json` in `tmp_path` (chdir),
  `main(argv=…)`, standard output by `capsys`, the exit code from the return value or `SystemExit`; `pipeline_wait`
  also directly, with a `Transport` holding a fake clock and sleep. Two subprocess tests run `sys.executable
  <scripts dir>/gitlab_wrapper.py` with `cwd=tmp_path`, proving the bootstrap when the script is run.
- **Framework tests** (`test/`, not shipped, CI's Python 3.10): the coverage test (D8);
  `test_gitlab_api_properties.py` (which puts `src/payload/scripts` on `sys.path` as D8 does) with the Hypothesis
  properties (Hypothesis is this repository's dev extra) and the UB-2 import scan (`sys.stdlib_module_names`, Python
  3.10+, https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names); `test_setup_prompts_gitlab_wrapper.py`.
  The shipped suites under `src/payload/test/` stay pytest-only and Python 3.9.
- **Unchanged** — `src/payload/test/test_wrapper_delivery.py` runs as it is.
- **Where it runs** — CI's `tests` group (`run_tests.py` over `pyproject.toml` `testpaths`: `src/payload/test`,
  `test`); locally `python scripts/run_tests.py <these files>`.
- **E2E: not applicable** — nothing deployed changes; the real-instance run stays on #11 (`requirements.md`).

## Correctness Properties

- **AC-1.1** — review: D1 names the mix and what each part serves. Example: `registry.call` with an undeclared value
  name raises `ValueError` and nothing is recorded; `lookup` raises `ValueError` for an unknown and a twice-declared id.
- **AC-1.2** — example: `discover_families(package=<synthetic package>)`, one call per package, under a package name
  unique to the test, after its files are written, returns a module added to its directory with no other file changed;
  oracle: the family set equals the module files present.
- **AC-1.3** — review: D2's table names each shared file with its reason.
- **AC-2.1** — example per token type: the recorded request carries exactly one of `Private-token`, `Authorization`,
  `Job-token`, with the expected value.
- **AC-2.2** — property: for any non-surrogate text `v` other than `.` and `..`, the expanded segment contains no `/`
  and `unquote(segment) == v`; examples: `group/project` → `group%2Fproject`; `""`, `.` and `..` raise
  `GitLabAPIError`. `@given(st.text(alphabet=st.characters(exclude_categories=("Cs",)), min_size=1))`
- **AC-2.3** — property, over non-surrogate text: for any list, `parse_qsl(query, keep_blank_values=True)` of the
  encoded query is `[("k[]", x) for x in list]` in order; for any dict of identifier keys, the `k[key]` pairs of the
  same `parse_qsl(query, keep_blank_values=True)` equal the dict; examples: an array of hashes gives `k[0][a]=…`; a
  JSON body holds the list and object natively.
- **AC-2.4** — example: a FILE value yields a `multipart/form-data` body whose file part has the field name, the file
  name and the file's bytes, and each other value is a field; a file name containing `"` is written `%22`.
- **AC-2.5** — example: page 1 → 2 by `x-next-page`, 2 → 3 by `Link`, page 3 sends `x-next-page:` empty, all with a
  wrong `x-total-pages`; a second case leaves the header out on the last page; oracle: the items of all three pages in
  order, and no fourth request (the fake fails on one).
- **AC-2.6** — example: keyset pages; oracle: each follow-up URL equals the `Link` `rel="next"` URL byte for byte,
  paging stops when `Link` is absent, and a next URL on another origin raises `GitLabAPIError` naming it with nothing
  fetched.
- **AC-3.1** — example, for each token type: a `302` to each of `https://<host>.evil.example/`,
  `https://<host>@evil.example/`, `http://<host>/`, `https://<host>:8443/`; oracle: the redirected request carries
  none of the three credential headers (names compared case-insensitively). A same-host `301` (also as
  `https://<HOST>:443/`) keeps the configured one; a chain host → foreign → host carries none on the return hop.
- **AC-3.2** — example: `429` with `Retry-After` then `200`; oracle: one sleep of that value, then the result.
- **AC-3.3** — example: two or more consecutive header-less `429`s, then `200`; oracle: the sleeps strictly increase.
- **AC-3.4** — example: `429` on every attempt; oracle: `GitLabRateLimitError` (a `GitLabAPIError`) with
  `status_code == 429` after `RATE_LIMIT_MAX_RETRIES` sleeps.
- **AC-3.5** — example per `conventions.md` body shape; oracle: `status_code` the status, `details` the raw body, and
  the message contains the shape's text: `404 Project Not Found`; `bio: is too long (maximum is 255 characters)`;
  `glql_yaml is missing, glql_yaml is empty`; `insufficient_scope: ` followed by the fixture's `error_description`;
  `error: Your snippet has been recognized as spam and has been discarded.`; the plain-text body.
- **AC-4.1** — example; oracle: one `POST` to `https://<host>/api/graphql` whose JSON body has `query` and
  `variables`.
- **AC-4.2** — example: two pages; oracle: the second request's `variables.after` is the first `endCursor`; the
  result is both pages' nodes.
- **AC-4.3** — examples: HTTP `200` with top-level `errors` and partial `data`, and a mutation payload with `errors`,
  raise `GitLabGraphQLResponseError` carrying the messages; a mutation payload with `errors: []` and a query result
  whose object has an `errors` field (`ciConfig`) return their data.
- **AC-5.1** — example: synthetic rows against synthetic families; oracle: `coverage_gaps` names exactly the rows
  neither mapped nor pending.
- **AC-5.2** — the AC-1.2 discovery example; oracle: the pending sets come from each module and no list of families
  exists in the code.
- **AC-5.3** — the coverage test over the real index passes.
- **AC-5.4** — the coverage test passes with the `socket.socket.connect` guard installed.
- **UB-1** — one case per argv form — each `/` and `|` alternative of D6 and each optional flag UB-1 lists
  (`--count N`, `--description D`, `--assignee` `*`, `none` and a username, `--user U`, `--unassign`, `label-remove`,
  `mr checks`) — each asserting the exact recorded requests (method, URL with query, JSON body), standard output and
  exit code. `claim-check` 0 (label), 0 (assignee), 0 (closed), 3 (open, unclaimed), 1 (404), 2 (no iid);
  `pipeline wait` 0, 10, 11 (`--timeout-seconds 0`); `issue start` 1 with no PUT for a closed issue and for an issue
  assigned to another user, and 1 when the re-read lacks the label; `issue reopen` 0 with no PUT on an open issue; a
  delivery verb through `main` returns the steward's code (4) with its arguments unparsed (`dequeue-pr 77 --reason x`).
  Subprocess: a usage error exits 2; without `config/gitlab.json` the exit is 1, and standard error contains
  `str(Path("config") / "gitlab.json")` and no `Traceback`. The setup-prompts test: both GitLab copy steps name
  `src/payload/scripts/gitlab_api/` with the entry script, and both "Shipped Python" lists name `scripts/gitlab_api/`.
  `test_wrapper_delivery.py` passes unchanged.
- **UB-2** — examples: a template-keys config sends `Private-token` and claims with `in-progress`; a missing file, a
  `PASTE_` value, and a token with a trailing newline or a zero-width space raise `GitLabAPIError` (the last two:
  neither the message nor `details` contains the value); a `GITLAB_TOKEN` set with monkeypatch is never sent. Static
  (properties module): every import of the entry script and the package is `gitlab_api…` or in
  `sys.stdlib_module_names`, and neither contains `os.environ` or `getenv`; the scanned set includes
  `gitlab_wrapper.py`, `gitlab_api/transport.py` and `gitlab_api/registry.py`.
- **UB-3** — verifier evidence: `git diff --name-only` against the merge base lists neither
  `src/payload/scripts/github_wrapper.py` nor any GitHub wrapper test nor `src/payload/test/test_wrapper_delivery.py`.

## Security Considerations

- **Token placement** — headers only, never the `private_token`/`job_token`/`access_token` URL parameters
  (`conventions.md` "Credential types"); no request header is logged; `GitLabAPIError` carries the response body, never
  the request; a token holding any character outside `!` to `~` is refused at load without being echoed. A `job` token
  is read from `config/gitlab.json` like any other; `CI_JOB_TOKEN` is never read (UB-2).
- **The credential reaches the configured origin only** — origins are compared by urllib's own parse (D4); `_send`
  refuses any other origin, so a `Link` next URL elsewhere (including `file:` or `ftp:`) is never fetched; across a
  redirect the credential survives only origin-to-origin hops and, once dropped, stays dropped; an `https`→`http` hop
  is another origin. Non-`GET`/`HEAD` redirects are not followed.
- **Input** — path values are single encoded segments, and an empty value, `.` or `..` is refused; multipart field and
  file names are escaped and the boundary is random; response bodies are parsed with `json.loads` only.
- **GraphQL** — a job token is refused before any request; GraphQL errors at HTTP `200` raise instead of returning
  partial data.
- **Steward token** — unchanged: stdin only (`test_wrapper_delivery.py`).

## Operability

Not applicable — no deployed service; the wrapper is a command-line script whose diagnostics (including each `429`
retry) go to the logger on standard error.

## Acceptance Criteria Mapping

T = `src/payload/test/test_gitlab_api_transport.py`, R = `src/payload/test/test_gitlab_api_registry.py`,
C = `src/payload/test/test_gitlab_wrapper_compat.py`,
V = `test/test_gitlab_wrapper_coverage.py`, P = `test/test_gitlab_api_properties.py`,
S = `test/test_setup_prompts_gitlab_wrapper.py`, D = `src/payload/test/test_wrapper_delivery.py`.

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1; `registry.call`, `lookup` | review; R `test_call_refuses_an_undeclared_value`, `test_lookup_refuses_unknown_and_duplicate_ids` |
| AC-1.2 | D2; `registry.discover_families` | V `test_a_family_module_is_discovered_alone` |
| AC-1.3 | D2 table | review |
| AC-2.1 | `TokenType`, `Transport._send` | T `test_one_credential_header_per_token_type` |
| AC-2.2 | `registry.expand` | P `test_path_value_is_one_segment`; R `test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused` |
| AC-2.3 | `registry.encode`, `Transport.request` | P `test_array_and_hash_pairs`; R `test_array_of_hashes_pairs`; T `test_json_body_is_native` |
| AC-2.4 | `Transport.request` multipart | T `test_file_value_sends_multipart` |
| AC-2.5 | `Transport.pages` OFFSET | T `test_offset_paging_follows_next_and_ignores_total_pages` |
| AC-2.6 | `Transport.pages` KEYSET, `_send` | T `test_keyset_paging_follows_link_unchanged`, `test_next_url_on_another_origin_is_refused` |
| AC-3.1 | `origin`, `CredentialStrippingRedirectHandler` | T `test_cross_origin_redirect_drops_credentials` (parametrized), `test_same_origin_redirect_keeps_credential`, `test_credential_stays_dropped_on_return_hop` |
| AC-3.2 | `Transport._send` | T `test_429_waits_retry_after` |
| AC-3.3 | `Transport._send` | T `test_429_without_headers_backs_off_increasingly` |
| AC-3.4 | `GitLabRateLimitError` | T `test_429_after_retries_raises` |
| AC-3.5 | `error_text`, `Transport._send` | T `test_error_shape_raises_gitlab_api_error` (parametrized) |
| AC-4.1 | `Transport.graphql` | T `test_graphql_posts_to_api_graphql` |
| AC-4.2 | `Transport.graphql_nodes` | T `test_graphql_pages_by_end_cursor` |
| AC-4.3 | `GitLabGraphQLResponseError` | T `test_graphql_errors_at_200_raise`, `test_empty_payload_errors_and_query_errors_fields_return_data` |
| AC-5.1 | `index_rows`, `coverage_gaps` | V `test_checker_names_each_unlisted_row` |
| AC-5.2 | `registry.discover_families`, `PENDING` | V `test_a_family_module_is_discovered_alone` |
| AC-5.3 | every `families/<family>.py` | V `test_every_index_row_is_mapped_or_pending` |
| AC-5.4 | coverage test | V `test_every_index_row_is_mapped_or_pending` (socket guard) |
| UB-1 | `commands/*`, `gitlab_wrapper.main`, the setup prompts | C `test_a_subcommand_form` (one case per form), `test_claim_check_exit_codes`, `test_pipeline_wait_exit_codes`, `test_issue_start_refusals`, `test_issue_reopen_of_open_issue`, `test_delivery_verb_through_main`, `test_script_usage_error_exits_2`, `test_script_without_config_exits_1`; S `test_both_prompts_copy_the_package_with_the_entry`; D unchanged |
| UB-2 | `_load_config`, `Transport.from_config` | C `test_template_config_sends_private_token`, `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` |
| UB-3 | the diff | verifier `git diff --name-only` evidence |

## Residuals

- Toolchain manifest (this repository): the first promotion of a release with this change adds `not_installed` entries
  `src/payload/scripts/gitlab_api/*`, `src/payload/test/gitlab_wrapper_fixtures.py`, `src/payload/test/test_gitlab_*.py`
  ("the repository is on GitHub") before it runs `scripts/toolchain_manifest.py` → one findings-ledger row (conductor).
- Request forms part 1 does not build, added to `transport.py`/`registry.py` by the family needing one: `*name` globs
  (their values keep `/`, which AC-2.2's one-segment rule does not allow), optional `(…)` segments, `<route-prefix>`
  and `https://HOST` paths, a raw-bytes body (generic packages), GraphQL multipart → #15.
- The "Only in GraphQL" capabilities are outside this AC-5 → #15 AC-2/AC-3, records in `gitlab_api/graphql_only.py`.
- A `Retry-After` or back-off can outlast a bounded `pipeline wait` timeout; AC-3.2 sets no cap → ledger if observed.
- `token_type` `bearer` or `job` does not reach the steward, which sends every token as `PRIVATE-TOKEN`
  (`merge_steward.GitLabAPI`) → conductor to route.

## User Prompts

- The run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end" (`/auto-work`).
- Issue #13 title: "GitLab wrapper rewrite, part 1: design, core transport, today's subcommands, coverage test".
- The operator's ask, as the issue quotes it: "The operator asked to split #11 and its GitHub sibling #12 into two
  children each: a foundation, then the remaining coverage."
