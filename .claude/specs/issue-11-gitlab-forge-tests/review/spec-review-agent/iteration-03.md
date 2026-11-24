# spec-review-agent — design review iteration 03 (delta, report-only)

Fix sites of iteration 02, checked against the code:

- B1 is resolved. `passes_own_worker_id` (`test/test_forge_suite_layout.py`) admits a call with no positional argument
  and exactly `worker_id=worker_id`, and `the_refusal` finds the call through `called_name`, which takes the attribute
  of `EPHEMERAL.refuse_distributed_run(...)`, the spelling `test/forge/conftest.py` `ephemeral_repository` uses. D1's
  one-keyword call therefore passes `refusal_problems` and `session_fixture_problems`. The two-keyword call to the reused
  function sits in `test/forge_gitlab/ephemeral.py`, outside the fixture body G walks. The GitLab module's function of
  the same name follows the same pattern as its `product_wrapper()`, which passed earlier review.
- C1 is resolved. `SubprocessGitRunner.run` calls `credential_helper_arguments(clone=self.clone)` only when
  `authenticated`. A `functools.partial` that binds the three new keyword-only parameters answers
  `helper(clone=self.clone)` the same way. The layout test names neither `credential_helper_arguments` nor
  `SubprocessGitRunner` (grep), so the default `helper=credential_helper_arguments` does not change L.
- C2 is resolved. `gitlab_wrapper.py` `CONFIG_FILE = Path("config") / "gitlab.json"` is resolved against the working
  directory. `_load_config` needs `hostname`, `project_id` and `token`, and `write_config(*, root, config)` writes any
  mapping. With `project_id` `"1234"`, the guard refuses with exit 2 before `call`'s gate does. That matches the
  example's "only the message tells them apart".
- The UB-4 restatement matches D10's `test/forge/ephemeral.py` row. It keeps every default at today's value, and the
  refusal message words still hold for `test_forge_support.py`'s `--workers 1` assertion. The requirements diff touches
  UB-4 only, and no AC or UB id was added.
- The new concurrency sentence matches `ci.yml` (`cancel-in-progress: ${{ github.event_name == 'pull_request' }}`) and
  docs.github.com "Control workflow concurrency": "By default, any existing `pending` job or workflow in the same
  concurrency group will be canceled".
- The design Residuals are now 8 lines. The two moved items exist as ledger rows (`memory_compile.py search`: "forge-gitlab
  rate limit", "forge-gitlab git helper").

### C1 — The GitLab clone helper that S tests has no name
Severity: C
Location: design.md § D10, the `SubprocessGitRunner` bullet and the `test/forge_gitlab/ephemeral.py` row; § Correctness
Properties AC-6.3, S `test_the_credential_helper_answers_git_with_the_clone_token`
Defect: this revision has S test "through the `helper` that `test/forge_gitlab/ephemeral.py` gives
`SubprocessGitRunner`", but neither the D10 bullet nor the row names that callable. The runners are built in
`conftest.py` `ephemeral_project` (D9: "#10's shape ... both runners bound to `<workspace>/clone`"), and S loads only
`ephemeral.py`. If the implementation writes the `functools.partial` inline in `ephemeral_project`, S tests a helper of
its own making, and only F checks the fixture's wiring.
Proposed-edit: in the D10 bullet, replace "bound (`functools.partial`)." with "bound (`functools.partial`): the module
constant `CLONE_GIT_HELPER`, which `ephemeral_project` passes as `SubprocessGitRunner(clone=clone,
helper=EPHEMERAL.CLONE_GIT_HELPER)` and S calls as `CLONE_GIT_HELPER(clone=...)`."; in the
`test/forge_gitlab/ephemeral.py` row, replace "`SubprocessWrapperRunner`;" with "`SubprocessWrapperRunner`;
`CLONE_GIT_HELPER`;".

## Residuals

None.

Verdict: READY (A 0, B 0, C 1, D 0) — CLEAN
