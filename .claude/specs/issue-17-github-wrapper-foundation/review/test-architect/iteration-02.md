# Test architect — design review, iteration 02 (delta)

## Iteration-01 fix sites

| Id | Fix site | Status |
|---|---|---|
| A1 | design.md § Correctness Properties UB-2.2, D7 (X1): top-level import names `github_api` or in `sys.stdlib_module_names`, V on CI's Python 3.10 (`.github/workflows/ci.yml` `python-version: '3.10'`); `import yaml` now fails it | RESOLVED |
| A2 | § Testing Strategy (P minus the `--token-stdin` cases); UB-1.1 (C only: exit 2, empty stdout, no request) | RESOLVED |
| B1 | UB-1.1 parser parity, `type` included; `list-issues --label` case. The fork's caller-used options carry `type=int` or none (`_register_issue_subcommands`, `_register_pr_subcommands`, `_add_*_arguments`), so the `type` comparison can pass | RESOLVED |
| B2 | § Testing Strategy ordered route responses and expected non-GET requests; UB-1.1 `start-issue`/`issue start` exit 0. `cmd_start_issue` GETs, POSTs labels and assignees, re-GETs: ordered responses build exit 0, the recorded writes fail a product that skips them | RESOLVED |
| B3 | AC-3.2 `retry-after` + `x-ratelimit-remaining: 0` + later reset sleeps `retry-after` | RESOLVED |
| B4 | AC-2.1 example includes a `download` | RESOLVED |
| B5 | AC-5.1 counts against the heading `every operation (N)`; the index heading's number equals its method rows and its distinct IDs; both named capabilities are first cells of the **Only in GraphQL** table, "Capability" is its header cell, **In both** follows it | RESOLVED |
| B6 | AC-5.2 an ID and a capability gap, a covered and a pending item of each kind | RESOLVED |
| C1–C4 | UB-1.3 oracle `str(Path("credentials") / "github-pat.txt")` (the fork's `_load_token` formats `CREDENTIALS_FILE`); merged headers recorded case-insensitively; P sets `sys.argv`; last page of the `prev`/`first`/`last` row sends `link` without `next` | APPLIED |

The delta's new oracles (AC-2.2 and AC-2.4 other-origin refusals, AC-3.1 `http://`, `:8443` and `:443` targets, AC-1.1 registry examples, UB-1.3 S) can each fail: the fake host patches `HTTPHandler.http_open` too and records full URLs, and S's Part 5.3 / Part 6.2 sections exist with a following `### Part` heading in both prompts.

## Findings

### C5 — P's comparison of the expected writes is implicit
Severity: C — § Testing Strategy says C compares the non-GET requests while P "runs the same `CASES`"; write "comparing stdout, exit code and the non-GET requests", and "every golden value of a case P runs is the fork's own output" (the `--token-stdin` and delivery cases are not the fork's).

### C6 — AC-2.1's `download` example and the storage hop
Severity: C — "every request recorded for … a `download`" would assert the version header on a storage-host hop, which AC-2.1 ("every REST request") does not require; let that example answer `200` on the API host (the hop is AC-3.1's).

### C7 — Where S cuts a shipped-Python list
Severity: C — `src/payload/scripts/github_api/` (the Part 5.3 edit) contains `scripts/github_api/`, so a whole-file search passes the list assertion without the list edit; D8: "each shipped-Python list, cut from its heading to the next `###` heading, names `scripts/github_api/`".

### C8 — D6's userinfo strip has no example
Severity: C — the fork's message embeds the URL (`_detect_repo`: "Could not parse GitHub owner/repo from origin URL: {url}") and P does not compare stderr, so nothing pins the strip; a C-only case: an unparseable `origin` holding `user:secret@` exits 2 with empty stdout and stderr without `secret`.

## Coverage

Tests are the design's § Acceptance Criteria Mapping rows (T, R, C, V, P, S as defined there).

| Criterion | Test | Status |
|---|---|---|
| AC-1.1 | inspection D1; R `test_call_refuses_an_undocumented_parameter`, `test_expand_encodes_and_refuses_dot_segments` | COVERED |
| AC-1.2 | inspection D2; V `test_discovery_follows_the_directory` | COVERED |
| AC-1.3 | V `test_one_module_per_family_holding_only_its_own_ids` | COVERED |
| AC-2.1 | T `test_every_rest_request_sends_the_api_version` | COVERED |
| AC-2.2 | T `test_link_pages_are_followed_as_given` | COVERED |
| AC-2.3 | T `test_wrapped_pages_return_the_item_key_items` | COVERED |
| AC-2.4 | T `test_an_asset_is_uploaded_to_the_upload_url` | COVERED |
| AC-3.1 | T `test_a_cross_origin_redirect_drops_the_credential` | COVERED |
| AC-3.2 | T `test_a_rate_limit_is_waited_out_and_retried` | COVERED |
| AC-3.3 | T `test_spent_retries_raise_naming_the_limit` | COVERED |
| AC-3.4 | T `test_an_error_status_raises_with_the_documented_body` | COVERED |
| AC-4.1 | T `test_graphql_posts_query_and_variables` | COVERED |
| AC-4.2 | T `test_graphql_follows_page_info_cursors` | COVERED |
| AC-4.3 | T `test_graphql_errors_raise_even_with_200` | COVERED |
| AC-5.1 | V `test_the_reference_is_read_whole` | COVERED |
| AC-5.2 | V `test_a_gap_is_named` | COVERED |
| AC-5.3 | V `test_every_operation_is_covered_or_pending` | COVERED |
| UB-1.1 | C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`, `test_the_parsers_match_option_by_option` | COVERED |
| UB-1.2 | `test_wrapper_delivery.py`; C `test_a_delivery_verb_delegates_to_the_steward` | COVERED |
| UB-1.3 | C `test_the_script_runs_by_path`; S `test_the_setup_prompts_copy_the_package` | COVERED |
| UB-2.1 | C `test_the_credential_comes_only_from_the_file` | COVERED |
| UB-2.2 | V `test_the_wrapper_imports_only_the_standard_library` | COVERED |
| UB-3.1 | `test_wrapper_delivery.py` in CI `tests` leg; PR diff | COVERED |
| UB-3.2 | C `test_the_module_loads_without_credential_or_network` | COVERED |

Verdict: CLEAN — TEST-READY (24 COVERED, 0 GAP)
