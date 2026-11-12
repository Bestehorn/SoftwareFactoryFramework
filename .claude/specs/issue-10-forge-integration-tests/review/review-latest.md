# Review — design iteration 02 (delta, consolidated)

Lanes on the revision of commit 170b4ba: spec-review-agent CLEAN; standards-reviewer CLEAN; devops-iac-reviewer CLEAN;
security-reviewer CLEAN; best-practice-reviewer CLEAN; test-architect NOT-CLEAN (0 A, 1 B), NOT-READY (33 OK, GAP
AC-4.3 and AC-8.1). Every iteration-01 A/B is resolved (each lane's iteration-02 file says so per id).

Combined A+B: 1. Nothing rejected.

## A/B (apply)

| Id | Lane | Defect | Fix |
|---|---|---|---|
| B1 | test-architect B1 | AC-4.3's oracle misses an in-process call: a forge module calling `product_wrapper().main(argv=...)` runs the wrapper without `-X sff_test_marker` | L, by `ast`: outside its definition `PRODUCT_WRAPPER` is named only in `SubprocessWrapperRunner` and `product_wrapper`; only `ephemeral.py` names `product_wrapper`; no file of `test/forge/` reads an attribute `main` (as the lane file proposes) |

## C/D (apply in the same pass — restate, clarify, tighten, remove)

- test-architect C1: AC-6.1's example adds a linked worktree that holds its own file (it is preferred); C2: L requires the fixture to pass its own `worker_id` parameter to `refuse_distributed_run`; D1: AC-7.3's `ast` check names `.py` files.
- standards C1 = spec-review D2: `owner.rpartition(USERINFO_SEPARATOR)[2]`, as `_without_userinfo` does.
- standards C2 = devops D1: the Residuals line on an interrupted local run says "Nothing in this change removes …", and that inside a session the scoped temp (`tmp/os-temp`) is emptied by `reap_agent_temp.py --scoped-temp`.
- standards C3 = best-practice C1: D8's Windows owner-only claim holds on CPython builds with the CVE-2024-4030 fix (3.12.4 and later, the 2024 security releases); say so in one sentence.
- standards D1: the D10 `ephemeral.py` row — the `product_wrapper()` clause in parentheses, scoped to the two constants.
- security C1: Rollback: the secret and the token stay only while the suite is to return; otherwise the operator deletes `SFF_TEST_TOKEN` and revokes the token.
- spec-review D1: the AC-6.2 mapping row cites D9 step 2.

## Residuals

Unchanged from iteration 01 (design.md `## Residuals`).
