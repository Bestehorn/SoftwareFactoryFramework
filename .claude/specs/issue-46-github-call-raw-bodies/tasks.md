# Tasks — issue #46: GitHub `call`: non-JSON request bodies, uploads and the 307 re-send

Tier: M. Derived from `requirements.md` (frozen) and `design.md` (approved, DL-008); nothing is added. Test files as
design § Correctness Properties: K = `src/payload/test/test_github_api_call.py`, R =
`src/payload/test/test_github_api_registry.py`, T = `src/payload/test/test_github_api_transport.py`, H =
`test/test_github_api_call_properties.py`, N = `test/test_github_wrapper_contract.py`, V =
`test/test_github_wrapper_coverage.py`, C = `src/payload/test/test_github_wrapper_compat.py`, P =
`test/test_github_wrapper_fork_parity.py`, G = `src/payload/test/test_github_api_repos.py`, M =
`src/payload/test/test_github_api_markdown.py`, B = `test/test_instruction_corpus_budget.py`; fx =
`src/payload/test/github_wrapper_fixtures.py`. Each test does what design § Correctness Properties states for its
criterion, with its cases, against that oracle. In a wave the TEST tasks run first and add failing tests only, but for
a test its task names green by design, red for the right reason — an assertion, or an exception raised inside the test
body (an `AttributeError` or `TypeError` on what is not yet written), never a collection error: a test names a product
name this change adds (`request_raw`, `REST_ROOTS`, the record fields `root` and `content_type`, `read_input`) only
inside its body, never at module level or in a `parametrize` argument, and its expected values (`307`, the media
types, the origins) are its own constants. K's new cases are `GoldenCase` rows named `issue-46/<criterion>/…`, run
with `fx.run_product_case` and kept outside `CALL_CASES`. The IMPL tasks then add the minimal code that turns them
green. No task edits an existing line of C, of P, of K or of fx's `CASES` (UB-1.1); G and M are restated only as D4
states.

## Preconditions (the conductor's; no files)

- Before wave 1: the branch is rebased onto origin/main, which holds #27 (PR #47): `families/repos.py` with
  `repos/upload-release-asset` on `PENDING`, `commands/call.py`'s branch-writing `GATED_OPERATIONS`, and G.
- Before wave 4: #33 has landed and the branch is rebased onto origin/main again, so `families/markdown.py` and M are
  as #33 leaves them; G and M are re-read then (D4). #33 also edits `commands/call.py` and N, which 2.5 and 2.4 edit:
  the rebase keeps #33's `GATED_OPERATIONS` entries, its module-docstring clause and N's step 3 alongside this
  branch's edits. Waves 1 to 3 touch neither `markdown.py` nor M.

## Wave 1 — Transport, registry and the `307` re-send

Run: `python scripts/run_tests.py src/payload/test/test_github_*.py test/test_github_*.py`

- [ ] 1.1 TEST: T — `test_a_raw_body_is_sent_unchanged_to_its_root` (on `API_ROOT` and `UPLOAD_ORIGIN`: body,
  `content-type`, origin and `authorization` as given; `data=None` sends no body and no `Content-Type`; a root outside
  `REST_ROOTS` raises `ValueError` with no request), `test_a_same_origin_307_is_re_sent_once` (its four cases),
  `test_a_second_307_ends_as_an_http_error` (`PATCH` and `DELETE`), and
  `test_a_cross_origin_307_is_not_followed` (its four `Location` origins), which is green before 1.5 by design and
  whose mutant for the verifier is 1.5's branch without its origin comparison. Existing T tests unedited. — Files:
  src/payload/test/test_github_api_transport.py — Validates: AC-1.1, AC-1.2, AC-2.2, AC-3.1, AC-3.2, UB-2.2
- [ ] 1.2 TEST: R — `test_send_sends_a_raw_record_to_its_origin`: a synthetic record, built inside the test with
  `root=UPLOAD_ORIGIN` and a `content_type`, sent by `registry.send(..., data=...)`, reaches the upload origin with the
  bytes and the type; the same `data` for a record whose `content_type` is `None` raises `ValueError` with no request.
  — Files: src/payload/test/test_github_api_registry.py — Validates: AC-1.2
- [ ] 1.3 TEST: K — `test_a_repository_update_follows_its_307`: `call repos/update --raw-field description=d`,
  answered `307` (`Location` `/repositories/42`) and then `200`, prints the second answer's JSON and exits 0; its
  writes are two `PATCH` requests with the same body. — Files: src/payload/test/test_github_api_call.py — Validates:
  AC-3.1
- [ ] 1.4 TEST (fixtures; adds no test): fx `NonGetRequest.of` per D5 — its `body` is `request.json()` when the
  recorded `content-type` is absent or `application/json`, and `request.body` otherwise; `CASES` untouched. — Files:
  src/payload/test/github_wrapper_fixtures.py — Validates: UB-1.1 (C, P and K on this Run line)
- [ ] 1.5 IMPL: D2's and D3's transport — `CONTENT_TYPE_OCTET_STREAM`, `CONTENT_TYPE_TEXT`, `REST_ROOTS`,
  `STATUS_TEMPORARY_REDIRECT`, `METHOD_PATCH`, `METHOD_DELETE`, `RESENT_METHODS`; `_api_url` takes `root` (default
  `API_ROOT`); `Transport.request_raw` (a root outside `REST_ROOTS` refused before anything is sent, the URL from
  `_api_url(root=...)`, `_send(..., allowed_origin=root)`); `ResentRequest` and the `redirect_request` branch on D3's
  four conditions, ahead of the deferral to urllib; `Transport.upload` unchanged — and D2's registry:
  `RestOperation.root: str = API_ROOT` and `content_type: Optional[str] = None` after `accept`, and `send` taking
  `data: Optional[bytes] = None` with D2's two paths; `call` and `pages` unchanged. Module docstrings per D6, neither
  containing `environ` or `getenv`. Standard library only. — Files: src/payload/scripts/github_api/transport.py,
  src/payload/scripts/github_api/registry.py — Validates: AC-1.2, AC-2.2, AC-3.1, AC-3.2, UB-2.2, UB-3.1

## Wave 2 — `call --input` and the upload record

Run: `python scripts/run_tests.py src/payload/test/test_github_*.py test/test_github_*.py`

- [ ] 2.1 TEST: K — `test_a_raw_body_the_call_cannot_send_is_refused` (`--input` on `issues/update`, a log record
  naming the ID and `--input`; a missing file on `markdown/render-raw`, standard error holding `argument --input:` and
  the path rendered with `json.dumps`), `test_a_raw_body_with_body_members_is_refused` (`-f text=T` and `-F text="T"`
  beside `--input <a file under tmp_path>` on `markdown/render-raw`; one log record naming `--input`, `-f/--raw-field`
  and `-F/--field`), each refusal exiting 2 with no request, and `test_an_asset_is_uploaded_to_its_host` (AC-4.2's argv
  over bytes that are not valid UTF-8 written under `tmp_path`, the upload's absolute-URL `StaticRouteSpec` answering
  `201` JSON). — Files: src/payload/test/test_github_api_call.py — Validates: AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2,
  AC-4.2
- [ ] 2.2 TEST: H — `test_any_bytes_are_sent_as_given`, AC-1.2's property over `st.binary()` and each of the two
  media types: the bytes, written to a file in a `tempfile.TemporaryDirectory`, come back from
  `read_input(text=<path>)`, and `Transport.request_raw(method="POST", root=API_ROOT, path="/markdown/raw", …)` on the
  fake host (fx loaded by path as N loads it, installed in a `pytest.MonkeyPatch.context()` per example) records one
  request with those bytes and that `content-type`. It imports `commands/call.py` inside the test as the existing
  property does; the module docstring names both properties; the existing property unedited. — Files:
  test/test_github_api_call_properties.py — Validates: AC-1.2
- [ ] 2.3 TEST: G per D4 — `test_only_the_upload_is_pending` becomes `test_no_repos_id_is_pending` (`PENDING` empty,
  no DL-002 in its docstring); `RECORDED_IDS`, its comment and `UPLOAD_RELEASE_ASSET` removed, both uses reading
  `REPOS_OPERATION_IDS`; the module docstring's DL-002 clause and the "but the pending one" of
  `test_every_record_sends_the_default_version_and_media_type`'s docstring dropped. No assertion relaxed; G's other
  tests unedited. — Files: src/payload/test/test_github_api_repos.py — Validates: AC-4.1
- [ ] 2.4 TEST: N per D5 — `ReferenceSection.host` (default `https://api.github.com`), read from a section's
  ``- Host: `…` `` line; `_plan_call` routing at `section.host` + `expected.path`; `READ_SECTIONS` gaining the upload's
  section (host `https://uploads.github.com`, path names `owner`, `repo`, `release_id`, query names `name`, `label`, no
  body names); `test_a_section_is_read_as_the_reference_writes_it`'s docstring drops "five". Green before 2.6 by
  design; its mutant for the verifier is N's reader leaving `host` at its default, under which that test's upload case
  fails on its assertion. After 2.6, `test_every_record_is_sent_as_its_section_documents` calls the upload, without
  `--input`, at its section's host. — Files: test/test_github_wrapper_contract.py — Validates: AC-2.1, AC-4.1
- [ ] 2.5 IMPL: `commands/call.py` per D1 and D6 — `OPTION_INPUT`, `ARG_RAW_BODY`, `METAVAR_FILE`, `STDIN_INPUT`;
  `--input` with `read_input` as its argparse `type` (dest `raw_body`, default `None`; `-` reads
  `sys.stdin.buffer.read()`, any other text `Path(text).read_bytes()`; an `OSError` raised again as
  `ArgumentTypeError` naming only the path, rendered with `json.dumps`); `refuse_both_bodies` and `refuse_raw_body`;
  `cmd_call` steps 1, 4 and 6, each refusal a `ValueError` logged with `logger.error` and returned as `EXIT_REFUSED`
  with nothing sent; `GATED_OPERATIONS` unchanged; the module docstring. No option string contains `token`; no text
  `environ` or `getenv`; standard library only. — Files: src/payload/scripts/github_api/commands/call.py — Validates:
  AC-1.1, AC-1.2, AC-1.3, AC-2.1, UB-2.1, UB-3.1
- [ ] 2.6 IMPL: `families/repos.py` per D4 — the `repos/upload-release-asset` record after `repos/list-release-assets`
  with D4's fields (`root=UPLOAD_ORIGIN`, `content_type=CONTENT_TYPE_OCTET_STREAM`); `PENDING` empty; the docstring's
  first sentence naming every `repos/` ID, and its DL-002 sentence replaced. — Files:
  src/payload/scripts/github_api/families/repos.py — Validates: AC-2.1, AC-4.1

## Wave 3 — Usage docstring and map

Run: `python scripts/run_tests.py src/payload/test/test_github_wrapper_compat.py src/payload/test/test_github_api_call.py test/test_github_wrapper_fork_parity.py test/test_github_wrapper_coverage.py test/test_instruction_corpus_budget.py`

- [ ] 3.1 TEST: C — `test_the_usage_names_the_raw_body_input`: the entry script's `__doc__` holds
  `call markdown/render-raw --input`, `--input FILE`, `standard input`, `repos/upload-release-asset`,
  `uploads.github.com` and `with -f/-F`. — Files: src/payload/test/test_github_wrapper_compat.py — Validates: AC-5.1
- [ ] 3.2 IMPL: the entry script's module docstring only — D6's lines after the `call issues/get` entry. — Files:
  src/payload/scripts/github_wrapper.py — Validates: AC-5.1
- [ ] 3.3 IMPL: the map's `src/payload/scripts/github_api/` bullet — the parenthesis after the `call issues/get`
  example becomes D6's; the map under its cap. — Files: docs/forLLMConsumption.md — Validates: AC-5.2

## Wave 4 — The raw Markdown record (after #33)

Run: `python scripts/run_tests.py src/payload/test/test_github_*.py test/test_github_*.py`

- [ ] 4.1 TEST: K — `test_a_raw_markdown_document_is_rendered`, with `capsysbinary`: `call markdown/render-raw
  --input -` with `sys.stdin` monkeypatched to `io.TextIOWrapper(io.BytesIO(…))` over Markdown bytes holding a `\r\n`
  line ending and the byte `\xff`, the route `POST /markdown/raw` answering HTML bytes. — Files:
  src/payload/test/test_github_api_call.py — Validates: AC-1.2, AC-4.3
- [ ] 4.2 TEST: M per D4 — `test_only_the_residual_ids_are_pending` drops `markdown/render-raw` from its residual set,
  as does any #33 case that expects `call markdown/render-raw` refused as undeclared; its docstring,
  `RESIDUAL_PENDING`'s comment and the module docstring's `RESIDUAL_PENDING` bullet no longer say it is pending nor
  `markdown/render` the one record; no assertion relaxed, M's other tests unedited. — Files:
  src/payload/test/test_github_api_markdown.py — Validates: AC-4.1
- [ ] 4.3 IMPL: `families/markdown.py` per D4 — the `markdown/render-raw` record after `markdown/render` with D4's
  fields (`content_type=CONTENT_TYPE_TEXT`, `root` at its default); `PENDING` empty, and the docstring names both
  records and says `PENDING` is empty. — Files: src/payload/scripts/github_api/families/markdown.py — Validates:
  AC-1.2, AC-4.1

## Final

- [ ] F.1 E2E: no system is deployed; the real-forge check is #10's fixture on an ephemeral `sff-test-*` repository
  (requirements § Out of scope). Until it exists, K and N run `call` through `main`'s argv up to the API boundary, and
  C `test_the_script_runs_by_path` (unchanged) runs the script by path; these suites run in the `verify` job of
  `.github/workflows/ci.yml`, matrix leg `tests` (`python scripts/run_checks.py --group tests`). — Files: none
- [ ] F.2 VERIFY: the branch's diff from its merge base (`git diff origin/main...HEAD`) changes no existing line of C,
  of P, of K or of fx's `CASES`, and C gains only `test_the_usage_names_the_raw_body_input`. Unchanged, C
  `test_a_subcommand_matches_its_golden_case` and `test_the_credential_comes_only_from_the_file`, P, and V
  `test_the_wrapper_imports_only_the_standard_library` pass in the run of every wave, and T
  `test_a_cross_origin_redirect_drops_the_credential` and `test_an_asset_is_uploaded_to_the_upload_url` in the run of
  wave 1. — Files: none (read-only) — Validates: UB-1.1, UB-2.1, UB-2.2, UB-3.1
- [ ] F.3 VERIFY: the map's `github_api/` bullet holds D6's parenthesis, and B `test_llm_map_within_cap` passes in the
  run of wave 3. — Files: none (read-only) — Validates: AC-5.2
## Coverage

| Criterion | TEST / VERIFY tasks |
|---|---|
| AC-1.1 | 1.1, 2.1; design D1 to D3 (approved, DL-008) |
| AC-1.2 | 1.1, 1.2, 2.1, 2.2, 4.1 |
| AC-1.3 | 2.1 |
| AC-2.1 | 2.1, 2.4 |
| AC-2.2 | 1.1, 2.1 |
| AC-3.1 | 1.1, 1.3 |
| AC-3.2 | 1.1 |
| AC-4.1 | 2.3, 2.4, 4.2; N and V, unchanged tests included, on the Run lines of waves 2 and 4 |
| AC-4.2 | 2.1 |
| AC-4.3 | 4.1 |
| AC-5.1 | 3.1; C `test_the_usage_names_the_operation_call`, unchanged, on the Run line of wave 3 |
| AC-5.2 | F.3 |
| UB-1.1 | 1.4, F.2; C, P and K on every Run line |
| UB-2.1 | F.2; C on every Run line |
| UB-2.2 | 1.1, F.2 |
| UB-3.1 | F.2; V on every Run line |
