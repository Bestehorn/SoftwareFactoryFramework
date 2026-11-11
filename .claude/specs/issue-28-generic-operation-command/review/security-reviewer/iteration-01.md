# Security review — design iteration 01 (issue #28)

### B1 — `call` reaches `pulls/merge` and `issues/create` past the gates that refuse their compatibility spellings
Severity: B
Location: design.md § D1 (`call` serves every record); § D8 "This change"; § Security Considerations
Defect: `gate_merge_steward.script_call` refuses a wrapper call only when its first positional is `merge-pr` (or
`mr merge`), and `API_MERGE_RE` only beside `curl`/`wget`/`Invoke-RestMethod`; `gate_filing.CREATE_RE` matches only
`create-issue`/`issue create`. So `python scripts/github_wrapper.py call pulls/merge --path pull_number=N --field
merge_method=squash` and `call issues/create --field title=T --field body=B`, both records declared today
(`families/pulls.py`, `families/issues.py`), pass both gates, and the design neither changes the gates nor records it.
Material-because: security — in a `"merge": "steward"` project set up from the next release (`prompts/setup-claude.txt`
Part 5.3 copies `src/payload/scripts/github_api/`; its settings template allow-lists
`Bash(python scripts/github_wrapper.py:*)`), an agent writes the trunk outside the steward with no gate and no
permission prompt, where the `gate_merge_steward` docstring says the gate "is the enforcement" on a host plan without
branch protection.
Proposed-edit:
1. D8 "This change" gains three rows:
   - `src/hooks/gate_merge_steward.py`: `script_call` also refuses a wrapper call whose positionals begin
     `call pulls/merge`, as it refuses `merge-pr`.
   - `src/hooks/gate_filing.py`: a wrapper call whose words hold `call issues/create` is a create call;
     `_create_call_words` starts after `issues/create`, and the provenance lines are read from the command text as today.
   - `src/hooks/tests/test_delivery_gates.py` and `src/hooks/tests/test_gate_filing.py`: one refusal case for each
     `call` spelling, and one allowed case (`call pulls/get`).
2. Security Considerations gains: "**Gates.** `merge-steward` and `issue-filing-gate` judge the wrapper by its
   subcommand words. They judge `call pulls/merge` as `merge-pr` and `call issues/create` as `create-issue`, so `call`
   reaches no endpoint that a gate refuses under its compatibility spelling."
3. Residuals gains: "A slice that declares another record that writes a branch (`repos/merge`, `git/update-ref`,
   `repos/create-or-update-file-contents`) makes it reachable through `call` with no gate; `merge-steward` gates no
   spelling of those endpoints today. Routed per `issue-filing-discipline.md` (OUT-OF-SCOPE) before #27 declares them."

### C1 — "Destructive operations" leaves out the default target and the absent permission prompt
Severity: C
Location: design.md § Security Considerations "Destructive operations"; § D2 `cmd_call` step 2
Defect: Under D2 step 2's default, `call repos/delete` (`DELETE /repos/{owner}/{repo}`, which the requirements'
Residuals say #27 declares) given no `--path` deletes the checkout's own `origin` repository. The wholesale wrapper
allow-list means no permission prompt comes first. The bullet names only the caller's decision.
Proposed-edit: replace the bullet's second sentence with: "Whether to run one is the caller's decision under
`continuous-work.md` Exception 1. No permission prompt comes first (the settings allow-list the wrapper as a whole), and
a record whose only path parameters are `{owner}` and `{repo}` acts on the checkout's `origin` when neither is given
(D2 step 2)."

### C2 — A secret body value can only be given on the command line
Severity: C
Location: design.md § Residuals ("A string body value read from a file …")
Defect: The command line is the only body input, so a secret value such as `repos/create-webhook` `config.secret`
(`rest/repos.md`) shows in the process's command line and in the calling session's command transcript.
Proposed-edit: append to that residual: "A secret value given inline (`repos/create-webhook` `config.secret`) shows in
the process's command line; reading it from a file belongs to this residual."

### C3 — Outside this lane: `--query NAME[]` passes D4, then the registry refuses it with an uncaught `ValueError`
Severity: C
Location: design.md § D2 "Registry additions" (`send`); § D4 "Documented names"; § Correctness Properties AC-1.2
(`--query state[]=open`)
Defect: D4 checks `state[]` as `state`, and D2 sends the name as written. `registry._check_names`, which `send` runs
and the unchanged `pages` runs, compares `state[]` as written with `query_params` (`issues/list-for-repo` holds
`state`) and raises `ValueError`. `_run_command` catches only `GitHubAPIError`, so that AC-1.2 row exits 1 with a
traceback.
Proposed-edit: in D2 "Registry additions", add to `send`'s description: "`_check_names` compares a query name with one
trailing `[]` removed, as D4 does; `pages` runs the same check."
Graded C only because this lane covers security. On its merits it is wrong-behaviour against AC-1.2, and the lane that
owns correctness should grade it.

### D1 — The argparse type errors are not covered by the `json.dumps` rendering rule
Severity: D
Location: design.md § D2 "Parsing"; § D4 "How a refusal is written"
Defect: D4 renders every caller-supplied name with `json.dumps` in `cmd_call`'s refusals, but says nothing about the
`ArgumentTypeError` text that `assignment` and `json_member` raise. argparse prints that text verbatim.
Proposed-edit: in D2 "Parsing", after the three cases, add: "Each message names the option and the NAME rendered with
`json.dumps`, never the value."

Verdict: NOT-CLEAN (0 A, 1 B)
