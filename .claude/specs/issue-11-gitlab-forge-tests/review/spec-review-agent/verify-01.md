# spec-review-agent — VERIFY 01 (issue #11, tier M)

Lens: the implemented diff `83a1415..c9a69f8` (`src`, `test`, `.github`, `docs`) conforms to the approved
`design.md` D1 to D10 and `requirements.md` AC-1.1 to AC-9.2, UB-1 to UB-5. The `test/forge_gitlab/forge_*.py`
modules are judged statically: every subcommand option, record ID and path or query parameter they pass is declared by
`gitlab_api/commands/` and `gitlab_api/families/`, and none is in `call.py` `GATED_OPERATIONS`. Their runtime verdict
waits on F.1.

No A or B finding. The guard (`_test_marker_set`, `_is_ephemeral_project`, `_refuse_unless_ephemeral`, its two calls in
`_run`, `main`'s `EXIT_PROJECT_REFUSED`), `GitLabProjectRefusedError`, the keyword-only parameters of
`test/forge/ephemeral.py`, `provision` steps 1 to 8, the teardown guard, the sweep, `SubprocessWrapperRunner`,
`push_branch`, `wait_until_checked`, `conftest.py`, `write_credential.py`, `pytest.ini`, the `forge-gitlab` job, the
`report` verdict and the two docs match their D sections. The diff touches no path that D10 "Not edited" lists. The one
file outside D10's table is `docs/findings-ledger.md`, whose rows `issue-filing-discipline.md` requires.

### C1 — The mergeability wait stops on `approvals_syncing`
Severity: C
Location: `test/forge_gitlab/ephemeral.py` § `UNDECIDED_MERGE_STATUSES` (`design.md` D10 `wait_until_checked`; AC-8.2)
Defect: `wait_until_checked` returns as soon as `detailed_merge_status` is `approvals_syncing`. GitLab documents that
  value as "The merge request's approvals are syncing." (docs.gitlab.com/api/merge_requests/, merge status values).
  `docs/api-reference/gitlab/conventions.md` § "Merge request mergeability, merge and rebase" lists it among the values
  that mean "ask again later". If it comes back, F:subcommands `test_a_merge_request_round_trip` fails its `mergeable`
  assertion when it should have read the merge request again.
Material-because: a risk only. Nobody has yet seen whether gitlab.com returns this value for a new merge request on a
  Free-tier project; F.1 is the first run that can show it. `ci_still_running`, the other transient value on that list,
  cannot occur, because no pipeline runs (AC-1.3).
Proposed-edit: `UNDECIDED_MERGE_STATUSES = ("unchecked", "checking", "preparing", "approvals_syncing")`, and D10's
  `wait_until_checked` bullet reads "none of `unchecked`, `checking`, `preparing` and `approvals_syncing`".

### C2 — `--help` output differs without the marker
Severity: C
Location: `src/payload/scripts/gitlab_wrapper.py` § module docstring (D2) against `requirements.md` § UB-3
Defect: `build_parser` passes `description=__doc__`, so without the marker `gitlab_wrapper.py --help` now also prints
  D2's new `Exit codes` and `project_id` text. UB-3's "the same output ... for every argv" is therefore not literally
  true for `--help`. D2 requires this docstring change. CI run 45033382186 `verify` passed on `c389d46`, so no existing
  test pins the help text.
Material-because: neither a behaviour change nor a regression. The requests and exit codes are unchanged. The only
  issue is that UB-3's wording overstates what the change keeps the same.
Proposed-edit: in UB-3, replace "for every argv as before this change" with "for every argv as before this change, but
  the `--help` text, which D2's docstrings extend".

CLEAN
Counts: A 0, B 0, C 2, D 0
Verdict: READY
