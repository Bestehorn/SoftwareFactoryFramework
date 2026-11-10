# Design review — devops-iac-reviewer — iteration 02 (delta)

## Iteration-01 findings

- B1 — closed. design.md § Residuals (X4) and requirements.md § Residuals carry the restatement. I checked it
  against `scripts/toolchain_manifest.py` at 1c69c2a by calling `derive` on the committed manifest:
  - At the pinned `v2026.11.10.1` all four entries are dropped, so this change cannot commit them.
  - On that release plus the planned paths (including nested `github_api/families/` and `github_api/commands/`
    modules and a part-2 `test_github_api_<family>.py`), `files` gains `scripts/github_api/**`,
    `test/github_wrapper_fixtures.py`, `test/test_github_api_*.py` and `test/test_github_wrapper_compat.py` without
    the entries, and nothing with them. The `scripts/github_wrapper.py` deviation is kept.
  - No pattern names `src/payload/scripts/github_wrapper.py` or `src/payload/test/test_wrapper_delivery.py`.
- C1 — closed by X3 and D8. setup-claude Part 5.3, setup-kiro Part 6.2 and both shipped-Python lists exist where
  D8 names them. Each section ends at a `### Part` heading (5.4 and 6.3), so S can cut them as
  `test/test_setup_prompts_gitignore.py` cuts PART 3.
- C2 — closed. The first bullet of D3 "Failures, in `_send`" logs a WARNING before each wait, and § Security
  Considerations "Waiting" agrees.
- § Operability "Not applicable" holds: every D2 path is product (`src/payload/`, `prompts/`) or a repository test
  in `test/`, and none is a `files` entry of `config/toolchain.json`. CI runs every new test: the `verify` job's
  `tests` leg runs on Python 3.10 (`.github/workflows/ci.yml`), which has X1's `sys.stdlib_module_names`, and
  `pyproject.toml` `testpaths` hold `src/payload/test` and `test`.

## Findings

### C1 — The X4 residual names the manifest tool as the installer, but the promotion copies files in an earlier step that D8 now points at the package
Severity: C
Location: design.md § Residuals (X4 bullet)
Defect: `scripts/toolchain_manifest.py` only lists unnamed sources under `files` (`installed_files`). The copy
  happens in `prompts/update.txt` § Task step 5 ("Apply the setup prompt with the delta as your worklist"), which
  runs before step 7 regenerates the manifest. After D8, that step tells the promoter to copy
  `src/payload/scripts/github_api/` to `scripts/github_api/`. A promoter who copies the package in step 5 and then
  adds the entries leaves `scripts/github_api/` outside the manifest. That is the second `github_api` copy the
  residual leaves for the new wrapper's promotion to settle.
Proposed-edit: replace "(`scripts/toolchain_manifest.py` installs every unnamed `src/payload/` source beside the
  fork)" with "and leaves `github_api/` out of its setup-prompt step although Part 5.3 now copies it
  (`scripts/toolchain_manifest.py` lists every unnamed `src/payload/` source under `files`, and
  `test/test_toolchain_integrity.py` then requires it installed)".

### C2 — The sections D8 edits still call the wrapper templates skeletons for the project to implement
Severity: C
Location: design.md § D8 (first two bullets)
Defect: setup-claude Part 5.3 says "The wrapper templates are skeletons; implement the subcommands the project's
  agents invoke", and setup-kiro Part 6.2 says "The template wrapper scripts are skeletons. The agent should
  extend…". After this change the GitHub wrapper implements UB-1.1's caller-used set. Only `get-jobs`, `rerun` and
  `cancel` of Part 5.3's minimum set remain (requirements § Residuals, part 2). A project set up from the next
  release is therefore told to implement what it was just given, which contradicts D8's stated aim of "a working
  wrapper" (design § Overview).
Proposed-edit: add to D8's first two bullets: "and its 'skeletons' sentence is restated to name the GitLab
  template only; for GitHub it says the wrapper implements the caller-used subcommands and that `get-jobs`, `rerun`
  and `cancel` arrive with part 2 (#14)".

### D1 — Two GitHub-wrapper mentions in the edited prompts still name the entry script alone
Severity: D
Location: design.md § D8
Defect: setup-claude Part 5.3's in-progress-claim bullet ends "See the expanded docstrings in the wrapper
  templates", but the claim endpoints are now in `github_api/commands/claim.py`. setup-kiro's project layout tree
  lists `github_wrapper.py # if GitHub` under `scripts/` with no `github_api/`.
Proposed-edit: extend D8's docstring-pointer edit to the claim bullet's "wrapper templates" sentence, and add
  `github_api/` beside `github_wrapper.py` in setup-kiro's layout tree.

CLEAN
