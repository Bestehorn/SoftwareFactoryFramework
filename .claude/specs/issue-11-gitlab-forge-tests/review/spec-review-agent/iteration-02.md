# spec-review-agent — design review iteration 02 (delta, report-only)

Fix sites of iteration 01: B1, C1, D1 and D2 are applied as proposed (AC-4.1, D2, W's no-config case; the D6 F:fixture
row; AC-8.6; D6's `--header` records). The changed regions match the code: every `_load_config` refusal is a
`GitLabAPIError` that `main` `_report` maps to 1; `EXIT_DELIVERY_ELSEWHERE = 2` and the docstring's `project_id` key line
exist; `GATED_OPERATIONS` holds `plan#create-an-issue` and `call_operation` refuses it with `EXIT_REFUSED` (2), so W's
subprocess example sends nothing either way. The six functions of `test/forge/ephemeral.py` exist, all keyword-only,
and so do the constants D10 defaults them to. Every existing call (`test/test_forge_support.py`, `test/forge/conftest.py`,
`test/forge/write_credential.py`, `provision`) passes only today's keywords. L `product_wrapper_problems` still holds
(`lines_naming` walks the whole `FunctionDef`, its defaults included). No AC or UB id was added.

### B1 — D1's two-keyword refusal call fails G's reuse of L's `session_fixture_problems`
Severity: B
Location: design.md § D1 "One project per run"; § Correctness Properties AC-1.1 (G
`test_the_session_fixture_wraps_one_provision`); § D10, the `test/forge_gitlab/ephemeral.py` row
Defect: this revision has `ephemeral_project` call the reused `refuse_distributed_run(worker_id=...,
command=GITLAB_FORGE_COMMAND)`. G applies L's `session_fixture_problems`, whose `refusal_problems` calls
`passes_own_worker_id` (`test/test_forge_suite_layout.py`), and that helper returns false unless the call has no positional
argument and exactly one keyword, `worker_id=worker_id`. So G reports "it does not call
`refuse_distributed_run(worker_id=worker_id)`" and fails. L cannot be loosened (UB-4). Same defect as test-architect
iteration-02 (dedupe).
Material-because: AC-1.1 — its structural test fails against D1 as written.
Proposed-edit: (1) in D1, replace "`ephemeral_project` first calls the reused `refuse_distributed_run(worker_id=...,
command=GITLAB_FORGE_COMMAND)`: #10 D1's check" with "`ephemeral_project` first calls
`refuse_distributed_run(worker_id=worker_id)` of `test/forge_gitlab/ephemeral.py`, which calls the reused one with
`command=GITLAB_FORGE_COMMAND` (L's `passes_own_worker_id` admits that one keyword only): #10 D1's check"; (2) in the
D10 `test/forge_gitlab/ephemeral.py` row, replace "the functions of D4, D8 and D9" with "`refuse_distributed_run(*,
worker_id)` (D1); the functions of D4, D8 and D9".

### C1 — D10 leaves the kind of `SubprocessGitRunner`'s `helper` to inference
Severity: C
Location: design.md § D10 "The git runner is the reused `SubprocessGitRunner(clone=..., helper=...)`, its `helper` D3's
call of `credential_helper_arguments`"
Defect: the D10 table makes the default the function `credential_helper_arguments`, and `SubprocessGitRunner.run`
calls it today as `credential_helper_arguments(clone=self.clone)`. "D3's call" can be read as that callable or as
the list one call returns. A list breaks only an authenticated command run through the runner, and no S test runs one
(the real-runner S test is local and unauthenticated), so only F would catch it.
Proposed-edit: replace "its `helper` D3's call of `credential_helper_arguments`" with "its `helper` a callable that
`run` calls as `helper(clone=self.clone)` when `authenticated`: `credential_helper_arguments` with D3's other three
keywords bound (`functools.partial`)".

### C2 — W's subprocess example does not name the configuration it needs
Severity: C
Location: design.md § Correctness Properties AC-4.1, W `test_the_interpreter_option_reaches_the_entry_script`
Defect: under this revision's AC-4.1, a configuration `_load_config` refuses exits 1. So the example exits 2 with the
marker message only if its `tmp_path` holds a `config/gitlab.json` that `_load_config` accepts. Without one,
`_read_config` raises "Missing credentials file" and `main` returns 1. The text names only "a `tmp_path` other than
the repository".
Proposed-edit: replace "the subprocess, in a `tmp_path` other than the repository, runs" with "the subprocess, in a
`tmp_path` other than the repository holding a `config/gitlab.json` that `_load_config` accepts with `project_id`
`"1234"` (`gitlab_wrapper_fixtures` `write_config`), runs".

## Residuals

None.

Verdict: NOT-READY (A 0, B 1, C 2, D 0) — NOT-CLEAN (0 A, 1 B)
