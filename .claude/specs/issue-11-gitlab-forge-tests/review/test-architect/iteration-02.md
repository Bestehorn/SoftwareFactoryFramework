# Test architect — design review, iteration 02 (delta)

## Findings

### A1 — The fixture's two-keyword refusal fails the structural check G reuses from L
Severity: A
Location: design.md § D1 "One project per run"; § Correctness Properties AC-1.1 (G `test_the_session_fixture_wraps_one_provision`)
Defect: this revision (standards B1) has `ephemeral_project` call the reused `refuse_distributed_run(worker_id=..., command=GITLAB_FORGE_COMMAND)`, but the G test applies L's `session_fixture_problems`, whose `passes_own_worker_id` (`test/test_forge_suite_layout.py`) is false unless the call has no positional argument and exactly one keyword, `worker_id=worker_id`; the fixture D1 specifies therefore makes G report "it does not call `refuse_distributed_run(worker_id=worker_id)`" and fail.
Material-because: AC-1.1 and AC-1.4 — their structural test cannot pass against the fixture the design specifies, so the change cannot be implemented as written (`tests-must-not-fail.md`).
Proposed-edit: in D1 "One project per run", replace "`ephemeral_project` first calls the reused `refuse_distributed_run(worker_id=..., command=GITLAB_FORGE_COMMAND)`: #10 D1's check" with "`ephemeral_project` first calls `refuse_distributed_run(worker_id=worker_id)` of `test/forge_gitlab/ephemeral.py`, which calls the reused one with `command=GITLAB_FORGE_COMMAND` (L's `passes_own_worker_id` admits that one keyword only): #10 D1's check".

### C1 — AC-1.1: the distributed-run refusal's command has no oracle
H's twin asserts only `--workers 1` in the message, so a GitLab call that drops `command=` passes S while telling the operator to run `test/forge`.
Proposed-edit: append to AC-1.1's "Example, S `test_a_distributed_run_is_refused`" the words "; the refusal names `GITLAB_FORGE_COMMAND`".

### C2 — AC-6.3: the helper test should exercise the GitLab binding, not the reused function
If S calls the reused `credential_helper_arguments` with constants the test passes itself, a `SubprocessGitRunner(helper=...)` binding left on the GitHub defaults passes S and fails only in F.
Proposed-edit: in AC-6.3, after "`test_the_credential_helper_answers_git_with_the_clone_token`, as #10's" insert ", through the `helper` that `test/forge_gitlab/ephemeral.py` gives `SubprocessGitRunner`".

## Coverage

Legend as design.md's mapping (W, S, G, L, H, F, C, A, K, V, P, I, B).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning, distributed run; G session fixture | OK; G red as written (A1) |
| AC-1.2 | S run id | OK |
| AC-1.3 | F fixture, no pipeline, repository records; S provisioning | OK |
| AC-1.4 | S provisioning, non-private creation refused and deleted; G session fixture | OK; G as AC-1.1 (A1) |
| AC-2.1 | S teardown deletes | OK |
| AC-2.2 | S teardown refuses | OK |
| AC-2.3 | S no creation | OK |
| AC-3.1 | S sweep property (near misses), boundaries; F sweep (inline selection) | OK |
| AC-3.2 | S sweep property, boundaries | OK |
| AC-3.3 | S sweep property, boundaries | OK |
| AC-4.1 | W refuses (seven values, near misses included; no config exits 1), W entry script | OK |
| AC-4.2 | W ephemeral through (call and `enqueue-pr`); every F | OK |
| AC-4.3 | S marker argv; W values, without marker; G | OK |
| AC-5.1 | G job beside verify (job and steps) | OK |
| AC-5.2 | G secret step, nothing keeps | OK |
| AC-5.3 | S missing secret (`main` logs the text, returns 1; with a token 0) | OK |
| AC-5.4 | G report; L report | OK |
| AC-6.1 | S credential lookup | OK |
| AC-6.2 | S bad credential | OK |
| AC-6.3 | S written only to clone, commits none, helper (options asserted first); G secret step | OK |
| AC-7.1 | G default collects none | OK |
| AC-7.2 | G path collects all | OK |
| AC-7.3 | G nothing keeps | OK |
| AC-8.1 | G ephemeral only; every F | OK |
| AC-8.2 | F subcommands (4) | OK |
| AC-8.3 | F records (3, MR records after `wait_until_checked`); F fixture | OK |
| AC-8.4 | F graphql | OK |
| AC-8.5 | F request forms (2); G uncalled forms | OK |
| AC-8.6 | G uncalled forms (record and its reason, in the module docstring) | OK |
| AC-8.7 | G ephemeral only | OK |
| AC-9.1 | G setup note (GitLab section, `gitlab.com`, local-only sentence in it) | OK |
| AC-9.2 | G map (`test/forge_gitlab` beside the command); B | OK |
| UB-1 | W, S, G in `verify` on doubles; fake-host suites unedited | OK |
| UB-2 | S sentinel (another token, `token_type`; clone config keys exact) | OK |
| UB-3 | C, A, K, V, P unedited; W without marker | OK |
| UB-4 | H unedited (five of the six defaulted functions); L one expectation extended (`STATUS_ASSIGNMENT` `^status=`, `FORGE_RESULT` `needs.forge.result` only; `product_wrapper_problems` walks defaults); the `forge` job (all six on github.com) | OK |
| UB-5 | I; the PR diff | OK |

37 OK, 0 GAP.

NOT-CLEAN (1 A, 0 B) — NOT-TEST-READY
