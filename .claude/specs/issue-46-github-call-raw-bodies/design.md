# Design — issue #46: GitHub `call`: non-JSON request bodies, uploads and the 307 re-send

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1..AC-5.2, UB-1.1..UB-3.1, frozen). Builds on
`.claude/specs/issue-28-generic-operation-command/design.md`, cited as "#28 Dn".

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: selected issue #46, "GitHub `call`: non-JSON request bodies, uploads and the 307 re-send" (filed from
   #27's DL-002), and derived `prompt.md` from the issue body; no interview (see `qa_log.md`).

## Overview

`call` gains `--input FILE` (`-` reads standard input): a raw body, sent unchanged, accepted by a record whose body is
not JSON (D1). `RestOperation` gains `root` and `content_type`, and `registry.send` sends a record that has a
`content_type` through a new `Transport.request_raw` to its `root` (D2). `CredentialStrippingRedirectHandler`
re-sends a same-origin `307` of a `PATCH` or `DELETE` once and refuses one to another origin (D3). The two pending
records are declared (D4). The fixtures compare a raw body as bytes, and the contract test routes each record's call
at its section's host (D5). The usage docstring and the map name the input (D6). Nothing is promoted.

**Order.** #27 has landed on origin/main (PR #47): `families/repos.py` with `repos/upload-release-asset` on
`PENDING`, `commands/call.py` with its branch-writing `GATED_OPERATIONS`, and `src/payload/test/test_github_api_repos.py`.
#33 fills `families/markdown.py`, leaving `markdown/render-raw` on `PENDING`, and adds
`src/payload/test/test_github_api_markdown.py`. This branch rebases onto origin/main, and onto #33 once #33 lands,
before its first wave; every edit below is to those modules as #27 and #33 leave them.

## Design

### D1 — The raw body input (AC-1.1, AC-1.2, AC-1.3)

```
python scripts/github_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
                                      [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]... [--input FILE]
```

- **`--input FILE`**: the request body is the bytes of FILE, or of standard input when FILE is `-`. The spelling is
  `gh api`'s: "The file to use as body for the HTTP request (use "-" to read from standard input)".
  - The option's `type` is `read_input(text) -> bytes`, with dest `raw_body` and default `None`. For `-` it returns
    `sys.stdin.buffer.read()`; this reads the binary buffer, as the Python docs for `sys.stdin` say to do for binary
    data. For any other text it returns `Path(text).read_bytes()`.
  - An `OSError` is raised again as `argparse.ArgumentTypeError` naming the path rendered with `json.dumps`; argparse
    names the option, as it does for `assignment` and `json_member`. That is argparse's usage error, exit 2, before
    the credential is read. argparse catches only `ArgumentTypeError`, `TypeError` and `ValueError` ("Other exception
    types are not handled"), which is why the `OSError` is converted. The read in the `type` is therefore safe:
    `Path.read_bytes` also closes the file before it returns, so none is left open when a later argument fails
    (argparse docs, `type` and `FileType`). `argparse.FileType` is not used: it is deprecated since Python 3.14.
  - No option string contains `token` (UB-2.1).
- **Which records accept it**: exactly the records whose `content_type` is set (D2). Those are the two non-JSON
  records (`conventions.md` "Request encoding": "Only two operations take a non-JSON body").
- **No JSON body through `--input`.** The ask is the three request forms `call` lacks (`prompt.md` Goal). Unless the
  input were parsed and its member names checked, a JSON body read from a file would get past #28 D4's refusal of a
  body name the record does not document. Checking them would add a second body path to every JSON record. #28's
  "Secrets in arguments" residual therefore stays (Residuals).
- **With `-f`/`-F`**: refused, exit 2 (AC-1.3). `gh api` handles this case differently: "When passing the request body
  this way, any parameters specified via field flags are added to the query string of the endpoint URL". Here a query
  parameter is given with `--query`, so a body member beside a raw body has nothing to mean.
- **A non-JSON record without `--input`** sends no body and no `Content-Type` (#28 D2 step 6). Both sections mark the
  body optional: `rest/releases.md` and `rest/markdown.md`, "Request body (…, optional)". Its `body_params` is empty,
  so #28 D4 refuses any `-f`/`-F` name on it.
- **`cmd_call`'s steps** (#28 D2):
  1. A raw body together with one or more members is refused by `refuse_both_bodies`. The message names `--input`,
     `-f/--raw-field` and `-F/--field`.
  2. An ID in `GATED_OPERATIONS` is refused, as in #28.
  3. `registry.lookup(operation_id=...)`, as in #28.
  4. A raw body for a record whose `content_type` is `None` is refused by `refuse_raw_body`. The message names the ID
     and `--input`, and says that its body is given with `-f`/`-F`.
  5. The path values and #28 D4's `check_call`, unchanged.
  6. The query; the body from `body_of(members=...)`; the raw bytes go to `registry.send(..., data=...)`.

  Every refusal is a `ValueError`. It is logged with `logger.error`, which the script's `__main__` writes to standard
  error, and returns `EXIT_REFUSED` with nothing sent, as #28 D4 handles a refusal.
- Alternatives:
  - **A file only.** Rejected: a body made by another command would need a temporary file.
  - **Standard input only.** Rejected: the compatibility commands take a body from a file (`--body-file`), and one
    option with `gh api`'s `-` serves both.
  - **JSON through `--input` as well.** Rejected above.

### D2 — The request media type and host: record fields (AC-1.1, AC-1.2, AC-2.1, AC-2.2)

`RestOperation` gains two fields after `accept`, each with a default. Every existing record, built by keyword, stays
as written.

- `root: str = API_ROOT`: the root the record's path is sent under. It is `UPLOAD_ORIGIN` for
  `repos/upload-release-asset`, whose section reads "Host: `https://uploads.github.com` (not
  `https://api.github.com`)". `conventions.md` "Hosts and base URLs" calls it "the single operation that overrides
  `servers`".
- `content_type: Optional[str] = None`: the media type of a body that is not JSON, chosen from the record's section.
  - `repos/upload-release-asset`: `CONTENT_TYPE_OCTET_STREAM` (`application/octet-stream`).
  - `markdown/render-raw`: `CONTENT_TYPE_TEXT` (`text/plain`), the first of its section's two `Request body` lines.
  - Every other record: `None`, because its body is JSON.
- **`registry.send`** gains `data: Optional[bytes] = None`.
  - A record whose `content_type` is `None` goes through `Transport.request` to `API_ROOT`, as today. A `data` value
    raises `ValueError` before anything is sent. N's routing at the section's host (D5) fails such a record if its
    section names another host.
  - Any other record goes through `Transport.request_raw(method=..., root=operation.root, path=..., query=...,
    data=data, content_type=operation.content_type, api_version=..., accept=...)`.
  - `call` and `pages` are unchanged.
- **`transport.py`**:
  - New constants: `CONTENT_TYPE_OCTET_STREAM`, `CONTENT_TYPE_TEXT`, and `REST_ROOTS = (API_ROOT, UPLOAD_ORIGIN)`.
  - `_api_url` takes `root` (default `API_ROOT`); every existing caller keeps the default.
  - `Transport.request_raw`:
    - It refuses a `root` outside `REST_ROOTS` with `ValueError` before anything is sent.
    - The URL is `_api_url(root=root, path=path, query=query)`, so a path that is not root-relative is refused as
      it is for `request`.
    - `data` is sent unchanged, with `Content-Type: content_type`. When `data` is `None`, no body and no
      `Content-Type` are sent.
    - `Accept` and `X-GitHub-Api-Version` are the record's.
    - The request goes through `_send(..., allowed_origin=root)`, so the credential goes only to that root's origin.
    - urllib sets `Content-Length` from `data`.
- **`Transport.upload`** (the `upload_url` template) is unchanged and not reused.
  - Reuse would mean rebuilding a `{?name,label}` template from the record's parts, the URL built from parts that
    `conventions.md` advises against. `upload` also takes `name` and `label` as arguments rather than the query, and
    fixes `Accept` and the API version.
  - Replacing it would delete T `test_an_asset_is_uploaded_to_the_upload_url` and the upload branch of
    `test_every_rest_request_sends_the_api_version`, a behaviour no criterion removes.
  - It stays the path for a release's `upload_url`. Nothing calls it yet (Residuals).
- Alternatives:
  - **Call options (`--host`, `--content-type`).** Rejected:
    - A host option would let any record's call carry the credential to the upload origin, and AC-2.2 limits that to
      the upload call.
    - N could not prove the host from the section.
    - Choosing a media type per call is #28's requirements residual.
  - **A table in `commands/call.py` beside `GATED_OPERATIONS`.** #28 D8's exceptions row names only `transport.py` and
    `commands/call.py`. Rejected:
    - The host and the media type are facts of the operation, documented in its section as its method and `Accept`
      are, which `RestOperation` already holds.
    - `registry.send` is the library call every caller uses, and with such a table
      `registry.send(operation_id="repos/upload-release-asset", ...)` would still send JSON to `API_ROOT`.
    - `GATED_OPERATIONS` is a policy of the `call` command, not a fact of an operation.

### D3 — The same-origin `307` re-send (AC-1.1, AC-3.1, AC-3.2, UB-2.2)

**Where.** In `CredentialStrippingRedirectHandler.redirect_request`.

- urllib calls it for a `301`, `302`, `303` or `307` (and a `308` from Python 3.11) that carries a `Location`, with
  `newurl` already resolved: the scheme is limited to `http`, `https` and `ftp`, the URL is quoted, and it is joined
  to the request's URL (`urljoin(req.full_url, newurl)`, CPython `HTTPRedirectHandler.http_error_302`). A relative
  `Location` is therefore resolved against the request's URL (AC-3.1).
- urllib's default raises `HTTPError` for a `307` of any method but `GET` or `HEAD` (CPython
  `HTTPRedirectHandler.redirect_request`). `conventions.md` "Downloads and redirects" says the same: "the `307` on
  `PATCH`/`DELETE /repos/{owner}/{repo}` surfaces as an `HTTPError` that the wrapper has to retry against `Location`".

**The branch**, ahead of the deferral to urllib, applies when all of these hold:

- `code` is `STATUS_TEMPORARY_REDIRECT` (`307`);
- `req.get_method()` is in `RESENT_METHODS` (`PATCH`, `DELETE`);
- `req` is not a `ResentRequest`;
- `origin(url=newurl) == origin(url=req.full_url)`.

It then returns `ResentRequest(url=newurl, data=req.data, headers=dict(req.headers), method=req.get_method(),
origin_req_host=req.origin_req_host, unverifiable=True)`. `ResentRequest` is a `urllib.request.Request` subclass with
no members of its own: it marks a request that has already been re-sent.

- **Same method, body bytes, `Content-Type` and credential.**
  - `_build_request` adds every header with `add_header`, so `req.headers` holds `Accept`, `Content-Type`,
    `Authorization`, `User-Agent` and `X-GitHub-Api-Version`.
  - `data` is the same bytes object, and urllib computes `Content-Length` for it again.
  - The answer to the re-sent request is the `Response` that `_open` returns, so `call` prints it (#28 AC-1.5 to
    AC-1.7).
- **Once.**
  - A `ResentRequest` answered by any redirect falls through to the default. For `PATCH` or `DELETE` the default
    raises `HTTPError`, and `_send` turns it into `GitHubAPIError` with status 307, exit 1 (AC-3.2).
  - A rate limit on the re-sent request is waited out by `_send`'s loop. Each retry is a fresh request to the original
    URL (`_build_request`), so each attempt re-sends at most once.
- **Another origin: refused** (AC-1.1's third question).
  - A cross-origin `307` falls through to the default, which raises. Nothing more is sent, and the call exits 1.
  - Re-sending without the credential is rejected. The request would carry its body, a repository's settings, to a
    host the credential does not belong to. It would also act as no user, so the update or deletion could not be the
    token's.
  - `conventions.md` "Hosts and base URLs" names no third REST origin.
- **Every other redirect is unchanged**: urllib's default, then the existing strip (UB-2.2). A `307` or `308` of a
  `POST`, any redirect of a `PUT`, and a `301`, `302`, `303` or `308` of a `PATCH` or `DELETE` still raise
  (requirements Out of scope).
- **Every entry point.** `request`, `request_raw`, `download`, `upload` and `graphql` all send through `_send` on this
  opener. The compatibility subcommands' `PATCH` and `DELETE` requests therefore get the re-send too (DL-002, UB-1.1's
  exception).
- **Python 3.9.** Its docs give `redirect_request(req, fp, code, msg, hdrs, newurl)` and `http_error_307`, the same as
  today's. `http_error_308` is "Added in version 3.11" and is not used.
- Alternative: **in `Transport._send`**, catching the `307` `HTTPError` and re-sending to its `location` header.
  Rejected: it would repeat urllib's resolution of `Location` (scheme check, quoting, `urljoin`) on the raw header, apart
  from the handler that already compares a redirect's two origins.

### D4 — The two records (AC-4.1)

**`repos/upload-release-asset`**, in `families/repos.py` (#27).

- Its place: after `repos/list-release-assets`, following the file's order of sections (`rest/releases.md`, "assets").
- Its fields:
  - method `POST`; path `/repos/{owner}/{repo}/releases/{release_id}/assets`
  - query `name`, `label`; no body names; no `multi_segment`
  - `Paging.NONE`, `item_key` `None`
  - `API_VERSION_DEFAULT`; `ACCEPT_JSON` (its `201` is `application/json` `release-asset`)
  - `root=UPLOAD_ORIGIN`, `content_type=CONTENT_TYPE_OCTET_STREAM`
- `PENDING` becomes empty.
- The docstring's first sentence names every `repos/` ID. Its DL-002 sentence is replaced: the upload goes to
  `UPLOAD_ORIGIN` with its body from `call --input`.

**`markdown/render-raw`**, in `families/markdown.py` (#33).

- Its place: after `markdown/render`.
- Its fields:
  - method `POST`; path `/markdown/raw`
  - no query, no body names, no `multi_segment`
  - `Paging.NONE`, `item_key` `None`
  - `API_VERSION_DEFAULT`; `ACCEPT_JSON`, as #33 AC-3 declares for every record of the family
  - `content_type=CONTENT_TYPE_TEXT`; `root` left at its default
- `PENDING` becomes empty, and the docstring says so.

**The tests that encode the deferral are restated**, because AC-4.1 removes the behaviour they pin:

- G `test_only_the_upload_is_pending` becomes `test_no_repos_id_is_pending`: `PENDING` must be empty, and its
  docstring no longer cites DL-002. G's module docstring drops its "`repos/upload-release-asset` stays pending
  (DL-002)" clause.
- G's `RECORDED_IDS` and its comment ("every `repos/` ID but the one left pending") are removed, and
  `UPLOAD_RELEASE_ASSET`, then unused, with them. Its two uses, in `test_no_repos_id_is_pending` and
  `test_every_record_sends_the_default_version_and_media_type`, read `REPOS_OPERATION_IDS`, and the latter's docstring
  drops "but the pending one".
- M `test_only_the_residual_ids_are_pending` drops `markdown/render-raw` from its residual set, as does any #33 case
  that expects `call markdown/render-raw` refused as undeclared (#33 UB-2).
- No assertion is relaxed, and every other test of G and M passes unedited: the upload's API version and `Accept` are
  G's defaults. G and M are re-read at the rebase onto #33.

`GATED_OPERATIONS` is unchanged: neither record writes a branch (#27's rule).

### D5 — The fake host, the fixtures and the contract test (AC-2.1, AC-4.1 to AC-4.3)

**`FakeGitHub` needs no new route kind.**

- A route named by an absolute URL is on that URL's origin (`_target_of`), so the upload is
  `StaticRouteSpec(method="POST", url="https://uploads.github.com/repos/o/r/releases/3/assets", query=...)`.
- A `307` is `fx.redirect(status=307, location=...)`. The fake's answer passes through urllib's `HTTPErrorProcessor`
  to the transport's own redirect handler, as the existing redirect cases do.

**`NonGetRequest.of`** (`src/payload/test/github_wrapper_fixtures.py`).

- Its `body` is `request.json()` when the recorded `content-type` is absent or `application/json`, and
  `request.body` (bytes) otherwise.
- Without this, a body that is not UTF-8 raises in `RecordedRequest.json` inside `assert_outcome`.
- Every existing row of `CASES` and K sends JSON as `application/json` (the product's `CONTENT_TYPE_JSON`, the fork's
  `CONTENT_TYPE_JSON`) or sends no body, so their comparisons are unchanged.

**N.**

- `ReferenceSection` gains `host: str`, read from the section's ``- Host: `…` `` line, with `https://api.github.com`
  as its default.
- `_plan_call` routes the planned call at `section.host` + `expected.path`. N's every-record test therefore proves
  that each record's call reaches its section's host.
- `READ_SECTIONS` gains the upload's section: host `https://uploads.github.com`, path names `owner`, `repo` and
  `release_id`, query names `name` and `label`, no body names.
- N calls both records without `--input`, so no body is sent and `sent_call` reads none.

### D6 — The usage docstring, the map and the module docstrings (AC-5.1, AC-5.2)

**The usage docstring.** These lines go into the usage list of `src/payload/scripts/github_wrapper.py`, after the
`call issues/get` entry:

```
    python scripts/github_wrapper.py call markdown/render-raw --input README.md   # a body that is not JSON
        # --input FILE (- reads standard input): the request body, its bytes sent unchanged with the record's media
        # type, for repos/upload-release-asset (sent to uploads.github.com) and markdown/render-raw; --input for any
        # other operation, or together with -f/-F, is refused before any request: exit 2.
```

**The map.** In the `src/payload/scripts/github_api/` bullet of `docs/forLLMConsumption.md`, the parenthesis after the
`call issues/get` example becomes: "(`--path`, `--query`, `-f/--raw-field`, `-F/--field`, and `--input FILE` for the
two bodies that are not JSON, `repos/upload-release-asset` and `markdown/render-raw`; a refusal exits 2)".

**The module docstrings.**

- `commands/call.py` states `--input`, its two refusals and step 1's message.
- `registry.py` states the two fields and `send`'s two paths.
- `transport.py` states `request_raw`, `REST_ROOTS` and the `307` re-send.
- None of them contains the words `environ` or `getenv` (UB-2.1's static check reads docstrings too).

### D7 — Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/transport.py` | `CONTENT_TYPE_OCTET_STREAM`, `CONTENT_TYPE_TEXT`, `REST_ROOTS`, `STATUS_TEMPORARY_REDIRECT`, `METHOD_PATCH`, `METHOD_DELETE`, `RESENT_METHODS`; `_api_url` takes `root`; `Transport.request_raw`; `ResentRequest` and the `redirect_request` branch (D3); the module docstring |
| `src/payload/scripts/github_api/registry.py` | `RestOperation.root`, `RestOperation.content_type`; `send` takes `data` (D2); docstrings |
| `src/payload/scripts/github_api/commands/call.py` | `OPTION_INPUT`, `ARG_RAW_BODY`, `METAVAR_FILE`, `STDIN_INPUT` (`-`), `read_input`, `refuse_both_bodies`, `refuse_raw_body`; `cmd_call` steps 1, 4, 6 (D1); the module docstring |
| `src/payload/scripts/github_api/families/repos.py` | the upload record, `PENDING` empty, the docstring (D4) |
| `src/payload/scripts/github_api/families/markdown.py` | the `render-raw` record, `PENDING` empty, the docstring (D4) |
| `src/payload/scripts/github_wrapper.py` | the module docstring only (D6, DL-006) |
| `docs/forLLMConsumption.md` | the `github_api/` bullet (D6) |
| `src/payload/test/github_wrapper_fixtures.py` | `NonGetRequest.of` (D5, DL-006); `CASES` untouched |
| K `src/payload/test/test_github_api_call.py` | new tests (Correctness Properties) |
| R `src/payload/test/test_github_api_registry.py` | adds `test_send_sends_a_raw_record_to_its_origin` |
| T `src/payload/test/test_github_api_transport.py` | adds `test_a_raw_body_is_sent_unchanged_to_its_root`, `test_a_same_origin_307_is_re_sent_once`, `test_a_second_307_ends_as_an_http_error`, `test_a_cross_origin_307_is_not_followed` |
| H `test/test_github_api_call_properties.py` | adds `test_any_bytes_are_sent_as_given` |
| N `test/test_github_wrapper_contract.py` | `ReferenceSection.host`, `_plan_call`'s route, the upload's `READ_SECTIONS` case (D5, DL-006) |
| C `src/payload/test/test_github_wrapper_compat.py` | adds `test_the_usage_names_the_raw_body_input` |
| G `src/payload/test/test_github_api_repos.py` | `test_no_repos_id_is_pending`, `RECORDED_IDS` removed (D4) |
| M `src/payload/test/test_github_api_markdown.py` | the residual set (D4) |
| `docs/findings-ledger.md` | rows for the Residuals routed to the ledger (`memory_compile.py ledger add`) |

### Data flow (the upload)

1. `call repos/upload-release-asset --path release_id=3 --query name=dist.zip --input dist.zip`: argparse reads
   `dist.zip` through `read_input`. `main` loads the credential and the repository.
2. `cmd_call` checks:
   - step 1: no members were given;
   - steps 2 and 3: the ID is not gated, and `registry.lookup` returns the record;
   - step 4: the record has a `content_type`;
   - step 5: `owner` and `repo` come from `origin`, and #28 D4's check passes.
3. `registry.send` calls `request_raw` with `root=UPLOAD_ORIGIN`. `_send` posts the bytes to
   `https://uploads.github.com/repos/o/r/releases/3/assets?name=dist.zip`, with `allowed_origin=UPLOAD_ORIGIN`.
4. The `201` JSON answer prints with `print_json`, and the call exits 0.

### Sources

- `docs/api-reference/github/rest/releases.md` "Upload a release asset"; `rest/markdown.md` "Render a Markdown
  document in raw mode"; `conventions.md` "Hosts and base URLs", "Request encoding", "Uploads and binary request
  bodies", "Downloads and redirects".
- CPython 3.14 `Lib/urllib/request.py`: `HTTPRedirectHandler.redirect_request` and `http_error_302`.
- Python [`urllib.request`](https://docs.python.org/3/library/urllib.request.html) and its
  [3.9 page](https://docs.python.org/3.9/library/urllib.request.html): `redirect_request` ("If a redirection should
  take place, return a new Request"); `http_error_308`, "Added in version 3.11".
- Python [`argparse`](https://docs.python.org/3/library/argparse.html): the caught `type` exceptions; `FileType`
  "Deprecated since version 3.14".
- [`gh api`](https://cli.github.com/manual/gh_api): `--input` and its field flags.

## Testing Strategy

- **Fake host.** `github_wrapper_fixtures.py` (D5).
- **CLI cases.** K's new cases are `GoldenCase` rows, named `issue-46/<criterion>/…`, run with `fx.run_product_case`
  in the fixture project (`origin` `o/r`). They stay outside `CALL_CASES`: `rows_of` keys its rows by #28's criterion
  ids, which #46's repeat.
  - A raw body is judged in bytes, through `NonGetRequest`.
  - Binary output is read with `capsysbinary`.
  - A refusal is judged by `assert_outcome` (which requires no request for exit 2) and by `caplog`.
- **Property.** H's property is in `test/`, which keeps Hypothesis out of the shipped suite (#17 X1). Each example
  installs the fake host in its own `pytest.MonkeyPatch.context()`, because Hypothesis refuses function-scoped
  fixtures in a `@given` signature.
- **Runner.** Locally, `python scripts/run_tests.py <these paths>`. In CI, the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests`.
- **E2E.** No system is deployed; the real-forge check is #10's fixture on an ephemeral `sff-test-*` repository
  (requirements Out of scope). Until then, K and N run `call` through `main` up to the API boundary in CI's `tests`
  leg.

## Correctness Properties

Test files:

- K = `src/payload/test/test_github_api_call.py`
- R = `src/payload/test/test_github_api_registry.py`
- T = `src/payload/test/test_github_api_transport.py`
- H = `test/test_github_api_call_properties.py`
- N = `test/test_github_wrapper_contract.py`
- V = `test/test_github_wrapper_coverage.py`
- C = `src/payload/test/test_github_wrapper_compat.py`
- P = `test/test_github_wrapper_fork_parity.py`
- G = `src/payload/test/test_github_api_repos.py`
- M = `src/payload/test/test_github_api_markdown.py`
- B = `test/test_instruction_corpus_budget.py`

- **AC-1.1**
  - Inspection: D1 (the input, the records that take it, no JSON body), D2 (fields, not options), D3 (another origin
    refused).
  - Example, K `test_a_raw_body_the_call_cannot_send_is_refused`. Each case exits 2 with no request:
    - `call issues/update --path issue_number=5 --input <a file under tmp_path>`, on a JSON record: a log record
      names `issues/update` and `--input`;
    - `call markdown/render-raw --input <a missing file>`: standard error holds `argument --input:` and the missing
      path rendered with `json.dumps`.
  - T `test_a_cross_origin_307_is_not_followed` (UB-2.2) covers the third question.
- **AC-1.2**
  - Property, H `test_any_bytes_are_sent_as_given`. For any `bytes` (`st.binary()`) and each of
    `CONTENT_TYPE_OCTET_STREAM` and `CONTENT_TYPE_TEXT`:
    - the bytes are written to a file in a `tempfile.TemporaryDirectory`, and `read_input(text=<path>)` returns them;
    - `Transport.request_raw(method="POST", root=API_ROOT, path="/markdown/raw", data=..., content_type=...)` records
      one request whose body is those bytes and whose `content-type` is the given type.
  - Examples:
    - R `test_send_sends_a_raw_record_to_its_origin`: a synthetic record with `root=UPLOAD_ORIGIN` and a
      `content_type` sends to the upload origin with the bytes and the type. The same `data` for a record whose
      `content_type` is `None` raises `ValueError`, and no request is sent.
    - T `test_a_raw_body_is_sent_unchanged_to_its_root`, on `API_ROOT` and `UPLOAD_ORIGIN`: the body, `content-type`,
      origin and `authorization` are as given. `data=None` sends no body and no `Content-Type`. A root outside
      `REST_ROOTS` raises `ValueError`, and no request is sent.
    - AC-4.2's and AC-4.3's tests.
- **AC-1.3** — Example, K `test_a_raw_body_with_body_members_is_refused`, parametrized with `-f text=T` and
  `-F text="T"` beside `--input` on `markdown/render-raw`. Oracle: exit 2, no request, and one log record naming
  `--input`, `-f/--raw-field` and `-F/--field`.
- **AC-2.1**
  - K `test_an_asset_is_uploaded_to_its_host` (AC-4.2).
  - N `test_every_record_is_sent_as_its_section_documents` routes the upload at its section's host.
  - N `test_a_section_is_read_as_the_reference_writes_it`, the upload case, pins the host reader.
- **AC-2.2**
  - In K `test_an_asset_is_uploaded_to_its_host`, every recorded request carrying `authorization` is on the origin of
    `https://uploads.github.com`.
  - T `test_a_raw_body_is_sent_unchanged_to_its_root` refuses a third root.
- **AC-3.1**
  - T `test_a_same_origin_307_is_re_sent_once` has four cases:
    - a `PATCH` with a JSON body, `Location` `https://api.github.com/repositories/42`;
    - the same `PATCH` with the relative `Location` `/repositories/42`;
    - a `PATCH` with `Location` `https://api.github.com:443/repositories/42`, the default port;
    - a `DELETE` with no body, whose second answer is `204`.

    Oracle: exactly two requests. The second has the first's method, body bytes, `content-type` and `authorization`,
    and its URL is the resolved `Location`. The `Response` is the second answer's.
  - K `test_a_repository_update_follows_its_307`: `call repos/update --raw-field description=d`, answered `307` and
    then `200`, prints the second answer's JSON and exits 0. Its writes are two `PATCH` requests with the same body.
- **AC-3.2** — T `test_a_second_307_ends_as_an_http_error`, for `PATCH` and `DELETE`. Both requests are answered
  `307`. Oracle: `GitHubAPIError` with status 307, and exactly two requests.
- **AC-4.1**
  - N `test_every_record_matches_its_reference_section` and `test_every_record_is_sent_as_its_section_documents`.
  - V `test_every_operation_is_covered_or_pending` and `test_one_module_per_family_holding_only_its_own_ids`.
  - G `test_no_repos_id_is_pending`, and M `test_only_the_residual_ids_are_pending` as restated (D4).
- **AC-4.2** — Example, K `test_an_asset_is_uploaded_to_its_host`.
  - Before the run, bytes that are not valid UTF-8 are written under `tmp_path`.
  - The argv is `call repos/upload-release-asset --path release_id=3 --query name=dist.zip --query label=Build
    --input <that path>`.
  - The route is the upload's `StaticRouteSpec` (D5), answering `201` JSON.
  - Oracle:
    - exit 0, and stdout is `printed_json` of the answer;
    - the writes are the one `POST` to `/repos/o/r/releases/3/assets`, with query `name` and `label`, whose body is
      the bytes;
    - that request is on the upload origin, with `content-type` `application/octet-stream` and `authorization` set;
    - no request is on another origin.
- **AC-4.3** — Example with `capsysbinary`, K `test_a_raw_markdown_document_is_rendered`.
  - The argv is `call markdown/render-raw --input -`. `sys.stdin` is monkeypatched to
    `io.TextIOWrapper(io.BytesIO(<the Markdown bytes>))`, the bytes holding a `\r\n` line ending and the byte `\xff`,
    which a read through the text layer translates or fails to decode.
  - The route `POST /markdown/raw` answers HTML bytes.
  - Oracle: exit 0; one request to `https://api.github.com/markdown/raw`, with `content-type` `text/plain` and a body
    equal to the bytes; stdout equal to the HTML bytes.
- **AC-5.1**
  - C `test_the_usage_names_the_operation_call` passes unchanged.
  - C `test_the_usage_names_the_raw_body_input`: the entry script's `__doc__` holds `call markdown/render-raw --input`,
    `--input FILE`, `standard input`, `repos/upload-release-asset`, `uploads.github.com` and `with -f/-F`.
- **AC-5.2** — Inspection of the map's text (D6), and B `test_llm_map_within_cap`.
- **UB-1.1**
  - C `test_a_subcommand_matches_its_golden_case`, P `test_the_fork_produces_the_golden_case`,
    `test_the_parsers_match_option_by_option`, and K's existing tests all pass.
  - PR diff: no existing line of `CASES`, C, P or K is edited.
  - `NonGetRequest.of` gives `request.json()` for every existing row (D5).
- **UB-2.1** — C `test_the_credential_comes_only_from_the_file`, unchanged, scans `commands/call.py` and its options,
  `--input` included.
- **UB-2.2**
  - T `test_a_cross_origin_redirect_drops_the_credential` passes unchanged.
  - T `test_a_cross_origin_307_is_not_followed`: a `PATCH` answered `307` with a `Location` on any of
    `https://api.github.com.example.net/…`, `http://api.github.com/…`, `https://api.github.com:8443/…` or
    `https://uploads.github.com/…`. Oracle: `GitHubAPIError` with status 307, and the host received only the
    original request.
- **UB-3.1** — V `test_the_wrapper_imports_only_the_standard_library`, unchanged.

## Security Considerations

- **Credential.**
  - The source is unchanged (`_load_token`), and no option takes a token.
  - The credential goes to `API_ROOT` for every record but the upload, and to `UPLOAD_ORIGIN` for the upload. Each
    record fixes its own `root` in code; no call option sets it.
  - `request_raw` refuses any root outside `REST_ROOTS`, and `_send`'s origin check is unchanged.
- **Redirects.**
  - A `307` is re-sent only on its own origin, and only once. A `307` to another origin sends nothing further.
  - Every other redirect keeps urllib's handling and the existing strip, so the credential reaches no third host.
- **Input.**
  - `--input` sends whatever the named file or standard input holds, unchanged, to the record's GitHub origin.
  - None of it is logged. argparse's error names only the path, rendered with `json.dumps`.
  - The body is held in memory whole, read when the arguments are parsed, so a call that steps 1 or 4 refuse has
    already read all of it; none of it is sent.
  - A caller who names `credentials/github-pat.txt` sends the token to GitHub as a body: the upload publishes it as a
    release asset, and `render-raw` prints it back on standard output. That is the same exposure as `--body-file` on
    `comment-issue`, which publishes it as a comment (Residuals).
- **Response bytes.** `render-raw`'s HTML reaches stdout unchanged (#28 D3, Security).
- **Gates.** Neither record writes a branch, and the hooks are unchanged. Publishing a release asset is outward-facing,
  so whether to make that call is the caller's decision (#28 "Destructive operations").
- **Dependencies.** None new: `urllib.request.Request` is subclassed. Hypothesis runs only in `test/`.

## Operability

Not applicable. Nothing deploys, and a session gets the product wrapper only through a release and its promotion.

## Residuals

- #28's "Secrets in arguments" stays: `--input` carries no JSON body (D1), so a secret body value still shows on the
  command line. The fix needs #28 D4's name check over a parsed input.
- The upload sends `application/octet-stream`, not the asset's own media type, and builds its URL from the record
  rather than from `upload_url` (requirements Residuals). `Transport.upload`, the `upload_url` path, has no caller.
- `markdown/render-raw` always sends `text/plain`. Choosing `text/x-markdown`, or any media type per call, is #28's
  requirements residual.
- GHES upload hosts (`https://HOST/api/uploads`) are outside `REST_ROOTS`, which holds github.com's roots only
  (`conventions.md` "Hosts and base URLs").
- No guard refuses an `--input` path that names `credentials/github-pat.txt` (Security Considerations, "Input").
- The same-origin `307` re-send is not logged, and a `307` that ends a call names only the original URL.
