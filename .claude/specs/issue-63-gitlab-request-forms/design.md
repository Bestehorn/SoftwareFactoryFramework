# Design — issue #63: GitLab wrapper rewrite, part 2 slice: request forms the records lack

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-9.2, UB-1..UB-4, frozen). Builds on
`.claude/specs/issue-13-gitlab-wrapper-foundation/design.md` ("#13 Dn"),
`.claude/specs/issue-41-gitlab-generic-operation-command/design.md` ("#41 Dn"), #40's design (merged in PR #62,
`252c21e`; "#40 Dn") and #43's approved design (`.claude/specs/issue-43-gitlab-package-records/design.md`, "#43 Dn";
its route prefix, `families/package.py` and F test are the base). This branch rebases onto `origin/main` once #43 has
merged, before its implementation waves (DL-001). Test files are named in the legend of the Acceptance Criteria
Mapping.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #63 was filed by intake from #15's residuals (the keys whose request form the record layer does not
   build). This spec was derived from #63's body; no interview (see `qa_log.md`).

## Overview

The forms, each built where the record layer lacks it, then one record per issue key (D8):

- **F1** several records may share a Reference's ID in one family; `registry.lookup` chooses one by its method and
  path, and `call --endpoint 'METHOD path'` names it (D1);
- **F2** `RestOperation.positional_names` lets a `:name` the path holds twice take one value per place, given as
  repeated `--path` (D2);
- **F3** `registry` reads the `[.name]` suffix; `RestOperation.suffix_values` holds its values (D3);
- **F4** `registry.base_of` reads a path's base: under `/api/v4`, the configured host's root, or the container
  registry, which `gitlab_api/container_registry.py` reaches with a registry token from `/jwt/auth` (D4);
- **F5** `Location.HEADER` and `call --header NAME=VALUE` send a request header a section documents (D5);
- **F6** the S3 import's rows are each a `Param` of a FORM-body record, N's `PARENT_KEY` reads every bracket level,
  and `call` refuses the record (D6).

N's readings follow the forms (D7). D9 names the existing tests that hold the base's pending state.

## Design

### D1 — F1: several records under one Reference (AC-2.1 to AC-2.4)

**The records.** Each endpoint of an F1 Reference is one `RestOperation` with the Reference's ID, in the family module
that holds the base record. The base record keeps its place in `OPERATIONS`; the records of the section's other
endpoints follow it, in the order the section's endpoint line lists them. So the base record is the first one
declared with its ID.

**`lookup(*, operation_id, endpoint: Optional[Tuple[str, str]] = None) -> Operation`.**

| The ID's declarations | `endpoint` | Result |
|---|---|---|
| none | any | `ValueError` naming the ID, as today |
| by more than one source (two families, or a family and `graphql_only`), or two records of one family with one `(method, path)` | any | `ValueError` "declared … times, by: …", as today |
| REST records of one family | `None` | the first declared: the base endpoint (AC-2.2) |
| the same | equal to a record's `(method, path)` | that record |
| the same | any other | `ValueError` naming the ID, the text given (`json.dumps`) and each declared endpoint, `METHOD path`, in declaration order (AC-2.4) |
| one GraphQL record | `None` / any | the record / `ValueError` saying it takes no endpoint |

An ID that one record declares behaves as on the base (UB-1). `send`, `call` and `pages` gain `endpoint=None`; each
calls `lookup(operation_id=...)` when it is `None` and `lookup(operation_id=..., endpoint=...)` otherwise, so R
`test_call_refuses_an_undeclared_value`, whose `lookup` takes `operation_id` alone, passes unedited.

**`call --endpoint 'METHOD path'`** (`commands/call.py`).

- Constants `OPTION_ENDPOINT` (`--endpoint`), `ARG_ENDPOINT` (`endpoint`, default `None`), `METAVAR_ENDPOINT`
  (`ENDPOINT`). One value, argparse `store` (the last one given wins). Its `type`, `endpoint_key(text)`, cuts the text
  at its first space into the method and the path, each verbatim as the index writes them. No space, an empty method
  or an empty path raise `argparse.ArgumentTypeError` naming the text with `json.dumps`: exit 2 before the config is
  read.
- `prepare_call` calls `registry.lookup(operation_id=..., endpoint=args.endpoint)`. Every later step reads the chosen
  record, so a path parameter of another endpoint (`issue_iid` beside the merge-request endpoint) is refused by
  `check_parameters` as #41 AC-2.2 refuses an undocumented name (AC-2.4).
- `PreparedCall.endpoint`; `send_call` and `registry.pages` receive it.

### D2 — F2: one value per place (AC-3.1 to AC-3.3; UB-1)

- **The record.** `RestOperation.positional_names: Tuple[str, ...] = ()`: each `:name` its path holds more than once
  that takes one value per place, in path order. An F2 record sets `("id",)`; any other record keeps `()`.
- **`expand`**, step 3: a name of `positional_names` takes a list or tuple holding one value per place, and the k-th
  place is written from the k-th item by `_segment`. Any other shape or length raises `ValueError` naming the name and
  its places. Every other name is written as today: one value at every place it holds, so
  `/<route-prefix>/symbolfiles/:file_name/:signature/:file_name` takes `file_name` once (#43 UB-4).
- **`call`.** `path_values` collects every `--path` value of a positional name, in command-line order, as a list; the
  `id` default never applies to a positional name. `missing_path_parameters` names a positional name once for each
  place left without a value (AC-3.3), and `check_parameters` adds "given more values than its places" for too many.
  `documented_text` lists a positional name once per place (`id, id`).
- **The call.** `call create#delete-a-group-ssh-certificate --path id=7 --path id=12345` sends
  `DELETE /api/v4/groups/7/ssh_certificates/12345` (AC-3.2).

### D3 — F3: the `[.format]` suffix (AC-4.1, AC-4.2)

- **The pattern.** `OPTIONAL_SUFFIX = re.compile(pattern=r"\[\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)\]")`.
- **The record.** `RestOperation.suffix_values: Tuple[str, ...] = ()`: the values of the path's `[.name]`, verbatim
  from its docs page. `create#retrieve-file-archive-from-a-repository` holds `("bz2", "tar", "tar.bz2", "tar.gz",
  "tb2", "tbz", "tbz2", "zip")` (docs.gitlab.com `repositories` "Available options").
- **The functions.** `placeholders` also names each suffix, in path order, so `--path format` is documented and
  `encode` skips it. `required_placeholders` removes each suffix as it removes an optional group. `expand` gains a
  first step: a suffix is written as `.` and its value when the value is one of `suffix_values`, as nothing when it has
  none, and any other value raises `ValueError` naming the values. A value is written verbatim: each is letters,
  digits and `.`.
- **`call`.** `--path format=zip` gives it. `check_parameters` names a suffix value that is none of `suffix_values`,
  with those values, in its one message: exit 2, nothing sent (AC-4.2).

### D4 — F4: the host root and the container registry (AC-5.1 to AC-5.3; UB-2)

**The base.** `registry.Base(Enum)`: `REST`, `HOST`, `CONTAINER_REGISTRY`. `base_of(*, path) -> Tuple[Base, str]`
returns `(HOST, rest)` for a path starting `HOST_ROOT` (`https://HOST`) and `/`; `(CONTAINER_REGISTRY, rest)` for one
starting `CONTAINER_REGISTRY_ROOT` (`/http(s)://${CI_REGISTRY}`) and `/`; `(REST, path)` otherwise. `placeholders`,
`required_placeholders` and `expand` read the rest only. In a `CONTAINER_REGISTRY` rest, each `${NAME}`
(`CONTAINER_REGISTRY_NAME`, `\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}`) is a path parameter, written as `_glob` writes a
glob: `/` kept, each part one percent-encoded segment, an empty, `.` or `..` part refused. A `REST` path reads as today.

**The host root** (AC-5.1). `Transport.request` and `request_raw` gain `base: Base = Base.REST`: `REST` sends under
`https://<hostname>/api/v4`, `HOST` under `https://<hostname>`, and `CONTAINER_REGISTRY` raises `ValueError`.
`registry.send` passes the record's base. The origin check and the one configured credential header are `_send`'s, as
before. `registry.pages` raises `ValueError` for a record whose base is not `REST`; no paged record has another.

**The container registry** (AC-5.2, AC-5.3). `registry.send` sends a `CONTAINER_REGISTRY` record through
`container_registry.send(*, transport, method, path, query, scope, project)`, a new module. `send` gains
`project: Optional[str] = None`, the configured project, which `send_call` passes; a container-registry record sent
without it raises `ValueError` before any request. Its steps, each before the next:

| Step | Request | Credential | Yields |
|---|---|---|---|
| 1 | `token_type` `private`: `software-supply-chain-security#as-a-regular-user-1` (`GET /user`) through `registry.send`; `job`: none; `bearer`: none | the configured header | the login: the answer's `username`; `gitlab-ci-token` for a job token; a `bearer` token raises `GitLabAPIError` |
| 2 | `tenant-scale#retrieve-a-project` (`GET /projects/<project>`) through `registry.send` | the configured header | the registry origin: `https://` and the text of `container_registry_image_prefix` before its first `/`, which must be non-empty and hold none of `@`, `?`, `#`, `\` or white space; any other raises `GitLabAPIError` before step 3 |
| 3 | `Transport.container_registry_token(login=..., scope=...)`: `GET https://<hostname>/jwt/auth?service=container_registry&scope=<scope>` | `Authorization: Basic` of `<login>:<token>` (RFC 7617), the request's only credential header | the answer's `token`, the registry token |
| 4 | `Transport.container_registry_request(origin=..., method=..., path=..., query=..., token=...)` | `Authorization: Bearer <registry token>` only | the `Response` |

- **The scope** is the record's `token_scope`, each `${NAME}` written as the call's value, as given:
  `package#delete-image-tags-by-reference` holds `repository:${CI_REGISTRY_IMAGE}:delete`,
  `package#listing-all-container-repositories` `registry:catalog:*` (Sources).
- **AC-5.3.** An HTTP error, no response, an answer whose field is absent or not a non-empty string, and an authority
  `transport.origin` refuses each raise `GitLabAPIError` before step 4: the entry script exits 1 and the registry
  receives nothing.
- **`_send(..., destination: Optional[Origin] = None)`**: the origin the URL must be on, the configured one by default.
  `container_registry_request` alone passes another, with a credential built from the registry token alone, so the
  configured token reaches only the configured origin (UB-2). The registry token enters no URL, log record or
  exception message: an error status at step 3 is reported as `_send` reports any, with the URL (which holds the
  scope) and GitLab's error text; a success answer whose `token` is absent or not a non-empty string is refused naming
  the URL and the field, never quoting its body, which holds the token.
- **`call`.** `--path CI_REGISTRY_IMAGE=group/project --path CI_COMMIT_SHORT_SHA=1a2b3c4` sends
  `DELETE https://<registry>/v2/group/project/tags/reference/1a2b3c4`.

### D5 — F5: request headers (AC-6.1 to AC-6.3)

- **The record.** `Location.HEADER = "header"`; a header `Param` is `Kind.SCALAR`, named as its section spells it
  (`X-Gitlab-Timestamp`, `Symbolchecksum`).
- **`encode`.** `EncodedRequest.headers: Tuple[Pair, ...] = ()`: each given header value as `_text` writes it, under its
  declared name, in the caller's order; a name given twice keeps its last value, as a path name or an attribute does
  and as `Request.add_header` stores one value per name. A value holding CR, LF or NUL raises `ValueError` (RFC 9110
  §5.5) through `registry.check_header_value(*, name, value)`, which `_build_request` also calls (`transport.py`
  already imports `gitlab_api.registry`). `send` passes the headers; `pages` refuses them as it refuses body values.
- **The transport.** `request` and `request_raw` gain `headers: Sequence[Pair] = ()`, carried by `_send` to
  `_build_request`, which adds each with `add_header` beside `Accept`, the `Content-Type` and the one credential header.
  A name equal, ignoring case, to `Accept`, `Content-Type`, `Content-Length`, `Transfer-Encoding`, `Host`,
  `User-Agent` or a `TOKEN_HEADERS` name, and a value holding CR, LF or NUL, raise `ValueError` before anything is
  sent. A header not given is not sent (AC-6.2).
- **`call --header NAME=VALUE`.** Constants `OPTION_HEADER` (`--header`) and `ARG_HEADERS` (`headers`); type
  `assignment`, `append`. `DESTINATION_OPTIONS` gains `(ARG_HEADERS, OPTION_HEADER)` last. `documented_names` gives
  `ARG_HEADERS` the `HEADER` `Param` names, and `ARG_FIELDS` and `ARG_FILES` the `QUERY` and `BODY` ones (every `Param`
  on the base). A name is matched ignoring case (RFC 9110 §5.1) and stored under its declared spelling; any other is
  refused as #41 AC-2.2 refuses an undocumented name (AC-6.3). A GraphQL record documents none.

### D6 — F6: two-level members, and the S3 import's gate (AC-7.1, AC-7.2)

- **The record.** `gitlab-dedicated#import-a-project-from-an-aws-s3-bucket`, `POST /projects/remote-import-s3`,
  `BodyFormat.FORM`: one `Location.BODY` `Param` per row of its table, in table order, under its full name
  (`override_params[visibility]`, `override_params[container_expiration_policy_attributes][cadence]`); `array of
  string` → `ARRAY`, `override_params[avatar]` (Notes "file upload") → `FILE`, any other → `SCALAR`; `required` where
  Required reads `yes`. No row of the section is a parent of another (#41 D5: "A bracketed body row with no parent row
  is declared in a FORM-body record").
- **How it is sent.** `registry._pairs` unchanged: `name=v`, an `ARRAY` as `name[]=v` per item, a `FILE` as the part of
  its name. A form body, or a multipart body when `--file` gives the avatar, carries each member at its bracketed name
  (`conventions.md` "Arrays, hashes and arrays of hashes"). The call gives them as any attribute:
  `-f 'override_params[container_expiration_policy_attributes][cadence]=7d'`, `-F 'override_params[tag_list]=["a"]'`,
  `--file 'override_params[avatar]=logo.png'`.
- **The gate.** `families/gitlab_dedicated.py` defines `OP_IMPORT_FROM_S3`; `GATED_OPERATIONS` maps it to `None`, so
  `call` refuses it before `registry.lookup`: ": no subcommand sends it", exit 2, nothing sent (#44 D6's form). The
  comment of `GATED_OPERATIONS` names the class it adds: a record that writes into an existing project. A test that
  proves the body runs `call` with `GATED_OPERATIONS` replaced, for that test only, by the mapping without the ID.
- **N.** `PARENT_KEY` reads one or more `[key]` levels (D7).

### D7 — N's readings (AC-1.2, AC-7.2, AC-8.1, AC-8.2)

`test/test_gitlab_wrapper_contract.py`. N restates each form with its own patterns and never calls `lookup`, `expand`
or `base_of`, so the oracle does not share the code it judges (#40 D3). N reads a field the base lacks with its
default (`getattr(record, "positional_names", ())`) and recognises a header `Param` by `location.value == IN_HEADER`
(a new N constant, `"header"`, beside `IN_PATH`), so that on the base its existing tests fail only through
`header_problems` and #43's `test_only_the_upload_module_path_holds_a_hyphenated_name` as D9 restates it.

| Reading | The edit |
|---|---|
| `PARENT_KEY` | `[A-Za-z_][A-Za-z0-9_]*(?:\[[A-Za-z0-9_]+\])+` (F6) |
| `Section.headers` (default `()`), `page_sections` | the backticked names of the section's `- Request headers:` line, then its `header` rows, each once (F5) |
| `record_problems` | gains `header_problems(*, record, section)`: the record's `HEADER` `Param` names differ, ignoring case, from `section.headers`; `param_problems` judges no `HEADER` `Param` (AC-8.2) |
| `SentCall`, `sent_call` | gain `base` (default `REST`) and `headers`. `REST` is a URL under `https://<HOST>/api/v4`, `HOST` one on that host outside it, any other the URL's origin text; `path` follows the base. `headers` are the recorded names but the transport's and urllib's (`Accept`, `Content-Type`, `Content-Length`, `Transfer-Encoding`, `Host`, `User-Agent`, the credential headers) |
| `expanded_path` | each `[.name]` written `.<value>` when given, else nothing; each `${NAME}` replaced as a `:name`; a list value written one item per place |
| `route_problems` | compares the sent base and path with each endpoint's: `https://HOST` → `HOST`, `/http(s)://${CI_REGISTRY}` → `https://` + N's `CONTAINER_REGISTRY_HOST`, else `REST`, and the rest expanded |
| `call_problems` | names a sent header the section does not name (ignoring case), and a given header not sent (AC-8.2) |
| `record_call` | `--endpoint 'METHOD path'` for a record whose ID more than one record declares; each place of a `positional_names` name its own value (`v1`, `v2`); no value for a `[.name]` suffix; `--header NAME=v1` per `HEADER` `Param` |
| the send test's loop | a container-registry record gets D4's answers to steps 1 to 3 queued before `{}` (a `username`, a `container_registry_image_prefix` on `CONTAINER_REGISTRY_HOST`, a `token`) and is judged on its last request, the others on the configured origin; an F1 record is judged against its own endpoint alone |

`test_every_record_is_sent_as_its_section_documents` keeps skipping `GATED_OPERATIONS`; the S3 import is sent by
`test_a_two_level_member_is_read_and_sent_as_written` with the gate lifted (D6). The module docstring names the forms.

### D8 — The records (AC-1.1 to AC-1.3)

**Rules.** An F1 record is written from its section by its family docstring's rules, the base record's, with its own
method and path, so it declares the base record's `Param`s less any naming a path parameter of its own path. A new ID
follows its family's rules plus D2 to D6's fields. Each family docstring states its F1 rule and any field of D2 to D6
it uses; `openapi_only.py`'s and `gitlab_dedicated.py`'s change the rules that kept the header rows and the S3 import
out.

| Family module | Reference | Keys it gains, beside the base record's |
|---|---|---|
| `create` | `create#generate-changelog-data` | `GET /projects/:id/repository/changelog.txt` |
| `create` | `create#delete-a-group-ssh-certificate` (new; F2) | `DELETE /groups/:id/ssh_certificates/:id` |
| `create` | `create#retrieve-file-archive-from-a-repository` (new; F3) | `GET /projects/:id/repository/archive[.format]` |
| `developer_experience` | `developer-experience#file-path-branches-and-tags-name` | `GET /projects/1/branches/my%2Fbranch/commits`, `GET /projects/1/repository/tags/my%2Ftag` (no path parameter, no `id` default) |
| `fulfillment` | `fulfillment#delete-an-ldap-group-link-deprecated` | `DELETE /groups/:id/ldap_group_links/:provider/:cn` |
| `plan` | the emoji-reaction "…a resource" References (list, add, retrieve, delete) | each one's `merge_requests/:merge_request_iid` and `snippets/:snippet_id` key |
| `plan` | `plan#retrieve-notification-settings`, `plan#update-group-or-project-notification-settings` | each one's `/groups/:id/notification_settings` key |
| `security_risk_management` | `security-risk-management#create-a-dependency-list-export` | `POST /groups/:id/dependency_list_exports`, `POST /pipelines/:id/dependency_list_exports` |
| `software_supply_chain_security` | the access-request and custom-attribute References; `…#set-your-user-status` | their `/groups/:id/…` and `/users/:id/…` keys; `PATCH /user/status` |
| `software_supply_chain_security` | `…#retrieve-the-token-information` (new; F4), `…#set-status-of-an-external-control` (new; F5) | `GET https://HOST/oauth/token/info`; the `PATCH …/compliance_external_controls/:external_control_id/status` key, with `Param(name=<name>, location=Location.HEADER, required=True)` for `X-Gitlab-Timestamp`, `X-Gitlab-Nonce` and `X-Gitlab-Hmac-Sha256` (each `(required)` on its `- Request headers:` line) |
| `tenant_scale` | the invitation References | each one's `/groups/:id/invitations…` key |
| `tenant_scale` | the revoke and rotate References of `…/personal_access_tokens/:id` and `…/resource_access_tokens/:id` (new; F2) | their keys |
| `verify` | `verify#list-all-of-a-groups-runners`, `verify#get-the-latest-release`, `verify#metadata-api-1` | `GET /groups/:id/runners/all`; `…/permalink/latest/downloads/bin/asset.exe`, `…/permalink/latest/evidence`; `GET /version` |
| `package` | each Conan v1 Reference #43 keeps pending; `package#upload-a-package-file-5` | its `/projects/:id/packages/conan/v1/…` key; `PUT /projects/:id/packages/nuget/v2` |
| `package` | `package#delete-image-tags-by-reference`, `package#listing-all-container-repositories` (new; F4) | the `/http(s)://${CI_REGISTRY}` keys |
| `gitlab_dedicated` | `gitlab-dedicated#import-a-project-from-an-aws-s3-bucket` (new; F6) | `POST /projects/remote-import-s3` |
| `openapi_only` | `openapi-only#the-nuget-symbol-file-download-endpoint` and `…-1` (changed; F5) | none: each gains `Param(name="Symbolchecksum", location=Location.HEADER, required=True)` |

Each family's `PENDING` loses those keys and keeps every other (AC-1.3).

### D9 — Existing tests that hold the base's pending state (UB-1)

These assert what AC-1.1, AC-6.1, D3 and D4 change: a family's `PENDING` set, one record per Reference, no record of a
kept ID, JSON-only bodies, `REQUIRED` without `Symbolchecksum`, or a path's parameters read as `:name` and `*name`
alone. Each keeps its assertions' subject; its expected literal gains this change's records and loses the issue keys,
and an "each ID once" assertion becomes "each key once, each ID's records starting with its base record". A
`{id: (method, path)}` literal keeps its shape and the base record's key; an F1 Reference's other keys are asserted
from a literal of their own (`developer_experience`, `fulfillment` and `tenant_scale` already hold
`OTHER_ENDPOINT_KEYS`):

- `test_only_the_kept_keys_are_pending` of `create`, `developer_experience`, `fulfillment`, `plan`, `tenant_scale`,
  `verify` and `gitlab_dedicated`; `test_only_the_unmapped_keys_are_pending` of `security_risk_management` and
  `software_supply_chain_security`;
- `test_every_reference_has_its_record` of `developer_experience`, `fulfillment`, `tenant_scale` and
  `gitlab_dedicated`, and `test_only_the_list_records_are_paged` of `gitlab_dedicated` (its `RECORD_ENDPOINTS` gains
  the S3 import); `test_every_key_has_its_record` of `security_risk_management` and `software_supply_chain_security`;
- `test_every_param_is_typed_as_its_row` of `tenant_scale`, `gitlab_dedicated` and `openapi_only`, and
  `test_the_required_attributes_are_the_sections` of `software_supply_chain_security`, whose literals are keyed by the
  family's IDs;
- #43's F `test_nothing_is_pending_but_the_kept_keys` and `test_a_two_endpoint_entry_maps_its_first_endpoint`, and
  #43's N `test_only_the_upload_module_path_holds_a_hyphenated_name`, whose rule gains two exceptions beside
  `package#upload-module`: the `archive[.format]` row gives `("id", "format")`, the delete-by-reference row
  `("CI_REGISTRY_IMAGE", "CI_COMMIT_SHORT_SHA")`.

Every other existing test of `src/payload/test/test_gitlab_*.py`, P, N and V passes unedited.

### D10 — Tests

The new tests are added to R, T, K, C, G (new), P, N and the family modules F:plan, F:software_supply_chain_security,
F:developer_experience, F:create, F:tenant_scale, F:package, F:openapi_only and F:gitlab_dedicated; each is named with
its oracle under Correctness Properties and per criterion in the Acceptance Criteria Mapping. P's properties are the
criteria that quantify over values (AC-2.4, AC-3.2, AC-4.2); P's module docstring names them. Every expected URL,
header, body, key and value is a literal transcribed from the index, the sections and docs.gitlab.com, never read from
the records.

### D11 — The usage docstring and the map (AC-9.1, AC-9.2)

The module docstrings of `src/payload/scripts/gitlab_wrapper.py` (its `call` usage lines) and `commands/call.py` (the
grammar, one bullet per option, the refusals) state each form with one example, wrapped at 120 columns:

```
call plan#add-an-emoji-reaction-to-a-resource --path merge_request_iid=5 -f name=thumbsup
    --endpoint 'POST /projects/:id/merge_requests/:merge_request_iid/award_emoji'
call create#delete-a-group-ssh-certificate --path id=7 --path id=12345
call create#retrieve-file-archive-from-a-repository --path format=zip
call software-supply-chain-security#set-status-of-an-external-control --path external_control_id=3 -f status=pass
    --header X-Gitlab-Timestamp=1700000000 --header X-Gitlab-Nonce=n1 --header X-Gitlab-Hmac-Sha256=ab12
-f 'override_params[container_expiration_policy_attributes][cadence]=7d'   # a two-level member, by its full name
```

They also say that an F1 Reference without `--endpoint` sends its first declared endpoint, that the S3 import is
refused, and that a container-registry record obtains its registry token from the configured instance. The
`commands/call.py` sentence "A path name … given twice keeps its last value" gains "but a name of the record's
`positional_names`, whose values fill its places in command-line order (D2)". The `src/payload/scripts/gitlab_api/`
bullet of `docs/forLLMConsumption.md` names `--endpoint`, the repeated `--path` (two `--path id=`), `--path format=`,
`--header` and the two-level member's full name in one sentence, under its cap.

### D12 — Files

#41 D8's slice table names #35–#40 and #42–#44. This change is the request-form work its exceptions row leaves to a
later change ("a request form that part 1 does not build"), and this table is the change's own. Its edits beyond that
row are `commands/call.py` past `GATED_OPERATIONS` (D1 to D6), the entry script's docstring (D11) and N past its path
reading (D7). Every other row of #41 D8 still holds.

| D | File | Change |
|---|---|---|
| D1–D5 | `src/payload/scripts/gitlab_api/registry.py` | `Base`, `base_of`, `HOST_ROOT`, `CONTAINER_REGISTRY_ROOT`, `CONTAINER_REGISTRY_NAME`, `OPTIONAL_SUFFIX`, `Location.HEADER`; `RestOperation.positional_names`, `suffix_values`, `token_scope`; `EncodedRequest.headers`, `check_header_value`; `lookup`'s `endpoint`; `placeholders`, `required_placeholders`, `expand`, `encode`; `send`'s `endpoint`, `project` and bases; `call`'s and `pages`' `endpoint`; the docstrings |
| D4 | `src/payload/scripts/gitlab_api/container_registry.py` | new: `send` and D4's steps 1 and 2 |
| D4, D5 | `src/payload/scripts/gitlab_api/transport.py` | `request`'s and `request_raw`'s `base` and `headers`; `_send`'s `destination` and `headers`; `_build_request`'s `headers`; `container_registry_token`, `container_registry_request`; the docstring |
| D1–D6 | `src/payload/scripts/gitlab_api/commands/call.py` | `--endpoint`, `endpoint_key`, `--header`, `DESTINATION_OPTIONS`, `documented_names`, `path_values`, `missing_path_parameters`, `check_parameters`, `documented_text`, `undocumented`, `_compared_name`, `call_values`, `attribute_values`, `prepare_call`, `PreparedCall.endpoint`, `send_call`'s `project`; `GATED_OPERATIONS` gains the S3 import; the docstring |
| D11 | `src/payload/scripts/gitlab_wrapper.py` | the module docstring |
| D8 | `families/create.py`, `developer_experience.py`, `fulfillment.py`, `plan.py`, `security_risk_management.py`, `software_supply_chain_security.py`, `tenant_scale.py`, `verify.py`, `package.py`, `gitlab_dedicated.py` (and `OP_IMPORT_FROM_S3`), `openapi_only.py` | D8's records; `PENDING`; the docstrings |
| D7, D9 | `test/test_gitlab_wrapper_contract.py` | D7's readings, its tests, D9's `test_only_the_upload_module_path_holds_a_hyphenated_name` rule, the docstring |
| D9, D10 | R, T, K, C, P, the new G and the family test modules D9 and D10 name | D10's tests; D9's literals |
| D11 | `docs/forLLMConsumption.md` | the `gitlab_api/` bullet |
| — | `docs/findings-ledger.md` | the Residuals' rows, with `python scripts/memory_compile.py ledger add` |

**Not edited:** `commands/_common.py`, the compatibility commands, `graphql_only.py`, `gitlab_wrapper_fixtures.py`
(`FakeGitLab.install` serves every origin through `https_open`), V (`record_key_problems` already takes several keys
per Reference), UB-4's GitHub files.

### Sources

- Local reference: `operations-index.md` (the issue keys' rows); `rest/plan.md` "Add an emoji reaction to a resource";
  `rest/create.md` "Delete a group SSH certificate", "Retrieve file archive from a repository"; `rest/tenant-scale.md`
  the enterprise-user token sections, "Retrieve a project" (`container_registry_image_prefix`);
  `rest/software-supply-chain-security.md` "Set status of an external control" (`- Request headers:`), "Retrieve the
  token information"; `rest/openapi-only.md` "The NuGet Symbol File Download Endpoint" (`Symbolchecksum` `header`);
  `rest/gitlab-dedicated.md` "Import a project from an AWS S3 bucket"; `rest/package.md` "Container registry API";
  `conventions.md` "Arrays, hashes and arrays of hashes".
- `gitlab-org/gitlab` `master`, read 2026-11-11:
  - `doc/api/container_registry.md`: `--user "${CI_REGISTRY_USER}:${CI_REGISTRY_PASSWORD}"`,
    `--url "${CI_SERVER_URL}/jwt/auth?service=container_registry&scope=${SCOPE}"`, `SCOPE` e.g.
    `repository:${CI_PROJECT_PATH}:delete`; "Listing all container repositories": `scope=registry:catalog:*` with
    administrator credentials; both registry calls send `--header "Authorization: Bearer <token_from_above>"`;
  - `doc/user/packages/container_registry/authenticate_with_container_registry.md`: the credential types (password,
    personal, fine-grained, deploy, project and group access tokens, the GitLab CLI); "Authenticate with a token":
    `docker login registry.example.com -u <username> --password-stdin`; "Authenticate with the registry API": "get a
    registry token from GitLab, then pass it in the `Authorization: Bearer` header", "A registry token is different
    from a personal, project, or group access token", "the registry token is its `token` field";
  - `doc/ci/variables/predefined_variables.md`: `CI_REGISTRY` "formatted as `<host>[:<port>]`"; `CI_REGISTRY_IMAGE`
    "formatted as `<host>[:<port>]/<project_full_path>`"; `CI_REGISTRY_PASSWORD` "the same as the `CI_JOB_TOKEN`";
  - `doc/api/projects.md` "Retrieve a project": `container_registry_image_prefix` "Prefix for container registry
    images", example `registry.example.com/diaspora/diaspora-client`;
  - `app/controllers/jwt_controller.rb` `authenticate_project_or_user`: `authenticate_with_http_basic` is its only
    credential reading; `lib/gitlab/auth.rb` `find_for_git_client`: `build_access_token_check` returns `unless login ==
    CI_JOB_USER` (`'gitlab-ci-token'`), and `personal_access_token_check(password, project)` compares no login.
- docs.gitlab.com `oauth2` "Retrieve the token information", `repositories` "Available options", `external_controls`,
  `group_ssh_certificates`, `groups` (as `requirements.md` quotes them).
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) §5.1 "Field names are case-insensitive"; §5.5 "Field values
  containing CR, LF, or NUL characters are invalid and dangerous". [RFC 7617](https://www.rfc-editor.org/rfc/rfc7617)
  §2: the user-id, a single colon and the password, "encoding this octet sequence using Base64".
- Python 3.9 `urllib.request` `AbstractHTTPHandler.do_request_` (adds `Content-type`, `Content-length` or
  `Transfer-encoding`, `Host` and the opener's `User-agent` as unredirected headers); `base64.b64encode`.

## Testing Strategy

- **Fake host.** `gitlab_wrapper_fixtures.FakeGitLab`, unedited: it records every request of every origin (the
  registry's included) with its method, URL, headers and body. Calls run `main(argv=["call", …])` through
  `fixtures.run_main`; refusals are judged by exit code, `caplog` and "no request recorded" (or none to the registry).
- **Registry and transport examples.** R works on synthetic `RestOperation`s on reference paths; T on a `Transport`
  of each `TokenType` against the fake host.
- **Properties.** P puts `src/payload/scripts` on `sys.path`, `@settings(deadline=None)`, as its existing properties.
- **Contract and coverage.** N, as in D7; V, unedited; both find the records by discovery.
- **Runner.** Locally `python scripts/run_tests.py <these paths>`; in CI the `verify` job of `.github/workflows/ci.yml`,
  leg `tests` (`python scripts/run_checks.py --group tests`).
- **E2E.** The wrapper is a command-line program with nothing deployed. N and the tests of AC-8.3 run `call` through
  `main`'s argv against the fake host to the API boundary in CI's `tests` leg; the real-instance check is #11's run on
  an ephemeral `sff-test-*` project.

## Correctness Properties

"The configured project" is a test's `project_id` in `config/gitlab.json`; "the registry" is the authority the test's
scripted `container_registry_image_prefix` holds (`registry.example.com`).

- **AC-1.1, AC-1.3, AC-1.4** — Structural: V `test_every_index_row_is_mapped_or_pending` and
  `test_every_declared_key_is_in_its_family` on the merged tree; D9's pending tests, each literal the base's kept keys
  less the issue keys.
- **AC-1.2** — Structural: N `test_every_record_matches_its_reference_section` over every record, the F1, header and
  S3 records included; D9's typing tests, their literals holding the new records' kinds and required rows; N
  `test_each_record_of_an_id_copies_its_base_record`: for every ID that several REST records of one family declare,
  each record after the first declares the first's `Param`s (name, location, kind, required) less those naming a
  placeholder of its own path, and the first's `body`, `paging` and `fixed` (D8 Rules); the IDs it judges include
  `plan#add-an-emoji-reaction-to-a-resource` and `verify#get-the-latest-release`, so it is red on the base.
- **AC-2.1**
  - Example, F:plan `test_an_other_endpoint_is_sent_when_named`: `call plan#add-an-emoji-reaction-to-a-resource
    --endpoint 'POST /projects/:id/merge_requests/:merge_request_iid/award_emoji' --path merge_request_iid=5
    -f name=thumbsup` records one `POST …/api/v4/projects/<project_id>/merge_requests/5/award_emoji`, JSON body names
    `name`.
  - Example, F:software_supply_chain_security `test_the_user_status_patch_is_sent_when_named`: `--endpoint
    'PATCH /user/status'` records one `PATCH …/api/v4/user/status`.
  - Example, K `test_an_endpoint_is_named_by_its_method_and_path`: the same emoji call with `--endpoint` of the
    snippet endpoint and `--path snippet_id=9` sends `…/snippets/9/award_emoji`.
- **AC-2.2** — Example, F:plan `test_an_other_endpoint_is_sent_when_named`: without `--endpoint`, `--path issue_iid=4`
  sends `…/issues/4/award_emoji`; R `test_lookup_chooses_an_endpoint_of_a_reference`: `lookup` with no endpoint
  returns the first record of a synthetic family declaring one ID on three paths.
- **AC-2.3** — Parametrized example, F:developer_experience `test_the_literal_endpoints_are_sent_as_written`: each
  endpoint of the section, named with `--endpoint` and no `--path`, records `GET …/api/v4` plus the path verbatim,
  `…/projects/1/repository/tags/my%2Ftag` among them.
- **AC-2.4**
  - Example, K `test_an_endpoint_the_reference_does_not_declare_is_refused`: `--endpoint 'POST /projects/:id/epics'` and
    `--endpoint 'PUT /projects/:id/issues/:issue_iid/award_emoji'` exit 2, nothing recorded, the log naming the three
    declared endpoints; `--endpoint POST` (no path) exits 2 with `argument --endpoint:` on standard error.
  - Example, K `test_an_endpoint_is_named_by_its_method_and_path`: the merge-request endpoint with `--path issue_iid=5`
    exits 2, nothing recorded, the log naming `"issue_iid"` given with `--path`.
  - Property, P `test_only_a_declared_endpoint_is_chosen`: over method and path texts, `lookup` on a synthetic ID
    returns the record whose key equals the pair and raises `ValueError` for any other; `@example` cases differing only
    in case, a trailing `/` or a `:name`.
  - Example, R `test_lookup_chooses_an_endpoint_of_a_reference`: two records of one key in one family, and one ID in
    two families, raise "declared … times"; a GraphQL record given an endpoint raises; the existing
    `test_lookup_refuses_unknown_and_duplicate_ids` (two families) passes unedited.
- **AC-3.1, AC-3.2**
  - Example, F:create `test_each_id_of_the_certificate_path_takes_its_place`: AC-3.2's first call sends
    `DELETE …/api/v4/groups/7/ssh_certificates/12345`.
  - Parametrized example, F:tenant_scale `test_each_id_of_a_token_path_takes_its_place`, each F2 key of the family
    with `--path id=7 --path id=self`: `POST …/api/v4/groups/7/manage/personal_access_tokens/self/rotate` among them.
  - Property, P `test_each_place_takes_its_own_value`: two values, each non-surrogate text but `""`, `.` and `..`;
    `expand` of `/groups/:id/ssh_certificates/:id` with `positional_names=("id",)` gives segments that unquote to
    the first and the second value.
  - Example, R `test_each_place_of_a_positional_name_takes_its_own_value`: as P with `7` and `my/group`; one value or
    three raise `ValueError`; without `positional_names`, `/<route-prefix>/symbolfiles/:file_name/:signature/:file_name`
    routed under `/projects/:id/packages/nuget` writes its one `file_name` at both places (UB-1).
- **AC-3.3** — Example, K `test_a_two_value_path_given_one_value_is_refused`: `create#delete-a-group-ssh-certificate`
  with one `--path id=7`, and with none, exits 2, nothing recorded, the log saying `id` has no value and listing
  `id, id`; three `--path id` exit 2 naming "more values than its places".
- **AC-4.1**
  - Parametrized example, F:create `test_the_archive_format_is_sent_as_its_suffix`: each listed format sends
    `GET …/projects/<project_id>/repository/archive.<format>`; no `--path format` sends `…/archive`; no URL holds `[`.
  - Example, R `test_the_suffix_is_written_only_when_given`: `placeholders` holds `format`, `required_placeholders`
    does not; `expand` with `zip`, with none, and with `None`.
- **AC-4.2**
  - Example, K `test_a_format_the_page_does_not_list_is_refused`: `--path format=rar` and `--path format=ZIP` exit 2,
    nothing recorded, the log naming every listed format.
  - Property, P `test_only_a_listed_format_reaches_the_path`: over `st.one_of(st.sampled_from(<the eight formats>),
    st.text())`, a listed value gives `.value`; any other raises `ValueError`.
- **AC-5.1**
  - Example, F:software_supply_chain_security `test_the_token_information_is_sent_outside_the_api`: one
    `GET https://<HOST>/oauth/token/info` carrying the configured `Private-token` and no other credential header.
  - Example, T `test_a_host_request_is_sent_outside_the_api`, per `TokenType`: `request(base=Base.HOST)` records that
    URL with the type's header; `base=Base.CONTAINER_REGISTRY` raises `ValueError`, nothing recorded.
  - Example, R `test_the_base_is_read_from_the_path`: `base_of` of a path of each base; `placeholders` of the delete
    path is `("CI_REGISTRY_IMAGE", "CI_COMMIT_SHORT_SHA")`.
- **AC-5.2**
  - Example, F:package `test_a_registry_record_is_sent_to_the_registry_with_its_token`: `call
    package#delete-image-tags-by-reference --path CI_REGISTRY_IMAGE=group/project --path CI_COMMIT_SHORT_SHA=1a2b3c4`,
    answers scripted. Oracle, in order: `GET …/api/v4/user`; `GET …/api/v4/projects/<project_id>`;
    `GET https://<HOST>/jwt/auth?service=container_registry&scope=repository%3Agroup%2Fproject%3Adelete` carrying
    `Authorization: Basic <base64 of username:token>` and no `Private-token`;
    `DELETE https://registry.example.com/v2/group/project/tags/reference/1a2b3c4` carrying `Authorization: Bearer
    <registry token>` and neither the configured token nor its header. `package#listing-all-container-repositories`
    asks for `registry%3Acatalog%3A%2A` and sends `GET https://registry.example.com/v2/_catalog`. With the registry
    answering `404` to step 4: exit 1, and neither the configured token nor the scripted registry token in any log
    record.
  - Example, T `test_the_registry_token_is_asked_for_with_basic_credentials` and
    `test_a_registry_request_carries_only_the_registry_token`: those URLs and headers; a request to an origin other
    than `destination` raises `GitLabAPIError`, nothing recorded.
  - Example, G `test_a_job_token_logs_in_as_gitlab_ci_token`: a job token sends no `GET /user`, and the `/jwt/auth`
    request's `Authorization: Basic` decodes to `gitlab-ci-token:<token>`. R
    `test_send_fetches_the_registry_token_before_the_registry`: a container-registry record sent without `project`
    raises `ValueError`, nothing recorded.
- **AC-5.3** — Parametrized example, F:package `test_no_registry_token_sends_nothing_to_the_registry`: `GET /user`
  answering 401; a project answer without `container_registry_image_prefix`, or with `""`, `/group/project`,
  `registry.example.com#/x` or `user@registry.example.com/x`; `/jwt/auth` answering 401, or `{}`; a `bearer` token.
  Oracle: exit 1; the recorded requests are exactly those of the steps up to the failing one, its own included (none
  for `bearer`, step 1 for `GET /user`'s 401, steps 1 and 2 for a project answer, steps 1 to 3 for a `/jwt/auth`
  answer); none of the configured token, the base64 of `<login>:<token>` and the scripted registry token in any log
  record.
- **AC-6.1** — Structural: N `test_every_record_matches_its_reference_section` through `header_problems`.
- **AC-6.2**
  - Example, F:software_supply_chain_security `test_the_external_control_status_carries_its_headers`: AC-6.2's call
    records one `PATCH …/projects/<project_id>/compliance_external_controls/3/status` with the given headers at their
    values, `Accept`, `Content-Type: application/json`, the configured header, and the JSON body `{"status": "pass"}`;
    without `--header X-Gitlab-Nonce` the request carries no `X-Gitlab-Nonce`.
  - Example, F:openapi_only `test_the_symbol_download_sends_its_checksum_header`: both records with
    `--header Symbolchecksum=SHA256:ab` send that header.
  - Example, T `test_a_request_header_is_sent_beside_the_transport_headers`: the headers given are recorded beside
    the transport's; `Accept`, `content-type`, `Host`, `Content-Length`, `PRIVATE-TOKEN` as names, and a value with
    `\r\n`, raise `ValueError` with nothing recorded. R `test_a_header_param_is_encoded_as_a_header`: `encode` gives
    `headers`, never query, form or JSON.
- **AC-6.3** — Example, K `test_an_undeclared_header_is_refused`: `--header X-Other=1`, `-f X-Gitlab-Nonce=n1` and
  `--header` on a record with no header exit 2, nothing recorded, the log naming the name with its option;
  `--header x-gitlab-nonce=n1` is accepted: exit 0, the recorded request's `header(name="X-Gitlab-Nonce")` is `n1`,
  and `call_values` holds it under `X-Gitlab-Nonce`.
- **AC-7.1**
  - Parametrized example, F:gitlab_dedicated `test_the_s3_import_sends_every_member_at_its_name`, the gate lifted
    (D6): the required rows with `-f`, `override_params[visibility]=private`, the two-level `cadence`,
    `-F 'override_params[tag_list]=["a","b"]'`. Form case: `application/x-www-form-urlencoded` pairs
    `override_params[container_expiration_policy_attributes][cadence]=7d` and `override_params[tag_list][]` twice.
    Multipart case, with `--file override_params[avatar]=<a file>`: parts of those names and a part
    `override_params[avatar]` with a `filename` and the file's bytes.
  - Example, K `test_the_s3_import_is_refused`: the same call without the lift exits 2, nothing recorded, the log
    ending ": no subcommand sends it".
- **AC-7.2** — Example, N `test_a_two_level_member_is_read_and_sent_as_written`: `record_problems` passes the declared
  record; names the record built `BodyFormat.JSON`; names the `cadence` row of the record built without it. Through
  `main` with the gate lifted, AC-7.1's form call passes `call_problems`; `call_problems` names a sent
  `override_params[container_expiration_policy_attributes][bogus]` and `override_params[bogus]`.
- **AC-8.1**
  - Structural: N `test_every_record_is_sent_as_its_section_documents`, each F1 record named with `--endpoint`, each
    F4 record at its base or origin (D7).
  - Example, N `test_an_endpoint_a_place_a_suffix_and_a_base_are_read_as_written`: `route_problems` passes
    `/groups/v1/ssh_certificates/v2` and names `…/v2/v2`; passes `/projects/v1/repository/archive` and
    `…/archive.zip` with `format=zip`, names `…/archive[.format]`; passes `GET /oauth/token/info` on `HOST` and names
    it on `REST`; passes `/v2/v1/tags/reference/v1` on the registry origin and names it on the configured one; judged
    against the snippet endpoint alone, names a sent issue path.
- **AC-8.2** — Example, N `test_a_request_header_is_read_and_sent_as_written`: `Section.headers` of the external
  control holds its `- Request headers:` names, and of both NuGet downloads `Symbolchecksum`; `header_problems` names
  the external control built without `X-Gitlab-Nonce` and with an `X-Other`; `call_problems` names a sent `X-Other`
  and a given `X-Gitlab-Nonce` not sent, and passes `x-gitlab-nonce` sent for `X-Gitlab-Nonce`.
- **AC-8.3** — The examples above of AC-2.1 to AC-2.3, AC-3.2, AC-4.1, AC-5.1, AC-5.2, AC-6.2 and AC-7.1 run `main` and
  assert method, URL, headers and body names; those of AC-2.4, AC-3.3, AC-4.2, AC-5.3 and AC-6.3 assert the exit code
  and that nothing was sent (to the registry, for AC-5.3).
- **AC-9.1** — Example, C `test_the_usage_names_the_request_forms` and K
  `test_the_call_docstring_names_the_request_forms`: each docstring holds `--endpoint`, two `--path id=` in one line,
  `--path format=`, `--header` and `override_params[container_expiration_policy_attributes]`.
- **AC-9.2** — Example, N `test_the_map_names_the_request_forms`: the `src/payload/scripts/gitlab_api/` bullet of
  `docs/forLLMConsumption.md` holds AC-9.1's spellings: `--endpoint`, two `--path id=`, `--path format=`, `--header`
  and `override_params[container_expiration_policy_attributes]`, as `test/test_gitlab_graphql_contract.py` pins the
  GraphQL bullet (#44 AC-5.2); `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` passes.
- **UB-1** — C and every existing test but D9's pass unedited; R's positional example holds the NuGet repeat; K's
  existing tests hold every base option and exit code.
- **UB-2** — P `test_standard_library_only` scans `container_registry.py` too; K `test_call_takes_no_token_option` reads
  `--endpoint` and `--header`; C `test_load_config_refusals`, `test_environment_token_ignored` pass; AC-5.2's and
  AC-5.3's oracles: no request off the configured origin carries the configured token or its header.
- **UB-3** — K's existing refusal tests pass; AC-2.4, AC-4.2 and AC-6.3's refusals; `GATED_OPERATIONS` changes only by
  D6's entry.
- **UB-4** — `src/payload/test/test_github_api_*.py` pass in CI; the PR diff names no GitHub file.

## Security Considerations

- **The configured token** goes only to the configured origin: in its header to every REST and `HOST` request, and as
  the password of `Authorization: Basic` to `/jwt/auth` alone (D4 step 3). `container_registry_request` builds its
  credential from the registry token, and `_send` refuses any origin but its `destination`.
- **The registry token** is GitLab's answer, scoped by the record's `token_scope`; GitLab grants it only what the
  configured token's user may do. It goes only to the origin named by the `container_registry_image_prefix` of step 2's
  answer, which, like every `GET`, may follow a redirect (#13 D4), over `https`, and is never logged or quoted.
- **Redirects.** `CredentialStrippingRedirectHandler` strips `Authorization` on a cross-origin hop, Basic and Bearer
  alike; a `DELETE` or `PATCH` redirect is not followed (#13 D4).
- **Headers.** Only a name the record declares is sent; the transport refuses a name it owns and a value with CR, LF or
  NUL, so a caller header neither replaces the credential nor splits the request. `X-Gitlab-Hmac-Sha256` is the
  caller's value (requirements Residuals).
- **Paths.** An endpoint is chosen by equality with a declared key, a format from a fixed list; positional and
  `${NAME}` values are written by `_segment` and `_glob`, so no value adds `?`, `#` or a dot segment, and none changes
  the host (#40 Security).
- **What stays callable**: every record of D8 but the S3 import (Gates), none gated (#41 Security "Destructive
  operations"): the F1 `DELETE` keys (access-request deny, custom-attribute deletes, invitation delete, the LDAP link
  delete, the Conan v1 recipe-and-package delete), the F2 revoke and rotate records and the SSH-certificate delete;
  the registry tag delete; `_catalog`, which GitLab answers for an administrator.
- **Gates.** `GATED_OPERATIONS` gains the S3 import, which takes `overwrite` (D6); the other kept imports stay pending.
- **Dependencies.** None added; standard library only, no subprocess.

## Operability

The GitLab wrapper is not installed here (`config/toolchain.json` `not_installed`); the records reach a project through
the setup prompts' copy of `gitlab_api/` (#13 D2). Nothing deploys and no configuration changes. An unknown endpoint,
a short positional path, an unlisted format and an undeclared header are refused as #41 refuses an undocumented name:
logged, exit 2, nothing sent. A registry token GitLab does not issue exits 1 with GitLab's error text.

## Acceptance Criteria Mapping

In `src/payload/test/`: R = `test_gitlab_api_registry.py`, T = `test_gitlab_api_transport.py`,
K = `test_gitlab_api_call.py`, C = `test_gitlab_wrapper_compat.py`, G = `test_gitlab_api_container_registry.py` (new),
F:<family> = `test_gitlab_api_<family>.py`. In `test/`: P = `test_gitlab_api_properties.py`,
N = `test_gitlab_wrapper_contract.py`, V = `test_gitlab_wrapper_coverage.py`.

| Criterion | Component | Tests |
|---|---|---|
| AC-1.1 | D8; `PENDING` | V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`; D9's pending tests |
| AC-1.2 | D8; D7 | N `test_every_record_matches_its_reference_section`, `test_each_record_of_an_id_copies_its_base_record`; D9's typing tests |
| AC-1.3 | D8 | D9's pending tests; V |
| AC-1.4 | D8 | V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` |
| AC-2.1 | D1 `lookup`, `--endpoint` | F:plan `test_an_other_endpoint_is_sent_when_named`; F:software_supply_chain_security `test_the_user_status_patch_is_sent_when_named`; K `test_an_endpoint_is_named_by_its_method_and_path` |
| AC-2.2 | D1 `lookup` | F:plan `test_an_other_endpoint_is_sent_when_named`; R `test_lookup_chooses_an_endpoint_of_a_reference` |
| AC-2.3 | D1; D8 | F:developer_experience `test_the_literal_endpoints_are_sent_as_written` |
| AC-2.4 | D1 `lookup`, `endpoint_key`, `check_parameters` | K `test_an_endpoint_the_reference_does_not_declare_is_refused`, `test_an_endpoint_is_named_by_its_method_and_path`; P `test_only_a_declared_endpoint_is_chosen`; R `test_lookup_chooses_an_endpoint_of_a_reference` |
| AC-3.1, AC-3.2 | D2 `positional_names`, `expand`, `path_values` | F:create `test_each_id_of_the_certificate_path_takes_its_place`; F:tenant_scale `test_each_id_of_a_token_path_takes_its_place`; P `test_each_place_takes_its_own_value`; R `test_each_place_of_a_positional_name_takes_its_own_value` |
| AC-3.3 | D2 `missing_path_parameters`, `check_parameters` | K `test_a_two_value_path_given_one_value_is_refused` |
| AC-4.1 | D3 `OPTIONAL_SUFFIX`, `expand` | F:create `test_the_archive_format_is_sent_as_its_suffix`; R `test_the_suffix_is_written_only_when_given` |
| AC-4.2 | D3 `suffix_values`, `check_parameters` | K `test_a_format_the_page_does_not_list_is_refused`; P `test_only_a_listed_format_reaches_the_path` |
| AC-5.1 | D4 `base_of`, `Transport.request(base=)` | F:software_supply_chain_security `test_the_token_information_is_sent_outside_the_api`; T `test_a_host_request_is_sent_outside_the_api`; R `test_the_base_is_read_from_the_path` |
| AC-5.2 | D4 `container_registry.send`, `container_registry_token`, `container_registry_request` | F:package `test_a_registry_record_is_sent_to_the_registry_with_its_token`; T `test_the_registry_token_is_asked_for_with_basic_credentials`, `test_a_registry_request_carries_only_the_registry_token`; G `test_a_job_token_logs_in_as_gitlab_ci_token`; R `test_send_fetches_the_registry_token_before_the_registry` |
| AC-5.3 | D4 steps 1 to 3 | F:package `test_no_registry_token_sends_nothing_to_the_registry` |
| AC-6.1 | D5; D8 | N `test_every_record_matches_its_reference_section` |
| AC-6.2 | D5 `encode`, `_build_request`, `--header` | F:software_supply_chain_security `test_the_external_control_status_carries_its_headers`; F:openapi_only `test_the_symbol_download_sends_its_checksum_header`; T `test_a_request_header_is_sent_beside_the_transport_headers`; R `test_a_header_param_is_encoded_as_a_header` |
| AC-6.3 | D5 `documented_names` | K `test_an_undeclared_header_is_refused` |
| AC-7.1 | D6 | F:gitlab_dedicated `test_the_s3_import_sends_every_member_at_its_name`; K `test_the_s3_import_is_refused` |
| AC-7.2 | D6; D7 `PARENT_KEY` | N `test_a_two_level_member_is_read_and_sent_as_written` |
| AC-8.1 | D7 | N `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents`, `test_an_endpoint_a_place_a_suffix_and_a_base_are_read_as_written`; N `test_a_two_level_member_is_read_and_sent_as_written` (the S3 record, gate lifted) |
| AC-8.2 | D7 `Section.headers`, `header_problems`, `call_problems` | N `test_a_request_header_is_read_and_sent_as_written` |
| AC-8.3 | D10 | the tests of AC-2.1 to AC-7.1 above, through `main` |
| AC-9.1 | D11 | C `test_the_usage_names_the_request_forms`; K `test_the_call_docstring_names_the_request_forms` |
| AC-9.2 | D11 | N `test_the_map_names_the_request_forms`; `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` |
| UB-1 | D2; D9 | C and every existing test but D9's; R `test_each_place_of_a_positional_name_takes_its_own_value` |
| UB-2 | D4; D5 | P `test_standard_library_only`; K `test_call_takes_no_token_option`; C `test_load_config_refusals`, `test_environment_token_ignored`; T `test_a_registry_request_carries_only_the_registry_token`; F:package's two tests |
| UB-3 | D1, D3, D5 refusals; D6 gate | K's existing and new refusal tests |
| UB-4 | none | `src/payload/test/test_github_api_*.py`; PR diff |

## Residuals

- The `requirements.md` Residuals stand, each a findings-ledger row (D12).
- `token_type` `bearer`: the registry's authentication page lists no OAuth credential (though `lib/gitlab/auth.rb`
  `oauth_access_token_check` accepts an OAuth token as the Basic password under any login), so a container-registry
  call exits 1 unsent (D4) → one ledger row.
- The registry is reached over `https` only; `CI_REGISTRY_IMAGE` is `<host>/<path>` in the CI variables but a
  repository path in the URL and the scope; the delete example's manifest `Accept` is not sent; a job token is
  refused at step 2's `GET /projects/:id` (`conventions.md` "Which endpoints accept a CI/CD job token" lists no
  Projects API endpoint), so a container-registry call under `job` exits 1 (AC-5.3) → one ledger row.
- Steps 1 and 2 accept an answer reached through a cross-origin `GET` redirect; refusing a response whose final URL is
  off the configured origin before step 3 → one ledger row.
