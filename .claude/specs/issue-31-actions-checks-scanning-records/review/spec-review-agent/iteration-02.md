# spec-review-agent — iteration 02 (tier S, combined, DELTA)

Delta: `change.md` § Residuals (iteration 01's replacement block, one wording change), DL-005, the #31 correction
comment. Unchanged text was not re-reviewed.

## Fix sites

| Finding | Status | Evidence |
|---|---|---|
| B1 — SARIF/zip forms routed to #46 | APPLIED | Residuals third bullet is the proposed text verbatim ("outside #46's request forms → ledger (DL-005)"). DL-005 is appended and supersedes DL-002 (SARIF routing only) and DL-004. Its Driver names #46's body and `prompt.md` scope. DL-002 and DL-004 are left unedited, as the append-only rule requires. Issue #31 comment 6787071249 corrects "routed to #46" (`get-issue-comments 31`). No other spec file still routes a response form to #46 (Grep `#46` outside `review/`). |
| B2 — Residuals over 10 lines | APPLIED | `## Residuals` is 10 lines; `change.md` is 7,761 B (cap 8,000). That is the predicted 7,756 B plus the 5 B of "`actions`" for "four", so nothing else in the file changed size. |
| C1 — `upload-sarif` on the command line | APPLIED | second bullet, as proposed |
| C2 — secret-bearing responses | APPLIED | last bullet, as proposed |
| D1 — dependabot reason | APPLIED | fourth bullet, as proposed |

## The one wording change ("The `actions` `302` downloads" for "The four `302` downloads")

The new wording is accurate and introduces no defect. `docs/api-reference/github/rest/actions.md` has five `302`
sections:
- the four pending downloads: `actions/download-artifact`, `-job-logs-for-workflow-run`,
  `-step-logs-for-workflow-run-job` and `-workflow-run-attempt-logs`;
- the existing `actions/download-workflow-run-logs`, whose module docstring says it "follows the redirect without the
  credential and returns the archive's bytes".

So the claim holds for all five. The family qualifier also excludes `code-scanning.md` "Get a CodeQL database for a
repository", which documents a `302` (its zip form). The record does not reach that form, because it sends
`ACCEPT_JSON` (AC-3), and the third bullet covers it. No `307` appears in the five reference files.

The first bullet's "the deferral is recorded on #31" is true: comment 6786809421 records DL-003's deferral of
`code-scanning/commit-autofix` and its `None`-mapping follow-up.

## New findings

None.

Verdict: READY
