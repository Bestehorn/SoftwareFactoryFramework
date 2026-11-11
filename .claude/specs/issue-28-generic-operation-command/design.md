# Design — issue #28: GitHub wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-5.3, UB-1.1..UB-3.1, frozen). Builds on
`.claude/specs/issue-17-github-wrapper-foundation/design.md`, cited as "#17 Dn".

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #14 re-assessed after part 1 landed and split into children; selected issue #28, "GitHub wrapper
   rewrite, part 2a: generic operation command, coverage-proof method, docs", and derived `prompt.md` from the issue
   body; no interview (see `qa_log.md`).

## Overview

A new command module, `src/payload/scripts/github_api/commands/call.py`, adds the subcommand `call`. It sends any
record a family module declares, named by its operation ID, with path, query and typed body values from the command
line, and prints the response by its kind. The two records a gated compatibility subcommand sends (`pulls/merge`,
`issues/create`) stay with that subcommand. The registry gains `send` (which returns the record's `Response`),
`path_parameters` and `query_name`; `Transport.pages` gains `accept`. `commands/_common.py` gains `EXIT_REFUSED` and
`print_bytes`. A contract test in `test/` reads `docs/api-reference/github/rest/*.md`. For every declared record it
proves that the record documents what its section documents and that its call sends exactly that. One test applies the
same proof to an unreachable operation. The coverage test gains the regeneration cases of AC-5.3. In the entry script
only the docstring changes. `_build_parser`, `main`, every compatibility command and `CASES` stay as they are
(UB-1.1). Nothing is promoted (`prompt.md`).

## Design

### D1 — How a record reaches the command line: a mix (AC-1.1)

| Part | Serves | Where |
|---|---|---|
| Compatibility commands, unchanged | UB-1.1's caller-used subcommands, with the fork's arguments and output, on the records of #17 D5's table; the only path to `pulls/merge` (`merge-pr`) and `issues/create` (`create-issue`) | `commands/issues.py`, `claim.py`, `pulls.py`, `ci.py` |
| `call <operation-id>` | every other `RestOperation` in the `OPERATIONS` of every family module: #17's records and every record a slice adds | `commands/call.py` |

- `call` is registered like any other command module. `_discover_command_modules` finds `call.py` in the directory
  and calls its `register` (#17 D2). The fork's parser has no `call` subcommand.
- `call.py`'s `GATED_OPERATIONS` maps `pulls/merge` to `merge-pr` and `issues/create` to `create-issue`; `call`
  refuses those IDs (D4, Security Considerations "Gates").
- Alternatives:
  - **Per-family command modules, one subcommand per record.** Rejected: every slice would write a parser and a
    handler for each record, so each record would have its own call path needing its own proof, and the parser code
    would be shared per group (#17 D2's `commands/<group>.py` row).
  - **Subparsers generated from the records** (`issues/get --issue-number 5`). Rejected: the parser would build a
    subparser for every record on every run, and a name that a record documents as both a path and a body parameter
    would still need a spelling rule.
  - **One generic `call`.** Chosen: there is one call path, proven once for all records (D5), so a slice's record
    becomes callable just by being declared.

### D2 — The `call` grammar, and how it sends (AC-1.2, AC-1.3)

```
python scripts/github_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
                                      [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]...
```

- `<operation-id>`: positional, the operation ID from the index (`issues/get`).
- `--path NAME=VALUE`: a path parameter, as text. `registry.expand` encodes it: `quote` with `safe=""`, or `safe="/"`
  for a `multi_segment` name (#17 D4).
- `--query NAME=VALUE`: a query parameter, as text.
  - A name given more than once is sent once per value, in the order given.
  - A name may end in `[]` and is sent as written. That is how `conventions.md` "Query strings" spells an array
    (`repository_ids[]=1&repository_ids[]=2`).
- `-f/--raw-field NAME=TEXT`: a body member whose value is the string TEXT.
- `-F/--field NAME=JSON`: a body member whose value is JSON parsed by `json.loads`: a number, boolean, array, object,
  `null` or a quoted string (AC-1.3). The option names are `gh api`'s; unlike `gh api -F`, which converts only `true`,
  `false`, `null` and integers, this `-F` refuses text that is not JSON (exit 2), so a string is given quoted or with
  `-f`.
- **Parsing.**
  - Each option uses `action="append"` with default `None`. `--raw-field` and `--field` share one `dest`, so body
    members keep their command-line order.
  - `NAME=VALUE` splits at the first `=`. Three cases raise `argparse.ArgumentTypeError`: no `=`, an empty name, and
    `--field` text that `json.loads` refuses. That is argparse's usage error, exit 2 (Python docs, argparse `type` and
    `ArgumentParser.error`), and it happens before `main` reads the credential. Each message names the option and the
    text before the first `=` (all of it when there is none), rendered with `json.dumps`; it never holds a value.
  - A path name or a body name given twice keeps its last value.
  - No option string contains `token` (UB-2.1).
- **`cmd_call(*, transport, owner, repo, args)`** (#17 D5's handler signature):
  1. An ID in `GATED_OPERATIONS` is refused, naming its subcommand.
  2. `registry.lookup(operation_id=...)`.
  3. Path values: the given ones. When the path names `{owner}` or `{repo}` and the call does not give it, the value
     is the `owner` or `repo` that `main` passes to every handler (`_detect_repo` on the `origin` in `.git/config`).
     In the index `{owner}` is always followed by `/{repo}`, so both name the repository. A defaulted `{owner}` or
     `{repo}` has a value for AC-2.3.
  4. D4's checks. A refusal in steps 1 to 4 returns `EXIT_REFUSED` (2), with nothing sent.
  5. Query: `{name: value}`, or `{name: [values in order]}` for a repeated name. `Transport.request` encodes it with
     `urlencode(doseq=True)`, one pair per value (#17 D3).
  6. Body: `body_of(members=...)` returns the members as one JSON object, or `None` when none was given. `None` sends
     no body and no `Content-Type` (#17 D3).
  7. A `Paging.LINK` record goes through `registry.pages(...)`, any other through `registry.send(...)`. Output is as
     in D3.
- **Registry additions** (`github_api/registry.py`):
  - `path_parameters(operation) -> Tuple[str, ...]`: the `{name}` placeholders of the record's path, in order
    (`PATH_PARAMETER_PATTERN`).
  - `query_name(name) -> str`: `name` with one trailing `[]` removed. `_check_names` compares a query name through
    it, so `send` and `pages` accept the array spelling and send the name as written; D4's check calls it.
  - `send(transport, operation_id, *, path_params, query=None, body=None) -> Response`: what `call` does today
    (`lookup`; `_check_names` for query and body; `expand`; `Transport.request` with the record's `method`,
    `api_version` and `accept`), returning the `Response` instead of parsed JSON. `call` becomes `send(...).json()`
    and behaves as before.
  - `pages` passes `accept=operation.accept` to `Transport.pages`, which gains `accept: str = ACCEPT_JSON` and sends
    it on every page through `_page_items`; every existing caller keeps the default.
  - The request is therefore exactly AC-1.2's for both kinds: the record's method, its path expanded by `expand`, the
    query string, the JSON object body, and the record's `api_version` and `accept`.

### D3 — What prints (AC-1.4 to AC-1.7)

AC-1.4 governs a `Paging.LINK` record's response. AC-1.5 and AC-1.6 govern a `Paging.NONE` record's.

- **`Paging.LINK`.** The items come from `registry.pages`, which uses `Transport.pages`: each `rel="next"` target as
  given, and the items under `item_key`.
  - They are collected and printed with `print_json(value=items)` once the last page has arrived, so a failure on any
    page prints nothing.
  - Every paged section of the reference is a `GET` except the two `POST …/attestations/bulk-list` operations
    (`rest/orgs.md`, `rest/users.md`), which page by cursor without a `Link` header. So `registry.pages` sending no
    body loses nothing.
  - A page that is not the documented JSON list raises `Transport.pages`' `GitHubAPIError` (exit 1).
- **`Paging.NONE`.** The output depends on the body of the `Response` from `registry.send`:

  | Body | Standard output |
  |---|---|
  | empty (a `204`) | nothing |
  | decodes as UTF-8 and parses with `json.loads` | `print_json(value=<parsed>)` |
  | anything else | the bytes unchanged, through `_common.print_bytes`: flush `sys.stdout`, then `sys.stdout.buffer.write` (Python docs, `sys.stdout`), with no line end added |

  Every row exits 0.
- **The test is on the body, not on `Content-Type`.** AC-1.5 and AC-1.6 are stated on the body. Also, the reference
  documents JSON under media types that are neither `application/json` nor `+json` (`rest/repos.md`
  `repos/get-content`: `application/vnd.github.object`), and it does not document what `Content-Type` GitHub sends
  with a raw file. A raw file whose bytes are a JSON document prints by AC-1.5.
- **Archives behind a redirect.** For an archive behind a `302` to a storage host, the transport's opener follows the
  redirect without the credential (#17 D3, as `get-logs` does), so the body is the archive.
- **Errors.** A `GitHubAPIError` from the handler goes to `_run_command`, unchanged. It writes the message and
  `Details:` with the JSON details to standard error, and exits 1 (AC-1.7, #17 D6).

### D4 — Refusals and exit codes (AC-2)

| Condition | Exit | Standard error names |
|---|---|---|
| no operation ID; a malformed `NAME=VALUE`; `--field` text that is not JSON | 2 | argparse's usage message |
| the credential or the repository is refused | 2 | `main`'s refusal (#17 D6) |
| an ID in `GATED_OPERATIONS` | 2 | the ID and the subcommand to use (`merge-pr`, `create-issue`) |
| an ID that no record declares, whether on a pending list or not in the index (`registry.lookup`'s `ValueError`) | 2 | the ID (AC-2.1) |
| a path, query or body name the record does not document, or a path parameter with no value | 2 | one message: each undocumented name with its kind, each missing path parameter, then the record's documented path, query and body parameters (AC-2.2, AC-2.3) |
| a `.` or `..` path segment (`registry.expand`) | 1 | `GitHubAPIError` (#17 D4) |
| an HTTP error, a spent rate limit, or no response | 1 | AC-1.7 |

- **Documented names:**
  - path: `registry.path_parameters(operation=record)`
  - query: `record.query_params`, each given name compared as `registry.query_name(name=...)`
  - body: `record.body_params`
- **How a refusal is written.** Every refusal of `cmd_call`'s steps 1 to 4 is a `ValueError`: `registry.lookup`'s
  own, the gated refusal, and D4's check, which raises its one message as `registry._check_names` does. `cmd_call`
  catches `ValueError` around those steps only, logs it with `logger.error` (the script's `__main__` sends log records
  to standard error, #17 D6), and returns `_common.EXIT_REFUSED`. Every name the caller supplied is rendered with
  `json.dumps`, as `registry._check_names` renders it.
- **No exit-2 row sends a request.** The first two are decided before the handler runs. The next three are decided in
  the handler, before `registry.pages` or `registry.send`.

### D5 — Proving a call no test repository can reach (AC-3)

**The rule.** An operation is *unreachable* when its index row's path names `{enterprise}` or `{org}`, or when the
family of its operation ID is `apps`, `billing` or `teams`. Every other operation is *reachable*.

- The `sff-test-*` repository is created with `POST /user/repos` (`docs/reports/self-hosting-proposal-2026-11-07.md`).
  It belongs to the token's user, so it has no enterprise, no organisation and no organisation team. The `teams`
  family holds the `/orgs/{org}/teams/…` operations, their `/teams/{team_id}` legacy forms, and `/user/teams`.
- The `apps` operations need a GitHub App's JWT or the app's client credentials (`conventions.md` "Authentication").
- `billing` is one of the ask's own categories. Its operations sit under `/organizations/{org}/` and
  `/users/{username}/settings/billing/`.
- `is_unreachable(operation_id, path)` in the contract module states the rule as code.

**The method: two halves**, both in `test/test_github_wrapper_contract.py`. That module lives in `test/` because it
reads `docs/api-reference/github/` (#17 X1).

- **Reference half.** `reference_sections(rest_dir)` reads every `rest/<category>.md` once and keys the sections by
  operation ID.
  - A section starts at its line `` `<METHOD> <path>` · operationId `<id>` `` and ends at the next heading.
  - Its path and query parameters are the rows of its `Parameter` table, told apart by the `In` cell.
  - Its body parameters are the first-level names in the `Field` table that follows a
    ``Request body (`application/json`…)`` line, read as `docs/api-reference/README.md` "Body field paths" writes
    them: a row whose Type cell is `constraint` names no field; a leading variant label, numbered (`{variant 1}`) or
    named (`{single_select}`), is removed with the `.` after it; the name is the text before the first `.`, `[` or
    `{`.
  - `record_problems(record, section)` names every difference in method, in path, and in path, query and body
    parameter names. A record with no section is itself a problem.
- **Call half.**
  - `expected_call(section, values)` is a `CallShape(method, path, query_names, body_names)`: the section's method,
    its path with each `{name}` replaced by its value, and its query and body names.
  - `sent_call(request)` is the `CallShape` of a request the fake host recorded: the names in its decoded query and
    the member names of its JSON body.
  - `call_problems(expected, sent)` names every difference. The test values are alphanumeric, so expanding the path
    needs no encoding.
- **Applied to every declared record:**
  - `test_every_record_matches_its_reference_section` applies the reference half to every record that
    `discover_families` yields.
  - `test_every_record_is_sent_as_its_section_documents` uses one temporary project and one fake host. For each
    record outside `GATED_OPERATIONS` it runs a `call` through the product's `main`, giving a value for every path,
    query and body parameter the section documents (with `--path`, `--query` and `--raw-field`). The host routes the
    expanded path and query. It answers `[]` for a `Paging.LINK` record (under the record's `item_key` when it has
    one) and `{}` for any other. The test expects exit 0, treats a refusal as a problem, and applies the call half.
  - Both tests find the records by discovery, so a record a slice declares is proven by them without editing them.
- **For an unreachable operation**, these two halves are the whole proof. A reachable operation also gets the
  real-forge run of #10's fixture.
- `test_a_section_is_read_as_the_reference_writes_it` pins the reader:
  - `issues/create` gives the body names `title`, `body`, `assignee`, `milestone`, `labels`, `assignees`,
    `issue_field_values`, `type` and `parent_issue_id`, with no `labels[]…` row leaking in.
  - `issues/add-labels` gives `labels` from its `{variant 1}.labels` row.
  - `projects/add-field-for-org` gives `issue_field_id`, `name`, `data_type`, `single_select_options` and
    `iteration_configuration`.
  - `pulls/request-reviewers` gives `reviewers` and `team_reviewers`, and nothing from its `(body)` constraint row.
  - `actions/get-workflow-run` gives the path parameters `owner`, `repo` and `run_id`, and the query parameter
    `exclude_pull_requests`.

**AC-3.2's tests.**

- **`test_an_unreachable_call_matches_its_reference_section`** uses `billing/update-budget-org`
  (`PATCH /organizations/{org}/settings/billing/budgets/{budget_id}`), for which `is_unreachable` is true. Steps:
  1. Build the operation's record the way a slice would write it: path parameters `org` and `budget_id`, no query,
     body `budget_amount`, `prevent_further_usage`, `budget_alerting` and `expires_at` (`rest/billing.md` "Update a
     budget for an organization").
  2. Assert that `record_problems` returns nothing.
  3. Add the record to `github_api.families.billing.OPERATIONS` with `monkeypatch.setattr`, for this test only.
  4. Run argv `("call", "billing/update-budget-org", "--path", "org=acme", "--path", "budget_id=b1", "--field",
     "budget_amount=100", "--field", "prevent_further_usage=true", "--field", 'budget_alerting={"will_alert": false}',
     "--field", "expires_at=null")` through the product's `main`, against a fake host that answers the `PATCH`.
  5. Assert that `call_problems` returns nothing, that the sent body equals the typed values, and that the exit code
     is 0.
- **`test_the_method_rejects_a_call_that_differs`** is parametrized on that section, with five cases:
  - a sent shape with method `PUT`
  - a sent shape with path `…/budget/b1`
  - a sent shape with body member `amount` in place of `budget_amount`
  - a sent shape with the query name `year`
  - the record with `body_params` lacking `expires_at`

  Each case returns a problem that names the method, the path or the parameter.

### D6 — Target revision and regeneration (AC-5)

- **Target.** The slices target `docs/api-reference/github/operations-index.md` as generated from
  `github/rest-api-description@2f8f80e, 2026-11-07`, the pin its banner carries. The full commit is
  `2f8f80e47ea4d3292cf4e37ba9d9b25475e06140` (`docs/api-reference/github/README.md` "Sources").
- **How a regeneration reaches the tests.** `test_github_wrapper_coverage.py` (V) and `test_github_wrapper_contract.py`
  (N) read the reference when they run. A commit that reruns `scripts/api_reference/build.py` therefore meets them in
  CI's `tests` leg:

| In the regenerated reference | Fails, naming the ID | What brings the modules back in line |
|---|---|---|
| an operation added (a rename counts as a removal plus an addition) | V `test_every_operation_is_covered_or_pending`; for a new family, V `test_one_module_per_family_holding_only_its_own_ids` names the missing module | the ID added to its family's `PENDING`; for a new family, a new module with `FAMILY`, an empty `OPERATIONS` and its `PENDING` |
| an operation removed that a record or a pending list holds | V `test_one_module_per_family_holding_only_its_own_ids` | the ID removed from `PENDING`, or the record deleted; deleting a record that a compatibility command sends is a design change for its own issue |
| a record's ID given another method or path | V `test_one_module_per_family_holding_only_its_own_ids`, showing both | the record's `method` and `path` |
| a pending ID given another method or path | nothing | nothing to do: a pending ID carries neither |
| a parameter of a record's operation added, removed or renamed | N `test_every_record_matches_its_reference_section`, naming the record and the parameter; also N `test_every_record_is_sent_as_its_section_documents` when the record lacks the parameter | the record's `query_params` or `body_params`; a changed path parameter changes the path, as in the third row |
| a parameter of a pending operation changed | nothing | nothing to do |

- **Which change fixes it.** A regeneration is its own change. It reruns `build.py` and `verify.py`, and in the same
  change it fixes every family module the failures name. A slice never regenerates. A slice that lands after a
  regeneration covers the regenerated reference.
- **AC-5.3.** The checks have existed since #17 D7 (`coverage_gaps`, `_pending_problems`, `_record_problems`). This
  change adds `test_a_regenerated_index_names_each_changed_id`, which feeds them a synthetic index and a synthetic
  family module (a `types.ModuleType` with `FAMILY`, `OPERATIONS` and `PENDING`) for AC-5.3's three changes.

### D7 — The usage docstring and the map (AC-4)

**The usage docstring.** These lines go into the usage list of `src/payload/scripts/github_wrapper.py`, after
`check-landed`:

```
    python scripts/github_wrapper.py call issues/get --path issue_number=5   # any record, by its operation ID
        # --path NAME=VALUE (owner and repo default to the origin in .git/config); --query NAME=VALUE (a name
        # repeated sends each value; an array parameter is NAME[]; a comma-list filter is one value, labels=bug,ui);
        # -f/--raw-field NAME=TEXT (a string body member); -F/--field NAME=JSON (a number, boolean, array, object,
        # null or quoted string). A list prints as one JSON array of every page's items, a JSON body as indented JSON,
        # an empty body as nothing, any other body as its bytes unchanged. An unknown operation,
        # an undocumented parameter, a missing path parameter, and pulls/merge and issues/create (use merge-pr
        # and create-issue) are refused before any request: exit 2.
```

Its "Layout" paragraph adds `commands/call.py` beside the other subcommand modules. Its last sentence becomes: "A
`GitHubAPIError` exits 1; a usage error, a credential refusal, a repository refusal or a refused `call` exits 2."

**The map.** The `src/payload/scripts/github_api/` bullet of `docs/forLLMConsumption.md` gains, before its closing
sentence: "The product wrapper calls any declared record by its operation ID: `python scripts/github_wrapper.py call
issues/get --path issue_number=5` (`--path`, `--query`, `-f/--raw-field`, `-F/--field`; a refusal exits 2).
`test/test_github_wrapper_contract.py` checks each record against its `rest/<category>.md` section." The closing
sentence stays last and becomes: "Not yet installed here: sessions run the fork, which has no `call`
(`config/toolchain.json`)."

The module docstring of `commands/call.py` states the D2 grammar and D3's print forms. No file of the package contains
the words `environ` or `getenv` (UB-2.1's static check reads docstrings too).

### D8 — Files: this change's, and a slice's (AC-1.1)

**This change:**

| File | Change |
|---|---|
| `src/payload/scripts/github_api/commands/call.py` | new: `register`, `cmd_call`, `GATED_OPERATIONS`, `assignment`, `json_member`, `body_of`, and D4's check |
| `src/payload/scripts/github_api/commands/_common.py` | adds `EXIT_REFUSED` and `print_bytes` |
| `src/payload/scripts/github_api/registry.py` | adds `path_parameters`, `query_name` and `send`; `_check_names` compares a query name through `query_name`; `pages` passes the record's `accept`; `call` becomes `send(...).json()` |
| `src/payload/scripts/github_api/transport.py` | `Transport.pages` and `_page_items` take `accept` (default `ACCEPT_JSON`) and send it on every page |
| `src/payload/scripts/github_wrapper.py` | the module docstring only (D7) |
| `src/payload/test/github_wrapper_fixtures.py` | adds `PRODUCT_SCRIPT` and `run_product_case(*, case, root, monkeypatch, capsys)`, which enters the project, runs the product's `main(argv=...)` (a `SystemExit` gives its code), calls `assert_outcome` and `assert_every_request_routed`, and returns the recorded requests; `CASES` is untouched |
| `src/payload/test/test_github_api_call.py` | new (Testing Strategy) |
| `src/payload/test/test_github_api_registry.py` | adds `test_send_returns_the_response_of_the_record`, `test_path_parameters_are_the_placeholders_in_order` and `test_a_query_name_ending_in_brackets_is_sent_as_written` |
| `src/payload/test/test_github_api_transport.py` | adds `test_link_pages_send_the_given_accept` |
| `src/payload/test/test_github_wrapper_compat.py` | adds `test_the_usage_names_the_operation_call` |
| `test/test_github_api_call_properties.py` | new: AC-1.3's property |
| `test/test_github_wrapper_contract.py` | new (D5) |
| `test/test_github_wrapper_coverage.py` | adds `test_a_regenerated_index_names_each_changed_id` (D6) |
| `docs/forLLMConsumption.md` | the `github_api/` bullet (D7) |

**A slice** (#27, #29, #31, #32, #33). This table replaces #17 D2's "What a family's change edits" for these slices:

| File | Edited when |
|---|---|
| `github_api/families/<family>.py` | always: each record added to `OPERATIONS` and its ID removed from `PENDING` |
| `src/payload/test/test_github_api_<family>.py` | new, when the family has a `Paging.LINK` record: one `GoldenCase` per such record, run with `fx.run_product_case`; argv `call <id>` with `--path NAME=VALUE` for each path parameter but `owner` and `repo`, plus `--query per_page=1` when the record documents `per_page`; a `ListRouteSpec` of two items under the `item_key` its section's Paging line names; stdout `printed_json` of both items. Every other record is proven by D5's two tests alone. |
| never | `github_wrapper.py`, `commands/*`, `families/__init__.py`, `github_wrapper_fixtures.py`, `test_github_wrapper_coverage.py`, `test_github_wrapper_contract.py` |
| the exceptions, each named by issue | `transport.py` and `commands/call.py` for a non-JSON request body (#27 `repos/upload-release-asset`, #33 `markdown/render-raw`); `transport.py` for the `307` re-send (#27); `graphql_only.py` and a GraphQL call (#30); `GATED_OPERATIONS` or the hook gates for a record that writes a branch (Residuals) |

### Data flow

1. `python scripts/github_wrapper.py call issues/get --path issue_number=5` reaches `main`, which parses the argv
   (`call.py` registered `call`), then runs `_load_token` and `_detect_repo` and builds a `Transport`.
2. `cmd_call` finds `issues/get` outside `GATED_OPERATIONS`, calls `registry.lookup`, adds `owner` and `repo` from
   `origin`, and runs D4's checks.
3. `registry.send` expands the path and calls `Transport.request` with `GET /repos/o/r/issues/5`, the record's
   `api_version` and `accept`.
4. The response is JSON, so `print_json` writes it and the exit code is 0.

A refusal exits 2 with no request. A `GitHubAPIError` exits 1.

### Sources

- `docs/api-reference/github/conventions.md`: "Authentication", "Headers, media types and API versions", "Request
  encoding" ("Path parameters", "Query strings"), "Pagination".
- `docs/api-reference/README.md`: "Reading the generated tables" ("Body field paths").
- `docs/api-reference/github/README.md`: "Sources".
- `docs/reports/self-hosting-proposal-2026-11-07.md`: the `sff-test-*` fixture.
- Python 3.9 [`argparse`](https://docs.python.org/3.9/library/argparse.html): `type` ("If the function raises
  `ArgumentTypeError`, `TypeError`, or `ValueError`, the exception is caught and a nicely formatted error message is
  displayed"), `ArgumentParser.error` ("terminates the program with a status code of 2"), `action='append'`, and a
  `dest` shared by two options.
- Python 3.9 [`sys.stdout`](https://docs.python.org/3.9/library/sys.html#sys.stdout): "to write bytes to `stdout`, use
  `sys.stdout.buffer.write(b'abc')`".
- [`gh api`](https://cli.github.com/manual/gh_api): `-f, --raw-field` "Add a string parameter in key=value format";
  for `-F, --field`, "literal values `true`, `false`, `null`, and integer numbers get converted to appropriate JSON
  types".
- [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html): `recursive(base,
  extend, *, …)`, `lists(elements, *, …)`, `dictionaries(keys, values, *, …)`.

## Testing Strategy

- **Fake host.** `src/payload/test/github_wrapper_fixtures.py`, as #17's Testing Strategy describes it, plus
  `run_product_case`.
- **Unit tests.**
  - The registry's `send`, `path_parameters` and `query_name` are tested in `test_github_api_registry.py` (R), using
    its synthetic family: `send` and `pages` send a query name ending in `[]` as written. `Transport.pages` sending
    its `accept` on every page is tested in `test_github_api_transport.py` (T). K's AC-1.2 rows test both through
    `call` too.
  - `json_member` and `body_of` get a Hypothesis property (AC-1.3) in H, `test/test_github_api_call_properties.py`,
    which puts `src/payload/scripts` on `sys.path` as V does: a `scripts_on_path` fixture applied with
    `@pytest.mark.usefixtures("scripts_on_path")` (#17 X1: a Hypothesis test lives in `test/`; the shipped suites stay
    pytest-only).
- **CLI tests, in K.**
  - `CALL_CASES` is a table of `GoldenCase` rows with argv `call …`, run with `fx.run_product_case`, against the
    fixture project (`origin` `o/r`).
  - Refusals are judged by `assert_outcome`, which requires no request for exit 2, and by `caplog`.
  - Non-JSON bodies are read with `capsysbinary`.
  - These rows are not in `CASES`, so the fork never runs them.
- **Docstring test.** C `test_the_usage_names_the_operation_call` (AC-4.1).
- **Contract tests.** `test/test_github_wrapper_contract.py` (N), as in D5.
- **Coverage tests.** `test/test_github_wrapper_coverage.py` (V) adds AC-5.3's test; its existing tests are unchanged.
- **Regression.** `test_github_wrapper_compat.py` (C) with no existing test edited, `test/test_github_wrapper_fork_parity.py`
  (P) and `src/payload/test/test_wrapper_delivery.py`, unchanged.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The real-forge check is #10's fixture on an ephemeral `sff-test-*` repository (`prompt.md`, requirements
  Residuals). Until it exists, `call` is exercised through `main`'s argv up to the API boundary by K and N, and the
  entry script loads `commands/call.py` by path in C `test_the_script_runs_by_path` (unchanged), all in CI's `tests`
  leg.

## Correctness Properties

Each entry gives the test kind and its oracle.

- **AC-1.1**
  - Inspection: D1 names both parts and what each serves; D8 names the files a slice edits.
  - Structural: N `test_every_record_is_sent_as_its_section_documents` calls every discovered record outside
    `GATED_OPERATIONS` through `call`.
  - Example, K `test_a_gated_operation_names_its_subcommand`: `call pulls/merge --path pull_number=1` and
    `call issues/create --raw-field title=T` each exit 2 with no request, and the log record of the first names
    `pulls/merge` and `merge-pr`, that of the second `issues/create` and `create-issue`.
- **AC-1.2** — Example table, K `test_an_operation_call_sends_its_record`:
  - `call issues/get --path issue_number=5` sends one `GET /repos/o/r/issues/5`, with no body and no `Content-Type`.
  - Adding `--path owner=x --path repo=y` sends to `/repos/x/y/issues/5`.
  - `call issues/remove-label --path issue_number=5 --path "name=area/ui"` sends one
    `DELETE /repos/o/r/issues/5/labels/area%2Fui`; with `--path "name=help wanted"` it sends `…/labels/help%20wanted`.
  - `call actions/get-workflow-run --path run_id=7 --query exclude_pull_requests=true` sends that query.
  - `call issues/update --path issue_number=5 --raw-field title=T --field labels=["bug"]` sends a `PATCH` with body
    `{"title": "T", "labels": ["bug"]}`.
  - `call issues/list-for-repo --query labels=bug --query labels=ui` sends `labels` twice.
  - `call issues/list-for-repo --query state[]=open` sends the name `state[]`.
  - Two rows run on copies of `issues/get` (`Paging.NONE`) and `issues/list-comments --path issue_number=5`
    (`Paging.LINK`, two pages) whose `api_version` is `API_VERSION_NEXT` and `accept`
    `application/vnd.github.full+json` (`dataclasses.replace`), set into `github_api.families.issues.OPERATIONS` in
    place of the originals, with `monkeypatch.setattr` for the test.

  Oracle: the recorded method, path as sent, decoded query and JSON body, and on every recorded request
  `X-GitHub-Api-Version` and `Accept` equal to the record's `api_version` and `accept`. Unit examples on the same
  oracle: R `test_send_returns_the_response_of_the_record`, `test_a_query_name_ending_in_brackets_is_sent_as_written`;
  T `test_link_pages_send_the_given_accept`.
- **AC-1.3**
  - Property, H `test_any_json_value_becomes_the_body_member`. For a name drawn from `[a-z_][a-z0-9_]*` and any JSON
    value: `body_of(members=[json_member(text=f"{name}={json.dumps(obj=value)}")]) == {name: value}`, and
    `body_of(members=[])` is `None`. Hypothesis sketch:

    ```python
    json_values = st.recursive(
        base=st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(),
        extend=lambda inner: st.lists(elements=inner) | st.dictionaries(keys=st.text(), values=inner),
    )
    ```
  - Example, K `test_a_body_member_holds_the_given_json_value`, parametrized over a string, a number, a boolean, an
    array, an object and `null`, run through `main` with `issues/update --path issue_number=5`. Oracle: the recorded
    body member equals the value.
- **AC-1.4** — Example, K `test_a_list_prints_every_page_as_one_array`, with `--query per_page=2`:
  - `issues/list-for-repo` (a bare list): the first page is a static route whose `link` names
    `https://api.github.com/repositories/1/issues?per_page=2&page=2`, as GitHub names a next page, and a second static
    route serves that URL, so only a request of the target as given is routed.
  - `actions/list-workflow-runs-for-repo` (items under `workflow_runs`), served by a list route across two pages.

  Oracle: stdout equals `printed_json` of every item in order, and every request was routed.
- **AC-1.5** — Example, K `test_a_json_or_empty_body_prints_as_documented`. `issues/get` answering JSON prints
  `printed_json` of the body. `git/delete-ref --path ref=heads/topic` answering `204` prints nothing. Both exit 0.
- **AC-1.6** — Parametrized example with `capsysbinary`, K `test_a_body_that_is_not_json_is_written_unchanged`. Four
  cases:
  - `actions/download-workflow-run-logs` answering `302` to a storage URL, where an uncredentialed route serves a zip
  - `pulls/get` answering diff text
  - a record answering HTML
  - a record answering bytes that are not UTF-8

  Oracle: the stdout bytes equal the body bytes, and the exit code is 0.
- **AC-1.7** — Example, K `test_an_api_error_exits_1_with_its_details`. `issues/get` answering `NOT_FOUND` exits 1,
  stdout is empty, and the log records hold the message and `Details:` with the body.
- **AC-2.1** — Parametrized, K `test_an_unknown_operation_is_refused`. Two cases: an ID on `pulls`' `PENDING`
  (`pulls/list`), and an ID not in the index. Oracle: exit 2, no request, and a log record that names the ID.
- **AC-2.2** — Parametrized, K `test_an_undocumented_parameter_is_refused`. Four cases:
  - `issues/get --path issue_number=5` with `--path number=5` added
  - the same with `--query sort=created` added
  - `issues/update --path issue_number=5 --raw-field color=red`
  - `issues/update --path issue_number=5 --path number=5 --query sort=created --raw-field color=red`, where one log
    record names `number`, `sort` and `color`, each with its kind

  Oracle: exit 2, no request, and a log record that names each undocumented parameter and the record's path, query
  and body parameters.
- **AC-2.3** — Example, K `test_a_missing_path_parameter_is_refused`. `call issues/get` exits 2 with no request, and
  the log record names `issue_number` and the path parameters `owner`, `repo` and `issue_number`. R
  `test_path_parameters_are_the_placeholders_in_order` pins the names D4 reads.
- **AC-3.1**
  - Inspection: D5's rule and method.
  - Example: within N's unreachable test, `is_unreachable` is true for `billing/update-budget-org`, `orgs/get`
    (`/orgs/{org}`: the path arm only) and `apps/get-authenticated` (`/app`: the family arm only), and false for
    `issues/get`.
- **AC-3.2** — Examples: N `test_an_unreachable_call_matches_its_reference_section` passes, and every case of
  `test_the_method_rejects_a_call_that_differs` names its difference (D5). N
  `test_a_section_is_read_as_the_reference_writes_it` pins the reader they use.
- **AC-4.1** — Static, C `test_the_usage_names_the_operation_call`. The entry script's `__doc__` holds
  `call issues/get`, `--path`, `--query`, `-f/--raw-field`, `-F/--field`, `JSON array`, `indented JSON`,
  `bytes unchanged` and `exit 2`.
- **AC-4.2**
  - Inspection of the map bullet (D7).
  - `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes.
- **AC-5.1** — Inspection: D6 names the pin.
- **AC-5.2** — Inspection: D6's table and its "Which change fixes it" item.
- **AC-5.3**
  - Parametrized example, V `test_a_regenerated_index_names_each_changed_id`, on a synthetic index and family module:
    - an added ID is returned by `coverage_gaps`
    - a pending ID and a record ID that the index lacks are each named by `_family_problems`
    - a record whose index row has another path is named by `_family_problems`
    - a record whose index row has another method, and the same path, is named by `_family_problems`
  - On the merged tree, V `test_every_operation_is_covered_or_pending` and
    `test_one_module_per_family_holding_only_its_own_ids` pass.
- **UB-1.1**
  - C `test_a_subcommand_matches_its_golden_case`, and P `test_the_fork_produces_the_golden_case` and
    `test_the_parsers_match_option_by_option`, pass with `CASES`, `PARSER_SPELLINGS` and their assertions unedited.
  - Verification: the PR diff changes no existing line of `CASES`, of C or of P; C gains only
    `test_the_usage_names_the_operation_call`.
  - The `call` subparser is new and is not one of the spellings P compares.
- **UB-2.1** — C `test_the_credential_comes_only_from_the_file`, unchanged, scans `commands/call.py` (no `environ`, no
  `getenv`) and the `call` subparser's options (none holds `token`).
- **UB-2.2** — V `test_the_wrapper_imports_only_the_standard_library`, unchanged, scans `commands/call.py` and the
  edited modules.
- **UB-3.1** — `src/payload/test/test_wrapper_delivery.py` passes in CI's `tests` leg, and the PR diff names neither
  file.

## Security Considerations

- **Credential.** The source is unchanged (`_load_token`, UB-2.1). `call` adds no token option, and the token goes
  only where #17 D3 sends it.
- **Command-line input.**
  - Path values are percent-encoded by `registry.expand`, and `.` and `..` segments are refused.
  - The URL is `API_ROOT` plus a record's root-relative path, so no value can change the host, and `Transport._send`'s
    origin check is unchanged.
  - Query values are encoded by `urlencode`, and the body by `json.dumps`.
  - An undocumented name is refused before anything is sent.
  - A refusal, `cmd_call`'s or argparse's type error, renders the caller's names with `json.dumps`, which escapes
    control characters, and holds no value.
- **Response bytes.** A non-JSON body reaches stdout unchanged (AC-1.6), including any control or terminal-escape bytes
  it holds. A caller that keeps such a body redirects stdout to a file. Error `details` still go to stderr through
  `json.dumps` (#17).
- **Gates.** `gate_merge_steward` (`script_call`) refuses the wrapper's `merge-pr`, and `gate_filing` (`CREATE_RE`)
  judges `create-issue`; both match the subcommand words, so neither sees `call`. `call` therefore refuses
  `pulls/merge` and `issues/create` (`GATED_OPERATIONS`), naming the gated subcommand, and reaches no endpoint that a
  gate refuses under its compatibility spelling. The hooks are unchanged.
- **Destructive operations.** `call` sends whatever a declared record allows, without asking for confirmation. Whether
  to run one is the caller's decision under `continuous-work.md` Exception 1. No permission prompt comes first (the
  settings allow-list the wrapper as a whole), and a record whose only path parameters are `{owner}` and `{repo}` acts
  on the checkout's `origin` when neither is given (D2 step 3).
- **Dependencies.** No new dependency of the shipped code, and no subprocess. H's Hypothesis is already in
  `pyproject.toml`'s `dev` extra and runs only in `test/`.

## Operability

Not applicable. Nothing deploys, and a session here gets the product wrapper only through a release and its promotion
(`prompt.md`).

## Acceptance Criteria Mapping

Test files:

- K = `src/payload/test/test_github_api_call.py`
- R = `src/payload/test/test_github_api_registry.py`
- T = `src/payload/test/test_github_api_transport.py`
- H = `test/test_github_api_call_properties.py`
- N = `test/test_github_wrapper_contract.py`
- V = `test/test_github_wrapper_coverage.py`
- C = `src/payload/test/test_github_wrapper_compat.py`
- P = `test/test_github_wrapper_fork_parity.py`

| Criterion | Component | Test |
|---|---|---|
| AC-1.1 | D1, D8; `commands/call.py`, `GATED_OPERATIONS` | design review; N `test_every_record_is_sent_as_its_section_documents`; K `test_a_gated_operation_names_its_subcommand` |
| AC-1.2 | `cmd_call`, `registry.send`, `registry.query_name`, `Transport.pages` | K `test_an_operation_call_sends_its_record`; R `test_send_returns_the_response_of_the_record`, `test_a_query_name_ending_in_brackets_is_sent_as_written`; T `test_link_pages_send_the_given_accept` |
| AC-1.3 | `json_member`, `body_of` | H `test_any_json_value_becomes_the_body_member`; K `test_a_body_member_holds_the_given_json_value` |
| AC-1.4 | `cmd_call` → `registry.pages`, `print_json` | K `test_a_list_prints_every_page_as_one_array` |
| AC-1.5 | `cmd_call`, `print_json` | K `test_a_json_or_empty_body_prints_as_documented` |
| AC-1.6 | `cmd_call`, `_common.print_bytes` | K `test_a_body_that_is_not_json_is_written_unchanged` |
| AC-1.7 | `_run_command` (unchanged) | K `test_an_api_error_exits_1_with_its_details` |
| AC-2.1 | `cmd_call` (D4), `registry.lookup` | K `test_an_unknown_operation_is_refused` |
| AC-2.2 | `cmd_call` (D4), `registry.query_name` | K `test_an_undocumented_parameter_is_refused` |
| AC-2.3 | `cmd_call` (D4), `registry.path_parameters` | K `test_a_missing_path_parameter_is_refused`; R `test_path_parameters_are_the_placeholders_in_order` |
| AC-3.1 | D5; `is_unreachable` | design review; N `test_an_unreachable_call_matches_its_reference_section` |
| AC-3.2 | `reference_sections`, `record_problems`, `call_problems` | N `test_an_unreachable_call_matches_its_reference_section`, `test_the_method_rejects_a_call_that_differs`, `test_a_section_is_read_as_the_reference_writes_it` |
| AC-4.1 | entry script docstring (D7) | C `test_the_usage_names_the_operation_call` |
| AC-4.2 | `docs/forLLMConsumption.md` (D7) | design review; `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` |
| AC-5.1 | D6 | design review |
| AC-5.2 | D6 | design review |
| AC-5.3 | `coverage_gaps`, `_family_problems` | V `test_a_regenerated_index_names_each_changed_id`, `test_every_operation_is_covered_or_pending`, `test_one_module_per_family_holding_only_its_own_ids` |
| UB-1.1 | `commands/*`, `_build_parser`, `main`, `CASES` (all unchanged) | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option`; PR diff |
| UB-2.1 | `_load_token`; `call`'s options | C `test_the_credential_comes_only_from_the_file` |
| UB-2.2 | `commands/call.py`, `registry.py`, `transport.py`, `_common.py` | V `test_the_wrapper_imports_only_the_standard_library` |
| UB-3.1 | none (the files are untouched) | `src/payload/test/test_wrapper_delivery.py`; PR diff |

## Residuals

- Out of scope, each with its owner: non-JSON request bodies (#27 `repos/upload-release-asset`, #33
  `markdown/render-raw`; D8's exceptions); the `307` re-send (#27); GraphQL capabilities (#30); the real-forge check
  (#10); the promotion.
- A body value read from a file (the compatibility commands' `--body-file`) is not in AC-1, so a secret value
  (`repos/create-webhook` `config.secret`) shows in the process's command line.
- Choosing a media type per call is the requirements' residual. D5 compares names only: `paging`, `item_key`,
  `multi_segment` and `accept` are checked by the slice's `Paging.LINK` cases and by review.
- A body documented as a map of any key (`*`, `copilot/set-copilot-content-exclusion-for-organization`) is not
  callable through `call`; the slice covering `copilot` routes it per `issue-filing-discipline.md`.
- A slice that declares a record writing a branch (`pulls/merge-async`, the asynchronous `pulls/merge`;
  `repos/merge`, `git/update-ref`, `git/create-ref`, `repos/create-or-update-file-contents`) extends
  `GATED_OPERATIONS` or the hook gates with it. `git/delete-ref`, declared since #17, is of the same class: it deletes
  any branch, the trunk included, through `call` as through `delete-remote-branch`, and `gate_merge_steward` refuses
  a trunk deletion only when it is spelled `git push --delete`.
- #10's fixture settles which reachable operations its account can exercise; the ones it cannot rest on D5 alone.
