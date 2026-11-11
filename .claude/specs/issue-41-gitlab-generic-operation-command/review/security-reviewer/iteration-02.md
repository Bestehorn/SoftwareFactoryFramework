# Security review — design iteration 02 (issue #41, delta)

Checked, no finding:

- C2's fix site. The claim that `create#delete-repository-branch` deletes the trunk is gone. The design now names that
  record only in the AC-1.2 and AC-1.5 examples. Dropping the claim, rather than restating it, removes the
  overstatement.
- C3's fix site. "Destructive operations" now says no permission prompt comes first. That matches
  `prompts/setup-claude.txt`, which carries `"Bash(python scripts/gitlab_wrapper.py:*)"`.
- C4's fix site. The merged residual "Secrets in arguments" still names `--file` with `config/gitlab.json` and
  `credentials/`, and routes it per `issue-filing-discipline.md`. The upload consequence is gone, but the risk is still
  routed.
- Y1's member-row rule. D4 still decides which names a caller may give: a name must equal a declared `Param` after
  `attribute_name`. In a JSON-body record, the members inside a parent's `-F` object go unchecked. That object goes to
  the configured origin under the caller's own token, so it crosses no boundary. The only `In` `header` rows in the
  reference are two `Symbolchecksum` rows (`rest/openapi-only.md`). They stay pending, so no command-line value
  reaches a request header in this change.
- The `/geo/` and `/hooks/` arms decide only how the tests classify an operation. They widen nothing `call` can send.
  The bare `/hooks` rows (`GET`, `POST`) are `gitlab-dedicated` sections, so the Offering arm catches them. Every
  `openapi-only` system-hook or Geo row starts with `/hooks/` or `/geo/` (`operations-index.md`).

### C1 — The merged gated-records line counts a branch deletion and does not plainly count a merge
Severity: C
Location: design.md § Residuals "A record that writes a branch or creates an issue"; § D8 slice table "the exceptions"
Defect: The cut line keeps the class from iteration-01 C1 but drops its members, and "writes a branch" now misses in
both directions:
- It covers deleting a branch. Yet `create#delete-repository-branch` is declared, outside `GATED_OPERATIONS`, and sent
  through `call` by the AC-1.2 example.
- It does not plainly cover a merge. `verify#add-a-merge-request-to-a-merge-train`
  (`POST /projects/:id/merge_trains/merge_requests/:merge_request_iid`, `rest/verify.md`) merges into the target branch.
  The merge-steward gate guards exactly that act.

So a slice author has to guess which records the line covers.
Proposed-edit: in both places replace "writes a branch" with "commits to or merges into a branch". The Residuals line
becomes "**A record that commits to or merges into a branch, or creates an issue,** is gated by its slice, in
`GATED_OPERATIONS` or the hooks." The line count stays the same.

### C2 — Y2's `parse_constant` refusal is a plain `ValueError`, and no test pins "it never holds a value"
Severity: C
Location: design.md § D2 "Parsing"; § Correctness Properties AC-1.3, K `test_a_field_that_is_not_json_is_refused`
Defect: The `parse_constant` refusal is not a `JSONDecodeError`. In the venv, `json.loads` with a `parse_constant`
that raises `ValueError` raises a `ValueError` that is not a `JSONDecodeError`, for `NaN`, `[1, NaN]`,
`{"a": Infinity}` and `-Infinity`. A `type` function that converts only `JSONDecodeError` therefore lets this one
escape. argparse then prints `argument -F: invalid <type> value: '{"secret": "s3", "n": NaN}'` (measured, exit 2): the <!-- pragma: allowlist secret -->
whole value, which D2 says the message never holds. K's oracle (exit 2, no request) passes either way.

This is graded C, not higher: the value is already on the command line ("Secrets in arguments"). #28's `json_member`
catches `ValueError`.
Proposed-edit: two changes, both to existing text.
- D2 "Parsing": replace "and `-F` text that `json.loads` refuses raise" with "and `-F` text that `json.loads`
  refuses (its `ValueError`: a `JSONDecodeError` or the `parse_constant` refusal) raise".
- K `test_a_field_that_is_not_json_is_refused`: replace "exit 2 with no request (D2)" with "exit 2 with no request,
  and standard error does not hold the text after the first `=` (D2)".

Verdict: CLEAN
