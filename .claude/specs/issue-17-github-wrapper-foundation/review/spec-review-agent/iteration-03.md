# Design review — spec-review-agent — iteration 03 (delta)

### C1 — D5 says the fork's unencoded-value crash returns none of UB-1.1's exit codes; it returns 1
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged" (closing paragraph, second sentence)
Defect: The fork's `main` catches only `GitHubAPIError`. So the `http.client.InvalidURL` that a space in a query value
raises ("URL can't contain control characters. '/repos/o/r/issues?labels=good first issue' (found at least ' ')")
ends the interpreter with a traceback and exit status 1 (measured: `exit=1`). That number is on UB-1.1's list, and
D5's own preface, "Visible only where the fork exited 1", says so. The case falls outside UB-1.1 because of its cause:
UB-1.1's exit 1 is "a `GitHubAPIError` raised by the subcommand". The sentence comes from my iteration-02 C1 wording.
Proposed-edit: replace "The unencoded-value case is an uncaught crash on the fork, none of UB-1.1's listed exit codes;
no golden case builds it." with "On the fork the unencoded-value case ends in an uncaught `http.client.InvalidURL`
— exit status 1 with a traceback, not the `GitHubAPIError` that UB-1.1's exit 1 names; no golden case builds it."

### C2 — D8 has the shipped setup prompts name this repository's issue as "#14"
Severity: C
Location: design.md § D8, third bullet (the "skeletons" sentence)
Defect: The prompt text D8 prescribes says `get-jobs`, `rerun` and `cancel` "arrive with part 2 (#14)". The setup
prompts are pasted into other projects, and there "#14" points at that project's own tracker. Neither prompt cites
this repository's issues anywhere else. The only `#N` tokens in either are upstream ones (`aws/jsii#700`,
`aws/aws-cdk-cli#802`) and examples (`#77`, `#326`).
Proposed-edit: replace "that `get-jobs`, `rerun` and `cancel` arrive with part 2 (#14)" with "that `get-jobs`,
`rerun` and `cancel` arrive in a later framework release".

### D1 — D6's gloss of "userinfo" includes the scheme
Severity: D
Location: design.md § D6 "Kept by name, with the fork's bodies" (`_detect_repo`)
Defect: "everything up to the last `@` before the host" starts at the beginning of the URL, so it also takes in
`https://`. Userinfo is the part between `//` and `@`. Neither reading lets `ghp_T` or `secret` reach stderr, and the
UB-1.1 compatibility-only example checks exactly that.
Proposed-edit: "(the authority's text up to and including its last `@`, a bare token included)".

CLEAN
