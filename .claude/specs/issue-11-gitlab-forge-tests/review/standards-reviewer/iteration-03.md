# Standards review — iteration 03 (delta: 5e04f25..0438e71)

No finding. Each fix site was checked against the project rules and the code it extends:

- B1 (iteration 02): D1's `ephemeral_project` now makes the one-keyword call `refuse_distributed_run(worker_id=worker_id)`.
  `test/test_forge_suite_layout.py` `passes_own_worker_id` accepts exactly that call: no positional argument, one
  keyword, `worker_id=worker_id`. `called_name` matches an attribute call on the loaded module as well as a bare name,
  so G's `session_fixture_problems` passes on the fixture D1 specifies. The forwarding function in
  `test/forge_gitlab/ephemeral.py` passes `command=GITLAB_FORGE_COMMAND` to the reused one. It follows the pattern this
  design already uses for `product_wrapper()`. D10's `test/forge_gitlab/ephemeral.py` row lists it, and AC-1.1's S and
  G rows name it.
- B2 (iteration 02): design.md `## Residuals` now has eight lines, within `proportionality.md`'s ten-line cap.
  requirements.md's Residuals did not change. Each of the two items that moved out is now a findings-ledger row:
  - Each row is one line, 223 B and 226 B, within `memory_compile.py` `LEDGER_ROW_MAX_BYTES = 240`.
  - Each row has the tool's six cells, with status `open`.
  - Each row is a pointer that resolves to a real finding: `review/devops-iac-reviewer/iteration-01.md` C4 and
    `review/security-reviewer/iteration-01.md` C3.
  - Both rows were committed in 0438e71 together with the spec change, not as a ledger-only change
    (`issue-filing-discipline.md`).
- C1 (iteration 02): the D10 bullet now describes `helper` as the callable that `run` calls as
  `helper(clone=self.clone)`. That matches today's `SubprocessGitRunner.run`, which calls
  `credential_helper_arguments(clone=self.clone)` only when `authenticated`. It also matches the D10 row's default.
  The other three keywords bound by `functools.partial` are D3's `helper_key=`, `username=` and `credential_file=`.
  - `functools` is standard library (`tech-stack.md`), and `test/test_github_wrapper_contract.py` already uses
    `functools.partial`.
  - `partial`'s function argument is positional-only, so coding-standards rule 4 cannot apply to it.
  - No forge layout test checks import allow-lists or positional calls.
- C2 (iteration 02): requirements.md UB-4 and design.md's D10 row now say the same thing. Both cover today's values as
  defaults, their use in the six bodies, and the docstrings. The Correctness Properties UB-4 row says "as D10's row
  says". This rewording only restates the criterion and adds no requirement (`proportionality.md` Scope freeze).
- D1 (iteration 02): the D10 row now says the refusal messages keep #10's words.
- The AC-4.1 W example now names `src/payload/test/gitlab_wrapper_fixtures.py` `write_config(*, root, config)`, which
  exists. It reuses that fixture instead of duplicating it.
- The D5 "Concurrency" bullet matches `.github/workflows/ci.yml`: `group: ci-${{ github.ref }}` and
  `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`.
- Tier M caps (decision-log DL-001): `design.md` is 59,934 B (cap 60,000) and `requirements.md` is 18,884 B
  (cap 20,000).

CLEAN

Counts: A 0, B 0, C 0, D 0

Verdict: READY
