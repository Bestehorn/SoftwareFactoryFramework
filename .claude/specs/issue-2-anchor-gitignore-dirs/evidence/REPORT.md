# Evidence report — issue #2: anchor root-only ignore entries

Tier S, one wave (T1, I1). Branch `issue-2-anchor-gitignore-dirs`.

| Criterion | Test (`test/test_setup_prompts_gitignore.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 setup-claude recommends `/reports/` with its comment | `test_reports_line_is_anchored_with_its_comment[setup-claude]` | red/wave-1.txt; green/wave-1.txt | green |
| AC-2 setup-kiro does the same | `test_reports_line_is_anchored_with_its_comment[setup-kiro]` | red; green | green |
| AC-3 the nine root-only packaging entries are anchored | `test_root_only_packaging_dirs_are_anchored` | red; green | green |
| AC-4 both sections say to replace a slash-free entry, forward and not kept | `test_section_says_to_replace_a_slash_free_entry[*]` | red; green; verify (M10, M11, R2–R7 killed) | green |
| AC-5 applied block ignores the root dirs only | `test_applied_block_ignores_only_the_root_dirs[*]` (git check-ignore) | red; green | green |
| UB-1 root `reports/` stays ignored | AC-5 `reports/junit.xml`, `reports/checks-lint.json` probes | green | green |
| UB-2 other entries still added only when missing | `test_section_still_adds_only_missing_entries[*]` | green | green |
| UB-3 `build/`, `dist/`, venvs, `tmp/` stay slash-free | `test_generated_dirs_stay_slash_free`; `frontend/build/x.js`, `tmp/x` probes | green | green |

Green capture (`# tasks: T1 I1`): the module with `test/test_layout.py`, 74 passed; after the rebase onto the trunk (b496691) the module, `test/test_layout.py` and `test/test_agent_rule_references.py` give 156 passed.

**Verifier.** First pass REFUTED AC-4 (a reversed or negated replace sentence kept every pinned word); T1 reopened to pin direction and polarity; re-verification VERIFIED (`verify/refutation-report.md`).

**Whole suite.** The CI run on the pushed head SHA; its id and SHA are in the PR and the closing comment. CI runs for this batch: target one.

**Diff.** `prompts/setup-claude.txt` and `prompts/setup-kiro.txt` PART 3; `test/test_layout.py` `HISTORICAL` +`.claude/specs/` (identical to the change already on the trunk via #3, so the rebase absorbed it).
