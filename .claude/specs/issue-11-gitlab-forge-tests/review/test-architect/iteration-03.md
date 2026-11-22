# Test architect — design review, iteration 03 (delta)

## Prior findings

- A1 (iteration 02) resolved. D1 now has `ephemeral_project` make one call with the single keyword
  `worker_id=worker_id`. L's `the_refusal` matches it through `called_name`, which returns `attr` for `obj.f(...)`.
  `passes_own_worker_id` and `refusal_problems` (`test/test_forge_suite_layout.py`) accept it, as they accept #10's
  `EPHEMERAL.refuse_distributed_run(worker_id=worker_id)` in `test/forge/conftest.py` `ephemeral_repository`. The
  two-keyword call to the reused function sits in `test/forge_gitlab/ephemeral.py`, outside the fixture body G inspects.
- C1 (iteration 02) applied. S `test_a_distributed_run_is_refused` fails if the GitLab wrapper drops `command=`: the
  message would then end in `FORGE_COMMAND`, which is a proper prefix of D1's command, so
  `GITLAB_FORGE_COMMAND in message` is false.
- C2 (iteration 02) applied. See C1 below for the binding it leaves unnamed.

## Findings

### C1 — AC-6.3: the GitLab `helper` that S tests has no name the fixture shares
Severity: C
Location: design.md § D10 bullet "The git runner"; § Correctness Properties AC-6.3
Defect: AC-6.3 now runs S "through the `helper` that `test/forge_gitlab/ephemeral.py` gives `SubprocessGitRunner`".
D10, however, names no symbol for that `functools.partial`, and D9 has `ephemeral_project` build both runners. A conftest
that builds its own partial, or passes none (leaving the GitHub default), therefore keeps S green on a binding the run
never uses. Only F would catch it.
Proposed-edit: in D10, replace "The git runner is the reused `SubprocessGitRunner(clone=..., helper=...)`, its `helper`
a callable that" with "The git runner is the reused `SubprocessGitRunner(clone=..., helper=GIT_HELPER)`, `GIT_HELPER`
this module's one binding, which `ephemeral_project` passes and S
`test_the_credential_helper_answers_git_with_the_clone_token` calls: a callable that".

## Coverage

Legend as design.md's mapping (W, S, G, L, H, F, C, A, K, V, P, I, B).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning, distributed run (names `GITLAB_FORGE_COMMAND`); G session fixture (one-keyword call) | COVERED |
| AC-1.2 | S run id | COVERED |
| AC-1.3 | F fixture, no pipeline, repository records; S provisioning | COVERED |
| AC-1.4 | S provisioning, non-private creation refused and deleted; G session fixture | COVERED |
| AC-2.1 | S teardown deletes | COVERED |
| AC-2.2 | S teardown refuses | COVERED |
| AC-2.3 | S no creation | COVERED |
| AC-3.1 | S sweep property (near misses), boundaries; F sweep | COVERED |
| AC-3.2 | S sweep property, boundaries | COVERED |
| AC-3.3 | S sweep property, boundaries | COVERED |
| AC-4.1 | W refuses (seven values; no config exits 1); W entry script (accepted config, `project_id` `"1234"`, the guard's message) | COVERED |
| AC-4.2 | W ephemeral through (call and `enqueue-pr`); every F | COVERED |
| AC-4.3 | S marker argv; W values, without marker; G | COVERED |
| AC-5.1 | G job beside verify | COVERED |
| AC-5.2 | G secret step, nothing keeps | COVERED |
| AC-5.3 | S missing secret | COVERED |
| AC-5.4 | G report; L report | COVERED |
| AC-6.1 | S credential lookup | COVERED |
| AC-6.2 | S bad credential | COVERED |
| AC-6.3 | S written only to clone, commits none, helper through the GitLab binding (C1); G secret step | COVERED |
| AC-7.1 | G default collects none | COVERED |
| AC-7.2 | G path collects all | COVERED |
| AC-7.3 | G nothing keeps | COVERED |
| AC-8.1 | G ephemeral only; every F | COVERED |
| AC-8.2 | F subcommands (4) | COVERED |
| AC-8.3 | F records (3); F fixture | COVERED |
| AC-8.4 | F graphql | COVERED |
| AC-8.5 | F request forms (2); G uncalled forms | COVERED |
| AC-8.6 | G uncalled forms | COVERED |
| AC-8.7 | G ephemeral only | COVERED |
| AC-9.1 | G setup note | COVERED |
| AC-9.2 | G map; B | COVERED |
| UB-1 | W, S, G in `verify` on doubles; fake-host suites unedited | COVERED |
| UB-2 | S sentinel | COVERED |
| UB-3 | C, A, K, V, P unedited; W without marker | COVERED |
| UB-4 | H unedited (the defaults; H has no `SubprocessGitRunner` test); L one expectation extended; the `forge` job (all six defaults, `helper` included, on github.com); the restated text adds no oracle | COVERED |
| UB-5 | I; the PR diff | COVERED |

37 COVERED, 0 GAP.

CLEAN (0 A, 0 B; 1 C) — TEST-READY
