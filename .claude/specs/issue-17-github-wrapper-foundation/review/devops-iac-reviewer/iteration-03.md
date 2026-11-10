# Design review — devops-iac-reviewer — iteration 03 (delta)

Fix sites checked in the worktree at 1c69c2a (HEAD equals `origin/main`; only the spec directory is untracked).

## Iteration-02 findings

- C1 (X4 residual): closed. design.md § Residuals now says the promotion leaves `github_api/` out of its
  setup-prompt step while the `not_installed` entries stand. That matches the code and the prompt:
  - `scripts/toolchain_manifest.py` `installed_files` maps every source no entry names through the
    `("src/payload/", "")` LAYOUT row.
  - `test/test_toolchain_integrity.py` `test_an_installed_file_equals_its_source_at_the_release` asserts
    `path.is_file()` for every `files` entry.
  - `prompts/update.txt` § Task step 5 (apply the setup prompt) comes before step 7 (regenerate the manifest).
  - requirements.md § Residuals ("the first promotion after the merge leaves the files out") agrees.
- C2 ("skeletons" sentences): closed. D8's third bullet quotes both sentences as they stand in
  `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` Part 6.2. Of either minimum set, only
  `get-jobs`, `rerun` and `cancel` are missing from the D5 table, as the bullet says, and requirements.md
  § Residuals routes them to #14.
- D1 (docstring pointers, Kiro tree): closed.
  - D8's first bullet now covers all three places in Part 5.3 that send the reader to a docstring: the claim
    bullet, the PR-lifecycle pointer and the checklist bullet. The records it points to exist in the D5 table
    (`checklist`: `issues/get`, `issues/update`).
  - D8's second bullet adds `github_api/` to the APPENDIX "Standard directory structure" tree.
  - Part 6.2's "the template docstrings specify them" can stay: D6 keeps the module docstring, and its usage
    list in `src/payload/scripts/github_wrapper.py` names `wait-run` and all six delivery verbs, every one in
    D5 or D6.
- § Operability "Not applicable" still holds. D8 edits only `prompts/` and adds a test under `test/`. No D8 path is
  a `files` entry of `config/toolchain.json`.

## Findings

None.

CLEAN
