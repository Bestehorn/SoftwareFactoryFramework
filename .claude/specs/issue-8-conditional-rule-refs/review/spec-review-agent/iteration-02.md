# Spec review — iteration 02 (tier S, combined mode, delta)

No findings.

Fix sites checked against the current `change.md`:
- B1 — S-AGENTS now gives the per-rule agent list. A grep of the three rule names over `clients/claude/agents/` and
  `clients/kiro/agents/` gives the same mapping in both clients: `aws-config.md` in devops-iac-reviewer and
  security-reviewer, `cdk-deployment-only.md` in devops-iac-reviewer only, and `use-doc-mcp-servers.md` in
  best-practice-reviewer, devops-iac-reviewer, spec-author and spec-conductor. That matches S-AGENTS and the Ask list.
  All five agents are rows of the 8A.1 advanced backlog fleet table in `prompts/setup-kiro.txt`.
- C1 — AC-3 now states containment only, which is what both AC-3 tests check. The placements moved to Files and match
  the prompts. `aws-config.md` and `use-doc-mcp-servers.md` are in the Part 8.2 "Always-on (no `paths:`)" list.
  `cdk-deployment-only.md` is in the "Path-scoped (`paths:`)" list. Both lists end before `### Part 8.2a`. The 8A.1
  fleet table ends before `### 8A.2`, outside the section's bash fences, so each placement falls inside its test slice.
- C2 — AC-4 now covers backticked occurrences, which is what the AC-1 and AC-2 count comparison checks.
- C3 — the Files bullet forbids a line break inside `(where installed)`. The Tests pattern `\s+` still allows a break
  between the rule name and the marker, so the bullet and the Tests paragraph agree.
- D1 — the Residuals reason now covers the `standards-reviewer.json` description.
- No contradiction elsewhere: no Python under the worktree parses Part 8.2 or 8A.1. S-AGENTS names no
  `prompts/`, `clients/`, `src/` or `templates/` path, so `test/test_layout.py` `FRAMEWORK_PATH` does not match it.
  No acceptance-criterion id was added (still AC-1 to AC-4, UB-1 and UB-2), and `change.md` is under the tier-S cap.
- `prompts.md` exists with the run's two entries, as `document-user-prompts.md` requires.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | `test_claude_bodies_mark_conditional_rules` (per Claude body) | a backticked rule name lacks the marker (red before I1) |
| AC-2 | `test_kiro_bodies_mark_conditional_rules` (per Kiro body) | the same in a Kiro body (red before I1) |
| AC-3 | `test_setup_claude_states_install_conditions` | a parenthetical or S-AGENTS is missing from the Part 8.2 slice (red before I1) |
| AC-3 | `test_setup_kiro_states_install_conditions` | a heading line differs, or S-AGENTS is missing from the 8A.1 slice (red before I1) |
| AC-4 | T1's red capture of the AC-1 and AC-2 tests | shows that a backticked occurrence without the marker fails the tests |
| UB-1 | `test_conditional_rules_still_named` (per client, body, heading, rule) | a listed rule leaves its section (green before and after I1) |
| UB-2 | `test_marker_only_on_conditional_rules` | the marker follows any other `*.md` name (green before and after I1) |

All of these are example tests. No criterion quantifies over an input domain, so no property-based test is owed.

Verdict: READY — CLEAN
