# Test-architect review — tasks, iteration 02 (delta)

## Findings

### C1 — 2.4 calls `registry.graphql_call`, which 2.5 writes in the same wave
Severity: C
Location: tasks.md § Wave 2, task 2.4
Defect: After B1's move, the `cmd_call` branch of 2.4 calls `registry.graphql_call`, and no earlier wave writes it. 2.5
  writes it in the same wave, while `parallel-by-default.md` says a wave's tasks "depend only on earlier waves". The
  dependency is only on an interface, which D3 and 2.5 both state. G cannot go green until 2.3, 2.4 and 2.5 are all
  in, just as iteration 01's G needed 2.3 and 2.4 together. Wave 2's single green run judges the three together, so the
  order cannot produce wrong behaviour. The risk: 2.4's implementer finds no `graphql_call` on the wave-1 commit and
  adds one to `registry.py`, a file 2.5 owns.
Material-because: not material. The edit restates the ownership that already holds.
Proposed-edit: In 2.4, replace "then `print_json(value=registry.graphql_call(...))`" with "then
  `print_json(value=registry.graphql_call(...))`, the function 2.5 writes in this wave with D3's signature (2.4 does
  not edit `registry.py`)".

## Fix sites

- B1, applied.
  - 1.3 no longer names `graphql_call`. Its Validates is AC-1.4, AC-2.5, which wave 1's 1.2 (V) and 1.1 (R) test.
  - 2.5 carries the removed text verbatim: Files `registry.py`, Validates AC-2.1, AC-2.2, AC-2.3. Its tests (G, 2.2)
    come before it in wave 2.
  - Wave 2's files are disjoint: Q, G, `graphql_only.py`, `call.py`, `registry.py`.
  - R is on wave 2's Run line, which guards "nothing else of the module changes".
  - D8's `registry.py` row already lists `graphql_call`.
  - `Transport.graphql` and `Transport.graphql_nodes` exist in `transport.py`, which F.3 holds unchanged.
  - G's red reason holds. After wave 1, `call` has no GraphQL branch, so `registry.lookup` refuses every `graphql/` ID,
    with or without 2.5.
- B2, applied.
  - Wave 2's Run line names `test_github_api_git.py` and `test_github_api_repos.py`. On `origin/main` (`3beba95`), both
    hold `test_a_branch_writing_record_is_refused`.
  - Each trunk `GATED_OPERATIONS` ID is named in K, the git suite or the repos suite, and all three are on wave 2's Run
    line: `pulls/merge`, `pulls/merge-async`, `issues/create`, the five `repos/*` IDs, `git/create-ref` and
    `git/update-ref`.
- My C1, applied. 2.2 names `json.dumps(sort_keys=True)`, which matches design § Correctness Properties AC-2.1.
- My D1, applied. 2.1's Red line admits `registry.graphql_lookup`'s `ValueError` raised inside the test body.
- Spec lane C2, applied in 2.2 and in design AC-3.2, and its oracle can fail.
  - The trunk's `refuse_gated` appends `SENDS_IT` (", which sends it") unless the ID is in `GATED_NOT_SENT`. If 2.4
    leaves out its entry, `test_a_refused_mutation_sends_nothing` fails.
  - At red, the unknown-ID message lacks `merge-pr`, so the test is still red on an assertion.
  - It mirrors K's `pulls-merge-async-is-merge-pr` case (`lacking(text=SENDS_IT)`).
- Spec lane C1, C3 and D1, applied in D5, D8, Residuals, F.3 and 2.4. None of them changes an oracle, a Run line or a
  task's files.
- The trunk tip moved from `fe79965` to `3beba95` (#31, #41).
  - Since then, of the D8 files and the Run-line suites, only `docs/forLLMConsumption.md` changed.
  - Neither the trunk map nor the trunk entry script holds `call graphql/`, so 3.1 and 3.2 are still red at their red
    run.
- Test-first order holds in every wave (1.1, 1.2 → 1.3; 2.1, 2.2 → 2.3, 2.4, 2.5; 3.1, 3.2 → 3.3, 3.4).
- The Coverage table still lists all 21 criteria of `requirements.md`.

## Coverage

| Criterion | TEST / VERIFY task(s) | Wave | Status |
|---|---|---|---|
| AC-1.1 | 2.1 (Q `test_every_record_matches_the_reference`); design inspection | 2 | COVERED |
| AC-1.2 | 2.1; V `…covered_or_pending`, `…its_own_ids` (W2 Run) | 2 | COVERED |
| AC-1.3 | 2.1 | 2 | COVERED |
| AC-1.4 | 1.2 | 1 | COVERED |
| AC-1.5 | 1.2; V's two tests (W2 Run) | 1, 2 | COVERED |
| AC-2.1 | 2.2 (impl 2.4, 2.5); H (W2 Run) | 2 | COVERED |
| AC-2.2 | 2.2 (impl 2.5) | 2 | COVERED |
| AC-2.3 | 2.2 (impl 2.5) | 2 | COVERED |
| AC-2.4 | 2.2 | 2 | COVERED |
| AC-2.5 | 1.1, 2.2 | 1, 2 | COVERED |
| AC-2.6 | 2.2 | 2 | COVERED |
| AC-3.1 | 2.1, 2.2 | 2 | COVERED |
| AC-3.2 | 2.2 (`merge-pr`, no "which sends it") | 2 | COVERED |
| AC-3.3 | 2.2 | 2 | COVERED |
| AC-4.1 | 3.1 | 3 | COVERED |
| AC-4.2 | 3.2, F.4 | 3 | COVERED |
| UB-1.1 | F.3; C, P on every Run line | all | COVERED |
| UB-1.2 | F.3; K, R (W1, W2), N, git and repos suites (W2) | 1, 2 | COVERED |
| UB-2.1 | F.3; C on every Run line | all | COVERED |
| UB-2.2 | F.3; V on every Run line | all | COVERED |
| UB-3.1 | F.2; `test_wrapper_delivery.py` on every Run line | all | COVERED |

21 COVERED, 0 GAP. TEST-READY.

Verdict: CLEAN
