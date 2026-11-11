# Security review — design iteration 02, delta (issue #28)

Fix sites of iteration 01, all resolved:

- B1 is closed by X4. D2 step 1 refuses an ID in `GATED_OPERATIONS` before `registry.lookup`. D4 has its exit-2 row,
  and D7, D8 and the "Gates" bullet state it. K `test_a_gated_operation_names_its_subcommand` covers both IDs.
- Bypass checks, all negative:
  - Case or spelling: `registry.lookup` compares `record.operation_id == operation_id` exactly, and every declared ID
    is lowercase, so `Pulls/Merge` or ` pulls/merge` is refused as unknown (exit 2, AC-2.1).
  - Alias or second record: `operations-index.md` has one row for `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge`
    and one for `POST /repos/{owner}/{repo}/issues`. V `_record_problems` requires a record's ID to be an index ID of
    its family carrying that row's method and path, and `lookup` refuses a duplicate ID. So no other record can reach
    either endpoint.
  - Path values: these cannot reroute a declared record onto either endpoint. `expand` encodes with `safe=""` and
    refuses `.`/`..` segments, and the method is fixed by the record.
- C1: applied in "Destructive operations", which cites D2 step 3 (the owner/repo default).
- C2: applied in Residuals.
- C3: applied as X1 (`query_name`, D2 "Registry additions", D8 `registry.py`).
- D1: applied in D2 "Parsing".

### C1 — The trunk-writing residual leaves out `pulls/merge-async` and the already-declared `git/delete-ref`
Severity: C
Location: design.md § Residuals (item "A slice that declares a record writing a branch …"); § Security Considerations
"Gates"
Defect: The residual's list leaves out two endpoints:
- `pulls/merge-async` (`PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async`, body `commit_title`,
  `commit_message`, `sha`, `merge_method`; `rest/pulls.md` "Merge a pull request asynchronously") is the asynchronous
  form of the gated `pulls/merge`, and it is on `PENDING` in `families/pulls.py`. Once a slice declares it,
  `call pulls/merge-async` merges a PR past both `GATED_OPERATIONS` and `gate_merge_steward`, whose `API_MERGE_RE`
  (`/pulls/\d+/merge\b`) matches that URL only beside `curl`/`wget`/`Invoke-RestMethod`.
- `git/delete-ref` (`families/git.py`, multi-segment `ref`) is declared today. It deletes `heads/main` through `call`,
  as it already does through the unchanged `delete-remote-branch`, while `trunk_push` refuses a `git push --delete` of
  the trunk. "No gate refuses those endpoints today" therefore reads as if no declared record writes a branch.

This is graded C, not B, because `call` adds no reach in this change: `pulls/merge-async` is pending, and
`git/delete-ref` was already reachable without a gate through `delete-remote-branch`.
Proposed-edit: replace that Residuals item with: "A slice that declares a record writing a branch (`pulls/merge-async`,
the asynchronous `pulls/merge`; `repos/merge`, `git/update-ref`, `git/create-ref`,
`repos/create-or-update-file-contents`) extends `GATED_OPERATIONS` or the hook gates with it. `git/delete-ref`, declared
since #17, deletes any branch, the trunk included, through `call` as through `delete-remote-branch`. `merge-steward`
refuses neither spelling, only a `git push --delete` of the trunk; routed per `issue-filing-discipline.md`."

Verdict: CLEAN
