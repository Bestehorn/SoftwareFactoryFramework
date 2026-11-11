# MCP servers and Kiro powers for the issue state model (research, 2026-11-10)

> Record from the factory state-model design discussion (2026-11-09 to 2026-11-11), copied from the working notes. Paths to working files were rewritten to this folder; the text is otherwise as written. Where it differs from `docs/design/factory-state-model/decisions.md`, that file wins.

Status: research only. Nothing in the framework was changed. This file complements
`checker-landscape.md` (sections 0, 2, 3) and does not repeat it: tools covered there (cdk-nag, cfn-lint, OSV-Scanner,
Security Agent and DevOps Agent as services, CodeRabbit, ...) appear here only where their **MCP server, plugin or
power** adds something.

Verification legend (same as the landscape study):

- **[F]** read on the primary page in this session.
- **[S]** from web-search result summaries that cite the named page; I did not open the page.
- **[U]** unverified: conflicting sources, background knowledge, or not found.

What the framework has today (read in this repository): `prompts/setup-claude.txt` configures five stdio servers,
`aws-documentation`, `aws-iac`, `aws-api` (with `READ_OPERATIONS_ONLY=true`), `strands-agents` and
`bedrock-agentcore`. Its example uses `@latest`, but the text tells the operator to pin `<pkg>==x.y.z`. It
auto-allows `mcp__awslabs.aws-api-mcp-server__*` and forbids `AWS_PROFILE` in any `env` block [F, repo].

---

## 0. Summary

1. **awslabs/threat-modeling-mcp-server is a structure server, not an analyser.** It exposes 11 tools for a
   9-phase STRIDE workflow. It keeps the model in memory, makes no LLM or network calls ("calls the existing agent's
   LLM") and needs no AWS credentials. It exports `.tc.json` (Threat Composer), `.md` and `.extended.json` [F]. The
   threat analysis is done by the *client's* model, so it is a **maker** tool for a SPEC-time threat-model lane.
   Its independence as a checker is nil. Maturity is low: v0.2.0 in `pyproject.toml`, **no releases or tags**,
   18 commits from 2025-12-12 to 2026-11-04, install from `git+https` [F].
2. **The awslabs catalog consolidated in 2026.** The CDK, CloudFormation and Cloud Control servers merged into the
   **AWS IaC MCP server**. The diagram, code-doc-gen, frontend, git-repo-research and synthetic-data servers are
   deprecated, and the **IAM MCP server** is deprecated in favour of the managed **AWS MCP Server** [F]. AWS tells
   users to replace the local `aws-api` and `aws-knowledge` servers with the AWS MCP Server [F].
3. **The highest-value AWS servers for checkers are read-only and partly deterministic.** The IaC server runs
   cfn-lint and cfn-guard locally with no credentials, and troubleshoots failed stacks by matching 30+ known
   patterns [F]. CloudWatch, CloudTrail and Application Signals are read-only telemetry servers, which makes them the
   raw material for **TEST-READY failure attribution** [F]. The Well-Architected Security Assessment server reads
   Security Hub, GuardDuty, Inspector and Access Analyzer read-only [F].
4. **Read-only must be enforced in IAM, not only by server flags.** AWS bulletins in 2026 list several awslabs MCP
   CVEs. Examples: the `aws-api-mcp-server` skipped its per-request policy check for the process lifetime when
   policy loading failed (CVE-2026-16584, fixed 1.3.47) [F]; the Security Agent server had an argument injection in
   diff scan (CVE-2026-97662, fixed 0.2.0) [F]. The managed AWS MCP Server adds the IAM condition keys
   `aws:ViaAWSMCPService` and `aws:CalledViaAWSMCP` [F], and its proxy has a `--read-only` flag [F].
5. **Kiro powers** live at kiro.dev/powers. The GitHub repo `kirodotdev/powers` holds only a subset (37 directories)
   [F]. Since CLI 2.25.0 (2026-09-28), `kiro-cli powers install <name|path>` works without chat [F]. Docs do not say
   whether keyword activation happens in `--no-interactive` runs [U], and **no power pinning mechanism is
   documented** [F]. Every power `mcp.json` I opened launches its servers with `@latest` [F].
6. **Claude Code's headless runs load a repository's `.mcp.json` without asking** [F], so a PR could add a server to a
   checker. Checker sessions must run with `--strict-mcp-config --mcp-config <framework file>`, or with
   `includeMcpJson: false` and an explicit `tools` list in Kiro [F].
7. **The GitHub and GitLab MCP servers conflict with `use-git-wrapper-scripts.md`.** They carry their own token
   handling. The useful part (code-scanning, secret-scanning and Dependabot alerts; GitLab `code_security`) belongs
   in **wrapper subcommands**, not in an MCP server.
8. **Vendor SAST/SCA MCP servers add little over their CLIs** in a deterministic pipeline. The standalone Semgrep MCP
   repository is archived; the server now ships in the `semgrep` binary [F]. Snyk and SonarQube need accounts. Their
   only extra is a maker's shift-left loop ("scan the snippet before writing it").
9. **For "run the thing", Playwright MCP is the one to pilot**, run with `--headless --isolated
   --allowed-origins=<stage>`. Its README states it "is not a security boundary" [F]. The E2E gate stays a committed
   script (`always-test-e2e.md`).

---

## 1. awslabs/threat-modeling-mcp-server (question 1)

### 1.1 What it does

| Aspect | Finding |
|---|---|
| Tools (11) [F] | Workflow: `manage_workflow`, `export_threat_model`. Context: `manage_system_context`. Domain managers: `manage_assumptions`, `manage_architecture`, `manage_threat_actors`, `manage_trust_boundaries`, `manage_asset_flows`, `manage_threats`. Data and validation: `inspect_data_models`, `manage_code_validation`. All CRUD tools gained batch operations (May 2026) [F, commit log] |
| Methodology [F] | STRIDE, run "in phases rather than quick conclusion". Phases: 1 business context, 2 architecture, 3 threat actors, 4 trust boundaries, 5 asset flows, 6 threat identification, 7 mitigation planning, 7.5 code validation (optional), 8 residual risk, 9 output. System context carries "software, data, user, and NFR taxonomy profiles". No MITRE ATT&CK, OWASP or LINDDUN mapping is documented [F] |
| Reads code? [F] | The **client** reads the code. The server "records evidence supplied by the client after it inspects the implementation". Phase 7.5 "fails the phase closed until every current threat and mitigation is covered". The server walks the file system only to detect whether source code is present; PR #23 (2026-11-04) fixed false negatives in that detection [F] |
| Inputs [F] | Prompts, design docs, an attached architecture image (example prompt), the project directory |
| Outputs [F] | In `<project>/.threatmodel/`: `<base>.tc.json` (Threat Composer importable, deterministic UUIDs, schema `maxLength` enforced; truncated fields are listed in the tool response), `<base>.md`, `<base>.extended.json` (server state, not importable) |
| State [F] | In memory per process. Exports are snapshots "not automatically loaded in a later session". A headless run must finish all phases in one session |
| LLM / network [F] | None of its own: "All tools are internal to the server and do not make external API calls" |
| Credentials [F] | None documented |

### 1.2 Maturity and how it runs

- Apache-2.0, 125 stars, 22 forks. `pyproject.toml` says version 0.2.0, Python `>=3.10`, dependencies
  `mcp[cli]>=1.6.0,<2.0.0`, `pydantic`, `loguru` [F]. **No releases or tags** [F]. Commits run from 2025-12-12 to
  2026-11-04; the recent ones harden code scan, export and logging [F].
- stdio via `uvx --from git+https://github.com/awslabs/threat-modeling-mcp-server.git threat-modeling-mcp-server`
  [F]. Since there are no tags, the only pin is a commit SHA in the git URL (`...git@<sha>`). That is standard uv/pip
  VCS syntax, but I did not test it for this repository [U].
- **Kiro:** the README configures `~/.kiro/settings/mcp.json`. The repository ships a Kiro CLI agent
  (`.kiro/agents/threat-modeler.json`, prompt `.kiro/prompts/threat-modeler.md`, per-phase skills in `.kiro/skills/`).
  The README's headless form is `kiro-cli chat --agent threat-modeler --no-interactive "Threat model this project"`
  [F]. The README's sample config auto-approves all 11 tools [F]. That is acceptable only because the server has no
  network access or credentials.
- **Claude Code:** not documented [F]. A generic stdio server works in `.mcp.json` or in a subagent's `mcpServers`
  frontmatter [F, Claude Code docs]. Untested here [U].

### 1.3 Where it fits

- **SPEC-REQUIRED, maker side of a "threat-model lane"** (tier L, or risk tags auth, money, iam-iac). The maker
  agent drives phases 1–9 against `design.md` and writes `.threatmodel/<issue>.tc.json` next to the spec.
  Checkers: the security-reviewer reads the `.tc.json` and `.md`, and a deterministic step validates the `.tc.json`
  against the Threat Composer schema. The landscape's ASVS citation rule applies to the mitigations.
- **IMPLEMENTATION-READY, phase 7.5:** the implementer records evidence for each mitigation; the server refuses to
  close until every threat is covered. That is a **maker-side completeness gate**. maker ≠ checker still needs the
  security-reviewer or the adversarial-verifier to check that evidence against the diff.
- **Not a checker on its own:** the analysis comes from the same model family as the maker. Its value is structure,
  completeness and a schema-bound artefact, not independent signal.

### 1.4 Comparison

| | threat-modeling-mcp-server | Threat Composer + threat-composer-ai | AWS Security Agent threat model / design review |
|---|---|---|---|
| Engine | Client's LLM; server is deterministic bookkeeping [F] | Composer: web app, VS Code extension and browser extension that edit `.tc.json` [F]. `threat-composer-ai`: Strands multi-agent generator on **Bedrock** ("Status: Experimental") [F] | AWS-hosted LLM agent (Security Agent, now "AWS Continuum") [F] |
| Inputs | Prompt, docs, image, project dir [F] | `threat-composer-ai-cli /path/to/code` [F] | Scope docs (DOC, DOCX, JPEG, MD, PDF, PNG, TXT, S3, Confluence) and/or sources (GitHub, GHES, GitLab, GitLab Self-Managed, Bitbucket, S3) [F] |
| Output | `.tc.json`, `.md`, `.extended.json` [F] | `threatmodel.tc.json` and component files [F] | System overview plus STRIDE threats with High/Medium/Low severity in the web app [F]. The Kiro/Claude skill writes `.security-agent/threat_model.md` [F, AWS blog]. A Threat Composer export was not found [U] |
| Credentials, cost | None [F] | `bedrock:InvokeModel`, token cost [F] | AWS account, Agent Space, IAM role, S3 [F]. Preview pricing not stated on the blog [F]; "free in preview" [S, landscape] |
| Headless | Kiro CLI `--no-interactive` [F]; Claude stdio [U] | CLI "suitable for CI/CD" [F]; MCP `threat-composer-ai-mcp` [F] | CLI `aws securityagent create-threat-model` / `start-threat-model-job` [S]; Claude plugin and Kiro power [F] |
| Independence from the maker | None (same model) | Partial (another agent stack, but a Claude model on Bedrock) | **High** (separate service, org security requirements packs) |
| Maturity | v0.2.0, no releases [F] | Composer v1.0.91, 2026-11-06 [F]; the AI part is experimental. Model naming conflicts: README `global.anthropic.claude-sonnet-5`, a June release note "Claude Sonnet 4.5" [F] | Threat modelling in preview since 2026-06-17 [F] |
| Best use | Maker for the SPEC threat-model lane | The `.tc.json` **schema** as the artefact format. Optionally one repo-wide baseline per project | Independent checker for L or risk-tagged specs, batched |

---

## 2. The awslabs MCP catalog (question 2)

### 2.1 Catalog state

- awslabs.github.io/mcp lists 61 servers in 10 categories [F]. It labels the managed **AWS MCP Server** "in
  preview" [F], while the Agent Toolkit README calls it generally available [F]. That is a conflict; treat the
  service as GA with an unstable tool surface [U].
- Deprecated, with replacements [F, awslabs/mcp README]: `cdk-mcp-server`, `cfn-mcp-server` and `ccapi-mcp-server`
  → `aws-iac-mcp-server`; `aws-diagram-mcp-server` → a diagram agent skill; `git-repo-research-mcp-server` →
  Context7; `code-doc-gen`, `syntheticdata` and `frontend` → native model abilities or Kiro specs;
  `cost-explorer` → `billing-cost-management`; `core-mcp-server` → configure servers individually;
  `iam-mcp-server` → AWS MCP Server [F]. The local ECS server points to a managed ECS MCP server [F].
- Every README I read installs with `@latest` [F]. The framework's own setup prompt already says to pin.

### 2.2 Servers relevant to makers or checkers

Role abbreviations: M = maker, C = checker. Credentials: "none", "RO" (read-only IAM) or "MUT" (mutating).

| Server | What it gives | State · role | Det / LLM | Credentials | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| **AWS IaC MCP** (`awslabs.aws-iac-mcp-server`) | 9 tools. `validate_cloudformation_template` (cfn-lint), `check_cloudformation_template_compliance` (bundled cfn-guard rules; which pack is not stated), `troubleshoot_cloudformation_deployment` (30+ patterns, optional CloudTrail), CDK/CFN doc search, `cdk_best_practices`, pre-deploy validation instructions [F] | IMPL M (inner loop on synthesized templates) · IMPL C (devops-iac-reviewer) · TEST C (failed-deploy attribution) · REWORK M | Validate, compliance, troubleshoot: deterministic. Doc search: backend not documented [F] | Validation: none. Troubleshoot: CFN `Describe*` plus `cloudtrail:LookupEvents`, RO [F] | v1.0.26, 2026-09-08 [F] · Apache-2.0 | Response data goes to the model provider (privacy notice) [F] | **Adopt** (already configured). Pin it; the CI gate still calls cfn-lint and cfn-guard directly |
| **AWS Knowledge MCP** (remote `https://knowledge-mcp.global.api.aws`) | `search_documentation`, `read_documentation`, `list_regions`, `get_regional_availability`, `retrieve_skill`; covers docs, What's New, blogs, Well-Architected, CDK/CFN, Strands [F] | SPEC M (spec-author, researcher) · SPEC/IMPL C (best-practice, devops-iac) · START M (region feasibility) | Deterministic retrieval | **None**; rate limited [F] | GA [F] | Low (AWS-authored content) | **Adopt**, replacing the local docs server |
| AWS Documentation MCP (local) | `read_documentation`, `search_documentation`, `read_sections`, `search_table`, `recommend` [F] | Same as Knowledge | Deterministic | None [F] | awslabs | Low | **Skip**, except as a fallback where remote MCP is blocked |
| **AWS MCP Server** (managed; `mcp-proxy-for-aws-cli` for SigV4) | `call_aws` to 300+ services, docs, skills, sandboxed scripts [F]. Proxy `--read-only` keeps only `readOnlyHint=true` tools [F]. Condition keys `aws:ViaAWSMCPService` and `aws:CalledViaAWSMCP` [F]. CloudTrail-audited [F]. Regions include eu-central-1, eu-west-1, eu-west-2 [F] | TEST C (inspect stage) · REWORK M (diagnose) · CLOSE C (leftover resources) | Deterministic API calls; the agent picks them | SigV4 or OAuth. **Read-only mode needs SigV4** [F] | GA or preview (conflict) · proxy Apache-2.0 [F] | Wide blast radius if the role is not read-only | **Pilot**: proxy `--read-only`, a read-only role, and a deny policy on `aws:ViaAWSMCPService`. It replaces `aws-api-mcp-server` |
| AWS API MCP (local) | `call_aws`, `suggest_aws_commands`. `READ_OPERATIONS_ONLY`, `REQUIRE_MUTATION_CONSENT`, deny lists, workdir sandbox, telemetry on by default [F] | as above | Deterministic | Local profile | 2026 CVEs: policy check skipped after init failure (fixed 1.3.47) [F]; file-access bypass (fixed 1.3.9) and OAuth audience (fixed 1.6.0) [S] | README: "Do not connect ... to data sources with untrusted data" [F] | **Skip** for new work; migrate to the AWS MCP Server. Today `prompts/setup-claude.txt` auto-allows all its tools |
| **CloudWatch MCP** | Metrics, alarms, `analyze_log_group` (anomalies, error patterns), Logs Insights incl. cross-region batch, PromQL [F] | TEST C (failure attributor, verdict watcher input) · REWORK M | Deterministic queries | RO `cloudwatch:*` and `logs:*` reads [F] | awslabs; licence not stated in excerpt [U] | **Logs carry untrusted user input**, so this is a prompt-injection path | **Adopt** in read-only sessions |
| **CloudTrail MCP** | `lookup_events`, CloudTrail Lake SQL [F] | TEST C (who changed what in the shared account: click-ops, a sibling deploy) · REWORK M | Deterministic | RO [F]; Lake queries are billed [U] | awslabs | Low | **Adopt** |
| CloudWatch Application Signals MCP | `audit_services`, `audit_slos`, `analyze_canary_failures`, spans, X-Ray, RUM, `list_change_events`; **mutating** `create_instrumentation` and `delete_instrumentation` [F] | TEST C (SLO and canary verdict after a batch deploy) | Deterministic | RO, except the instrumentation tools | awslabs | Instrumentation tools change resources | **Pilot** where Application Signals is on; deny both instrumentation tools |
| Well-Architected Security Assessment MCP | `CheckSecurityServices`, `GetSecurityFindings`, `GetResourceComplianceStatus`, `GetStoredSecurityContext`, `ExploreAwsResources`, `AnalyzeSecurityPosture` [F] | TEST C (new findings after a batch deploy) · CLOSE C (posture retro) | Deterministic reads plus a framework mapping | RO security services [F] | Apache-2.0 [F] | Needs Security Hub, GuardDuty and Inspector enabled | **Pilot**, per batch or weekly, not per issue |
| AWS Pricing MCP | `get_pricing`, `analyze_cdk_project`, `analyze_terraform_project`, `generate_cost_report` [F] | SPEC M (cost note in design) | API deterministic; the filters are built by the LLM ("cannot guarantee" correct filters) [F] | `pricing:*`, public data, free [F] | awslabs | Wrong estimates | **Pilot** for M+ with new billable resources (landscape §2.11) |
| Billing and Cost Management MCP | Replaces Cost Explorer [F] | CLOSE C (actual cost of the batch vs the design estimate) | Deterministic | Billing reads [U] | awslabs | Low | **Pilot**, low priority (tools not researched [U]) |
| **AWS Security Agent MCP** (`awslabs.security-agent-mcp-server`) | `setup_check`, `setup` (creates Agent Space, IAM role, S3 bucket), `start_security_scan` (zips and uploads code), `get_scan_status`, `get_scan_findings`, `list_scans`, `stop_scan`, `call_api` (any SecurityAgent operation, **including pentests**), `get_api_guide` [F] | SPEC C (threat model on spec) · IMPL C (diff scan, risk tags) · TEST C (pentest) | LLM SaaS | **MUT**: IAM role creation, S3 write, scans, pentests [F] | v0.2.2, 2026-11-09, PyPI trusted publishing [F]; CVE-2026-97662 fixed 0.2.0 [F] | Code leaves the repo; cost per scan and pentest [F]; `call_api` is unbounded | **Pilot** for L and risk tags. `setup` runs once by a human; the checker role cannot create IAM or start pentests |
| AWS DevOps Agent remote MCP (`https://connect.aidevops.{region}.api.aws/mcp`) | Investigations, chat; release readiness and release tests through the `aws-agents-for-devsecops` skills [F] | TEST C (batch release readiness) · REWORK M (root cause) | LLM SaaS | Bearer token or SigV4 [F] | Remote; skills listed [F] | The Kiro power passes the token as **environment variables** [F], which conflicts with `no-environment-vars.md` | **Pilot** (landscape §2.3) |
| AWS Serverless MCP | `sam_*` and `deploy_webapp` behind `--allow-write`; read-only `sam_logs`, `get_metrics`, `get_iac_guidance`, schemas; logs need `--allow-sensitive-data-access` [F] | IMPL M (SAM projects only) | Deterministic | MUT with the flag | Path-traversal CVE fixed v0.2.1 [S] | Deploys outside the pipeline | **Skip** unless the project uses SAM; never `--allow-write` |
| AWS Lambda Tool MCP | Exposes filtered functions as tools [F] | TEST (run a smoke Lambda) | Deterministic | `lambda:InvokeFunction` [F] | awslabs | Invocation is a side effect [F] | **Skip**; smoke stays a script |
| Amazon ECS MCP | `ecs_troubleshooting_tool` (CFN status, service events, task failures, task logs, image-pull failures, network) [F]; `ALLOW_WRITE` and `ALLOW_SENSITIVE_DATA` default false [F] | TEST C, REWORK M (ECS projects) | Deterministic | RO by default | Superseded by a managed ECS MCP [F] | — | **Pilot** only for ECS projects |
| IAM MCP | CRUD on users, roles and policies; `--readonly`; `simulate_principal_policy` [F] | — | Deterministic | **MUT by default** [F] | **Deprecated** [F] | — | **Skip**; use the AWS MCP Server read-only, or the Access Analyzer CLI |
| IAM Policy Autopilot (awslabs; MCP and CLI) | Static analysis of SDK calls (Python, TS/JS, Go, Java, Terraform plan) → baseline identity policy; `--explain`; `fix-access-denied` [F] | IMPL M (least-privilege policy for new code) · IMPL C input (actions the code needs vs actions the CDK grants) | **Deterministic** [F] | None for `generate-policies`; fixes need credentials [F] | Apache-2.0, 505 stars [F] | `fix-access-denied` mutates IAM | **Pilot**: the CLI in `run_checks`, the MCP for makers; never give `fix-access-denied` to a checker |
| Bedrock KB Retrieval, Kendra, Q index | Org knowledge with citations [F] | SPEC C (only if org security requirements live in a KB) | Retrieval | RO | awslabs | Low | **Skip** by default |
| Document Loader | Parses documents [F] | START/SPEC M (attached PDF/DOCX) | Deterministic | None [U] | awslabs | Attachments are untrusted content | **Skip**; the Read tool already reads PDFs |
| OpenAPI, Step Functions, SNS/SQS, data servers (DynamoDB, Aurora, ...) | Execute APIs, workflows, queries [F] | — | Deterministic | MUT or data access | One example of a read-only bypass: `mysql-mcp-server` (fixed 1.0.23) [S] | Shared-account data and side effects | **Skip** for all roles |
| Deprecated servers (§2.1) | — | — | — | — | Deprecated [F] | Unmaintained | **Skip** |

---

## 3. Other MCP servers (question 3)

| Server | What it gives | State · role | Det / LLM | Credentials | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| GitHub MCP (`github/github-mcp-server`) | Toolsets `code_security`, `secret_protection`, `dependabot`, `security_advisories`, `actions`, `pull_requests`... [F]. `--read-only` [F]. Lockdown mode filters content from users without push access in public repos ("best-effort", "not an authorization boundary") [S] | IMPL C (alerts on the PR SHA) · START C (search) | Deterministic alert data | PAT, OAuth or GitHub App, outside `credentials/` [F] | MIT [F]. CVE-2026-48529: the lockdown cache in HTTP mode used the first user's client [S] | Bypasses the wrapper; issue and PR text is untrusted | **Skip.** Add wrapper subcommands for code-scanning, secret-scanning and Dependabot alerts instead |
| GitLab MCP (official) | Toolsets `core`, `merge_requests`, `work_items`, `repository`, `ci` by default; `code_security`, `wikis`, `orbit` opt-in via `X-Gitlab-Enabled-Mcp-Server-Toolsets` [F]. No read-only mode stated [F] | IMPL C (vulnerabilities), TEST (pipelines) | Deterministic | OAuth with `mcp` scope, fine-grained PAT [F] | GA in 19.5; Free tier since 19.2 [F]. One search result said "beta, Premium" [S], contradicted by the primary page | Same wrapper conflict. Community `zereight/gitlab-mcp` had CVE-2026-61559 (SSRF) and CVE-2026-61560 (unauthenticated SSE) [S] | **Skip**; add wrapper subcommands. Never the community server |
| Semgrep MCP | `security_check`, `semgrep_scan`, `semgrep_scan_with_custom_rule`, AST, rule schema [F]. Standalone repo **archived 2025-10-28**; now in the `semgrep` binary [F] (≥1.146.0 [S]). "Semgrep Guardian" plugin hooks send written files to `scanner.semgrep.ai` [S] | IMPL M (shift-left scan before a write) | Deterministic | None; a token unlocks Pro tools [S] | MIT for the MCP [F]; rules licence per landscape §2.2 | Guardian sends code to the vendor [S] | **Skip** as a checker (the CLI gate is better). Possible maker **pilot**, local-only, no token |
| Snyk MCP (`snyk mcp`) | 14 tools: SCA, Code, IaC, container, SBOM, secrets, AI-BOM; local only; profiles `lite`, `full`, `experimental` [S] | IMPL M or C | Hybrid (SaaS engine) | Snyk account | Snyk CLI | SCA "may run build tools" on untrusted projects [S] | **Skip** unless the org licenses Snyk |
| SonarQube MCP | 50+ tools: snippet and file analysis, issues, quality gates, hotspots, dependency risks, coverage, duplications [F]. `SONARQUBE_READ_ONLY`, `SONARQUBE_TOOLSETS`, pinnable image tags, telemetry on [F] | IMPL C (quality gate on the SHA) | Deterministic | Sonar token; Server 2025.1+ or Cloud [F] | **SONAR Source-Available License v1.0** [F] | Low with read-only | **Skip** unless the org runs Sonar |
| **Context7** (`https://mcp.context7.com/mcp`) | `resolve-library-id`, `query-docs` for current library docs [F]. Content "community-contributed", accuracy and security not guaranteed [F] | SPEC M, IMPL M (non-AWS libraries: pytest, Hypothesis, React, Vitest...) · best-practice-reviewer | Retrieval | Optional key [F] | MIT [F]. "ContextCrush" (Feb–Mar 2026): library "custom rules" passed unfiltered to agents, demonstrated `.env` exfiltration; vendor says fixed [S]. CVE-2026-75130 (fix disputed) [S]. Issue #2673 reported an instruction embedded in `query-docs` output [S] | **Prompt injection through docs** | **Pilot** for makers and best-practice only; output treated as data; library allowlist where offered [S] |
| **Playwright MCP** (`@playwright/mcp`) | Accessibility-tree browser automation; opt-in caps `testing`, `codegen`, `vision`, `pdf`, `devtools`; `--headless`, `--isolated`, `--allowed-origins`, `--blocked-origins`, `--secrets` [F] | TEST M (write E2E scripts), TEST C (reproduce a smoke failure on stage), REWORK M | Deterministic driver, agent-driven | Stage test principal only | Apache-2.0, Microsoft [F] | "not a security boundary"; page text can inject [F] | **Pilot**, pinned, `--isolated --headless --allowed-origins=<stage>` |
| Sentry MCP | Issues, events, Seer root cause; "AI-powered search tools require an LLM provider" [F]; `MCP_SKILLS` limits [F] | TEST C, REWORK M (only if the project uses Sentry) | Mixed (embedded LLM) | Sentry token, plus an LLM key for search | OSS [F] | Event payloads are untrusted | **Skip** by default |
| OSV MCP servers | StacklokLabs `osv-mcp` (`query_vulnerability`, `query_vulnerabilities_batch`, `get_vulnerability`) [S]; an official `osv-scanner` MCP was not confirmed [S/U] | IMPL C | Deterministic | None | Third-party | Unvetted publishers | **Skip**; the OSV-Scanner CLI gate (landscape) covers it |
| Mutation and coverage MCPs | `mutmut-mcp` (runs mutmut 3, ranks survivors), `stryker-mcp-reporter` (unofficial, German tool descriptions), `coverctl`, `test-coverage-mcp` [S] | IMPL C (adversarial-verifier) | Deterministic | None | Single-maintainer projects | Unvetted | **Skip**; call mutmut, Stryker and diff-cover from `run_checks` |
| Kiro catalog testing powers | Postman, Swagger contract testing (SmartBear), Amazon Nova Act browser automation, ScoutQA [F, listing only] | TEST M | Mixed | Vendor accounts [U] | Vendor | — | **Skip**, not researched beyond the listing [U] |

**MCP Registry** (registry.modelcontextprotocol.io): still in preview, "breaking changes or data resets may occur" [F].
It verifies **namespace** ownership (GitHub, DNS or HTTP) and **package** ownership (npm `mcpName`; an `mcp-name:`
string in the PyPI, NuGet or Cargo README; an OCI annotation) [F]. It does **no security vetting** (none described)
[F]. Integrity: MCPB entries *must* carry `fileSha256`, which "the MCP Registry does not validate", clients do [F].
OCI images can be pinned by putting a digest in `identifier` [F]. npm and PyPI entries have no hash field [S].
**Use it for discovery only**; trust comes from pinning (section 6).

---

## 4. Kiro powers (question 4)

- **What a power is:** an Agent Plugins bundle, `plugin.json` (with activation keywords), `skills/` and an optional
  `mcp.json`. The older POWER.md format still works [F]. A power loads "dynamically based on keywords" [F].
- **Where:** kiro.dev/powers is the full registry. `github.com/kirodotdev/powers` holds 37 of them; others are
  hosted by their authors [F]. Install from the IDE panel, a GitHub URL or a local folder [F]. Kiro's docs say powers
  are third-party and you should review "the power's source and the access it requests" [F].
- **Headless:**
  - `kiro-cli powers install|uninstall <name|path>` works without chat (CLI 2.25.0, 2026-09-28) [F].
  - V3 `--no-interactive` runs load hooks from the selected agent and workspace (2.27.1) [F].
  - A tool that needs approval is denied in headless mode unless `--trust-tools` or `--trust-all-tools` covers it [F].
  - Whether a power's *keyword activation* fires in a headless run is not documented [U].
  - **Recommendation:** headless checkers do not rely on powers. Copy the power's MCP entry, pinned, into the custom
    agent's `mcpServers`, set `includeMcpJson: false`, and list tools as `@server/tool` [F, agent config reference].
- **Pinning:** not documented. Updates are pulled by hand ("Check for updates") [F]. The `mcp.json` files I opened
  all use `@latest`: Security Agent power (`awslabs.security-agent-mcp-server@latest`), `aws-infrastructure-as-code`
  (`aws-iac-mcp-server@latest`, auto-approving its 5 doc tools), `aws-observability` (5 servers, all `@latest`) [F].
- **Claude Code equivalent:** plugins. The Agent Toolkit offers `aws-core` and `aws-agents-for-devsecops` [F].
  Plugins update "automatically when it refreshes its marketplace data" [F], which is another floating version.

| Power (publisher) | Contents | State · role | Headless | Rec |
|---|---|---|---|---|
| AWS Security Agent (`awssecurityagent`) | Security Agent MCP (`@latest`), steering, a hook that suggests a diff scan after each agent turn (`security-diff-scan-suggester.kiro.hook`) [S]; README billing warning [F]; Apache-2.0 [F] | SPEC C (spec threat model) · IMPL C (diff scan) · TEST C (pentest) | MCP yes; the hook in V3 headless [F, generic]; scans take 5–30 min [S] | **Pilot** for L and risk tags; drop the hook in autonomous runs (cost) |
| AWS DevOps Agent (`aws-devops-agent`) | Remote DevOps Agent MCP, falls back to `aws-mcp` [F]; token in `DEVOPS_AGENT_TOKEN` and `DEVOPS_AGENT_REGION` [F] | TEST C (release readiness) · REWORK M | Remote MCP yes | **Pilot**, but use SigV4 through `mcp-proxy-for-aws` instead of token environment variables |
| Build AWS infrastructure with CDK and CloudFormation (`aws-infrastructure-as-code`) | `aws-iac-mcp-server@latest` [F] | IMPL M and C | Yes | **Adopt** the server (pinned) directly, not the power |
| AWS Observability | CloudWatch, Application Signals, CloudTrail, Prometheus, docs servers (all `@latest`) [F] | TEST C, REWORK M | Yes | **Adopt** the servers, pinned and read-only; not the power |
| IAM Policy Autopilot | IAM Policy Autopilot MCP [F, catalog] | IMPL M | Yes | **Pilot** (section 2.2) |
| AWS SAM, Step Functions, Lambda durable functions, Amplify, ECS Express | Build and deploy helpers [F, listing] | IMPL M | — | **Skip** unless the stack uses them; their deploy tools never go to checkers |
| SonarQube, Snyk "Secure at Inception", Checkmarx, Aikido, Sonatype Guide | Vendor scanners [F, listing] | IMPL C | Vendor CLI | **Skip** unless licensed |
| Context7 | Docs [F, listing] | SPEC/IMPL M | Remote | **Pilot** under the section 3 caveats |
| Postman, Swagger contract testing, Nova Act, ScoutQA | API and browser testing [F, listing] | TEST M | — | **Skip** [U] |
| Build a Power, Power Builder | Authoring [F] | — | — | Relevant only if the framework ships its own power for Kiro users |

There is no threat-modelling power in the catalog other than the Security Agent's. The threat-modeling MCP server
ships a Kiro CLI *agent*, not a power [F].

---

## 5. Tables per state (the deliverable)

Columns: Role · Adds over what we have · Det/LLM · Credentials · Maturity/licence · Risk · Recommendation (reason).
"Have" means the landscape's deterministic plan plus the five servers the setup prompt configures.

### 5.1 START (triage)

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| AWS Knowledge `get_regional_availability` | M (triage feasibility) | Checks whether a named service, API or CFN resource exists in the stage region | Det | None | GA | Low | **Pilot**: cheap, only when the issue names AWS services |
| GitHub / GitLab MCP search | C (dedupe retrieval) | Nothing the wrapper cannot do | Det | Own token | MIT / GitLab | Wrapper bypass | **Skip**: extend the wrapper |
| Document Loader | M | Parses attachments | Det | None | awslabs | Untrusted content | **Skip**: Read covers it |

### 5.2 SPEC-REQUIRED

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| threat-modeling-mcp-server | M (threat-model lane) | Phased STRIDE, a fail-closed workflow, schema-bound `.tc.json` | Server det; analysis by the client LLM | None | v0.2.0, no releases · Apache-2.0 | Unpinned git install | **Pilot** for L and risk tags: structured artefact for free |
| Threat Composer schema check | C (det) | Validates the `.tc.json` artefact | Det | None | Composer v1.0.91 · Apache-2.0 | None | **Adopt**: free deterministic check |
| threat-composer-ai | M (alternative) | Code-to-threat-model generator | LLM (Bedrock) | `bedrock:InvokeModel` | Experimental | Cost | **Skip**: duplicates the lane; at most one repo baseline |
| Security Agent threat model (plugin skill, power or `call_api`) | C (independent) | Different vendor stack plus org requirement packs | LLM SaaS | MUT setup, S3 upload | Preview | Cost; docs leave the repo | **Pilot** for L + auth/money: the only independent threat-model checker |
| AWS Knowledge MCP | M + C | Current AWS docs and What's New for spec-author and best-practice | Det | None | GA | Low | **Adopt**: replaces the local docs server |
| AWS IaC MCP doc tools | C (devops-iac) | CDK best practices and samples | Retrieval | None | v1.0.26 | Low | **Adopt** (already configured) |
| AWS Pricing MCP | M (cost note) | Public price-list estimate | Det API, LLM filters | `pricing:*` | awslabs | Wrong filters | **Pilot** for M+ with billable resources |
| Context7 | M | Current non-AWS library docs | Retrieval | Optional key | MIT; injection history | Injection | **Pilot**, makers only |

### 5.3 IMPLEMENTATION-READY

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| AWS IaC MCP validate + compliance | M (inner loop) · C (devops-iac) | cfn-lint and cfn-guard inside the agent loop before CI | Det | None | v1.0.26 · Apache-2.0 | Low | **Adopt**: the gate stays the CLI |
| IAM Policy Autopilot | M (baseline policy) · C input | Code-derived required actions to compare with the CDK grants | **Det** | None for generate | Apache-2.0 | `fix-access-denied` mutates | **Pilot**: deterministic least-privilege signal nobody else gives |
| threat-modeling-mcp-server phase 7.5 | M (evidence) → C verifies | Every mitigation tied to code evidence | Det status | None | v0.2.0 | — | **Pilot** with the SPEC lane |
| Security Agent diff scan | C (independent) | Diff-focused, exploit-validated review | LLM SaaS | MUT (S3 upload) | v0.2.2; CVE fixed 0.2.0 | Cost; code leaves | **Pilot** for risk:auth/money |
| DevOps Agent release readiness (plugin skill) | C | Release verdict on PR/MR (landscape §2.3) | LLM + IAM proofs | Token / SigV4 | Preview | Environment-variable token | **Pilot** for risk:iam-iac |
| Semgrep `semgrep mcp` | M (shift-left) | Scans a snippet before writing | Det | None | CLI | Guardian uploads code | **Skip** as a checker; optional maker pilot |
| GitHub MCP security toolsets / GitLab `code_security` | C | Alert state on the SHA | Det | Own token | MIT / GitLab | Wrapper bypass | **Skip**: add wrapper subcommands |
| Snyk, SonarQube MCP | C | Vendor engines | Hybrid / det | Accounts | Vendor; Sonar source-available | — | **Skip** unless licensed |
| Mutation / coverage MCPs | C | Nothing over the CLIs | Det | None | Unofficial | Unvetted | **Skip** |
| Context7 | M | Library docs | Retrieval | — | — | Injection | **Pilot**, makers only |

### 5.4 TEST-READY (queue, CI, batched deploy to the shared account, smoke)

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| AWS IaC MCP `troubleshoot_cloudformation_deployment` | C (failed-deploy attributor) | 30+ known failure patterns plus CloudTrail correlation | Det | RO | v1.0.26 | Low | **Adopt**: fastest attribution of a red deploy |
| CloudWatch MCP | C (smoke-failure attributor) | Log anomalies and error patterns per log group; alarm history | Det | RO | awslabs | Injection via logs | **Adopt**, read-only session |
| CloudTrail MCP | C | Who or what changed the shared account; drift evidence | Det | RO | awslabs | Low | **Adopt** |
| Application Signals MCP | C (verdict watcher input) | SLO breaches, canary failures, traces, change events | Det | RO except instrumentation | awslabs | 2 mutating tools | **Pilot**: deny instrumentation tools |
| AWS MCP Server (`--read-only`) | C | Any other read-only check across 300+ services | Det | SigV4 RO role | GA/preview conflict | Over-broad role | **Pilot** as the single "inspect" server |
| Well-Architected Security Assessment | C (batch posture) | New Security Hub, GuardDuty and Inspector findings after deploy | Det | RO | Apache-2.0 | Services must be on | **Pilot**, per batch or weekly |
| DevOps Agent (remote MCP) | C | Batch release readiness and release tests | LLM SaaS | Token / SigV4 | Preview | Cost | **Pilot** for batches with iam-iac |
| Security Agent pentest (`call_api`) | C | Exploit-validated DAST (landscape §2.2) | LLM SaaS | MUT | GA | $50 per task-hour (landscape) | **Pilot**, batched and capped; never auto-approved |
| Playwright MCP | M (E2E authoring) · C (reproduce) | The agent "runs the thing" against stage | Det driver | Stage test principal | Apache-2.0 | Page injection | **Pilot**, restricted origins |
| ECS MCP troubleshooting | C | ECS task, image and network diagnosis | Det | RO default | Superseded | — | **Pilot** for ECS projects |
| Lambda Tool, OpenAPI, Step Functions | — | Side-effecting execution | Det | MUT | — | Side effects | **Skip**: smoke is a script |

### 5.5 REWORK-REQUIRED

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| CloudWatch, CloudTrail, IaC troubleshoot | M (diagnosis) | Evidence for the root cause on the failing SHA | Det | RO | awslabs | Injection via logs | **Adopt**, same read-only set as TEST |
| DevOps Agent investigation | M input | Root cause plus an agent-readable fix plan (landscape) | LLM SaaS | Token / SigV4 | GA (investigation) | Cost | **Pilot** |
| Security Agent remediation (`StartCodeRemediation`) | M | Vendor-generated fix PRs | LLM SaaS | MUT, opens PRs | — | PRs outside the flow | **Skip** auto-fix; consume findings only |
| threat-modeling-mcp-server code validation | C (delta) | Re-checks that mitigation evidence still holds | Det | None | v0.2.0 | — | **Pilot** with the lane |

### 5.6 CLOSE-READY

| Server / power | Role | Adds | Det/LLM | Creds | Maturity · licence | Risk | Rec |
|---|---|---|---|---|---|---|---|
| Billing and Cost Management MCP | C (retro) | Actual cost delta vs the design estimate | Det | Billing RO [U] | awslabs | Low | **Pilot**, low priority |
| AWS MCP Server (`--read-only`) | C (clean-up) | Finds leftover stage resources the issue created | Det | RO | — | — | **Pilot** |
| Well-Architected Security Assessment | C (retro) | Posture delta after the batch | Det | RO | Apache-2.0 | — | **Pilot** (shared with TEST) |
| threat-modeling `export_threat_model` (residual-risk phase) | M (retro artefact) | Final `.tc.json` with residual risk | Det | None | v0.2.0 | — | **Pilot** with the lane |
| Diagram skill / code-doc-gen | M | Deprecated or native [F] | — | — | — | — | **Skip** |

---

## 6. Ranked shortlist (top 10)

1. **AWS IaC MCP server**, pinned. A deterministic inner loop for CDK makers, plus deploy-failure attribution in
   TEST and REWORK. It is already configured.
2. **AWS Knowledge MCP** (remote, no credentials). Documentation grounding for spec-author, best-practice and
   devops-iac. It replaces the local docs server.
3. **CloudWatch MCP**, read-only role. The core of a TEST-READY smoke-failure attributor and REWORK diagnosis.
4. **CloudTrail MCP**, read-only. Shows who changed the shared account, and which batch or click-op broke it.
5. **AWS MCP Server through `mcp-proxy-for-aws --read-only`**, with a read-only role and a deny on
   `aws:ViaAWSMCPService` for writes. One audited inspection server for checkers; it retires `aws-api-mcp-server`.
6. **threat-modeling-mcp-server**, pinned to a commit. The maker of the SPEC threat-model lane (L or risk tags),
   producing `.tc.json` plus phase-7.5 evidence. Add a deterministic schema check on the artefact.
7. **IAM Policy Autopilot.** Deterministic "actions the code needs" to diff against the CDK grants: a least-privilege
   signal for iam-iac issues.
8. **AWS Security Agent** (MCP, plugin or power). The only *independent* checker for spec threat models and
   diff scans. Budget-capped, L and risk tags only, setup done by a human.
9. **AWS DevOps Agent remote MCP** (`aws-agents-for-devsecops`). Batch release readiness and root-cause analysis;
   SigV4, not token environment variables.
10. **Playwright MCP**, pinned, with `--headless --isolated --allowed-origins`. Lets an agent run the deployed thing
    to reproduce smoke failures and draft E2E scripts. The gate remains the committed script.

Next in line: Application Signals (where instrumented), Well-Architected Security Assessment (batch posture),
Context7 (makers only), Pricing (SPEC cost note).

Explicit skips:
- GitHub and GitLab MCP: wrapper rule; add wrapper subcommands instead.
- Semgrep, Snyk and SonarQube MCP: the CLIs are better, or they need accounts.
- IAM MCP: deprecated and mutating by default.
- Lambda Tool, Step Functions, OpenAPI: side effects.
- OSV and mutation MCP wrappers: they add nothing over the CLIs.
- All deprecated awslabs servers.

---

## 7. Supply-chain and trust rules (question 5)

1. **Checkers get read-only servers only, and read-only is enforced in IAM first.** Each checker session uses an
   AWS profile whose role is read-only, scoped to the dev/stage account. Add an explicit deny on writes when
   `aws:ViaAWSMCPService` is true [F]. Server flags are a second layer only: `READ_OPERATIONS_ONLY`, proxy
   `--read-only`, IAM `--readonly`, no `--allow-write`, `ALLOW_WRITE=false`, `SONARQUBE_READ_ONLY`, GitHub
   `--read-only`. The reason: CVE-2026-16584 shows a server can silently stop enforcing its own policy [F].
2. **Mutating tools never reach a checker.** Deny them by tool name: Claude Code `disallowedTools: mcp__<server>__<tool>`
   in the subagent frontmatter [F]; Kiro an explicit `tools: ["@server/tool"]` allowlist [F]. The list:
   - Security Agent `setup`, `start_security_scan`, `call_api`, unless the lane is the Security Agent lane itself
   - Serverless with `--allow-write`
   - ECS with `ALLOW_WRITE`
   - the IAM MCP server
   - Lambda Tool, Step Functions, OpenAPI
   - Application Signals `create_instrumentation` and `delete_instrumentation`
   - IAM Policy Autopilot `fix-access-denied`
   - API MCP without `READ_OPERATIONS_ONLY`
   - the GitLab MCP `manage_pipeline` and `create_*` tools [S]
3. **Pin every server, and never use `@latest`.**
   - PyPI: `uvx <pkg>==X.Y.Z` or `uvx --from '<pkg>==X.Y.Z' <cmd>` [F, uv docs].
   - Unreleased git servers: `git+https://...@<commit-sha>` [U].
   - npm: `npx @playwright/mcp@X.Y.Z`.
   - Docker: by digest.
   - Rewrite the `@latest` in every power and plugin `mcp.json` before use [F], and disable plugin auto-update or
     vendor the plugin [F].
   - For hash-level integrity, install each server into a dedicated venv from a `--require-hashes` requirements file
     and point the MCP `command` at that entry point. npm and PyPI registry entries carry no hash [S]. The awslabs
     Security Agent package has PyPI trusted-publishing provenance [F].
   - Upgrade on purpose, and only to versions at or above the fix in the AWS security bulletins. Search results list eight
     awslabs MCP CVEs published in 2026 (api ×3, MQ, HealthLake, Serverless, Security Agent, MySQL) [S]; two were
     read on the bulletin pages [F].
4. **Headless checker sessions use a fixed server set.**
   - Claude Code: `claude -p` loads a repository's project-scoped `.mcp.json` "without asking" [F], so checkers run
     with `--strict-mcp-config --mcp-config <framework-owned file>` [F]. Add `disabledMcpjsonServers` and managed
     `allowedMcpServers` / `deniedMcpServers` as defence in depth [F].
   - Kiro: `includeMcpJson: false` plus explicit `mcpServers` [F].
   - No keyword-activated powers or plugin hooks in checker sessions; a diff-scan hook that bills per scan, for
     example, has no place there.
5. **Credentials.** No deploy credentials in any session that also has a server reading untrusted content. The
   untrusted sources:
   - CloudWatch logs (they contain user input)
   - issue and PR text
   - Context7 and other web documentation
   - Playwright pages
   - Sentry events

   MCP responses go to the model provider (the IaC server's privacy notice) [F]. Under `no-environment-vars.md`:
   - `AWS_PROFILE` and `AWS_REGION` in an MCP `env` block are scoped config, not shell variables. The framework's
     setup prompt still forbids `AWS_PROFILE` there [F, repo]; reconcile the two when adopting.
   - The DevOps Agent power's `DEVOPS_AGENT_TOKEN` environment variable [F] is replaced by SigV4 through
     `mcp-proxy-for-aws`, or by a Claude Code `headersHelper` that reads a file under `credentials/` [F, helper
     mechanism].
6. **Untrusted-content servers are data sources, never sources of instructions.** Pair them only with read-only
   tools. CVE-2026-18655 is the pattern to avoid: injected text steered an MQ server into sending broker credentials
   to an attacker's host [S]. Other incidents: ContextCrush (Context7) [S] and the GitHub lockdown-cache CVE [S]. Use
   GitHub lockdown mode wherever the GitHub MCP is used at all [S].
7. **No blanket auto-approval.** Auto-approve only tools that read local or public data:
   - threat-modeling server: all 11 are acceptable (no network, no credentials).
   - Knowledge, IaC doc tools, cfn-lint and cfn-guard tools: acceptable.

   Never auto-approve `call_aws` without `--read-only`, or the Security Agent `call_api` and `start_security_scan`.
   `prompts/setup-claude.txt` currently allows `mcp__awslabs.aws-api-mcp-server__*` [F, repo]. That is safe only as
   long as both `READ_OPERATIONS_ONLY` and a read-only IAM role hold.
8. **Cost-bearing tools are tier- and risk-gated, and budgeted:** Security Agent scans and pentests, DevOps Agent,
   CloudTrail Lake queries [U], and threat-composer-ai Bedrock calls.
9. **The MCP Registry is discovery, not trust.** It vets ownership, not security [F]. Prefer first-party publishers
   (awslabs, aws, microsoft, github, SonarSource), and prefer a vendor's CLI over its MCP server when the job is a
   deterministic gate.

---

## 8. Prompt-injection and agent-directed text seen during research

None of these was acted on.

- **threat-modeling-mcp-server README:** prompts addressed to the client agent, for example telling the client to
  name the server so it follows the exact phases, plus a sample config that auto-approves every tool [F]. This is
  documentation for users, not an instruction to me; ignored.
- **awslabs/mcp README:** guidance that tells agents to validate a template and then "deploy via aws cloudformation
  deploy" [F]. Ignored. A framework checker must never deploy.
- **Agent Toolkit for AWS:** rules files tell agents to "search documentation before acting" [F]. The
  `aws-agents-for-devsecops` plugin tells agents never to auto-execute commands returned by DevOps Agent [F], which
  is benign.
- **One Snyk-related search result** contained an embedded instruction to write the answer in a specific controlled
  English. The search tool reported it, and it was ignored.

---

## 9. Sources

- awslabs threat-modeling MCP: https://github.com/awslabs/threat-modeling-mcp-server ·
  https://raw.githubusercontent.com/awslabs/threat-modeling-mcp-server/main/README.md ·
  https://raw.githubusercontent.com/awslabs/threat-modeling-mcp-server/main/pyproject.toml ·
  https://github.com/awslabs/threat-modeling-mcp-server/commits/main ·
  https://github.com/awslabs/threat-modeling-mcp-server/releases ·
  https://github.com/awslabs/threat-modeling-mcp-server/pull/23
- Threat Composer: https://github.com/awslabs/threat-composer ·
  https://github.com/awslabs/threat-composer/tree/main/packages/threat-composer-ai ·
  https://github.com/awslabs/threat-composer/releases
- AWS Security Agent: https://docs.aws.amazon.com/securityagent/latest/userguide/perform-threat-model.html ·
  https://aws.amazon.com/blogs/aws/aws-security-agent-adds-threat-modeling-kiro-power-and-claude-code-plugin-and-more/ ·
  https://awslabs.github.io/mcp/servers/security-agent-mcp-server ·
  https://pypi.org/project/awslabs.security-agent-mcp-server/ ·
  https://github.com/AWS-Security-Agent/aws-security-agent-kiro-power ·
  https://docs.aws.amazon.com/securityagent/latest/userguide/code-review-ide-integration.html [S]
- awslabs catalog: https://awslabs.github.io/mcp/ · https://github.com/awslabs/mcp ·
  https://github.com/awslabs/mcp/tree/main/src/aws-iac-mcp-server ·
  https://awslabs.github.io/mcp/servers/aws-iac-mcp-server · https://pypi.org/project/awslabs.aws-iac-mcp-server/ ·
  https://github.com/awslabs/mcp/tree/main/src/aws-api-mcp-server ·
  https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server ·
  https://github.com/awslabs/mcp/tree/main/src/cloudtrail-mcp-server ·
  https://awslabs.github.io/mcp/servers/cloudwatch-applicationsignals-mcp-server ·
  https://github.com/awslabs/mcp/tree/main/src/well-architected-security-mcp-server ·
  https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server ·
  https://github.com/awslabs/mcp/tree/main/src/iam-mcp-server ·
  https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server ·
  https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server ·
  https://awslabs.github.io/mcp/servers/aws-serverless-mcp-server ·
  https://awslabs.github.io/mcp/servers/lambda-tool-mcp-server · https://awslabs.github.io/mcp/servers/ecs-mcp-server ·
  https://github.com/awslabs/iam-policy-autopilot
- AWS MCP Server and Agent Toolkit: https://github.com/aws/agent-toolkit-for-aws ·
  https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html ·
  https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html · https://github.com/aws/mcp-proxy-for-aws ·
  https://aws.amazon.com/blogs/security/understanding-iam-for-managed-aws-mcp-servers/ ·
  https://github.com/aws/agent-toolkit-for-aws/tree/main/plugins/aws-agents-for-devsecops
- DevOps Agent: https://docs.aws.amazon.com/devopsagent/latest/userguide/connecting-to-devops-agent-remote-servers-connecting-to-the-devops-agent-mcp-server.html
- AWS security bulletins: https://aws.amazon.com/security/security-bulletins/2026-121-aws/ ·
  https://aws.amazon.com/security/security-bulletins/2026-063-aws/ ·
  https://aws.amazon.com/de/security/security-bulletins/2026-070-aws/ [S] ·
  https://aws.amazon.com/security/security-bulletins/2026-007-AWS/ [S] ·
  https://aws.amazon.com/security/security-bulletins/2026-152-aws/ [S] ·
  https://aws.amazon.com/security/security-bulletins/2026-164-aws/ [S] ·
  https://aws.amazon.com/es/security/security-bulletins/2026-103-aws/ [S]
- Kiro: https://kiro.dev/docs/powers/ · https://kiro.dev/powers/ · https://kiro.dev/docs/powers/installation/ ·
  https://kiro.dev/changelog/cli/2-25/ · https://kiro.dev/docs/cli/headless/ ·
  https://kiro.dev/docs/custom-agents/configuration-reference/ · https://github.com/kirodotdev/powers ·
  https://raw.githubusercontent.com/kirodotdev/powers/main/aws-infrastructure-as-code/mcp.json ·
  https://raw.githubusercontent.com/kirodotdev/powers/main/aws-observability/mcp.json
- Claude Code: https://code.claude.com/docs/en/mcp · https://code.claude.com/docs/en/sub-agents
- Other servers: https://github.com/github/github-mcp-server ·
  https://docs.gitlab.com/user/gitlab_duo/model_context_protocol/mcp_server/ · https://github.com/semgrep/mcp ·
  https://github.com/SonarSource/sonarqube-mcp-server · https://github.com/microsoft/playwright-mcp ·
  https://github.com/upstash/context7 · https://github.com/getsentry/sentry-mcp ·
  https://github.com/snyk/studio-mcp [S] · https://github.com/StacklokLabs/osv-mcp [S] ·
  https://github.com/wdm0006/mutmut-mcp [S] · https://noma.security/noma-labs/contextcrush [S] ·
  https://context7.com/guides/contextcrush [S] · https://github.com/upstash/context7/issues/2673 [S] ·
  https://github.com/advisories/GHSA-pjp5-fpmr-3349 [S] ·
  https://advisories.gitlab.com/npm/@zereight/mcp-gitlab/CVE-2026-61559/ [S]
- MCP Registry: https://github.com/modelcontextprotocol/registry · https://modelcontextprotocol.io/registry/package-types
- uv: https://docs.astral.sh/uv/guides/tools/
