# Test architect — design review, iteration 02 (delta, issue #13, tier M)

Fix sites from iteration 01:
- B1 is closed by X1. The properties and the import scan are now in `test/test_gitlab_api_properties.py` (P in the Mapping). `.github/workflows/ci.yml` runs Python 3.10 (`setup-python`). `pyproject.toml` lists `hypothesis` in `[project.optional-dependencies] dev` and has `test` in `testpaths`. The Testing Strategy keeps `src/payload/test/` pytest-only and 3.9-compatible.
- B2 is closed. The oracle was measured in the venv: `urlencode(pairs, safe="[]", quote_via=quote)` followed by `parse_qsl(..., keep_blank_values=True)` round-trips `""`, `a+b c`, `[x]`, `a&b=c`, `%41`, `;`, `\x00`, `\r\n`, `é` and `k[]=z`. The hash form round-trips too. For AC-2.2, `quote(v, safe="")`/`unquote` round-trips `/`, `%2F`, control characters and non-ASCII. Hypothesis 6.170.15 accepts `st.characters(blacklist_categories=("Cs",))` and emits no warning.
- B3 is closed. Each `/` and `|` form and each optional flag now has its own case, with the exact requests, output and exit code. Both `issue start` refusals have no PUT, and the delivery verb through `main` returns 4 with its arguments unparsed.
- C1 to C7 are applied in the Testing Strategy and Correctness Properties (AC-2.4, AC-2.5, AC-3.1, AC-3.3, AC-3.5, AC-4.3, UB-1 subprocess).

New tests from the rewrite:
- The AC-1.1 registry refusals, the AC-2.2 empty, `.` and `..` refusals, AC-2.6's refusal of a next URL on another origin, AC-3.1's four hostile targets per token type plus the return hop, AC-4.3's `errors: []` and `ciConfig` cases, the UB-1 setup-prompts pin and UB-2's trailing-newline token can each fail on a wrong implementation.
- `test_wrapper_delivery.py` `load` reads `src/payload/scripts/gitlab_wrapper.py` in place. D3's bootstrap therefore finds `gitlab_api/` beside it, and the file can stay unchanged (UB-1, UB-3).
- `test/test_layout.py` `FRAMEWORK_PATH` checks `src/payload/...` and not `scripts/...`, and `HISTORICAL` skips `.claude/specs/`. So the new prompt text resolves once the package exists.
- Skeleton `pipeline_wait` loops `while monotonic() < deadline`. So `--timeout-seconds 0` returns 11 with no request, and the fake fails on none.

No A or B finding.

### C1 — AC-2.3 dict clause does not restate the blank-keeping parse
Severity: C
Location: design.md § Correctness Properties AC-2.3
Defect: `keep_blank_values=True` is written in the list clause only. The dict clause says "the `k[key]` pairs", and the dict strategy generates `""` values, which a plain `parse_qsl` drops.
Proposed-edit: replace "for any dict of identifier keys, the `k[key]` pairs equal the dict" with "for any dict of identifier keys, the `k[key]` pairs of the same `parse_qsl(query, keep_blank_values=True)` equal the dict".

### C2 — The synthetic-package discovery test has no named seam past the cache
Severity: C
Location: design.md § D2 "Discovery, not a list"; § Correctness Properties AC-1.2
Defect: `discover_families()` takes no package and caches its result. Its synthetic test therefore depends on whether the real-index test filled the cache first in the same xdist worker.
Proposed-edit: after "and caches the result" add "(the AC-1.2 test points `gitlab_api.families.__path__` at its `tmp_path` package with `monkeypatch`, removes the `gitlab_api.families.*` entries from `sys.modules`, and clears the cache before and after)".

### C3 — The fake's unscripted-request failure must not be an `OSError`
Severity: C
Location: design.md § Testing Strategy "Fake host"
Defect: `_send` turns `OSError` (`URLError`) into `GitLabAPIError` with status 0. If the fake failed by raising one, an oracle written as `pytest.raises(GitLabAPIError)` would accept an extra request.
Proposed-edit: replace "and an unscripted request fails the test" with "and an unscripted request is recorded and then raises `AssertionError` (not an `OSError`, which `_send` converts)".

### C4 — The properties module's import path is not stated
Severity: C
Location: design.md § Testing Strategy "Framework tests"
Defect: `pyproject.toml` `addopts` sets `--import-mode=importlib`, so pytest puts no test directory on `sys.path`. D8 adds `src/payload/scripts` for V and the Testing Strategy does the same for T, but nothing does it for P. P's `gitlab_api` import would then pass or fail depending on which module a worker imported first.
Proposed-edit: after "`test_gitlab_api_properties.py`" add "(which puts `src/payload/scripts` on `sys.path` as D8 does)".

### C5 — The UB-2 import scan can pass over zero files
Severity: C
Location: design.md § Correctness Properties UB-2 "Static"
Defect: "every import ... is stdlib" is vacuously true when the scan's file set is mis-rooted and empty.
Proposed-edit: after "neither contains `os.environ` or `getenv`" add "; the scanned set includes `gitlab_wrapper.py`, `gitlab_api/transport.py` and `gitlab_api/registry.py`".

### D1 — AC-3.5 OAuth substring carries a typographic ellipsis
Severity: D
Location: design.md § Correctness Properties AC-3.5
Defect: The design writes `insufficient_scope: …` with a typographic ellipsis, but the `conventions.md` "Body shapes" sample is `"error_description": "..."`. A test that asserts the design's text literally would fail on a correct message.
Proposed-edit: replace "`insufficient_scope: …`" with "`insufficient_scope: ` followed by the fixture's `error_description`".

## Coverage

The test-file letters T, C, V, P, S and D are those of the design's Mapping.

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | review of D1; T `test_call_refuses_an_undeclared_value`, `test_lookup_refuses_unknown_and_duplicate_ids` | OK |
| AC-1.2 | V `test_a_family_module_is_discovered_alone` (C2) | OK |
| AC-1.3 | review of the D2 table | OK |
| AC-2.1 | T `test_one_credential_header_per_token_type` | OK |
| AC-2.2 | P `test_path_value_is_one_segment`; T `test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused` | OK |
| AC-2.3 | P `test_array_and_hash_pairs` (C1); T `test_array_of_hashes_pairs`, `test_json_body_is_native` | OK |
| AC-2.4 | T `test_file_value_sends_multipart` | OK |
| AC-2.5 | T `test_offset_paging_follows_next_and_ignores_total_pages` | OK |
| AC-2.6 | T `test_keyset_paging_follows_link_unchanged`, `test_next_url_on_another_origin_is_refused` | OK |
| AC-3.1 | T `test_cross_origin_redirect_drops_credentials`, `test_same_origin_redirect_keeps_credential`, `test_credential_stays_dropped_on_return_hop` | OK |
| AC-3.2 | T `test_429_waits_retry_after` | OK |
| AC-3.3 | T `test_429_without_headers_backs_off_increasingly` | OK |
| AC-3.4 | T `test_429_after_retries_raises` | OK |
| AC-3.5 | T `test_error_shape_raises_gitlab_api_error` (D1) | OK |
| AC-4.1 | T `test_graphql_posts_to_api_graphql` | OK |
| AC-4.2 | T `test_graphql_pages_by_end_cursor` | OK |
| AC-4.3 | T `test_graphql_errors_at_200_raise`, `test_empty_payload_errors_and_query_errors_fields_return_data` | OK |
| AC-5.1 | V `test_checker_names_each_unlisted_row` | OK |
| AC-5.2 | V `test_a_family_module_is_discovered_alone` | OK |
| AC-5.3 | V `test_every_index_row_is_mapped_or_pending` | OK |
| AC-5.4 | V same test with the socket guard | OK |
| UB-1 | C `test_a_subcommand_form` and seven named tests; S `test_both_prompts_copy_the_package_with_the_entry`; D unchanged | OK |
| UB-2 | C `test_template_config_sends_private_token`, `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` (C5) | OK |
| UB-3 | verifier evidence from `git diff --name-only` | OK |

Verdict: TEST-READY — CLEAN (0 A, 0 B); 24 OK, 0 GAP.
