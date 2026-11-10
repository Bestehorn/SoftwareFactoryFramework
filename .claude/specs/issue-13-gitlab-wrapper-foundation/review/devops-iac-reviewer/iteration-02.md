# Review — devops-iac-reviewer — iteration 02 (delta) — issue #13

Iteration-01 findings, verified at the fix sites (no finding): B1 closed — § D2 "Install path" edits setup-claude Part 5.3,
setup-kiro Part 6.2 and both shipped-Python lists, S pins them, and `test/test_layout.py` `resolves` accepts the directory
token `src/payload/scripts/gitlab_api/` (`(ROOT / token).exists()`). B2 closed — at 1c69c2a `scripts/toolchain_manifest.py`
maps every `src/payload/` source (LAYOUT `("src/payload/", "")`) unless `names` matches a previous-manifest
`not_installed` entry by `fnmatch.fnmatchcase`, whose `*` spans `/`, so the three patterns cover `families/`, `commands/`
and part 2's `test_gitlab_api_<family>.py`; entries added now would be dropped by `derive` (`kept_not_installed`) and fail
`test_check_on_the_committed_manifest_exits_zero_and_writes_nothing`, so the promotion is the step. C1–C3 applied (CI runs
`test/` on Python 3.10 with `.[dev]`, `.github/workflows/ci.yml`).

### B1 — The GitLab text beside the edited copy steps still describes the removed skeleton
Severity: B
Location: design.md § D2 "Install path", § D7 "Removed"; prompts/setup-claude.txt Part 5.3 "Required wrapper subcommands"; prompts/setup-kiro.txt Part 6.2
Defect: The design edits only the copy steps and lists, so after D7 removes the implementation-notes block and `main` serves UB-1's set, setup-claude Part 5.3 still says "The wrapper templates are skeletons; implement the subcommands the project's agents invoke" and points three times at that removed block ("See the expanded docstrings in the wrapper templates", "the expanded docstrings in … `src/payload/scripts/gitlab_wrapper.py` for the exact REST endpoints and the \"can't approve your own PR/MR\" caveat", "(See the wrapper docstrings.)"), and setup-kiro Part 6.2 still says "The template wrapper scripts are skeletons … (see the docstring in each template)" — where #17 D8 retargets the same pointer for GitHub and § "Differences from #17" has no row for not doing so (X2).
Material-because: regression — a GitLab project set up from the next release is told its working wrapper is a skeleton to implement, and the checklist toggle that Part 5.3 calls "required, on both hosts" and part 1 does not build (requirements.md § Residuals → #15) loses the only GitLab implementation note the prompt points to (`toggle_checklist_item`, with the due-date, `add_spent_time` and parent-link notes).
Proposed-edit: Append to § D2 "Install path": "Beside the copy steps the same edit restates the GitLab text, as #17 D8 does the GitHub text: in setup-claude Part 5.3 'The wrapper templates are skeletons; implement the subcommands the project's agents invoke.' becomes 'The GitHub wrapper template is a skeleton; implement the subcommands the project's agents invoke. The GitLab wrapper serves the minimum set below except the issue metadata and the checklist toggle (#15), which a project adds as a module of `scripts/gitlab_api/commands/` defining `register(subparsers)`.', and setup-kiro Part 6.2's 'The template wrapper scripts are skeletons. The agent should extend them …' says the same; Part 5.3's pointers to the GitLab wrapper's 'expanded docstrings' name `src/payload/scripts/gitlab_api/` (the endpoints are its records; `commands/mr.py`'s docstring carries the own-MR approval caveat of the D6 `mr approve` row)." In § D7 replace "its field constants and its implementation-notes comment block" with "its field constants, and its implementation-notes comment block except the issue-metadata and checklist-toggle notes (due date, time spent, parent link, `toggle_checklist_item`), which stay as a comment in the entry script until #15 builds those subcommands".

### C1 — The restated Part 5.3 sentence is shared with #17
Severity: C
Location: design.md § D2 "Install path"; #17 design.md § D8
Defect: #17 D8 also edits Part 5.3 and Part 6.2 but leaves the "skeletons" sentence, which becomes false for GitHub when #17's wrapper lands; B1's edit keeps the GitHub half as it is.
Proposed-edit: none in this spec — the conductor routes the GitHub half of the sentence to #17 under X3.

### D1 — Two more places still describe the one-file skeleton
Severity: D
Location: prompts/setup-kiro.txt § APPENDIX "Standard directory structure" (`scripts/` tree); design.md § D7 (kept usage docstring)
Defect: The tree lists `gitlab_wrapper.py # if GitLab` with no `gitlab_api/`; the kept docstring says SSO cookie handling is added "here", in the entry script, which after D4 belongs in `gitlab_api/transport.py`.
Proposed-edit: Add to § D2 "Install path": "the setup-kiro appendix tree lists `gitlab_api/` beside `gitlab_wrapper.py`"; add to § D7: "the docstring's SSO sentence names `gitlab_api/transport.py` as the extension point".

NOT-CLEAN (0 A, 1 B)
