# Design review — spec-review-agent — iteration 01

### B1 — UB-1.1 still binds the fork's exit 1 in the redirect and rate-limit states; for the same-origin redirect no criterion overrides it
Severity: B
Location: requirements.md § UB-1.1, § Residuals (same-host redirect bullet); design.md § D5 "Deviations from the fork, flagged"
Defect: UB-1.1 binds the fork's stdout and exit codes "for the same state of the repository on the host", and D5 settles the conflict only inside design.md ("The criteria govern those states; UB-1.1's cases build neither"). That holds for the cross-host redirect (AC-3.1) and the `403`/`429` limit (AC-3.2), but not for the same-origin `301` GitHub answers a GET to a renamed repository with (`Location: https://api.github.com/repositories/<id>/…`; writes get `307`, which D3 leaves unfollowed). AC-3.1 is cross-host only, and requirements § Residuals puts the same-host redirect outside AC-3.1, yet D3 follows it. So `get-issue`, `get-pr`, `get-run` and `list-issues` print and exit 0 where the fork's `_RefusingRedirectHandler.http_error_301` raises `GitHubRedirectRefusedError` and `main` returns 1. "UB-1.1's cases build neither" narrows the golden table, not the criterion.
Material-because: UB-1.1 is contradicted by D3 in the same-origin-redirect state, and no acceptance criterion of the ask licenses that change.
Proposed-edit:
1. requirements.md UB-1.1: replace "and, for the same state of the repository on the host, to write" with "and, for the same state of the repository on the host — except a response that redirects the request or that AC-3.2 rate-limits, which Requirement 3 and `design.md` D3 govern — to write".
2. requirements.md § Residuals, same-host bullet: replace "whether `Authorization` is kept there is `design.md`'s decision" with "whether it is followed and whether `Authorization` is kept there is `design.md`'s decision".
3. design.md D5: replace "(the fork's `_RefusingRedirectHandler` refuses every redirect; AC-3.1 follows it)" with "(the fork's `_RefusingRedirectHandler` refuses every redirect; D3 follows it — AC-3.1 for another host, D3's own decision for the same origin, so `get-issue` on a renamed repository exits 0 where the fork exits 1)". Then replace "The criteria govern those states; UB-1.1's cases build neither." with "UB-1.1 excludes these states; its golden cases build none of them."

### C1 — UB-1.1 binds the delivery verbs to fork behaviour that UB-1.2 and DL-001 replace
Severity: C
Location: requirements.md § UB-1.1 (delivery bullet), § UB-1.2
Defect: UB-1.1 holds all six delivery verbs to the fork's `_build_parser` arguments, stdout and exit codes. But `wait-landed`, `check-handoff` and `check-landed` are not in the fork (DL-001). For the other three, the fork's `cmd_enqueue_pr` → `_run_merge_steward` never reads `config/delivery.json`, so when `host` names another forge the fork runs the steward, while UB-1.2 requires `EXIT_DELIVERY_ELSEWHERE`. Design D6 and the parity test, which excludes the delivery verbs, already follow UB-1.2.
Proposed-edit: replace the delivery bullet with "- delivery: `enqueue-pr`, `dequeue-pr`, `queue-status` (the fork's arguments; output and exit codes per UB-1.2), and `wait-landed`, `check-handoff`, `check-landed` (UB-1.2 alone; not in the fork — DL-001)."

### C2 — D6 steps 2 to 5 leave the delegation argv to inference
Severity: C
Location: design.md § D6 `main`, steps 2, 4, 5
Defect: Step 5 rebuilds the argument list "as the fork's `cmd_enqueue_pr`, `cmd_dequeue_pr`, `cmd_queue_status` build it". Those lists start with the steward verb (`[STEWARD_ENQUEUE, str(args.pr_number)]`), but `steward_delegate` prepends `DELIVERY_VERBS[verb]` itself (`test_wrapper_delivery.py` passes `["77"]`), so the literal reading sends the verb twice. Also, only step 3 is marked "Otherwise", so the design never says whether steps 4 and 5 run for the three verbs of step 2.
Proposed-edit: step 5 becomes "Every delivery verb returns `steward_delegate(verb, args, token, "github")`. For the step-2 verbs, `args` is the argv after the subcommand. For the others, it is what the fork's handlers pass after the steward verb: `[pr_number]`, `[pr_number, "--reason", reason]`, or `["--json"]` when given." Append to step 2: "Steps 4 and 5 apply to them."

### C3 — The fork cannot be the parity oracle for the `--token-stdin` case
Severity: C
Location: design.md § Testing Strategy (CLI golden tests); § Correctness Properties, UB-1.1
Defect: `CASES` includes a usage-error case for `--token-stdin`, and the parity test runs `CASES`, minus only the delivery verbs, against the fork. But the fork registers that option on `list-issues` and `create-issue` (`_add_stdin_credential_option`) and reads standard input for it (`_load_stdin_token`). The case's outcome on the fork therefore depends on the test's stdin, not on UB-1.1, which drops the option on purpose.
Proposed-edit: "…runs the same `CASES`, minus the delivery verbs and the `--token-stdin` cases (deviations UB-1.1 makes on purpose), against the installed fork…"

### C4 — D5 says query encoding does not show on stdout; for a value with a space it does
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged"
Defect: The fork puts `--labels` and `--assignee` into the query unencoded (`cmd_list_issues`) and `--workflow` into the path unencoded (`cmd_list_runs`). `http.client` refuses a URL containing a space (`InvalidURL: URL can't contain control characters`, measured). That is an `HTTPException`, which the fork's `_api_request` `except HTTPError` does not catch. So `list-issues --labels "help wanted"` crashes on the fork (exit 1, no stdout) and prints the issues under D4's encoding. A crash is not one of UB-1.1's listed exit codes, but the difference is visible, so "not visible" is wrong.
Proposed-edit: delete "; query values are urlencoded" from the "Not visible on standard output" sentence. Append to the "Visible only where the fork exited 1" sentence: "and a query value or path segment the fork sent unencoded that `http.client` refuses (a space: `InvalidURL`, an uncaught crash), which D4 encodes."

### C5 — D2's table of shared files leaves out the test fixture module and `_common.py`
Severity: C
Location: design.md § D2 "What a family's change edits" (AC-1.2)
Defect: AC-1.2 asks for every file a family's change still edits, each with its reason. The table names `registry.py` and `transport.py` for the case where they lack a mechanic. It does not name `src/payload/test/github_wrapper_fixtures.py`, the fake host every per-family test module loads, for the case where it lacks a response shape. Nor does it name `github_api/commands/_common.py`, which holds the helpers every command module shares.
Proposed-edit: add the rows "`src/payload/test/github_wrapper_fixtures.py` | a family's test needs a fake-host response the module lacks | every suite installs the one fake host" and "`github_api/commands/_common.py` | a command needs a body or printing helper it lacks | the fork's `_resolve_body` and JSON printing exist once".

NOT-CLEAN (0 A, 1 B)
