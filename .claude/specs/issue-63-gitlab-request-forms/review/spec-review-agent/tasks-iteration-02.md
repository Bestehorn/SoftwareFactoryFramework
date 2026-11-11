# Tasks review — iteration 02 (delta) — lane spec-review-agent

Reviewed: `tasks.md` at c7a4958 (14,938 B, cap 15,000 B), read whole, against this lane's and the test lane's
iteration-01 findings, `design.md` D4, D12 and § Correctness Properties, and the frozen `requirements.md`.

## Iteration-01 findings

| Finding | Fix site | Status |
|---|---|---|
| SRA B1: AC-8.3 in no TEST task | `Validates:` of 2.2, 2.3, 2.4, 2.5 and 2.6 each ends with AC-8.3 (2.5 before UB-2) | RESOLVED |
| SRA C1: 1.1's registry test green on the base | 1.1: "(its record built with `token_scope`)" | RESOLVED |
| SRA C2: 2.1's "built" record | 2.1: "the declared records of the IDs whose sections or paths its oracle names, a "built" record a `dataclasses.replace` of one" | RESOLVED |
| SRA C3: AC-1.4 in no `Validates:` | F.3 validates AC-1.4; row AC-1.4 "2.3 to 2.6, F.3; V's two tests it names" | RESOLVED |
| SRA D1: G's red reason | preamble lists `AttributeError`, `TypeError` only; 1.4 names "the import helper's `AssertionError` or `ModuleNotFoundError`", and both are raised in the body | RESOLVED |
| TA B1: AC-5.3 coded in wave 1, tested in wave 2 | 1.7 drops the token clause and AC-5.3; 1.8 reads "on the answers they expect", Validates AC-5.2, UB-2; new 2.12 owns AC-5.3 in `container_registry.py` and `transport.py`, paired with 2.5 in the same wave | RESOLVED |
| TA B2: wave 3's Run line misses the graphql pins | wave 3 Run holds `src/payload/test/test_gitlab_*.py test/test_gitlab_*.py`, which match `test_gitlab_api_graphql_only.py` and `test_gitlab_graphql_contract.py` | RESOLVED |
| TA C1: AC-1.4 in no `Validates:` | 2.3, 2.4, 2.5 and 2.6 each validate AC-1.4 | RESOLVED |
| TA D1: 2.2's red for accepted calls | 2.2: "each refusal fails on its standard-error or log assertion and each accepted call on its exit code" | RESOLVED |

## Delta checks, no finding

- Cap: 14,938 B, 62 B under the cap.
- 2.12's files. `container_registry.py` and `transport.py` belong to no other wave-2 task. The other IMPL tasks own the
  eleven family modules (2.7 to 2.10) and `commands/call.py` (2.11). The TEST tasks own N, K and the F: suites. Wave 1
  edits both files in 1.7 and 1.8, which is an earlier wave.
- 2.12 against D12. AC-5.3's checks sit in the steps D12 gives each file: steps 1 and 2 in `container_registry.send`,
  and step 3's answer refusal in `container_registry_token`. D4 § AC-5.3 and the paragraph on the registry token are
  the text 2.12 cites. No new symbol is added.
- Wave 1 stays green without AC-5.3. Each wave-1 oracle that reaches the registry path uses the scripted answers
  each step expects:
  - G's job-token login;
  - T's registry URLs and headers, and `_send`'s `destination` refusal (D4, still in 1.7);
  - R's `ValueError` for a record sent without `project`.
  None of them needs a step-1 to step-3 failure or the token-in-no-log property. No `CONTAINER_REGISTRY` record exists
  until 2.9, so `call` cannot reach the unchecked steps between the wave-1 and wave-2 commits.
- Pairing. 2.5 validates AC-5.3 and UB-2. Its red is an assertion on the base: exit 2 for an ID no record declares,
  where 1 is expected. It precedes 2.12 in wave 2. AC-5.2's 404-at-step-4 log oracle is also 2.5's, so it is green
  only after 2.12, in the same wave.
- Coverage. The table has all 30 criteria of `requirements.md`, AC-1.1 to AC-9.2 and UB-1 to UB-4. Every TEST or
  VERIFY task a row names lists that criterion in its `Validates:`. AC-5.3's row is 2.5, and no IMPL task other than
  2.12 validates AC-5.3.
- Wave 3's Run files exist on this branch: `test/test_instruction_corpus_budget.py`, `test_toolchain_manifest.py`,
  `test_layout.py`. Row UB-1's "the existing suites on every Run line" now holds for wave 3.

CLEAN
Verdict: READY
