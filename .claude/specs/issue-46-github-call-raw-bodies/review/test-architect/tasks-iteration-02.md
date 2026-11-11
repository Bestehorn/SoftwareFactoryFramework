# Test-architect review — issue #46 tasks, iteration 02 (delta)

## Findings

None. Every iteration-01 fix site is applied, and the edits add no A or B defect.

## Fix sites

- **TA-T-B1, applied.** Waves 1, 2 and 4 now carry
  `python scripts/run_tests.py src/payload/test/test_github_*.py test/test_github_*.py`. Wave 3's line is unchanged.
  This fix also covers the spec lane's C1, which asked for a narrower pattern.
  - **Expansion in Git Bash.** Bash expands both patterns before the native Python starts. Run from the worktree root,
    `run_tests.py --print-command` with this line printed a pytest argv that lists every matching file as its own
    path: K, R, T, C, H, N, V and P on the current pre-rebase HEAD 4c7f007.
  - **What each wave runs.** On origin/main (now 3beba95; PR #49 touched only GitLab), the patterns match 21 files
    under `src/payload/test/` and 4 under `test/`. That is every GitHub suite: T, R, K, C, G, the eleven family suites
    of #27, #29 and #32, and H, N, V and P. The issue-33 branch adds 31 `test_github_api_*.py` suites, M among them,
    and modifies N. Wave 4's line therefore picks them up after the second rebase.
  - **Nothing unwanted is picked up.** The fixture module `github_wrapper_fixtures.py` and the GitLab suites do not
    match. A `git grep` for `sff-test`, `urlopen` and `skipif` in the matched files finds only docstring and comment
    text, so no wave run reaches the forge.
  - **No collection conflicts.** No basename repeats across the two directories, and `pyproject.toml` sets
    `--import-mode=importlib`.
  - **The host-wide suite slot.** `run_tests.needs_slot` is False when every target is an existing file. For this
    line's expansion it printed `needs_slot False`, so `run_tests.py` passes the files to pytest under its bounded `-n`
    and takes no slot. `ci-owns-the-test-suite.md` and `native-tools-over-shell.md` require a slot only for "any run
    wider than named test files", so this complies with the rules.
  - **No empty match.** An empty match would hand pytest the literal pattern. Both directories have matches on
    origin/main, so neither wave can hit that case.
- **TA-T-C1, applied.** 2.1 reads "beside `--input <a file under tmp_path>` on `markdown/render-raw`". The log-record
  oracle of `test_a_raw_body_with_body_members_is_refused` is therefore reached at `cmd_call` step 1, not at argparse.
- **Spec C2, applied.** The second Preconditions bullet now names #33's edits to `commands/call.py`
  (`git diff --name-status origin/main...issue-33-remaining-github-families` lists it as `M`) and to N. Both are on
  the glob line of wave 4, so a bad merge of either goes red in that wave's capture.
- **Spec C3, applied.** 4.2 restates M's docstring, `RESIDUAL_PENDING`'s comment and the module docstring's bullet.
  4.3 now reads "names both records and says `PENDING` is empty". The other 30 #33 suites mention `markdown/render-raw`
  only in a `RESIDUAL_PENDING` comment, and each of them sets its own `RESIDUAL_PENDING = frozenset()`. No assertion
  outside M depends on `markdown.PENDING`, so the wave-4 glob run gains no red test that no task owns.
- **Spec D1, applied.** 2.4 says "`test_a_section_is_read_as_the_reference_writes_it`'s docstring drops "five"".
- **No regression from the edits:**
  - Within each wave, every TEST task still comes before its IMPL tasks.
  - The files each wave owns are still disjoint:
    - wave 1: T, R, K, fx, `transport.py` and `registry.py`;
    - wave 2: K, H, G, N, `call.py` and `repos.py`;
    - wave 3: C, `github_wrapper.py` and the map;
    - wave 4: K, M and `markdown.py`.
  - The glob holds every suite that the Coverage rows and F.2 place "on every Run line" or "in the run of wave 1":
    C, P, K, V and T. Wave 3's line still holds C, K, P, V and B.
  - `tasks.md` is 14,226 B, under its 15,000 B cap.
  - `requirements.md` defines 16 criterion ids. Its other `AC-1.5` and `AC-1.7` strings refer to #28, not to this
    spec.

## Coverage

| Criterion | Test task(s) | Status |
|---|---|---|
| AC-1.1 | 1.1, 2.1; design D1 to D3 | COVERED |
| AC-1.2 | 1.1, 1.2, 2.1, 2.2, 4.1 | COVERED |
| AC-1.3 | 2.1 (input file under `tmp_path`) | COVERED |
| AC-2.1 | 2.1, 2.4 | COVERED |
| AC-2.2 | 1.1, 2.1 | COVERED |
| AC-3.1 | 1.1, 1.3 | COVERED |
| AC-3.2 | 1.1 | COVERED |
| AC-4.1 | 2.3, 2.4, 4.2; N and V on the glob lines of waves 2 and 4 | COVERED |
| AC-4.2 | 2.1 | COVERED |
| AC-4.3 | 4.1 | COVERED |
| AC-5.1 | 3.1; C on wave 3's line | COVERED |
| AC-5.2 | F.3; B on wave 3's line | COVERED |
| UB-1.1 | 1.4, F.2; C, P and K on every Run line | COVERED |
| UB-2.1 | F.2; C on every Run line | COVERED |
| UB-2.2 | 1.1, F.2; T on wave 1's line | COVERED |
| UB-3.1 | F.2; V on every Run line | COVERED |

16 COVERED, 0 GAP. TEST-READY.

Verdict: CLEAN
