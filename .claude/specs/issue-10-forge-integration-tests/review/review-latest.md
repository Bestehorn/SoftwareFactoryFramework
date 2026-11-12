# Review — tasks iteration 01 (consolidated)

The design was approved at design iteration 03 (all six lanes CLEAN, test-architect TEST-READY 35 of 35).

Tasks lanes on commit 1b17919: test-architect CLEAN, TEST-READY (35 of 35, no GAP); spec-review-agent NOT-CLEAN
(0 A, 2 B). Combined A+B: 2. Nothing rejected.

## A/B (apply as the lane file proposes)

| Id | Lane | Defect | Fix |
|---|---|---|---|
| B1 | spec-review B1 | S imports `test/forge/ephemeral.py` (and subclasses its runners) at module level, so waves 1 and 2 red runs fail on collection, which the RED step refuses | 1.3: S loads `ephemeral.py` by path inside each test body through a cached helper; nothing at S's module level names a symbol of it; the doubles of 2.1 and 3.1 and 4.2's load of `write_credential.py` are built the same way |
| B2 | spec-review B2 | wave 5 (and 4.3) has no red run the RED step accepts | move 5.1–5.4 into Wave 4 as 4.7–4.10; delete the Wave 5 heading and paragraph; the Runs paragraph and F.1 as the lane file proposes; delete 4.3's "Red:" sentence |

## C/D (apply in the same pass)

- test-architect C1: the layout file runs in the wave that writes the forge modules (B2 merges it into wave 4, whose runs include L).
- test-architect C2: no per-module red claim for the forge modules (resolved by B2's deletion; state nothing new).
- test-architect C3: 1.1 names `github_wrapper_fixtures.load_script`, not `load_wrapper` (a function of a test module, not importable under `--import-mode=importlib`).
- spec-review C1: 3.3 names `CHECKOUT`.
- spec-review C2: 4.6: `write_credential.py` loads `ephemeral.py` by path, as `conftest.py` does, and calls `write_test_credential`.
