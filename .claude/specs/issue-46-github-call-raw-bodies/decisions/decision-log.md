# Decision Log

## DL-001 — 2026-11-11T04:19:22Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's tier line): one design choice spanning `commands/call.py`, `registry.py` and `transport.py`; implementation after #27 and #33 land (their modules hold the two records).
**Driver:** issue #46 Tier line and Open questions; #27 DL-002; #33 DL-001.
**Alternatives considered:** tier S (rejected: the input form and the redirect policy are open design choices).
**Evidence:** issue #46 body; .claude/specs/issue-28-generic-operation-command/design.md D2, D4.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T04:28:57Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Accept the requirements as written: Requirement 5 (usage docstring and map) from the issue's work item; UB-1.1's two exceptions (the same-origin `307` re-send for every `PATCH`/`DELETE`, and the two newly declared records); the credential reaches `https://uploads.github.com` only on the upload call.
**Driver:** issue #46 Work items and draft AC-2, AC-3; requirements.md author report (the draft's UB-1 contradicted AC-3).
**Alternatives considered:** limit the re-send to `call` (rejected: the draft's AC-3 names every PATCH or DELETE, and the existing subcommands fail the same way today).
**Evidence:** requirements.md Requirements 3 and 5, UB-1.1.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Body input is `--input FILE` (`-` for standard input), accepted only by a record that declares a non-JSON media type, refused with `-f`/`-F` (exit 2, first step); a JSON body never comes through it, so #28's secrets-in-arguments residual stays a residual.
**Driver:** requirements.md AC-1.1..AC-1.3; issue #46 Open question 1; `gh api --input`.
**Alternatives considered:** JSON bodies from a file (rejected: bypasses #28's undocumented-name refusal); `argparse.FileType` (rejected: deprecated since Python 3.14).
**Evidence:** design.md D1.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-004 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** `RestOperation` gains `origin` (default `API_ROOT`) and `content_type` (default none) — a registry change past #28 D8's exceptions row, owned by this issue; `Transport.request_raw` refuses any root but the API and upload origins; `Transport.upload` stays unchanged.
**Driver:** requirements.md AC-2.1, AC-2.2; issue #46 Open question 2.
**Alternatives considered:** call options (rejected: any call could send the credential to the upload host); a table in `commands/call.py` (rejected: `registry.send` would still send JSON to the API host).
**Evidence:** design.md D2.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-005 — 2026-11-11T04:53:21Z — issue-work-orchestrator — phase:DESIGN

**Decision:** The `307` re-send lives in `CredentialStrippingRedirectHandler.redirect_request`, once (`ResentRequest` marker), same origin only; a cross-origin `307` exits 1 without the credential; #27's `test_only_the_upload_is_pending` and #33's pending-ids test are restated as a spec change when the two records are declared.
**Driver:** requirements.md AC-3.1, AC-3.2, UB-2.2; design.md D3, D4.
**Alternatives considered:** re-send in `Transport._send` (rejected: repeats urllib's `Location` resolution).
**Evidence:** design.md D3, D4.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-006 — 2026-11-11T05:12:30Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Edit three files #28 D8 marks "never" for a slice: `src/payload/test/github_wrapper_fixtures.py` (`NonGetRequest.of` compares a non-JSON body as bytes), N `test/test_github_wrapper_contract.py` (the upload routed to its `Host:`), and the entry script's docstring (AC-5.1); this issue owns the request form, not a family slice.
**Driver:** review/spec-review-agent/iteration-01.md C6; requirements.md AC-4.1, AC-5.1.
**Alternatives considered:** none (each edit is the only route to its criterion).
**Evidence:** design.md D5, D7.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-007 — 2026-11-11T05:31:50Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** The record field DL-004 names `origin` is `root` (review ST-D1), matching `request_raw(root=...)`.
**Driver:** review/standards-reviewer/iteration-01.md D1; review/test-architect/iteration-02.md.
**Alternatives considered:** none
**Evidence:** design.md D2.
**Supersedes:** DL-004 (its field name only)
**Artifacts touched:** design.md

## DL-008 — 2026-11-11T05:31:50Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md and design.md after design review iteration 02: every lane CLEAN or READY (Z1 and every C/D applied).
**Driver:** review/*/iteration-0{1,2}.md; review/review-latest.md.
**Alternatives considered:** none
**Evidence:** review/test-architect/iteration-02.md (16/16 COVERED) Verdict line.
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md

## DL-009 — 2026-11-11T06:04:10Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 02 (the cap): test lane CLEAN (16/16 COVERED), spec lane READY; the Run lines of waves 1, 2 and 4 are the glob over every GitHub suite.
**Driver:** review/test-architect/tasks-iteration-0{1,2}.md; review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** none
**Evidence:** review/test-architect/tasks-iteration-02.md Verdict line.
**Supersedes:** none
**Artifacts touched:** tasks.md
