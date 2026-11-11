# Decision Log

## DL-001 — 2026-11-11T11:43:34Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S, one wave: declare `pulls/update-branch` and `code-scanning/commit-autofix`, each refused through a `None` entry of `GATED_OPERATIONS` (no subcommand sends it), and declare `copilot/set-copilot-content-exclusion-for-organization`, leaving its body form to the change.md author with evidence; the three are all that keeps #14's "part 1's pending list empty" unmet.
**Driver:** issue #14 Ask ("Done: part 1's pending list empty"); trunk 7ec47d1 PENDING: code_scanning, copilot and pulls hold one id each; ledger rows of #31 DL-003 and #32 DL-002 ("gating is one None entry now that #27 landed"), #33 DL-004.
**Alternatives considered:** leave the three in the ledger and close #14 over an open item (rejected: #14's Done names an empty list).
**Evidence:** git show origin/main:src/payload/scripts/github_api/families/{pulls,code_scanning,copilot}.py `PENDING`; docs/findings-ledger.md rows on origin/main.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T11:57:07Z — issue-work-orchestrator — phase:SPEC

**Decision:** `copilot/set-copilot-content-exclusion-for-organization` declares `body_params={"*"}`, `registry.ANY_BODY_NAME = "*"` meaning any body name (an early return in `registry._check_names` and `commands/call.py` `_undocumented` for body names only); both branch-writers get a `None` entry in `GATED_OPERATIONS`; registry.py and call.py edits beyond `GATED_OPERATIONS` are a #28 D8 exception this issue names.
**Driver:** rest/copilot.md: the section's only body row is `*` ("any key"); N's `first_level_name` reads `{"*"}` and `_plan_call` sends `--raw-field *=...`; the copilot section is the only `*` body row in the reference; docs.github.com pages for update-branch (merges into the PR branch) and commit-autofix (commits to `target_ref`).
**Alternatives considered:** `content_type` with `--input` (rejected: N expects `{"*"}` and a JSON body); keep pending (rejected: #14's Done).
**Evidence:** change.md AC-1..AC-4; test/test_github_wrapper_contract.py `first_level_name`, `_plan_call`.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T11:57:07Z — issue-work-orchestrator — phase:SPEC

**Decision:** Close the three open ledger rows (#31 DL-003, #32 DL-002, #33 DL-004) with new rows of status `enforced <F path>`, written through `memory_compile.py ledger add`, in this change.
**Driver:** issue-filing-discipline.md "findings ledger": rows are written only by the tool; status `enforced <path>` names the test.
**Alternatives considered:** editing the rows (rejected: the tool is the only writer).
**Evidence:** change.md Files.
**Supersedes:** none
**Artifacts touched:** docs/findings-ledger.md (at IMPL)

## DL-004 — 2026-11-11T12:17:29Z — issue-work-orchestrator — phase:SPEC

**Decision:** Approve change.md after combined review iteration 01 READY (0 A, 0 B; C1, C2, D1, D2 applied, 7,958 B); K's `pending-id` row and `OP_PULLS_UPDATE_BRANCH` leave K, as #39 restated `OP_PENDING_ONLY`, because no id stays pending. The official pages: update-branch merges the base branch into the pull request branch; commit-autofix commits to the existing branch `target_ref`.
**Driver:** review/iteration-01.md verdict; docs.github.com pulls#update-a-pull-request-branch, code-scanning#commit-an-autofix-for-a-code-scanning-alert.
**Alternatives considered:** none
**Evidence:** review/iteration-01.md; change.md AC-3, Files.
**Supersedes:** none
**Artifacts touched:** change.md
