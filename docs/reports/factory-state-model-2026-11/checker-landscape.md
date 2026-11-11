# Checker landscape for the issue state model (research, 2026-11-09)

> Record from the factory state-model design discussion (2026-11-09 to 2026-11-11), copied from the working notes. Paths to working files were rewritten to this folder; the text is otherwise as written. Where it differs from `docs/design/factory-state-model/decisions.md`, that file wins.

Status: research only. Nothing in the framework was changed. Input: the state model in
`discussion-log.md` (START, SPEC-REQUIRED, IMPLEMENTATION-READY, TEST-READY,
REWORK-REQUIRED, CLOSE-READY; maker != checker; deterministic tools first, then LLM checkers).

Verification legend, used throughout:

- **[F]** I read it on the primary page during this session.
- **[S]** From web-search results that cite the named primary or vendor page. I did not open the page myself.
- **[U]** Not verified in this session: background knowledge, conflicting sources, or an odd date. Check it before relying on it.
- **vendor claim**: a number published by the vendor, or by a competitor's benchmark. None of these were independently reproduced.

---

## 0. Summary

1. The framework's checkers are almost all **LLM lanes**: security, devops/IaC, standards, best-practice,
   test-architect, adversarial-verifier and spec-review. Its **deterministic layer is thin and Python-only**:
   ruff, mypy, bandit, detect-secrets, pytest+coverage, a red-for-right-reason hook and the e2e group.
   It has no dependency-vulnerability audit, no IaC scanner (cdk-nag, cfn-lint, checkov), no
   `cdk diff --security-only` gate, no diff-coverage gate, no mutation tool, no architecture contracts and no
   licence scan. It also produces **no SARIF**: `run_checks.py` writes its own JSON per group.
2. The market settled on one pattern in 2025–26. **Deterministic tools and LLM finders run in parallel, then
   a separate verification or judge pass, then severity ranking, plus a per-project memory of precedents.**
   Examples: Claude Code Review (find, verify, rank), Bugbot (8 shuffled passes plus majority vote and learned
   rules), CodeRabbit (40+ sandboxed linters plus a judge model plus learnings), Copilot code review (CodeQL,
   ESLint and PMD inside the agent), and Semgrep Assistant (AI triage plus Memories).
3. **Exploit- or test-backed validation** is becoming the norm for security findings: AWS Security
   Agent/Continuum, OpenAI Codex Security, Google CodeMender and AWS Security Agent pen testing. For a
   gating framework, the closest equivalent is "an A-grade security finding must come with a failing test or
   a concrete data-flow trace".
4. AWS shipped two agents that map directly onto these states. **AWS DevOps Agent release management**
   (preview, June 2026) gives a release-readiness verdict on GitHub PRs and GitLab MRs, checks with
   deterministic IAM proofs that permissions do not grow, and runs autonomous release tests. **AWS Security
   Agent (now "AWS Continuum")** covers design review, threat models, PR review and pen tests. Both have
   Claude Code plugins and Kiro powers. Both suit risk-tagged or batched work, not every issue.
5. SARIF is a good exchange format. Its `baselineState`, `suppressions`, `fixes`, `partialFingerprints`,
   `logicalLocations` and `invocations.executionSuccessful` fields map directly onto the review contract and
   the state model's "verdict on SHA" rule. GitHub ingests SARIF natively. GitLab does too since 18.11
   (behind a feature flag), GA in 19.2, **Ultimate only**.
6. Several high-value gaps are cheap to fill. In order of value: a SARIF findings bus, the IaC deterministic
   gate, OSV-Scanner, diff-coverage, a dedupe pipeline at triage, a general logic-bug reviewer lane and an
   EARS/INCOSE spec lint. See section 3.4.

---

## 1. Inventory: what the framework already has

### 1.1 Agents (`clients/claude/agents/*.md`; Kiro twins exist under `clients/kiro/agents/`)

States: START, SPEC (SPEC-REQUIRED), IMPL (IMPLEMENTATION-READY), TEST (TEST-READY), REWORK, CLOSE (CLOSE-READY).

| Agent | Role per front-matter / body | Maker or checker | State(s) it serves | Notes for the state model |
|---|---|---|---|---|
| product-management-agent | Builds a candidate pool (issues, code-review findings, feature ideas), scores it, files gated issues | Maker (of issues) | upstream of START | Its "code-review findings" class overlaps with a general reviewer; never edits code |
| issue-intake-agent | Turns an observation into at most one researched issue; filing gate incl. **G.4 duplicate and adjacency check** (open + recently closed) | Maker with an internal self-check | START (new filings only) | The dedupe logic exists, but only at filing time, and maker == checker |
| issue-housekeeping-agent | Batch triage: closes resolved issues with evidence, implements Type1 quick fixes, drafts Type2 spec prompts | Maker **and** checker in one agent | START (batch), IMPL (Type1) | Violates maker != checker when it closes or fixes; split it in the new model |
| issue-work-orchestrator | Main-session loop: pick issue, worktree, spec/TDD cycle, PR, CI, steward, landing | Orchestrator | all | Becomes the per-state dispatcher or "transition verb" owner |
| spec-conductor | Main-session spec+TDD orchestrator; tiering; parallel review panel; waves; VERIFY | Orchestrator | SPEC, IMPL | Owns consolidation of lane verdicts |
| spec-researcher | Read-only research burst with citations | Helper (neither) | START, SPEC | Useful for triage sanity checks too |
| spec-author | Writes change.md or requirements/design/tasks under byte caps; fixes findings by restating or removing | Maker | SPEC | |
| spec-prompt-author-agent | Interactive: converges on a Kiro spec-mode prompt | Maker (interactive) | pre-SPEC | Not headless (interactive) |
| spec-review-agent | Reviews Kiro spec files against the codebase, MCP docs and the web; A/B/C/D; READY/NOT-READY; hedge/ambiguity scan; open questions | Checker (LLM) | SPEC | The only lane with an ambiguity/hedge scan; no deterministic requirement lint |
| test-architect | Every AC/UB has a falsifiable test; PBT only for domain-quantified criteria; test-first wave order; coverage table | Checker (LLM), CORE gate | SPEC (design/tasks), IMPL (VERIFY) | |
| standards-reviewer | Conformance to `.claude/rules/`, CLAUDE.md and mined conventions | Checker (LLM) | SPEC, IMPL | Architecture rules are checked by LLM only; no import contracts |
| best-practice-reviewer | Tech choices vs official docs via MCP doc servers | Checker (LLM) | SPEC, IMPL | |
| security-reviewer | Input validation, authn/z, secrets, IAM, injection/SSRF/traversal, dependency and logging hygiene; CLEAN in one line when no trust boundary is touched | Checker (LLM) | SPEC, IMPL | No threat-model artefact, no SAST/SCA input, no precedent file |
| devops-iac-reviewer | Least-privilege IaC, rollback, observability, automated e2e in CI; may run `cdk synth` / `cdk diff` read-only | Checker (LLM) | SPEC, IMPL (and the design of TEST) | No cdk-nag, cfn-lint or `--security-only` output to ground it |
| adversarial-verifier | CI verdict for the SHA, **per-wave mutant kill** (revert/stub the wave), vacuity scan, red-for-right-reason audit, change coverage; VERIFIED/REFUTED | Checker (LLM-driven, tool-executing), CORE gate | IMPL | Already a hand-rolled mutation test; step 5 (change coverage) could be deterministic |
| spec-implementer | TEST task writes failing tests; IMPL task writes minimal code; stays in its Files | Maker | SPEC (acceptance tests), IMPL | |
| ci-workflow-agent | Runs every CI stage locally, fixes root causes, raises coverage | Maker | IMPL, REWORK | |
| code-merge-reviewer | Holistic merge review, line-by-line conflict resolution, test-suite regression gate | Maker (with self-gate) | IMPL, REWORK, TEST (rebase) | |
| dead-code-removal-agent | vulture, ruff F401/F811/F841, coverage (zero coverage = candidate, never proof), rg reachability; removes one candidate at a time, test-verified | Maker (with tool evidence) | CLOSE (today repo-wide) | The language matrix still lists **ts-prune as REQUIRED**, but ts-prune is in maintenance mode and recommends knip [S] |
| doc-reviewer-agent | Detects and fixes doc inconsistencies, deviations, gaps and hedging; never edits code | Maker **and** checker | CLOSE | Repo-wide batch; no delta mode; no deterministic link/drift tools |

### 1.2 Deterministic checks the payload already runs

| Where | Check | Output |
|---|---|---|
| `src/payload/scripts/run_checks.py` group `lint` | `ruff check`, `ruff format --check` (src, test, scripts, cdk) | per-group JSON report + summary (custom shape) |
| group `types` | `mypy src --ignore-missing-imports` | same |
| group `security` | `bandit -r src scripts`; detect-secrets via `detect_secrets.pre_commit_hook` against the baseline (non-zero exit on new secret) | same |
| group `tests` | `scripts/run_tests.py --workers auto --coverage --junit reports/junit.xml`; vendored hook suite | JUnit XML + JSON |
| group `e2e` (on request, post-merge) | `test/e2e/` suite | JSON |
| `.pre-commit-config.yaml` (repo) and `templates/pre-commit-config.yaml.template` | ruff, ruff-format, detect-secrets (baseline), detect-private-key, bandit `-ll` on `src/`; mypy at pre-push (template); memory-reconcile; pytest manual | exit codes |
| `.secrets.baseline` | detect-secrets v1.5.0 with about 27 detector plugins (AWS, GitHub, GitLab, JWT, OpenAI, private keys, entropy, and others) | baseline JSON |
| `src/hooks/red_for_right_reason.py` | Red test must fail on an assertion, not a load error | hook verdict |

Design note: `run_checks.py` already treats "tool missing" as a failure, not a skip. SARIF has the matching
field, `invocations[].executionSuccessful`, so the same rule carries over to a SARIF bus.

**Absent from the payload:** dependency-vulnerability audit (pip-audit, OSV-Scanner, npm audit), IaC scanning
(cdk-nag, cfn-lint, cfn-guard, checkov), `cdk diff --security-only`, a SAST engine with custom rules
(Semgrep/Opengrep/CodeQL), diff-coverage, mutation testing, import/architecture contracts, a licence scan,
link and doc-drift checks, TypeScript checks (tsc, eslint, knip) in `run_checks.py`, and SARIF output.

---

## 2. Landscape by category

Column legend: **Kind** is LLM agent, deterministic tool or hybrid. **Headless** means usable from CI or from a
Claude Code or Kiro session without a GUI.

### 2.1 Security review of specs and designs (threat modelling)

| Tool | Kind | Headless | Licence / cost | Output | Adopt / imitate |
|---|---|---|---|---|---|
| **AWS Security Agent, design security review** (now "Continuum for design security review") | LLM agent (SaaS) | Web app upload; boto3 `securityagent` API (2025-09-06) incl. `ImportSecurityRequirements` [S]; Claude Code plugin, Kiro power and MCP since June 2026 [S] | Paid AWS service; no separate design-review price on the pricing page [F] | Findings plus remediation in the app/API; SARIF not found [U] | **Imitate** the "organisational security requirements defined once, checked on every design and code review" idea [F]. Requirement packs reportedly include Well-Architected, NIST CSF and PCI DSS [S]. In the framework: a project `security-requirements.md` the security-reviewer must cite |
| **AWS Security Agent, threat modelling** (Continuum threat modeling, preview June 2026, free in preview) [S] | LLM agent | API/CLI (`batch-get-threat-models`) [S] | Free during preview [S] | System overview, trust boundaries, data flows, **STRIDE-classified threats with severity** [F]; re-runnable configuration [F] | Optional external checker for L or risk-tagged specs |
| **AWS Threat Composer** + `threat-composer-ai` CLI/MCP (awslabs) | Deterministic schema/editor + LLM generator (Bedrock) | `threat-composer-ai-cli /path/to/codebase`; MCP server; schema validation tool [S] | Open source (Apache-2.0 [U]); Bedrock cost | `.tc.json` v1 schema (JSON, git-friendly) [S] | **Adopt** `.tc.json` as the threat-model artefact next to the spec for risk-tagged issues. Validating it against the schema is a free deterministic check |
| awslabs `threat-modeling-mcp-server` | LLM-guided (9 phases) | MCP; ships a Kiro agent config [S] | OSS | `.tc.json` + `.md` [S] | Reference flow for a "threat-modeller" lane |
| STRIDE GPT (`stride-gpt analyze .`) | LLM agent | CLI, Docker [S] | OSS (MIT [U]); BYO LLM | Markdown, JSON, **SARIF**, HTML [S]; maps to the OWASP LLM/Agentic Top 10 and ATT&CK/ATLAS [S] | Prior art for SARIF-emitting LLM threat models |
| OWASP pytm / Threagile / Threat Dragon / SecOpsTM | Deterministic threat-model-as-code (pytm in Python, Threagile in YAML); Threat Dragon is a GUI with a JSON model | pytm and Threagile are CI-friendly [S] | OSS | DFDs, STRIDE reports, machine-readable risks [S] | pytm suits Python projects that want a deterministic threat model in the repo; probably too heavy as a per-issue artefact |
| OWASP ASVS 5.0.0 (May 2025; renumbered requirements) [S] | Standard (catalogue) | n/a | CC BY-SA 4.0 [S] | CSV, PDF, Word | **Adopt** as the citation source for `## Security Considerations`. The security-reviewer cites ASVS IDs instead of free text |

### 2.2 Security review of code

**LLM agents and services**

| Tool | Kind | Headless / forge | Licence / cost | Output | Notes and what to adopt |
|---|---|---|---|---|---|
| **AWS Security Agent, code security review** (Continuum) | LLM agent | Full-repo scans and automated PR/MR comments on GitHub, GitLab, Bitbucket, GHES or S3; auto-fix PRs/MRs [F] | "Continuum for code vulnerabilities": a context fee of about $200 per million LOC plus $10 per inference unit [F, pricing page] | PR/MR comments; console/API | Continuum ingests *other* tools' findings and validates exploitability in a sandbox (gated preview, June 2026) [S]. **Imitate** "tool findings in, validated findings out" |
| **AWS Security Agent, pen testing** | LLM agent (DAST-like, exploit-validated) | On demand against URLs (any cloud) [S]; GA 2026-03-31 [S] | **$50 per task-hour**, per-second metering, 2-month trial [F]; budget controls and finding revalidation since Aug 2026 [S] | CVSS, repro steps, fix PRs [S] | Candidate checker in TEST against the shared dev/stage account, **batched and budget-capped**, for auth/money tags only. The vendor says it does not replace professional pen tests [S] |
| Anthropic `/security-review` (Claude Code command) and **`claude-code-security-review`** GitHub Action | LLM agent | Action is **GitHub Actions only** [F]; the command runs in any Claude Code session | OSS action; API tokens | **JSON results file + inline PR comments; no SARIF** [F] | The FP filter drops DoS, rate-limiting, resource exhaustion, generic input validation and open redirects by default [F]. Its custom filter file has three sections, *HARD EXCLUSIONS / SIGNAL QUALITY CRITERIA / PRECEDENTS* [S]; **imitate this for the security-reviewer**. The README says the action is "not hardened against prompt injection" [F]. Default model is the old `claude-opus-4-1-20250805` [F]. Reported bug: the filter step called a retired Haiku model, got a 404 and silently skipped filtering (issue #103) [S]; status unknown [U] |
| Anthropic **Claude Security** (ex Claude Code Security; public beta 2026-04-30, Enterprise) [S] | LLM agent (SaaS) | claude.ai/security; Claude Code plugin for ZDR/3P providers [S] | Enterprise; promotional credits [S] | Triage tracking, CSV/Markdown export, Slack/Jira webhooks [S] | Writes a threat model before the baseline scan [S]. Same pattern as Aardvark |
| GitHub **CodeQL + Copilot Autofix** | Deterministic SAST + LLM fixer | GitHub only; CodeQL CLI usable in any CI for OSS/GHAS [U] | Free on public repos; GitHub Code Security / GHAS for private [S] | **SARIF native** | Agentic autofix (preview 2026-07-10) also takes **third-party SARIF alerts**, but validates only by re-running the CodeQL default suite [S]. Use SARIF upload with one `category` per tool, because an upload without one replaces the previous [S] |
| Semgrep CE / **Opengrep** / Semgrep AppSec Platform + Assistant | Deterministic SAST (+ LLM triage in the platform) | CLI anywhere; Opengrep has **native Windows** and signed binaries [S] | Engines LGPL-2.1. Semgrep-maintained rules are under the **Semgrep Rules License v1.0** (internal use allowed, no competing SaaS) [S]. Opengrep's rule fork has been stale since Jan 2025 [S]. Platform free up to 10 contributors [S] | SARIF 2.1.0, JSON | Assistant: about 20% of SAST findings auto-filtered as FP at first, about 40% after a week, around 96% agreement (**vendor claim**) [S]. Memories: the top categories are "non-production environment" (25.6%) and "framework protection" (21.9%) [S]. **Adopt** Opengrep or Semgrep CE with *project-written* rules as a deterministic SAST stage |
| Snyk Code | Hybrid (symbolic + ML) SaaS | CLI; `--sarif-file-output` [S] | Free: 100 Code tests/month; Team from $25/month; Enterprise credits [S] | SARIF, JSON | Optional; needs a SaaS account and token |
| OpenAI **Codex Security** (ex Aardvark) | LLM agent | Research preview (Mar 2026) [S]. A CLI/SDK `@openai/codex-security` (Apache-2.0) that runs in CI and exports SARIF was reported in Jul 2026 by secondary sources only [S/U] | ChatGPT Pro/Business/Enterprise [S] | PR review via `@codex security review`; SARIF via CLI [U] | Four steps: threat model, commit scan, sandbox reproduction, patch [S]. Beta claim of FP down more than 50% (**vendor claim**) |
| Google **CodeMender** | LLM agent | Public preview on the Gemini Enterprise Agent Platform since Jul 2026; CLI/daemon builds and tests locally; only snippets are sent [S] | GCP | Patches validated against PoC exploits [S] | Out of scope for an AWS-centric stack; validate-by-exploit is again the pattern |
| Amazon Q Developer `/review` | LLM + rules | **Retiring**: new sign-ups blocked 2026-05-15, end of support 2027-04-30 [S] | — | — | **Do not adopt.** Kiro has no built-in SAST; security scanning in Kiro comes from the **AWS Security Agent Kiro power** (diff scan after an agent turn, full-repo scan on request) [S] |
| GitLab Duo | LLM | GitLab | SAST false-positive detection GA in 18.10; agentic code review at $0.25 per review [S] | GitLab vulnerability objects | Relevant for GitLab Ultimate users only |

**Deterministic tools**

| Tool | Scope | Licence | Output | Note |
|---|---|---|---|---|
| Bandit (in the framework) | Python SAST | Apache-2.0 [U] | `-f sarif` built in since 1.7.8 [S] | Switch the CI invocation to SARIF; keep `-ll` at pre-commit |
| **OSV-Scanner v2** | SCA for PyPI and npm lockfiles, containers; licence allowlist via deps.dev; `fix` guided remediation (experimental) [S] | Apache-2.0 [U] | **SARIF 2.1.0**, JSON, CycloneDX 1.7, SPDX [S] | **Best single SCA tool** for Python+TS: one tool, both ecosystems, SARIF and licences |
| pip-audit | Python SCA (PyPI/OSV) | Apache-2.0 [U] | columns, JSON, CycloneDX, markdown; **no SARIF** [S] | Needs a converter; OSV-Scanner makes it redundant |
| npm audit | npm SCA | npm | `--json` only [U] | Same: OSV-Scanner covers it |
| Dependabot | Alerts + update PRs | GitHub only | GitHub alerts | GitLab equivalent: Renovate or GitLab Dependency Scanning (Ultimate) [U] |
| detect-secrets (in the framework) | Secrets, baseline workflow | Apache-2.0 | baseline JSON (no SARIF) | **No release since v1.5.0 (May 2024)** [S]; the baseline-plus-audit workflow is still its strength |
| gitleaks / **Betterleaks** | Secrets in git history | MIT | gitleaks: JSON, CSV, JUnit, **SARIF** [S] | The gitleaks creator started Betterleaks (Feb 2026, drop-in, 463 rules) after losing control of the gitleaks name [S]; its recall claims are unverified |
| TruffleHog | Secrets, **live verification** | AGPL-3.0 [S] | JSON | Use for "is this leaked key live?" checks in CI, not as a commit hook |
| Trivy | Vulnerabilities, misconfiguration (incl. CloudFormation), secrets, licences | Apache-2.0 [U] | SARIF, JSON, CycloneDX, SPDX | **Supply-chain caution:** in March 2026, 76 of 77 `trivy-action` tags and all `setup-trivy` tags were force-pushed to a credential stealer, and a backdoored v0.69.4 was published (CVE-2026-33634) [S]. `kics-github-action` was hit four days later and the KICS Docker images in April [S]. Lesson for every scanner stage: **pin by commit SHA or digest and keep deploy credentials out of scanner jobs** |

### 2.3 DevOps / IaC (AWS CDK, CloudFormation)

| Tool | Kind | Headless | Licence / cost | Output | Adopt / imitate |
|---|---|---|---|---|---|
| **cdk-nag** (cdklabs) v3 | Deterministic rule packs at synth time | `cdk synth` | OSS (Apache-2.0 [U]) | Writes `policy-validation-report.json` in the cloud assembly [F]; **no SARIF found** | Packs: AWS Solutions, HIPAA, NIST 800-53 r4/r5, PCI DSS 3.2.1, Serverless [F]. v3 replaces `NagSuppressions` with `Validations.of(construct).acknowledge({id, reason})`, one finding at a time [F]. **Adopt** AwsSolutions for every IaC-tagged change; a small converter turns the JSON report into SARIF |
| CDK policy-validation plugins (`policyValidationBeta1`), **CfnGuardValidator** | Deterministic (Guard rules; Control Tower proactive controls on by default) | `cdk synth` fails on violation [S] | OSS, experimental (v0.0.x) [S] | Console report | AWS calls it a best-effort shift-left check, to be paired with CloudFormation Hooks or AWS Config [S] |
| **cfn-lint** | Deterministic template validation | CLI | OSS (MIT-0 [U]) | `--format sarif` (extra `cfn-lint[sarif]`), JUnit, JSON; `--non-zero-exit-code` threshold [S] | **Adopt** on `cdk.out/*.template.json` |
| cfn-guard | Deterministic policy-as-code | CLI | Apache-2.0 [U] | JUnit and SARIF workflows linked in the README [S]; exact flag (`--output-format sarif`) [U] | Use for project-specific policies, e.g. "no `*` in IAM actions" |
| Checkov | Deterministic + graph checks (1,000+ policies incl. CloudFormation) | CLI | Apache-2.0 [S] | SARIF, JSON, JUnit, CycloneDX [S] | Alternative to cfn-guard with more built-ins; scan synthesized templates (no native CDK) |
| KICS | Deterministic (Rego queries) | CLI | Apache-2.0 [S] | SARIF, GitLab SAST, ASFF and more [S] | Compromised twice in 2026 [S]; prefer Checkov plus cfn-lint |
| **`cdk diff --security-only`**, `--method change-set` | Deterministic diff | CLI | — | Text | Shows only *broadened* IAM / security-group changes [S]. **Adopt** as an IaC-tagged gate: any output requires the security-reviewer or devops-iac-reviewer to accept it explicitly |
| **CloudFormation drift-aware change sets** (Nov 2025) | Deterministic preview (three-way: new template, last template, live state) | `cdk deploy --method=prepare-change-set --revert-drift` [S] | — | `describe-change-set` JSON | TEST: in a shared dev/stage account someone will have clicked something; review drift before a batch deploy |
| IAM Access Analyzer custom policy checks (`check-no-new-access`, `check-access-not-granted`) | Deterministic (automated reasoning) | CLI/API | Per-check fee [U] | JSON | [U, not researched this session] Strong deterministic "no new access" proof for IAM diffs; this is apparently what DevOps Agent's "deterministic proofs" refers to [U] |
| **AWS DevOps Agent** (GA 2026-03-31 for incident investigation [S]); **release management** (preview 2026-06-17, us-east-1, no extra cost) [S] | LLM agent + deterministic IAM proofs | PR/MR comments on GitHub and GitLab, console, chat, **Kiro power / Claude Code plugin, CI/CD** [S]; "headless mode with managed MCP/A2A endpoints" [S] | Agent-second billing; release management free in preview [S] | Verdict BLOCK / Deploy with Caution / Standard Deployment / Request Permissions / Insufficient Data, findings tied to code locations [S] | **Strong candidate checker for IMPL (IaC/IAM tag) and TEST (batch release readiness).** Its autonomous release tests run in an environment *you* provision, i.e. the shared dev/stage account [S]. The incident-investigation side feeds REWORK (a root cause plus an agent-readable fix plan for Kiro or Claude Code [S]) |
| AWS Well-Architected IaC Analyzer (aws-samples) | LLM (Bedrock) web app | Not CI-native; a GitHub Action is claimed but unverified [S/U] | Sample; Bedrock cost | Web report | Not a fit for headless use. The framework's devops-iac-reviewer with the AWS IaC MCP server already covers this |
| AWS IaC MCP server | LLM tool server (validate templates, CDK best practices, CloudTrail troubleshooting) [S] | MCP | OSS | Tool results | Already referenced by devops-iac-reviewer |

### 2.4 General code review agents

| Tool | Kind | Forges / headless | Cost model | Output | What it does differently |
|---|---|---|---|---|---|
| **Claude Code Review** (managed, ~Mar 2026) [S] | LLM multi-agent | GitHub; Team/Enterprise; `@claude review` | Usage-based; admin "review level" [S] | Inline comments tagged by severity, a summary and a check run that **never fails** [S] | Parallel specialist finders, then a **verification step that drops false positives**, then dedupe and severity rank [S]. Scope limited to logic errors, no style [S]. Vendor claim: under 1% of findings marked incorrect [S] |
| Claude Code `/code-review` plugin, ultrareview, **claude-code-action** | LLM | Any CI (headless `claude -p`), any forge via scripts | API tokens | Whatever the prompt emits (can be SARIF/JSON) | Published plugin prompt: a Haiku agent summarises, then 5 parallel Sonnet agents each take one lens (CLAUDE.md compliance, obvious bugs, git blame/history, previous PR comments, code comments) [S]. **Directly reusable in the framework's Claude Code sessions** |
| **Cursor Bugbot** | LLM | GitHub (Cursor) | Usage-based since May 2026, about $1.00–1.50 per run [S] | PR comments, Autofix PRs | **8 parallel passes over shuffled diffs, majority vote** [S]; learned rules (Apr 2026) [S]. Defines and publishes a **resolution rate** (share of flagged bugs fixed by merge, judged by AI): about 52% at launch, 70%+ by Jan 2026, near 80% by Apr 2026 (**vendor claim**) [S] |
| **CodeRabbit** | LLM + 40–50 sandboxed linters/scanners + code graph | GitHub, GitLab, Azure DevOps, Bitbucket; **CLI `coderabbit review --agent`** for coding agents [S] | Free tier; Pro about $24/dev/month [S] | PR comments; structured agent output from the CLI | Code graph rebuilt per review; learnings from chat feedback; reads `CLAUDE.md` and similar rule files; a **judge model** filters nits and FPs [S]. The CLI is a cheap optional checker in Claude Code sessions |
| **Greptile** | LLM with full-repo index | GitHub, GitLab [U] | Per-seat [U] | PR comments | Codebase-wide index. Top of the Martian Code Review Bench (Jul 2026): F1 60.8%, precision 76.2% [S, secondary] |
| **Qodo 2.0** / **PR-Agent** | LLM | PR-Agent: GitHub, GitLab, Bitbucket, Azure DevOps, Gitea; Action, CLI, Docker, webhook; BYO model via LiteLLM [S] | PR-Agent is OSS, community-maintained since Apr 2026 (licence reported as MIT or Apache-2.0, conflicting [U]); Qodo commercial [S] | PR comments, GitHub Checks (v0.39+) [S] | Qodo 2.0 runs parallel specialist agents (bugs, quality, security, tests) plus a context engine over PR history and tickets [S]. PR-Agent v0.39 reads `AGENTS.md` and SKILL.md [S]. **PR-Agent is the only mature OSS, self-hostable, two-forge reviewer** |
| GitHub **Copilot code review** | LLM + CodeQL/ESLint/PMD | GitHub; agentic architecture GA 2026-03-05; runs on Actions runners [S] | Copilot plans | PR comments; hand-off to the coding agent | Tool calling for repo context; **runs deterministic tools inside the review**, configurable by ruleset [S] |
| Graphite Agent (ex Diamond) | LLM | GitHub | about $40/user/month [S] | PR comments | Optimised for low noise ("under 3% unhelpful", **vendor claim**) at the price of low recall (18.3% in Macroscope's benchmark) [S]. Cursor reportedly agreed to acquire Graphite in Dec 2025 [S/U] |
| Kiro (headless CLI, Autonomous Agent, community review actions) | LLM | `kiro-cli chat --no-interactive --agent <name>`, `KIRO_API_KEY` [S]; community `kiro-cli-review-action` [S] | Kiro subscription | Whatever the agent emits | The framework's Kiro agents can run headless the same way |
| GitLab Duo agentic code review | LLM | GitLab | $0.25 per review [S] | MR comments | — |

**Published precision / false-positive data (all vendor-run or vendor-reported; treat as directional):**

| Source | Finding |
|---|---|
| Augment / Propel benchmark, 50 PRs from 5 OSS repos [S] | Precision / recall: Bugbot 60/41, Greptile 45/45, CodeRabbit 36/43, Claude Code 23/51, Copilot 20/34, Codex 68/29 (each publisher ranks itself first) |
| Martian Code Review Bench (described as independent; secondary source) [S] | Greptile F1 60.8%, precision 76.2% (Jul 2026); CodeRabbit led in Jan–Feb 2026 |
| Qodo Code Review Benchmark 1.0 (Qodo's own; 100 PRs, 580 planted issues) [S] | Qodo 2.0 F1 60.1%, recall 56.7% |
| Cursor's resolution-rate table [S] | Bugbot 78%, Greptile 63%, CodeRabbit 49%, Copilot 47% |
| CR-Bench critique (arXiv 2603.11078) [S] | Correct comments that are off the planted bug count against precision, so benchmarks disagree by construction |

**What the best ones do differently** (evidence above):

1. They run **separate finders and a separate verifier**: Claude Code Review's verify step, CodeRabbit's judge
   model, Bugbot's majority vote. The verifier is what controls false positives.
2. They give the model **codebase-wide context**: a code graph (CodeRabbit), an index (Greptile), agentic tool
   calls (Copilot) and linked tickets or PR history (Qodo, CodeRabbit).
3. They **run deterministic tools inside the review** and let the LLM reason over their output (Copilot with
   CodeQL/ESLint/PMD, CodeRabbit with 40+ linters).
4. They **learn from feedback**: CodeRabbit learnings, Bugbot learned rules, Semgrep Memories.
5. They **measure checker quality** by outcome, e.g. resolution rate, not by finding count.
6. They **narrow scope** to logic and security bugs and leave style to linters.

The framework already has 6, and its review contract enforces scope. It lacks 1, 3, 4 and 5 for code.

### 2.5 Dead and unnecessary code

| Tool | Kind | Licence | Output | Note |
|---|---|---|---|---|
| vulture (in the framework) | Deterministic | MIT [U] | Text; confidence levels (100 for args/unreachable, 90 for imports, 60 for others); exit code 3 when dead code is found; whitelist file; `[tool.vulture]` [S] | Already used. Suggested CI ramp: confidence 90, then a whitelist, then 80 [S] |
| deadcode (Python) | Deterministic | OSS | Text; `--strict` [S] | Alternative with more precise detection [S] |
| Skylos | Deterministic, framework-aware (Flask/Django routes, pytest fixtures) | OSS | JSON; `--diff origin/main` [S] | Author's own benchmark: recall 98.1% vs 84.6% for vulture, 220 vs 644 FPs (**vendor claim**) [S]. Its **diff mode suits a per-issue CLOSE checker**. `--trace` executes project code [S] |
| ruff F401/F811/F841 (in the framework) | Deterministic | MIT | SARIF via `--output-format sarif` [U] | Already used |
| **knip** | Deterministic (TS/JS unused files, exports, dependencies) | ISC [U] | Reporters: json, **sarif**, codeclimate, markdown; `--fix` [S] | **Replaces ts-prune**, which is in maintenance mode and points to knip [S]. Common FP source: plugins disabled (one repo: about 78% of 232 findings) [S] |
| coverage-based detection | Deterministic signal | — | coverage JSON | The framework's rule ("zero coverage is a candidate, never proof") matches practice |
| LLM "unnecessary code" review | LLM | — | — | Claude Code's `/simplify` skill (reuse, simplification, efficiency) is available in sessions; CodeRabbit and Bugbot flag it too. **No framework lane reviews the issue's own diff for unnecessary code**; the dead-code agent is a repo-wide batch |

### 2.6 Test adequacy

| Tool | Kind | Licence | Output | Note |
|---|---|---|---|---|
| **mutmut 3** | Deterministic mutation testing (Python) | BSD [U] | `mutants/` directory, interactive browser | Incremental per changed *function*; `mutate_only_covered_lines`; no git-diff mode found [S]. Pass changed files from `git diff` as `paths_to_mutate` |
| cosmic-ray | Deterministic (Python) | MIT [U] | Session DB | Thorough but slow [S]; a git-diff filter is reported from memory only [U] |
| **StrykerJS** | Deterministic (TS/JS) | Apache-2.0 [U] | JSON against the **mutation-testing-elements schema** (draft-07, `MutationTestResult`) [S]; incremental mode (`--incremental`, 6.2+) [S] | Nightly full runs plus incremental PR runs is the documented pattern [S] |
| **Meta ACH** (FSE '25) | LLM generates a few *concern-specific* mutants, then tests that kill them | Paper | — | 10,795 classes, 571 hardening tests, **73% accepted by engineers**; LLM equivalent-mutant detector precision/recall 0.95/0.96 with preprocessing [S]. **Imitate** for risk-tagged ACs ("remove the authz check", "round the wrong way") |
| diff-cover | Deterministic (coverage of changed lines) | Apache-2.0 [U] | JSON, markdown, HTML [U] | Cheaper deterministic replacement for adversarial-verifier step 5 [U, not researched this session] |
| Hypothesis | Property-based testing | MPL-2.0 [U] | pytest | The framework's test-architect already rules when PBT applies |
| LLM test reviewers | LLM | — | — | e.g. `pr-test-analyzer` in Claude Code's PR Review Toolkit, ported to Kiro review agents [S]. The framework's test-architect (falsifiability and traceability) plus adversarial-verifier (mutant kill, vacuity) are already stronger than these |

### 2.7 Requirements and spec quality

| Item | Kind | Output | Adopt / imitate |
|---|---|---|---|
| **EARS** (Kiro uses it in `requirements.md`) | Notation | — | Deterministic checks from an INCOSE IS 2024 study: exactly one "shall"; starts with When/While/Where/If/The; no repeated condition keyword [S]. Only 34% of 148 automotive requirements complied before LLM correction [S] |
| **INCOSE Guide to Writing Requirements** (41–44 rules by revision) [S] | Rule set | — | Automatable rules include R7 vague terms, R9 escape clauses, R10 open-ended clauses, R26 pronouns and R28 absolutes [S]. Commercial: QVscribe, Jama [S] |
| ISO/IEC/IEEE 29148:2018 | Standard | — | Quality characteristics such as necessary, unambiguous, complete, singular, feasible and verifiable [U] |
| **`EnzinoBB/requirements-review`** | Deterministic stdlib linter (29148 + INCOSE rule IDs, quoted evidence) **then** an LLM skill for coverage gaps, semantic duplicates, feasibility and EARS rewrites [S] | Rule-ID findings | **The exact "deterministic first, then LLM" pattern for specs.** Worth vendoring or imitating as a SPEC pre-check |
| GitHub **spec-kit** `/speckit.analyze` | LLM, read-only cross-artifact check (spec, plan, tasks, constitution) | Table of up to 50 findings with ID, severity (CRITICAL/HIGH/MEDIUM/LOW), `file:Lx-y` location and recommendation; **stable IDs on rerun** [S] | Imitate the stable IDs and the cross-artifact "terminology drift" check |
| spec-kit `/speckit.checklist` | LLM | CHK001… items that test the *requirements text*, not behaviour [S] | Fits the spec-review-agent |
| **AWS AI-DLC workflows** (awslabs) | Staged workflow with Approve/Request-Changes gates | — | Stage 2.2: quality, developer and devsecops agents review **in parallel, without seeing each other's input**, then a human interview [S]. A phase-boundary verification gate [S]. The engine refuses the reviewer until the required files exist [S]. **Imitate** blind first-iteration lanes and deterministic preconditions before an LLM review starts |

### 2.8 Architecture conformance

| Tool | Kind | Licence | Output | Note |
|---|---|---|---|---|
| **import-linter** | Deterministic contracts (layers, forbidden, independence; transitive) | BSD [U] | Text, exit code | `ignore_imports` as a list that "only shrinks" [S]; baseline mode requested, not shipped [S]; misses directories without `__init__.py` [S] |
| tach | Deterministic module boundaries + public interfaces; `tach sync` generates the config | MIT [U] | Text | PostHog runs both tools: tach between products, import-linter inside each [S] |
| **dependency-cruiser** | Deterministic (TS/JS): forbidden/allowed/required, `reachable`, `circular` | MIT [U] | `err`, **`json`**, `baseline` (known violations), dot, mermaid [S] | — |
| ArchUnitTS / ts-arch | Architecture rules as tests | OSS | Test-runner output | — |

None of these emits SARIF [none found]; wrap their JSON or text. **Fit:** the rules the standards-reviewer now
checks by LLM ("absolute imports", layering in `.claude/rules/`) become contracts. The LLM lane then only
judges what the contracts cannot express.

### 2.9 Docs drift and dead docs

| Tool | Kind | Output | Note |
|---|---|---|---|
| Vale, markdownlint, cspell, **lychee** (links) | Deterministic | Text/JSON [U] | Each covers one aspect; none detects drift between code and docs [S] |
| **fiberplane `drift`** (Mar 2026) | Deterministic: links spec/markdown to code symbols in `drift.lock`, uses tree-sitter fingerprints, `drift check` exits 1 when stale [S] | Exit code | **Good fit for spec artefacts**: bind the AC sections to the code symbols they govern |
| pallaprolus `drift` | Deterministic docstring/param/README-example mismatch, optional AI [S] | Scores and severities | — |
| Doc Drift (GitHub Action), Doc-Sentinel AI | LLM per PR [S] | PR comment, label | — |
| interrogate (docstring coverage) | Deterministic | Text | [U, not found in results] |
| framework `doc-reviewer-agent` | LLM maker+checker | Lane files | Repo-wide only; needs a diff-scoped mode for CLOSE |

### 2.10 Licence compliance

| Tool | Licence | Output | Note |
|---|---|---|---|
| OSV-Scanner `--licenses="MIT,Apache-2.0"` | Apache-2.0 [U] | SARIF/JSON [S] | One tool for SCA and licences (deps.dev; sends package names only) [S] |
| Trivy `--scanners license` | Apache-2.0 [U] | SARIF, JSON, SPDX, CycloneDX [S] | Needs dependencies installed first [S]; supply-chain caution (2.2) |
| licensecheck (Python, `[tool.licensecheck]`) | OSS | JSON, CSV [S] | Checks compatibility with the project's own licence |
| pip-licenses, license-checker (npm) | OSS | JSON, CSV, markdown [S] | — |
| ScanCode Toolkit, FOSSology, ORT | OSS | JSON, SPDX | Audit grade, heavy [S]; ORT not researched [U] |

Run these **only when a dependency manifest or lockfile changes**, plus once at CLOSE for M/L.

### 2.11 Performance and cost

| Tool | Kind | Output | Note |
|---|---|---|---|
| **Infracost** | Deterministic cost diff | PR/MR comment with cost delta and policy results; GitHub, GitLab, Azure Repos [S] | CloudFormation and **CDK** supported in Infracost Cloud (early access; it runs `cdk synth`) [S]. CLI v2 reads CloudFormation natively [S]; CDK in the CLI was "on the roadmap for 2026" and may have shipped [U]. Free CI/CD tier of 1,000 runs/month [S] |
| AWS Pricing MCP server (`analyze_cdk_project` + `get_pricing` + `generate_cost_report`) | LLM-driven estimate | Markdown/CSV report [S] | Planning estimate; the docs warn filters may be wrong [S]. Fine for SPEC (design cost note), not for a gate |
| CodSpeed (pytest-codspeed, vitest via CLI) | Deterministic performance regression ("simulation" mode under 1% variance) | PR checks/comments; GitHub and GitLab [S] | Commercial [U]. Only for issues tagged `perf` |

### 2.12 Duplicate-issue detection at triage

| Item | Kind | Note |
|---|---|---|
| GitHub built-in semantic duplicate suggestions while an issue is written | Vector search + hidden LLM re-rank, feature-flagged | Source is a gist; **unverified** [U] |
| "AI Duplicate Issue Detector" Action | Embeddings; two thresholds ("duplicate" vs "related"); waits 3.5 min for edits [S] | Imitate the two-threshold design |
| "GenAI Issue Deduplicator" Action | Small LLM narrows candidates by label, large LLM confirms [S] | Cheap-first cascade |
| GitLab Duo Agent Platform community flows | LLM; thresholds in `AGENTS.md` [S] | No native GitLab feature found [S] |
| **anthropics/claude-code dedupe bot** (the cautionary tale) | LLM flags 1–3 candidates, 3-day grace, then **auto-close** [S] | Complaint of 15,240 auto-closures, including an issue titled "NOT A DUPLICATE" [S]. It suggests already-closed issues and builds duplicate chains (#20282, #19267) [S]. **Lesson:** never close on one LLM verdict; exclude closed-as-duplicate candidates; a second agent confirms (the state-model draft already requires this) |
| framework intake G.4 | LLM search of open and recently closed issues | Filing-time only; same agent decides |

---

## 3. Recommended TEAM per state

Principles: deterministic tools run first and emit SARIF. LLM checkers receive that SARIF filtered to the
diff. Each checker posts a verdict *on a SHA*. A checker that does not apply posts `CLEAN` in one line, as the
review contract already says. External SaaS agents are optional plug-ins and never the only checker for a
gate.

Tier and risk notation: **every** = every issue. **M+** = tiers M and L. **L** = tier L only.
**risk:<tag>** = issues carrying that tag (auth, iam-iac, data-migration, money, plus optional perf and deps).

### 3.1 Team per state

| State | Makers | LLM checkers | Deterministic checkers | When |
|---|---|---|---|---|
| **START** (triage) | triage worker (intake G.1–G.4 logic, split out of housekeeping) | **duplicate-confirmer** (a second agent; only when a candidate passes the threshold; mandatory before any close) · sanity/scope checker | Candidate retrieval: forge search plus embedding or BM25 over open and recently closed issues, **excluding issues closed as duplicate** · issue-template/field lint · risk-tag heuristics (paths and keywords: `iam`, `cdk/`, `auth`, `migration`, money terms) · footprint estimate (files and modules likely touched) | Retrieval, lint and tagging: **every**. Confirmer: only on candidates, always on close. Sanity checker: L |
| **SPEC-REQUIRED** | spec-author (+ spec-researcher); spec-implementer TEST tasks (acceptance tests) | **test-architect** (every) · spec-review-agent or panel consolidation (M+) · standards-reviewer (M+) · best-practice-reviewer (M+, only when external tech is touched) · security-reviewer (every, one-line CLEAN when no trust boundary; full on risk:auth/money/data-migration) · **threat-model lane** (new; STRIDE table + ASVS 5.0 IDs; optional `.tc.json`) (L or risk:auth/money/iam-iac) · devops-iac-reviewer (risk:iam-iac or any deploy change) | **EARS/INCOSE spec lint** (new) (M+) · AC-to-test traceability script (every) · `red_for_right_reason` (exists) (every) · spec byte caps (exists) · `.tc.json` schema validation (when a threat model exists) | Optional external: AWS Security Agent design review / threat model for L + risk:auth/money |
| **IMPLEMENTATION-READY** | spec-implementer (waves), ci-workflow-agent, code-merge-reviewer | **adversarial-verifier** (every) · test-architect VERIFY (every) · **logic-bug reviewer** (new; find, then verify, then rank; diff plus repo context) (M+) · standards-reviewer (M+) · security-reviewer (risk tags, or any security SARIF result on the diff) · devops-iac-reviewer (risk:iam-iac) · ACH-style concern mutants (risk:auth/money) | ruff, mypy, bandit (SARIF), detect-secrets (every) · pytest + coverage + **diff-coverage on changed lines** (every) · **OSV-Scanner** (when manifests/lockfiles change, and nightly) · Opengrep/Semgrep CE with project rules (M+) · import-linter/tach or dependency-cruiser (where contracts exist) (every) · tsc/eslint/knip (TS projects) · **mutation on changed functions** with mutmut/Stryker incremental (L or risk tags) · **IaC gate**: `cdk synth` + cdk-nag AwsSolutions + cfn-lint (SARIF) + Checkov or cfn-guard + **`cdk diff --security-only`** (risk:iam-iac or any change under `cdk/`) · CodeQL (GitHub projects, M+) | Optional external: DevOps Agent release-readiness review on the PR (risk:iam-iac); AWS Security Agent PR review (risk:auth/money); CodeRabbit CLI or PR-Agent as a second-opinion finder (M+) |
| **TEST-READY** (queue, CI, batched deploy to the shared account, smoke/E2E) | merge steward (queue owner); CDK deploy pipeline | **batch release-readiness checker** (LLM over the batch's change sets and security diffs; or DevOps Agent release management) (batches containing risk:iam-iac) · post-deploy verdict watcher (exists) · failure attributor (which issue in the batch broke E2E; steward plus bisect) | CI on the merged batch (every) · `cdk diff --method change-set --security-only` for the batch (every IaC batch) · **change-set replacement/deletion detector** (new; any `Replacement: True` or `Remove` on stateful types such as RDS, DynamoDB, S3 or Cognito blocks unless the issue is risk:data-migration and approved) · **drift-aware change set** preview before deploy (every IaC batch) · smoke/E2E (`run_checks.py --group e2e`) (every) · Infracost on the batch (risk:iam-iac with cost-relevant resources) | Optional external: AWS Security Agent pen test against stage, **budget-capped and batched** (weekly, or per batch containing risk:auth/money) |
| **REWORK-REQUIRED** | any implementer (ci-workflow-agent, spec-implementer) | Only the lanes with open findings, plus lanes whose files the fix touched (delta mode); finding revalidation | Re-run the same deterministic set on the new SHA; SARIF `baselineState` shows which findings are fixed, new or unchanged | Scope is decided by the previous SARIF, so no full re-review |
| **CLOSE-READY** (cleanup and retrospective) | cleanup worker (dead-code-removal in **diff-scoped** mode; doc-reviewer in **delta** mode); retrospective writer | **unnecessary-code reviewer** (`/simplify`-style, on the issue's merged diff) (M+) · doc-drift reviewer on the diff (M+) · **retro checker**: each learning is backed by evidence, is not a duplicate of an existing rule or memory, and files nothing without an observed defect (every) | vulture/Skylos `--diff` / knip on changed modules and their importers · ruff F401/F811/F841 · zero-coverage lines in changed modules · lychee + markdownlint + `drift check` · licence scan (if manifests changed) · leftover TODO/FIXME/debug-flag grep on the diff | Tier S: deterministic only plus the retro checker |

### 3.2 Cost proportionality matrix (checker on or off by tier, with risk overrides)

| Checker | S | M | L | Forced on by risk tag |
|---|---|---|---|---|
| Deterministic baseline (lint, types, bandit, secrets, tests, diff-coverage) | on | on | on | — |
| test-architect, adversarial-verifier | on (change.md scale) | on | on | — |
| security-reviewer | one-line CLEAN unless a trust boundary is touched | on | on | auth, money, data-migration, iam-iac: full |
| threat-model lane | off | off | on | auth, money, iam-iac |
| standards / best-practice | off (S: deterministic contracts only) | on | on | — |
| logic-bug reviewer | off | on | on (with verify pass) | — |
| IaC gate (cdk-nag, cfn-lint, Checkov, `--security-only`) | when `cdk/` changes | when `cdk/` changes | when `cdk/` changes | iam-iac: plus devops-iac-reviewer |
| Mutation on changed functions / ACH mutants | off | off | on | auth, money |
| OSV-Scanner / licence | on manifest change | on manifest change | on manifest change | deps |
| External SaaS (Security Agent, DevOps Agent, CodeRabbit…) | off | off | optional | auth/money: pen test (batched); iam-iac: release readiness |
| CLOSE LLM reviewers | off | on | on | — |

### 3.3 Must-run on every issue

These are cheap and deterministic, except the CORE LLM gates:

- triage retrieval and tagging
- the deterministic baseline
- AC-to-test traceability
- red-for-right-reason
- diff-coverage
- test-architect and adversarial-verifier
- the retro checker

Everything else is selected by tier and risk tag.

### 3.4 Gap list, ordered by expected value

1. **SARIF findings bus** (`run_checks.py` emits SARIF per tool, plus small converters for pip-audit, cdk-nag,
   detect-secrets, vulture, import-linter and dependency-cruiser output, plus the review contract mapped to
   SARIF; section 4). Everything below depends on it; it is cheap.
2. **IaC deterministic gate**: cdk-nag v3 + cfn-lint SARIF + Checkov or cfn-guard + `cdk diff --security-only`.
   Today IaC review is LLM-only, and the target is a *shared* AWS account, so the blast radius is high.
3. **Dependency vulnerability scan**: OSV-Scanner, one tool for PyPI and npm with SARIF and licences. The
   framework has none.
4. **Diff-coverage gate** (deterministic), which offloads adversarial-verifier step 5. Plus **mutation on
   changed functions** for L and risk tags (mutmut 3 / Stryker incremental).
5. **Triage dedupe pipeline**: retrieval prefilter, LLM confirmer, second agent for any close. Apply the
   claude-code bot lessons.
6. **Logic-bug reviewer lane** (find, verify, rank) for M+. The current lanes are lens-specific and none of
   them hunts general bugs in the diff; the adversarial-verifier refutes claims instead.
7. **Spec lint**: deterministic EARS/INCOSE checks before the LLM panel (pattern: `requirements-review`).
8. **Threat-model lane** for L or risk-tagged specs: STRIDE table with ASVS 5.0 IDs; optional `.tc.json`.
9. **Precedent and memory files per lane** (FP control; section 4.3), and a **resolution-rate metric** per lane.
10. **Architecture contracts** (import-linter/tach, dependency-cruiser) generated from `.claude/rules/`.
11. **SAST with project rules** (Opengrep or Semgrep CE). Promote any LLM finding raised N times into a rule.
12. **TEST-READY batch checks**: the change-set replacement detector and a drift-aware change-set preview.
    Optionally, DevOps Agent release readiness and a budget-capped Security Agent pen test.
13. **Diff-scoped CLOSE agents**: dead code (Skylos `--diff`, knip), docs delta, an unnecessary-code reviewer.
14. **Docs drift tools**: lychee, markdownlint, `drift check`.
15. **Licence policy** check on manifest change.
16. **Cost diff** (Infracost CLI on `cdk.out`) for IaC changes that touch cost. CDK support in the CLI is still
    uncertain, so this is low priority.
17. Small defects to fix directly, not file:
    - `dead-code-language-matrix.md` lists ts-prune as REQUIRED; knip alone covers it.
    - detect-secrets has had no release since 2024. Keep the baseline workflow, and consider gitleaks or
      Betterleaks with SARIF for history scans.
    - Pin every scanner action by SHA or digest (the Trivy/KICS 2026 incidents).

---

## 4. Deterministic first, SARIF to the LLM checkers, false-positive control

### 4.1 Order of execution (cheap signal first)

1. **Tier 0, seconds** (pre-commit or the first CI job): ruff, format, mypy, bandit `-ll`, detect-secrets,
   detect-private-key.
2. **Tier 1, seconds to minutes** (CI on the SHA, diff-scoped where the tool allows): tests with coverage,
   diff-coverage, OSV-Scanner on manifest change, Opengrep rules, import contracts, knip/tsc/eslint, and the
   IaC gate (`cdk synth`, cdk-nag, cfn-lint, Checkov, `--security-only`).
3. **Tier 2, LLM lanes**. Each lane gets three inputs: the diff; the Tier 0–1 SARIF results whose locations
   fall in the diff hunks (or in files the diff imports); and the project's precedent file. Each lane must:
   - (a) **triage** every tool result in its lens, marking it true positive with a fix, or false positive with
     a proposed suppression and justification;
   - (b) find what tools cannot find: logic, authorization, business rules, spec conformance.
   ZeroFalse (arXiv 2510.02534) enriches SARIF with data-flow and CWE context before LLM triage and reports
   F1 0.91–0.96 on two benchmarks. That is an academic result, but it supports feeding SARIF rather than
   asking the LLM to rediscover the same issues.
4. **Tier 3, expensive and by tier or risk only**: mutation runs, a verify pass with several samples for the
   logic-bug lane, threat models, and external agents (Security Agent, DevOps Agent, pen tests).

A Tier 0–1 failure that the maker can fix deterministically, such as lint or a missing dependency pin,
**fails fast before any LLM tokens are spent**.

### 4.2 Mapping the review contract onto SARIF 2.1.0

| Review-contract field / state-model rule | SARIF field |
|---|---|
| lane (security, devops, test, …) and failure class | `runs[].tool.driver.name` = lane; `ruleId` = `<failure-class>` or the tool's own rule id |
| Severity A/B/C/D | `level` (A, B = `error`; C = `note`; D = `none`) plus `properties.severity: "A"` (keep the letter, because the gate logic uses it) |
| Location (no line numbers for spec artefacts) | `logicalLocations[].fullyQualifiedName` = `requirements.md#AC-3`; code findings use `physicalLocation.region` |
| Defect | `message.text` |
| Material-because | `properties.materialBecause` |
| Proposed-edit | `fixes[].artifactChanges[].replacements` for code; `properties.proposedEdit` for prose |
| "A verdict on an older SHA does not count" | `runs[].versionControlProvenance[].revisionId` = SHA; `automationDetails.id` = `<issue>/<state>/<lane>/<sha>` |
| Delta review: a checker verifies its own findings on the new SHA | `partialFingerprints` (stable across iterations) + `baselineState` (`new` / `unchanged` / `updated` / `absent`) |
| Maker answers each finding: fixed / alternative / disputed | `suppressions[]` with `kind: external`, `status: underReview` or `accepted`, `justification` |
| Lane verdict CLEAN / NOT-CLEAN | `invocations[].executionSuccessful: true` + zero `error` results; `properties.verdict` |
| "Tool missing is a failure, not a skip" | `invocations[].executionSuccessful: false` + `toolExecutionNotifications` |

Forge ingestion:

- **GitHub:** `github/codeql-action/upload-sarif`, one `category` per lane or tool (an upload without a
  category replaces the previous one) [S]. Free for public repos; private repos need GitHub Code Security.
- **GitLab:** `artifacts:reports:sarif` on Ultimate, GitLab 19.2+ (18.11 behind a flag) [S]. On other tiers,
  keep the SARIF files as job artifacts and let the framework's wrapper post a summarised MR note.

The state-model predicate ("every required checker posted a verdict on SHA X") should read the SARIF
artifacts themselves, never the forge's UI.

### 4.3 False-positive control (ordered by value per token)

1. **Precedent and memory file per lane, per project.** This is the strongest lever in the market:
   - Semgrep Memories: the top two memory types are non-production code and framework protections.
   - The three-section filter file in `claude-code-security-review`.
   - CodeRabbit learnings and Bugbot learned rules.
   The framework already forbids re-raising a finding the conductor rejected. **Persist those rejections
   across issues** as `review-precedents/<lane>.md`, appended by the conductor after a dispute is upheld.
2. **Gate only on new findings**, using SARIF `baselineState == new` on the diff. Pre-existing debt goes to a
   backlog. import-linter's `ignore_imports` list and dependency-cruiser's `baseline` output are examples of a
   baseline that only shrinks.
3. **Evidence-backed A findings.** A security A must come with a failing test or a concrete source-to-sink
   trace (compare exploit validation in Security Agent, Codex Security and CodeMender). Without it, the finding
   becomes C, which matches the contract's no-hedge rule.
4. **Separate verify pass** for LLM finders on M+: a verifier tries to refute each candidate, as in Claude Code
   Review and ultrareview. For L, consider majority-of-N sampling, as Bugbot does. It is expensive, so not for S.
5. **Category exclusions by default**, tuned per project. Examples: DoS and rate-limiting, generic input
   validation without demonstrated impact, open redirects (the claude-code-security-review defaults).
6. **Measure each checker.** Track two numbers: the resolution rate (findings fixed by landing, per Bugbot's
   definition) and the dispute-upheld rate. Demote a lane to non-gating when its resolution rate falls below a
   threshold. This makes "a reviewer is judged on the defects it catches" measurable.
7. **Destructive outcomes always need a second checker.** Closing as duplicate, deleting code and
   revert-first steward actions all qualify. The claude-code dedupe bot shows what happens without one.
8. **Determinism of LLM output:**
   - schema-constrained SARIF output (as in ZeroFalse);
   - stable finding IDs across reruns (as in spec-kit `/analyze`);
   - fingerprints;
   - a fixed model per lane, recorded in `tool.driver.version`.
9. **Prompt-injection hygiene.** LLM checkers read untrusted issue and PR text, and Anthropic's action is
   explicitly not hardened against this [F]. Run checkers with read-only forge tokens and without deploy
   credentials. Run only on trusted authors, or after the maker's SHA is claimed by a framework worker.
10. **Scanner supply chain.** Pin scanner actions and images by SHA or digest, and keep them in jobs that hold
    no deploy credentials. This follows directly from the Trivy and KICS compromises in March and April 2026.

---

## 5. Sources

Framework files read: `clients/claude/agents/*.md` (front-matter of all 20; bodies of security-reviewer,
devops-iac-reviewer, best-practice-reviewer, standards-reviewer, test-architect, adversarial-verifier; headings
and key sections of spec-review-agent, doc-reviewer-agent, code-merge-reviewer, dead-code-removal-agent),
`clients/common/docs/review-contract.md`, `clients/claude/docs/dead-code-language-matrix.md`,
`src/payload/scripts/run_checks.py`, `.pre-commit-config.yaml`, `templates/pre-commit-config.yaml.template`,
`.secrets.baseline`, `discussion-log.md`.

Web:

- AWS Security Agent / Continuum: [what-is](https://docs.aws.amazon.com/securityagent/latest/userguide/what-is.html) [F]; [pricing](https://aws.amazon.com/security-agent/pricing/) [F]; [pen-test GA](https://aws.amazon.com/blogs/security/aws-security-agent-on-demand-penetration-testing-now-generally-available/); [Continuum launch](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-continuum/); [threat modeling](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-security-agent-threat-modeling/); [Kiro power + Claude Code](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-kiro-power-claude-code/); [budget controls](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-security-agent/); [boto3 API](https://docs.aws.amazon.com/goto/boto3/securityagent-2025-09-06/ImportSecurityRequirements)
- Threat Composer: [README](https://github.com/awslabs/threat-composer/blob/main/README.md); [AI CLI/MCP](https://github.com/awslabs/threat-composer/blob/main/docs/AI-CLI-MCP.md); [threat-modeling-mcp-server](https://github.com/awslabs/threat-modeling-mcp-server); [STRIDE GPT](https://github.com/mrwadams/stride-gpt); [OWASP SecOpsTM](https://owasp.org/www-project-secopstm/); [OWASP ASVS](https://github.com/OWASP/ASVS)
- Anthropic: [claude-code-security-review README](https://github.com/anthropics/claude-code-security-review/blob/main/README.md) [F]; [custom filtering](https://github.com/anthropics/claude-code-security-review/blob/main/docs/custom-filtering-instructions.md); [issue #103](https://github.com/anthropics/claude-code-security-review/issues/103); [Claude Code Security](https://www.anthropic.com/news/claude-code-security); [Claude Security beta](https://www.infosecurity-magazine.com/news/anthropic-claude-security-for-ai/); [Code Review docs](https://docs.anthropic.com/en/docs/claude-code/code-review); [code-review plugin](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-review/commands/code-review.md)
- GitHub: [Copilot Autofix](https://docs.github.com/enterprise-cloud@latest/code-security/concepts/code-scanning/copilot-autofix-for-code-scanning); [agentic autofix](https://github.blog/changelog/2026-07-10-agentic-autofix-for-code-scanning-alerts-in-public-preview/); [SARIF upload](https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file); [CCR agentic](https://github.blog/changelog/2026-03-05-copilot-code-review-now-runs-on-an-agentic-architecture/); [CCR full picture](https://github.blog/changelog/2025-10-28-new-public-preview-features-in-copilot-code-review-ai-reviews-that-see-the-full-picture/)
- Semgrep/Opengrep: [Memories](https://semgrep.dev/blog/2026/inside-the-ai-memories-security-teams-are-writing/); [96% agreement](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time); [Opengrep](https://github.com/opengrep/opengrep); [Semgrep vs Opengrep](https://semgrep.dev/docs/faq/comparisons/opengrep)
- Snyk: [plans](https://snyk.io/plans/); [CLI SARIF](https://github.com/snyk/user-docs/blob/main/developer-tools/snyk-cli/scan-and-maintain-projects-using-the-cli/snyk-cli-for-snyk-code/view-snyk-code-cli-results.md)
- OpenAI: [Aardvark](https://openai.com/index/introducing-aardvark); [Codex Security](https://openai.com/index/codex-security-now-in-research-preview/)
- Google: [CodeMender preview](https://cloud.google.com/blog/products/identity-security/find-and-fix-software-vulnerabilities-with-codemender)
- Amazon Q / Kiro: [Q end of support](https://aws.amazon.com/blogs/devops/amazon-q-developer-end-of-support-announcement/); [Kiro headless](https://kiro.dev/blog/introducing-headless-mode/); [kiro-cli-review-action](https://github.com/konippi/kiro-cli-review-action)
- Deterministic security: [Bandit SARIF](https://bandit.readthedocs.io/en/latest/formatters/sarif.html); [OSV-Scanner output](https://google.github.io/osv-scanner/output/); [guided remediation](https://google.github.io/osv-scanner/experimental/guided-remediation/); [pip-audit](https://github.com/pypa/pip-audit); [secret scanners 2026](https://appsecsanta.com/secret-scanning-tools/best-open-source-secret-scanning-tools); [Trivy compromise (Microsoft)](https://www.microsoft.com/en-us/security/blog/2026/03/24/detecting-investigatin); [Trivy compromise (Legit)](https://www.legitsecurity.com/blog/the-trivy-supply-chain-compromise-what-happened-and-playbooks-to-respond); [KICS compromise (Docker)](https://www.docker.com/blog/trivy-kics-and-the-shape-of-supply-chain-attacks-so-far-in-2026/)
- IaC: [cdk-nag README](https://github.com/cdklabs/cdk-nag/blob/main/README.md) [F]; [CDK policy validation](https://docs.aws.amazon.com/cdk/v2/guide/policy-validation-synthesis.html); [cdk-validator-cfnguard](https://github.com/cdklabs/cdk-validator-cfnguard); [cfn-lint](https://github.com/aws-cloudformation/cfn-lint/blob/main/README.md); [cfn-guard](https://github.com/aws-cloudformation/cloudformation-guard); [Checkov vs KICS](https://appsecsanta.com/iac-security-tools/checkov-vs-kics); [cdk diff](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-diff.html); [drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html); [WA IaC Analyzer](https://github.com/aws-samples/well-architected-iac-analyzer)
- DevOps Agent: [preview launch](https://aws.amazon.com/about-aws/whats-new/2025/12/devops-agent-preview-frontier-agent-operational-excellence); [release management](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-devops-agent-release-management/); [release readiness review](https://docs.aws.amazon.com/devopsagent/latest/userguide/release-management-release-readiness-code-review.html); [frontier agents GA](https://aws.amazon.com/blogs/machine-learning/aws-launches-frontier-agents-for-security-testing-and-cloud-operations/)
- Code review agents: [Augment benchmark](https://www.augmentcode.com/blog/we-benchmarked-7-ai-code-review-tools-on-real-world-prs-here-are-the-results); [Propel benchmarks](https://www.propelcode.ai/benchmarks); [Bugbot learned rules](https://prod.cursor.com/blog/bugbot-learning); [Building Bugbot](https://cursor.com/blog/building-bugbot); [CodeRabbit tools](https://docs.coderabbit.ai/tools); [CodeRabbit CLI](https://www.coderabbit.ai/cli); [Qodo 2.0](https://www.qodo.ai/blog/introducing-qodo-2-0-agentic-code-review/); [PR-Agent handover](https://www.qodo.ai/blog/qodo-is-handing-pr-agent-over-to-the-community/); [PR-Agent](https://github.com/Codium-ai/PR-Agent); [Macroscope ranking](https://macroscope.com/content/best-ai-code-review-tools-github-2026)
- Dead code: [vulture](https://github.com/jendrikseipp/vulture/blob/main/README.md); [Skylos benchmark](https://dev.to/duriantaco/python-dead-code-i-scanned-flask-fastapi-and-7-other-popular-repos-heres-what-i-found-5c1c); [knip reporters](https://knip.dev/features/reporters); [ts-prune](https://github.com/nadeesha/ts-prune)
- Tests: [mutmut](https://github.com/boxed/mutmut/blob/main/README.rst); [Stryker incremental](https://stryker-mutator.io/docs/stryker-js/incremental/); [mutation-testing-elements schema](https://github.com/stryker-mutator/mutation-testing-elements); [Meta ACH paper](https://arxiv.org/abs/2501.12862v1); [Meta ACH blog](https://engineering.fb.com/2025/02/05/security/revolutionizing-software-testing-llm-powered-bug-catchers-meta-ach/)
- Requirements: [QVscribe INCOSE automation](https://2367473.fs1.hubspotusercontent-na1.net/hubfs/2367473/Automating%20the%20INCOSE%20Guide%20for%20Writing%20Requirements.pdf); [requirements-review](https://github.com/EnzinoBB/requirements-review); [INCOSE IS2024 paper](https://www.incose.org/wp-content/uploads/2026/01/paper_505.pdf); [EARS](https://en.wikipedia.org/wiki/Easy_Approach_to_Requirements_Syntax); [spec-kit](https://github.com/github/spec-kit); [AI-DLC phases](https://awslabs.github.io/aidlc-workflows/guide/04-phases-and-stages/); [AI-DLC construction](https://awslabs.github.io/aidlc-workflows/reference/04-stages/construction/)
- Architecture: [import-linter layers](https://github.com/seddonym/import-linter/blob/main/docs/contract_types/layers.md); [tach vs import-linter](https://github.com/gauge-sh/tach/discussions/72); [PostHog architecture](https://github.com/PostHog/posthog-foss/blob/master/products/architecture.md); [dependency-cruiser CLI](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md); [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS)
- Docs drift: [fiberplane drift](https://github.com/fiberplane/drift); [drift blog](https://fiberplane.com/blog/drift-documentation-linter/); [pallaprolus drift](https://github.com/pallaprolus/drift-vscode); [EkLine on docs CI](https://ekline.io/blog/documentation-review-in-ci)
- Licences: [Trivy license](https://trivy.dev/docs/latest/scanner/license/); [licensecheck](https://pypi.org/project/licensecheck/); [licence scanner roundup](https://appsecsanta.com/sca-tools/open-source-license-compliance)
- Cost/perf: [Infracost CDK](https://www.infracost.io/resources/blog/aws-cdk-support); [Infracost CloudFormation CLI](https://www.infracost.io/resources/blog/infracost-cli-v2-now-reads-cloudformation); [Infracost FAQ](https://www.infracost.io/faq); [AWS Pricing MCP](https://github.com/awslabs/mcp/blob/main/src/aws-pricing-mcp-server/README.md); [CodSpeed](https://docs.codspeed.io/features/performance-checks)
- Dedupe: [AI Duplicate Detector](https://github.com/mackgorski/ai-duplicate-detector); [GenAI Issue Deduplicator](https://github.com/marketplace/actions/genai-issue-deduplicator); [claude-code auto-close complaint #50898](https://github.com/anthropics/claude-code/issues/50898); [#20282](https://github.com/anthropics/claude-code/issues/20282); [GitHub duplicate-detection gist](https://gist.github.com/sunnyi101/91f76bd838585479aa72cb190dd628a1); [GitLab issue triage flow](https://devpost.com/software/issue-triage-agent)
- SARIF / FP research: [GitLab SARIF reports](https://docs.gitlab.com/user/application_security/detect/sarif); [ZeroFalse](https://arxiv.org/abs/2510.02534v1)
