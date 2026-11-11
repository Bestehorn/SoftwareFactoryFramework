# Requirements — issue #44: GitLab wrapper rewrite, part 2 slice: the GraphQL-only capabilities

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the issue's open questions are design choices settled in `design.md`
(DL-001). Builds on `.claude/specs/issue-41-gitlab-generic-operation-command/` ("#41 AC-n", "#41 Dn").

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #44, "GitLab wrapper rewrite, part 2 slice:
   the GraphQL-only capabilities", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Introduction

Part 1 (#13) declared the record type `registry.GraphQLOperation` and the module
`src/payload/scripts/gitlab_api/graphql_only.py`, whose `OPERATIONS` is empty. #41 gave the record its `capability`,
put the first cell of every row of the "Only in GraphQL" table of `docs/api-reference/gitlab/graphql/conventions.md` on
`graphql_only.PENDING_CAPABILITIES`, added the capability check of `test/test_gitlab_wrapper_coverage.py`
(`capability_problems`), and made `call <operation-id>` send a GraphQL record's document with the `-f`/`-F` values as
its variables (`registry.call`, #41 AC-1.9). No GraphQL record exists, so no capability is callable. Every capability
is in scope, experimental or not (#41 DL-001, D6). This change declares the records that serve each capability, sends
a mutation that takes an `Upload` as the multipart request of `conventions.md` "File uploads" (`Transport.graphql`
sends a JSON body only), refuses before any request the mutations that create a work item, and documents the call.

## Glossary

- **Capability** — the first cell of a row of the "Only in GraphQL" table, verbatim. Its **members** are the names the
  row's GraphQL cell writes in code spans — root fields (`workItem`, `Query.vulnerabilities`), object fields
  (`Project.workItems`), mutations (`workItemCreate`) and types (`WorkItem`) — each with the argument or selection its
  span gives (`pipelineCreate(async: true)`, `queryComplexity { score limit }`).
- **GraphQL record** — a `registry.GraphQLOperation` in `graphql_only.OPERATIONS`. Whether a capability has one record
  or one per member is `design.md`'s.
- **Declared variables** — the variables `registry.variables` names: the `$name` definitions of a record's `document`,
  except the `$after` of a record with a `connection`, which `Transport.graphql_nodes` sets on every page.
- **Upload value** — a place in a record's variables that the GraphQL reference types `Upload`: a declared variable, an
  input field of one (`DesignManagementUploadInput.files`, `WorkItemsCsvImportInput.file`), or an item of a list of
  them.
- **GraphQL call** — `python scripts/gitlab_wrapper.py call <operation-id> …` naming a GraphQL record. How an Upload
  value's file is given on the command line is `design.md`'s; variables are given as #41 D2 states.
- **Fake host** — the recording host `FakeGitLab` of `src/payload/test/gitlab_wrapper_fixtures.py`.

## Requirements

### Requirement 1 — Every capability has its records (issue AC-1, AC-5)

As a caller of the wrapper, I want every "Only in GraphQL" capability served by declared records, so that the coverage
test counts it as served, never as pending.

- AC-1.1 `design.md` SHALL record: whether a capability has one record or one per member, and which records have a
  `connection`; the operation ID each GraphQL record is called by; how a GraphQL call gives the file of an Upload value,
  and which part of the request path builds Requirement 3's request; how a caller obtains the global IDs a document's
  variables take (`WorkItemID`, `ProjectsBranchRuleID`, `WorkItemsTypeID`; `conventions.md` "Global IDs and other
  identifiers"); what a refusal of AC-4.1 names when no compatibility subcommand sends the mutation's effect
  (`commands/call.py` `GATED_OPERATIONS` maps each ID to a subcommand); and which members #11's test project cannot
  exercise — the issue asks it of row 4's instance-wide list — with what proves their call (#41's proof method covers
  REST sections only, #41 Residuals).
- AC-1.2 Every capability SHALL be the `capability` of at least one GraphQL record, and
  `graphql_only.PENDING_CAPABILITIES` SHALL be empty: `test/test_gitlab_wrapper_coverage.py`
  `test_every_graphql_only_capability_is_served_or_pending` SHALL pass.
- AC-1.3 For each capability, the documents of its records SHALL together select every member its row names, with the
  argument or selection its code span gives, and row 2's `WorkItem` with its `widgets`.
- AC-1.4 `registry.lookup` SHALL return one record for each GraphQL record's operation ID, over every family module and
  `graphql_only`.

### Requirement 2 — A GraphQL call sends its record and prints its result (issue AC-2, AC-4, AC-5)

As a caller, I want to call a capability the way I call a REST record, so that a GraphQL-only capability needs no
other command and fails the way a REST call fails.

- AC-2.1 WHEN a GraphQL call of a record that has no Upload value and runs no mutation of AC-4.1 gives values for
  declared variables, the wrapper SHALL send one `POST` to `https://<hostname>/api/graphql` (`hostname` of
  `config/gitlab.json`) as `Transport.graphql` sends it, whose JSON body's `query` is the record's `document` and whose
  `variables` hold each given variable with the JSON value the caller gave: a string, number, boolean, array, object or
  `null`.
- AC-2.2 WHEN the record has a `connection`, the wrapper SHALL ask for each next page with the previous page's
  `pageInfo.endCursor` as `after` while `hasNextPage` is `true`, as `Transport.graphql_nodes` does, SHALL write to
  standard output, once the last page has arrived, one JSON array in the form `commands/_common.print_json` writes,
  holding every node of every page in page order, and SHALL exit 0.
- AC-2.3 WHEN the record has no `connection`, the wrapper SHALL write the response's `data` in the form `print_json`
  writes and exit 0.
- AC-2.4 WHEN the transport raises `GitLabAPIError` for a GraphQL call — a top-level `errors` member, with or without
  `data`, or a mutation payload's non-empty `errors` (`GitLabGraphQLResponseError`); an HTTP error; spent `429` retries
  (`GitLabRateLimitError`); no response; a body that is not a JSON object; a connection absent or forbidden, or a next
  page without `endCursor`; a job token; a file that cannot be read — the wrapper SHALL write nothing to standard
  output, write the error's message and details to standard error, and exit 1, as #41 AC-1.7 states.
- AC-2.5 Each GraphQL record whose document runs no mutation of AC-4.1 SHALL have a test that runs its GraphQL call
  through the product's `main` against the fake host and asserts the posted request — `query` and `variables`, or for a
  record with an Upload value the parts of AC-3.1 — and the standard output; for a record with a `connection`, across
  two pages.

### Requirement 3 — An Upload value is sent as a multipart request (issue AC-3)

As a caller, I want to send the files a mutation takes, so that a capability whose mutation uploads is callable like
any other.

- AC-3.1 WHEN a GraphQL call of a record that has an Upload value and runs no mutation of AC-4.1 names a file for each
  Upload value, the wrapper SHALL send one `POST` to `https://<hostname>/api/graphql`, with the credential and to the
  origin `Transport.graphql` uses, whose `multipart/form-data` body holds, as `conventions.md` "File uploads" states: an
  `operations` part, the JSON of `query` (the record's `document`) and `variables` (the given values, each Upload value
  `null`); a `map` part, the JSON object mapping each file part's name to the variable path it fills
  (`variables.files.0`); and one part per file, named after its `map` key, holding the file's bytes unchanged. The
  wrapper SHALL then print the response or report its error as AC-2.3 and AC-2.4 state.
- AC-3.2 AC-2.5's test of a record that runs `designManagementUpload` SHALL give two files and assert each part of
  AC-3.1, the `map` naming a path for each item of `files`.

### Requirement 4 — Refused before any request

As the operator, I want `call` to create no work item, so that an issue reaches GitLab only through `issue create`,
which the `issue-filing-gate` judges (#41 Security Considerations "Gates", D8).

- AC-4.1 WHEN a GraphQL call names a record whose document runs a mutation that creates an issue or another work item
  (`workItemCreate`, `workItemsCsvImport`), the wrapper SHALL send no request, log the operation ID and the mutation's
  name, and exit 2 (`EXIT_REFUSED`).
- AC-4.2 Each refusal of AC-4.1 SHALL name the compatibility subcommand that `design.md` records for its effect, or
  state that no subcommand sends it (AC-1.1).
- AC-4.3 A test SHALL run a GraphQL call of each record AC-4.1 refuses through the product's `main` against the fake
  host and assert exit 2, no recorded request, and AC-4.2's log; the test SHALL fail when it finds no record to call.

### Requirement 5 — Docs (issue AC-5)

As an agent calling the wrapper, I want the usage docstring and the project map to say how to call a capability, so
that I find the call without reading the package.

- AC-5.1 The module docstring of `src/payload/scripts/gitlab_wrapper.py` SHALL name the operation ID of every GraphQL
  record with its capability, how a GraphQL call gives a variable and a file (AC-2.1, AC-3.1), how a result with and
  without a connection prints (AC-2.2, AC-2.3), and that AC-4.1's mutations are refused with exit 2.
- AC-5.2 `docs/forLLMConsumption.md` SHALL name how to call a GraphQL-only capability, a file included, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.

## Unchanged behaviour

- UB-1.1 Every caller-used subcommand (#41 Glossary), run as `python scripts/gitlab_wrapper.py <argv>`, SHALL CONTINUE
  TO accept the argv and return the exit codes its callers use: `src/payload/test/test_gitlab_wrapper_compat.py` SHALL
  CONTINUE TO pass with no existing case, spelling or assertion edited.
- UB-1.2 `call` SHALL CONTINUE TO send and print every `RestOperation` as #41 AC-1.2 to AC-1.8 state, and to refuse with
  exit 2 and no request what #41 Requirement 2 refuses — an ID no record declares, a name a record does not document (a
  record's `after` on a connection included) — and `ai-coding#merge-a-merge-request` and `plan#create-an-issue`,
  naming `mr merge` and `issue create`: `src/payload/test/test_gitlab_api_call.py` and
  `test/test_gitlab_wrapper_contract.py` SHALL CONTINUE TO pass.
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `config/gitlab.json` (`_load_config`) — never from an
  environment variable, an argument or another file; no GraphQL call takes a token option
  (`test_gitlab_wrapper_compat.py` `test_load_config_refusals`, `test_environment_token_ignored`;
  `test_gitlab_api_call.py` `test_call_takes_no_token_option`).
- UB-2.2 The entry script and `src/payload/scripts/gitlab_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_gitlab_api_properties.py` `test_standard_library_only`).
- UB-3.1 `src/payload/scripts/github_wrapper.py`, `src/payload/scripts/github_api/` and their tests
  (`src/payload/test/*github*.py`, `test/*github*.py`) SHALL CONTINUE TO be untouched by this change and to pass.

## Out of scope

- Members a row names only in words or elides (row 1's "and more"; row 3's squash options, external status checks and
  approval project rules): AC-1.3 covers the code-span members.
- Refusing the branch-rule mutations: they stay callable, as the GitHub twin's protection-rule mutations do (DL-002).
- The REST families, the GitHub twin (#30), the hook gates, and promoting the new wrapper.
- The real-instance run: #11's. Until its fixture exists, AC-2.5's and AC-4.3's tests run each call through `main` up
  to the API boundary in CI.

## Residuals

- `workItemUpdate`, `workItemDelete`, `workItemExport` and `pipelineCreate` stay callable; whether to run one is the
  caller's decision (#41 Security Considerations "Destructive operations").
- Row 7's record is declared and refused (AC-4.1), so Requirement 3's request reaches GitLab for row 5 only.
- A non-null variable left without a value is not refused before a request; GitLab's `errors` answer exits 1 by AC-2.4,
  as #41 Residuals leaves required attributes to the host.
