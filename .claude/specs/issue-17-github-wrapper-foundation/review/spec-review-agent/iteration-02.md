# Design review — spec-review-agent — iteration 02 (delta)

### B1 — The UB-1.1 redirect carve-out also drops `get-logs`, whose every success is a followed `302`
Severity: B
Location: requirements.md § UB-1.1 (the "except a response that redirects the request" clause); design.md § D5 "Deviations from the fork, flagged" (first bullet, closing sentence)
Defect: The carve-out (my iteration-01 B1 edit) takes every redirected response out of UB-1.1. But `get-logs` always gets a `302` to a storage host (`conventions.md` "Downloads and redirects", `actions/download-workflow-run-logs`), and the fork follows it: `cmd_get_logs` → `_fetch_log_content` → `_build_download_opener` → `_NoRedirectHandler`, which strips `Authorization` and follows ("refusing the redirect would break `get-logs`"). So UB-1.1 no longer binds `get-logs`' archive printing or its exit 0 on the response GitHub actually sends. D5's "the fork's `_RefusingRedirectHandler` refuses every redirect" is false for this download. And "its golden cases build none of them" keeps the `get-logs` case off the `302` path.
Material-because: UB-1.1 — a caller-used subcommand's unchanged output and exit code are left unprotected (regression).
Proposed-edit:
1. requirements.md UB-1.1: replace "except a response that redirects the request or that AC-3.2 rate-limits" with "except a redirect other than the `302` that sends `get-logs`' download to its storage host, or a response that AC-3.2 rate-limits".
2. design.md D5, first bullet: replace "a redirected `GET` — the fork's `_RefusingRedirectHandler` refuses every redirect;" with "a redirected `GET` other than the download's `302` to its storage host — the fork's `_RefusingRedirectHandler` refuses every redirect of an API request (its `_NoRedirectHandler` follows the download's redirects with the credential stripped on every hop);".
3. design.md D5: replace "UB-1.1 excludes the redirect and rate-limit states; its golden cases build none of them." with "UB-1.1 excludes these states and its golden cases build none of them; the `get-logs` case serves the `302` to a storage host, which both wrappers follow without the credential."

### C1 — D5 flags a third visible deviation that UB-1.1's exclusions do not name
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged" (third bullet, closing sentence)
Defect: The unencoded-value bullet (from iteration-01 C4) is a visible deviation. UB-1.1's carve-out names only redirects and rate limits, and D5's closing sentence speaks of those two only. The deviation is consistent with UB-1.1 only because the fork's outcome there is an uncaught crash, which is none of UB-1.1's listed exit codes. The design does not say so.
Proposed-edit: append to D5's closing sentence, after B1's edit: "The unencoded-value case is an uncaught crash on the fork, none of UB-1.1's listed exit codes; no golden case builds it."

### C2 — `origin()` defines no outcome for a non-numeric port, which is where a userinfo URL without a port ends up
Severity: C
Location: design.md § D3 "Origin (X5)"; § D3 "Failures, in `_send`"
Defect: `Request(url).host` keeps the userinfo (`_splithost`). So for `https://u:p@api.github.com/`, the split "after the last `:`" yields the port `p@api.github.com`. At that point `http.client.HTTPConnection._get_hostport`, which `origin()` copies, raises `InvalidURL`, an `HTTPException` and not a `ValueError`; for an empty port (`host:`) it uses the default. D3's failure list maps only `URLError` and `ValueError`. A server-supplied `Location` or `link` URL of this shape therefore ends in a traceback instead of `GitHubAPIError`. Both exit 1, and nothing is sent.
Proposed-edit: append to the "Origin (X5)" paragraph: "A non-numeric port raises `ValueError` (an empty one counts as absent), which `_send` raises as `GitHubAPIError` naming the request URL, as for a malformed `Location`."

### C3 — D8 re-points one docstring pointer; the other "skeleton / docstring" sentences in the same sections point at the block D6 removes
Severity: C
Location: design.md § D8; § D6 "Removed"
Defect: D6 removes the skeleton's implementation-instructions comment block (endpoints, claim and checklist guidance). D8 re-points only setup-claude Part 5.3's "(See the expanded docstrings in `src/payload/scripts/github_wrapper.py` …)". The same two sections still say, for GitHub too: "The wrapper templates are skeletons; implement the subcommands the project's agents invoke", "See the expanded docstrings in the wrapper templates" and "(See the wrapper docstrings.)" in Part 5.3, and "The template wrapper scripts are skeletons … (see the docstring in each template)" and "the template docstrings specify them" in Part 6.2. A set-up agent is sent to guidance that no longer exists and told to implement subcommands the template now has.
Proposed-edit: add a D8 bullet: "In both sections, the sentences that call the templates skeletons to be extended per their docstrings say, for GitHub, that the template implements the caller-used subcommands and that a further subcommand is added as a `github_api/commands/` module (D2)."

### D1 — D6 step 5 writes the PR number unconverted
Severity: D
Location: design.md § D6 `main`, step 5
Defect: The fork passes `str(args.pr_number)` and `test_wrapper_delivery.py` passes `["77"]`, but `[pr_number]` reads as the parsed integer.
Proposed-edit: "`[str(pr_number)]`, `[str(pr_number), "--reason", reason]`".

### D2 — setup-kiro's directory tree still lists the wrapper alone
Severity: D
Location: design.md § D8; prompts/setup-kiro.txt § APPENDIX "Standard directory structure"
Defect: The tree's `scripts/` entry shows `github_wrapper.py # if GitHub` with no `github_api/`, and D8 does not edit it.
Proposed-edit: append to D8's setup-kiro bullet: "and its 'Standard directory structure' tree lists `github_api/` under `scripts/` beside `github_wrapper.py`."

NOT-CLEAN (0 A, 1 B)
