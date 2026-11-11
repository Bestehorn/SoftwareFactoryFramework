# Refutation report: issue #14, the last three GitHub pending operations (tier S, one wave)

Tree: worktree `.claude/worktrees/issue-14`, branch `issue-14-github-empty-pending-list`, PR #64, merge base 7ec47d1.
HEAD cf17ede4214049dbdce4c278e31407cb060a2e3c  # pragma: allowlist secret
CI was read through `scripts/github_wrapper.py` from the main checkout. Local runs: `scripts/run_tests.py -p
no:cacheprovider --color=no <files>` in the worktree. Paired set (133 tests): F (pulls, code_scanning, copilot), K, R,
N, V. Each mutant capture holds its `git diff` and the complete pytest output.

## The five steps

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Suite green on this SHA | `wait-run 43023154117`, `get-jobs 43023154117` | FAILED-TO-REFUTE: completed/success, head_sha = HEAD, 5 of 5 jobs success | full-suite.txt |
| S2 | The wave is what its tests demand | the 5 IMPL files reset to 7ec47d1; paired set | FAILED-TO-REFUTE: 10 failed, 123 passed: the 10 tests of red/wave-1.txt | mutant-wave-1.txt |
| S2t | Each criterion is pinned | 16 targeted mutants, table below | REFUTED: R4 (AC-1) and Q6 (UB-3) survive | mutant-*.txt |
| S3 | No vacuous test | Grep of the 4 changed test files; `def test_` lines of the diff | FAILED-TO-REFUTE: no skip, xfail, importorskip, deselect; only `parametrize` marks (one-row `BRANCH_WRITING_CALLS` ran: G2); removed pending tests and K's `pending-id` row replaced per change.md Files, DL-004; IDs, paths, body names, argv are literals; `registry.lookup(...) ==` the record is an identity check | grep |
| S4 | Red fails for the right reason | Grep of red/wave-1.txt | FAILED-TO-REFUTE: 10 failed, 10 `E   AssertionError`, 0 collection or import errors; S2 reproduces the same 10 | red/wave-1.txt |
| S5 | Every changed line is pinned | diff hunks against the mutants | REFUTED (AC-1): commit-autofix's new `item_key=None` line and both gated records' `content_type` default (R4); every other executable hunk is killed below; the rest is docstrings, comments, ledger rows | mutant-record-unnamed-fields.txt |
| G | Green before and after | paired set at HEAD; then the 10 files of green/wave-1.txt after every restore | 133 passed; 641 passed, exit 0 | baseline-green.txt, green-after-restore.txt |

## Mutants

| Id | Criterion | Mutation | Result | Killed by | Capture (mutant-) |
|---|---|---|---|---|---|
| G1 | AC-3 | `pulls/update-branch` gate entry removed | KILLED, 1 failed | pulls F `test_a_branch_writing_record_is_refused` (the PUT was sent) | gate-pulls |
| G2 | AC-3 | `code-scanning/commit-autofix` gate entry removed | KILLED, 1 | code_scanning F refusal (the POST was sent) | gate-autofix |
| G3 | AC-3 | both entries map to `"merge-pr"` | KILLED, 2 | both F refusal tests: no "no subcommand sends" log | gate-names-a-subcommand |
| B1 | AC-4 | `_undocumented` body line reverted | KILLED, 1 | copilot F `test_the_content_exclusion_map_is_sent_as_given` (exit 2) | call-any-body-reverted |
| B2 | AC-4 | `_check_names` `*` return removed | KILLED, 1 | same test (`registry.send` raises) | registry-any-body-reverted |
| P1 | AC-2 | each ID back on its `PENDING` | KILLED, 4 | three F `test_nothing_is_pending`; V `test_one_module_per_family_holding_only_its_own_ids` | pending-restored |
| R1 | AC-1 | PUT->POST; path loses `/commits`; PUT->PATCH | KILLED, 4 (re-run) | N `test_every_record_matches_its_reference_section` (3 named), V, N send, copilot F map | record-method-path |
| R2 | AC-1 | body `{}`; loses `message`; `{"octo-repo"}` | KILLED, 3 | N match (3 named), N send, copilot F map | record-body-names |
| R3 | AC-1 | paging LINK (pulls); multi_segment, accept (code_scanning); item_key, content_type (copilot) | KILLED, 6 | pulls F transcription; code_scanning F version/media type, multi-segment; copilot F transcription, map; N send | record-fixed-fields |
| R4 | AC-1 | `item_key="items"` on commit-autofix; `content_type` set on both gated records | **SURVIVED, 133 passed** | none | record-unnamed-fields |
| U1 | UB-3 | call: every record takes any body name | KILLED, 2 | K `test_an_undocumented_parameter_is_refused` (body-name, one-of-each-kind) | call-any-body-for-every-record |
| U2 | UB-3 | registry: every body name accepted | KILLED, 2 (+2 teardown errors of the same tests: unrouted request) | R `test_call_refuses_an_undocumented_parameter` (undocumented-body-name, query-name-sent-as-body) | registry-any-body-for-every-record |
| Q2 | UB-3 | call: the `*` record skips path and query names | KILLED, 1 | copilot F `test_the_content_exclusion_call_checks_its_query` | call-any-body-skips-path-and-query |
| Q6 | UB-3 | registry guard becomes `ANY_BODY_NAME in operation.body_params` (every kind) | **SURVIVED, 133 passed** | none | registry-any-body-skips-query |
| Q1 | UB-3 | registry guard without `kind == KIND_BODY and` | equivalent, 133 passed: a query's `documented` is `query_params`, and the only `"*"` of any family is copilot's `body_params` | none | registry-kind-guard-dropped |
| Q4 | probe | call: the `*` record skips path names (a line not in the diff) | survived, 133 passed; not graded | none | call-any-body-skips-path |

## Refutations

REF-1 (UB-3). UB-3: "`call` and `registry.send` SHALL CONTINUE TO refuse before any request ... an undocumented path
or query name ... of any record." Q6 rewrites the condition of the line this diff adds to `registry._check_names`;
`registry.send` and `registry.pages` then send an undocumented query name of
`copilot/set-copilot-content-exclusion-for-organization`, and all 133 paired tests pass. `call` still refuses it
(`check_call` runs first), and R's cases run a synthetic family with no `*` record, so no test reaches the registry's
query check of the `*` record. What pins it: `registry.send` for that record with an undocumented query name raises
`ValueError` and sends nothing.

REF-2 (AC-1). AC-1: each record "with ... `item_key` `None` ... and `content_type` `None`". R4 sets `item_key` on
`code-scanning/commit-autofix` and `content_type` on it and on `pulls/update-branch`: 133 passed. Grep: no GitHub test
reads a family record's `.content_type` but R's `issues/update` check, and code_scanning F reads no `Paging.NONE`
record's `item_key`. What pins it: code_scanning F asserts both `None` for commit-autofix, pulls F `content_type`.

Observation, not graded: under Q4 `call` sends an undocumented `--path` name of the `*` record, every test green; the
`path =` line of `_undocumented` is outside the diff. A copilot F case with such a name pins it beside REF-1.

## Unchanged behaviour

| Id | Command | Result |
|---|---|---|
| UB-1 | C, P in run G | FAILED-TO-REFUTE: green |
| UB-2 | K gated and unknown-ID cases in every paired run; G1-G3 | FAILED-TO-REFUTE |
| UB-3 | U1, U2, Q2 killed; Q6 survived | REFUTED (REF-1) |
| UB-4 | V `test_the_wrapper_imports_only_the_standard_library` in every paired run; no shipped import added | FAILED-TO-REFUTE |
| UB-5 | `git diff --name-only 7ec47d1 HEAD`: 18 files, neither `gitlab_wrapper.py` nor `src/payload/test/test_wrapper_delivery.py`; delivery green in G | FAILED-TO-REFUTE |

## Interference and re-runs

The orchestrator ran `git merge --no-commit origin/main` and `git merge --abort` in this worktree between 13:25:40Z
and 13:27:00Z (its notice; reflog `reset: moving to HEAD`). Only R1's first run overlapped (finished 13:26:22Z): it was
discarded and R1 re-run on a clean tree, 13:27:57Z to 13:30:22Z, `git status` captured before and after. Every other
run ended before 13:25:40Z (P1 at 13:23:36Z) or began after 13:27:00Z.

## Tree restored

`git checkout --` restored each mutated file after its run. The five implementation files' sha256 equal the values
recorded before the first mutant (green-after-restore.txt). `git status --porcelain` shows only
`?? .claude/specs/issue-14-github-empty-pending-list/evidence/verify/`. No tmp/ file, no `.kiro/` path, no commit.

Refuted ids: REF-1 (UB-3), REF-2 (AC-1)
Verdict: REFUTED
REFUTED UB-3 AC-1
