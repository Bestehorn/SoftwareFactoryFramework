# Review — devops-iac-reviewer — iteration 03 (delta) — issue #13

Iteration-02 findings, verified at the fix sites (no finding): B1 closed. design.md § D2 "Install path" quotes the
Part 5.3 sentence ("The wrapper templates are skeletons; implement the subcommands the project's agents invoke.") and
the Part 6.2 sentence ("The template wrapper scripts are skeletons. The agent should extend them … (see the docstring
in each template)") as they stand in the worktree's `prompts/setup-claude.txt` and `prompts/setup-kiro.txt`. The
restated claim, that the GitLab wrapper serves the minimum set except the metadata and the checklist toggle, holds
against D6: every GitLab verb Part 5.3 and Part 6.2 list (pipeline status/log/wait, issue list/show/create/comment/
close/reopen, label list/create, the claim verbs, mr create/get/checks/approve/merge, delete-branch) has a row, and
the delivery verbs stay on `steward_delegate`. Both "expanded docstrings" pointers (the claim bullet and the PR/merge
bullet) are retargeted to `gitlab_api/`. "(See the wrapper docstrings.)" stays as true as it is today, because D7
keeps the metadata and `toggle_checklist_item` notes. They are a comment block in the current skeleton too. C1 is
routed and checked below. D1 closed: § D2 adds `gitlab_api/` to the setup-kiro APPENDIX tree, and § D7's SSO
sentence names `gitlab_api/transport.py` instead of the docstring's "add that handling here".

### C1 — #17 D8 still keeps GitLab inside the shared "skeletons" sentence
Severity: C
Location: design.md § D2 "Install path" (first bullet); #17 design.md § D8 (third bullet)
Defect: #17 D8 says the sentence in both sections "names the GitLab template only", but this spec says the same
sentence "no longer covers GitLab". The two edits touch the same prompt lines, so whichever lands second has to
resolve a conflict. If #17 lands second and follows its D8 word for word, it calls GitLab a skeleton again. Neither
`test_setup_prompts_gitlab_wrapper.py` nor `test_setup_prompts_github_wrapper.py` pins the sentence. This spec's text
is correct and leaves the GitHub half to #17, so the defect is in #17's artefact.
Proposed-edit: none in this spec. The conductor routes to #17 D8: replace "names the GitLab template only" with "keeps
its GitLab half as #13 D2 restates it (the GitLab wrapper is no longer a skeleton)".

### D1 — The APPENDIX tree entry lacks the host annotation its siblings carry
Severity: D
Location: design.md § D2 "Install path" (third bullet)
Defect: The tree marks `gitlab_wrapper.py  # if GitLab`, and #17 D8 adds `github_api/  # if GitHub`. This spec
names `gitlab_api/` with no annotation.
Proposed-edit: "lists `gitlab_api/  # if GitLab` beside `gitlab_wrapper.py` under `scripts/`".

CLEAN
