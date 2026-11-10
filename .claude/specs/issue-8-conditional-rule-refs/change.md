# Change — issue #8: agents name AWS/MCP rules that non-AWS projects do not install

Tier: S. Kind: BUGFIX. Scope decided in `decisions/decision-log.md` DL-001.

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end"
- Issue #8: "Agents name AWS/MCP rules that non-AWS projects do not install"

## Ask

Five shipped agents name `aws-config.md`, `cdk-deployment-only.md` or `use-doc-mcp-servers.md` as rules to apply; a
project without AWS, CDK or documentation MCP servers does not install them. Every such reference gains the fixed
marker `(where installed)`, and both setup prompts state when each rule is installed and which agents reference
it. Omitting the three in a non-AWS project is the intended install; `devops-iac-reviewer` stays installed (DL-001).

The references, by body and heading — identical in `clients/claude/agents/` and `clients/kiro/agents/` (the Kiro
`<name>.json` descriptors load these `<name>.md` bodies through `prompt: "file://<name>.md"` and name no rule):

- `devops-iac-reviewer.md` — `# Binding rules`: `cdk-deployment-only.md`, `aws-config.md`;
  `# Checklist (apply what the change touches)`: `use-doc-mcp-servers.md`
- `security-reviewer.md` — `# Binding rules`: `aws-config.md`
- `best-practice-reviewer.md` — `# Binding rules`: `use-doc-mcp-servers.md`
- `spec-author.md` — `# What you produce`: `use-doc-mcp-servers.md`
- `spec-conductor.md` — `# Binding rules (always loaded; the ones you apply most)`: `use-doc-mcp-servers.md`

The agents sentence, written verbatim in both prompts (call it S-AGENTS):

> `aws-config.md` is named by `devops-iac-reviewer` and `security-reviewer`, `cdk-deployment-only.md` by
> `devops-iac-reviewer`, and `use-doc-mcp-servers.md` by `best-practice-reviewer`, `devops-iac-reviewer`,
> `spec-author` and `spec-conductor`, each with the marker `(where installed)`; a project that omits any of the three
> installs these agents unchanged.

## Acceptance criteria

- AC-1 — WHEN a project does not install one of the three rules, the agent bodies under `clients/claude/agents/`
  SHALL NOT direct the agent to apply it unconditionally: every backticked occurrence of a rule name SHALL be
  followed by whitespace and `(where installed)`, e.g. "`aws-config.md` (where installed)".
- AC-2 — The agent bodies `clients/kiro/agents/*.md` SHALL meet AC-1.
- AC-3 — The setup prompts SHALL name each rule's install condition and the agents that reference it:
  - `prompts/setup-claude.txt` `### Part 8.2 — .claude/rules/ (the detailed rules)` SHALL contain
    "`aws-config.md` (installed only in an AWS project)", "`use-doc-mcp-servers.md` (installed only where
    documentation MCP servers are configured)", "`cdk-deployment-only.md` (installed only where the project has a
    `cdk/` directory)" and S-AGENTS.
  - `prompts/setup-kiro.txt` SHALL carry these three heading lines:
    - `` ### 8.9 `aws-config.md` (always; installed only in an AWS project) ``
    - `` ### 8.17 `cdk-deployment-only.md` (conditional, CDK; installed only where the project has a `cdk/` directory) ``
    - `` ### 8.19 `use-doc-mcp-servers.md` (always; installed only where documentation MCP servers are configured) — replaces 4 separate files ``

    and `### 8A.1 Create the agents directory and install the fleet` SHALL contain S-AGENTS.
- AC-4 — WHEN a body under `clients/claude/agents/` or `clients/kiro/agents/` carries a backticked occurrence of one
  of the three rule names that is not followed by whitespace and `(where installed)`,
  `test/test_agent_rule_references.py` SHALL fail.

## Unchanged behaviour

- UB-1 — A project that installs the three rules SHALL CONTINUE TO have them applied: each of the ten bodies SHALL
  CONTINUE TO name, under the heading listed under Ask, each rule listed there.
- UB-2 — References to always-installed rules (`no-guessing.md`, `no-environment-vars.md` and every other
  backticked `*.md` name in the bodies) SHALL CONTINUE TO read as now, without `(where installed)`.

## Files

- The five bodies listed under Ask, in `clients/claude/agents/` and in `clients/kiro/agents/` —
  ` (where installed)` after each listed occurrence, the paragraph re-wrapped with no line break inside
  `(where installed)`; no other text changes (AC-1, AC-2).
- `prompts/setup-claude.txt` — Part 8.2: the `aws-config.md` and `use-doc-mcp-servers.md` parentheticals in the
  always-on list, the `cdk-deployment-only.md` parenthetical in the path-scoped list, and S-AGENTS after the
  path-scoped list (AC-3).
- `prompts/setup-kiro.txt` — the 8.9, 8.17 and 8.19 headings; S-AGENTS in 8A.1 after the advanced backlog fleet
  table (AC-3).
- `test/test_agent_rule_references.py` — new framework test module (AC-4).

## Tests

All in `test/test_agent_rule_references.py`, reading from `ROOT = Path(__file__).resolve().parents[1]`; example
tests (no criterion quantifies over an input domain). Bodies are `sorted((ROOT / d).glob("*.md"))` for `d` in
`clients/claude/agents` and `clients/kiro/agents`. A marked occurrence matches `` `<rule>`\s+\(where installed\) ``,
so a marker wrapped onto the next line still counts. Phrase checks compare whitespace-collapsed text; the Part 8.2
slice runs from its heading to `### Part 8.2a`, the 8A.1 slice to `### 8A.2`; heading checks compare stripped lines;
a body section runs from its heading line to the next line beginning `# `.

- AC-1 — `test_claude_bodies_mark_conditional_rules`, parametrized over the Claude bodies: for each rule, the
  count of `` `<rule>` `` equals the count of marked occurrences.
- AC-2 — `test_kiro_bodies_mark_conditional_rules`: the same over the Kiro bodies.
- AC-3 — `test_setup_claude_states_install_conditions`: the Part 8.2 slice contains the three parenthesised names
  and S-AGENTS. `test_setup_kiro_states_install_conditions`: setup-kiro has the three heading lines and the 8A.1
  slice contains S-AGENTS.
- AC-4 — T1's red capture: the AC-1 and AC-2 tests fail on the unmarked bodies.
- UB-1 — `test_conditional_rules_still_named`, parametrized over (client, body, heading, rule) from the Ask list:
  the body's section under that heading contains `` `<rule>` ``.
- UB-2 — `test_marker_only_on_conditional_rules`: in every body, each match of
  `` `([\w.-]+\.md)`\s+\(where installed\) `` names one of the three rules.

Red before I1: the AC-1, AC-2 and AC-3 tests. Green before and after I1: the UB-1 and UB-2 tests.

E2E: not applicable — agent and prompt text; no runtime behaviour of a running system changes. CI's `tests` group
runs the module (`pyproject.toml` `[tool.pytest.ini_options]` `testpaths` includes `test`).

## Tasks (one wave)

- [ ] T1 TEST: write the module described under Tests; capture it red before I1 — Files:
  `test/test_agent_rule_references.py` — Validates: AC-1, AC-2, AC-3, AC-4, UB-1, UB-2
- [ ] I1 IMPL: mark the ten bodies per AC-1 and AC-2; write the AC-3 parentheticals, headings and S-AGENTS — Files:
  the ten bodies under Files, `prompts/setup-claude.txt`, `prompts/setup-kiro.txt` — Validates: AC-1, AC-2, AC-3

## Residuals

- This repository's installed `.claude/agents/` copies (toolchain) change only by the release and promotion that
  batches this run's fixes — the issue's last work item.
- Unmarked references outside the agent bodies stay: setup-claude `### Part 8.1 — CLAUDE.md (root, always loaded)`
  template (`use-doc-mcp-servers.md`), setup-kiro 8.22 and 8.23 steering bodies (`cdk-deployment-only.md`,
  `use-doc-mcp-servers.md`), and the `description` of `clients/kiro/agents/standards-reviewer.json` (`aws-config`).
  Qualifying them extends the marker to rule and template text and to an agent description that is not prompt
  text, beyond this ask.
