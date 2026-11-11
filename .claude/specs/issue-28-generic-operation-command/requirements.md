# Requirements — issue #28: GitHub wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the issue's open questions are design choices settled in `design.md`
(DL-001).

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end, following
  `.claude/agents/issue-work-orchestrator.md` exactly."
- The backlog run: "#14 re-assessed after part 1 landed and split into children; selected issue #28, "GitHub wrapper
  rewrite, part 2a: generic operation command, coverage-proof method, docs", and derived `prompt.md` from the issue
  body; no interview (see `qa_log.md`)."
- The operator's ask, relayed in #14: "The operator asked to split #12 and its GitLab sibling #11 into two children
  each: a foundation, then the remaining coverage."

## Overview

Part 1 (#17) built `src/payload/scripts/github_api/`: the transport, the record layer (`registry.RestOperation`,
`lookup`, `expand`, `call`, `pages`), one family module per family of `docs/api-reference/github/operations-index.md`
holding its records and its pending list, and the caller-used subcommands in `commands/`. A record reaches the
command line only through a caller-used subcommand that sends it. This change makes every record a family module
declares callable with its documented parameters, records how the call of an operation no test repository can reach
is proven, records the index revision the slices target and how a regeneration reaches the coverage test, and
documents the call. It adds no record to a family module (the slices), no call of a GraphQL capability (#30), and
promotes nothing over the installed fork.

## Glossary

- **Record** — a `registry.RestOperation` in the `OPERATIONS` of a family module,
  `src/payload/scripts/github_api/families/<family>.py`.
- **Pending list** — a family module's `PENDING`; for the "Only in GraphQL" capabilities,
  `graphql_only.PENDING_CAPABILITIES`.
- **Operation call** — the wrapper invocation that sends one record, named by its operation ID. Its spelling — one
  generic subcommand, per-family command modules, or a mix — is `design.md`'s.
- **Documented parameters** — a record's path parameters (the `{name}` placeholders of its `path`), its
  `query_params` and its `body_params` (top-level fields of the JSON request body): what the operation's section of
  `docs/api-reference/github/rest/<category>.md` lists.
- **Caller-used subcommand** — a subcommand of the set that UB-1.1 of
  `.claude/specs/issue-17-github-wrapper-foundation/requirements.md` lists: what `clients/`, `src/hooks/` and
  `src/payload/` invoke today.
- **Unreachable operation** — an operation that an ephemeral `sff-test-*` repository and its token cannot exercise,
  because it acts on an enterprise, an organisation, billing or a GitHub App.
- **Slice** — one of #27, #29, #31, #32, #33: a change that adds the records of a group of families.

## Requirements

### Requirement 1 — Every declared record is a documented call (issue AC-1)

As a slice worker, I want every record a family module declares to be callable with its documented parameters, so
that covering a family is adding records and their tests, never revisiting how a record reaches the command line.

- AC-1.1 `design.md` SHALL record how a record reaches the command line — one generic operation call over every
  record, per-family command modules, or a mix, and for a mix which records each part serves — and SHALL name every
  file a slice edits to make a record of its family callable.
- AC-1.2 WHEN an operation call gives a value for each path parameter of the record and any of its documented query
  and body parameters, the wrapper SHALL send the record's `method` to the record's `path` with each `{name}`
  replaced by its value as `registry.expand` encodes it, the given query parameters as the query string, the given
  body parameters as a JSON object body (no body when none is given), and the record's `api_version` and `accept`.
- AC-1.3 WHEN an operation call gives a body parameter, the request body SHALL hold that member with the JSON value
  the caller gave: a string, number, boolean, array, object or `null`.
- AC-1.4 WHEN the record's `paging` is `Paging.LINK`, the wrapper SHALL request each page by the previous response's
  `rel="next"` target, as `Transport.pages` does, and SHALL write to standard output one JSON array, in the form
  `commands/_common.print_json` writes, holding every item of every page in page order — for a record with an
  `item_key`, the items under that key.
- AC-1.5 WHEN the record's `paging` is `Paging.NONE` and the response body is JSON, the wrapper SHALL write the parsed
  body in the form `print_json` writes; WHEN the response body is empty, it SHALL write nothing to standard output;
  either way it SHALL exit 0.
- AC-1.6 WHEN the response body of an operation call is not a JSON document — an archive served after a `302` to a
  storage host, a `diff`, a file's raw bytes, rendered HTML — the wrapper SHALL write the body's bytes unchanged to
  standard output and exit 0.
- AC-1.7 WHEN the transport raises `GitHubAPIError` for an operation call (#17 AC-3.3, AC-3.4), the wrapper SHALL
  write its message and its details to standard error and exit 1, as it does for a caller-used subcommand.

### Requirement 2 — Refusals before any request (issue AC-2)

As a caller, I want an operation call the wrapper cannot send as written to be refused before anything reaches
GitHub, naming what the record accepts, so that a wrong name never becomes a request and the message carries the
correction.

- AC-2.1 WHEN an operation call names an operation ID that no record declares — one only on a pending list, or one
  the index does not hold — the wrapper SHALL send no request, write a message naming that ID to standard error, and
  exit 2 (`EXIT_REFUSED`, the usage-error code).
- AC-2.2 WHEN an operation call gives a path, query or body parameter that the record does not document, the wrapper
  SHALL send no request, write to standard error a message naming each such parameter and the record's documented
  path, query and body parameters, and exit 2.
- AC-2.3 WHEN an operation call leaves a path parameter of the record without a value, the wrapper SHALL send no
  request, write to standard error a message naming that parameter and the record's path parameters, and exit 2.

### Requirement 3 — Proving a call no test repository can reach (issue AC-3)

As a slice worker covering enterprise, organisation, billing or apps operations, I want one recorded way to prove
their calls, so that each is covered by evidence a test produces rather than by its declaration alone.

- AC-3.1 `design.md` SHALL record the method that proves the operation call of an unreachable operation, and the
  rule by which a slice tells an unreachable operation from one an `sff-test-*` repository can exercise.
- AC-3.2 A test SHALL apply that method to the operation call of one unreachable operation and pass, and SHALL show
  the method rejecting a call that differs from that operation's section of
  `docs/api-reference/github/rest/<category>.md` in its method, its path or a parameter name.

### Requirement 4 — Docs (issue AC-4)

As an agent calling the wrapper, I want the usage docstring and the project map to say how to call an operation, so
that I find the call without reading the package.

- AC-4.1 The module docstring of `src/payload/scripts/github_wrapper.py` SHALL name how to make an operation call:
  its spelling with one example, how path, query and body parameters are given, how list, JSON and non-JSON
  responses print (AC-1.4 to AC-1.6), and the exit code of a refusal (Requirement 2).
- AC-4.2 `docs/forLLMConsumption.md` SHALL name how to make an operation call, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.

### Requirement 5 — Target revision and regeneration (issue AC-5)

As a slice worker, I want the index revision the slices target and the way a regeneration reaches the coverage test
recorded, so that a regenerated reference never silently changes what a slice covers.

- AC-5.1 `design.md` SHALL name the revision of `docs/api-reference/github/operations-index.md` the slices target, by
  the source pin its generated banner carries.
- AC-5.2 `design.md` SHALL record how a regeneration of `docs/api-reference/github/` by
  `scripts/api_reference/build.py` reaches `test/test_github_wrapper_coverage.py`: what an added, a removed or a
  changed operation, and a changed parameter of a record's operation, does to its tests, and which change brings the
  family modules back in line.
- AC-5.3 WHEN a regenerated index holds an operation ID that no record or pending list holds, lacks one that a record
  or a pending list holds, or gives a record's operation ID another method or path,
  `test/test_github_wrapper_coverage.py` SHALL fail and name that ID.

## Unchanged behaviour

- UB-1.1 Every caller-used subcommand, run as `python scripts/github_wrapper.py <subcommand> …`, SHALL CONTINUE TO
  accept the same arguments, write the same standard output and return the same exit codes (#17 UB-1.1, UB-1.2):
  `src/payload/test/test_github_wrapper_compat.py` over the golden `CASES` of
  `src/payload/test/github_wrapper_fixtures.py`, and `test/test_github_wrapper_fork_parity.py`, SHALL CONTINUE TO
  pass with no existing case, spelling or assertion edited; this change only adds cases.
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `credentials/github-pat.txt` (`_load_token`) —
  never from an environment variable, an argument or another file; no operation call takes a token option.
- UB-2.2 The entry script and `src/payload/scripts/github_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_github_wrapper_coverage.py` `test_the_wrapper_imports_only_the_standard_library`).
- UB-3.1 `src/payload/scripts/gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be
  untouched by this change and to pass.

## Residuals

- The call of a `GraphQLOperation` of `graphql_only.py`: #30 (no family module declares one, so AC-1 does not reach it).
- Non-JSON request bodies — `repos/upload-release-asset` (`Transport.upload`), `markdown/render-raw`: #27 and #33, by
  #17 `design.md` D2's table of shared files.
- Choosing per call among an operation's "Media types named in the docs" (`diff`, `patch`, `raw`) is not in AC-1; a
  record sends its one `accept`.
- Required query and body parameters are not checked before a request (a record carries no required flag); the host's
  error status exits 1 by AC-1.7.
- #17's `307` re-send for `PATCH`/`DELETE /repos/{owner}/{repo}` stays with #27, which declares those records.
- The real-forge run is #10's fixture; promoting the new wrapper over the installed fork is out of scope.
