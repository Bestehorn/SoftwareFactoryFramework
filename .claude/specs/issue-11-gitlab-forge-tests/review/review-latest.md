# Review — latest (design review iteration 02, delta)

Lanes: spec-review-agent NOT-READY (0 A, 1 B, 2 C), test-architect NOT-TEST-READY (1 A, 2 C; 37 OK, 0 GAP of 37),
standards-reviewer NOT-READY (0 A, 2 B, 2 C, 1 D), best-practice-reviewer READY (1 C); security-reviewer and
devops-iac-reviewer READY since iteration 01.

Combined A+B after dedupe: 2 (1 A, 1 B). None rejected or downgraded.

## Open material findings (to apply)

- test A1 = spec B1 = standards B1 (one defect, graded A) — D1's two-keyword `refuse_distributed_run` call fails L's
  `passes_own_worker_id`, which G reuses: `ephemeral_project` calls a one-keyword `refuse_distributed_run(*,
  worker_id)` of `test/forge_gitlab/ephemeral.py`, which passes `command=GITLAB_FORGE_COMMAND` to the reused one;
  D10 lists it.
- standards B2 — design.md `## Residuals` over ten lines: delete the `report`/action-pins bullet and the local-workspace
  bullet (restated elsewhere); the two sub-threshold bullets (the proposed gitlab.com per-user limit; the helpers git
  asks on an unauthenticated command) leave the spec for findings-ledger rows the conductor writes in this change.

## C/D (apply in the same pass)

spec C1 (`helper` a callable, `functools.partial`), spec C2 (W subprocess example names its accepted config), test C1
(the refusal names `GITLAB_FORGE_COMMAND`), test C2 (the helper test goes through the GitLab `helper`), standards C1
(as spec C1), standards C2 (UB-4 allows the matching body and docstring edits), standards D1, best-practice C1 (a
pending run on `main` can be replaced).
