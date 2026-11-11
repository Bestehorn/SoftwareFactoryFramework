# Requirements — issue #63: GitLab wrapper rewrite, part 2 slice: request forms the records lack

Tier: M. Kind: FEATURE. Scope: `prompt.md` and DL-001: the six request forms F1 to F6, the records of the keys they
unblock, the usage docstring and `docs/forLLMConsumption.md`; not the gated kept IDs, #40's path forms, #43's route
prefix or the real-forge run (#10). Builds on `.claude/specs/issue-13-gitlab-wrapper-foundation/` ("#13"),
`.claude/specs/issue-41-gitlab-generic-operation-command/` ("#41"),
`.claude/specs/issue-40-gitlab-openapi-only-records/` ("#40", PR #62) and
`.claude/specs/issue-43-gitlab-package-records/` ("#43"). The **base** is `origin/main` once #40 and #43 have merged;
this branch rebases onto it before its implementation waves (DL-001).

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #63 was filed by intake from #15's residuals (the keys whose request form the record layer does not
   build). This spec was derived from #63's body; no interview (see `qa_log.md`).

## Introduction

#15 AC-3 needs every family module's `PENDING` empty. On the base, the keys issue #63 lists stay pending because each
needs a request form the record layer does not build:

- F1: a section that lists several endpoints has one record, as `registry.lookup` refuses an ID declared twice (#41
  `design.md` Residuals, "Several keys under one Reference"), so its other keys stay pending;
- F2: `registry.expand` writes one value at every `:id` of a path;
- F3: `registry.PLACEHOLDER` reads `:name` and `*name` only, so `[.format]` would be sent literally;
- F4: `Transport` sends every REST path under `/api/v4`, and `Transport._send` refuses every origin but the configured
  one;
- F5: `_build_request` sends `Accept`, the `Content-Type` and the one credential header, none of a caller's;
- F6: N's `PARENT_KEY` reads one `parent[key]` level.

This change builds the six forms and gives each of those keys its record. How a form is spelled on the command line
and held in a record is `design.md`'s; these criteria state what a call sends and what it refuses.

## Glossary

- **Record**, **key**, **documented parameters** — #41's glossary. **`call`** — #41's
  `python scripts/gitlab_wrapper.py call <operation-id>`. **N**, **V** — `test/test_gitlab_wrapper_contract.py` and
  `test/test_gitlab_wrapper_coverage.py`.
- **Reference** — the `<stem>#<anchor>` an index row links, the operation ID of its records. Its **section** is the
  `###` section of `docs/api-reference/gitlab/rest/<stem>.md` it names; the section's **endpoints** are the
  `` `METHOD path` `` spans of its first line (N `section_endpoints`).
- **Issue key** — a key AC-1.1 lists.
- **F1 Reference** — a Reference whose section lists more than one endpoint; its **base endpoint** is the one its
  record declares on the base.
- **F2 path** — the path of an F2 key of AC-1.1: it holds `:id` twice, for two values.
- **F3 suffix** — the `[.format]` of `/projects/:id/repository/archive[.format]`.
- **F4 path** — a path that starts with `https://HOST`, the configured host's root (`operations-index.md`: "paths are
  relative to `https://HOST/api/v4` unless they start with `https://HOST`"), or with `/http(s)://${CI_REGISTRY}`, the
  container registry's own host.
- **F5 request header** — a table row whose `In` is `header`, or a name on a section's `- Request headers:` line.
- **F6 two-level member** — a row named `a[b][c]`:
  `override_params[container_expiration_policy_attributes][cadence]`.

## Requirements

### Requirement 1 — A record for every issue key (issue AC-1)

As the owner of #15, I want every issue key mapped by a record, so that no `PENDING` holds one.

- AC-1.1 Each issue key SHALL be the method and path, verbatim as its index row writes them, of a record declared with
  its row's Reference, and SHALL be on no `PENDING`. The issue keys, by form and family:
  - F1: the 37 keys issue #63 counts under F1 (create, developer-experience, fulfillment, plan,
    security-risk-management, software-supply-chain-security, tenant-scale, verify); in package, the
    `/projects/:id/packages/conan/v1/...` key of each Conan v1 entry and `("PUT", "/projects/:id/packages/nuget/v2")`,
    which #43 keeps pending (#43 AC-1.2, DL-003);
  - F2: create `("DELETE", "/groups/:id/ssh_certificates/:id")`; tenant-scale the `DELETE` and `POST .../rotate` keys
    of `/groups/:id/manage/personal_access_tokens/:id` and `/groups/:id/manage/resource_access_tokens/:id`;
  - F3: create `("GET", "/projects/:id/repository/archive[.format]")`;
  - F4: software-supply-chain-security `("GET", "https://HOST/oauth/token/info")`; in package, the two keys whose path
    starts with `/http(s)://${CI_REGISTRY}` (#43 AC-1.3, DL-002);
  - F5: software-supply-chain-security
    `("PATCH", "/projects/:id/compliance_external_controls/:external_control_id/status")`;
  - F6: gitlab-dedicated `("POST", "/projects/remote-import-s3")`.
- AC-1.2 Each record of this change SHALL be transcribed from its section by the rules its family module's docstring
  states, its request headers (Requirement 6) and two-level members (Requirement 7) included.
- AC-1.3 Every other key SHALL stay mapped or pending as the base holds it.
- AC-1.4 WHEN this change is complete, V `test_every_index_row_is_mapped_or_pending` and
  `test_every_declared_key_is_in_its_family` SHALL pass.

### Requirement 2 — F1: several endpoints under one Reference (issue AC-2)

As a caller, I want to call any endpoint of a Reference by its one ID, so that every key of its section is reachable.

- AC-2.1 WHEN a call of an F1 Reference names one of its endpoints, the wrapper SHALL send that endpoint's method and
  path, with that endpoint's path parameters and the configured project as the `id` of a path starting with
  `/projects/:id` that the call gives no `id` (#41 AC-1.8). With `merge_request_iid=5`,
  `plan#add-an-emoji-reaction-to-a-resource` naming `POST /projects/:id/merge_requests/:merge_request_iid/award_emoji`
  is sent as `POST /api/v4/projects/<project_id>/merge_requests/5/award_emoji`, and
  `software-supply-chain-security#set-your-user-status` naming `PATCH /user/status` as `PATCH /api/v4/user/status`.
  How a call names an endpoint is `design.md`'s.
- AC-2.2 WHEN a call of an F1 Reference names no endpoint, the wrapper SHALL send its base endpoint (UB-1).
- AC-2.3 The literal example endpoints of developer-experience "File path, branches, and tags name" are endpoints of
  its section and rows of the index; each SHALL be sent as written, with no path parameter:
  `GET /api/v4/projects/1/repository/tags/my%2Ftag`.
- AC-2.4 IF a call names an endpoint that no record of its Reference declares, THEN the wrapper SHALL send no request,
  write to standard error a message naming the Reference's declared endpoints, and exit 2. IF a call gives a path
  parameter of an endpoint other than the one it sends (`issue_iid` with the merge-request endpoint), THEN the wrapper
  SHALL refuse it as #41 AC-2.2 refuses an undocumented parameter.

### Requirement 3 — F2: one name, two meanings (issue AC-3)

As a caller, I want the group and the certificate or token of an F2 path given as two values, so that each reaches
its own segment.

- AC-3.1 A call of an F2 key SHALL take its two `:id`s as two path parameters: the first the group, the second the SSH
  certificate or the access token (docs.gitlab.com `group_ssh_certificates` "Delete a group SSH certificate" lists
  `id` twice, "The ID of the group" and "The ID of the SSH certificate"; `groups` "Revoke a personal access token for
  an enterprise user": "ID of a personal access token or the keyword `self`"). How a call names them is
  `design.md`'s.
- AC-3.2 WHEN a call gives both, the wrapper SHALL write each at its own place as `registry.expand` writes a `:name`:
  group `7` and certificate `12345` send `DELETE /api/v4/groups/7/ssh_certificates/12345`; group `7` and token `self`
  send `POST /api/v4/groups/7/manage/personal_access_tokens/self/rotate`.
- AC-3.3 IF a call leaves either without a value, THEN the wrapper SHALL refuse it as #41 AC-2.3 does: no request, a
  message naming it and the record's path parameters, exit 2.

### Requirement 4 — F3: the `[.format]` suffix (issue AC-3)

As a caller, I want the archive format sent as the path's suffix only when I give one.

- AC-4.1 WHEN a call of `create#retrieve-file-archive-from-a-repository` gives a format, the wrapper SHALL send
  `/archive.<format>`; WHEN it gives none, `/archive`; never `[.format]` (docs.gitlab.com `repositories`: "`.format`
  is an optional suffix for the archive format, and defaults to `tar.gz`"). With `zip` and no `id`:
  `GET /api/v4/projects/<project_id>/repository/archive.zip`. How a call gives the format is `design.md`'s.
- AC-4.2 The formats SHALL be that page's "Available options": `bz2`, `tar`, `tar.bz2`, `tar.gz`, `tb2`, `tbz`,
  `tbz2`, `zip`. IF a call gives any other, THEN the wrapper SHALL send no request, write to standard error a message
  naming the formats, and exit 2.

### Requirement 5 — F4: another base or origin (issue AC-4)

As a caller, I want an F4 path sent where GitLab serves it, so that the token-information and registry operations are
callable.

- AC-5.1 WHEN a call names `software-supply-chain-security#retrieve-the-token-information`, the wrapper SHALL send
  `GET https://<hostname>/oauth/token/info` — the configured host's root on the configured origin, outside `/api/v4` —
  with the configured token type's one credential header (docs.gitlab.com `oauth2` "Retrieve the token information":
  the token as `Authorization: Bearer`).
- AC-5.2 WHEN a call names `package#delete-image-tags-by-reference` or `package#listing-all-container-repositories`,
  the wrapper SHALL send the record's method to the container registry's origin, at the record's path after
  `/http(s)://${CI_REGISTRY}`, each `${NAME}` of it a path parameter of the call, with the registry's own bearer token
  (docs.gitlab.com `container_registry`: the registry's endpoints take "an authentication token" that is "different
  from project or personal access tokens", obtained from `/jwt/auth`). Where the registry's origin comes from, how its
  token is obtained within UB-2, and how a `${NAME}` value is written are `design.md`'s.
- AC-5.3 IF the registry's token cannot be obtained, THEN the wrapper SHALL send nothing to the registry and exit 1, as
  #41 AC-1.7 does for a `GitLabAPIError`.

### Requirement 6 — F5: request headers (issue AC-4)

As a caller, I want a request header that a section documents sent with the value I give, so that the external
control and the NuGet symbol download reach GitLab whole.

- AC-6.1 A record SHALL declare each F5 request header of its section: `X-Gitlab-Timestamp`, `X-Gitlab-Nonce` and
  `X-Gitlab-Hmac-Sha256` for `software-supply-chain-security#set-status-of-an-external-control` (its
  `- Request headers:` line); `Symbolchecksum` for `openapi-only#the-nuget-symbol-file-download-endpoint` and
  `openapi-only#the-nuget-symbol-file-download-endpoint-1` (their `header` rows; #40 Residuals).
- AC-6.2 WHEN a call gives a value for a declared header, the request SHALL carry that header with that value beside
  `Accept`, its `Content-Type` and the one credential header; a header the call does not give SHALL NOT be sent. With
  `X-Gitlab-Timestamp` `1700000000`, `X-Gitlab-Nonce` `n1`, `X-Gitlab-Hmac-Sha256` `ab12`, `external_control_id=3` and
  `status=pass`, the call sends `PATCH /api/v4/projects/<project_id>/compliance_external_controls/3/status` carrying
  the three headers and the JSON body `{"status": "pass"}`. How a call gives a header is `design.md`'s.
- AC-6.3 IF a call gives a header its record does not declare, THEN the wrapper SHALL refuse it as #41 AC-2.2 refuses
  an undocumented parameter.

### Requirement 7 — F6: two-level members (issue AC-5)

As a caller, I want the S3 import's `override_params` members sent at their names, two-level ones included, so that
the record sends every row its section documents.

- AC-7.1 WHEN a call of `gitlab-dedicated#import-a-project-from-an-aws-s3-bucket` gives `override_params` members,
  one-level (`override_params[visibility]`) or two-level (an F6 two-level member), the body SHALL carry each at its
  name as `conventions.md` "Arrays, hashes and arrays of hashes" writes a hash — nested objects in a JSON body,
  bracketed names in a form or multipart body — an `array of string` member as an array, and the `file` member
  `override_params[avatar]` as the multipart part of that name. How a call gives them and the record's body format
  are `design.md`'s.
- AC-7.2 N SHALL read every row of that section's table, the two-level rows included, and SHALL name the record when
  it declares no way to send a row, or when a body member it sends, at any level, is no row of the section.

### Requirement 8 — Proven through the contract test and `main` (issue AC-4, AC-5)

As the owner of #10, I want each form proven by a test that runs `call` to the API boundary, so that every record of
this change rests on test evidence rather than on its transcription alone.

- AC-8.1 Every record of this change, and each record AC-6.1 changes, SHALL pass N
  `test_every_record_matches_its_reference_section` and `test_every_record_is_sent_as_its_section_documents`; the send
  test SHALL call each declared endpoint of an F1 Reference once, naming it, and each F4 record at its own base or
  origin.
- AC-8.2 N SHALL name a record whose declared request headers differ from its section's, and a sent call that carries
  an undeclared header or lacks one the call gave.
- AC-8.3 AC-2.1 to AC-2.3, AC-3.2, AC-4.1, AC-5.1, AC-5.2, AC-6.2 and AC-7.1 SHALL each have a test that runs `call`
  through the product's `main` against the fake host (`src/payload/test/gitlab_wrapper_fixtures.py` `FakeGitLab`) and
  asserts the sent method, URL, headers and body names; each refusal of AC-2.4, AC-3.3, AC-4.2, AC-5.3 and AC-6.3, a
  test that asserts its exit code and that nothing was sent.

### Requirement 9 — Docs (issue work item)

As an agent calling the wrapper, I want the usage docs to name each form, so that I find the call without reading
the package.

- AC-9.1 The module docstrings of `src/payload/scripts/gitlab_wrapper.py` and `gitlab_api/commands/call.py` SHALL
  state, with one example each, how a call names an endpoint and gives the two values of an F2 path, a format, a
  request header and a two-level member.
- AC-9.2 `docs/forLLMConsumption.md` SHALL name the same, and `test/test_instruction_corpus_budget.py`
  `test_llm_map_within_cap` SHALL CONTINUE TO pass.

## Unchanged behaviour

- UB-1 Every call the wrapper accepts on the base SHALL CONTINUE TO send the same request — method, URL, headers and
  body — and to print its response as there; every caller-used subcommand SHALL CONTINUE TO accept its argv and return
  its exit codes (#13 UB-1). A `:name` that a path other than an F2 path holds twice SHALL CONTINUE TO take its one
  value at both places (`/<route-prefix>/symbolfiles/:file_name/:signature/:file_name`, #43 UB-4). The existing tests
  of `src/payload/test/test_gitlab_*.py`, `test/test_gitlab_api_properties.py`, N and V SHALL CONTINUE TO pass with no
  existing assertion edited.
- UB-2 The entry script and `src/payload/scripts/gitlab_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_gitlab_api_properties.py` `test_standard_library_only`), to read their only credential from
  `config/gitlab.json` (`_load_config`), with no token option, and to send the configured token only to the configured
  origin (#13 AC-3.1): no request to the registry carries it.
- UB-3 A value its record does not declare SHALL CONTINUE TO be refused with nothing sent and exit 2 (#41
  Requirement 2) — the endpoints, formats and request headers of this change held to the same rule (AC-2.4, AC-4.2,
  AC-6.3) — and `commands/call.py` `GATED_OPERATIONS` SHALL CONTINUE TO be as the base has it.
- UB-4 `src/payload/scripts/github_wrapper.py`, `src/payload/scripts/github_api/` and their tests SHALL CONTINUE TO be
  untouched by this change and to pass.

E2E: the wrapper is a command-line program with nothing deployed. N and the tests of AC-8.3 run `call` through
`main`'s argv against the fake host to the API boundary in CI's `tests` leg; the real-forge check is #10's run on an
ephemeral `sff-test-*` project.

## Residuals

- Computing `X-Gitlab-Hmac-Sha256` (docs.gitlab.com `external_controls`: HMAC-SHA256 of the timestamp, nonce, path and
  `status=<status>` "using your secret key") needs the control's secret, which UB-2 keeps out; the caller gives it.
- The S3 import takes `overwrite`, which replaces an existing project, the reason `families/gitlab_dedicated.py`
  (#38 DL-005) keeps the archive imports pending; gating it is the gated kept IDs' slice, which the Ask excludes.
- "Delete image tags by reference": the docs' example URL has `/manifests/` where its endpoint line and the index have
  `/tags/reference/`; the record follows the index, and GitLab's answer is #10's run.
- "Retrieve the token information" documents an OAuth token as `Authorization: Bearer`; under `token_type` `private`
  the configured header is `PRIVATE-TOKEN`, and whether GitLab answers it is #10's run.
- The emoji resource sections' row `issue_iid/merge_request_iid/snippet_id` is one `Param` (`families/plan.py`); the
  new endpoints share their Reference's table, and reading that row as a path parameter is not this change's.
