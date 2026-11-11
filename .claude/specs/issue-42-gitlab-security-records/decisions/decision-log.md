# Decision Log

## DL-001 — 2026-11-11T06:03:50Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #41's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #42 Tier line (S — data records and fake-host tests in five existing family modules on part 1's rec…); #41 design D8 (a slice edits its family modules and test modules).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #42 body; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T06:19:26Z — issue-work-orchestrator — phase:SPEC

**Decision:** The issue's open questions: the administrator sections get records of their own (they do not join part 1's records, whose rows N compares to their own section); downloads are plain records printed as bytes under #41 D3.
**Driver:** issue #42 Open questions; N `record_problems`; #41 design D3.
**Alternatives considered:** join the admin attributes into part 1's records (rejected: fails N).
**Evidence:** test/test_gitlab_wrapper_contract.py `record_problems`; issue-41 design D3.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T06:19:26Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep 17 keys pending: the second endpoints of multi-endpoint References (one record per id; the record takes the `/projects/:id/` endpoint, else the first), the `https://HOST/oauth/token/info` path, and the compliance external-control status `PATCH` that needs HMAC request headers the transport cannot send; the item "five `PENDING` empty" is deferred on #42, with a ledger row.
**Driver:** #41 design Residuals (one record per id; `https://HOST` paths; `In` `header` rows).
**Alternatives considered:** re-tier to M and build the missing forms (rejected: a mechanism outside the slice's ask).
**Evidence:** change.md AC-2, Residuals.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T06:19:26Z — issue-work-orchestrator — phase:SPEC

**Decision:** A GET headed "List" or "Get all" is `Paging.OFFSET`, none `KEYSET`; Type maps to `Kind` except `PUT /user/avatar`'s `avatar` is `FILE` (multipart per conventions.md "Avatars"); one F module per family, `security_governance` included.
**Driver:** docs/api-reference/gitlab/conventions.md "Pagination", "Avatars"; #41 design D8.
**Alternatives considered:** none
**Evidence:** conventions.md; docs.gitlab.com/api/users ("use the --form argument").
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T06:41:18Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** The administrator sections get no record in this slice (as change.md's Ask and Residuals say), superseding DL-002's "records of their own": their attributes are not part 1's records' own section rows, and giving them records is outside the slice's ask (ledger row).
**Driver:** review/spec-review-agent/iteration-01.md B2.
**Alternatives considered:** records for them (rejected: not the issue's ask).
**Evidence:** change.md Ask, Residuals.
**Supersedes:** DL-002 (its administrator-sections clause only)
**Artifacts touched:** change.md

## DL-006 — 2026-11-11T06:41:18Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** AC-5's paging rule names three exceptions: `security-factory#list-all-project-security-settings` and `software-supply-chain-security#list-all-token-associations` answer one object (`Paging.NONE`), and `security-risk-management#retrieve-project-external-status-check-services` pages (`Paging.OFFSET`); `avatar` is `FILE` on the create-user and modify-user sections as on `PUT /user/avatar`.
**Driver:** review/spec-review-agent/iteration-01.md A1, B1; GitLab docs and `ee/lib/api/status_checks.rb`, `lib/api/users.rb` at a186442.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md.
**Supersedes:** DL-004 (its paging rule and avatar exception, extended)
**Artifacts touched:** change.md

## DL-007 — 2026-11-11T06:41:18Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** No record of these families writes a branch, merges or creates an issue; the policy store persists policies to the database (GitLab 19.4), not to a branch, so `commands/call.py` is untouched.
**Driver:** review/spec-review-agent/iteration-01.md D1 (the citation moves here to free bytes).
**Alternatives considered:** none
**Evidence:** docs.gitlab.com/api/policy_store.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-008 — 2026-11-11T06:52:01Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 02 READY (the tier-S cap); iteration 01's A1, B1, B2, C1, C2 and D1 applied.
**Driver:** review/spec-review-agent/iteration-0{1,2}.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-02.md Verdict line.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-009 — 2026-11-11T08:38:03Z — issue-work-orchestrator — phase:VERIFY

**Decision:** Accept the verifier's AC-3 refutation as a test gap: each of the five F modules gains `test_every_body_is_json_and_unfixed` (every record's `body` is JSON and `fixed` empty), proven by the verifier's B1/B3 mutants; no product change, then a delta re-verification.
**Driver:** evidence/verify/refutation-report.md AC-3 row (B1, B3 survived).
**Alternatives considered:** one check in N (rejected: N is #41 D8's never-edit row).
**Evidence:** evidence/verify/refutation-report.md; change.md AC-3.
**Supersedes:** none
**Artifacts touched:** the five src/payload/test/test_gitlab_api_<module>.py files
