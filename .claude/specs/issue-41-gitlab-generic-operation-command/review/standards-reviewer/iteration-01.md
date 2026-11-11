# Standards review — design iteration 01 (issue #41)

### S-C1 — `GATED_OPERATIONS` re-spells two IDs the command modules already define
Severity: C
Location: design.md § D1 (`GATED_OPERATIONS` bullet); § D8 "This change", `commands/call.py` row
Defect: D1 writes the two gated IDs as text, but each already exists once as a constant of the module that sends it
(`commands/mr.py` `OP_MERGE_MR`, `commands/issue.py` `OP_CREATE_ISSUE`). D6 fixes a renamed anchor in "the record's
`operation_id`" and the compatibility command. A second spelling in `call.py` survives that fix, and the renamed ID
then passes `call`. K `test_a_gated_operation_names_its_subcommand` uses the old ID, so it still passes.
Proposed-edit: in D1 replace "`call.py`'s `GATED_OPERATIONS` maps `ai-coding#merge-a-merge-request` to `mr merge` and
`plan#create-an-issue` to `issue create`." with "`call.py`'s `GATED_OPERATIONS` maps `mr.OP_MERGE_MR`
(`ai-coding#merge-a-merge-request`) to `mr merge` and `issue.OP_CREATE_ISSUE` (`plan#create-an-issue`) to
`issue create`. It imports both from those modules, so each ID is spelled once."

### S-C2 — The fixtures' new helpers restate three of C's, and D8 does not say so
Severity: C
Location: design.md § D8 "This change", `src/payload/test/gitlab_wrapper_fixtures.py` row
Defect: `load_wrapper(*, module_name)`, `write_config(*, root, config)` and `run_main(*, wrapper, argv)` do what
`test_gitlab_wrapper_compat.py`'s `load_wrapper`, `write_json` and `main_exit_code` already do. C keeps its copies
(Correctness Properties UB-1.1: "the PR diff changes no existing line of C"), but D8 does not say that the two sets
exist side by side or why. An implementer could therefore change C to use the shared copies, which breaks that
verification, or leave the duplicate unexplained.
Proposed-edit: append to the row: "C keeps its own `load_wrapper`, `write_json` and `main_exit_code` unedited
(UB-1.1); K and N use these."

### S-C3 — `_common.py` gains `print_bytes` and `EXIT_REFUSED`, but its docstring is not updated
Severity: C
Location: design.md § D8 "This change", `commands/_common.py` row
Defect: `_common.py`'s module docstring lists what the module holds and calls `print_json` "the one way a subcommand
writes its result". `print_bytes` makes that sentence false. D8 adds both names without the docstring change and
gives no signature for `print_bytes`. `print_json` and every other `_common` helper are keyword-only
(`print_json(*, value)`, `add_command(*, ...)`).
Proposed-edit: replace the row's change cell with "adds `EXIT_REFUSED` and `print_bytes(*, body)`, keyword-only as
`print_json` is; its module docstring names both output forms and `EXIT_REFUSED`".

### S-D1 — The handler name follows `github_api`, not `gitlab_api`
Severity: D
Location: design.md § D2 "`cmd_call(...)`"; § D8 `commands/call.py` row; § Acceptance Criteria Mapping
Defect: every GitLab handler is named verb then object (`branch.delete_branch`, `mr.merge_mr`, `issue.list_issues`,
`pipeline.status_pipelines`). The `cmd_` prefix belongs to `github_api.commands`.
Proposed-edit: rename `cmd_call` to `call_operation` throughout design.md.

Verdict: CLEAN
