# Design — issue #17: GitHub wrapper rewrite, part 1 (design, core transport, today's subcommands, coverage test)

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-5.3, UB-1.1..UB-3.2, frozen). Decisions:
`decisions/decision-log.md` DL-001; cross-wrapper decisions X1–X5 (`review/review-latest.md`, shared with #13).

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end"
- Issue #17: "GitHub wrapper rewrite, part 1: design, core transport, today's subcommands, coverage test"
- The operator's ask, relayed in issue #17: "The operator asked to split #12 and its GitLab sibling #11 into two
  children each: a foundation, then the remaining coverage. (relayed; original request in #12)"

## Overview

`src/payload/scripts/github_wrapper.py` becomes a thin entry script beside a standard-library package,
`src/payload/scripts/github_api/`: one transport for REST and GraphQL, a registry of declarative operation records,
one module per operation family holding that family's records and pending list, and command modules that rebuild
every caller-used subcommand of the fork on those records. The delivery verbs stay in the entry script as the
skeleton has them. A coverage test in `test/` checks the records and pending lists against
`docs/api-reference/github/`. The setup prompts' GitHub copy steps copy the package with the entry script (D8), so
a project set up from the next release gets a working wrapper (`design-principles.md` item 3). Nothing is promoted
here: this repository's sessions keep running the fork (`config/toolchain.json` `deviations`).

## Design

### D1 — The operation layer is a mix (AC-1.1)

- **Generic part — every operation.** Each REST operation of `operations-index.md` and each "Only in GraphQL"
  capability is served by a declarative record (`RestOperation`, `GraphQLOperation`, D4). A record is data: the
  index row it covers (operation ID, method, path template), its documented parameters, its paging kind and item
  key. A record is the "wrapper call" whose declaration makes an operation covered (requirements Glossary). Part 1
  declares exactly the records the compatibility commands use (D5 table); part 2 (#14) adds the rest.
- **Hand-written part — exactly UB-1.1's caller-used set**, in `github_api/commands/`, each command composing
  records and printing the fork's output. Nothing outside that set is hand-written.
- **Why a mix.** Records alone cannot reproduce the fork's outputs and multi-call flows (`cmd_start_issue`'s
  verifying re-read, `cmd_get_pr_checks`' merge of three responses, `cmd_list_issues`' pull-request filter and
  limit). Hand-written code alone gives the index no machine link to the code, so AC-5 would rest on names, and
  puts all of part 2 into bespoke functions. With records, each index row is one line of data that the coverage
  test checks against the row it names, and part 2 is mostly data.
- The GitLab wrapper (#13) is designed to the same structure under its own sibling package, so the two wrappers
  are one design.

### D2 — Layout (AC-1.2, AC-1.3, UB-1.3)

```
src/payload/scripts/
  github_wrapper.py            entry script; installs as scripts/github_wrapper.py (UB-1.3)
  github_api/
    __init__.py
    errors.py                  GitHubAPIError and its subclasses (X2)
    transport.py               origin(), redirect handler, Transport (D3)
    registry.py                record types, discovery, lookup, path expansion, call/pages (D4)
    graphql_only.py            GraphQL capability records + PENDING_CAPABILITIES (AC-1.3)
    families/__init__.py
    families/<family>.py       FAMILY, OPERATIONS, PENDING — one per family of operations-index.md
    commands/__init__.py
    commands/_common.py        body resolution, JSON printing, the FIELD_* constants the command modules share
                               (the fork's names); not a command module
    commands/{issues,claim,pulls,ci}.py   register(subparsers) + handlers (D5)
src/payload/test/
  github_wrapper_fixtures.py   fake host + golden case table; loaded by path, not collected
  test_github_api_transport.py   test_github_api_registry.py   test_github_wrapper_compat.py
test/
  test_github_wrapper_coverage.py   test_github_wrapper_fork_parity.py   test_setup_prompts_github_wrapper.py
prompts/setup-claude.txt, prompts/setup-kiro.txt   the GitHub copy steps (D8)
```

**Family module contract.** `FAMILY` is the operation-ID prefix (`code-scanning`); the file name is `FAMILY` with
`-` replaced by `_`. `OPERATIONS` holds only records of that family; `PENDING` (a frozenset) holds only that
family's operation IDs that no record covers. Every family of the index has a module, including families with no
record. The "Only in GraphQL" capabilities, which belong to no family, are pending in
`github_api/graphql_only.py` `PENDING_CAPABILITIES`, beside that module's `OPERATIONS` of `GraphQLOperation`
records.

**Discovery, not a list.** `registry.discover_families()` walks `pkgutil.iter_modules(github_api.families.__path__)`
in sorted name order and imports each module by its absolute name; the entry script discovers `github_api.commands`
the same way, skipping `_`-prefixed modules and calling each module's `register`. This is the pattern of the hook
runtime's gate discovery (`src/hooks/hooks.py`: a `gate_*.py` is found by being there and declaring its names).
No file lists the families or the command modules.

**What a family's change edits:**

| File | Edited when | Why it is shared |
|---|---|---|
| `github_api/families/<family>.py` | always: its records and its `PENDING` | not shared |
| `src/payload/test/test_github_api_<family>.py` | always: one new test module per family (part 2) | not shared |
| `github_api/graphql_only.py` | an "Only in GraphQL" capability is covered | the capabilities are one table with no family |
| `github_api/commands/<group>.py` | a covered operation joins an existing command group; a new group is a new module | one group's arguments are one parser |
| `github_api/commands/_common.py` | a command needs a body, printing or `FIELD_*` helper it lacks | the fork's `_resolve_body`, JSON printing and field names exist once |
| `github_api/errors.py` | an operation needs an error type the module lacks | one exception hierarchy under `GitHubAPIError` (X2) |
| `github_api/registry.py` | the record types lack a field an operation needs | one record type is what the coverage test reads |
| `github_api/transport.py` | an operation needs a request mechanic the transport lacks | one request path is AC-2's purpose |
| `src/payload/test/github_wrapper_fixtures.py` | a family's test needs a fake-host response the module lacks | every suite installs the one fake host |
| never: `github_wrapper.py`, `families/__init__.py`, `commands/__init__.py`, `test/test_github_wrapper_coverage.py` | — | discovery by scan; the coverage test reads the union |

### D3 — Transport (`github_api/transport.py`, `github_api/errors.py`; AC-2, AC-3, AC-4)

**Exceptions (X2).** `errors.py` holds `GitHubAPIError(message, status_code=None, details=None)` — the fork's
signature — and its subclasses `GitHubRateLimitError` and `GitHubGraphQLResponseError`, named with the base prefix
as the fork names `GitHubRedirectRefusedError` (`coding-standards.md` items 5, 6 and 9).

**Constants.** `API_ROOT`, `GRAPHQL_URL`, `UPLOAD_ORIGIN` (`https://uploads.github.com`; `conventions.md` "Hosts and
base URLs"), `ACCEPT_JSON`, `USER_AGENT`, `API_VERSION_DEFAULT = "2022-11-28"`, `API_VERSION_NEXT = "2026-03-10"`,
`API_VERSIONS`, `CREDENTIAL_HEADERS = ("Authorization",)` (the only credential header the transport sets),
`RATE_LIMIT_STATUSES` (`403`, `429`), `RATE_LIMIT_MAX_RETRIES`, and one `FIELD_*` constant for every JSON field the
transport reads or writes (`coding-standards.md` item 1).

**Origin (X5).** `origin(url)` builds `Request(url=url)` and takes its `type` and `host` — the scheme and authority
urllib's `AbstractHTTPHandler.do_open` connects with — splits the port after the last `:` outside `[...]` as
`http.client.HTTPConnection` does, lower-cases scheme and host, and uses the scheme's default port when none is given
(443 for `https`, 80 for `http`: `http.client`'s `default_port`). Two URLs are the same origin only when the three
parts are equal, so a URL carrying userinfo never matches the API's. A port that is not an integer — which the last
`:` of a `user:password@` part also yields — raises `GitHubAPIError` naming the URL, where `HTTPConnection` raises
`http.client.InvalidURL`, which is no `ValueError`; an empty port counts as absent, as in `HTTPConnection`. It is
computed for every URL the transport opens and for every redirect target.

**Redirects.** `CredentialStrippingRedirectHandler(HTTPRedirectHandler)` overrides `redirect_request`, the
stdlib's one point that builds the redirected `Request` (Python docs, `HTTPRedirectHandler.redirect_request`). It
calls the parent, then, when `origin` of the target differs from `origin(url=req.full_url)` of the request that
received the redirect (never its `host`, which `ProxyHandler` rewrites to the proxy's), removes every
`CREDENTIAL_HEADERS` name with `Request.remove_header`, which removes it from both the regular and the unredirected
headers (Python docs). **Same origin keeps `Authorization`** — the decision the
requirements leave to this design: the target is the token's own audience, and `conventions.md` "Redirects in
general" says to use a `301`'s new URL (a renamed repository). A redirected request copies its headers from the hop
it follows, so a credential removed on one hop is absent on every later hop, back on the API host too.
`transport.build_opener()` returns `urllib.request.build_opener(CredentialStrippingRedirectHandler())` and is the
module's only opener factory; this is the fork's `_NoRedirectHandler` strip, made origin-conditional.

**`Transport(token, *, opener=None, sleep=time.sleep, clock=time.time)`** — `opener` defaults to `build_opener()`.

- `_send(method, url, data, headers, rest, allowed_origin)` is the one send. Before sending it refuses, with
  `GitHubAPIError`, a URL whose `origin` is not `allowed_origin` — `API_ROOT`'s, or `UPLOAD_ORIGIN` for `upload` —
  the fork's `next_page_path` and `_expand_upload_url` guards made exact. It sets `Accept`,
  `Authorization: Bearer <token>` (with `add_header`, so the redirect handler decides), `User-Agent`,
  `Content-Type` when there is a body, and `X-GitHub-Api-Version` on every REST request (`conventions.md` "Headers,
  media types and API versions").
- `request(method, path, query=None, body=None, api_version=API_VERSION_DEFAULT, accept=ACCEPT_JSON)` — `path`
  must start with `/` and not `//` (the fork's guard); the URL is `API_ROOT + path`, plus
  `urlencode(query, doseq=True)`; any body other than `None` is JSON, on `DELETE` too (`conventions.md` "Request
  encoding"). An `api_version` outside `API_VERSIONS` raises `ValueError` before anything is sent. It returns a
  `Response` (status, headers with lower-cased names, body bytes; `.json()` gives `None` for an empty body, as the
  fork).
- `pages(path, query=None, item_key=None, api_version=...)` is a generator yielding items in page order. The next
  URL is the `rel="next"` target of the `link` header, parsed with the pattern `<([^>]*)>\s*;\s*rel="([^"]*)"` (a
  `rel` may list several values), so a comma inside a URL (`labels=bug,ui`) does not split it. The target is sent
  exactly as given, after the origin check; an absent header or no `next` ends the list (`conventions.md`
  "Pagination"). With `item_key`, each page's items are the list under that key; a page without the key raises
  `GitHubAPIError`.
- `upload(upload_url, name, data, media_type, label=None)` — the URL is `upload_url` cut at its first `{`, with
  `name` (and `label` when given) urlencoded as the query; body the bytes, `Content-Type` the media type
  (`conventions.md` "Uploads and binary request bodies").
- `download(path)` — a REST `GET` returning bytes; a `302` to a storage host is followed without the credential.
- `graphql(document, variables)` — `POST` of `{"query": document, "variables": variables}` to `GRAPHQL_URL`, with
  no `X-GitHub-Api-Version` (`graphql/conventions.md` documents it for REST only). A parsed body that has an
  `errors` key raises `GitHubGraphQLResponseError` with `status_code` the HTTP status, `details` the `errors` value
  and the first error's `message`, whether or not `data` is present (`graphql/conventions.md` "Errors"); otherwise
  it returns `data`.
- `graphql_nodes(document, variables, connection)` — `connection` is the key path under `data`; the first call
  sends `after: null`, each next call `after` = `pageInfo.endCursor`, while `pageInfo.hasNextPage` is true; it
  yields the `nodes` of every page in order (`graphql/conventions.md` "Connections and cursor pagination").

**Failures, in `_send`.** Every response-supplied value placed in a message or a log line (the bucket name, the
GraphQL error message, a redirect target) is rendered with `json.dumps`.

- An `HTTPError` with a status in `RATE_LIMIT_STATUSES` that carries `retry-after` or `x-ratelimit-remaining: 0`
  waits `retry-after` seconds, else until `x-ratelimit-reset` (`max(0, reset - clock())`), and resends, up to
  `RATE_LIMIT_MAX_RETRIES` times, logging a WARNING naming the bucket or kind of limit and the seconds before each
  wait (`conventions.md` "When limited"). When they are spent it raises `GitHubRateLimitError` with that status,
  `details` the parsed body, and a message naming the `x-ratelimit-resource` bucket when sent, else the kind of
  limit (the `retry-after` limit or the primary limit).
- Every other `HTTPError` — a `403`/`429` without those headers, a rate header that is not an integer, the
  unfollowed `307` — raises `GitHubAPIError("GitHub API <method> <url> failed: HTTP <code>")` with `status_code`
  the status and `details` the JSON body (`basic-error`, `validation-error`), or `None` when it does not parse —
  the fork's `_http_error_details` (`conventions.md` "Errors").
- A `URLError` (no response), and a `ValueError` or an `http.client.InvalidURL` raised while urllib resolves or
  opens a redirect's `Location`, raise `GitHubAPIError` naming the request URL, with `status_code` `None`.

### D4 — Registry and records (`github_api/registry.py`)

- `Paging` (an `Enum`): `NONE`, `LINK` — `LINK` covers the page-number and cursor styles alike, because the `link`
  URL carries whichever the endpoint uses.
- `RestOperation` (frozen dataclass): `operation_id`, `method`, `path` (the index row); `query_params`,
  `body_params`, `multi_segment` (frozensets of documented names, from the operation's `rest/*.md` section and
  `conventions.md` "Path parameters"); `paging`; `item_key` (`conventions.md` "Lists wrapped in an object");
  `api_version`; `accept`.
- `GraphQLOperation` (frozen dataclass): `capability` (a first cell of the "Only in GraphQL" table, verbatim),
  `document`, `connection`.
- `discover_families()` (D2); `lookup(operation_id)` over every family's `OPERATIONS`, raising `ValueError` for an
  unknown or twice-declared ID.
- `expand(operation, path_params)` replaces each `{name}` with `quote(str(value), safe="")`, or `safe="/"` for a
  `multi_segment` name; a missing parameter raises `ValueError`; a value that is `.` or `..`, or for a
  `multi_segment` name has such a segment, raises `GitHubAPIError` (a refused argument exits 1, as the fork's
  refusals do).
- `call(transport, operation_id, *, path_params, query=None, body=None)` returns `transport.request(...).json()`;
  `pages(transport, operation_id, *, path_params, query=None)` returns `transport.pages(..., item_key=...)`. A
  query or body name the record does not document raises `ValueError` before any request.

### D5 — Compatibility commands (`github_api/commands/`; UB-1.1)

Each command module registers the fork's arguments for its subcommands — names, types, defaults, choices, required
flags and mutually exclusive groups as the fork's `_register_*_subcommands` and `_add_*_arguments` define them, with
argparse's default `allow_abbrev`, so `list-issues --label` resolves to `--labels`. Each handler re-creates the fork
handler's requests and standard output. Handlers take `(*, transport, owner, repo, args)` and return `None` or an
exit code. `commands/pulls.py`'s docstring carries the PR endpoints and the own-PR approval caveat of the fork's
`cmd_approve_pr` (D8 points to it).

| Subcommand (nested spelling) | Module | Fork handler | Records |
|---|---|---|---|
| `list-issues` | `issues` | `cmd_list_issues` | `issues/list-for-repo`: Link pages of `GITHUB_MAX_PER_PAGE`, entries with `pull_request` skipped, stop at `--limit` |
| `get-issue`, `get-issue-comments` | `issues` | `cmd_get_issue`, `cmd_get_issue_comments` | `issues/get`; `issues/list-comments` (every page) |
| `comment-issue`, `create-issue`, `update-issue` | `issues` | `cmd_comment_issue`, `cmd_create_issue`, `cmd_update_issue` | `issues/create-comment`, `issues/create`, `issues/update` |
| `reopen-issue`, `checklist` | `issues` | `cmd_reopen_issue`, `cmd_checklist` | `issues/get`, `issues/update` |
| `start-issue` (`issue start`) | `claim` | `cmd_start_issue` | `issues/get`, `users/get-authenticated`, `issues/add-labels`, `issues/add-assignees` |
| `release-issue` (`issue release`) | `claim` | `cmd_release_issue` | `issues/get`, `users/get-authenticated`, `issues/update`, `issues/remove-assignees` |
| `claim-check` (`issue claim-check`) | `claim` | `cmd_claim_check` | `issues/get` |
| `label-add`, `label-remove`, `assign` (`issue …`) | `claim` | `cmd_label_add`, `cmd_label_remove`, `cmd_assign` | `issues/add-labels`, `issues/remove-label`, `issues/get`, `users/get-authenticated`, `issues/add-assignees`, `issues/remove-assignees` |
| `create-pr`, `get-pr`, `approve-pr`, `merge-pr` | `pulls` | `cmd_create_pr`, `cmd_get_pr`, `cmd_approve_pr`, `cmd_merge_pr` | `pulls/create`, `pulls/get`, `pulls/create-review`, `pulls/merge` |
| `get-pr-checks` | `pulls` | `cmd_get_pr_checks` | `pulls/get`, `checks/list-for-ref`, `repos/get-combined-status-for-ref` (one page each, as the fork) |
| `delete-remote-branch` | `pulls` | `cmd_delete_remote_branch` | `git/delete-ref` (`ref` multi-segment) |
| `list-workflows`, `list-runs`, `get-run` | `ci` | `cmd_list_workflows`, `cmd_list_runs`, `cmd_get_run` | `actions/list-repo-workflows`, `actions/list-workflow-runs-for-repo` or `actions/list-workflow-runs`, `actions/get-workflow-run` (one page each, as the fork) |
| `wait-run` | `ci` | `cmd_wait_run` | `actions/get-workflow-run`; the fork's poll, deadline check, sleep order and defaults |
| `get-logs` | `ci` | `cmd_get_logs` | `actions/download-workflow-run-logs` via `Transport.download`; the fork's archive printing |

These are the only records part 1 declares; every other index operation is on its family's `PENDING`. The nested
`issue` group is registered by `claim.py`; both spellings share one argument helper and one handler, as the fork's
`ISSUE_GROUP_DISPATCH` does.

**Deviations from the fork, flagged.** Not visible on standard output: `list-issues` and `get-issue-comments` follow
`link` instead of the fork's `page=` loop and short-page stop, giving the same items in the same order. Visible only
where the fork exited 1:

- a redirected `GET` other than the download's `302` to its storage host — the fork's `_RefusingRedirectHandler`
  refuses every redirect of an API request (its `_NoRedirectHandler` follows the download's redirects with the
  credential stripped on every hop); D3 follows it, by AC-3.1 for another host and by D3's own decision for the same
  origin, so `get-issue` on a renamed repository exits 0 where the fork exits 1. A `POST`, `PATCH`, `PUT` or `DELETE`
  on a renamed repository gets `307`, which urllib does not follow for those methods, so it exits 1 as the fork does;
- a rate-limited response — the fork raises at once; AC-3.2 waits;
- a query value or path segment the fork sent unencoded that `http.client` refuses (a space: `InvalidURL`, an
  uncaught crash), which D4 encodes.

UB-1.1 excludes these states and its golden cases build none of them; the `get-logs` case serves the `302` to a
storage host, which both wrappers follow without the credential. On the fork the unencoded-value case ends in an
uncaught `http.client.InvalidURL` — exit status 1 with a traceback, not the `GitHubAPIError` that UB-1.1's exit 1
names; no golden case builds it. `--token-stdin` is dropped (UB-1.1).

### D6 — Entry script (`github_wrapper.py`; UB-1.2, UB-1.3, UB-2.1, UB-3.2)

- **Finding the package.** The script inserts its own directory (`Path(__file__).resolve().parent`) at the front
  of `sys.path` when it is absent, then imports `github_api` absolutely. Run as `python scripts/github_wrapper.py`,
  `sys.path[0]` is already that directory; loaded by `importlib.util.spec_from_file_location`
  (`test_wrapper_delivery.load`), the insertion makes the import resolve. Loading has no other effect: no
  credential read, no request, no logging set-up (UB-3.2).
- **Kept from the skeleton, unchanged:** `STEWARD_SCRIPT`, `DELIVERY_CONFIG`, `DELIVERY_VERBS`,
  `EXIT_DELIVERY_ELSEWHERE`, `steward_delegate`. **Kept by name, with the fork's bodies:** `CREDENTIALS_FILE`,
  `PLACEHOLDER`, `_load_token` (the fork's `_one_token` validation; credential file only), `_detect_repo` (the
  fork's parsing and missing-`origin` refusal; its unparseable-URL message names `.git/config` and the URL with its
  userinfo (the authority's text up to and including its last `@`, a bare token included) removed, never the URL
  verbatim — stderr only, so stdout and exit code 2 are unchanged). `GitHubAPIError` is re-exported from `errors`;
  the module docstring, the usage list, is kept. **Removed:** the skeleton's `_api_request`, `wait_run`, `API_ROOT`,
  field constants and its implementation-instructions comment block.
- **`main(argv=None) -> int`** (`argv` `None` reads `sys.argv[1:]`):
  1. Reconfigures stdout and stderr to UTF-8 with `errors="replace"` before parsing, as the fork's
     `_force_utf8_output`.
  2. `wait-landed`, `check-handoff`, `check-landed` (DL-001): the argv after the subcommand is not parsed, so the
     steward's parser is their only argument definition. Steps 4 and 5 apply to them.
  3. Otherwise parses with `_build_parser()` (the fork's name): `enqueue-pr`, `dequeue-pr`, `queue-status` with the
     fork's `_register_delivery_subcommands` arguments, and every discovered command module.
  4. `_load_token()`, then `_detect_repo()`; a `GitHubAPIError` from either is logged and returns 2.
  5. Every delivery verb returns `steward_delegate(verb=verb, args=<list>, token=token, host="github")`. For the
     step-2 verbs the list is the argv after the subcommand; for the others it is what the fork's handlers pass
     after the steward verb — `[str(pr_number)]`, `[str(pr_number), "--reason", reason]`, or `["--json"]` when
     given — since `steward_delegate` prepends `DELIVERY_VERBS[verb]` itself (UB-1.2).
  6. Otherwise builds `Transport(token=token)` and calls `args.handler`; a `GitHubAPIError` logs its message and
     `Details:` with the JSON details, as the fork's `main`, and returns 1; else `0` for `None`, the handler's
     integer otherwise (the fork's `_exit_code_of`).
- `__main__` calls `logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")` (the fork's
  format; logs go to stderr) and `sys.exit(main())`.

### D7 — Coverage test (`test/test_github_wrapper_coverage.py`; AC-5, AC-1.2, AC-1.3, UB-2.2)

It lives in `test/` because it reads `docs/api-reference/github/`, which only this repository has; it loads the
product package by putting `src/payload/scripts` on `sys.path`.

- `index_rows(path)` — every table row of `operations-index.md` whose first cell is an HTTP method, as
  `{operation_id: (method, path)}`.
- `graphql_only(path)` — the first cell of every row of the table after the `**Only in GraphQL**` line of
  `graphql/conventions.md`, up to that table's end.
- `coverage_gaps(index, capabilities, covered, pending)` — a pure function returning, sorted, every ID and
  capability neither covered nor pending. Covered is the union of the records' `operation_id`s and `capability`s;
  pending is the union of every `PENDING` and `PENDING_CAPABILITIES`.
- The standard-library import check of UB-2.2 lives here too (X1): `test/` is never installed into projects and runs
  on CI's Python 3.10, which has `sys.stdlib_module_names`; the shipped suites stay pytest-only and Python 3.9.

### D8 — The setup prompts' GitHub copy steps (X3; UB-1.3)

- `prompts/setup-claude.txt` Part 5.3: the GitHub sentence copies `src/payload/scripts/github_wrapper.py` to
  `scripts/github_wrapper.py` and `src/payload/scripts/github_api/` to `scripts/github_api/` (the entry script
  imports it); its pointer to "the expanded docstrings in `src/payload/scripts/github_wrapper.py`" names
  `src/payload/scripts/github_api/` instead (the endpoints are its records; `commands/pulls.py` carries the own-PR
  approval caveat, D5), and so, for GitHub, do the claim bullet's "See the expanded docstrings in the wrapper
  templates" and the checklist bullet's "(See the wrapper docstrings.)".
- `prompts/setup-kiro.txt` Part 6.2: the GitHub bullet copies the same two, and the APPENDIX "Standard directory
  structure" lists `github_api/  # if GitHub` under `scripts/` beside `github_wrapper.py`.
- In both sections the "skeletons" sentence ("The wrapper templates are skeletons; implement …" in Part 5.3, "The
  template wrapper scripts are skeletons … (see the docstring in each template)" in Part 6.2) keeps its GitLab
  half as the tree holds it when this change lands (#13 D2's text once #13 has merged); for GitHub it says the wrapper implements the caller-used subcommands, that `get-jobs`, `rerun` and
  `cancel` arrive in a later framework release, and that a further subcommand is added as a `github_api/commands/`
  module (D2).
- Each prompt's shipped-Python list ("Shipped Python (shared with the Kiro prompt …)" in `setup-claude.txt`,
  "Shipped Python referenced by this prompt" in `setup-kiro.txt`) names `scripts/github_api/` beside
  `scripts/github_wrapper.py`.
- `test/test_setup_prompts_github_wrapper.py` pins the copy: the Part 5.3 and Part 6.2 sections (heading to the next
  `### Part` heading, cut as `test/test_setup_prompts_gitignore.py` cuts PART 3) name `src/payload/scripts/github_api/`
  beside `src/payload/scripts/github_wrapper.py`, and each shipped-Python list, cut from its heading to the next `###`
  heading, names `scripts/github_api/`.

### Data flow

`python scripts/github_wrapper.py get-pr-checks 7` → `main` parses (the `pulls` module registered the
subcommand) → `_load_token`, `_detect_repo` → `Transport` → the handler →
`registry.call(transport=transport, operation_id="pulls/get", path_params=...)` → `Transport.request` → the opener
with `CredentialStrippingRedirectHandler` → `api.github.com` → JSON → `registry.call` for `checks/list-for-ref` and
`repos/get-combined-status-for-ref` → the fork's summary JSON on stdout → exit 0. A `GitHubAPIError` anywhere →
stderr, exit 1.

### Sources

`docs/api-reference/github/conventions.md` and `graphql/conventions.md` (sections named above), and the official
pages they cite: [Using pagination in the REST API](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api)
("If the endpoint does not support pagination, or if all results fit on a single page, the `link` header will be
omitted"), [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
(`retry-after`, then `x-ratelimit-remaining` `0` and `x-ratelimit-reset`; `x-ratelimit-resource` "the rate limit
resource that the request counted against"), [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions),
[Release assets](https://docs.github.com/en/rest/releases/assets),
[Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api),
[Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql),
[Using pagination in the GraphQL API](https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api);
Python 3.9 [`urllib.request`](https://docs.python.org/3.9/library/urllib.request.html)
(`HTTPRedirectHandler.redirect_request`, `Request.remove_header`, `build_opener`, `HTTPErrorProcessor`) and
[`pkgutil.iter_modules`](https://docs.python.org/3.9/library/pkgutil.html#pkgutil.iter_modules).

## Testing Strategy

- **Fake host** (`src/payload/test/github_wrapper_fixtures.py`, loaded by path as `test_wrapper_delivery.load`
  loads a wrapper). `FakeGitHub` is installed with `monkeypatch` over `urllib.request.HTTPSHandler.https_open` and
  `HTTPHandler.http_open`, so every opener in the process — the product's and the fork's — reaches it and no socket
  is opened. It returns `urllib.response.addinfourl` objects with `msg` set (which `HTTPErrorProcessor.http_response`
  reads), so `HTTPErrorProcessor`, `HTTPRedirectHandler` and the wrapper's handler run unchanged. It records each
  request's method, URL, body and the headers `AbstractHTTPHandler.do_open` sends (`unredirected_hdrs` merged with
  `headers`), compared case-insensitively. Static routes match method, URL path and decoded query, so the fork's and
  the product's query encodings meet the same route; a route may hold responses served in order, the last
  repeating. List routes serve `page`/`per_page` slices of a canned list with a `link` `rel="next"`. An unrouted
  request fails the test. The module also holds `CASES`, the golden table: argv, host state, exact stdout, exit code
  and the expected non-GET requests (method, path, decoded query, JSON body).
- **Unit tests** — the transport in `src/payload/test/test_github_api_transport.py`, with a recording `sleep` and a
  fixed `clock`; the registry in `src/payload/test/test_github_api_registry.py`.
- **CLI golden tests** — `src/payload/test/test_github_wrapper_compat.py` runs `CASES` through the product's `main`
  in a temporary project (fixture `credentials/github-pat.txt`, `.git/config` with a GitHub `origin`), reading stdout
  with `capsys` and the exit code from the return value or `SystemExit`, and comparing the non-GET requests.
  `test/test_github_wrapper_fork_parity.py` runs the same `CASES`, minus the delivery verbs and the C-only cases (the
  `--token-stdin` and userinfo cases, deviations UB-1.1 makes on purpose), against the installed fork
  `scripts/github_wrapper.py`, in the same temporary project and fixture token, comparing stdout, exit code and the
  non-GET requests; it sets `sys.argv`, because the fork's `main()` takes no `argv`. Every golden value of a case P
  runs is the fork's own output.
- **Coverage, structure and standard library** — `test/test_github_wrapper_coverage.py` (D7).
- **Setup prompts** — `test/test_setup_prompts_github_wrapper.py` (D8).
- **Regression** — `src/payload/test/test_wrapper_delivery.py`, unchanged.
- **Runner.** Locally `python scripts/run_tests.py <these paths>`; in CI the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E:** the real-forge check is #10's fixture on an ephemeral `sff-test-*` repository (requirements Residuals; its
  item stays open on #17); until then the CLI is exercised through its real interface up to the API boundary by
  `test_the_script_runs_by_path` and the golden `CASES`, in CI's `tests` leg.

## Correctness Properties

- **AC-1.1** — Inspection: D1 names the choice and what each part serves. Example (registry): `registry.call` with a
  query or body name the record does not document raises `ValueError` and the fake host records no request; `expand`
  percent-encodes `/` and a space in a single-segment value, keeps `/` in a multi-segment one, and refuses a `.` or
  `..` segment with `GitHubAPIError`.
- **AC-1.2** — Inspection of D2's table. Structural test: the names `discover_families()` returns equal the module
  files present in `github_api/families/`, so no list exists to edit.
- **AC-1.3** — Structural test: the family module names equal the index's families with `-` replaced by `_`; each
  `FAMILY` matches its file; every `PENDING` ID is an index ID with that prefix; every record's ID has that prefix and
  its method and path equal its index row; no ID is declared twice or is both covered and pending; capabilities are
  pending only in `graphql_only.PENDING_CAPABILITIES`.
- **AC-2.1** — Example: every request recorded for a single call, each Link page, an upload and a `download`
  (answering `200` on the API host; the storage hop is AC-3.1's) carries `X-GitHub-Api-Version: 2022-11-28`; with
  `api_version=API_VERSION_NEXT` each carries `2026-03-10`; any other value raises `ValueError` with nothing sent.
- **AC-2.2** — Parametrized example table: one page without `link`; pages by `page`; pages by an opaque `after`
  cursor; a `link` also listing `prev`, `first`, `last` in another order, whose last page sends a `link` without
  `next`; a next URL whose query holds a comma. Oracle: the items equal the pages' concatenation, and the requested
  URLs equal the first URL followed by each `rel="next"` target, byte for byte. A `rel="next"` on another origin
  raises `GitHubAPIError` and the fake host records no request to it.
- **AC-2.3** — The same table with each page wrapped as `{"total_count": …, "workflow_runs": [...]}`: the items
  equal the concatenation of the item-key lists.
- **AC-2.4** — Example, with and without `label`: the recorded request is a `POST` to the upload URL without its
  template, the query is `name` (and `label`) urlencoded, the body equals the bytes, `Content-Type` is the media
  type. An `upload_url` on another origin than `UPLOAD_ORIGIN` raises `GitHubAPIError` and nothing is sent to it.
- **AC-3.1** — Example through the real opener: an API `302` to another host, from `request` and from `download`, is
  followed with no `Authorization`; a further hop back to the API host carries none; a same-origin `301` keeps it; a
  same-host `http://` target carries none; a target on another port of the API host (`https://api.github.com:8443/`)
  carries none; `https://api.github.com:443/` keeps it; a `302` to `https://user:pw@api.github.com/x` raises <!-- pragma: allowlist secret -->
  `GitHubAPIError` with no request recorded to it; `https://api.github.com:/x` keeps `Authorization`.
- **AC-3.2** — Examples: `429` with `retry-after` then `200` gives one sleep of the header's seconds and the `200`
  body; `403` with `x-ratelimit-remaining: 0` sleeps `x-ratelimit-reset` minus the clock; a `403` with
  `retry-after`, `x-ratelimit-remaining: 0` and a later `x-ratelimit-reset` sleeps the `retry-after` seconds; an
  always-limited host receives `RATE_LIMIT_MAX_RETRIES` + 1 requests.
- **AC-3.3** — Example: the always-limited host raises `GitHubRateLimitError` with the last status; its message
  holds the `x-ratelimit-resource` value; without that header it names the kind of limit.
- **AC-3.4** — Parametrized: `404` with a `basic-error` body, `422` with a `validation-error` body, `500` with a
  non-JSON body, `403` without rate headers each raise `GitHubAPIError` with that `status_code` and `details` equal
  to the parsed body (`None` for non-JSON), with no sleep.
- **AC-4.1** — Example: the recorded request is a `POST` to `https://api.github.com/graphql` whose JSON body has
  exactly `query` and `variables`, with the given values.
- **AC-4.2** — Example: a three-page connection yields the nodes in page order; each request's `variables.after`
  is the previous page's `endCursor`; nothing is sent after `hasNextPage: false`.
- **AC-4.3** — Parametrized: `200` with `errors` and `data`, and `200` with `errors` and `data: null`, raise
  `GitHubGraphQLResponseError` with `status_code` `200` and `details` the `errors` array.
- **AC-5.1** — Example: `index_rows` returns distinct IDs, as many as the number in the index heading
  `every operation (N)`, including `issues/get`; `graphql_only` includes "Repository discussions" and "Branch
  protection with wildcard patterns" and excludes "Capability" and every first cell of the **In both** table.
- **AC-5.2** — Example on `coverage_gaps` with a synthetic index: an ID and a capability, each neither covered nor
  pending, are returned by name, and a covered and a pending item of each kind are not; the real test's failure
  message lists every gap.
- **AC-5.3** — The real coverage test passes on the merged tree.
- **UB-1.1** — Golden example table `CASES`: each caller-used subcommand and spelling; each exit code — 0, 1, 2 for
  usage, credential and repository refusals, 3, 10, 11 (`--timeout-seconds 0`); `start-issue` and `issue start` on an
  open unclaimed issue (exit 0); `list-issues --label <name>`; each case's expected non-GET requests. The oracle is
  the fork: the parity test runs the table against it. `list-issues --token-stdin` and `create-issue --token-stdin`
  are in C only: exit 2, empty stdout, no request recorded. In C only (the fork prints the URL verbatim): an
  unparseable `origin` holding userinfo — `https://ghp_T@github.com/o/socket.io.git` and
  `https://user:secret@github.com/o/socket.io.git` — exits 2 with empty stdout, and the captured log records <!-- pragma: allowlist secret -->
  (`caplog`) hold the refusal naming `.git/config` and `github.com/o/socket.io.git`, while neither they nor stderr
  hold `ghp_T` or `secret`. Parser parity (P): for each caller-used subcommand of the fork's parser and each nested
  spelling, the fork's and the product's `_build_parser()` subparsers have equal option strings, and each action's
  `dest`, `nargs`, `const`, `default`, `type`, `choices`, `required` and mutually exclusive group are equal, except the
  fork's `--token-stdin`.
- **UB-1.2** — `test_wrapper_delivery.py` unchanged, plus: `main` for each of the six verbs hands a faked
  `subprocess.run` the steward argv `[…, "--token-stdin", <steward verb>, *args]` (the DL-001 three verbatim) and
  returns its code; a `config/delivery.json` naming another host returns `EXIT_DELIVERY_ELSEWHERE`.
- **UB-1.3** — Subprocess example: `python <product scripts dir>/github_wrapper.py get-issue 1` from an empty
  directory exits 2 with stderr holding `str(Path("credentials") / "github-pat.txt")`, so the package resolved from
  the script's own directory; the file keeps the name `gate_merge_steward.SCRIPT_KINDS` recognises. Example (S): the
  setup prompts' GitHub copy steps and shipped-Python lists name the package (D8).
- **UB-2.1** — Example and static: without the file, exit 2 and no request recorded; with it, the recorded
  `Authorization` is `Bearer` and the file's token; the entry script and package contain no `os.environ` or
  `getenv`; the parser has no token option.
- **UB-2.2** — Static (V, CI's Python 3.10): every top-level import name of the entry script and package is
  `github_api` or in `sys.stdlib_module_names`; Python 3.9 syntax by ruff's `target-version`
  (`src/hooks/ruff.toml`).
- **UB-3.1** — `test_wrapper_delivery.py` green in CI's `tests` leg; the PR diff names neither file (verification).
- **UB-3.2** — Example: loading the module by path in a directory without credentials or `.git`, the fake host
  installed, raises nothing, records no request, and exposes `steward_delegate` and `EXIT_DELIVERY_ELSEWHERE`.

## Security Considerations

- **Credential source** — `credentials/github-pat.txt` only (`_load_token` with the fork's one-token check); no
  environment variable, argument or second file; never logged, never in argv or a URL; handed to the steward on
  stdin by the unchanged `steward_delegate` (UB-1.2, UB-2.1). No message carries the git remote URL's userinfo
  (`_detect_repo`).
- **Where the token goes** — `https` requests on the `API_ROOT` origin (paths, `link` targets, `GRAPHQL_URL`) and
  `upload_url` targets on `UPLOAD_ORIGIN`; any other origin raises `GitHubAPIError` with nothing sent. Across a
  redirect it goes only to the same origin (D3, X5); a cross-origin hop drops it for the rest of the chain.
- **Paths** — path parameters percent-encoded (`safe=""`, `safe="/"` for multi-segment names); root-relative paths
  only, `//` refused; `.` and `..` segments refused.
- **Untrusted output** — error `details` and every response value inside a message go to stderr through
  `json.dumps`, which escapes control characters; API text on stdout (issue titles) is printed as the fork prints it.
- **Waiting** — rate-limit waits come only from integer headers, are logged, and are bounded by
  `RATE_LIMIT_MAX_RETRIES`.
- **Subprocess and dependencies** — the steward's fixed argv without a shell is unchanged; no third-party import.

## Operability

Not applicable — nothing deploys, and nothing is installed in this repository; the product wrapper reaches a session
here only through a release and its promotion (out of scope, `prompt.md`).

## Acceptance Criteria Mapping

Files: T = `src/payload/test/test_github_api_transport.py`, R = `src/payload/test/test_github_api_registry.py`,
C = `src/payload/test/test_github_wrapper_compat.py`, V = `test/test_github_wrapper_coverage.py`,
P = `test/test_github_wrapper_fork_parity.py`, S = `test/test_setup_prompts_github_wrapper.py`.

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1; `registry.call`, `registry.expand` | design review; R `test_call_refuses_an_undocumented_parameter`, `test_expand_encodes_and_refuses_dot_segments` |
| AC-1.2 | D2; `registry.discover_families` | design review; V `test_discovery_follows_the_directory` |
| AC-1.3 | `families/<family>.py`, `graphql_only.py` | V `test_one_module_per_family_holding_only_its_own_ids` |
| AC-2.1 | `Transport._send`, `request` | T `test_every_rest_request_sends_the_api_version` |
| AC-2.2 | `Transport.pages` | T `test_link_pages_are_followed_as_given` |
| AC-2.3 | `Transport.pages` (`item_key`) | T `test_wrapped_pages_return_the_item_key_items` |
| AC-2.4 | `Transport.upload` | T `test_an_asset_is_uploaded_to_the_upload_url` |
| AC-3.1 | `origin`, `CredentialStrippingRedirectHandler` | T `test_a_cross_origin_redirect_drops_the_credential` |
| AC-3.2 | `Transport._send` | T `test_a_rate_limit_is_waited_out_and_retried` |
| AC-3.3 | `GitHubRateLimitError` | T `test_spent_retries_raise_naming_the_limit` |
| AC-3.4 | `GitHubAPIError` | T `test_an_error_status_raises_with_the_documented_body` |
| AC-4.1 | `Transport.graphql` | T `test_graphql_posts_query_and_variables` |
| AC-4.2 | `Transport.graphql_nodes` | T `test_graphql_follows_page_info_cursors` |
| AC-4.3 | `GitHubGraphQLResponseError` | T `test_graphql_errors_raise_even_with_200` |
| AC-5.1 | `index_rows`, `graphql_only` | V `test_the_reference_is_read_whole` |
| AC-5.2 | `coverage_gaps` | V `test_a_gap_is_named` |
| AC-5.3 | every `PENDING`, `PENDING_CAPABILITIES` | V `test_every_operation_is_covered_or_pending` |
| UB-1.1 | `commands/*`, `_build_parser`, `main` | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option` |
| UB-1.2 | `main`, `steward_delegate` | `src/payload/test/test_wrapper_delivery.py`; C `test_a_delivery_verb_delegates_to_the_steward` |
| UB-1.3 | entry script path set-up; D8 | C `test_the_script_runs_by_path`; S `test_the_setup_prompts_copy_the_package` |
| UB-2.1 | `_load_token`, `main` | C `test_the_credential_comes_only_from_the_file` |
| UB-2.2 | entry script, `github_api/` | V `test_the_wrapper_imports_only_the_standard_library` |
| UB-3.1 | — (untouched files) | `src/payload/test/test_wrapper_delivery.py`; PR diff |
| UB-3.2 | entry script module level | C `test_the_module_loads_without_credential_or_network` |

## Residuals

- X4: the first promotion of a release with this change adds `src/payload/scripts/github_api/*` and, under
  `src/payload/test/`, `github_wrapper_fixtures.py`, `test_github_api_*.py`, `test_github_wrapper_compat.py` to
  `config/toolchain.json` `not_installed` before its manifest step, and while they stand skips Part 5.3's
  `github_api/` copy (`scripts/toolchain_manifest.py` lists every unnamed `src/payload/` source under `files`, and
  `test/test_toolchain_integrity.py` then requires it installed). This change cannot add the entries
  (`test/test_toolchain_manifest.py` drops those naming no source of the pinned release). The new wrapper's promotion
  removes them and settles which `github_api` copy one test process imports; one findings-ledger row records it.
- Part 2 (#14): records no compatibility command uses reach the command line as a `commands/` module; GraphQL's
  primary limit (`200` with `errors`) raises per AC-4.3, unretried. A wait until `x-ratelimit-reset` can outlast a
  caller's bounded timeout (no cap in AC-3.2) — ledger if observed. Real-forge E2E: #10's fixture.
