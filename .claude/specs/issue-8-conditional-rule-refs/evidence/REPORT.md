# Evidence report — issue #8: agents name rules a project may not install

Tier S, one wave (T1, I1). Branch `issue-8-conditional-rule-refs`.

| Criterion | Test (`test/test_agent_rule_references.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 Claude bodies mark every reference `(where installed)` | `test_claude_bodies_mark_conditional_rules[*]` | red/wave-1.txt (5 bodies unmarked); green/wave-1.txt | green |
| AC-2 Kiro bodies do the same | `test_kiro_bodies_mark_conditional_rules[*]` | red/wave-1.txt; green/wave-1.txt | green |
| AC-3 setup prompts state the install conditions and the per-rule agents | `test_setup_claude_states_install_conditions`, `test_setup_kiro_states_install_conditions` | red/wave-1.txt; green/wave-1.txt | green |
| AC-4 an unmarked reference fails a test | the AC-1/AC-2 tests (red before I1; verifier mutants M1, M7) | red/wave-1.txt; verify/refutation-report.md | proven |
| UB-1 the three rules are still named | `test_conditional_rules_still_named[*]` | green/wave-1.txt; verifier M5 | green |
| UB-2 always-installed rules carry no marker | `test_marker_only_on_conditional_rules[*]` | green/wave-1.txt; verifier M2 | green |

Green capture (`# tasks: T1 I1`): the module with `test/test_layout.py`, 138 passed. Red capture (`# tasks: T1`): 12 failed, 70 passed, all assertion errors.

**Verifier.** `adversarial-verifier` VERIFIED: full revert and eight targeted mutants each caught (`verify/refutation-report.md`).

**Whole suite.** The CI run on the pushed head SHA is the regression verdict; run id and SHA are in the PR and the issue's closing comment. CI runs for this batch: target one.

**Residuals.** Four unmarked rule references in setup-prompt prose (not agent bodies) that no criterion covers — recorded as one findings-ledger row. The installed `.claude/agents/` copies change at the next release and promotion.
