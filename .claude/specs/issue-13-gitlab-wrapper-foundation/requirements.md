# Requirements — issue #13: GitLab wrapper rewrite, part 1 (foundation)

Tier: M. Kind: FEATURE. Parent: #11. Part 2: #15. GitHub sibling: #17.

## Overview

The product GitLab wrapper `src/payload/scripts/gitlab_wrapper.py` is a skeleton: `main` raises
`NotImplementedError`; `_load_config`, `_api_request` (one REST call with `PRIVATE-TOKEN`, no paging, no retry),
`GitLabAPIError`, `pipeline_wait` and `steward_delegate` exist, and the module docstring lists the subcommands.
This change builds the foundation of #11: the operation-layer decision, a REST v4 and GraphQL transport that
applies `docs/api-reference/gitlab/conventions.md` and `docs/api-reference/gitlab/graphql/conventions.md`, the
subcommands callers use served from that transport, and the coverage test part 2 drives to green. The remaining
endpoint families are part 2; the real-instance test target stays on #11.

E2E: not applicable in this change — nothing deployed changes; the real-instance run stays on #11. Fake-host unit
tests (no network) cover the transport and every subcommand; CI's `tests` group runs them.

Design inputs (not criteria):

- The operation-layer structure matches the GitHub sibling #17, worked in parallel, where the forges allow;
  design.md records each deliberate difference (DL-001).
- Callers reach the wrapper as the one file `scripts/gitlab_wrapper.py`: `hooklib.project_wrapper` discovers it,
  `gate_merge_steward.SCRIPT_KINDS` names it, the setup prompts copy it (`prompts/setup-claude.txt` Part 5.3,
  `prompts/setup-kiro.txt` Part 6.2 — with its package after this change, design.md "Install path"), and
  `src/payload/test/test_wrapper_delivery.py` loads it from its file path.
- `docs/api-reference/` is this repository's documentation and does not ship to projects (`file-organization.md`);
  the coverage test lives where `operations-index.md` exists.
- GraphQL documents only `Authorization: Bearer`, and a CI/CD job token cannot authenticate GraphQL
  (`graphql/conventions.md` "Credentials").

## Glossary

- **Transport** — the code that turns one operation call into HTTP requests and their responses, REST v4 or
  GraphQL.
- **Operation layer** — the code between the subcommands and the transport that names each GitLab endpoint the
  wrapper serves.
- **Endpoint family** — a group of `operations-index.md` rows that part 2 adds as one unit; design.md fixes the
  grouping.
- **Mapped** — an `operations-index.md` row (method and path) that the operation layer serves.
- **Pending list** — the rows of one endpoint family that are not yet mapped.
- **Token type** — the header the configured token is sent in: `PRIVATE-TOKEN`, `Authorization: Bearer` or
  `JOB-TOKEN`.

## Requirements

### Requirement 1 — Operation layer and per-family layout (issue AC-1)

**User story:** As a part-2 worker on #15, I want each endpoint family in files of its own, so that workers adding
families in parallel never edit the same file.

- **AC-1.1** design.md SHALL record the operation-layer decision — generic and driven by `docs/api-reference/gitlab/`,
  hand-written per operation, or a mix — and, for a mix, which operations each approach serves.
- **AC-1.2** The layout SHALL let each part-2 endpoint family be added without editing a file another family edits,
  its pending-list file (AC-5.2) included.
- **AC-1.3** IF a file that more than one family edits remains, THEN design.md SHALL name it with the reason it
  cannot be split.

### Requirement 2 — REST v4 transport (issue AC-2)

**User story:** As an agent running a subcommand, I want one REST transport that applies GitLab's documented
conventions, so that every operation sends correct requests without restating them.

- **AC-2.1** WHEN a REST v4 request is sent, the transport SHALL send the token in exactly one header, the one of
  the configured token type: `PRIVATE-TOKEN: <token>`, `Authorization: Bearer <token>` or `JOB-TOKEN: <token>`.
- **AC-2.2** WHEN a value is substituted into a path parameter (a project id or full path, a branch, a file path,
  a tag), the transport SHALL percent-encode it as one path segment, `/` encoded as `%2F` (`conventions.md`
  "URL-encoding path parameters").
- **AC-2.3** WHEN an array, a hash or an array of hashes is sent in a query string or a form body, the transport
  SHALL encode it in a bracket form `conventions.md` "Arrays, hashes and arrays of hashes" documents
  (`key[]=a&key[]=b`, `key[sub]=v`, `key[0][sub]=v`); in a JSON body it SHALL send JSON arrays and objects.
- **AC-2.4** WHEN a request carries a file, the transport SHALL send a `multipart/form-data` body with the file under
  its field name and every other parameter as a form field.
- **AC-2.5** WHEN a list operation is called, the transport SHALL follow offset pagination by `x-next-page` or the
  `Link` header's `rel="next"` until it is absent or empty, never by `x-total-pages`, and return the items of every
  page.
- **AC-2.6** WHERE an endpoint offers only keyset pagination, the transport SHALL follow the `Link` header's
  `rel="next"` URL unchanged until it is absent, and return the items of every page.

### Requirement 3 — Redirects, rate limits and errors (issue AC-3)

**User story:** As an operator, I want the token never to reach a host other than mine and every failure to surface
as one exception, so that a credential cannot leak and a caller can rely on exit code 1.

- **AC-3.1** WHEN a response redirects to a host other than the configured one, the transport SHALL NOT send
  `PRIVATE-TOKEN` or `JOB-TOKEN` to that host.
- **AC-3.2** WHEN a response is `429` with a `Retry-After` header, the transport SHALL wait that many seconds and then
  retry the request.
- **AC-3.3** WHEN a response is `429` without `Retry-After` and without `RateLimit-*` headers (GitLab.com sends such
  responses from the Projects, Groups and Users APIs), the transport SHALL retry after a backoff that grows with each
  consecutive `429`.
- **AC-3.4** IF a request is still answered `429` when the transport's bounded retries are spent, THEN it SHALL raise
  `GitLabAPIError` with `status_code` 429.
- **AC-3.5** IF a response status is 400 or above, THEN the transport SHALL raise `GitLabAPIError` with that status as
  `status_code`, the raw body as `details`, and a message carrying the error text of each body shape
  `conventions.md` "Body shapes" documents: `message` as a string; `message` as a field hash, flattened to
  `field: message` pairs; `error` with `error_description`; the OAuth scope error; the spam hash; a non-JSON body
  kept as text.

### Requirement 4 — GraphQL transport (issue AC-4)

**User story:** As a part-2 worker, I want a GraphQL request path beside REST, so that an operation only GraphQL
offers is served by the same wrapper.

- **AC-4.1** WHEN a GraphQL call is made, the transport SHALL POST a JSON body `{"query": ..., "variables": ...}` to
  `/api/graphql` on the configured host, not under `/api/v4`.
- **AC-4.2** WHEN a GraphQL call pages a connection, the transport SHALL re-issue it with `after` set to the previous
  `pageInfo.endCursor` while `pageInfo.hasNextPage` is true, and return the nodes of every page.
- **AC-4.3** IF a GraphQL response carries a non-empty top-level `errors` array, or a mutation payload whose own
  `errors` list is non-empty, THEN the transport SHALL raise `GitLabAPIError` with those messages, also when the
  HTTP status is `200` and partial `data` is present.

### Requirement 5 — Coverage test (issue AC-5)

**User story:** As the owner of #11, I want a test that names every endpoint the wrapper does not serve yet, so that
part 2 is done exactly when its pending lists are empty.

- **AC-5.1** The coverage test SHALL read every method-and-path row of `docs/api-reference/gitlab/operations-index.md`
  and fail, naming each such row, for any row that is neither mapped nor on a pending list.
- **AC-5.2** The pending list SHALL be one file per endpoint family (DL-001), and the coverage test SHALL read every
  family's file without a shared file that enumerates them.
- **AC-5.3** WHEN this change is complete, the coverage test SHALL pass: every row this change does not map is on its
  family's pending list.
- **AC-5.4** The coverage test SHALL run without network access in the suite CI's `tests` group runs.

## Unchanged behaviour

- **UB-1** Every subcommand below — the docstring's, plus the caller-used ones it omits (marked †) — SHALL CONTINUE
  TO accept the argv and return the exit codes its callers use, now served by the new transport.

  | Argv | Exit codes callers read | Callers |
  |---|---|---|
  | `pipeline status` [`--count N`†] | 0; 1 | docstring; `--count`: `prompts/setup-kiro.txt` Part 6.3 |
  | `pipeline log` | 0; 1 | docstring; `prompts/setup-claude.txt` Part 5.3 |
  | `pipeline wait <pipeline_id> --timeout-seconds N` | 0 success, 10 not success, 11 timeout | `clients/claude/rules/ci-owns-the-test-suite.md`; `clients/claude/commands/close-session.md` Step 3 |
  | `issue list` [`--state`] [`--assignee <user>`\|`"*"`\|`none`] [`--labels L`] | 0; 1 | docstring; `prompts/setup-claude.txt` Part 5.3 |
  | `issue show <iid>` † | 0; 1 | `clients/kiro/prompts/close-session.md` Step 2; `prompts/setup-claude.txt` Part 5.3; `prompts/setup-kiro.txt` Part 6.2 |
  | `issue create --title T` [`--description D`†] [`--labels L`] | 0; 1 | docstring; `src/hooks/gate_filing.py` (recognises `issue create`); `--description`: `prompts/setup-kiro.txt` PART 13 |
  | `issue comment <iid> --body B` | 0; 1 | docstring |
  | `issue start <iid>` | 0 claim verified; non-zero otherwise | `src/hooks/gate_claim.py` `run`; `clients/claude/commands/work-issue.md` |
  | `issue claim-check <iid>` | 0 claimed or not open; 3 open and unclaimed | `src/hooks/gate_claim.py` `run` |
  | `issue release <iid>` | 0; 1 | `clients/claude/commands/auto-work.md`; `clients/claude/agents/issue-work-orchestrator.md` |
  | `issue label-add <iid> --labels L` | 0; 1 | docstring; `clients/claude/rules/issue-tracking.md` |
  | `issue label-remove <iid> --labels L` † | 0; 1 | `clients/claude/rules/issue-tracking.md`; both `issue-work-orchestrator.md`; `clients/claude/commands/work-issue.md`; `clients/kiro/prompts/close-session.md` Step 6 |
  | `issue assign <iid> --me` \| `--user U`† \| `--unassign`† | 0; 1 | docstring; `--unassign`: `clients/kiro/prompts/close-session.md` Step 6; `--user`: `prompts/setup-claude.txt` Part 5.3 |
  | `issue close <iid>` | 0; 1 | docstring |
  | `issue reopen <iid>` | 0, also for an issue already open; 1 | `clients/claude/rules/issue-tracking.md`; `clients/claude/commands/close-session.md` Step 2 |
  | `label list` †, `label create` † (no caller fixes their options) | 0; 1 | `prompts/setup-claude.txt` Part 5.3; `prompts/setup-kiro.txt` Part 6.2 |
  | `mr create --source B --target T --title X` | 0; 1 | docstring; `prompts/setup-claude.txt` Part 5.3 |
  | `mr get <mr_iid>`, `mr checks <mr_iid>`, `mr approve <mr_iid>` | 0; 1 | docstring; `prompts/setup-claude.txt` Part 5.3 |
  | `mr merge <mr_iid>` | 0; 1 | `src/hooks/gate_merge_steward.py` (matches the tokens `mr merge` after the script) |
  | `delete-branch <branch>` | 0; 1 | docstring |
  | `enqueue-pr <mr_iid>`, `dequeue-pr <mr_iid> --reason R`, `queue-status` [`--json`], `wait-landed <mr_iid> --timeout-seconds N`, `check-handoff <iid>`, `check-landed <mr_iid> ...` | the steward's code passed through by `steward_delegate`; `EXIT_DELIVERY_ELSEWHERE` on a host that is not the queue's | `src/hooks/gate_issue_loop.py` `_wrapper_verdict` (`check-handoff`, `check-landed`: 0 or 4); `src/payload/test/test_wrapper_delivery.py` |

  Across the table, a `GitLabAPIError` SHALL CONTINUE TO exit 1 and a usage error 2, which `gate_claim.py` reads as
  no verdict. `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO pass unchanged. The command strings in
  `src/hooks/tests/test_no_sleep.py` and `src/hooks/tests/test_delivery_gates.py` are gate-parsing fixtures and set
  no argv.
- **UB-2** The wrapper SHALL CONTINUE TO use only the Python 3.9+ standard library and to read credentials only from
  `config/gitlab.json`, never from an environment variable. A `config/gitlab.json` holding only the keys of
  `templates/config/gitlab.json.template` (`hostname`, `project_id`, `token`, `in_progress_label`) SHALL CONTINUE TO
  be accepted and to send `PRIVATE-TOKEN`, with `in_progress_label` defaulting to `in-progress`; `_load_config`
  SHALL CONTINUE TO raise `GitLabAPIError` for a missing file or a `PASTE_` placeholder. The `token` key stays the
  one `merge_steward.read_token` reads.
- **UB-3** `src/payload/scripts/github_wrapper.py` and its tests, `src/payload/test/test_wrapper_delivery.py`
  included, SHALL CONTINUE TO be untouched by this change.

## Residuals

- Checklist toggle, due date, time spent and parent link: callers name them ("the wrapper's checklist toggle",
  `clients/claude/commands/close-session.md` Step 2; the best-effort list in `issue-work-orchestrator.md`) but no
  GitLab argv exists in the docstring or any caller; giving them one is new interface → part 2, #15.
- `Authorization: Bearer` across hosts: `conventions.md` "Do not forward the token" says `urllib` copies every header
  but `Content-Length` and `Content-Type` to the redirect target; AC-3.1 names the two headers the ask names →
  closed by design.md "Redirects (AC-3.1)"; no criterion added.
- A base URL with a relative URL root (`conventions.md` "Hosts and base URLs"): the config carries `hostname` only →
  #11.
- AC-5 checks one direction: a mapped or pending entry that names no index row is not flagged → findings ledger if
  wanted.
- The real-instance end-to-end run → #11.

## User Prompts

- The run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end" (`/auto-work`).
- Issue #13 title: "GitLab wrapper rewrite, part 1: design, core transport, today's subcommands, coverage test".
- The operator's ask, as the issue quotes it: "The operator asked to split #11 and its GitHub sibling #12 into two
  children each: a foundation, then the remaining coverage."
