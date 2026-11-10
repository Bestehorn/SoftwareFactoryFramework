# Spec review — iteration 01 (tier S, combined mode)

### B1 — S-AGENTS does not name, per rule, the agents that reference it
Severity: B
Location: change.md § Ask (S-AGENTS), as required by § Acceptance criteria AC-3
Defect: S-AGENTS names the five agents as one group for all three rules. Read rule by rule, it lists agents that do not
reference that rule: `spec-author`, `spec-conductor` and `best-practice-reviewer` never name `aws-config.md`, and only
`devops-iac-reviewer` names `cdk-deployment-only.md`. AC-3's own lead-in ("each rule's install condition and the agents
that reference it") and issue #8 AC-3 ("for each of the three rules ... the agents that reference it") both ask for the
per-rule list. A grep of the three names over both clients' agent bodies gives this mapping: `aws-config.md` is named by
devops-iac-reviewer and security-reviewer (`# Binding rules`), `cdk-deployment-only.md` by devops-iac-reviewer
(`# Binding rules`), and `use-doc-mcp-servers.md` by devops-iac-reviewer (`# Checklist`), best-practice-reviewer and
spec-conductor (`# Binding rules`) and spec-author (`# What you produce`).
Material-because: AC-3 — the setup prompts would state a wrong rule-to-agent mapping, so they would not give the per-rule
agent list that AC-3 calls for.
Proposed-edit: replace the S-AGENTS quote with:
"> `aws-config.md` is named by `devops-iac-reviewer` and `security-reviewer`, `cdk-deployment-only.md` by
> `devops-iac-reviewer`, and `use-doc-mcp-servers.md` by `best-practice-reviewer`, `devops-iac-reviewer`,
> `spec-author` and `spec-conductor`, each with the marker `(where installed)`; a project that omits any of the three
> installs these agents unchanged."
The AC-3 tests compare S-AGENTS as one whitespace-collapsed phrase, so they need no other change.

### C1 — AC-3's placement clauses are not tested
Severity: C
Location: change.md § Acceptance criteria AC-3; § Tests AC-3
Defect: AC-3 fixes where each item goes ("in the always-on list", "in the path-scoped list", "S-AGENTS after the
path-scoped list", "after the advanced backlog fleet table"). Both AC-3 tests only check that each phrase appears
somewhere in the Part 8.2 slice or the 8A.1 slice.
Proposed-edit: delete those four placement phrases from AC-3. State each placement once instead, in the Files bullets for
`prompts/setup-claude.txt` and `prompts/setup-kiro.txt`. The containment tests then match AC-3 exactly.

### C2 — AC-4 says "names", but the test counts only backticked names
Severity: C
Location: change.md § Acceptance criteria AC-4
Defect: AC-4 says the test fails "WHEN a body ... names one of the three rules without `(where installed)`". The AC-1 and
AC-2 tests count only backticked occurrences, which is all that AC-1 governs, so an unbackticked `aws-config.md` would
pass. Today every occurrence in the ten bodies is backticked.
Proposed-edit: AC-4 → "WHEN a body under `clients/claude/agents/` or `clients/kiro/agents/` carries a backticked
occurrence of one of the three rule names that is not followed by whitespace and `(where installed)`,
`test/test_agent_rule_references.py` SHALL fail."

### C3 — The re-wrap must not split the marker across lines
Severity: C
Location: change.md § Files (the agent-bodies bullet)
Defect: the marked-occurrence pattern has a literal space inside `\(where installed\)`. A re-wrap that breaks the line
between "(where" and "installed)" therefore fails AC-1 as written and turns its test red. The Files bullet asks for the
paragraph to be re-wrapped but does not state this constraint.
Proposed-edit: "... ` (where installed)` after each listed occurrence, the paragraph re-wrapped with no line break
inside `(where installed)`; no other text changes (AC-1, AC-2)."

### D1 — The Residuals reason does not fit the Kiro descriptor
Severity: D
Location: change.md § Residuals (second bullet)
Defect: the reason given, "extends the marker to rule and template text", does not cover the `description` of
`clients/kiro/agents/standards-reviewer.json`. That field is agent metadata, not rule or template text. The Kiro CLI
configuration reference (kiro.dev, custom-agents configuration reference) says `description` is "primarily for human
readability", and in that description "aws-config" is one example in a list that ends in "etc.".
Proposed-edit: "... Qualifying them extends the marker to rule and template text and to an agent description that is
not prompt text, beyond this ask."

Lenses with no finding:
- Security: no auth, IAM, secrets or input handling is touched.
- Operability: no deploy or runtime effect. `E2E: not applicable` fits `always-test-e2e.md`, and CI's `tests` group runs
  the module through the `testpaths` entry `test`.
- Best practice: the Kiro `file://` prompt claim matches the Kiro configuration reference, and all five descriptors carry
  `prompt: "file://<name>.md"` and name none of the three rules.
- Standards: the test location, the `ROOT` idiom and the module constants match `test/test_layout.py` and
  `test/test_session_title.py`. Every framework path the spec, the new prose and the planned test name exists, so the
  layout guard stays green. `change.md` is under the tier-S cap.
- Heading change: no file under prompts/ or clients/ quotes the old 8.9, 8.17 or 8.19 heading text; other text cites those
  sections by number only, and no Python parses the headings.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | `test_claude_bodies_mark_conditional_rules` (per Claude body) | a backticked rule name lacks the marker (red before I1) |
| AC-2 | `test_kiro_bodies_mark_conditional_rules` (per Kiro body) | the same in a Kiro body (red before I1) |
| AC-3 | `test_setup_claude_states_install_conditions` | a parenthetical or S-AGENTS is missing from the Part 8.2 slice (red before I1; placement: C1) |
| AC-3 | `test_setup_kiro_states_install_conditions` | a heading line differs, or S-AGENTS is missing from the 8A.1 slice (red before I1) |
| AC-4 | T1's red capture of the AC-1 and AC-2 tests | evidence that the failing direction works on the unmarked bodies |
| UB-1 | `test_conditional_rules_still_named` (per client, body, heading, rule) | a listed rule leaves its section (green before and after I1) |
| UB-2 | `test_marker_only_on_conditional_rules` | the marker follows any other `*.md` name (green before and after I1) |

All of these are example tests. No criterion quantifies over an input domain, so no property-based test is owed.

Verdict: NOT-READY — NOT-CLEAN (0 A, 1 B)
