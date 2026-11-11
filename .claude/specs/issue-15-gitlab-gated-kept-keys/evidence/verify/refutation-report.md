# Refutation report: issue #15 (the kept keys), PR #67, head b4d11ac

The verifier procedure, run once. Every mutant ran in a detached worktree `tmp/verify-mutants` at b4d11ac, since
removed. Each mutant capture starts with that mutant's `git diff`, then the complete `scripts/run_tests.py` output.
F, K, C, N, V and P are the test files change.md names.

| # | Claim | Command (mutation; tests run) | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the tree's SHA | `github_wrapper.py get-run`, `wait-run 43109048909`, `get-jobs` | FAILED-TO-REFUTE: completed/success; head_sha b4d11ac = tree HEAD = origin branch; jobs types, tests, security, lint, report all success | full-suite.txt |
| 2 | Wave 1's tests need the wave's code | call.py, the 8 family modules, gitlab_wrapper.py checked out from origin/main; 8 F + K | FAILED-TO-REFUTE: 49 failed, 361 passed; the 49 are the red capture's 49 node ids | mutant-wave-1.txt |
| 3 | AC-3: each W ID refused before any request | the 22 new `None` entries deleted; 7 F + K + N | FAILED-TO-REFUTE: 22 failed, every `test_a_writing_record_is_refused` case of the 7 families, each `exits 2, got 0` | mutant-gate-dropped.txt |
| 4 | AC-3: the refusal says no subcommand sends it | the 22 entries mapped to `mr merge`; 7 F + K | FAILED-TO-REFUTE: the same 22 cases fail on the message assertion (logged "use the mr merge subcommand") | mutant-gate-subcommand.txt |
| 5 | AC-2: every PENDING empty | one kept key put back on each of the 8 families' PENDING; 8 F + V | FAILED-TO-REFUTE: 8 failed, each family's `test_nothing_is_pending` | mutant-pending-restored.txt |
| 6 | AC-1: Kind | trigger-a-flow `additional_context` (ARRAY_OF_HASHES), `agent_privileges` (ARRAY); create `actions`, `ids` (ARRAY); local archive `override_params` (HASH); import-project-resources `file` (FILE); package `container_expiration_policy_attributes` (HASH), each made SCALAR; 4 F + N | FAILED-TO-REFUTE: 4 `test_every_param_is_typed_as_its_row` fail, naming all 7 | mutant-kinds.txt |
| 7 | AC-1: required | clone `to_project_id`, MR note `body`, ref-name download `job`, branch `ref`, remote archive `url` made optional; trigger-a-flow `goal` made required; 5 F + N | FAILED-TO-REFUTE: plan's required test and 4 typed tests fail, naming all 6 | mutant-required.txt |
| 8 | AC-1: method and path | rebase PUT to POST, merge-train POST to PUT; branch, `/projects/:id/`, clone, restart, import-relation paths altered; 7 F + N + V | FAILED-TO-REFUTE: 13 failed; one F test per family, N and both V tests name all 7 | mutant-method-path.txt |
| 9 | AC-1: Param names and locations (as N reads them) | clone `with_notes` renamed; delete-file `branch` to BODY; rebase `skip_ci` to QUERY; merge-train `squash`, local archive `namespace_path`, package `mirror` dropped; 6 F + N | FAILED-TO-REFUTE: N `test_every_record_matches_its_reference_section` names all 6; verify F too | mutant-param-name-location.txt |
| 10 | AC-1: the other seven create writers | cherry-pick `dry_run`, submodule `commit_message`, mirror-pull `force`, create-file `encoding` dropped; changelog `from` renamed; update-file `last_commit_id` to QUERY; revert `branch` optional; create F + N | FAILED-TO-REFUTE: N names the 6 row changes, create F the revert's required | mutant-create-remaining.txt |
| 11 | AC-1: Paging.NONE | one new record per family made OFFSET; 8 F + N | FAILED-TO-REFUTE: 11 failed: every family's paging test (plan: `test_every_list_record_has_a_case`), plus the orbit and job-id glob sends | mutant-paging.txt |
| 12 | AC-1, AC-4: the reads declare only their rows | orbit read and ref-name download given a `ref` query Param; orbit + verify F + N | FAILED-TO-REFUTE: both N tests name both records; verify F `RECORD_PARAMS` fails. Orbit F alone passes: change.md Tests assign Param names to N | mutant-reads-param.txt |
| 13 | AC-4: the glob keeps its `/` | orbit `*path` to `:path`, job-id `*artifact_path` to `:artifact_path`; orbit + verify F + N + V | FAILED-TO-REFUTE: 10 failed, all 4 orbit glob cases and the job-id send among them | mutant-reads-path.txt |
| 14 | AC-4: a `..` part is refused | `registry._glob` refuses `REFUSED_SEGMENTS - {".."}`; orbit + verify F | FAILED-TO-REFUTE: only `glob-part-dot-dot-refused` fails (exit 1 expected, got 0) | mutant-glob-dot-dot-allowed.txt |
| 15 | AC-4: an empty part is refused | same, `- {""}` | FAILED-TO-REFUTE: only `glob-part-empty-refused` fails | mutant-glob-empty-allowed.txt |
| 16 | Restored; UB-1 to UB-4 green | restored worktree; 8 F, K, C, `test_gitlab_api_graphql_only.py`, `test_wrapper_delivery.py`, N, V, P | FAILED-TO-REFUTE: 582 passed | restored-green.txt |

## Vacuity scan (step 3)

- The added test lines hold no skip, xfail, importorskip, mark other than parametrize, deselect or commented-out
  test; no pytest configuration file is in the diff.
- Removed: seven `test_only_the_kept_keys_are_pending` and package's `test_nothing_is_pending_but_the_kept_keys`,
  each replaced by `test_nothing_is_pending` (Files); K's `only-on-a-pending-list` case (Files). Row 5 kills every
  replacement.
- The one early return (orbit's glob test, sent cases) follows its exit-code and request assertions; rows 2 and 13
  kill those cases.
- Each AC-3 test scripts an answer before its call; row 3 proves each W argv complete: without the gate every one
  exits 0 and sends its request.

FAILED-TO-REFUTE.

## Red for the right reason (step 4)

`evidence/red/wave-1.txt`: 49 failed, 353 passed, no collection or load error. Every failure is an
`AssertionError` or a `Failed:` (plan's `ValueError` re-raised as `AssertionError` by `looked_up`); AC-3's lookups find
no record and AC-4's calls exit 2, as change.md's Red line states. Row 2 reproduces it. FAILED-TO-REFUTE.

## Coverage of the change (step 5)

Executable changed lines: call.py's import and 22 entries, the 22 `OP_` constants (rows 3, 4); the 25 records,
each with at least one field mutant killed (rows 6 to 13); the 8 `PENDING` lines (row 5). Every other changed line is
a docstring, a comment or gitlab_wrapper.py's usage text, none executable. FAILED-TO-REFUTE.

## Scope checks

- UB-4: `git diff --name-only origin/main...HEAD` names no `github_wrapper.py`, `github_api/` or GitHub test;
  `test_wrapper_delivery.py` passed (row 16 and CI).
- Files' "No other file": the diff is the Files list plus this spec directory.
- `gitlab_wrapper.py`: one hunk, the REST `call` entry; the GraphQL entry is unchanged context.
- Every module of `gitlab_api/families/` has `PENDING ... = frozenset()`.
- Observation, no criterion: the ledger closes the six open rows with eight `enforced` rows, one per F path, where
  Files reads one row per open row; each open row is closed.

## Tree

The mutant worktree is removed (`git worktree list`), `tmp/` is removed, HEAD is b4d11ac with no diff, and
`git status --porcelain` lists only `evidence/verify/`.

Refuted ids: none.

Verdict: VERIFIED
