# Standards review — iteration 01 (whole-artefact)

### B1 — Six #10 support functions are re-implemented with only their constants changed
Severity: B
Location: design.md § D1 "One project per run" and Alternatives, § D3 "The helper", § D8 "Lookup" and "CI", § D10 `SubprocessGitRunner`, `product_wrapper()`; requirements.md § UB-4
Defect: `test/forge/ephemeral.py` `refuse_distributed_run` (`FORGE_COMMAND`), `credential_helper_arguments` (`GITHUB_HELPER_KEY`, `ACCESS_TOKEN_USERNAME`, `CLONE_CREDENTIAL_FILE`), `find_test_credential` and `write_test_credential` (`TEST_CREDENTIAL_FILE`, `SECRET_NAME`), `SubprocessGitRunner.run` (the module-level `credential_helper_arguments`) and `product_wrapper` (`PRODUCT_WRAPPER`, `PRODUCT_WRAPPER_MODULE`) hard-code GitHub constants, so the design redefines each in `test/forge_gitlab/ephemeral.py` with the same logic ("#10 D1's check", "the same reset of the helper list, the same single quoting ... the same `ForgeSetupError`", "#10's, with D3's helper options", "as #10's loader does"); the rejected alternative's reason ("edits the GitHub suite, which the by-path reuse does not need") is untrue for these six, and the clause forcing the copies, UB-4 "every file under `test/forge/` unchanged", is stricter than the ask ("The GitHub forge suite, its job and its tests keep their behaviour"; "Reuse it; deviate only where GitLab differs").
Material-because: unmaintainable-by-rule `coding-standards.md` rules 9 and 10 and `design-principles.md` rule 2 (reuse, no duplication): a later fix to one copy (the helper's quoting, the main-worktree fallback) silently misses the other.
Proposed-edit: requirements.md UB-4: replace "every file under `test/forge/` unchanged" with "every existing call of `test/forge/ephemeral.py` behaving as before". design.md D10 table: add the row "`test/forge/ephemeral.py` | keyword-only parameters, each defaulting to today's GitHub constant: `refuse_distributed_run(command=)`, `credential_helper_arguments(helper_key=, username=, credential_file=)`, `find_test_credential(credential_file=)`, `write_test_credential(credential_file=, secret_name=)`, `SubprocessGitRunner(helper=)`, `product_wrapper(path=, module_name=)`"; D1, D3, D8 and D10 call these with the GitLab constants instead of defining them; delete D1's third Alternative; drop `test/forge/` from D10 "Not edited", from the Overview's "No file under `test/forge/` is edited", and from Correctness Properties UB-4 and the mapping row UB-4 ("the diff under `test/forge/` empty" → "H passes unedited").

### B2 — Both User Prompts sections omit two user messages that drove them
Severity: B
Location: requirements.md § User Prompts; design.md § User Prompts
Defect: `prompts.md` items 5 ("There is no "Service Accounts" submenu in the settings of the group") and 6 ("The group URL is https://gitlab.aws.dev/bestehorn-sff-test") are user messages behind the test group's working value (DL-002), the gitlab.aws.dev Residual (DL-003) and AC-9.1's "the group's Settings > Service accounts", yet both sections replace them with a pointer to `prompts.md`.
Material-because: unmaintainable-by-rule `document-user-prompts.md` rule 1 (the verbatim prompts that drove the document's current state).
Proposed-edit: in both sections insert, after item 3, `4. User, 2026-11-21: "There is no "Service Accounts" submenu in the settings of the group"` and `5. User, 2026-11-22: "The group URL is https://gitlab.aws.dev/bestehorn-sff-test" (issue #11)`; renumber "Use gitlab.com" as 6 and delete its sentence "The operator's other answers (the group, the token, its file, the CI secret) are in `prompts.md`."

### C1 — `ci.yml`'s toolchain status is argued from precedent, not from the manifest
Severity: C
Location: design.md § D5 first paragraph; requirements.md § UB-5
Defect: `project-specific.md`'s table lists `.github/workflows/` as toolchain (changed from `templates/ci/`), while `config/toolchain.json` `not_installed` `templates/ci/*` records ".github/workflows/ci.yml is the project's own"; D5 cites only "#10 D5".
Proposed-edit: D5 "`ci.yml` is this project's own (#10 D5)" → "`ci.yml` is this project's own: no `config/toolchain.json` `files` entry names it, and its `not_installed` entry `templates/ci/*` says so (#10 D5)".

### C2 — Reusing `EXIT_REFUSED` leaves its docstring stale
Severity: C
Location: design.md § D2 (`main` returns `EXIT_REFUSED`), § D10 "Not edited"
Defect: `gitlab_api/commands/_common.py` documents `EXIT_REFUSED` as "the exit code of a `call` refused before any request is sent", D10 leaves that file unedited, and the entry script keeps its own exit constants (`EXIT_OK`, `EXIT_API_ERROR`, `EXIT_DELIVERY_ELSEWHERE = 2`).
Proposed-edit: D2: "returns `EXIT_PROJECT_REFUSED = 2`, a constant of `gitlab_wrapper.py` beside `EXIT_DELIVERY_ELSEWHERE`" (or name `_common.py`'s docstring line in D10).

### C3 — The `project_id` key description stays "numeric"
Severity: C
Location: design.md § D2, last bullet
Defect: the wrapper's Credentials paragraph says `project_id  the numeric project ID (Settings > General)`, but under the marker only the `<namespace>/<path>` form is served; D2 updates only `Exit codes`, `_run` and `main`.
Proposed-edit: append to D2's last bullet: "and the `project_id` key line: a numeric ID or the `<namespace>/<path>` path, the path only while the test marker is set".

### C4 — The GitLab text satisfies three of L's GitHub checks on its own
Severity: C
Location: design.md § D5 "The GitHub layout test", § D7, § D10 `docs/forLLMConsumption.md`
Defect: in L `test_the_map_names_the_forge_suite`, `FORGE_COMMAND` ("... --workers 1 test/forge") is a prefix of the GitLab command, `FORGE_SUITE` ("test/forge") a substring of `test/forge_gitlab`, and `FORGE_JOB_MENTION` matches "GitLab forge job"; in `test_the_setup_note_names_the_credential`, `says_only_local_machines_need_it` is met by AC-9.1's GitLab sentence. After this change each passes without the GitHub text: UB-4's "no assertion weakened" holds in letter, not in effect. D5 says only that the other L tests keep passing.
Proposed-edit: design.md Residuals: add "L's map checks and its local-only sentence check are also met by the GitLab text, so they no longer prove the GitHub mentions alone."

### D1 — Positional call samples
Severity: D
Location: design.md § D2 `json.dumps(project_id)`; § D10 `subprocess.run([sys.executable, ...], ...)`; § Testing Strategy `monkeypatch.setitem(sys._xoptions, TEST_MARKER_OPTION, True)`
Defect: written positionally where the codebase names them (`json.dumps(obj=...)`; `test/forge/ephemeral.py` `_invoke` `subprocess.run(args=...)`; `test_github_wrapper_marker.py` `monkeypatch.setitem(dic=, name=, value=)`), `coding-standards.md` rule 4.
Proposed-edit: write `json.dumps(obj=project_id)`, `subprocess.run(args=[...], ...)`, `monkeypatch.setitem(dic=sys._xoptions, name=TEST_MARKER_OPTION, value=True)`.

Checked and conforming: `test/forge_gitlab/` under `test/` (`file-organization.md`, `test/test_layout.py` `test_python_lives_only_in_src_test_and_scripts`; L's `read_forge_modules` rglobs only `test/forge`); no `config/toolchain.json` file in D10; `GitLabProjectRefusedError(GitLabAPIError)` inherits `details=None` and joins the one hierarchy; the wrapper change uses `sys` and `json` only; the L edit keeps the exact-set assertion with a third member, and neither the `forge-gitlab` guard (`needs.forge-gitlab` fails `FORGE_RESULT`; starts `if`, not `status=`) nor `secrets.SFF_GITLAB_TEST_TOKEN` (`SECRET_REFERENCE`) trips another L test; the one environment read is #10's sanctioned CI step.

NOT-CLEAN (0 A, 2 B)

Counts: A 0, B 2, C 4, D 1

Verdict: NOT-READY
