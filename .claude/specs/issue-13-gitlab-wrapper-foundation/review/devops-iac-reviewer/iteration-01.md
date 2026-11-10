# Review — devops-iac-reviewer — iteration 01 — issue #13

### B1 — The setup prompts install an entry script that cannot import its package
Severity: B
Location: design.md § Residuals ("Promotion"), § Import bootstrap; requirements.md § Overview "Design inputs" ("the setup prompts copy only that file")
Defect: The design splits the wrapper into `gitlab_wrapper.py` plus `scripts/gitlab_api/` but leaves `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` Part 6.2 copying only `src/payload/scripts/gitlab_wrapper.py`, and routes that copy step to "the promotion of the new wrapper" — but promotion (`prompts/update.txt` run on this repository) installs only here, where the GitLab wrapper is `not_installed`; `prompts/update.txt` names no GitLab wrapper copy for any project, and neither #11 nor #15 carries a work item for it.
Material-because: regression — a GitLab project set up from any release tagged after this merge gets `scripts/gitlab_wrapper.py` without `scripts/gitlab_api/`, so the entry's `from gitlab_api.errors import GitLabAPIError` raises `ModuleNotFoundError`, every subcommand exits 1, and the project's installed `test/test_wrapper_delivery.py` (its `load` runs `exec_module`) errors — where today's skeleton imports only the standard library and that test passes against it.
Proposed-edit: Add after the Layout tree: "Install path (product text, edited in this change): `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` Part 6.2 copy `src/payload/scripts/gitlab_wrapper.py` together with the directory `src/payload/scripts/gitlab_api/` into `scripts/`, and each prompt's shipped-Python list names `scripts/gitlab_api/` beside `scripts/gitlab_wrapper.py`; `test/test_layout.py` `test_every_framework_path_named_in_a_live_file_exists` resolves the new path." In § Residuals delete "the setup prompts' copy step (`prompts/setup-claude.txt` Part 5.3, `prompts/setup-kiro.txt` Part 6.2) and". (`issue-filing-discipline.md` fix-first branch 2: a few lines, no design choice.)

### B2 — The manifest residual states the wrong treatment and routes it to a step that never runs
Severity: B
Location: design.md § Residuals ("Promotion": "`config/toolchain.json` must carry `gitlab_api/`, `gitlab_fake_host.py` and the new suites → the promotion of the new wrapper")
Defect: This repository never installs the GitLab wrapper (`config/toolchain.json` `not_installed`: `src/payload/scripts/gitlab_wrapper.py` — "the repository is on GitHub"), so there is no "promotion of the new wrapper" here, while `scripts/toolchain_manifest.py` on main (507a57e; `installed_files`, LAYOUT row `("src/payload/", "")`) installs every release source under `src/payload/` that `not_installed` does not name.
Material-because: wrong-behaviour — the first promotion of any release containing this change writes `scripts/gitlab_api/**`, `test/gitlab_fake_host.py`, `test/test_gitlab_transport.py` and `test/test_gitlab_commands.py` into `files` while `scripts/gitlab_wrapper.py` stays excluded, so this repository's toolchain and CI carry a GitLab package and the suites of an entry script that is not installed.
Proposed-edit: Replace the manifest half of the residual with: "- Toolchain manifest (this repository): the first promotion of a release containing this change adds `not_installed` entries `src/payload/scripts/gitlab_api/*`, `src/payload/test/gitlab_fake_host.py` and `src/payload/test/test_gitlab_*.py` ('the repository is on GitHub') to `config/toolchain.json` before it runs `scripts/toolchain_manifest.py` (`fnmatch` treats `/` as an ordinary character, so the patterns cover `families/` and part 2's `test_gitlab_family_<family>.py`). Not added in this change: `test/test_toolchain_manifest.py` `test_check_on_the_committed_manifest_exits_zero_and_writes_nothing` regenerates against the pinned release, which drops an entry naming none of its sources. Routed: one findings-ledger row (`python scripts/memory_compile.py ledger add --subject toolchain-manifest ...`) committed with this change, pointing at this residual."

### C1 — The fake host covers only `https`; nothing keeps an `http://` URL off the network
Severity: C
Location: design.md § Testing Strategy ("Transport and records", "Subcommands")
Defect: `FakeHost` subclasses `HTTPSHandler` only, and `build_opener` still adds the default `HTTPHandler` (https://docs.python.org/3.10/library/urllib.request.html, `build_opener`). So a test of the `https`→`http` redirect that § Security Considerations names, or of an `http://` `Link`, opens a real socket, and only the coverage test has a socket guard.
Proposed-edit: "`FakeHost` defines `http_open` as well as `https_open`, both serving the script; both suites install the AC-5.4 `socket.socket.connect` guard as an autouse fixture; the two subprocess tests run `sys.executable` with `cwd=tmp_path`."

### C2 — A 429 sleep inside `pipeline wait` is silent and not bounded by the wait's deadline
Severity: C
Location: design.md § Transport "`429` (AC-3.2–AC-3.4)"; § Entry script handler table, `pipeline wait`
Defect: `_send` sleeps the full `Retry-After` ("Seconds until the quota resets", `conventions.md` "Headers and the 429 response") up to `RATE_LIMIT_RETRIES` times with no log line. Callers run `pipeline wait --timeout-seconds 540` under the 600 s foreground ceiling (`ci-owns-the-test-suite.md`, `parallel-by-default.md`), so a 429 near the deadline can push the call past that ceiling with nothing on standard error. Exit codes 0/10/11 are kept.
Proposed-edit: Add to the `429` paragraph: "Each retry logs one WARNING with the status and the sleep in seconds, never a request header." Bounding the sleep by the wait's remaining time adds a mechanism, so it goes under Residuals.

### C3 — The UB-2 stdlib check uses a 3.10-only attribute in a shipped suite
Severity: C
Location: design.md § Correctness Properties UB-2; § Acceptance Criteria Mapping UB-2 (T `test_standard_library_only`)
Defect: `sys.stdlib_module_names` is new in Python 3.10, and `src/payload/test/` is shipped code held to Python 3.9 (`tech-stack.md`), so the test raises `AttributeError` on a 3.9 interpreter.
Proposed-edit: "`test_standard_library_only` lives in V `test/test_gitlab_wrapper_coverage.py` (framework-only; CI runs 3.10), not in T."

NOT-CLEAN (0 A, 2 B)
