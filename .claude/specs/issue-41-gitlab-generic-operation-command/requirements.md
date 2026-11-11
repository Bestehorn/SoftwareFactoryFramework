# Requirements — issue #41: GitLab wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the call mechanism follows the GitHub sibling #28, and the issue's AC-4
covers rather than excludes (DL-001).

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

Part 1 (#13) built `src/payload/scripts/gitlab_api/`: the transport (`transport.Transport`, REST v4 and GraphQL), the
record layer (`registry.RestOperation`, `GraphQLOperation`, `lookup`, `expand`, `encode`, `call`, `pages`), one family
module per family of `docs/api-reference/gitlab/operations-index.md` holding its records and its pending keys, an empty
`graphql_only.py`, the caller-used subcommands in `commands/`, and `test/test_gitlab_wrapper_coverage.py`. A record
reaches the command line only through a caller-used subcommand that sends it. This change makes every record a family
module or `graphql_only.py` declares callable with its documented parameters, records how the call of an operation no
test project can reach is proven, holds the `/<route-prefix>/...` keys and the experimental GraphQL-only capabilities
to the coverage rule, records the reference revision the slices target and how a regeneration reaches the coverage
test, and documents the call. It adds no record (the slices) and promotes nothing.

## Glossary

- **Record** — a `registry.RestOperation` in the `OPERATIONS` of a family module,
  `src/payload/scripts/gitlab_api/families/<family>.py`, or a `registry.GraphQLOperation` in the `OPERATIONS` of
  `gitlab_api/graphql_only.py`.
- **Key** — the `(method, path)` of an index row or of a REST record, the path verbatim
  (`/projects/:id/issues/:issue_iid`).
- **Pending list** — a family module's `PENDING` keys; for the GraphQL-only capabilities, the list `design.md` names.
- **Operation call** — the wrapper invocation that sends one record, named by its operation ID
  (`plan#update-an-issue`). Its spelling — one generic subcommand, per-family command modules, or a mix — is
  `design.md`'s.
- **Documented parameters** — of a REST record: its path parameters (the `:name` placeholders of its `path`,
  `registry.placeholders`) and its `params`, each attribute with its `location` and `Kind`: what the attribute table of
  the operation's section of `docs/api-reference/gitlab/rest/<stage>.md` lists by name, `In` and `Type`. Of a GraphQL
  record: the variables its `document` declares.
- **Caller-used subcommand** — a subcommand of the table of
  `.claude/specs/issue-13-gitlab-wrapper-foundation/requirements.md` UB-1.
- **Unreachable operation** — an operation that the test project of #11's real-instance run and its token cannot
  exercise, because it needs an administrator, acts on the whole instance, or needs GitLab Dedicated or a Geo site.
- **GraphQL-only capability** — a row of the "Only in GraphQL" table of
  `docs/api-reference/gitlab/graphql/conventions.md`, named by its first cell; experimental when a query or mutation it
  names carries `Status: Experiment`.
- **Slice** — one of #35–#40, #42–#44: a change that adds the records of a group of families.

## Requirements

### Requirement 1 — Every declared record is a documented call (issue AC-1)

As a slice worker, I want every record a family module or `graphql_only.py` declares to be callable with its documented
parameters, so that covering a family or a capability is adding records and their tests, never revisiting how a record
reaches the command line.

- AC-1.1 `design.md` SHALL record how a record reaches the command line — one generic operation call over every
  record, per-family command modules, or a mix, and for a mix which records each part serves — and SHALL name every
  file a slice edits to make a record of its family or of `graphql_only.py` callable.
- AC-1.2 WHEN an operation call of a REST record gives a value for each path parameter and any of its attributes, the
  wrapper SHALL send the record's `method` to `/api/v4` followed by the record's `path` with each `:name` replaced by
  its value as `registry.expand` encodes it, the `Location.QUERY` attributes followed by the record's `fixed` pairs as
  the query string, and the `Location.BODY` attributes as a JSON object body when the record's `body` is
  `BodyFormat.JSON` and as a form body when it is `BodyFormat.FORM` (no body when none is given), with the configured
  token type's one credential header (#13 AC-2.1).
- AC-1.3 WHEN an operation call gives an attribute a value, the request SHALL carry the value the caller gave in the
  shape the attribute's `Kind` declares — a string, number or boolean (`SCALAR`), an array (`ARRAY`), an object
  (`HASH`), an array of objects (`ARRAY_OF_HASHES`) — natively in a JSON body and as `registry.encode`'s bracket pairs
  in a query string or a form body (#13 AC-2.3); for a `FILE` attribute, the bytes of the file the caller names, in a
  `multipart/form-data` body that holds every other body attribute as a form field (#13 AC-2.4).
- AC-1.4 WHEN the record's `paging` is `Paging.OFFSET` or `Paging.KEYSET`, the wrapper SHALL request each page as
  `Transport.pages` does (#13 AC-2.5, AC-2.6) and SHALL write to standard output one JSON array, in the form
  `commands/_common.print_json` writes, holding every item of every page in page order.
- AC-1.5 WHEN the record's `paging` is `Paging.NONE` and the response's `Content-Type` is JSON, the wrapper SHALL write
  the parsed body in the form `print_json` writes; WHEN the response body is empty, it SHALL write nothing to standard
  output; either way it SHALL exit 0.
- AC-1.6 WHEN the record's `paging` is `Paging.NONE` and the response's `Content-Type` is not JSON — a job trace, a
  repository file's raw content, an artifacts archive served after a redirect to an object-storage host
  (`docs/api-reference/gitlab/conventions.md` "Responses", "Downloads and redirects") — the wrapper SHALL write the
  body's bytes unchanged to standard output and exit 0.
- AC-1.7 WHEN the transport or the registry raises `GitLabAPIError` for an operation call — `GitLabRateLimitError` and
  `GitLabGraphQLResponseError` included (#13 AC-3.4, AC-3.5, AC-4.3) — the wrapper SHALL write its message and its
  details to standard error and exit 1, as `main` does for a caller-used subcommand.
- AC-1.8 WHEN an operation call names a REST record whose path starts with `/projects/:id` and gives no value for `id`,
  the wrapper SHALL send the `project_id` of `config/gitlab.json` as that value, as the caller-used subcommands do
  (`commands/_common.PATH_PROJECT`).
- AC-1.9 WHEN an operation call names a GraphQL record, the wrapper SHALL send the record's `document` with each given
  variable as the JSON value the caller gave, through `Transport.graphql`, and write `data` in the form `print_json`
  writes — or, for a record with a `connection`, through `Transport.graphql_nodes`, writing one JSON array of the nodes
  of every page (#13 AC-4.1, AC-4.2) — and exit 0.

### Requirement 2 — Refusals before any request (issue AC-2)

As a caller, I want an operation call the wrapper cannot send as written to be refused before anything reaches GitLab,
naming what the record accepts, so that a wrong name never becomes a request and the message carries the correction.

- AC-2.1 WHEN an operation call names an operation ID that no record declares — the ID of a row whose key is only on a
  pending list, or an ID the reference does not hold — the wrapper SHALL send no request, write a message naming that
  ID to standard error, and exit 2, the usage-error code.
- AC-2.2 WHEN an operation call gives a parameter that the record does not document — a path parameter or attribute of
  a REST record, a variable of a GraphQL record — the wrapper SHALL send no request, write to standard error a message
  naming each such parameter and the record's documented parameters, and exit 2.
- AC-2.3 WHEN an operation call leaves a path parameter of the record without a value once AC-1.8 has supplied `id`,
  the wrapper SHALL send no request, write to standard error a message naming that parameter and the record's path
  parameters, and exit 2.
- AC-2.4 WHEN an operation call gives an attribute a value of a shape its `Kind` does not take
  (`registry.KIND_ACCEPTS`: a string for an `ARRAY`, an object for a `SCALAR`), the wrapper SHALL send no request, write
  to standard error a message naming that attribute and its `Kind`, and exit 2.

### Requirement 3 — Proving a call no test project can reach (issue AC-3)

As a slice worker covering administrator, instance, GitLab Dedicated or Geo operations, I want one recorded way to
prove their calls, so that each is covered by evidence a test produces rather than by its declaration alone.

- AC-3.1 `design.md` SHALL record the method that proves the operation call of an unreachable operation, and the rule
  by which a slice tells an unreachable operation from one that #11's test project can exercise.
- AC-3.2 A test SHALL apply that method to the operation call of one unreachable operation and pass, and SHALL show the
  method rejecting a call that differs from that operation's section of `docs/api-reference/gitlab/rest/<stage>.md` in
  its method, its path, or an attribute's name or `In`.

### Requirement 4 — Docs (issue AC-5, the call)

As an agent calling the wrapper, I want the usage docstring and the project map to say how to call an operation, so
that I find the call without reading the package.

- AC-4.1 The module docstring of `src/payload/scripts/gitlab_wrapper.py` SHALL name how to make an operation call: its
  spelling with one example, how path parameters, attributes (a file included) and GraphQL variables are given, how
  list, JSON, empty and other responses print (AC-1.4 to AC-1.6, AC-1.9), and the exit code of a refusal
  (Requirement 2).
- AC-4.2 `docs/forLLMConsumption.md` SHALL name how to make an operation call, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.

### Requirement 5 — Target revision and regeneration (issue AC-5, the reference)

As a slice worker, I want the reference revision the slices target and the way a regeneration reaches the coverage test
recorded, so that a regenerated reference never silently changes what a slice covers.

- AC-5.1 `design.md` SHALL name the revision of `docs/api-reference/gitlab/` the slices target, by the source pin the
  generated banner of `operations-index.md` carries.
- AC-5.2 `design.md` SHALL record how a regeneration of `docs/api-reference/gitlab/` by `scripts/api_reference/build.py`
  reaches `test/test_gitlab_wrapper_coverage.py`: what an added, a removed or a changed key, and a changed attribute of
  a record's operation, does to its tests, and which change brings the family modules back in line.
- AC-5.3 WHEN a regenerated index holds a key that no record maps and no pending list holds, lacks a key that a record
  maps or a pending list holds, or gives the row whose Reference is a record's operation ID another method or path,
  `test/test_gitlab_wrapper_coverage.py` SHALL fail and name that key or ID.

### Requirement 6 — Protocol routes and experiments are covered (issue AC-4)

As the owner of #11, I want the `/<route-prefix>/...` package-manager protocol keys and the experimental GraphQL-only
capabilities held to the rule every other operation is held to — covered, none excluded (DL-001) — so that the
complete set of API features has no silent gap.

- AC-6.1 WHEN a key whose path starts with `/<route-prefix>/` is neither mapped by a record nor on its family's pending
  list, `test/test_gitlab_wrapper_coverage.py` SHALL fail and name that key, as for any other key.
- AC-6.2 WHEN a GraphQL-only capability, experimental or not, is neither served by a `graphql_only.py` record nor on a
  pending list, `test/test_gitlab_wrapper_coverage.py` SHALL fail and name that capability.
- AC-6.3 WHEN this change is complete, `test/test_gitlab_wrapper_coverage.py` SHALL pass with every
  `/<route-prefix>/...` key mapped or pending and every GraphQL-only capability pending.

## Unchanged behaviour

- UB-1.1 Every caller-used subcommand, run as `python scripts/gitlab_wrapper.py <argv>`, SHALL CONTINUE TO accept the
  argv and return the exit codes its callers use (#13 UB-1), the delivery verbs still passed unparsed to
  `steward_delegate`: `src/payload/test/test_gitlab_wrapper_compat.py` SHALL CONTINUE TO pass with no existing case,
  spelling or assertion edited; this change only adds tests.
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `config/gitlab.json` (`_load_config`) — never from an
  environment variable, an argument or another file; no operation call takes a token option
  (`test_gitlab_wrapper_compat.py` `test_load_config_refusals`, `test_environment_token_ignored`).
- UB-2.2 The entry script and `src/payload/scripts/gitlab_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_gitlab_api_properties.py` `test_standard_library_only`).
- UB-3.1 `src/payload/scripts/github_wrapper.py`, `src/payload/scripts/github_api/`, their tests
  (`src/payload/test/*github*.py`, `test/*github*.py`) and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE
  TO be untouched by this change and to pass.

## Residuals

- Request forms part 1's transport does not build — `*name` globs, optional `(…)` segments, the `<route-prefix>`
  choice, `https://HOST` paths, a raw-bytes body (generic packages), GraphQL multipart uploads — stay with the slice
  whose family needs one (#13 `design.md` D2 and Residuals); AC-6.1 counts those keys now.
- Required attributes (`Param.required`) are not checked before a request; the host's error status exits 1 by AC-1.7.
- A `null` attribute value is not in AC-1.3 (`registry.encode` sends no `None`).
- AC-3 proves REST sections; proving a GraphQL record's call against `docs/api-reference/gitlab/graphql/` is not in it.
- The real-instance run is #11's; promoting the new wrapper is out of scope.
