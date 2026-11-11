# Requirements — issue #40: GitLab wrapper rewrite, part 2 slice: the OpenAPI-only operations

Tier: M. Kind: FEATURE. Scope: `prompt.md`, DL-001 and DL-007: the keys `families/openapi_only.py` holds pending, the
three `ml_models` file keys of `families/deploy.py`, and the path forms and the raw body they need. Builds on
`.claude/specs/issue-13-gitlab-wrapper-foundation/` ("#13") and
`.claude/specs/issue-41-gitlab-generic-operation-command/` ("#41").

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #40, "GitLab wrapper rewrite, part 2 slice:
   the OpenAPI-only operations", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Introduction

`src/payload/scripts/gitlab_api/families/openapi_only.py` declares no record: `OPERATIONS` is empty, and `PENDING` holds
every key whose index rows link only `docs/api-reference/gitlab/rest/openapi-only.md`; each of those rows' References
carries one key. `families/deploy.py` declares no record either: its `PENDING` holds the three `ml_models` file keys,
whose rows link both `rest/deploy.md` and `rest/openapi-only.md` and which belong to `deploy`, the module that sorts
first (#13 D2; `test/test_gitlab_wrapper_coverage.py` `key_families`).

`registry.expand` writes each `:name` (`registry.PLACEHOLDER`) as one percent-encoded segment, refusing an empty, `.` or
`..` value (`REFUSED_SEGMENTS`), and builds no other path form. The pending paths carry three more (#13 Residuals;
`rest/openapi-only.md` preamble, "Parentheses mark optional path segments"):

- the `*name` glob, whose value keeps its `/` (`/projects/:id/packages/npm/*package_name`, the Debian `*distribution`);
- the optional group `(*path/)` of the generic-package and ML-model file paths;
- OData parentheses written escaped, `\(` and `\)` (`/projects/:project_id/packages/nuget/v2/Packages\(\)`).

The reference's tables give a glob or optional name the `In` `query`, `body` or `form` (`rest/openapi-only.md` "Download
package file": `package_version` and `path` in the query), while `rest/deploy.md` gives the `(*path/)` name `path` the
`In` `path`.

The issue's raw-body question: #41's `call` sends a `Kind.FILE` attribute given with `--file` as a part of a
`multipart/form-data` body (`commands/call.py` module docstring; `registry.encode`; `transport.request_body`) and has
no raw-bytes body. GitLab Workhorse fixes each upload's form by its route (`gitlab-org/gitlab`
`workhorse/internal/upstream/routes.go`). `PUT …/packages/generic/`, `PUT …/packages/ml_models/`,
`PUT …/packages/terraform/modules/` and `POST …/terraform/state/` go to `requestBodyUploader`, which stores the
request body as the file and forwards the request "without the original request body"
(`workhorse/internal/upload/body_uploader.go` `RequestBody`); `POST /jobs/:id/artifacts` goes to the multipart
`upload.Artifacts`. `conventions.md` "Generic packages" agrees: "The body is the raw file bytes (curl `--upload-file`),
not multipart", with `status` and `select` as query attributes. The ML-model file upload is such a route, though
docs.gitlab.com's "Send the file" example sends `--form` (Residuals).

This change adds a record for each of those keys, with none excluded, the three path forms and the raw body, with their
tests, and leaves both `PENDING` sets empty.

## Glossary

- **Record**, **key**, **documented parameters** — as #41's glossary defines them. **`call`** — #41's
  `python scripts/gitlab_wrapper.py call <operation-id>`.
- **Entry** — the section of `docs/api-reference/gitlab/rest/<stem>.md` that a record's operation ID
  (`<stem>#<anchor>`) names, with its `| Attribute | In | Type |` table.
- **Glob parameter** — a `*name` in a record's path: `*` followed by an identifier.
- **Optional group** — an unescaped `(…)` in a record's path; in this change always `(*path/)`.
- **Escaped parenthesis** — `\(` or `\)` in a record's path.
- **Path parameter** — a `:name`, a glob parameter, or the glob parameter inside an optional group.
- **N**, **V** — `test/test_gitlab_wrapper_contract.py` (#41 D5) and `test/test_gitlab_wrapper_coverage.py` (#41 D6).

## Requirements

### Requirement 1 — A record for every pending key (issue AC-1, AC-5)

As the owner of #11, I want every key that the index links to `rest/openapi-only.md` to have a record, so that the
OpenAPI-only operations are callable like every other covered operation and the coverage rule holds with no exclusion.

- AC-1.1 For each key of `openapi_only.PENDING` — the Workhorse `authorize` routes, the runner routes (`/jobs/request`,
  `/jobs/:id` and its sub-paths), the Geo-internal `/geo/` routes and the administrator `/admin/` routes included —
  `openapi_only.OPERATIONS` SHALL hold one `RestOperation` whose `method` and `path` are its index row's, verbatim, and
  whose `operation_id` is `openapi-only#<anchor>`, the row's Reference without `rest/` and `.md`.
- AC-1.2 For each of the three `ml_models` file keys, `deploy.OPERATIONS` SHALL hold one `RestOperation` with the row's
  method and path verbatim and the `operation_id` of its `rest/deploy.md` Reference (`deploy#send-the-file`); no record
  SHALL declare the `openapi-only#` Reference of those keys.
- AC-1.3 Each record SHALL declare one `Param` per `query`, `body` or `form` row of its entry that does not name a path
  parameter and is not a raw-body record's `file` row (AC-3.2): its `location` the row's `In`, `form` read as
  `Location.BODY`, every `Param` of a raw-body record `Location.QUERY` (AC-3.2); its `kind` by the row's Type
  (`array of string` `ARRAY`, `object` `HASH`, `array of object` `ARRAY_OF_HASHES`, `file` `FILE`, any other
  `SCALAR`); `required` where Required reads `yes`. Each record SHALL have the `body` `BodyFormat.JSON` and no `fixed`
  pairs.
- AC-1.4 A row whose name is a glob parameter or the parameter of an optional group of the record's path SHALL be read
  as that path parameter, whatever its `In`, and SHALL be no `Param`.
- AC-1.5 A `GET` record whose entry holds the query rows `page` and `per_page` SHALL be `Paging.OFFSET`
  (`docs/api-reference/gitlab/conventions.md` "Offset-based"); every other record SHALL be `Paging.NONE`.
- AC-1.6 WHEN this change is complete, `openapi_only.PENDING` and `deploy.PENDING` SHALL be empty, and V
  `test_every_index_row_is_mapped_or_pending` and `test_every_declared_key_is_in_its_family` SHALL pass.

### Requirement 2 — The path forms (issue AC-4; #13 Residuals)

As a caller, I want a glob value sent with its slashes, an optional group sent only when I give it, and an escaped
parenthesis sent as a parenthesis, so that the request reaches the route GitLab declares.

- AC-2.1 WHEN a call gives a glob parameter a value, the wrapper SHALL write the value in place of `*name` with each `/`
  kept and each part between them percent-encoded as `registry.expand` encodes one segment: `1.0/rc 1` is written
  `1.0/rc%201`.
- AC-2.2 WHEN a glob value has an empty, `.` or `..` part (`a//b`, `/a`, `a/../b`), the wrapper SHALL send no request
  and exit 1 with a `GitLabAPIError`, as `registry.expand` refuses such a segment (#41 D4).
- AC-2.3 WHEN a call gives the parameter of an optional group a value, the wrapper SHALL write the group's contents
  without its parentheses, the parameter written as AC-2.1 writes it; WHEN the call gives it no value, the wrapper SHALL
  leave the whole group out and refuse nothing for it. With `package_name=pkg`, `package_version=1.0` and
  `file_name=file.txt`, `…/generic/:package_name/*package_version/(*path/):file_name` is sent as
  `…/generic/pkg/1.0/a/b/file.txt` with `path=a/b`, and as `…/generic/pkg/1.0/file.txt` without `path`.
- AC-2.4 A glob parameter and the parameter of an optional group SHALL be documented path parameters: given with
  `--path` and named among the record's path parameters in #41 D4's message (#41 AC-2.2). WHEN a call leaves a glob
  parameter outside an optional group without a value, the wrapper SHALL refuse the call as #41 AC-2.3 refuses a
  missing path parameter.
- AC-2.5 WHERE a record's path holds an escaped parenthesis, the wrapper SHALL send `(` or `)` without its backslash and
  SHALL NOT read it as an optional group; the path's other literal characters (`$metadata`, `'`, `,`, `=`) SHALL be sent
  as the path writes them. `Packages\(Id='*package_name',Version='*package_version'\)` with `package_name=N` and
  `package_version=1.0` is sent as `Packages(Id='N',Version='1.0')`.
- AC-2.6 Each form — a glob value holding `/`, a refused glob part, an optional group given and one left out, the
  escaped parentheses — SHALL have a test that runs `call` through the product's `main` against the fake host
  (`src/payload/test/gitlab_wrapper_fixtures.py` `FakeGitLab`) and asserts the sent method and URL, or, for the
  refusal, that nothing was sent.

### Requirement 3 — Each record is sent as its entry documents (issue AC-2, AC-3)

As a caller, I want every new record sent as `call` sends any record and proven against its entry, so that a record's
declaration rests on test evidence rather than on its transcription alone.

- AC-3.1 WHEN a call names a record of this change with a value for each path parameter and any of its attributes, the
  wrapper SHALL send the record's method to `/api/v4` followed by its path written by Requirement 2 and
  `registry.expand`, its attributes as #41 AC-1.2 and AC-1.3 send them, the configured project as the `id` of a
  `/projects/:id` path the call gives no `id` (#41 AC-1.8), and SHALL print the response as #41 AC-1.4 to AC-1.6 do.
- AC-3.2 Each upload SHALL be sent in the form GitLab Workhorse reads on its route (Introduction):
  - WHEN a call gives `openapi-only#upload-job-artifacts` its `file` with `--file`, the wrapper SHALL send the file's
    bytes as the `multipart/form-data` part `file`, every other body attribute a form field, as #41 AC-1.3 sends any
    `FILE` attribute.
  - WHEN a call gives `--input FILE` to a raw-body record — `openapi-only#upload-package-file`,
    `openapi-only#upload-terraform-module-package-file`, `openapi-only#create-or-update-a-terraform-state` and
    `deploy#send-the-file` — the wrapper SHALL send the bytes of FILE, or of standard input when FILE is `-`,
    unchanged as the whole request body with `Content-Type: application/octet-stream`, and the call's `--query` values
    in the query. A raw-body record's `file` row is that body and no `Param`; its other `body` or `form` rows that name
    no path parameter are `Location.QUERY` `Param`s.
  - IF a call gives `--input` beside `-f` or `-F`, or to a record that is not a raw-body record, THEN the wrapper SHALL
    send no request and exit 2.
- AC-3.3 Every record of this change SHALL pass N `test_every_record_matches_its_reference_section` (its endpoint, path
  parameters and `Param`s against its entry, read by AC-1.4 and AC-3.2) and
  `test_every_record_is_sent_as_its_section_documents` (one fake-host call whose method, path written by Requirement 2,
  query names and body names match the entry). For a record that #41 D5's rule calls unreachable (the `/admin/`,
  `/geo/` and `/hooks/` keys), these two tests are its proof.
- AC-3.4 WHEN a `Paging.OFFSET` record of this change is called through `call` against the fake host serving two pages,
  the second named by `x-next-page`, the wrapper SHALL print the items of both pages as one JSON array; each paged
  record SHALL have such an example in `src/payload/test/test_gitlab_api_openapi_only.py` (#41 D8).

## Unchanged behaviour

- UB-1 Every caller-used subcommand, run as `python scripts/gitlab_wrapper.py <argv>`, SHALL CONTINUE TO accept the argv
  and return the exit codes its callers use (#13 UB-1): `src/payload/test/test_gitlab_wrapper_compat.py` SHALL CONTINUE
  TO pass with no existing case, spelling or assertion edited.
- UB-2 The entry script and `src/payload/scripts/gitlab_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_gitlab_api_properties.py` `test_standard_library_only`) and to take the credential only from
  `config/gitlab.json` (`_load_config`), with no token option; a record's `token` attribute (`/jobs/request`) is a body
  value the caller gives, never the configured credential.
- UB-3 `src/payload/scripts/github_wrapper.py`, `src/payload/scripts/github_api/` and their tests SHALL CONTINUE TO be
  untouched by this change and to pass.
- UB-4 Every existing GitLab record, and every path whose parameters are all `:name`, SHALL CONTINUE TO be sent as
  before, each `:name` one percent-encoded segment (#13 AC-2.2). `call`'s refusals (#41 Requirement 2) and
  `commands/call.py` `GATED_OPERATIONS` SHALL CONTINUE TO be as they are: no key of this change merges a merge request
  or creates an issue. The existing tests of `src/payload/test/test_gitlab_api_registry.py`, `test_gitlab_api_call.py`,
  `test_gitlab_api_no_stage_assigned.py`, `test/test_gitlab_api_properties.py`, N and V SHALL CONTINUE TO pass with no
  existing assertion edited.

## Out of scope

- The records of every other family; #43's `/<route-prefix>/` and registry-host (`http(s)://${CI_REGISTRY}`) forms.
- #11's real-instance run on an ephemeral `sff-test-*` project, and promoting the wrapper. E2E: the wrapper is a
  command-line program with nothing deployed; `call` is exercised through `main`'s argv against the fake host in CI's
  `tests` leg (AC-2.6, AC-3.2, AC-3.3, AC-3.4), and the real-forge check is #11's.

## Residuals

- Upload forms: AC-3.2 follows Workhorse's routes. docs.gitlab.com's Model registry "Send the file" example sends
  `--form "file=@model.pkl"`, and `conventions.md` "Other package formats" gives Terraform modules a "multipart
  `file`"; GitLab's own answer is #11's real-instance run.
- The `Symbolchecksum` `header` rows of the two NuGet symbol-file entries are not sent (`Transport.request` takes no
  header, #41 D5); sending one needs a header location in `Param`, the transport and N.
- The `status` row of the `openapi-only#` `ml_models` entries, which `rest/deploy.md` lacks, is not declared (AC-1.2).
- `conventions.md` advises not to call the `authorize` routes ("unverified"); a call is the caller's decision (#41).
- `openapi-only#upload-job-artifacts` authenticates in Workhorse's body-less pre-authorization
  (`POST …/artifacts/authorize`), so it needs a job token in `config/gitlab.json` (`JOB-TOKEN`). Its `token` form field
  does not reach that step.
