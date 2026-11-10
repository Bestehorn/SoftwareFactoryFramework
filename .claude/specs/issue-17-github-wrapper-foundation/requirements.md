# Requirements — issue #17: GitHub wrapper rewrite, part 1 (design, core transport, today's subcommands, coverage test)

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the issue's open questions are decided in DL-001.

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end"
- Issue #17: "GitHub wrapper rewrite, part 1: design, core transport, today's subcommands, coverage test"
- The operator's ask, relayed in issue #17: "The operator asked to split #12 and its GitLab sibling #11 into two
  children each: a foundation, then the remaining coverage. (relayed; original request in #12)"

## Overview

The product wrapper `src/payload/scripts/github_wrapper.py` is a skeleton: `main` raises `NotImplementedError`, and
`_api_request` sets `Authorization` with `add_header`, which urllib's redirect handler copies to the redirect target
(`docs/api-reference/github/conventions.md`, "Downloads and redirects"). Sessions run the adopted fork installed as
`scripts/github_wrapper.py`. This change is the foundation of #12: it records the wrapper's structure, builds the REST
and GraphQL transport, puts every caller-used subcommand on that transport with the fork's behaviour, and adds the
coverage test whose pending lists part 2 (#14) empties. Part 2's operations, the real-forge test on the #10 fixture
and promoting the new wrapper over the fork are out of scope.

## Glossary

- **Fork** — the installed `scripts/github_wrapper.py` (`_build_parser`, `DISPATCH`, `main`); read only, the
  reference behaviour.
- **Caller-used subcommand** — a subcommand in the set UB-1.1 names: what `clients/`, `src/hooks/` and `src/payload/`
  invoke today.
- **Transport** — the part of the product wrapper that sends REST and GraphQL requests and turns each response into a
  return value or a `GitHubAPIError`.
- **Operation family** — the part of an operation ID in `docs/api-reference/github/operations-index.md` before the
  `/` (`issues` in `issues/get`).
- **Covered** — named by a wrapper call's declaration of the REST operation ID or "Only in GraphQL" capability it
  implements.
- **Pending list** — the files naming the operations and capabilities not yet covered.
- **Item key** — the property that holds a paged list returned inside an object (`conventions.md`, "Lists wrapped in
  an object").

## Requirements

### Requirement 1 — Structure and layout (issue AC-1)

As a part-2 worker, I want the operation layer and the file layout decided, so that I can add an operation family in
parallel with other workers without editing a file they edit.

- AC-1.1 `design.md` SHALL record the choice of operation layer — generic and driven by `docs/api-reference/github/`,
  hand-written subcommands, or a mix — and, for a mix, which operations each part serves.
- AC-1.2 `design.md` SHALL give a file layout under which covering an operation of one family edits only that
  family's files wherever possible, and SHALL name every file a family's change still edits, each with the reason it
  stays shared.
- AC-1.3 The pending list SHALL be one file per operation family (DL-001), each holding only its own family's
  operation IDs; `design.md` SHALL name the file that holds the "Only in GraphQL" capabilities.

### Requirement 2 — REST transport: version, pagination, uploads (issue AC-2)

As a subcommand author, I want one REST request path that pins the API version, returns whole lists and uploads to the
upload host, so that no subcommand re-implements them.

- AC-2.1 The transport SHALL send `X-GitHub-Api-Version` on every REST request: `2022-11-28` unless the caller
  selects `2026-03-10` (DL-001; `conventions.md`, "API versions").
- AC-2.2 WHEN a caller requests a paginated list, the transport SHALL follow each `rel="next"` URL of the response's
  `Link` header exactly as given until a page carries none, and SHALL return the items of every page in page order
  (`conventions.md`, "Pagination").
- AC-2.3 WHEN the operation returns its list inside an object, the transport SHALL return the items under the
  operation's item key from every page.
- AC-2.4 WHEN a release asset is uploaded, the transport SHALL send it to the release's `upload_url` with the
  `{?name,label}` template removed and `name` (and `label` when given) as the query, the file's bytes as the body and
  the asset's media type as `Content-Type` (`conventions.md`, "Uploads and binary request bodies").

### Requirement 3 — Redirects, rate limits, errors (issue AC-3)

As an operator, I want the token never sent to a redirect target on another host and rate limits waited out before
anything fails, so that no credential reaches a storage host and a limit hit does not read as a defect.

- AC-3.1 WHEN a response redirects a request to a host other than the one the request was sent to, the transport
  SHALL send the redirected request without an `Authorization` header (`conventions.md`, "Do not forward the
  token").
- AC-3.2 WHEN a response has status `403` or `429` and carries `retry-after` or `x-ratelimit-remaining: 0`, the
  transport SHALL wait the `retry-after` seconds when present, else until `x-ratelimit-reset`, and SHALL retry the
  request a bounded number of times (`conventions.md`, "Rate limits", "When limited").
- AC-3.3 WHEN the retries of AC-3.2 are spent, the transport SHALL raise `GitHubAPIError` carrying the status and a
  message naming the limit hit — the `x-ratelimit-resource` bucket where the response sends one.
- AC-3.4 WHEN any other response has a status of `400` or above, the transport SHALL raise `GitHubAPIError` with
  `status_code` set to that status and `details` holding the parsed error body GitHub documents (`basic-error` or
  `validation-error`; `conventions.md`, "Errors").

### Requirement 4 — GraphQL (issue AC-4)

As a part-2 worker covering an "Only in GraphQL" capability, I want one GraphQL request path, so that the request
shape, cursor paging and error handling are written once.

- AC-4.1 WHEN a GraphQL operation is called, the transport SHALL POST a JSON body of `query` and `variables` to
  `https://api.github.com/graphql` (`graphql/conventions.md`, "Endpoint and request shape").
- AC-4.2 WHEN a GraphQL connection is paged, the transport SHALL repeat the operation with `after` set to
  `pageInfo.endCursor` while `pageInfo.hasNextPage` is true, and SHALL return the nodes of every page in page order
  (`graphql/conventions.md`, "Connections and cursor pagination").
- AC-4.3 WHEN a GraphQL response holds a top-level `errors` array, the transport SHALL raise `GitHubAPIError`
  carrying those errors, also when the HTTP status is `200` and also when `data` is present
  (`graphql/conventions.md`, "Errors").

### Requirement 5 — Coverage test (issue AC-5)

As the maintainer of #12, I want a test that names every operation and "Only in GraphQL" capability the wrapper
neither covers nor lists as pending, so that part 2's remaining work is a list that only shrinks.

- AC-5.1 The coverage test SHALL read every operation ID of `docs/api-reference/github/operations-index.md` and every
  capability of the "Only in GraphQL" table of `docs/api-reference/github/graphql/conventions.md`.
- AC-5.2 WHEN an operation ID or a capability is neither covered nor on a pending list, the coverage test SHALL fail
  and name each one.
- AC-5.3 WHEN this change merges, every operation and capability no wrapper call covers SHALL be on a pending list,
  so that the coverage test passes.

## Unchanged behaviour

- UB-1.1 Every caller-used subcommand SHALL CONTINUE TO accept the arguments of the fork's `_build_parser`, including
  argparse's unambiguous-prefix abbreviations (the skeleton's documented `list-issues --label`), and, for the same
  state of the repository on the host — except a redirect other than the `302` that sends `get-logs`' download to its
  storage host, or a response that AC-3.2 rate-limits, which Requirement 3 and `design.md` D3 govern — to write the
  fork's standard output and return the fork's exit codes: 0 success, 1 a `GitHubAPIError` raised by the subcommand, 2
  a usage error or a credential or repository refusal, 3 `claim-check` on an open unclaimed issue, 10 and 11
  `wait-run`. The caller-used set:
  - issues: `list-issues`, `get-issue`, `get-issue-comments`, `comment-issue`, `create-issue`, `update-issue`,
    `reopen-issue`, `checklist`;
  - claim: `start-issue`, `release-issue`, `claim-check`, `label-add`, `label-remove`, `assign`, and the nested
    `issue start`, `issue release`, `issue claim-check`, `issue label-add`, `issue label-remove`, `issue assign`;
  - pull requests: `create-pr`, `get-pr`, `get-pr-checks`, `approve-pr`, `merge-pr`, `delete-remote-branch`;
  - CI: `list-workflows`, `list-runs`, `get-run`, `get-logs`, `wait-run`;
  - delivery: `enqueue-pr`, `dequeue-pr`, `queue-status` (the fork's arguments; output and exit codes per UB-1.2), and
    `wait-landed`, `check-handoff`, `check-landed` (UB-1.2 alone; not in the fork — DL-001).
  The fork's `--token-stdin` option of `list-issues` and `create-issue`, which no caller passes, is not carried
  (UB-2.1).
- UB-1.2 The delivery verbs SHALL CONTINUE TO delegate through `steward_delegate` as
  `src/payload/test/test_wrapper_delivery.py` pins it: `scripts/merge_steward.py --token-stdin <steward verb> <args>`,
  the token on standard input only, the steward's exit code passed through, and `EXIT_DELIVERY_ELSEWHERE` on a host
  that is not the queue's (`config/delivery.json` `host`; DL-001 for `wait-landed`, `check-handoff`,
  `check-landed`).
- UB-1.3 The installed wrapper SHALL CONTINUE TO run as `python scripts/github_wrapper.py <subcommand> …` from the
  project root — the path `hooklib.project_wrapper` resolves and `gate_claim` and `gate_issue_loop` execute — under
  the file name `github_wrapper.py` that `gate_merge_steward` recognises (`SCRIPT_KINDS`).
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `credentials/github-pat.txt` (`_load_token`) —
  never from an environment variable, an argument or another file.
- UB-2.2 The shipped wrapper SHALL CONTINUE TO import only the Python 3.9 standard library.
- UB-3.1 `src/payload/scripts/gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be
  untouched by this change and to pass.
- UB-3.2 `src/payload/scripts/github_wrapper.py` SHALL CONTINUE TO expose `steward_delegate(verb, args, token, host)`
  and `EXIT_DELIVERY_ELSEWHERE` at module level and to load without a credential or the network, as that test loads
  the module by path.

## Residuals

- Named only by `prompts/` and `docs/ci-capacity-ladder.md`: `get-jobs` (written `--steps`; the fork spells it
  `--show-steps`), `get-variable`, and the setup prompts' `rerun`, `cancel` — part 2 (#14), with the fork's other
  subcommands no caller uses.
- urllib raises `HTTPError` on the `307` GitHub sends to every `POST`, `PATCH`, `PUT` and `DELETE` on a renamed or
  transferred repository (and that `PATCH`/`DELETE /repos/{owner}/{repo}` declare; `conventions.md`, "Downloads and
  redirects"); re-sending to `Location` is not in AC-3 — part 2, with those operations.
- A same-host redirect (a `301` for a renamed repository) is outside AC-3.1; whether it is followed and whether
  `Authorization` is kept there is `design.md`'s decision.
- A `403`/`429` with neither `retry-after` nor `x-ratelimit-remaining: 0` (a secondary limit; `conventions.md` says
  wait at least a minute) is not retried by AC-3.2 and raises per AC-3.4 — findings ledger if it is ever observed.
- A layout of more than one file needs the setup prompts' copy step and `config/toolchain.json` to carry the added
  files: the copy step is edited by this change (`design.md` D8); `config/toolchain.json` is routed per `design.md`
  § Residuals — the first promotion after the merge leaves the files out, and the new wrapper's promotion installs
  them (out of scope, `prompt.md`).
- The real-forge test on the #10 fixture is out of scope (blocked on the operator's token); its work item stays open
  on #17 until #10 lands.
