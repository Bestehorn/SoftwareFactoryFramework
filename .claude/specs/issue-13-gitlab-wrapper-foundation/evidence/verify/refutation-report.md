# Refutation report — issue #13, PR #34

Scope: `git diff origin/main...HEAD`, base 7f2a1a9, worktree HEAD `c3efdcb2beaf1f1a6833ef6688033167c2b5e273` = PR head.
Tests ran only as `venv\Scripts\python.exe scripts/run_tests.py <paired tests>` from the worktree. Each mutant was
applied alone (unique anchor) by a scratch driver under `tmp/verify/` (deleted), then the original bytes were
restored and SHA-256-checked. T, R, C, V, P, S, D are design.md's test-module letters.

Wave commands (`run_tests.py` + the arguments; green after every restore):
- W1 `R P V::test_a_family_module_is_discovered_alone V::test_checker_names_each_unlisted_row` → 18 passed
- W2 `T R::test_call_refuses_an_undeclared_value P::test_standard_library_only` → 60 passed
- W3 `V::test_every_index_row_is_mapped_or_pending C::test_load_config_refusals C::test_delivery_verb_through_main
  C::test_script_usage_error_exits_2 C::test_script_loads_by_path D` → 40 passed
- W4 `C::` the seven 4.1 tests (subcommand forms, claim-check, start refusals, reopen, template, environment,
  no config) → 53 passed
- W5 `C::test_a_subcommand_form C::test_pipeline_wait_exit_codes S` → 44 passed
- RC `src/payload/test/test_run_checks.py` → 21 passed

## Claims

| Claim | Command | Result | Evidence |
|---|---|---|---|
| Whole suite green on c3efdcb | `github_wrapper.py get-pr-checks 34`; `get-run 42918925603` | FAILED-TO-REFUTE | head `c3efdcb2…`; `verify (lint/types/tests/security)` and `report` all `completed`/`success`; `combined_status: pending` with `statuses: []` (GitHub docs: "pending if there are no statuses"); run 42918925603 `ci` #31 `completed`/`success` |
| AC-1.1 | W1 1f, W2 2n | FAILED-TO-REFUTE | both killed: `test_lookup_refuses_unknown_and_duplicate_ids`, `test_call_refuses_an_undeclared_value` |
| AC-1.2, AC-5.2 | W1 1g (discover the first module only) | FAILED-TO-REFUTE | killed: `test_a_family_module_is_discovered_alone`, `test_checker_names_each_unlisted_row` |
| AC-1.3, UB-3 (F.2) | `git diff --name-only origin/main...HEAD \| grep -Ei "github\|test_wrapper_delivery"` | FAILED-TO-REFUTE | no match (exit 1); every added `gitlab_api/` file is a row of the D2 table; D green in W3 |
| AC-2.1 | W2 2l (JOB sent as PRIVATE-TOKEN) | FAILED-TO-REFUTE | 9 failed |
| AC-2.2 | W1 1a (`.`/`..`/empty accepted), 1b (`safe="/"`) | FAILED-TO-REFUTE | 3 failed; 6 failed incl. `test_path_value_is_one_segment` |
| AC-2.3 | W1 1c/1d/1e; y1 (`QUERY_SAFE=""`); W2 2q (form pairs sent as a JSON object) | **REFUTED** | 1c/1d/1e killed; y1 killed in C (`issue-list-assignee-username`, `pipeline-log`); **2q SURVIVED, `60 passed`**; transport.py `request_body` form branch never runs (coverage) |
| AC-2.4 | W2 2m (`"` not escaped) | FAILED-TO-REFUTE | `test_file_value_sends_multipart` failed |
| AC-2.5, AC-2.6 | W2 2f, 2g, 2b | FAILED-TO-REFUTE | 2, 1 and 8 failed |
| AC-3.1 | W2 2a (strip loop removed) | FAILED-TO-REFUTE | 15 failed (cross-origin × 3 token types, return hop) |
| AC-3.2 to AC-3.4 | W2 2c, 2d, 2e | FAILED-TO-REFUTE | 2, 1, 1 failed |
| AC-3.5 | W2 2k (field hash not flattened) | FAILED-TO-REFUTE | `message-field-hash`, `spam-hash` failed |
| AC-4.1 to AC-4.3 | W2 2i, 2j, 2h | FAILED-TO-REFUTE | 7, 1, 1 failed |
| AC-5.1, AC-5.3, AC-5.4 | W3 3a (drop plan.py PENDING `("DELETE", "/projects/:id/issues/:issue_iid")`) | FAILED-TO-REFUTE | `test_every_index_row_is_mapped_or_pending` failed (socket guard autouse) |
| UB-1 | W3 3e, 3f; W4 4a–4g, 4i; W5 5a–5i | FAILED-TO-REFUTE | all killed; 3f (bootstrap removed) fails `test_script_loads_by_path` with `ModuleNotFoundError: No module named 'gitlab_api'` in the child; 5g/5h/5i fail S |
| UB-2 | W2 2o; W3 3b, 3c, 3d; W4 4h | FAILED-TO-REFUTE | all killed; Grep `environ\|getenv` over `gitlab_api/`, `gitlab_wrapper.py`: prose and endpoint paths only (see O1) |
| DL-006 batching | RC rc-a…rc-g | FAILED-TO-REFUTE | 7/7 killed: batch over bound (1), bound 40,000 (9), failing batch swallowed (3), last code wins (1), stop after failure (1), head not repeated (2), never batched (2) (see O2) |
| Red for right reason | `python .claude/hooks/red_for_right_reason.py evidence/red/<f>` × 6 | FAILED-TO-REFUTE | wave-1…5, run-checks-batching: `OK … genuine assertion/property falsification`, exit 0; red/wave-5 S fails on "does not name `src/payload/scripts/gitlab_api/`" |
| No vacuous test | Grep skip/xfail/importorskip/commented `def test_`/`assert True`/deselect in the changed test modules | FAILED-TO-REFUTE | no match; no pyproject/conftest in the diff; every kill is an `AssertionError` or a `pytest.raises` oracle |
| Secrets hygiene | Grep f-strings/log calls naming a token in GitLab code | FAILED-TO-REFUTE | only `token_type {value!r}`, the fixed job-token sentence, key + code point; 3d (token echoed) killed by 5 tests |

Totals: 61 mutants, 54 killed, 7 survived (2p, 2q, 2r, 3g, x1, z1, w1).

## Coverage of the change (step 5)

`run_tests.py --coverage --cov-report=term-missing` over R T C D RC P V S: `197 passed`, exit 0. Missed lines:
transport 205-206, 235, 268-269, 310, 327, 395-396, 418, 424, 448-449, 458, 472, 554, 566, 578, 589, 620, 671-676;
registry 200, 259, 269, 323-327, 350, 354; commands/issue 107, 143; commands/pipeline 108, 115, 123, 147, 260-263;
gitlab_wrapper 85, 138-140, 144, 309, 332-333; run_checks 406-408 (the only miss among its new lines).

- **transport.py 424** (AC-2.3 "in a form body"): no GitLab test sent `form=` without a file; mutant 2q
  (`json.dumps(dict(form))`, `application/json`) passed W2 (60 passed). **REFUTED AC-2.3.**
- transport 235 (a non-GET/HEAD redirect is not followed, D4) survives as 2r. It serves no AC: CPython
  `HTTPRedirectHandler.redirect_request` (request.py) follows only POST 301/302/303, as a GET, and raises for every
  other method, and the strip loop (killed in 2a) still drops the credential, so AC-3.1 holds.
- 85 and 332-333 run only in the subprocess tests (3f killed). 578 and 323-327: part 1 has no GraphQL record.
  260-263: the only caller passes `--count 1` (setup-kiro Part 6.3). The rest refuse malformed responses or configs;
  no AC or UB names them.

## Observations (not refutations; route per issue-filing-discipline)

- O1: x1 (`from os import environ`) and 2p (`__import__("os").environ`) passed P and C. O2: z1 (console-script head
  not adjusted) and w1 (`invoke` returns 0, not 127) passed RC. All four are killed in the re-verification below.
- O3 3g is equivalent: with `required=False` the top-level parser still exits 2 through `parser.error`.

Tree: 61 mutants each `restored=True` (SHA-256 equal); `git status --porcelain` empty after every wave; scratch
`tmp/verify/` deleted; the only new path is this report.

Verdict: REFUTED AC-2.3

## Re-verification — 2026-11-11, HEAD 9e78001

`git diff c3efdcb 9e78001 -- src/payload/scripts prompts docs templates`: empty. Mutants applied alone (Edit),
restored, SHA-256 equal to before, `git status --porcelain` empty after each.

| Claim | Command | Result | Evidence |
|---|---|---|---|
| Whole suite | `get-pr-checks 34` | FAILED-TO-REFUTE | head `9e78001a…`; `report`, `verify (lint/types/security/tests)` all `completed`/`success` |
| AC-2.3 | 2q; W2 | FAILED-TO-REFUTE | `12 failed, 60 passed`: every `test_form_pairs_send_a_form_body` case, got `application/json` |
| O1 | x1, 2p in `_load_config`; `P C` | killed | `1 failed, 86 passed` each; `test_standard_library_only` names `from os import environ` / `__import__('os').environ` |
| O2 | z1, w1; RC | killed | z1 `1 failed, 23 passed` (`…keep_the_console_script_head`); w1 `2 failed, 22 passed` (`…fails_with_127`, `0 == 127`) |
| Restored tree; AST check on shipped code | rework-1's seven modules | FAILED-TO-REFUTE | `253 passed`; the admitted calls are `command_modules` and `discover_families` |
| No vacuous test | Grep skip/xfail/commented/`assert True`/deselect, T RC P | FAILED-TO-REFUTE | no match; every kill is an `AssertionError` |

O4 (observation): probe g1 `getattr(os, "environ")` passes `P C` (`87 passed`): the scan reads names, not strings;
the shipped files hold no such construct (Grep `environ|getenv`: prose and paths only).

Tree restored and clean, `tmp/` empty; this section is the only change.

Verdict: VERIFIED
