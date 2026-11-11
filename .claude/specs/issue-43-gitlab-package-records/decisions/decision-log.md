# Decision Log

## DL-001 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's tier line): records plus the `/<route-prefix>`, hyphenated-placeholder and registry-host forms; the `*name` glob is #40's form, reused here after #40 lands (this branch rebases onto it before its implementation waves).
**Driver:** issue #43 Tier line and open questions; #40 DL-001 (owns the glob and optional-segment forms, reusable by #43).
**Alternatives considered:** building the glob here too (rejected: two implementations of one form); tier S by excluding every key that needs a form (rejected: #41 records no such exclusion rule, #40 DL-002).
**Evidence:** issue #43 body; .claude/worktrees/issue-40/.claude/specs/issue-40-gitlab-openapi-only-records/decisions/decision-log.md DL-001, DL-002.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T08:32:10Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** The two container-registry host keys stay pending with a residual, narrowing prompt.md's Tier line (no registry-host form is built): they need the registry's own host and a `/jwt/auth` bearer token, and the transport refuses any other origin.
**Driver:** docs.gitlab.com container registry API ("Delete image tags by reference", "Listing all container repositories"); transport.py `_send` origin check; #13 Security Considerations; UB-2 (credentials only from config/gitlab.json).
**Alternatives considered:** records with another base URL (rejected: a new config key, a token exchange and a second allowed origin).
**Evidence:** requirements.md AC-1.3, Residuals; src/payload/scripts/gitlab_api/transport.py `_send`.
**Supersedes:** DL-001 (its registry-host clause only)
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-11T08:32:10Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** A two-endpoint entry (the Conan v1 entries, NuGet "Upload a package file") gets one record on its first endpoint and its second key stays pending; no exclusion rule; `:module-name` handled by widening `PLACEHOLDER` (the only `:name-` path in the index); no default route prefix (a missing or unlisted prefix is refused, exit 2); `string array` → `ARRAY`.
**Driver:** registry.lookup one record per id; V `record_key_problems`; #41 design Residuals (several keys under one Reference); #40 DL-002, DL-003; #13 D5.
**Alternatives considered:** renaming `:module-name` in the record (rejected: the path must match the index verbatim); a default prefix (rejected: silently picks instance, group or project).
**Evidence:** requirements.md AC-1.2, AC-1.5, AC-2.x, UB-4; docs/api-reference/gitlab/rest/package.md; operations-index.md.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-004 — 2026-11-11T10:13:16Z — issue-work-orchestrator — phase:DESIGN

**Decision:** The Workhorse body-upload package routes (Conan v1/v2, Debian, Maven, npm, Ruby gems, the Terraform module upload) are raw-body records on #40's D5 form (`call --input`; npm `application/json`, the rest `application/octet-stream`; attributes in the query); NuGet, PyPI, Helm, the Maven virtual-registry upload and `avatar` stay multipart; requirements AC-1.4, AC-4.2 and the two Residuals that cited #40 DL-004 are restated to match, as #40 DL-007 restated its AC-3.2.
**Driver:** design.md D5 (Workhorse `routes.go` `requestBodyUploader` vs `mimeMultipartUploader`); #40 DL-007, DL-008; a multipart body to a body-uploader route is stored with its envelope as the file.
**Alternatives considered:** keep multipart per the frozen ACs (rejected: stores a corrupted package, the defect #40's review found as A1).
**Evidence:** design.md D5; .claude/worktrees/issue-40/.claude/specs/issue-40-gitlab-openapi-only-records/decisions/decision-log.md DL-007.
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md

## DL-005 — 2026-11-11T10:13:16Z — issue-work-orchestrator — phase:DESIGN

**Decision:** The hyphenated placeholder widens `PLACEHOLDER`'s name group (only the Terraform upload row matches `[:*]name-`); the route prefix is a record field `route_prefixes` chosen by exact text through `call --route-prefix PREFIX` after the lookup (no default, refused otherwise), with N reading the page's `<route-prefix>` line; #41 D8's never-edit row yields for `call.py` as it did for #40.
**Driver:** requirements AC-1.5, AC-2.x, AC-4.1; operations-index.md grep; rest/package.md `<route-prefix>` lines; DL-003.
**Alternatives considered:** rename `:module-name` in the record (rejected: DL-003); free-text prefixes (rejected: caller text would become path text).
**Evidence:** design.md D1-D4.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-006 — 2026-11-11T11:12:20Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Apply design review iteration 01: npm "Create or update a dist-tag" becomes a raw JSON-body record (`version` a query `Param`); `("PUT", "/projects/:id/")` stays pending (a pull mirror can overwrite the trunk; residual to tenant-scale's "Update a project"); the NuGet v3 upload keeps its record but goes to the proxy residual; the Conan, Debian, NuGet, Helm and Ruby gems routes get no transport authentication (one residual; HTTP Basic out of scope).
**Driver:** review/review-latest.md A1, B1-B4; npm_endpoints.rb dist-tags `put` (`env['api.request.body']`); docs.gitlab.com project pull mirroring; Workhorse routes.go `/packages/nuget/`; each route's `authenticate_with`.
**Alternatives considered:** gating `PUT /projects/:id/` (rejected: no compatibility subcommand to name; UB-4 freezes `GATED_OPERATIONS`).
**Evidence:** review/*/iteration-01.md; design.md D4-D6, Security Considerations, Residuals.
**Supersedes:** DL-004 (its `avatar` clause only)
**Artifacts touched:** requirements.md, design.md

## DL-007 — 2026-11-11T11:31:49Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md and design.md after design review iteration 02: every lane READY (best-practice, security, standards, spec at iteration 02; devops and test-architect at iteration 01); the practice lane's last D (the Workhorse catch-all route wording) applied by the conductor as the lane's sentence.
**Driver:** review/{best-practice-reviewer,security-reviewer,standards-reviewer,spec-review-agent}/iteration-02.md; review/{devops-iac-reviewer,test-architect}/iteration-01.md.
**Alternatives considered:** none
**Evidence:** the lane files' Verdict lines.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-008 — 2026-11-11T11:57:07Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 01 (both lanes READY, 0 A, 0 B; C1, C2, D1 applied, 14,793 B); implementation starts after #40's PR merges and this branch rebases onto origin/main (DL-001).
**Driver:** review/test-architect/tasks-iteration-01.md; review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** none
**Evidence:** both tasks-iteration-01.md Verdict lines.
**Supersedes:** none
**Artifacts touched:** tasks.md
