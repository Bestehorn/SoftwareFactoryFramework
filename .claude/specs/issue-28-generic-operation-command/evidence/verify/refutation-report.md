# Refutation report — issue #28, PR #45, head b127712

Scope `git diff origin/main...HEAD` (base 2eb1c9e). Tests ran only as `venv python scripts/run_tests.py <files>` from the
worktree. K R T H N V C P as in tasks.md. Captures were scratch files under `tmp/`; each row quotes the deciding line.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Suite green on pushed SHA | `github_wrapper.py get-pr-checks 45` | FAILED-TO-REFUTE | head `b1277125…` = HEAD; report, verify (tests/types/lint/security) all `completed` `success`; `statuses: []` |
| 2 | Red captures right reason | `red_for_right_reason.py` on red/wave-1..4 | FAILED-TO-REFUTE | 4x `OK … genuine assertion/property falsification`; no collection error |
| 3 | W1 AC-1.2, AC-2.3 | registry.py + transport.py reverted to origin/main; R T | FAILED-TO-REFUTE | `10 failed, 63 passed` |
| 4 | AC-1.2 `[]` names | `query_name` returns name; R T | FAILED-TO-REFUTE | `2 failed` brackets[send], [pages] |
| 5 | AC-1.2 page Accept | `_page_items` sends ACCEPT_JSON; R T | FAILED-TO-REFUTE | `1 failed` test_link_pages_send_the_given_accept |
| 6 | AC-1.2 record accept | `send` omits `accept`; R T | FAILED-TO-REFUTE | `2 failed` test_send_returns_the_response_of_the_record |
| 7 | AC-1.2, AC-2.3 | `send` returns `.json()`; `path_parameters` sorted; R T | FAILED-TO-REFUTE | `11 failed`: "send returned {…}, not the Response"; order asserts |
| 8 | AC-1.2 list accept | `registry.pages` omits `accept`; R T K | FAILED-TO-REFUTE | `1 failed`, K …media-type-on-every-page (R, T alone pass) |
| 9 | AC-1.1 gates | `GATED_OPERATIONS` emptied; K H N | FAILED-TO-REFUTE | `2 failed`: "no route for PUT …/pulls/1/merge", "POST …/issues" |
| 10 | AC-1.7 | `GitHubAPIError` caught as refusal; K H N | FAILED-TO-REFUTE | `1 failed`: "exit code 2, the golden is 1" |
| 11 | AC-2.2 | undocumented path names ignored; K H N | FAILED-TO-REFUTE | `2 failed`: "no route for GET …/issues/5" |
| 12 | AC-1.3 | `json_member` keeps text unparsed; K H N | FAILED-TO-REFUTE | `9 failed`: H falsified, 6 K rows, N unreachable |
| 13 | AC-1.4 | LINK items printed one by one; K H N | FAILED-TO-REFUTE | `5 failed`, both AC-1.4 rows |
| 14 | AC-1.6 | non-JSON body decoded lossily; K H N | FAILED-TO-REFUTE | `2 failed` archive, not-utf-8 |
| 15 | AC-2.3 | missing path parameter not refused; K H N | FAILED-TO-REFUTE | `1 failed` |
| 16 | AC-1.1 every record | only first body member sent; N | FAILED-TO-REFUTE | `2 failed`: "3 problems calling 21 records" |
| 17 | AC-1.5, AC-3.1, AC-3.2 | empty body prints `null`; `call_problems` drops method; `is_unreachable` drops family arm; K N | FAILED-TO-REFUTE | `3 failed`: empty-body stdout, unreachable judged map, "method-put: the method returned []" |
| 18 | UB-2.1, UB-2.2 | `--token` on `call` + `import pytest` in call.py; C V `-k` | FAILED-TO-REFUTE | `2 failed`: "options that take a token: ['-c call --token']", "imports outside the standard library" |
| 19 | AC-5.3 | `_record_problems` compares path only; V | FAILED-TO-REFUTE | `1 failed` [record_method_changed_same_path] |
| 20 | AC-5.3 | pending ID absent from index accepted; V | FAILED-TO-REFUTE | `1 failed` [pending_id_removed] |
| 21 | AC-4.1 | docstring loses `exit 2`; C + budget | FAILED-TO-REFUTE | `1 failed`: "does not name: ['exit 2']" |
| 22 | AC-4.2 | map bullet loses the `call` sentences; wave-4 Run line | FAILED-TO-REFUTE (inspection) | `622 passed`: the mutant survives. The design's oracle is inspection plus the cap test (Correctness Properties AC-4.2, F.4). Inspected: D7's sentences present, closing sentence last; `test_llm_map_within_cap` PASSED. No test guards the content. |
| 23 | Parse refusals, D2 | `_split` accepts no `=` and an empty name; `-F` accepts NaN; `-F` usage error carries the value; wave-2 Run line | REFUTED AC-1.2, AC-1.3 | `592 passed`, exit 0 |
| 24 | Coverage | `--coverage` K R T H N | REFUTED AC-1.2, AC-1.3 | `121 passed`; call.py `96%`, missing `108, 110, 122, 131-132`; registry missing `104, 131`, `_common` missing `65-71, 86`, both unchanged lines; changed transport lines all run |
| 25 | UB-3.1 (F.2) | `git diff --name-only` grep for the gitlab wrapper and delivery test | FAILED-TO-REFUTE | no match (grep exit 1); delivery tests pass (row 28) |
| 26 | UB-1.1 (F.3) | `git diff --numstat` / `-U0` | FAILED-TO-REFUTE | 0 deletions in fixtures (CASES), C, V, R, T; P not in diff; C adds only test_the_usage_names_the_operation_call, V only test_a_regenerated_index_names_each_changed_id |
| 27 | Vacuity, step 3 | added test lines grepped for skip/skipif/xfail/importorskip/deselect/no cover/`assert True`/health-check suppression | FAILED-TO-REFUTE | none found; no conftest, pyproject or workflow file in the diff |
| 28 | Re-confirm green | K R T C delivery H N V P budget, restored tree | FAILED-TO-REFUTE | `648 passed`, exit 0 |
| 29 | Inspection ACs | design D1/D8, D5, D6 | FAILED-TO-REFUTE | AC-1.1 D1 table + D8; AC-3.1 D5 rule; AC-5.1 pin `2f8f80e, 2026-11-07` = operations-index.md banner line 1; AC-5.2 D6 table + "Which change fixes it" |

Secrets hygiene, by inspection: call.py imports only argparse, json, logging, dataclasses, types, typing and
github_api. It holds no `environ`, `getenv` or `token`. Its refusal and usage-error messages render names with
`json.dumps` and hold no value. The token stays in `Transport`, and the diff changes only the `Accept` header there.
The usage-error half of this claim has no test (row 23).

## Refuted: AC-1.2, AC-1.3 (step 5)

Lines 108 and 110 of `src/payload/scripts/github_api/commands/call.py` (`_split`: no `=`, empty name) and lines 122
and 131-132 (`_refuse_constant`, the non-JSON refusal of `json_member`) are reachable by any malformed
`--path/--query/-f/-F` argument, and no test runs them. Grep for their messages, `NaN` or `json_member` refusals in
`test/` and `src/payload/test/` finds nothing. The combined mutant passes the whole wave-2 Run line. The lines
implement design D2 "Parsing". D2 is headed AC-1.2, AC-1.3, and its `-F` bullet is cited as AC-1.3. They also
implement the Security Considerations claim that an argparse type error holds no value. The gap closes with a test
that passes `--field x=NaN`, `--field x=nope`, `--path noequals` and `--query =v`, and asserts exit 2, no request, and a
standard error that names the name and not the value.

Not refuted, noted: row 8, where `registry.pages` forwarding `accept` is guarded only by K, and row 22, where the map
content is guarded only by inspection, as designed.

## Tree

Every mutated file (registry.py, transport.py, call.py, github_wrapper.py, forLLMConsumption.md, the V and N modules)
was restored from a `tmp/` copy, with `sha256sum -c` OK for all seven after every run. `git status --porcelain` was
empty before this report. This report is the only new file. The `tmp/` scratch is deleted right after it is written.

Verdict: REFUTED AC-1.2 AC-1.3
