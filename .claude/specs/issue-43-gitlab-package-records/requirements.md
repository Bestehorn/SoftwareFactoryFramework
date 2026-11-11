# Requirements — issue #43: GitLab wrapper rewrite, part 2 slice: the package stage group

Tier: M. Kind: FEATURE. Scope: `prompt.md` and DL-001: the keys `families/package.py` holds pending, and the path forms
they need beyond #40's. Builds on `.claude/specs/issue-13-gitlab-wrapper-foundation/` ("#13") and
`.claude/specs/issue-41-gitlab-generic-operation-command/` ("#41"). Depends on #40
(`.claude/specs/issue-40-gitlab-openapi-only-records/`, "#40"): this change uses #40's glob form and does not build it;
the branch rebases onto `origin/main` once #40's PR has merged, before its implementation waves (DL-001).

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #41 landed and unblocked the GitLab slices; selected issue #43, "GitLab wrapper rewrite, part 2 slice:
   the package stage group", and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Introduction

`src/payload/scripts/gitlab_api/families/package.py` declares no record: `OPERATIONS` is empty, and `PENDING` holds
every key whose index rows link `docs/api-reference/gitlab/rest/package.md`. `registry.expand` writes each `:name` of
`registry.PLACEHOLDER` as one percent-encoded segment, and that pattern already reads the in-segment forms of this group
(`binary-:architecture`, `:package_name$:sha`, `:module_version.info`, `:file_name.tgz`). The pending paths carry four
more:

- `/<route-prefix>/`, which the Debian, npm and NuGet pages define by a line "`<route-prefix>` on this page is one of:
  …" listing instance, group or project prefixes (`rest/package.md` "Debian API", "npm API", "NuGet API");
- the `*name` glob (the Debian `*distribution`, the Maven `*path`, the virtual-registry `*id`), #40's form;
- the hyphenated names of "Upload module", `:module-name/:module-system/:module-version`, which `PLACEHOLDER` reads as
  `:module` each time; the entry lists `module-name`, `module-system` and `module-version` as `body` rows;
- the container-registry host, `/http(s)://${CI_REGISTRY}/v2/…`, of "Delete image tags by reference" and "Listing all
  container repositories".

Several uploads go to routes GitLab Workhorse stores as a raw request body (`routes.go` `requestBodyUploader`), so they
take #40's raw-body form rather than a multipart part (AC-4.2, DL-004).

Each Conan v1 entry, and NuGet "Upload a package file", lists more than one endpoint under its heading, so its Reference
carries more than one key, while `registry.lookup` takes one record per ID (#41 `design.md` Residuals, "Several keys
under one Reference").

This change adds a record for each pending key but those AC-1.2 and AC-1.3 keep, excludes none by a rule (#41 D6, "one
rule, with no exclusion"; #40 DL-002), and adds the prefix and hyphenated-name forms with their tests.

## Glossary

- **Record**, **key**, **documented parameters** — as #41's glossary defines them. **`call`** — #41's
  `python scripts/gitlab_wrapper.py call <operation-id>`.
- **Entry** — the section of `rest/package.md` that a record's operation ID (`package#<anchor>`) names, with its
  `| Attribute | In | Type |` table.
- **Prefix page** — a page of `rest/package.md` with a `<route-prefix>` line; its **prefix values** are the values that
  line lists, verbatim. A **prefix record** is a record whose path starts with `/<route-prefix>/`.
- **Glob parameter** — #40's: a `*name` in a record's path.
- **Hyphenated name** — a `:name` whose name continues past a `-` that a name character follows (`:module-name`).
- **Path parameter** — a `:name` (a hyphenated name included) or a glob parameter of a record's path, or a `:name` of
  the prefix value a call chooses.
- **N**, **V** — `test/test_gitlab_wrapper_contract.py` (#41 D5) and `test/test_gitlab_wrapper_coverage.py` (#41 D6).

## Requirements

### Requirement 1 — A record for every pending key (issue AC-1, AC-2)

As the owner of #11, I want every key that the index links to `rest/package.md` to have a record wherever the wrapper
can send it, so that the package operations, the package-manager protocol routes included, are callable like every
other covered operation.

- AC-1.1 For each key that `package.PENDING` holds when this change starts, but those AC-1.2 and AC-1.3 keep,
  `package.OPERATIONS` SHALL hold one `RestOperation` whose `method` and `path` are its index row's, verbatim, and whose
  `operation_id` is `package#<anchor>`, the row's Reference without `rest/` and `.md`.
- AC-1.2 WHERE an entry lists more than one endpoint, its record SHALL map the endpoint the entry lists first, and the
  key of every other endpoint of the entry SHALL stay in `package.PENDING`.
- AC-1.3 The keys whose path starts with `/http(s)://${CI_REGISTRY}`, and `("PUT", "/projects/:id/")`, SHALL stay in
  `package.PENDING`, with no record.
- AC-1.4 Each record SHALL declare one `Param` per `query`, `body` or `form` row of its entry that does not name a path
  parameter and is not a raw-body record's `file` row (AC-4.2): its `location` the row's `In`, `form` read as
  `Location.BODY`, every `Param` of a raw-body record `Location.QUERY`; its `kind` by the row's Type (`array of string`
  and `string array` `ARRAY`, `object` `HASH`, `array of object` `ARRAY_OF_HASHES`, `file` `FILE`, any other
  `SCALAR`); `required` where Required reads `yes`. Each record SHALL have the `body` `BodyFormat.JSON` and no `fixed`
  pairs.
- AC-1.5 A row whose name is a path parameter of the record's path SHALL be read as that path parameter, whatever its
  `In`, and SHALL be no `Param`: the `body` rows `module-name`, `module-system` and `module-version` of "Upload
  module", and a glob parameter's row as #40 AC-1.4 reads it.
- AC-1.6 A `GET` record whose entry holds the query rows `page` and `per_page` SHALL be `Paging.OFFSET`
  (`docs/api-reference/gitlab/conventions.md` "Offset-based"); every other record SHALL be `Paging.NONE`.
- AC-1.7 WHEN this change is complete, `package.PENDING` SHALL hold exactly the keys AC-1.2 and AC-1.3 keep, and V
  `test_every_index_row_is_mapped_or_pending` and `test_every_declared_key_is_in_its_family` SHALL pass.

### Requirement 2 — The `/<route-prefix>` paths (issue AC-4)

As a caller, I want a protocol route sent under the instance, group or project prefix I choose from those its page
documents, so that the request reaches the endpoint I mean and no other.

- AC-2.1 A prefix record SHALL accept as its prefix exactly the prefix values of its page: Debian
  `/projects/:id/packages/debian`, `/groups/:id/-/packages/debian`; npm `/packages/npm`, `/projects/:id/packages/npm`,
  `/groups/:id/-/packages/npm`; NuGet `/groups/:id/-/packages/nuget`, `/projects/:id/packages/nuget`. How a call names
  its prefix is `design.md`'s.
- AC-2.2 WHEN a call names one of the record's prefix values, the wrapper SHALL send the record's path with
  `/<route-prefix>` replaced by that value, each `:name` of the value a path parameter of the call, written as
  `registry.expand` writes it. With `package_name=pkg`, `GET /<route-prefix>/-/package/:package_name/dist-tags` is
  sent as `GET /api/v4/groups/7/-/packages/npm/-/package/pkg/dist-tags` under `/groups/:id/-/packages/npm` with
  `id=7`, and as `GET /api/v4/packages/npm/-/package/pkg/dist-tags` under `/packages/npm`.
- AC-2.3 WHEN the chosen value starts with `/projects/:id` and the call gives no `id`, the wrapper SHALL send the
  `project_id` of `config/gitlab.json` as that value, as #41 AC-1.8 does.
- AC-2.4 WHEN a call of a prefix record names no prefix, or a value that is not one of the record's prefix values, the
  wrapper SHALL send no request, write to standard error a message naming the record's prefix values, and exit 2. WHEN
  a call gives a path parameter that neither the chosen value nor the rest of the path holds (`id` under
  `/packages/npm`), the wrapper SHALL refuse it as #41 AC-2.2 refuses an undocumented parameter.
- AC-2.5 For each prefix page, one record SHALL have, per prefix value, a test that runs `call` through the product's
  `main` against the fake host (`src/payload/test/gitlab_wrapper_fixtures.py` `FakeGitLab`) and asserts the sent method
  and URL; each refusal of AC-2.4 SHALL have a test that asserts exit 2 and that nothing was sent.

### Requirement 3 — The hyphenated name and the glob (issue AC-4)

As a caller, I want `:module-name` read as the one parameter its entry names, and a glob value sent with its slashes,
so that the Terraform upload and the Debian, Maven and virtual-registry routes reach the route GitLab declares.

- AC-3.1 A hyphenated name SHALL be one path parameter, named with its hyphens, wherever the wrapper and N read path
  parameters (`registry.placeholders`, `registry.expand`, `call`'s documented and missing path parameters). With
  `module-name=infra`, `module-system=aws`, `module-version=1.0.0` and no `id`,
  `PUT /projects/:id/packages/terraform/modules/:module-name/:module-system/:module-version/file` is sent as
  `PUT /api/v4/projects/<project_id>/packages/terraform/modules/infra/aws/1.0.0/file`.
- AC-3.2 WHERE a record's path holds a glob parameter, the wrapper SHALL write it, refuse it and name it as #40 AC-2.1,
  AC-2.2 and AC-2.4 do. With `path=com/example/app/1.0` and `file_name=app-1.0.jar`,
  `GET /projects/:id/packages/maven/*path/:file_name` is sent as
  `GET /api/v4/projects/<project_id>/packages/maven/com/example/app/1.0/app-1.0.jar`; under
  `/projects/:id/packages/debian` with `distribution=stable`, `GET /<route-prefix>/dists/*distribution/Release` is
  sent as `GET /api/v4/projects/<project_id>/packages/debian/dists/stable/Release`.
- AC-3.3 The hyphenated names, a glob record of this change without a prefix and one with a prefix SHALL each have a
  test that runs `call` through the product's `main` against the fake host and asserts the sent method and URL.

### Requirement 4 — Each record is sent as its entry documents (issue AC-3)

As a caller, I want every new record sent as `call` sends any record and proven against its entry, so that a record's
declaration rests on test evidence rather than on its transcription alone.

- AC-4.1 WHEN a call names a record of this change with a value for each path parameter, a prefix where AC-2.1
  applies, and any of its attributes, the wrapper SHALL send the record's method to `/api/v4` followed by its path
  written by Requirements 2 and 3 and `registry.expand`, its attributes as #41 AC-1.2 and AC-1.3 send them, the
  configured project as the `id` of a `/projects/:id` path the call gives no `id` (#41 AC-1.8), and SHALL print the
  response as #41 AC-1.4 to AC-1.6 do.
- AC-4.2 Each upload, and npm "Create or update a dist-tag", SHALL be sent in the form GitLab reads on its route
  (`routes.go`, `design.md` D5):
  - WHEN a call gives `--input FILE` to a raw-body record — the Conan v1 and v2, Debian, Maven, npm and Ruby gems
    uploads, "Upload module" and npm "Create or update a dist-tag" — the wrapper SHALL send the bytes of FILE, or of
    standard input when FILE is `-`, unchanged as the whole request body with `Content-Type:
    application/octet-stream`, npm's `application/json`, and the call's `--query` values in the query, as #40 AC-3.2
    does.
  - WHEN a call gives a record's `FILE` attribute with `--file` — the NuGet, PyPI and Helm uploads and the Maven
    virtual-registry upload — the wrapper SHALL send the file's bytes as the `multipart/form-data` part named by that
    attribute, every other body attribute a form field, as #41 AC-1.3 sends any `FILE` attribute.
  - IF a call gives `--input` beside `-f` or `-F`, or to a record that is not a raw-body record, THEN the wrapper SHALL
    send no request and exit 2.
- AC-4.3 Every record of this change SHALL pass N `test_every_record_matches_its_reference_section` (its endpoint, path
  parameters and `Param`s against its entry, read by AC-1.5 and AC-4.2) and
  `test_every_record_is_sent_as_its_section_documents` (one fake-host call whose method, path, query names and body
  names match the entry). N SHALL read a prefix record's
  sent path with the call's prefix value written in, and SHALL name a prefix record whose prefix values are not its
  page's. For a record that #41 D5's rule calls unreachable (the pages whose `Offering:` lacks GitLab.com: the three
  Debian pages, Go Proxy, Ruby gems, Protected packages), these two tests are its proof.
- AC-4.4 WHEN a `Paging.OFFSET` record of this change is called through `call` against the fake host serving two
  pages, the second named by `x-next-page`, the wrapper SHALL print the items of both pages as one JSON array; each
  paged record SHALL have such an example in `src/payload/test/test_gitlab_api_package.py` (#41 D8).

## Unchanged behaviour

- UB-1 Every caller-used subcommand, run as `python scripts/gitlab_wrapper.py <argv>`, SHALL CONTINUE TO accept the argv
  and return the exit codes its callers use (#13 UB-1): `src/payload/test/test_gitlab_wrapper_compat.py` SHALL CONTINUE
  TO pass with no existing case, spelling or assertion edited.
- UB-2 The entry script and `src/payload/scripts/gitlab_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_gitlab_api_properties.py` `test_standard_library_only`) and to take the credential only from
  `config/gitlab.json` (`_load_config`), with no token option. `Transport._send` SHALL CONTINUE TO refuse a URL on any
  origin but the configured one, so no record of this change sends the credential to another host.
- UB-3 `src/payload/scripts/github_wrapper.py`, `src/payload/scripts/github_api/` and their tests SHALL CONTINUE TO be
  untouched by this change and to pass.
- UB-4 Every existing GitLab record, and every path of `operations-index.md` but the "Upload module" key, SHALL
  CONTINUE TO hold the path parameters it holds on the #40 base and to be sent as there: each `:name` one
  percent-encoded segment (#13 AC-2.2); `binary-:architecture` holding `architecture`, `:package_name$:sha` holding
  `package_name` and `sha`, `:module_version.info` holding `module_version`; a `:name` that a path holds twice taking
  its one value at both places (`/<route-prefix>/symbolfiles/:file_name/:signature/:file_name`). #41 Requirement 2's
  refusals and `commands/call.py` `GATED_OPERATIONS` SHALL CONTINUE TO be as they are: no key of this change merges a
  merge request or creates an issue. The existing tests of every `src/payload/test/test_gitlab_*.py`,
  `test/test_gitlab_api_properties.py`, N and V SHALL CONTINUE TO pass with no existing assertion edited.

## Out of scope

- The records of every other family; #40's glob, optional-group and escaped-parenthesis forms and its raw-body form
  (`call --input`), which #40 builds and this change uses (DL-001, DL-004).
- #11's real-instance run on an ephemeral `sff-test-*` project, and promoting the wrapper. E2E: the wrapper is a
  command-line program with nothing deployed; `call` is exercised through `main`'s argv against the fake host in CI's
  `tests` leg (AC-2.5, AC-3.3, AC-4.3, AC-4.4), and the real-forge check is #11's.

## Residuals

- More than one key under one Reference (AC-1.2): the project endpoint of each Conan v1 entry and the `/v2` endpoint
  of NuGet "Upload a package file" stay pending; a record needs `registry.lookup` to hold several records per ID and
  a call to choose among them (#41 `design.md` Residuals).
- Registry host (AC-1.3): both keys need the registry's own host in `config/gitlab.json`, a `/jwt/auth` bearer token
  for a registry scope (https://docs.gitlab.com/api/container_registry/) and a second origin, against UB-2.
- Project update (AC-1.3): the `import_url`, `mirror` and `mirror_overwrites_diverged_branches` of `PUT /projects/:id/`
  configure a pull mirror that overwrites its branches (`design.md` Sources, pull mirroring); it is mapped and gated
  with tenant-scale's "Update a project", whose entry has the same rows (#41 Residuals).
- "Upload module" lists no `file` row and npm "Upload a package file" a multipart `file`; both follow Workhorse's
  route as raw bodies (AC-4.2), as docs.gitlab.com's examples do; GitLab's own answer is #11's real-instance run.
