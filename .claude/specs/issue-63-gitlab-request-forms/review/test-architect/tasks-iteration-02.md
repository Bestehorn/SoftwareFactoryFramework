# Test architect — tasks review, iteration 02 (delta)

Reviewed: `tasks.md` at c7a4958 (14,938 B, under the 15,000 B cap), against this lane's iteration 01, the spec lane's
iteration 01 B1, `design.md` D4, D12 and § Correctness Properties (AC-5.2, AC-5.3, AC-8.3), and the frozen
`requirements.md`. Only the fix sites and the coverage were reviewed.

## Iteration-01 findings

| Finding | Fix site in tasks.md | Status |
|---|---|---|
| TA B1: AC-5.3 coded in wave 1, tested only in wave 2 | 1.7 drops the token clause and AC-5.3. 1.8 reads "on the answers they expect" (Validates AC-5.2, UB-2). New 2.12 IMPL owns `container_registry.py` and `transport.py` for AC-5.3 (Validates AC-5.3, UB-2), after its TEST 2.5 in the same wave | RESOLVED |
| TA B2: wave 3's Run line left out the tests pinning the texts it edits | Wave 3 Run is now the proposed `run_tests.py` line. Its globs reach `test/test_gitlab_graphql_contract.py` and `src/payload/test/test_gitlab_api_graphql_only.py` | RESOLVED |
| TA C1: AC-1.4 in no Validates | AC-1.4 is in 2.3, 2.4, 2.5, 2.6 and F.3. Coverage row AC-1.4 names them | RESOLVED |
| TA D1: 2.2's red reason covered only refusals | 2.2: "each refusal fails on its standard-error or log assertion and each accepted call on its exit code" | RESOLVED |
| SR B1: AC-8.3 in no TEST Validates | AC-8.3 is in the Validates of 2.2, 2.3, 2.4, 2.5 and 2.6. Design § AC-8.3 has those examples assert method, URL, headers and body names, and each refusal assert exit code and nothing sent. The preamble binds each test to that oracle | RESOLVED |

## Checked at the fix sites, no new finding

- 2.12 is test-first. At wave 2's red, 2.5 `test_no_registry_token_sends_nothing_to_the_registry` fails on an
  assertion: the package records are missing, so the call exits 2 where the test expects 1. That is not a
  collection error. At green, the cases need 2.12's code, not just 2.9's records:
  - with prefix `""`, step 3 would be recorded beyond the steps the oracle allows;
  - with `/jwt/auth` answering `{}`, the token-field refusal is required;
  - with a `bearer` token, the D4 step-1 refusal is required.
  So the test can fail against a 2.9-only tree.
- Wave 1 stays green without the AC-5.3 code:
  - G (1.4) is the job-token happy path;
  - T (1.2) checks URLs, headers and the `destination` refusal, which is `_send`'s and stays in 1.7;
  - R's missing-`project` `ValueError` is `registry.send`'s, in 1.6.
  1.8 is now the minimal code for 1.4.
- 2.12's symbols are within D12's rows: `container_registry.py` covers `send` and D4's steps 1 and 2, and
  `transport.py` covers `container_registry_token`. The step-4 404 log check in AC-5.2's oracle (2.5) is met by
  `_send`'s reporting from 1.7.
- Disjoint files hold within each wave. In wave 2, 2.12 is the only task on `container_registry.py` and
  `transport.py`, and 2.7 to 2.11 own families and `call.py`.
- Each wave orders its TEST tasks before its IMPL tasks: 1.1–1.5 before 1.6–1.8, 2.1–2.6 before 2.7–2.12, and
  3.1–3.2 before 3.3–3.5.
- Every IMPL criterion has a TEST task validating it in the same wave. 2.12 is paired with 2.5 for AC-5.3 and UB-2.
- Wave 3's Run line covers the other readers of the edited texts:
  - The map's only `call graphql/` is in the `github_api` bullet, not the `gitlab_api/` bullet 3.4 edits, so
    `test/test_github_graphql_contract.py` `test_the_map_names_the_graphql_call` cannot be affected.
  - `test/test_toolchain_manifest.py` is on the line.
  - The ledger checks of `test/test_instruction_corpus_budget.py` cover 3.5's rows.

## Coverage

| Criterion | TEST / VERIFY tasks | Status |
|---|---|---|
| AC-1.1 | 2.3–2.6 | COVERED |
| AC-1.2 | 2.1, 2.3, 2.4, 2.6 | COVERED |
| AC-1.3 | 2.3–2.6; V | COVERED |
| AC-1.4 | 2.3–2.6, F.3; V | COVERED |
| AC-2.1 | 2.2, 2.3, 2.4 | COVERED |
| AC-2.2 | 1.1, 2.3 | COVERED |
| AC-2.3 | 2.3 | COVERED |
| AC-2.4 | 1.1, 1.3, 2.2 | COVERED |
| AC-3.1 | 1.1, 1.3, 2.3 | COVERED |
| AC-3.2 | 1.1, 1.3, 2.3 | COVERED |
| AC-3.3 | 2.2 | COVERED |
| AC-4.1 | 1.1, 2.3 | COVERED |
| AC-4.2 | 1.3, 2.2 | COVERED |
| AC-5.1 | 1.1, 1.2, 2.4 | COVERED |
| AC-5.2 | 1.1, 1.2, 1.4, 2.5 | COVERED |
| AC-5.3 | 2.5 (paired with 2.12) | COVERED |
| AC-6.1 | 2.1 | COVERED |
| AC-6.2 | 1.1, 1.2, 2.4, 2.6 | COVERED |
| AC-6.3 | 2.2 | COVERED |
| AC-7.1 | 2.2, 2.6 | COVERED |
| AC-7.2 | 2.1 | COVERED |
| AC-8.1 | 2.1, F.1 | COVERED |
| AC-8.2 | 2.1 | COVERED |
| AC-8.3 | 2.2–2.6, F.1 | COVERED |
| AC-9.1 | 2.2, 3.1 | COVERED |
| AC-9.2 | 3.2; `test_llm_map_within_cap` | COVERED |
| UB-1 | 1.1, 1.5, F.3; existing suites on all three Run lines | COVERED |
| UB-2 | 1.2, 2.5, F.3 | COVERED |
| UB-3 | 2.2, F.3 | COVERED |
| UB-4 | F.2 | COVERED |

Counts: 0 A, 0 B, 0 C, 0 D. All 5 iteration-01 findings are resolved. 30 criteria are COVERED and none is a GAP.

CLEAN

Verdict: READY
