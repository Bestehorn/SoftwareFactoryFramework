# Spec review — issue-2-anchor-gitignore-dirs — iteration 01 (tier S, combined)

Reviewed: `change.md` against the worktree at 69e03ff (context: `prompt.md`, DL-001, `qa_log.md`).

### B1 — setup-claude's replace sentence misses the anchored entries it takes from the Kiro standard
Severity: B
Location: change.md § Files (`prompts/setup-claude.txt` bullet); AC-4
Defect: setup-claude PART 3 applies "the standard Python/venv/IDE/testing/AWS/temp entries from the Kiro standard" (the setup-kiro PART 3 block, which after I1 anchors `/lib/` to `/wheels/`) in addition to its own block, but § Files limits the replace sentence to the `reports/` line of its own block. An existing Claude project that carries the slash-free `lib/` from GitHub's `Python.gitignore` therefore keeps it, because of "add only those missing" and Rule 1 MERGE ("When it would change an existing value, KEEP the existing value").
Evidence: setup-claude.txt header ("Claude Code counterpart of prompts/setup-kiro.txt"), `## PART 3 — .gitignore`, `### Rule 1`; github/gitignore `Python.gitignore` "Distribution / packaging" lists `lib/` to `wheels/` slash-free.
Material-because: AC-4 ("the PART 3 section of each prompt SHALL instruct the project to replace that line"). setup-claude PART 3 is the only `.gitignore` instruction a Claude project gets, so the replacement never happens there and `cdk/lib/` stays ignored (wrong-behaviour). On the point you asked me to judge: yes, the setup-claude sentence must name these entries for AC-4 to hold.
Proposed-edit: in § Files, setup-claude bullet, replace `the replace sentence beside "Apply Rule 1. Read existing entries, add only those missing".` with `the replace sentence beside "Apply Rule 1. Read existing entries, add only those missing", worded:`
> Exception to Rule 1's keep-the-existing-value: an existing line that is the slash-free form of an anchored entry — `reports/` below, or `lib/`, `lib64/`, `var/`, `downloads/`, `eggs/`, `develop-eggs/`, `parts/`, `sdist/` or `wheels/` from the Kiro standard — is REPLACED by the same entry with a leading slash (`reports/` → `/reports/`, `lib/` → `/lib/`), not kept beside it: the slash-free form also ignores a nested directory of that name, such as `docs/reports/` or `cdk/lib/`.

### B2 — the AC-4 test passes when the replace sentence names only reports/
Severity: B
Location: change.md § Tests, AC-4 bullet
Defect: The test checks only for "replace" and `/reports/` outside the fenced block. A sentence that names only `reports/` therefore passes for both prompts, even though the setup-kiro block anchors nine more entries (AC-3) and setup-claude applies them (B1).
Material-because: AC-4 is untested for the packaging entries: the test stays green on an implementation that leaves `lib/` in place.
Proposed-edit: replace `the section text outside the fenced block contains "replace" and `/reports/`. Example.` with `the section text outside the fenced block contains "replace", `/reports/` and `/lib/`. Example.`

### B3 — the new test module turns test/test_layout.py red
Severity: B
Location: change.md § Tests (the `docs/reports/x.md` probe of the AC-5 test); § Files `test/test_setup_prompts_gitignore.py`
Defect: `test_every_framework_path_named_in_a_live_file_exists` scans every tracked file except `HISTORICAL`, `test/test_layout.py` and the toolchain files. Its `FRAMEWORK_PATH` pattern reads the probe literal `"docs/reports/x.md"` as a framework path, and that path does not exist. I ran the pattern on the literal: `'docs/reports/x.md' MISSING`. The prompt comment's `docs/reports/` resolves.
Material-because: regression: committing the module as written makes an existing test fail (`tests-must-not-fail.md`).
Proposed-edit: append to the § Tests paragraph, after "(git-check-ignore(1), … https://git-scm.com/docs/git-check-ignore).": `The module builds the docs/reports/x.md probe from its parts (Path("docs", "reports", "x.md").as_posix()), so test/test_layout.py test_every_framework_path_named_in_a_live_file_exists does not read it as a framework path.`

### C1 — the replace sentence contradicts "Apply Rule 1" unless it says it is the exception
Severity: C
Location: change.md § Files (`prompts/setup-kiro.txt` bullet); AC-4
Defect: Both sections open with "Apply Rule 1". Its MERGE step keeps an existing value and its PRESERVE step forbids overwriting, so a replace sentence that does not call itself the exception leaves two conflicting instructions.
Proposed-edit: in § Files, setup-kiro bullet, after `the replace sentence beside "Apply Rule 1. Read existing entries, add only those that are missing"` insert `, worded:`
> Exception to Rule 1's keep-the-existing-value: an existing line that is the slash-free form of an entry below that starts with `/` is REPLACED by that entry (`reports/` → `/reports/`, `lib/` → `/lib/`), not kept beside it: the slash-free form also ignores a nested directory of that name, such as `docs/reports/` or `cdk/lib/`.

### C2 — committing the spec directory trips the same guard
Severity: C
Location: change.md AC-5 and § Tests; prompt.md § Scope
Defect: `.claude/specs/` is not in `HISTORICAL`, so if this spec directory is committed, `docs/reports/x.md` in change.md and prompt.md fails the same test as B3. Today `git ls-files .claude/specs` lists only `_workflow/`.
Proposed-edit: no edit while the directory stays uncommitted. If it is committed, write the spec-text probe as `docs/reports/<name>.md`: `resolves()` treats `<` as a placeholder and checks only `docs/reports/`.

### C3 — prompts.md is absent
Severity: C
Location: spec directory
Defect: `document-user-prompts.md` item 2 requires a `prompts.md` holding the full chronological conversation. The directory holds only `prompt.md` and `qa_log.md`.
Proposed-edit: the conductor writes `prompts.md` with the run prompt and the issue #2 body, verbatim.

### D1 — AC-3 test: line check or substring check
Severity: D
Location: change.md § Tests, AC-3 bullet
Defect: "none of its slash-free forms is" does not say whether it checks whole lines or substrings. A substring check fails on `/lib/` itself and on `.eggs/` and `/develop-eggs/`.
Proposed-edit: replace `none of its slash-free forms is` with `none of its slash-free forms is a line of the block`.

Other lenses, no finding:
- Security: the credentials and config lines are unchanged, and no auth, IAM, secret or input handling is touched.
- Operability: CI artifact paths name `reports/` explicitly. `E2E: not applicable` holds because the change is prompt text only.
- Probe design: confirmed in this worktree. `git check-ignore --no-index -q` gives exit 0 for `reports/junit.xml` and for a path under a directory that does not exist, exit 1 for `docs/reports/x.md`, and exit 128 with "--quiet is only valid with a single pathname" for two paths.

## Coverage

| Criterion | Test | Can it fail? |
|---|---|---|
| AC-1 | `test_reports_line_is_anchored_with_its_comment[setup-claude]` | yes, red before I1 |
| AC-2 | `test_reports_line_is_anchored_with_its_comment[setup-kiro]` | yes, red before I1 |
| AC-3 | `test_root_only_packaging_dirs_are_anchored` | yes, red before I1 (`lib/` present) |
| AC-4 | `test_section_says_to_replace_a_slash_free_entry[both]` | only for `reports/` until B2 is applied |
| AC-5 | `test_applied_block_ignores_only_the_root_dirs` | yes, `docs/reports/x.md` and `cdk/lib/stack.ts` probes red before I1 |
| UB-1 | AC-5 `reports/junit.xml` and `reports/checks-lint.json` probes | yes, if the line is dropped |
| UB-2 | `test_section_still_adds_only_missing_entries[both]` | yes, if the phrase is removed |
| UB-3 | `test_generated_dirs_stay_slash_free` + `frontend/build/x.js` and `tmp/x` probes | yes, if a line is anchored or dropped |

Verdict: NOT-READY — NOT-CLEAN (0 A, 3 B)
