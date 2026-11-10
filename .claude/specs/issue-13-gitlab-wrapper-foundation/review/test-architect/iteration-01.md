# Test architect — design review, iteration 01 (issue #13, tier M)

### B1 — The shipped transport suite imports Hypothesis and a 3.10-only API
Severity: B
Location: design.md § Testing Strategy (Transport and records); § Correctness Properties AC-2.2, AC-2.3, UB-2; § Acceptance Criteria Mapping
Defect: The AC-2.2/AC-2.3 properties (Hypothesis) and `test_standard_library_only` (`sys.stdlib_module_names`, 3.10+) are placed in `src/payload/test/test_gitlab_transport.py`. That suite ships to projects (design Residuals "the new suites"; the `test_wrapper_delivery.py` docstring says "Installed from src/payload/test/"). Shipped suites may need only pytest and must run on 3.9, and the design does not flag the new dependency.
Material-because: unmaintainable-by-rule `dependencies.md` rule 1 / `tech-stack.md`. A project without Hypothesis, or on Python 3.9, would get a red suite from the installed file.
Proposed-edit: Testing Strategy, replace "Hypothesis for AC-2.2 and AC-2.3." with "The AC-2.2 and AC-2.3 properties and the UB-2 import scan live in `test/test_gitlab_transport_properties.py` (framework test, not shipped: Hypothesis is this repository's dev dependency, CI runs 3.10); `src/payload/test/` stays pytest-only and 3.9-compatible." Add that file to the Layout block. In the Mapping, move `test_path_value_is_one_segment`, `test_array_and_hash_pairs` and `test_standard_library_only` to it.

### B2 — The AC-2.3 property oracle rejects a correct encoder
Severity: B
Location: design.md § Correctness Properties AC-2.3
Defect: The oracle compares the input with `parse_qsl` of the encoded query, but `parse_qsl` drops blank values by default. Measured in the venv: `parse_qsl("k[]=&k[]=a%2Bb%20c")` returns `[('k[]', 'a+b c')]`. The list and dict strategies generate `""`, so the property fails against an encoder that is right.
Material-because: AC-2.3. Its only quantified test cannot pass on a correct implementation, so the criterion has no valid oracle, and the failing test pushes toward an encoder that drops empty values.
Proposed-edit: in AC-2.3, replace "`parse_qsl` of the encoded query" with "`parse_qsl(query, keep_blank_values=True)` of the encoded query" (for both the list property and the dict property).

### B3 — UB-1 pins one argv per handler row, so caller-used † forms go untested
Severity: B
Location: design.md § Correctness Properties UB-1; § Acceptance Criteria Mapping UB-1
Defect: "example per table row" gives one argv per row. Several handler-table rows hold more than one caller-used form: `label-add`/`label-remove`, `mr get`/`mr checks`, `--me`/`--user U`/`--unassign`, `--assignee` `*`/`none`/username, `--count N`, `--description D`. Also, the only `issue start` refusal that is pinned is the failed re-read.
Material-because: UB-1. The † forms are listed because callers use them (`label-remove` has five callers; `--unassign` is used in `clients/kiro/prompts/close-session.md` Step 6), and a handler that drops one of them still passes the planned tests.
Proposed-edit: replace "example per table row: argv → recorded requests, output, exit code" with "one case per argv form (each `/` and `|` alternative of the handler table, and each optional flag UB-1 lists: `--count N`, `--description D`, `--assignee` `*`, `none` and a username, `--user U`, `--unassign`, `label-remove`, `mr checks`), each asserting the exact recorded requests (method, URL with query, JSON body), the standard output and the exit code". After the `issue start` clause, add "`issue start` 1 with no PUT for a closed issue and for an issue assigned to another user; a delivery verb through `main` returns the steward's code (4) with its arguments unparsed (`dequeue-pr 77 --reason x`)".

### C1–C7
- C1 AC-2.5: pin both stop forms. The last page sends `x-next-page:` empty (GitLab's last-page form), and a second case leaves the header out.
- C2 AC-3.1: parametrize the cross-host `302` over `private`, `bearer` and `job`. Redirect targets must be `https://`: an `http://` target reaches urllib's default `HTTPHandler`, which opens a real socket.
- C3 FakeHost:
  - It fails the test on an unscripted request, so AC-2.5's "no fourth request", AC-3.4's bound and AC-4.2's stop fail instead of hanging (there is no pytest-timeout).
  - AC-3.3 scripts two or more consecutive `429`s.
  - Responses set `msg` and carry an `http.client.HTTPMessage`. Measured: `addinfourl` has no `msg`, and `HTTPErrorProcessor` reads it.
- C4 AC-3.5: name the expected substring per shape, for example `bio: is too long (maximum is 255 characters)` and `error: Your snippet has been recognized as spam and has been discarded.`. As written, a message that is just the raw JSON body would pass.
- C5 AC-4.3: add a mutation payload with `errors: []` that returns its data. This is the "non-empty" boundary.
- C6 AC-2.4: the oracle also compares the file part's bytes and filename.
- C7 Subprocess test without a config: also assert that stderr names `config/gitlab.json` and has no `Traceback`. An ImportError or an uncaught `GitLabAPIError` also exits 1.

Judgements:
- FakeHost: an `HTTPSHandler` subclass instance passed to `build_opener` replaces only the default HTTPS handler. Measured opener: `HTTPDefaultErrorHandler`, `HTTPRedirectHandler`, `Fake`, `HTTPErrorProcessor`. So urllib's real error and redirect paths run (given C3).
- Hypothesis is justified for AC-2.2 and AC-2.3: both are encoders over value domains.
- AC-5 can fail: an unparseable line, an absent or unimportable family, the synthetic checker cases and the socket guard each make it red. `operations-index.md` is one table.

## Coverage

T, C, V, D as in the design's Mapping.

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | review of the operation-layer decision | COVERED |
| AC-1.2 | V `test_a_family_module_is_discovered_alone` | COVERED |
| AC-1.3 | review of "Shared files" | COVERED |
| AC-2.1 | T `test_one_credential_header_per_token_type` | COVERED |
| AC-2.2 | T `test_path_value_is_one_segment` (B1 placement), `test_project_path_is_encoded` | COVERED |
| AC-2.3 | T `test_array_and_hash_pairs` (B2), `test_array_of_hashes_pairs`, `test_json_body_is_native` | GAP |
| AC-2.4 | T `test_file_value_sends_multipart` | COVERED |
| AC-2.5 | T `test_offset_paging_follows_next_and_ignores_total_pages` | COVERED |
| AC-2.6 | T `test_keyset_paging_follows_link_unchanged` | COVERED |
| AC-3.1 | T `test_cross_host_redirect_drops_credentials`, `test_same_host_redirect_keeps_credential` | COVERED |
| AC-3.2 | T `test_429_waits_retry_after` | COVERED |
| AC-3.3 | T `test_429_without_headers_backs_off_increasingly` | COVERED |
| AC-3.4 | T `test_429_after_retries_raises` | COVERED |
| AC-3.5 | T `test_error_shape_raises_gitlab_api_error` | COVERED |
| AC-4.1 | T `test_graphql_posts_to_api_graphql` | COVERED |
| AC-4.2 | T `test_graphql_pages_by_end_cursor` | COVERED |
| AC-4.3 | T `test_graphql_errors_at_200_raise` | COVERED |
| AC-5.1 | V `test_checker_names_each_unlisted_row` | COVERED |
| AC-5.2 | V `test_a_family_module_is_discovered_alone` | COVERED |
| AC-5.3 | V `test_every_index_row_is_mapped_or_pending` | COVERED |
| AC-5.4 | V same test, socket guard | COVERED |
| UB-1 | C `test_subcommand` and seven named tests; D (B3) | GAP |
| UB-2 | C three config tests; T `test_standard_library_only` (B1 placement) | COVERED |
| UB-3 | verifier `git diff --name-only` | COVERED |

Verdict: NOT-TEST-READY — NOT-CLEAN (0 A, 3 B); 22 COVERED, 2 GAP.
