# Prompt — issue #8: agents name AWS/MCP rules that non-AWS projects do not install

Tier: S — reference wording in agent bodies and install notes in the setup prompts; no new interface, no
per-project agent rendering.

Kind: BUGFIX.

## Goal

Five shipped agents (`devops-iac-reviewer`, `security-reviewer`, `best-practice-reviewer`, `spec-author`,
`spec-conductor`, in both `clients/claude/agents/` and `clients/kiro/agents/`) tell the agent to apply
`aws-config.md`, `cdk-deployment-only.md` or `use-doc-mcp-servers.md`. A project without AWS, CDK or
documentation MCP servers does not install those rules — this repository's `.claude/rules/` holds none of the
three — so an installed agent is told to apply a rule that does not exist. Correct: every reference to one of
the three rules is conditional on the rule being installed, and the setup prompts state when each rule is
installed and which agents reference it.

## Scope (the ask)

- Decided (DL-001), the issue's first open question: the condition lives in BOTH places — a fixed conditional
  marker next to each reference in the ten agent bodies, and an install note in the setup prompts.
- The marker is the literal text `(where installed)` immediately after each backticked rule name in an agent
  body, e.g. "`aws-config.md` (where installed)". One fixed form keeps the AC-4 test exact.
- `prompts/setup-claude.txt` `### Part 8.2 — .claude/rules/ (the detailed rules)`: the always-on list keeps the
  three names, each followed by its install condition — `aws-config.md` for an AWS project,
  `use-doc-mcp-servers.md` for a project that configures documentation MCP servers (Part 0.1 / `.mcp.json`),
  `cdk-deployment-only.md` (the scoped list) for a project with `cdk/` — and one sentence naming the five agents
  that reference them conditionally. Decided (DL-001), the issue's second open question: omitting the three in
  a non-AWS project IS the intended install (Part 5.1 already drops the AWS/CDK deny rules for non-AWS projects;
  Part 0.1 says a non-AWS project may need no MCP server), so the prompts state the condition rather than name a
  deviation.
- `prompts/setup-kiro.txt`: the headings `### 8.9 \`aws-config.md\` (always)` and
  `### 8.19 \`use-doc-mcp-servers.md\` (always) — replaces 4 separate files` gain their install condition, and
  the section that installs the Kiro agents names the five agents' conditional references; 8.17 already says
  "(conditional, CDK)".
- Decided (DL-001), the issue's third open question: `devops-iac-reviewer` is still installed in a project
  with no infrastructure code — its own body says a change touching none of its areas is CLEAN in one line,
  and it also reviews CI and operability.
- A test under `test/` (AC-4) that fails when a shipped agent body under `clients/claude/agents/` or
  `clients/kiro/agents/` names one of the three rules without the marker.

## Out of scope

- The installed `.claude/agents/` copies of this repository (toolchain; they change by the release and
  promotion that batches this run's fixes — the issue's last work item).
- Rendering per-project agent variants (the issue's M alternative).

## Tests

Every acceptance criterion and unchanged-behaviour clause is pinned by a test.
E2E: not applicable — agent and prompt text; no runtime behaviour of a deployed system changes. CI's `tests`
group runs the new test.
