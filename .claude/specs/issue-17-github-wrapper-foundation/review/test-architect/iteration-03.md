# Test architect - design review, iteration 03 (delta)

## Fix sites

| Id | Site | Status |
|---|---|---|
| C5 | Testing Strategy: P compares stdout, exit, non-GET requests | APPLIED |
| C6 | AC-2.1 `download` answers `200` on the API host | APPLIED; hop handed to AC-3.1 (B1) |
| C7 | D8 cut to the next `###`: both lists are `###` sections ending at "### Custom agents" / "### Custom-agent sources", and neither holds `github_api` today, so S is red until the list edit | APPLIED |
| C8 | UB-1.1 C-only userinfo example | APPLIED; oracle vacuous (A1) |

Iteration-02 edits: the `get-logs` `302` case is in P's set, so a product refusing the download redirect exits 1 against the fork's 0. Default port: `:443` keeps (fails a raw-authority compare), `:8443` and `http://` strip (fail a hostname-only compare). Non-integer and empty port: C9.

## Findings

### A1 - The userinfo example reads stderr, which an in-process logged refusal never reaches
Severity: A
Location: design.md § Correctness Properties UB-1.1 (userinfo example)
Defect: C runs the case through `main` in process and D6 step 4 logs the refusal; during a test pytest keeps handlers on the root logger (`_pytest/logging.py` `_runtest_for` -> `catching_logs` -> `root_logger.addHandler`; `pyproject.toml` `addopts` leaves the plugin on), so logging's last-resort stderr handler never fires and captured stderr is empty whatever the message holds; a product keeping the fork's verbatim `_detect_repo` message passes.
Material-because: security - D6's strip (§ Security Considerations "No message carries a URL's userinfo") has no test that can fail, so a token in `origin` can reach the operator's log.
Proposed-edit: replace "and stderr holds neither `ghp_T` nor `secret`" with "and the captured log records (`caplog`) hold the refusal naming `.git/config` and `github.com/o/socket.io.git`, while neither they nor stderr hold `ghp_T` or `secret`".

### B1 - No test sends `download`'s redirect, which C6 and D5 hand to AC-3.1
Severity: B
Location: design.md § Correctness Properties AC-3.1; D5 (`get-logs` case)
Defect: AC-2.1 says "the storage hop is AC-3.1's" and D5 says the `get-logs` `302` is followed "without the credential", but AC-3.1's examples do not name `download`, and C and P compare only non-GET requests, so a `download` on its own default opener (the fork has a separate `_build_download_opener`) forwards `Authorization` to the storage host and passes every test.
Material-because: AC-3.1 - the one cross-host redirect a caller-used subcommand makes (`get-logs`) is untested.
Proposed-edit: in AC-3.1 replace "an API `302` to another host is followed with no `Authorization`" with "an API `302` to another host, from `request` and from `download`, is followed with no `Authorization`".

### C9 - D3's non-integer and empty port rules have no example
Severity: C - add to AC-3.1: a `302` to `https://user:pw@api.github.com/x` raises `GitHubAPIError` with no request recorded to it; `https://api.github.com:/x` keeps `Authorization`. Without them an `http.client` split lets `InvalidURL` escape. <!-- pragma: allowlist secret -->

## Coverage (tests per § Acceptance Criteria Mapping)

| Criterion | Test | Status |
|---|---|---|
| AC-1.1 | inspection D1; R | COVERED |
| AC-1.2 | inspection D2; V | COVERED |
| AC-1.3 | V | COVERED |
| AC-2.1 | T | COVERED |
| AC-2.2 | T | COVERED |
| AC-2.3 | T | COVERED |
| AC-2.4 | T | COVERED |
| AC-3.1 | T | COVERED (B1: `download` path) |
| AC-3.2 | T | COVERED |
| AC-3.3 | T | COVERED |
| AC-3.4 | T | COVERED |
| AC-4.1 | T | COVERED |
| AC-4.2 | T | COVERED |
| AC-4.3 | T | COVERED |
| AC-5.1 | V | COVERED |
| AC-5.2 | V | COVERED |
| AC-5.3 | V | COVERED |
| UB-1.1 | C; P | COVERED (A1 is the strip's oracle) |
| UB-1.2 | `test_wrapper_delivery.py`; C | COVERED |
| UB-1.3 | C; S | COVERED |
| UB-2.1 | C | COVERED |
| UB-2.2 | V | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |
| UB-3.2 | C | COVERED |

Verdict: NOT-CLEAN (1 A, 1 B) - NOT-TEST-READY (24 COVERED, 0 GAP)
