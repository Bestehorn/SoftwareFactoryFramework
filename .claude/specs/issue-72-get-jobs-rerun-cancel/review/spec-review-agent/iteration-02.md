# Combined review, iteration 02 (delta 0fc6c3b..654d9f3): issue-72-get-jobs-rerun-cancel (tier S, all six lenses)

### C1 — AC-2's attempt condition is tested only together with the flag
Severity: C
Location: change.md § Tests, the AC-2 line
Defect: No case lists jobs of more than one `run_attempt` without `--all-attempts`. A product that prints the suffix only when `--all-attempts` is given AND the page has more than one distinct attempt therefore passes `all-attempts` (suffix), `every-column` (none) and `latest-attempt` (none), against AC-2's WHEN, which names only the page's attempts (the copy's `cmd_get_jobs`: `show_attempt = len({job.get(FIELD_RUN_ATTEMPT) ...}) > 1`). Also, "`success` completed" does not say the job has both timestamps. Without them, `failed-only`'s TOTAL is the same whether or not the `success` job is counted.
Proposed-edit: in the AC-2 line, "`get-jobs/exit-0/failed-only` with `--timing` (`success` completed," → "`get-jobs/exit-0/failed-only` with `--timing` on jobs of two attempts (`success` billed," and "the suffix in `all-attempts`, none in `every-column`" → "the suffix there and in `all-attempts`, none in `every-column`". To stay under the cap, delete "(`ListFailureRouteSpec` or an error `Reply`) " from the AC-6 line. The fixtures' existing exit-1 rows already show both forms.

## Fix sites

- B1: applied. `Route.matches` compares the whole decoded query, so a `StaticRouteSpec` pins `per_page=100` and `filter=latest|all`, as in the copy's `cmd_get_jobs` path. If the reply carries a `link` to page 2 and the product requests it, that request has no route and `pytest.fail` stops the test. So `registry.call`, which sends once, passes, and `registry.pages`, which follows the link, fails. `every-column` (`--all-attempts`, one attempt) splits the suffix from the flag. `[wall=? billed=?]` now prints, because `every-column` has no `--failed-only`. The `failed-only` TOTAL is pinned, with C1's timestamp caveat.
- B2: applied. `test_the_usage_names_the_ci_commands` is a new name, with no collision in `src/payload/test/`. It follows `test_the_usage_names_the_operation_call`. The product `__doc__` has no `get-jobs` line, so it is red before T3. The compat file is in T1 `Files:`.
- B3: applied. The two `get-jobs <run-id> --steps` sites are `docs/ci-capacity-ladder.md` Rung 0 and `prompts/setup-kiro.txt`'s ladder, and no other tracked text has them. `--show-runner` adds the copy's `[runner=… labels=…]`, which the shape (B)/(C) table needs.
- C1–C3: applied. T1's red/green split matches the parser: an unknown name exits 2 with no request. The CLAUDE.md clause matches the product docstring ("added as a module of `github_api/commands/` that defines `register(subparsers)`"). The UB-4 GitLab half is now handled as checked on the diff.
- C4: applied. 7,979 B against the 8,000 B cap; § Files points at the Tasks' `Files:` lists, which name all nine files.
- D1: applied. `rerun` and `cancel` take `run_id` as `int` in the copy's `add_parser` rows.
- D2: applied. The docstrings of fixtures, compat and fork parity all still name the installed fork; § Files names all three.
- No criterion was added: the ids are still AC-1..AC-8 and UB-1..UB-4. The AC-7 and AC-8 edits restate the oracle source, which is the preamble's "the copy", correct the ladder flags and say what replaces the stale CLAUDE.md clause.
- The oracle holds. `git diff v2026.11.10.1 c2d86cd~1 -- scripts/github_wrapper.py` is empty. The fixtures and parity file last changed on 2026-11-11, while the chess copy was installed, so every existing `FORK_CASES` row passed on the tag's file (UB-1).

## Lenses without a finding

Security: the delta touches no auth, secret or input path. Best practice: the four records match `families/actions.py` (`re-run-workflow` lists `enable_debug_logging`, and AC-4's "no body" sends none). Standards: CLAUDE.md is not in `config/toolchain.json`, so T4 edits no installed file (UB-3). DevOps: unchanged.

## Coverage
| Criterion | Named test | Finding | Row |
|---|---|---|---|
| AC-1 | latest-attempt, all-attempts (`StaticRouteSpec`, next-page `link`) | `per_page`, `filter`, one request, `None`, widths pinned | OK |
| AC-2 | failed-only, all-attempts, every-column | the filter is pinned; the attempt-only path is untested (C1) | OK |
| AC-3 | every-column, failed-only TOTAL | suffix order, `?` timing, `(none)`/`-`, step lines, TOTAL | OK |
| AC-4 | rerun whole-run, failed-only | the POST path and the absent body pinned (`NonGetRequest`) | OK |
| AC-5 | cancel requested | the same | OK |
| AC-6 | exit-1 rows, `_refusal_cases` | exit-1 red first; refusals already exit 2 (T1) | OK |
| AC-7 | parser rows, parity on the tag, `test_the_usage_names_the_ci_commands` | usage now pinned | OK |
| AC-8 | the diff | prose | OK |
| UB-1 | existing `CASES` and parser rows on the tag's copy | | OK |
| UB-2 | `test_the_wrapper_imports_only_the_standard_library` | | OK |
| UB-3 | `test_an_installed_file_equals_its_source_at_the_release` | | OK |
| UB-4 | the copy-step tests; GitLab half on the diff | | OK |

CLEAN
Coverage: TEST-READY
Counts: A 0, B 0, C 1, D 0
Verdict: READY
