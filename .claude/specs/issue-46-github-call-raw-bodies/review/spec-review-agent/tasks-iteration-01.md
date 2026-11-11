# Spec review — issue #46, tasks iteration 01 (SPEC lane)

### C1 — Three Run lines omit family suites that run through the changed fixtures and `call`
Severity: C
Location: tasks.md § Wave 1 Run; § Wave 2 Run; § Wave 4 Run
Defect: Every family suite runs its cases through `fx.run_product_case`, which reaches `assert_outcome` →
`NonGetRequest.of` (1.4), `cmd_call` (2.5) and the `RestOperation` records (1.5). Wave 1's Run line names the eight
family suites of #27 and #32 but not #29's `test_github_api_apps.py`, `test_github_api_orgs.py`,
`test_github_api_teams.py` and `test_github_api_users.py`, which are on origin/main since fe79965 and each call
`fx.run_product_case`. Wave 2's Run line names only G of them. Wave 4's names none of #33's 31 suites, which first
meet the code of waves 1 to 3 at the second rebase. Adding the paths one by one would take tasks.md (14,846 B) over
its 15,000 B cap.
Material-because: not A/B. CI's `tests` leg runs every suite before the merge (`ci-owns-the-test-suite.md`), so the gap
costs a CI run, not a shipped regression. Still, a wave's capture is not the affected set that `post-activity.md`
step 1 names.
Proposed-edit: in the Run lines of waves 1, 2 and 4, replace every `src/payload/test/test_github_api_<name>.py` path
with the one pattern `src/payload/test/test_github_api_*.py`. The shell expands it to every such file present at the
wave, so T, R, K, G and M stay covered. The edit makes tasks.md shorter.

### C2 — The wave-4 rebase replays 2.4's and 2.5's edits over #33's edits to the same files
Severity: C
Location: tasks.md § Preconditions, second bullet
Defect: #33 also edits `commands/call.py` (the module docstring's refusal paragraph, `GATED_OPERATIONS` and its
comment) and N (step 3 of `test_an_unreachable_call_matches_its_reference_section`). Evidence: #33 change.md § Files,
and commit 7bd0b7d in the #33 worktree. 2.5 rewrites that module docstring and 2.4 edits N, both before the second
rebase. The bullet names only `markdown.py` and M as #33's files, so it does not cover a conflict in those two
files.
Proposed-edit: replace "G and M are re-read then (D4). Waves 1 to 3 touch neither `markdown.py` nor M." with "G and M
are re-read then (D4). #33 also edits `commands/call.py` and N, which 2.5 and 2.4 edit: the rebase keeps #33's
`GATED_OPERATIONS` entries, its docstring clause and N's step 3 alongside this branch's edits. Waves 1 to 3 touch
neither `markdown.py` nor M."

### C3 — Wave 4 empties `markdown.PENDING` but keeps texts saying `render-raw` is pending or `render` is the only record
Severity: C
Location: tasks.md § 4.2, § 4.3
Defect: In #33's M, three texts go stale and 4.2 does not restate them:
- the module docstring's `RESIDUAL_PENDING` bullet ("stays pending for #46 … so the family's one record is
  `markdown/render`");
- the comment above `RESIDUAL_PENDING`;
- the docstring of `test_only_the_residual_ids_are_pending` ("`markdown.PENDING` is exactly
  `{"markdown/render-raw"}`").

In #33's `markdown.py`, 4.3's "the docstring says so" covers the `PENDING` sentence. It does not cover "The one
record, `markdown/render`", which is false once there are two records. 2.3 restates G's equivalent texts.
Proposed-edit: 4.2: after "drops `markdown/render-raw` from its residual set," insert "and its docstring,
`RESIDUAL_PENDING`'s comment and the module docstring's `RESIDUAL_PENDING` bullet no longer say it is pending,". 4.3:
replace "and the docstring says so" with "and the docstring names both records and says `PENDING` is empty".

### D1 — N's reader test docstring counts "D5's five sections"
Severity: D
Location: tasks.md § 2.4
Defect: The docstring of `test_a_section_is_read_as_the_reference_writes_it` reads "D5's five sections as the
reference writes them". 2.4 adds a sixth `READ_SECTIONS` entry.
Proposed-edit: append to 2.4's first sentence: "; that test's docstring drops 'five'".

Verdict: READY
