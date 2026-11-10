# Spec review — issue-2-anchor-gitignore-dirs — iteration 02 (tier S, combined, delta)

Reviewed: the iteration-01 fix sites in `change.md` (B1, B2, B3, C1, C2, D1, the AC-4 restatement) against the
worktree at 69e03ff.

### A1 — the AC-4 test cannot pass on the wording § Files prescribes
Severity: A
Location: change.md § Tests, AC-4 bullet; § Files, both worded replace sentences
Defect: The test requires the section text outside the block to contain "replace", but both prescribed sentences
(new in this revision, from B1 and C1) carry only "REPLACED", and neither PART 3 section contains "replace" in any
case today; on the setup-kiro sentence `'replace' in s` is False and `'REPLACED' in s` is True.
Material-because: AC-4: with T1 and I1 implemented as written, `test_section_says_to_replace_a_slash_free_entry`
stays red after I1 for both prompts, so the wave has no green capture (wrong-behaviour).
Proposed-edit: in § Tests, AC-4 bullet, replace `contains "replace",` with `contains "REPLACED",`. The test stays
red before I1, because neither section contains `REPLACED`.

### D1 — test_layout.py's docstring keeps the old list of historical records
Severity: D
Location: change.md § Files, `test/test_layout.py` bullet
Defect: The module docstring names the unchecked historical records as "docs/reports/, .kiro/specs/, the agent
design notes"; after I1 adds `\.claude/specs/` to `HISTORICAL` the docstring no longer matches the regex.
Proposed-edit: replace `` `HISTORICAL` also matches `\.claude/specs/`: `` with
`` `HISTORICAL` also matches `\.claude/specs/`, and the module docstring lists it: ``

Fix sites with no finding:
- B1: the setup-claude sentence names `reports/` plus the nine AC-3 entries (the AC-3 and DL-001 set) and calls
  itself the exception to Rule 1, whose MERGE "KEEP the existing value" and PRESERVE steps exist in both prompts
  (`### Rule 1: Migration-aware merge`). The restated AC-4 ("an entry PART 3 anchors") agrees with both sentences.
- B2: with A1 applied, the test fails on a sentence that omits `/reports/` or `/lib/`.
- B3: `FRAMEWORK_PATH` matches only tokens under `prompts`, `clients`, `src/hooks`, `src/payload`, `templates`,
  `docs/reports`, `docs/design`, so `Path("docs", "reports", "x.md")` is not read. The other literals the module
  needs resolve (`docs/reports/`, the two `prompts/setup-*.txt`) or sit outside those prefixes (`cdk/lib/stack.ts`,
  `lib/x.py`, `reports/junit.xml`, `frontend/build/x.js`, `tmp/x`), as does `cdk/lib/` in the new prompt text.
- C2 resolution: the only tracked `.claude/specs/` files are the five `_workflow/phases/` copies, already skipped
  as `config/toolchain.json` `files` keys, so the `HISTORICAL` addition removes no live file from any
  `test_layout.py` guard; `test/test_layout.py` is not a toolchain file.
- Iteration-01 D1: "a line of the block (whole-line comparison)" leaves `.eggs/` and the anchored lines passing.
- Security, operability and `E2E: not applicable`: no change since iteration 01 touches them.

## Coverage

| Criterion | Test | Can it fail? |
|---|---|---|
| AC-1 | `test_reports_line_is_anchored_with_its_comment[setup-claude]` | yes, red before I1 |
| AC-2 | `test_reports_line_is_anchored_with_its_comment[setup-kiro]` | yes, red before I1 |
| AC-3 | `test_root_only_packaging_dirs_are_anchored` | yes, red before I1 (`lib/` is a line) |
| AC-4 | `test_section_says_to_replace_a_slash_free_entry[both]` | yes, but red after I1 too until A1 is applied |
| AC-5 | `test_applied_block_ignores_only_the_root_dirs` | yes, `docs/reports/x.md` and `cdk/lib/stack.ts` probes red before I1 |
| UB-1 | AC-5 `reports/junit.xml` and `reports/checks-lint.json` probes | yes, if the line is dropped |
| UB-2 | `test_section_still_adds_only_missing_entries[both]` | yes, if the phrase is removed |
| UB-3 | `test_generated_dirs_stay_slash_free` + `frontend/build/x.js` and `tmp/x` probes | yes, if a line is anchored or dropped |

Verdict: NOT-READY — NOT-CLEAN (1 A, 0 B)
