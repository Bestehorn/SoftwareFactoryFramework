# Requirements — issue #30: GitHub wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the issue's open questions are design choices settled in `design.md`
(DL-001). Builds on `.claude/specs/issue-28-generic-operation-command/` ("#28 AC-n", "#28 Dn").

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed (aafecbb) and unblocked the slices; selected issue #30, "GitHub wrapper rewrite, part 2
   slice: the GraphQL-only capabilities", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Introduction

Part 1 (#17) declared the record type `registry.GraphQLOperation` (`capability`, `document`, `connection`) and the
module `src/payload/scripts/github_api/graphql_only.py`, whose `OPERATIONS` is empty and whose `PENDING_CAPABILITIES`
holds the first cell of every row of the "Only in GraphQL" table of `docs/api-reference/github/graphql/conventions.md`.
#28 added `call <operation-id>`, which sends a `RestOperation` of a family module; `registry.lookup` finds only those,
so no GraphQL record is callable today. This change declares the records that serve each capability, makes each
callable through `call` over `Transport.graphql` and `Transport.graphql_nodes`, refuses before any request the
mutations that write a branch, arrange a merge or move an issue outside the subcommands the hook gates judge, and
documents the call.

## Glossary

- **Capability** — the first cell of a row of the "Only in GraphQL" table, verbatim. Its **members** are the mutations
  and fields the row's GraphQL cell names in code spans, without arguments (`Repository.mergeQueue(branch:)` names the
  field `mergeQueue` of `Repository`).
- **GraphQL record** — a `registry.GraphQLOperation` in `graphql_only.OPERATIONS`. Whether a capability has one record
  or one per member is `design.md`'s.
- **Declared variables** — the `$name` variable definitions of a record's `document`, except the `$after` of a record
  that pages a connection, which `Transport.graphql_nodes` sets on every page.
- **GraphQL call** — `python scripts/github_wrapper.py call <operation-id> …` naming a GraphQL record. How a variable's
  value is spelled on the command line is `design.md`'s.
- **Fake host** — the recording host of `src/payload/test/github_wrapper_fixtures.py` (#17 Testing Strategy).

## Requirements

### Requirement 1 — Every capability has its records (issue AC-1, AC-5)

As a caller of the wrapper, I want every "Only in GraphQL" capability served by declared records, so that the coverage
test counts it as covered, never as pending.

- AC-1.1 `design.md` SHALL record: whether a capability has one record or one per member; the operation ID each
  GraphQL record is called by; what a record that pages no connection holds in `connection`; how a caller obtains the
  global node IDs a mutation's `input` takes (`conventions.md` "Global node IDs", "Mutations"); and which members an
  `sff-test-*` repository cannot exercise, with what proves their call.
- AC-1.2 Every capability SHALL be the `capability` of at least one GraphQL record, every GraphQL record's
  `capability` SHALL be a capability, and `graphql_only.PENDING_CAPABILITIES` SHALL be empty.
- AC-1.3 For each capability, the documents of its records SHALL together select every member its row names.
- AC-1.4 Each GraphQL record's operation ID SHALL differ from every other GraphQL record's and from every operation ID
  of `docs/api-reference/github/operations-index.md`.
- AC-1.5 `test/test_github_wrapper_coverage.py` `test_every_operation_is_covered_or_pending` and
  `test_one_module_per_family_holding_only_its_own_ids` SHALL pass.

### Requirement 2 — A GraphQL call sends its record and prints its result (issue AC-2, AC-3, AC-4)

As a caller, I want to call a capability the way I call a REST record, so that a GraphQL-only capability needs no
other command and fails the way a REST call fails.

- AC-2.1 WHEN a GraphQL call that runs no mutation of AC-3.1 gives values for declared variables, the wrapper SHALL
  send one `POST` to `https://api.github.com/graphql` as `Transport.graphql` sends it, whose JSON body's `query` is the
  record's `document` and whose `variables` hold each given variable with the JSON value the caller gave: a string,
  number, boolean, array, object or `null`.
- AC-2.2 WHEN the record pages a connection, the wrapper SHALL ask for each next page with the previous page's
  `pageInfo.endCursor` as `after` while `hasNextPage` is `true`, as `Transport.graphql_nodes` does, SHALL write to
  standard output, once the last page has arrived, one JSON array in the form `commands/_common.print_json` writes,
  holding every node of every page in page order, and SHALL exit 0.
- AC-2.3 WHEN the record pages no connection, the wrapper SHALL write the response's `data` in the form `print_json`
  writes and exit 0.
- AC-2.4 WHEN the transport raises `GitHubAPIError` for a GraphQL call — a response with a top-level `errors` member,
  with or without `data` (`GitHubGraphQLResponseError`), an HTTP error, a spent rate limit, no response, or a page
  without its connection — the wrapper SHALL write nothing to standard output, write the error's message and its
  details (for `errors`, the `errors` array) to standard error, and exit 1, as #28 AC-1.7 states for a REST record.
- AC-2.5 WHEN a GraphQL call gives a variable that the record's document does not declare, the wrapper SHALL send no
  request, write to standard error a message naming that variable and the record's declared variables, and exit 2
  (`EXIT_REFUSED`), as #28 AC-2.2 states for an undocumented parameter.
- AC-2.6 Each GraphQL record whose call runs no mutation of AC-3.1 SHALL have a test that runs its GraphQL call through
  the product's `main` against the fake host and asserts the posted `query` and `variables` and the standard output;
  for a record that pages a connection, across two pages.

### Requirement 3 — Refused before any request

As the operator, I want `call` to write no branch, arrange no merge and add no issue to a repository, so that those
effects reach GitHub only through the subcommands the hook gates judge (#28 Security Considerations "Gates", #27
AC-7, #32 AC-6).

- AC-3.1 WHEN a GraphQL call would run a mutation that commits to or creates a branch (`createCommitOnBranch`,
  `revertPullRequest`), sets a pull request to merge into its base branch (`enablePullRequestAutoMerge`) or moves an
  issue into another repository (`transferIssue`), the wrapper SHALL send no request, log the operation ID and the
  mutation's name, and exit 2.
- AC-3.2 The refusal of `enablePullRequestAutoMerge` SHALL name `merge-pr`, the subcommand that sends a merge, as #32
  AC-6 does for `pulls/merge-async`; the refusal of each other mutation of AC-3.1 SHALL state that no subcommand sends
  it, as #27 AC-7 does.
- AC-3.3 A test SHALL run a GraphQL call of each mutation of AC-3.1 through the product's `main` against the fake host
  and assert exit 2, no recorded request, and AC-3.2's log.

### Requirement 4 — Docs (issue AC-5)

As an agent calling the wrapper, I want the usage docstring and the project map to say how to call a capability, so
that I find the call without reading the package.

- AC-4.1 The module docstring of `src/payload/scripts/github_wrapper.py` SHALL name the operation ID of every GraphQL
  record with its capability, how a GraphQL call gives a variable, how a connection and a result without one print
  (AC-2.2, AC-2.3), and that AC-3.1's mutations are refused with exit 2.
- AC-4.2 `docs/forLLMConsumption.md` SHALL name how to make a GraphQL call, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.

## Unchanged behaviour

- UB-1.1 Every caller-used subcommand (#28 Glossary), run as `python scripts/github_wrapper.py <subcommand> …`, SHALL
  CONTINUE TO accept the same arguments, write the same standard output and return the same exit codes:
  `src/payload/test/test_github_wrapper_compat.py` over the golden `CASES` of
  `src/payload/test/github_wrapper_fixtures.py`, and `test/test_github_wrapper_fork_parity.py`, SHALL CONTINUE TO pass
  with no existing case, spelling or assertion edited.
- UB-1.2 `call` SHALL CONTINUE TO send and print every `RestOperation` as #28 AC-1 states, and to refuse with exit 2
  and no request an ID no record declares and `pulls/merge` and `issues/create`, naming `merge-pr` and
  `create-issue`: `src/payload/test/test_github_api_call.py` and `test/test_github_wrapper_contract.py` SHALL CONTINUE
  TO pass.
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `credentials/github-pat.txt` (`_load_token`) —
  never from an environment variable, an argument or another file; no GraphQL call takes a token option.
- UB-2.2 The entry script and `src/payload/scripts/github_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_github_wrapper_coverage.py` `test_the_wrapper_imports_only_the_standard_library`).
- UB-3.1 `src/payload/scripts/gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be
  untouched by this change and to pass.

## Out of scope

- The members a row elides with `...` (the discussions and Sponsors rows): AC-1.3 covers the members a row names.
- The REST families (#27, #29, #31, #32, #33), the GitLab twin (#44), the hook gates, and promoting the product wrapper
  over the installed fork.
- The real-forge run on an `sff-test-*` repository: #10's fixture. Until it exists, AC-2.6's and AC-3.3's tests run
  each call through `main` up to the API boundary in CI.

## Residuals

- `createBranchProtectionRule` stays callable: it writes no branch, as #27 keeps branch protection callable; its input
  sets `allowsDeletions` and `allowsForcePushes` for any `pattern`, the trunk's included.
- `deleteProjectV2` and `createSponsorship` stay callable; whether to run one is the caller's decision (#28 Security
  Considerations "Destructive operations").
- A non-null variable left without a value is not refused before a request; GitHub's `errors` answer exits 1 by
  AC-2.4, as #28 Residuals leaves required REST parameters to the host.
