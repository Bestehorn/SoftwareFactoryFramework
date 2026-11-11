# Requirements — issue #46: GitHub `call`: non-JSON request bodies, uploads and the 307 re-send

Tier: M. Kind: FEATURE. Scope: `prompt.md`; the issue's open questions are design choices settled in `design.md`
(DL-001).

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this
   project's open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md`
   exactly."
2. Backlog run: selected issue #46, "GitHub `call`: non-JSON request bodies, uploads and the 307 re-send" (filed from
   #27's DL-002), and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Introduction

`call <operation-id>` (#28, merged at aafecbb) builds a request body only from `-f`/`-F` members:
`commands/call.py` `body_of` joins them into one JSON object, and `registry.send` hands it to `Transport.request`,
which sends it as JSON with `Content-Type: application/json`, only to `API_ROOT`. `RestOperation` carries no host and
no request media type (its `accept` is the response's). `Transport.upload` sends bytes with a given media type to
`UPLOAD_ORIGIN`, but neither a subcommand nor `call` reaches it. `CredentialStrippingRedirectHandler` defers to
`urllib.request.HTTPRedirectHandler.redirect_request`, which raises `HTTPError` for a `307` answering a method other
than `GET` or `HEAD`, so `Transport._send` ends a `307` to a `PATCH` or `DELETE` as a `GitHubAPIError`, exit 1.

Three documented request forms therefore have no call: `rest/releases.md` "Upload a release asset" (host
`https://uploads.github.com`, an `application/octet-stream` body, query `name` and `label`), `rest/markdown.md`
"Render a Markdown document in raw mode" (a `text/plain` or `text/x-markdown` body), and the `307` that `rest/repos.md`
"Update a repository" and "Delete a repository" declare. This change lets `call` send a raw body unchanged with a
documented media type, send the upload to its host with the credential going nowhere else, and re-send a same-origin
`307` once, and it declares the two records #27 (DL-002) and #33 (DL-001) leave pending. Both records live in modules
#27 and #33 change; this branch rebases onto both before its implementation (`prompt.md`).

## Glossary

- **Record**, **pending list** — as in `.claude/specs/issue-28-generic-operation-command/requirements.md`: a
  `registry.RestOperation` of a family module's `OPERATIONS`; its `PENDING`.
- **Section** — a record's operation section of `docs/api-reference/github/rest/<category>.md`.
- **Non-JSON record** — a record whose section has a `Request body (…)` line naming a media type other than
  `application/json`: `repos/upload-release-asset` and `markdown/render-raw`, the only two by `conventions.md`
  "Request encoding".
- **Raw body** — a request body an operation call takes as bytes from the input `design.md` names, rather than from
  `-f`/`-F` members.
- **Origin** — scheme, host and port, as `transport.origin` computes them.
- **Credential** — the `Authorization` header `Transport._build_request` adds.
- **Fake host** — the injected opener the wrapper's tests answer requests with; nothing reaches GitHub.

## Requirements

### Requirement 1 — A raw request body (issue AC-1, AC-4)

As a caller, I want to give `call` a request body as bytes, so that an operation whose body is not a JSON object is
sent as its section documents.

- AC-1.1 `design.md` SHALL record the answer to each of the issue's open questions: the form of the raw body input (a
  file, standard input, or both) and which records accept it, including whether a JSON body may come through it
  (#28 Residuals); whether a record's request media type and host are `RestOperation` fields or call options; and
  whether a `307` whose `Location` is on another origin is refused or re-sent without the credential.
- AC-1.2 WHEN an operation call names a non-JSON record and gives a raw body, the wrapper SHALL send a request whose
  body is exactly the raw body's bytes — none added, removed, re-encoded or reordered — and whose `Content-Type` is a
  media type that a `Request body (…)` line of the section names.
- AC-1.3 WHEN an operation call gives a raw body and one or more `-f`/`-F` members, the wrapper SHALL send no request,
  write a message naming both inputs to standard error, and exit 2 (`EXIT_REFUSED`).

### Requirement 2 — The release-asset upload (issue AC-2)

As a caller publishing a release, I want `call` to upload an asset to the host its section names, so that an upload
needs no compatibility subcommand and the token goes to no host the upload does not need.

- AC-2.1 WHEN an operation call of `repos/upload-release-asset` gives a value for each path parameter, the query
  parameter `name`, optionally `label`, and a raw body, the wrapper SHALL send one `POST` to `https://uploads.github.com`
  followed by the record's path expanded as `registry.expand` encodes it, with `name` and any given `label` as its
  query string.
- AC-2.2 During that call the credential SHALL reach no origin but that of `https://uploads.github.com`: no request it
  sends to `https://api.github.com` or to any other origin SHALL carry `Authorization`.

### Requirement 3 — The same-origin `307` re-send (issue AC-3)

As a caller updating or deleting a repository, I want a `307` that keeps the request on its origin to be followed, so
that `repos/update` and `repos/delete` succeed instead of ending with exit 1.

- AC-3.1 WHEN a `PATCH` or `DELETE` request the wrapper sends is answered `307` with a `Location` that, resolved
  against the request's URL, names a URL on the request's origin, the wrapper SHALL send one request to that URL with
  the same method, body bytes, `Content-Type` and credential, and SHALL treat its answer as the answer to the original
  request (#28 AC-1.5 to AC-1.7).
- AC-3.2 WHEN the request AC-3.1 sends is itself answered `307`, the wrapper SHALL send no further request and SHALL
  end as an HTTP error: `GitHubAPIError`, exit 1 (#28 AC-1.7).

### Requirement 4 — The two pending records (issue AC-5)

As a slice worker, I want the two records the slices left pending declared and proven against a fake host, so that
no family keeps an ID pending for want of a request form.

- AC-4.1 `repos/upload-release-asset` SHALL have one record in `families/repos.py` `OPERATIONS` and
  `markdown/render-raw` one in `families/markdown.py` `OPERATIONS`; neither ID SHALL be on a pending list; each
  record's `method`, `path`, `query_params` and `body_params` SHALL be its section's as
  `test/test_github_wrapper_contract.py` `reference_sections` reads it.
- AC-4.2 A fake-host test SHALL make AC-2.1's operation call with a raw body that is not valid UTF-8 and SHALL assert
  that its one request is a `POST` on the origin of `https://uploads.github.com`, to the expanded path, with the query
  `name` and `label`, `Content-Type: application/octet-stream` and a body equal to the given bytes, and that no
  request carried `Authorization` to another origin.
- AC-4.3 A fake-host test SHALL make an operation call of `markdown/render-raw` with a raw body and SHALL assert that
  its one request is a `POST` to `https://api.github.com/markdown/raw` with the `Content-Type` `design.md` names for
  it (`text/plain` or `text/x-markdown`) and a body equal to the given bytes.

### Requirement 5 — Docs (issue work item "Usage docstring and the project map name the new input")

As an agent calling the wrapper, I want the usage docstring and the project map to name the raw body input, so that
I find it without reading the package.

- AC-5.1 The module docstring of `src/payload/scripts/github_wrapper.py` SHALL name the raw body input with one
  example and its refusal alongside `-f`/`-F` (AC-1.3), and `src/payload/test/test_github_wrapper_compat.py`
  `test_the_usage_names_the_operation_call` SHALL CONTINUE TO pass.
- AC-5.2 `docs/forLLMConsumption.md` SHALL name the raw body input, and `test/test_instruction_corpus_budget.py`
  `test_llm_map_within_cap` SHALL CONTINUE TO pass.

## Unchanged behaviour

- UB-1.1 Every subcommand other than `call`, and an operation call that gives no raw body and names neither record of
  Requirement 4, SHALL CONTINUE TO send the same requests, write the same standard output and return the same exit
  codes, for every answer but AC-3.1's same-origin `307`: `src/payload/test/test_github_wrapper_compat.py` over the
  golden `CASES` of `src/payload/test/github_wrapper_fixtures.py`, `test/test_github_wrapper_fork_parity.py` and
  `src/payload/test/test_github_api_call.py` SHALL CONTINUE TO pass with no existing case or assertion edited.
- UB-2.1 The wrapper's credential SHALL CONTINUE TO come only from `credentials/github-pat.txt` (`_load_token`) —
  never from an environment variable, an argument or another file, the raw body input included; no option takes a
  token.
- UB-2.2 Apart from requests to the origin of `https://uploads.github.com` (AC-2.2's upload, and `Transport.upload`,
  unchanged), the credential SHALL CONTINUE TO be sent only on requests to the origin of `https://api.github.com`
  (`Transport._send`'s `allowed_origin` check); a request that follows a redirect to another origin than the request
  that received it — the `307` of a `PATCH` or `DELETE` included — SHALL CONTINUE TO carry no `Authorization`, on
  every later hop too (`CredentialStrippingRedirectHandler`; `src/payload/test/test_github_api_transport.py`
  `test_a_cross_origin_redirect_drops_the_credential`).
- UB-3.1 The entry script and `src/payload/scripts/github_api/` SHALL CONTINUE TO import only the Python 3.9 standard
  library (`test/test_github_wrapper_coverage.py` `test_the_wrapper_imports_only_the_standard_library`).

## Out of scope

- Other request forms (`prompt.md`): a `307` or `308` of a `POST`, any redirect of a `PUT`, and a `301`, `302`, `303`
  or `308` of a `PATCH` or `DELETE` still end as #28 AC-1.7.
- The GitLab twin (`src/payload/scripts/gitlab_wrapper.py`).
- The real-forge run (#10); promoting the new wrapper over the installed fork.

## Residuals

- The upload's `Content-Type` is its section's `application/octet-stream` (AC-1.2); `conventions.md` "Uploads and
  binary request bodies" names the asset's own media type (`application/zip`), which this change does not send.
- `conventions.md` "Hosts and base URLs" advises the release's `upload_url` over a URL built from parts; AC-2.1 builds
  it from the record's path on the upload origin, as the section documents.
