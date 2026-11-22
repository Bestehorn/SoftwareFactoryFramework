# Review — latest (design review iteration 01)

Lanes: spec-review-agent NOT-READY (0 A, 1 B), test-architect NOT-TEST-READY (0 A, 4 B; 33 OK, 4 GAP of 37),
standards-reviewer NOT-READY (0 A, 2 B), best-practice-reviewer NOT-READY (0 A, 1 B), security-reviewer READY
(3 C), devops-iac-reviewer READY (4 C, 1 D).

Combined A+B: 8 (0 A, 8 B). Every B carries a Material-because and a Proposed-edit; none is rejected or downgraded.

## Open material findings (to apply)

- spec B1 — AC-4.1 vs D2: a config `_load_config` refuses exits 1 before the guard; narrow AC-4.1 to configs it
  accepts and say so in AC-4.1 and D2.
- standards B1 — six #10 functions copied with GitHub constants swapped; give the six keyword-only parameters
  defaulting to today's GitHub constants and call them; restate UB-4 as behaviour, not untouched files.
- standards B2 — the User Prompts sections of requirements.md and design.md lack two verbatim operator messages.
- test B1 — AC-4.1 near-miss values (`Bestehorn/x-sff-test-y`, `Bestehorn/sff-test-x/SoftwareFactoryFramework`).
- test B2 — AC-1.4: a creation answered other than `private` is refused and still deleted; add the S case.
- test B3 — AC-9.1: scope the setup-note checks to the GitLab section and require `gitlab.com`.
- test B4 — AC-5.3: assert that `write_credential.main` logs the "secret unavailable" message.
- best-practice B1 — `test_the_merge_request_records` reads MR commits before GitLab builds the diff; call
  `wait_until_checked` after `mr create`.

## C/D (apply in the same pass where they restate; a scope-adding C stays a residual)

spec C1, D1, D2; test C1 to C8; standards C1 to C4, D1; best-practice C1; security C1 to C3; devops C1 to C4, D1 —
each lane file under `review/<lane>/iteration-01.md`.
