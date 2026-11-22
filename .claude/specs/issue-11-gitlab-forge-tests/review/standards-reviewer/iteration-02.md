# Standards review — iteration 02 (delta: c6cb2ad..5e04f25)

### B1 — D1's two-keyword refusal call fails the L helper that AC-1.1's G test applies
Severity: B
Location: design.md § D1 "One project per run"; § Correctness Properties AC-1.1; § D10 `test/forge_gitlab/ephemeral.py` row
Defect: this revision (applying standards B1) has `ephemeral_project` call the reused `refuse_distributed_run(worker_id=..., command=GITLAB_FORGE_COMMAND)`, but AC-1.1's G `test_the_session_fixture_wraps_one_provision` runs L's `session_fixture_problems` on that fixture, whose `refusal_problems` uses `passes_own_worker_id` (`test/test_forge_suite_layout.py`: `if call.args or len(call.keywords) != 1: return False`; `called_name` matches `f(...)` and `obj.f(...)` alike), so G reports "it does not call `refuse_distributed_run(worker_id=worker_id)`" against the fixture D1 specifies.
Material-because: AC-1.1 — its structural test fails on the design's own fixture, and passing it would mean loosening L's helper, which UB-4 forbids ("no assertion removed or weakened").
Proposed-edit: D1 bullet → "**One project per run.** `--workers 1`, and `ephemeral_project` first calls `refuse_distributed_run(worker_id=worker_id)` of `test/forge_gitlab/ephemeral.py`, which calls the reused `refuse_distributed_run(worker_id=worker_id, command=GITLAB_FORGE_COMMAND)`: #10 D1's check against `CONTROLLER_WORKER_ID`, its message naming D1's command, called with the one keyword L's `passes_own_worker_id` accepts." D10 `test/forge_gitlab/ephemeral.py` row: "the functions of D4, D8 and D9" → "the functions of D1 (the forwarding refusal), D4, D8 and D9".

### B2 — design.md `## Residuals` is over the ten-line cap
Severity: B
Location: design.md § Residuals
Defect: this revision grew the section to sixteen lines in nine bullets, against `proportionality.md` "Scope freeze" ("recorded in `## Residuals` (≤ 10 lines), routed per `issue-filing-discipline.md`"). Two bullets repeat what is already said: `report`'s `if: always()` and the action pins are #10's Residuals, and Operability "Leftovers" already says an interrupted local run leaves its workspace "as #10". Two are sub-threshold by `issue-filing-discipline.md` ("this could go wrong" / "not hardened against X"): a gitlab.com per-user limit "not yet in effect", and the helpers git asks on an unauthenticated command. The route for those two is the findings ledger, not the spec. requirements.md § Residuals has eight lines and is within the cap.
Material-because: unmaintainable-by-rule `proportionality.md` (Scope freeze, ten-line Residuals cap) and `issue-filing-discipline.md` (sub-threshold findings go to `docs/findings-ledger.md`, written only with `memory_compile.py ledger add` and committed in the change they came from).
Proposed-edit: delete the bullets "`report` keeps `if: always()` and the workflow's action pins stay as they are (#10 Residuals)." and "Nothing here removes an interrupted local run's workspace; in a session, `/close-session`'s `reap_agent_temp.py --scoped-temp tmp/os-temp --apply` empties it, as for #10."; replace the bullets "Concurrent runs would share gitlab.com's proposed per-user request limit, …" and "A git command run without `authenticated` asks the machine's configured helpers; …" with the two-line bullet "- Findings-ledger rows (`python scripts/memory_compile.py ledger add`, this change): gitlab.com's proposed per-user limits under concurrent runs; git's configured helpers asked by an unauthenticated command." The section then has ten lines.

### C1 — `helper` is a callable in the D10 row and a list in the D10 bullet
Severity: C
Location: design.md § D10 `test/forge/ephemeral.py` row; § D10 bullet "The git runner"
Defect: the row's default for `SubprocessGitRunner(helper=)` is `credential_helper_arguments`, a callable that `run` calls with `clone=` on each authenticated command, as `SubprocessGitRunner.run` does today. The bullet passes "D3's call of `credential_helper_arguments`", which is its result, a `List[str]`.
Proposed-edit: bullet → "The git runner is the reused `SubprocessGitRunner(clone=..., helper=...)`, its `helper` the callable `functools.partial(credential_helper_arguments, helper_key=GITLAB_HELPER_KEY, username=GIT_USERNAME, credential_file=CLONE_GIT_TOKEN_FILE)`, which `run` calls with `clone=` as it calls the default."

### C2 — UB-4's "change only by keyword-only parameters" leaves out their use and the docstrings
Severity: C
Location: requirements.md § UB-4; design.md § D10 `test/forge/ephemeral.py` row
Defect: the six bodies must read the new parameters (for example, `credential_helper_arguments` builds its path from `CLONE_CREDENTIAL_FILE`). Their docstrings name GitHub ("authenticate to github.com", "D3's helper options"). `SubprocessGitRunner`'s default is a function, not a constant. Read literally, "the file SHALL change only by keyword-only parameters that default to its GitHub constants" forbids the body and docstring edits the parameters need.
Proposed-edit: UB-4 → "the file SHALL change only by keyword-only parameters that default to today's values (its GitHub constants; `credential_helper_arguments` for `SubprocessGitRunner`), their use in the six bodies and the docstrings that describe them (`design.md` D10)".

### D1 — The reused refusals keep #10's nouns
Severity: D
Location: design.md § D8 "Lookup"; § D1
Defect: `find_test_credential`'s refusal says "Paste the test organization's token" and `refuse_distributed_run`'s says "each worker would create its own repository", so the GitLab suite will print these words about a group and a project.
Proposed-edit: append to the D10 `test/forge/ephemeral.py` row: "; the refusal messages keep #10's words (\"test organization\", \"repository\")".

Checked and conforming at the fix sites:
- B2 of iteration 01: both User Prompts sections now quote the two operator messages verbatim.
- C2 of iteration 01: `EXIT_PROJECT_REFUSED = 2` sits beside `gitlab_wrapper.py`'s `EXIT_DELIVERY_ELSEWHERE = 2`.
- C3 of iteration 01: the wrapper has the `project_id` key line ("the numeric project ID (Settings > General)") that D2 now rewrites.
- L `product_wrapper_problems` still finds `PRODUCT_WRAPPER` in `product_wrapper`, because a parameter default lies inside the `FunctionDef` it walks, and still finds it in `SubprocessWrapperRunner`.
- H patches only `subprocess.run`, `shutil`, `time` and `sys.modules` (under its own key). Defaults bound at definition time therefore change none of H's calls, and "H passes unedited" holds.
- The positional samples of D1 (iteration 01) are now named.
- The row's `<!-- pragma: allowlist secret -->` follows the issue-10 and issue-17 designs.
- C1 (iteration 01) now cites `config/toolchain.json`.

NOT-CLEAN (0 A, 2 B)

Counts: A 0, B 2, C 2, D 1

Verdict: NOT-READY
