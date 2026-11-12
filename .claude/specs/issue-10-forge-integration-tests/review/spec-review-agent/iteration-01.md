# Design review — spec-review-agent — iteration 01

Lens: implementability and internal consistency. Every AC-1.1 to AC-9.3 and UB-1 to UB-4 has a row in the
Acceptance Criteria Mapping. Every record D6 and D9 name exists in `github_api/families/` with the path, query and
body parameters the invocations give, and none is in `call.py` `GATED_OPERATIONS`. The paged ones (`pulls/list`,
`search/repos`, `dependabot/list-repo-secrets`, `actions/list-workflow-runs-for-repo`, `reactions/list-for-issue`,
`activity/list-stargazers-for-repo`, `repos/list-for-org`) print `[]` through `Paging.LINK` and their `item_key`. The
compatibility options exist as used (`label-add --labels`, `update-issue --state`, `create-pr --head/--base/--title/
--body`, `merge-pr`, `comment-issue --body`), and `main`'s refusal block is described correctly. Two findings gate.

### A1 — Provisioning runs `git -C <clone>` before `<clone>` exists
Severity: A
Location: design.md § D9 step 3 (`prepare_clone`); § D10 `SubprocessGitRunner`; § D3 "The clone"
Defect: `SubprocessGitRunner` is bound to `<workspace>/clone` and always passes `-C <clone>`. The workspace is a fresh
`tempfile.mkdtemp`, and nothing creates `<workspace>/clone` before `prepare_clone`'s first command, `git init`. Git
dies on a `-C` directory it cannot enter (git.c `handle_options`: `if (chdir((*argv)[1])) die_errno("cannot change
to '%s'", ...)`), so every forge run fails in setup. S drives `provision` through `ScriptedGitRunner`, so the
default collection cannot catch this; the first forge-job run would.
Material-because: AC-1.3 (and with it AC-1.1): implemented as written, no run gets a fixture clone or creates its
ephemeral repository — wrong-behaviour.
Proposed-edit: D9 step 3 → "`prepare_clone`: `<workspace>/clone` created with `Path.mkdir`, then `git init`, the
clone's credential file and exclude line (D8), `git remote add origin`." and D3 "`git init <clone>`" → "`git init` in
the created `<clone>`".

### B1 — D8's linked-worktree lookup contradicts AC-6.1
Severity: B
Location: design.md § D8 "Lookup"; requirements.md AC-6.1; design.md § Correctness Properties AC-6.1
Defect: AC-6.1 says the suite reads the token "only from the test credential file of the repository checkout that
runs it". D8 also falls back to "the same path under the main working tree" (the parent of `git rev-parse
--git-common-dir`), and S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree` asserts the fallback.
For a linked worktree that is another checkout's file, which the frozen criterion does not allow.
Material-because: AC-6.1 is contradicted by the design and by the test written for it.
Proposed-edit: restate AC-6.1 to say what the design does: "THE forge suite SHALL read the test token only from the
test credential file of the checkout that runs it or, when that checkout is a linked worktree without one, of the
repository's main working tree (both git-ignored by `.gitignore` `credentials/*`)." If the frozen text stands instead:
delete D8's "else, for a linked worktree, … the parent of `git rev-parse --git-common-dir` … prints a relative path"
clause and the worktree half of the AC-6.1 test.

### C1 — The teardown reads `run_id` when step 1 fails, before step 2 has bound it
Severity: C
Location: design.md § D9 steps 1, 2 and 7
Defect: step 7's `finally` covers steps 1 to 6 and calls `delete_ephemeral(..., run_id=run_id)`, but `run_id` is bound
in step 2. A refused credential (step 1) therefore ends in `UnboundLocalError`, chained over the `ForgeSetupError`,
and S `test_a_bad_test_credential_fails_before_any_request` (`provision` raises `ForgeSetupError`) fails.
Proposed-edit: swap steps 1 and 2 and bind them before the `try`: "1. `run_id = new_run_id()`, `name =
ephemeral_name(run_id=run_id)`. 2. `read_test_token(...)`." Step 7 then reads "In the `finally` around steps 2 to 6 and
the yield". `new_run_id` sends nothing, so AC-6.2's "before any request" holds.

### C2 — The clone's credential file needs an LF line end, or the D3 helper sends `token\r` on Windows
Severity: C
Location: design.md § D8 "Writing"; § D3 "Alternatives"
Defect: D8 writes "the token and a line end", and D3 rejects the operator's file because `read` keeps a CR. Python's
text-mode write (`Path.write_text`, `newline=None`) turns `\n` into `\r\n` on Windows, so the clone's own file ends in
CRLF there: `read -r t` keeps the `\r`, and git sends a password the forge refuses. CI's ubuntu `verify` leg would
not show it.
Proposed-edit: D8 "Writing" → "the clone's `credentials/github-pat.txt` holds the token and `\n`, written as bytes
(`Path.write_bytes`), owner-only file mode, …".

### C3 — `test_no_leftover_survives_the_sweep` judges at the test's time, not the sweep's
Severity: C
Location: design.md § D6 table, F:fixture `test_no_leftover_survives_the_sweep`
Defect: the sweep correctly keeps a leftover that is a day old or less (AC-3.2). If that leftover passes the one-day
mark between the sweep and the assertion, `is_leftover` at "the test's time" is true and the test fails, though the
sweep did what AC-3.1 asks.
Proposed-edit: "`call repos/list-for-org --path org=bestehorn-sff-test`: no item `is_leftover` at the sweep's `now`
(`EphemeralRepository` carries it as `swept_at`) (AC-3.1)", and add `swept_at` to D9's `EphemeralRepository` field
list.

### D1 — D1's rejected alternative gives a reason the chosen command does not meet
Severity: D
Location: design.md § D1 "Alternatives"
Defect: `-o python_files=` is rejected because "AC-7.2 has the path alone run the suite", but the chosen command also
needs `--workers 1`. On a host where `local_workers()` is above 1, `run_tests.py test/forge` gets `-n`, and
`refuse_distributed_run` errors every test.
Proposed-edit: "`forge_*.py` with `-o python_files=` on the command line (the module convention would belong to the
command, not to the suite's own configuration)".

NOT-CLEAN (1 A, 1 B)
