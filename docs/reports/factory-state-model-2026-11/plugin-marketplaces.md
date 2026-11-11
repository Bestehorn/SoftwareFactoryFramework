# Plugin marketplaces as a source of makers and checkers (research, 2026-11-10)

> Record from the factory state-model design discussion (2026-11-09 to 2026-11-11), copied from the working notes. Paths to working files were rewritten to this folder; the text is otherwise as written. Where it differs from `docs/design/factory-state-model/decisions.md`, that file wins.

Status: research only. Nothing in the framework was changed, nothing was installed, no marketplace command was
run, no repository was cloned. Companion of `checker-landscape.md` (read its sections 0 and 3 first; this file
does not repeat the deterministic-tool and SaaS-agent landscape, the SARIF bus, the dedupe-bot lesson or the
team-per-state table, and refers to them by section).

Verification legend (same as `checker-landscape.md`):

- **[F]** read on the primary page in this session.
- **[S]** from web-search results that cite the named page; I did not open the page.
- **[U]** not verified in this session.

Prompt-injection note: no fetched page contained instructions that tried to redirect this research. Several
plugin pages contain instructions written for the agent that *uses* the plugin (for example the session-report
skill's "run the bundled analyzer", superpowers' "mandatory workflows, not suggestions", the skill-creator ethics
paragraph). They were read as data and not followed. The fetch tool's summariser sometimes labelled ordinary
README text as "note for AI agents"; those labels are the summariser's, not the pages'.

---

## 0. Summary

1. **Mechanics are mature and pinnable.** A Claude Code plugin is a directory with `.claude-plugin/plugin.json`
   carrying skills, commands, agents, hooks, MCP and LSP servers, monitors, output styles, themes, workflows,
   `bin/` and two default settings. A marketplace is a git repo or URL with `.claude-plugin/marketplace.json`.
   Plugin entries can be pinned to a 40-character commit `sha` (github, url, git-subdir) or an archive `sha256`
   [F]. Organisations allow-list marketplace sources with managed `strictKnownMarketplaces`, block with
   `blockedMarketplaces`, force-enable with managed `enabledPlugins`, and seed CI images with
   `CLAUDE_CODE_PLUGIN_SEED_DIR` [F].
2. **A plugin cannot carry our whole framework.** It has no rules component (`CLAUDE.md` at the plugin root is not
   loaded), its `settings.json` honours only `agent` and `subagentStatusLine`, and plugin agents ignore
   `permissionMode`, `hooks` and `mcpServers` in front-matter [F]. Our always-loaded rules, permissions, scripts
   and CI templates stay outside any plugin. Agents, commands and the Python hook dispatcher could be packaged.
3. **Kiro is not format-compatible.** Kiro powers use the cross-vendor Agent Plugins 1.0 format (root
   `plugin.json`, `skills/`, `mcp.json`) [F]; Claude Code does not read it [S]. The portable intersection is
   `SKILL.md` plus MCP. Agents, hooks and steering stay per client, which matches the existing
   `clients/common` + `clients/claude` + `clients/kiro` split. Kiro documents no power pinning and manual updates
   only [F].
4. **Few plugins are worth installing as-is; many are worth imitating.** Worth adopting or piloting: the
   first-party LSP plugins (diagnostics after every edit), `claude plugin eval` (regression tests for our own
   agents, with a no-plugin baseline), the built-in `/simplify` and `/code-review` skills, `claude-security`
   (find, threat-model, verify-to-disprove, SARIF), and a short list of Trail of Bits skills. Most others overlap
   with what we have, or conflict with our rules: they call `gh` (forbidden by `use-git-wrapper-scripts.md`),
   configure through shell environment variables (`no-environment-vars.md`), stop for human approval
   (`continuous-work.md`), or send code to a vendor.
5. **The best plugins share about fifteen techniques** (section 3). The high-value ones for us: a verifier that
   tries to *disprove* each finding and caps its severity; cheap gates before expensive finders; rules retrieved
   only for the touched paths; proof taken from runner result files, not model opinion (test canary, novel inputs,
   "named, not run"); repository text treated as evidence, never as instruction; persistent finding ids with a
   revision stamp; and evals with a baseline arm.
6. **Trust is the binding constraint.** Hooks, monitors, MCP/LSP servers and `bin/` run with the user's full
   permissions, outside the sandbox [F]. Official-marketplace plugins auto-update by default, so reviewed files
   can change on disk [F]. In 2025–26 the agent ecosystem had real supply-chain incidents: a trojanised Claude Code
   extension on Cursor's marketplace (2026-10-29) [F], 341 malicious skills on ClawHub [S], 76 confirmed malicious
   payloads among 3,984 audited skills [S], a backdoored MCP server on npm [S], and repository-file hooks that ran
   before the trust dialog (CVE-2025-59536) [S]. Section 4 gives the rules.

---

## 1. What we already have (overlap baseline)

Agents (`clients/claude/agents/`, Kiro twins in `clients/kiro/agents/`) [F]: issue-work-orchestrator,
spec-conductor (orchestrators); spec-author, spec-researcher, spec-prompt-author-agent, spec-implementer,
ci-workflow-agent, code-merge-reviewer, dead-code-removal-agent, doc-reviewer-agent, issue-intake-agent,
issue-housekeeping-agent, product-management-agent (makers or maker-checkers); spec-review-agent, test-architect,
standards-reviewer, best-practice-reviewer, security-reviewer, devops-iac-reviewer, adversarial-verifier
(checkers). Roles and gaps are in `checker-landscape.md` §1.1.

Commands (`clients/claude/commands/`) [F]: `/work-issue` (one issue, claim to landing, SESSION verdict),
`/issues-work` and `/auto-work` (backlog loops), `/continue-work` (resume a stalled run), `/spec-new`,
`/spec-review`, `/spec-tasks`, `/spec-implement` (spec/TDD engine), `/close-session` (close-out audit, reopen
issues closed over open items), `/compile-memory` (turn ledger rows and lessons into tests, hooks or rules),
`/supervise` (resume runs an API error ended).

Built-in Claude Code skills visible in this session's skill list [F, observed in session]: `code-review` (effort
levels low..max, `--comment`, `--fix`, `--max-findings`), `simplify` (reuse, simplification, efficiency; "does not
hunt for bugs"), `security-review` (pending changes on the branch). These are part of Claude Code itself, not
third-party plugins.

---

## 2. How plugins and marketplaces work (question 1)

### 2.1 What a plugin can contain

| Component | Location | Runs code? | Notes |
|---|---|---|---|
| Skills | `skills/<name>/SKILL.md` | no (instructions) | Invoked as `/<plugin>:<skill>`; name + description sit in context every turn [F components, overview] |
| Commands | `commands/*.md` | no | "the older format"; skills supersede them [F components] |
| Agents | `agents/**/*.md` | no | Namespaced `<plugin>:<name>`; supported front-matter includes `model`, `effort`, `tools`, `disallowedTools`, `skills`, `memory`, `isolation: worktree`; **ignored: `permissionMode`, `hooks`, `mcpServers`, `initialPrompt`** [F components] |
| Hooks | `hooks/hooks.json` | **yes**, as the user | Same shape as the `hooks` object in settings; fire from load, not only when a skill runs [F components] |
| Hooks module ("mod") | `modules` key in `hooks.json` | **yes** (JavaScript inside Claude Code) | Can draw panes and add commands [F overview, security] |
| MCP servers | `.mcp.json` or `mcpServers` | **yes** (stdio process) | Tools named `mcp__plugin_<plugin>_<server>__<tool>`; permission rules apply to tool calls [F components] |
| LSP servers | `.lsp.json` | **yes** | Binary not bundled; must be on `PATH` [F components, code-intelligence] |
| Monitors | `monitors/monitors.json` | **yes**, background | **Do not start under `-p`**; run outside the sandbox [F components] |
| `bin/` | `bin/` | **yes** when Claude runs it | Added after the user's `PATH`, so it cannot shadow `git` [F components] |
| Output styles, themes | `output-styles/`, `themes/` | no | [F components] |
| Workflows | `workflows/*.js` | orchestrates subagents | [F components] |
| Default settings | `settings.json` | no | **Only `agent` and `subagentStatusLine` take effect; every other key is dropped** [F components] |
| User config | `userConfig` in manifest | no | `sensitive: true` stores in secure storage; values reach hooks as `CLAUDE_PLUGIN_OPTION_<KEY>` [F components] |

No rules component: "Claude Code doesn't load a `CLAUDE.md` at the plugin root" and instructions must be written
as skills; a rule that must always hold belongs in a hook [F components]. Path variables: `${CLAUDE_PLUGIN_ROOT}`
(changes per version, never write state there), `${CLAUDE_PLUGIN_DATA}` (survives updates), `${CLAUDE_PROJECT_DIR}`
[F components]. An enabled plugin is part of every session and its skill/agent descriptions cost context every
turn; the official marketplace shows a "Context cost" estimate [F overview].

**Consequence for this framework:** `clients/claude/agents/`, `commands/` and the `src/hooks/` dispatcher could be
packaged as a plugin (hook command `python "${CLAUDE_PLUGIN_ROOT}/hooks/hooks.py" pre-tool-use`). The always-loaded
`rules/`, the `permissions` block, `scripts/`, `templates/ci/` and the per-agent `permissionMode` cannot. Whether
`Agent(spec-author, …)` allow-lists in our orchestrator front-matter accept namespaced names such as
`sff:spec-author` is [U]. This is an option to record, not a recommendation (it is a design question beyond this
research's scope).

### 2.2 Marketplaces, sources and version pinning

- `marketplace.json` requires `name`, `owner`, `plugins`; each entry needs `name` and `source` [F create].
- Plugin source types: relative path, `github` (`repo`, `ref`, `sha`), `url` (any git URL, `ref`, `sha`),
  `git-subdir` (`url`, `path`, `ref`, `sha`, sparse partial clone), `npm` (fetched with install scripts
  disabled), `archive` (HTTPS zip, `sha256`), `command` (a directory printed by a local command) [F reference].
- `sha` is "a full 40-character lowercase commit SHA"; with `ref` and `sha` both set, Claude Code checks out
  the `sha` [F reference]. An `archive` with a mismatching `sha256` is refused [F security].
- **Version resolution:** manifest `version` first, then the entry's `version`, else the commit SHA (12
  characters) for git sources, the digest for archives, `unknown` for npm [F loading]. A pinned
  `"version": "1.0.0"` keeps every user on the cached copy however many commits are pushed [F loading,
  host-marketplace].
- **Auto-update:** on by default for Anthropic's official marketplaces, off for every other marketplace; a
  managed `autoUpdate` on the `extraKnownMarketplaces` entry overrides the user toggle; `DISABLE_AUTOUPDATER`
  turns the pass off fleet-wide [F loading, org]. Updates take effect at `/reload-plugins` or next launch;
  previous version directories are swept 14 days later [F loading].
- **Release channels** are two marketplaces with different `name`s pointing at different refs; Claude Code "has
  no release-channel concept" [F host-marketplace].
- **Rename/remove:** `renames` map (append-only), `forceRemoveDeletedPlugins` uninstalls delisted plugins [F
  host-marketplace].
- `claude plugin validate` checks syntax, names, `..` paths and unknown keys; it does not catch fetch errors or
  entry hooks written as a path [F reference].

### 2.3 Distribution to a team or organisation

| Need | Mechanism | Source |
|---|---|---|
| One repository's contributors | `extraKnownMarketplaces` + `enabledPlugins` in the committed `.claude/settings.json`; applies only after workspace trust; each contributor still runs `claude plugin install … --scope project` unless the plugin is a relative-path entry of a local marketplace | [F org, loading] |
| Whole fleet | Managed settings (server-managed from the claude.ai admin console, MDM, or `managed-settings.json` + `managed-settings.d/`); managed `enabledPlugins: true` force-enables, `false` blocks and hides | [F org] |
| Allow-list | `strictKnownMarketplaces` (alias `allowedMarketplaces`): exact `github`/`git`/`url`/`file`/`directory` matches, `owner/*` wildcards, `hostPattern`/`pathPattern` regexes; `[]` blocks everything including the official marketplace; add `{ "source": "skills-dir" }` or skills-directory plugins stop loading | [F org, reference] |
| Block-list | `blockedMarketplaces`, checked first, canonicalises git URLs | [F org] |
| No side-loading | `disableSideloadFlags` rejects `--plugin-dir`, `--plugin-url`, `--agents`, SDK `plugins` | [F org] |
| Hooks only from the org | `allowManagedHooksOnly` blocks user, project, local and plugin hooks; hooks of plugins force-enabled in managed `enabledPlugins` are exempt | [F org; exemption [S] settings-reference] |
| Customisation only via plugins | `strictPluginOnlyCustomization` blocks skills, agents, hooks and MCP servers from user and project sources | [F org, settings-reference] |
| Private marketplace | User's own git credentials, non-interactive (SSH agent or stored HTTPS credential); `marketplace.json` cannot carry a token; `GITHUB_TOKEN` alone does not authenticate the background check | [F host-marketplace] |
| Audit | OTel `claude_code.plugin_installed` / `plugin_loaded`; Enterprise analytics endpoint per plugin per day | [F org] |

**Consequence for this framework:** in an organisation that sets `allowManagedHooksOnly` or
`strictPluginOnlyCustomization`, the framework's project-installed `.claude/agents/` and settings hooks would not
load. There, the only route for our agents and hook dispatcher is a plugin that managed settings force-enable [F
org]. This is worth knowing before rolling out to a regulated client.

### 2.4 Headless (`claude -p`) and CI

- Managed `extraKnownMarketplaces`/`enabledPlugins` apply in `-p` and CI, with installs in the background; a
  repository's `extraKnownMarketplaces` applies only in a folder whose trust was accepted interactively (or
  `hasTrustDialogAccepted` in `~/.claude.json`) [F org].
- `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` makes a run wait for installs before its first query [F org].
- Seed images: install into a seed with `CLAUDE_CODE_PLUGIN_CACHE_DIR`, run with `CLAUDE_CODE_PLUGIN_SEED_DIR`;
  seeds are read-only and auto-update is forced off [F org].
- Verify in CI with `--output-format stream-json --verbose`: the `init` event lists loaded plugins [F org].
- Monitors do not start under `-p` [F components]; LSP servers do not start in cloud sessions [F
  code-intelligence]; `project-artifact` cannot publish headless [F].
- `anthropics/claude-code-action` takes `plugin_marketplaces` and `plugins` inputs, always clones the default
  branch HEAD, and cannot pin a ref yet (issue #1229 open, PR #1497 pending since July 2026) [F issue]. Private
  marketplaces fail to clone in the action without a prior credential step (#850) [S].
- Conflict to decide: the seed and sync knobs are environment variables. `no-environment-vars.md` permits the
  `env` block of `.claude/settings.json`, but a CI job environment is not covered by its wording [U].

### 2.5 Kiro equivalents

| Claude Code | Kiro | Source |
|---|---|---|
| Plugin | **Power**: Agent Plugins format (`plugin.json` required, `skills/`, `mcp.json`) recommended; legacy `POWER.md` with keywords, `steering/`, `mcp.json` and hook files | [F powers/create; legacy detail S] |
| Skill (`SKILL.md`) | Skill (Agent Skills standard, `~/.kiro/skills/` or workspace); custom agents load skills only via `resources: skill://…` | [S kiro.dev/docs/skills] |
| Subagent | Custom agent, JSON or Markdown in `.kiro/agents/` | [S; our `clients/kiro/agents/*.json` F] |
| Rules / `CLAUDE.md` | Steering | [S] |
| Hooks | `.kiro/hooks/*.json`; CLI events agentSpawn, userPromptSubmit, preToolUse, postToolUse, stop | [S] |
| Marketplace | Powers registry, GitHub URL, local path; "Check for updates" is manual; no pinning documented | [F powers/installation] |
| Managed allow-list | Enterprise MCP on/off and an MCP registry allow-list URL; model governance; no power allow-list documented | [S kiro.dev/docs/enterprise/governance] |
| `claude plugin eval` | none found | [U] |

Agent Plugins 1.0 (2026-08-06) standardises only skills and MCP servers; launch clients include Kiro, Codex,
Cursor, Copilot and VS Code; Anthropic is not a maintainer and Claude Code keeps `.claude-plugin/plugin.json` [S].
**Consequence:** a shared asset that must work on both clients is a `SKILL.md` (plus an MCP server where needed),
generated into both a Claude plugin and a Kiro power from `clients/common/`. Agents, hooks and rules stay
client-specific.

---

## 3. Per-state tables (questions 2 and 3)

Recommendation vocabulary: **adopt** (install as-is, pinned), **pilot** (one project, pinned, measured), **imitate**
(build the technique into our own maker or checker), **skip**. "Anthropic" = in `anthropics/claude-plugins-official`
`plugins/` (Anthropic-maintained) [F]; "partner" = its `external_plugins/` [F].

Cross-cutting conflicts that decide many rows:
- **`gh`**: `code-review` calls `gh pr view` and posts with an MCP inline-comment tool [F]; `project-artifact`
  pulls PR state via `gh` [F]; Sentry's PR skills need `gh` [S]. Our wrapper rule forbids `gh`, so these cannot
  run as-is.
- **Shell environment variables**: `security-guidance` is configured only through env vars such as
  `SECURITY_REVIEW_MODEL` and `ENABLE_STOP_REVIEW` [F]; superpowers telemetry opt-out is an env var [F].
- **Human approval stops**: `feature-dev` waits for approval at phases 3, 4, 5, 6 [F]; `code-modernization` has
  human sign-off gates [F]. Our `continuous-work.md` forbids that shape.
- **Code egress**: Semgrep Guardian sends edited files and lockfiles to scanner.semgrep.ai [S].

### 3.1 START (triage)

| Plugin / skill | Source, maintainer | Role | Technique worth having | Overlap with ours | Recommendation |
|---|---|---|---|---|---|
| `code-review` step 1 gate | Anthropic [F] | checker pre-gate | A Haiku agent stops the run when the PR is closed, draft, trivial or already reviewed [F] | none at triage | **Imitate**: a cheap gate before any expensive lane (also for re-triage of already-triaged issues) |
| `feature-dev` phases 1–3 | Anthropic [F] | maker | Discovery, then all clarifying questions in one batch before design [F] | `continuous-work.md` already asks at the start in one batch | **Skip** (already have it) |
| AI-DLC adaptive scope | awslabs/aidlc-workflows [S] | maker | Scope detected from the request; opt-in `*.opt-in.md` extensions (security, testing, resiliency) offered at requirements analysis [S] | tiering in `proportionality.md`; risk tags proposed in `checker-landscape.md` §3 | **Imitate**: risk-tag extensions offered at classification, recorded once |
| Sentry plugin (`/seer`, issue summariser) | getsentry, in official marketplace [S] | evidence for severity | Production error counts as triage evidence [S] | product-management-agent scores without runtime data | **Pilot** only in a project that already uses Sentry |
| GitHub, GitLab, Linear, Asana plugins | partner [F list] | tracker access | — | the git wrapper | **Skip**: bypasses `scripts/github_wrapper.py` |
| superpowers `brainstorming` | obra/superpowers [F] | interactive maker | Socratic design refinement [S] | spec-prompt-author-agent (interactive) | **Skip** |

### 3.2 SPEC-REQUIRED (spec, acceptance tests, review)

| Plugin / skill | Source, maintainer | Role | Technique worth having | Overlap | Recommendation |
|---|---|---|---|---|---|
| `feature-dev` code-architect ×2–3 | Anthropic [F] | maker | Parallel architects with fixed philosophies: minimal change, clean architecture, pragmatic balance [F] | spec-author writes one design | **Imitate** for tier M/L: two or three design alternatives, chosen against the ask, decision logged |
| `feature-dev` code-explorer ×2–3 | Anthropic [F] | helper | Parallel explorers return entry points with file:line and a reading list [F] | spec-researcher bursts | **Skip** (have it) |
| spec-kit `/speckit.analyze`, `/speckit.checklist` | github/spec-kit [S] | checker | Read-only cross-artifact consistency check before implement; checklists as "unit tests for your requirements" [S] | spec-review-agent (hedge/ambiguity scan) | **Imitate**: a deterministic AC-to-design-to-task consistency pass before the LLM panel (pairs with the EARS lint in `checker-landscape.md` §3.4 item 7) |
| AI-DLC rule layers | awslabs [S] | policy | Rules stack org → team → project → phase → stage; lower layers only add [S] | `.claude/rules/` single layer + project-specific | **Imitate** when adding per-state rules: additive only, never override |
| `code-modernization` extract-rules | Anthropic [F] | maker | Business rules as Given/When/Then cards, 50–200 parallel agents, then a person confirms [F] | spec-author for bugfix/legacy | **Imitate** the card format for characterisation of legacy behaviour; replace the human gate with test-architect |
| superpowers `writing-plans` | obra/superpowers [F] | maker | Tasks of 2–5 minutes with exact paths, full code and a verification step each [S] | `/spec-tasks` | **Imitate** only the "verification step per task" if tasks.md lacks it [U whether it does] |
| `claude-security` threat-model phase | Anthropic [F] | checker | Architecture map, then threat model, then component hunt [F] | security-reviewer (no threat-model artefact) | **Pilot** for L or risk:auth/money specs |
| Trail of Bits `audit-context-building` | trailofbits/skills, CC-BY-SA-4.0 [F] | helper | Line-by-line understanding before any bug hunting [S] | spec-researcher | **Pilot** inside the security lane for L |
| Trail of Bits `property-based-testing` | trailofbits [F] | test maker/checker | Write, review and triage PBT (Hypothesis, fast-check, proptest) [F] | test-architect (PBT only for domain-quantified criteria) | **Pilot** as a skill test-architect may load |

### 3.3 IMPLEMENTATION-READY (implement until tests pass, review the diff)

| Plugin / skill | Source, maintainer | Role | Technique worth having | Overlap | Recommendation |
|---|---|---|---|---|---|
| `code-review` command | Anthropic [F] | checker | Haiku gate → Haiku finds the CLAUDE.md files for touched dirs → Sonnet summary → **2 Sonnet (rule compliance) + 2 Opus (bugs) in parallel** → **one validation subagent per flagged issue** → only validated issues reported; suggestions only for self-contained fixes under 6 lines [F] | none hunts general bugs (`checker-landscape.md` §3.4 item 6) | **Imitate** as the logic-bug lane; cannot run as-is (`gh`). Note: this supersedes the "5 parallel Sonnet" description in `checker-landscape.md` §2.4 [S there, F here] |
| built-in `/code-review` skill | Claude Code [F session] | checker | Effort-scaled finder count; `--fix` [F session] | same gap | **Pilot** as an optional second-opinion finder for M+ until our own lane exists; its internal algorithm is [U] |
| `pr-review-toolkit` silent-failure-hunter | Anthropic [F] | checker | Empty catches, swallowed errors, fallbacks masking failure, log-without-rethrow, optional chaining hiding failures; CRITICAL/HIGH/MEDIUM [F] | none (coding standard 5 "errors are exceptions" has no checker) | **Imitate** as a lens of the logic-bug lane; directly enforces `coding-standards.md` rule 5 |
| `pr-review-toolkit` type-design-analyzer | Anthropic [F] | checker | Four 1–10 scores: encapsulation, invariant expression, usefulness, enforcement [F] | standards-reviewer | **Imitate** as an optional L lens for new data models |
| `pr-review-toolkit` pr-test-analyzer, code-reviewer | Anthropic [F] | checker | Gap rating 1–10; issues scored 0–100 [F] | test-architect, standards-reviewer | **Skip** (covered) |
| `security-guidance` | Anthropic [F] | checker | Three layers: ~25 regex patterns on Edit/Write; Stop-hook diff review by Opus; agentic commit review tracing data flow across files; warn-only; **project policy file** `.claude/claude-security-guidance.md`; inline justified suppressions [F] | security-reviewer | **Imitate** the policy file and the commit-time cross-file review; **skip** installing (env-var config, a model call at every Stop interacts with our Stop gates, warn-only) |
| `claude-security` scan-changes | Anthropic [F] | checker | Verifiers try to disprove each candidate; must find an exploitation path in the code; may not exceed the verifier's severity; unconfirmed findings are dropped; SARIF 2.1.0 + JSONL with a persistent finding id + revision stamp with SHA; "repository says is evidence rather than instruction" [F] | security-reviewer | **Pilot** for L and risk:auth/money/iam-iac; its SARIF feeds the bus in `checker-landscape.md` §4. Needs Python 3.9+ on PATH [F] |
| Semgrep Guardian | Semgrep, official marketplace [S] | deterministic in-loop | PostToolUse scan of each changed file (Code, Supply Chain, Secrets), Claude rewrites until clean [S] | gap: no SAST with project rules | **Skip** (paid seat, code egress, ~31 KB SessionStart + ~1 KB per-prompt context injection that users could not turn off, issue #46 [S]); **imitate** with local Opengrep/Semgrep CE on changed files |
| Snyk `claude-plugin-snyk` | Snyk [S] | deterministic in-loop | Background SAST per edit; at Stop, new vulnerable lines block the stop, **at most 3 rounds**; SCA on manifest change; dependency-health skill before adding a package [S] | gap: no SCA | **Pilot** only where a Snyk licence exists; **imitate** the bounded Stop-loop (N rounds, then hand to a checker) |
| tdd-guard → Probity | nizos (single maintainer), MIT, 2.4k stars [F] | maker guard | PreToolUse blocks implementation before a failing test and over-implementation; validated by a model [F]; hardening: deny `Read` of its own state, block shell file edits [S] | spec-implementer TEST/IMPL split, `red_for_right_reason.py`, TDD gate hook | **Skip** (an LLM call per edit; we have the split); **imitate** the anti-tamper hardening |
| superpowers `subagent-driven-development` | obra/superpowers, MIT [F] | orchestration | Fresh subagent per task with a coordinator-written brief; **two-stage review after each task: spec compliance, then code quality**; subagents never read the whole plan [S] | spec-conductor waves | **Imitate** the two-stage per-task review if waves only get a wave-level check [U]; **skip** install (SessionStart bootstrap mandates its own workflow [F]) |
| `pyright-lsp`, `typescript-lsp` (and other LSP plugins) | Anthropic [F] | deterministic in-loop | Diagnostics after every edit, symbol navigation tool [F] | mypy at pre-push only | **Adopt (pilot first)** for makers; binary must be on PATH; not in cloud sessions [F]; pyright and mypy can disagree, so mypy stays the gate [U] |
| `context7` | partner [F list] | doc source | Version-specific library docs over MCP [U] | best-practice-reviewer "MCP doc servers" | **Pilot** as one of the doc servers, read-only tools allow-listed |
| Trail of Bits `differential-review`, `insecure-defaults`, `sharp-edges`, `static-analysis` | trailofbits, 8.1k stars [F] | checker | Security review of a diff with git history; fail-open defaults with "a refuting verifier per candidate file"; CodeQL/Semgrep/SARIF parsing [F] | security-reviewer | **Pilot** for risk-tagged issues; **imitate** the per-candidate refuting verifier. Licence is ShareAlike: imitate, do not copy text |
| Trail of Bits `supply-chain-risk-auditor` | trailofbits [F] | checker | Version-matched advisories, abandoned upstreams, publisher concentration, install scripts [F] | gap (OSV-Scanner proposed) | **Pilot** on manifest changes, next to OSV-Scanner |
| Trail of Bits `mutation-testing` | trailofbits [F] | checker | Configure mutation testing, analyse survivors [F] | adversarial-verifier per-wave mutant kill | **Imitate** survivor triage into adversarial-verifier |
| wshobson/agents | single maintainer, MIT, 42.4k stars, 94 plugins / 202 agents [F]; no versioned releases [S] | catalogue | Breadth | many | **Skip** install; mine lens ideas only |

### 3.4 TEST-READY (merge queue, CI, batched deploy, smoke/E2E)

| Plugin / skill | Source, maintainer | Role | Technique worth having | Overlap | Recommendation |
|---|---|---|---|---|---|
| `code-modernization` `modernize-verify` | Anthropic [F] | checker | Proof by script, not opinion: clean rebuild and full rerun with **counts from the runner's result files only**; old and new on the same inputs with a byte comparison and a listed mask; **≥10 novel inputs**; **test canary** (a one-line break must fail) and a self-test of the comparison; skipped tests reported as "named, not run"; verdict PROVEN / PARTLY PROVEN / NOT PROVEN [F] | adversarial-verifier, verdict watcher | **Imitate** in adversarial-verifier and in the post-deploy smoke verdict |
| `webapp-testing` skill | anthropics/skills [F] | E2E maker | Server-lifecycle helper (`with_server.py`) plus reconnaissance-then-action Playwright scripts [S] | `test/e2e/` authoring | **Imitate** for web projects' E2E scripts; the check stays a CI script (`always-test-e2e.md`) |
| `playwright` | partner [F list] | interactive | Browser driving over MCP [U] | — | **Skip** for gates (interactive, not reproducible) |
| Trail of Bits `agentic-actions-auditor` | trailofbits [S] | checker | Audits GitHub Actions workflows that run AI agents for prompt-injection risk [S] | devops-iac-reviewer | **Pilot** once on `templates/ci/` and any workflow that runs an agent |
| AWS `aws-core`, `deploy-on-aws` | aws / awslabs [S] | maker knowledge | CDK/CloudFormation skills; deploy-on-aws analyses, costs, generates IaC, deploys [S] | devops-iac-reviewer | **Pilot** `aws-core` for CDK knowledge; **skip** `deploy-on-aws` (deploys are the pipeline's) |
| AWS Security Agent / DevOps Agent plugins | AWS [S] | checker (SaaS) | Covered in `checker-landscape.md` §0 item 4 and §3.1 | — | as there |
| Performance: `benchmark-checklist`, perf guide | community [S] | checker | ≥5 alternating A/B runs, report median and range, a gap inside run-to-run noise is no difference; deny `Edit(perf/**)` so the agent cannot change its own benchmark [S] | none | **Imitate** if a perf lane is added (risk:perf) |

### 3.5 REWORK-REQUIRED

| Plugin / skill | Source | Technique worth having | Overlap | Recommendation |
|---|---|---|---|---|
| `claude-security` JSONL ids + revision stamp | Anthropic [F] | Persistent finding id across scans; revision file with commit SHA, effort, severity counts, rigour [F] | SARIF `baselineState` plan (`checker-landscape.md` §4.2) | **Imitate**: our review contract gets a stable finding id and a per-SHA stamp |
| `code-review` "already commented" gate | Anthropic [F] | Do not re-review what was reviewed [F] | delta mode proposed | **Imitate** |
| Snyk `/snyk-fix` | Snyk [S] | Scan, fix the top issue, rescan to confirm [S] | ci-workflow-agent | **Imitate** "rescan confirms the fix" per finding |
| Sentry `sentry-code-review` | getsentry [S] | Before fixing a bot comment, check the issue still exists [S] | implementers | **Imitate** "revalidate before fixing" |
| superpowers `receiving-code-review` | obra [F list] | Evaluate review feedback instead of accepting it blindly [U] | spec-author "restate or remove" | **Skip** |

### 3.6 CLOSE-READY (cleanup, retrospective)

| Plugin / skill | Source, maintainer | Role | Technique worth having | Overlap | Recommendation |
|---|---|---|---|---|---|
| built-in `/simplify`; `code-simplifier` agent | Claude Code [F session]; Anthropic [F] | maker | Recently modified code only; preserve behaviour and public API [F partial] | gap: unnecessary-code reviewer on the issue's diff (`checker-landscape.md` §3.4 item 13); dead-code agent is repo-wide | **Adopt** the built-in `/simplify` on the merged diff for M+; the plugin's sample standards are JavaScript-specific, so do not install it |
| `pr-review-toolkit` comment-analyzer | Anthropic [F] | checker | Comment accuracy and comment rot [F] | doc-reviewer (repo-wide) | **Imitate** in a doc-delta lane |
| `claude-md-management` | Anthropic [F] | maker | Audit CLAUDE.md with a quality score; `/revise-claude-md` captures session learnings [F] | `/compile-memory`, doc-reviewer | **Skip** (ours is mechanical and capped) |
| `hookify` | Anthropic [F] | maker | Turns corrections from the conversation into regex warn/block rules in `.claude/hookify.*.local.md` [F] | `use-lessons-learned.md` (mechanism over prose), gate dispatcher | **Skip** install; **imitate** in `/compile-memory`: propose a gate from a repeated correction |
| docs-sync-plugin, doc-drift-detector, docs-guardian | community [S] | checker | Topic map from code paths to docs, then a post-commit "docs affected" artefact; stdlib signature-vs-API-doc validator; commit hook strictness off/warn/block [S] | doc-reviewer, `checker-landscape.md` §3.4 item 14 | **Imitate** the topic map and signature validator in doc-reviewer delta mode |
| `session-report`, `receipts` | Anthropic [F] | metrics | Local, read-only transcript analysis: tokens, cache breaks, cost per subagent and skill; receipts refuses "hours saved" as "a guess dressed up as a measurement" [F] | our manual wait-time and load analyses | **Pilot** `session-report` at user scope as retro evidence |
| `ralph-loop` | Anthropic [F] | loop | Stop hook refeeds the same prompt; completion promise; max iterations [F] | `continuous-work.md` + stop gates | **Skip** |
| `project-artifact` | Anthropic [F] | report | Living status page; publish needs interactive [F] | close-session report | **Skip** |

### 3.7 Framework authoring (all states)

| Tool | Source | Technique | Recommendation |
|---|---|---|---|
| `claude plugin eval` | Claude Code CLI [F] | Each case runs in a fresh isolated headless session with only the plugin loaded, 3 runs by default, **with-arm vs no-plugin baseline (Δ)**, graders `regex`/`tool_used`/`tool_order`/`file_exists` (free) and `llm`/`baseline` (judge); mock MCP servers with replay recordings; `--model` pinned in CI; `--trust-plugin`, `--json` [F] | **Adopt (pilot)** for our core gates (test-architect, adversarial-verifier, spec-review-agent, security-reviewer): seeded defects as cases, `file_exists`/`regex` graders on the review file. Needs the agents packaged as a plugin directory; every run is a billed model call [F] |
| `skill-creator` | Anthropic [F] | Description optimisation against under-triggering, benchmark with variance, blind A/B [F partial] | **Imitate** the trigger-accuracy check for agent `description:` fields (auto-delegation depends on them) |
| `plugin-dev`, `agent-sdk-dev`, `mcp-server-dev` | Anthropic [F list] | Authoring guidance [U] | **Skip** unless we package |
| `claude plugin validate` | Claude Code CLI [F] | Schema and path checks | **Adopt** in CI if we package |
| awesome-claude-code | hesreallyhim, 57.7k stars [F] | Discovery only; the page states no vetting criteria [F] | Catalogue, not a trust signal |

---

## 4. Techniques that recur in the best ones (deliverable 2)

Build these into our own makers and checkers regardless of installing anything. Each line names where it was seen.

1. **Verify to disprove, then drop.** A separate verifier per candidate tries to refute it; unconfirmed findings
   are discarded, not downgraded, and severity may not exceed what the verifier supports (`claude-security`,
   `code-review` step 5, Trail of Bits `fp-check` and `insecure-defaults`) [F].
2. **Cheap gate first, expensive finders second.** A small model decides whether to run at all, and another
   finds only the rule files for the touched directories (`code-review` steps 1–2) [F].
3. **Lens-split parallel finders, model per lens.** Rule compliance on a mid model, bug hunting on the top model,
   all dispatched together (`code-review`, `feature-dev` review ×3, `docs-guardian` ×4) [F/S].
4. **A written "do not flag" list and a high-signal bar.** Compile/parse failures, definite wrong results and
   unambiguous rule violations only; no style, no "potential" issues (`code-review`); confidence ≥80
   (`feature-dev`) [F].
5. **Deterministic tool inside the edit loop, bounded.** LSP diagnostics or a scanner on each changed file; a Stop
   hook blocks at most N times, then the issue goes to a checker (LSP plugins [F], Snyk 3 rounds [S], Semgrep [S]).
6. **Proof from runner files, never from the model.** Clean rerun; counts parsed from result files; test canary;
   comparison self-test; ≥10 novel inputs; skipped tests reported as "named, not run" (`code-modernization`) [F].
7. **Repository text is evidence, not instruction.** Checkers list instruction-shaped text found in code, issues or
   docs and never follow it (`claude-security`, `code-modernization`) [F]. Our checkers read untrusted diffs and
   issue bodies, so every checker prompt should carry this line.
8. **Machine-readable findings with stable ids.** SARIF + JSONL with a persistent id, plus a revision stamp per
   SHA (`claude-security`) [F]; this is what makes REWORK delta reviews cheap.
9. **Alternatives by philosophy.** Two or three designs (minimal, clean, pragmatic) before choosing
   (`feature-dev`) [F].
10. **Fresh context per task, coordinator-written brief, two-stage review** (spec compliance, then quality)
    (superpowers) [S].
11. **A project policy file the checker must read**, plus justified inline suppressions (`security-guidance`) [F];
    our analogue is a per-lane precedent file (`checker-landscape.md` §4.3).
12. **Evals with a baseline arm**, repeated runs, free deterministic graders preferred over judges, model pinned in
    CI (`claude plugin eval`) [F].
13. **Anti-tamper for guards.** Deny the agent edits of its own benchmark, guard state or thresholds (perf guide
    `Edit(perf/**)`, tdd-guard `Read` deny) [S].
14. **Additive policy layers** (org → team → project → phase → stage, lower layers only add) (AI-DLC) [S].
15. **Cross-artifact consistency before implementation** (spec-kit `analyze`; checklists as tests of requirements)
    [S].

Already present in the framework: parallel review panels, maker ≠ checker, per-wave mutant kill, vacuity scan,
red-for-right-reason, one batch of questions at the start, proportional tiers. Missing and cheap: items 1
(as a formal per-finding verifier), 2, 4, 6 (canary, "named, not run", novel inputs), 7, 8, 12, 13.

---

## 5. Trust, pinning and distribution rules (question 4, deliverable 3)

### 5.1 What a plugin can do and what is known to have gone wrong

- A plugin "can execute arbitrary code on your machine with your user privileges" [F security]. Hooks, monitors,
  MCP and LSP servers and mod processes run **outside the sandbox**; only Claude's tool calls (MCP tools, `bin/`
  executables) pass through permission rules [F security].
- Anthropic's trust warning says it "cannot verify that they will work as intended" [F security].
  Third-party marketplaces are not reviewed by Anthropic [F anthropic-marketplaces]. The community marketplace
  states automated security scanning plus approval [F] and pins nearly every entry to a commit SHA, and Claude Code
  refuses a different commit [F security]. Official and community names are accepted only from
  `github.com/anthropics/`; impersonating names are refused [F reference].
- Updates change reviewed files: the official marketplace auto-updates by default [F loading]; Semgrep users
  reported that local `hooks.json` edits were overwritten on update [S].
- Incidents:
  - **2026-10-29**: trojanised `anthropic.claude-code` 2.1.312/2.1.313 on Cursor's extension marketplace for about
    11 hours. It installed an SSH key, a reverse tunnel and persistence; Microsoft recommends allow-lists, pinned
    versions and update cooldowns [F Microsoft blog]. About 5,000 machines [S].
  - **ClawHavoc, January 2026**: 341 malicious skills on ClawHub, 335 from one campaign [S].
  - **Snyk ToxicSkills, February 2026**: of 3,984 skills, 13.4% had a critical issue and 76 confirmed malicious
    payloads were found; 91% of the malicious ones also used prompt injection; one community "skill scanner" was
    itself malware [S].
  - **postmark-mcp, September 2025**: an npm MCP server, clean for 15 versions, then a one-line BCC of every
    email in 1.0.16 [S].
  - **CVE-2025-59536 / CVE-2026-21852**: repository `.claude/settings.json` hooks and `enableAllProjectMcpServers`
    ran, and `ANTHROPIC_BASE_URL` leaked the API key, before the trust dialog; fixed [S Check Point].
  - I found no reported malicious plugin inside Anthropic's own Claude Code marketplaces [S, absence of evidence
    only].

### 5.2 Rules to adopt (proposed)

1. **Imitate by default; install by exception.** A technique from a third-party plugin is rebuilt in our own
   agents and gates. A third-party plugin is installed only when it brings something we cannot rebuild cheaply
   (an LSP integration, a licensed scanner, `claude plugin eval`), and never into every project by default.
2. **No third-party code-executing components in the shared baseline.** Hooks, monitors, MCP/LSP servers, mods
   and `bin/` from outside Anthropic's `plugins/` directory and our own repository are pilot-only, per project, by
   decision-log entry.
3. **Pin by commit, update by pull request.** Every adopted plugin is re-listed in **our own marketplace** with a
   `github` or `git-subdir` source carrying `ref` **and** `sha` (archives: `sha256`), `autoUpdate: false`, and a
   bump is a reviewed PR, the same pattern as `.claude/FRAMEWORK_COMMIT`. Re-listing an Anthropic plugin under
   its own name may hit the reserved-plugin-name validation ("passes as one of Anthropic's own") [F message text;
   applicability U].
4. **Review checklist for every pin bump:** diff of `hooks/hooks.json`, `.mcp.json`, `.lsp.json`,
   `monitors/`, `bin/`, `settings.json`, `package.json` + lockfile; `claude --plugin-dir <dir> plugin details
   <name>` component inventory [F security]; data egress; calls to `gh` or shell env tokens; front-matter that
   would expand tool access; licence (Apache-2.0 for the official repository [F]; CC-BY-SA-4.0 for Trail of Bits
   [F] means imitate, never paste).
5. **Permissions stay ours.** MCP tools from any plugin are denied unless a `permissions.allow` rule names
   `mcp__plugin_<plugin>_<server>__<tool>` [F naming]; read-only doc tools only.
6. **Fleet controls where an organisation manages Claude Code:** `strictKnownMarketplaces` with our marketplace,
   the official marketplace and `{ "source": "skills-dir" }`; `disableSideloadFlags: true`; managed
   `enabledPlugins` for the framework plugin if we ship one; `DISABLE_AUTOUPDATER` or per-marketplace
   `autoUpdate: false`; `pluginTrustMessage` pointing at our review rule [F org]. If the organisation sets
   `allowManagedHooksOnly` or `strictPluginOnlyCustomization`, our hooks and agents must arrive as a force-enabled
   plugin [F org].
7. **CI:** bake plugins into a seed directory at image build, from the pinned marketplace; do not use
   `claude-code-action`'s `plugin_marketplaces` until it can pin (issue #1229) [F]; assert the `init` event's
   plugin list in the job log [F org].
8. **Kiro:** install powers only from a local path of a pinned checkout (no pinning or auto-update control is
   documented [F]); share only `SKILL.md` and MCP definitions across clients; govern MCP with the enterprise MCP
   registry allow-list where available [S].
9. **Every checker prompt carries the untrusted-input line** (technique 7), because checkers read issue bodies,
   diffs and plugin output.
10. **Telemetry for audit:** export OTel `plugin_loaded` with `OTEL_LOG_TOOL_DETAILS=1` where an organisation
    collects it, so third-party plugin names are not redacted [F security]. (An environment variable: same
    open question as §2.4.)

### 5.3 Open questions for the operator (not decided here)

- Package `clients/claude/` agents, commands and hooks as a plugin (for `claude plugin eval` and for
  organisations that lock customisation to plugins), keeping rules and scripts on the existing installer?
- Does a CI job environment count as a "shell environment variable" under `no-environment-vars.md` (seed dir,
  sync install, OTel detail flag)?

---

## 6. Sources

Claude Code documentation (all [F]):
- https://code.claude.com/docs/en/plugins (overview)
- https://code.claude.com/docs/en/plugins/components.md
- https://code.claude.com/docs/en/plugin-marketplaces (create a marketplace)
- https://code.claude.com/docs/en/plugins/marketplace-reference.md
- https://code.claude.com/docs/en/plugins/host-marketplace.md
- https://code.claude.com/docs/en/plugins/loading.md
- https://code.claude.com/docs/en/plugins/org.md
- https://code.claude.com/docs/en/plugins/security.md
- https://code.claude.com/docs/en/plugins/anthropic-marketplaces.md
- https://code.claude.com/docs/en/plugins/code-intelligence.md
- https://code.claude.com/docs/en/plugin-evals.md
- https://code.claude.com/docs/en/settings-reference.md (first 100,000 characters read)

Anthropic repositories:
- https://github.com/anthropics/claude-plugins-official, `tree/main/plugins`, `tree/main/external_plugins` [F]
- `plugins/code-review/commands/code-review.md` (raw) [F]
- `plugins/pr-review-toolkit` README and `agents/silent-failure-hunter.md` [F]
- `plugins/feature-dev`, `security-guidance`, `claude-security`, `hookify`, `claude-md-management`, `receipts`,
  `code-modernization`, `project-artifact`, `ralph-loop` READMEs [F]; `code-simplifier`, `session-report`,
  `skill-creator` [F, partial page content]
- https://github.com/anthropics/claude-plugins-community [F]
- https://github.com/anthropics/skills [F]; `skills/webapp-testing` [F, partial]; document-skill licence [U]
- https://github.com/anthropics/claude-code-action/issues/1229 [F]; issue #850 [S]

Kiro:
- https://kiro.dev/docs/powers/create/ [F]; https://kiro.dev/docs/powers/installation/ [F]
- https://kiro.dev/docs/skills/, https://kiro.dev/docs/custom-agents/configuration-reference/,
  https://kiro.dev/docs/enterprise/governance/ [S]
- Agent Plugins 1.0: https://composio.dev/content/what-are-agent-plugins,
  https://startdebugging.net/2026/08/agent-plugins-1-0-vs-vendor-specific-plugin-formats/ [S]

Community and vendor:
- https://github.com/wshobson/agents [F]; https://rywalker.com/research/wshobson-agents [S]
- https://github.com/obra/superpowers [F]
- https://github.com/nizos/tdd-guard [F]
- https://github.com/trailofbits/skills [F]
- https://github.com/hesreallyhim/awesome-claude-code [F]
- https://github.com/semgrep/guardian and issue #46 [S]; https://semgrep.dev/guardian/ [S]
- https://github.com/snyk/claude-plugin-snyk [S]
- https://github.com/getsentry/sentry-for-ai, https://github.com/getsentry/skills [S]
- https://github.com/awslabs/agent-plugins [S];
  https://docs.aws.amazon.com/securityagent/latest/userguide/code-review-ide-integration.html [S]
- https://github.com/awslabs/aidlc-workflows, https://awslabs.github.io/aidlc-workflows/ [S]
- https://github.com/github/spec-kit [S]
- https://github.com/hagaybar/docs-sync-plugin,
  https://github.com/borghei/Claude-Skills/blob/main/engineering/doc-drift-detector/SKILL.md,
  https://github.com/xiaolai/docs-guardian-for-claude [S]
- https://developertoolkit.ai/en/claude-code/operate/performance/,
  https://github.com/michael-denyer/pstack-claude/blob/main/plugins/pstack/skills/benchmark-checklist/SKILL.md [S]

Incidents:
- https://microsoft.com/en-us/security/blog/2026/10/30/inside-malicious-claude-code-branded-cursor-extension-persistent-ssh-backdoor [F]
- https://securityweek.com/malicious-claude-code-extension-served-in-cursor-supply-chain-attack [S]
- https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/ [S]
- https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html [S]
- https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/ [S]
