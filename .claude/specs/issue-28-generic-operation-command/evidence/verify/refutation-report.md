# Refutation report — issue #28, PR #45, head b127712

Scope `git diff origin/main...HEAD` (base 2eb1c9e). Tests ran only as `venv python scripts/run_tests.py <files>` from the
worktree. K R T H N V C P as in tasks.md. Rows 1-29 are the first pass, trimmed to their deciding counts.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Suite green on b127712 | `get-pr-checks 45` | FAILED-TO-REFUTE | head = HEAD; every check `success` |
| 2 | Red captures right reason | red/wave-1..4 | FAILED-TO-REFUTE | 4x assertion/falsification, no load error |
| 3 | W1 AC-1.2, AC-2.3 | registry.py + transport.py reverted; R T | FAILED-TO-REFUTE | `10 failed` |
| 4 | AC-1.2 `[]` names | `query_name` returns name; R T | FAILED-TO-REFUTE | `2 failed` |
| 5 | AC-1.2 page Accept | `_page_items` sends ACCEPT_JSON; R T | FAILED-TO-REFUTE | `1 failed` |
| 6 | AC-1.2 record accept | `send` omits `accept`; R T | FAILED-TO-REFUTE | `2 failed` |
| 7 | AC-1.2, AC-2.3 | `send` returns `.json()`; `path_parameters` sorted; R T | FAILED-TO-REFUTE | `11 failed` |
| 8 | AC-1.2 list accept | `registry.pages` omits `accept`; R T K | FAILED-TO-REFUTE | `1 failed`, in K only |
| 9 | AC-1.1 gates | `GATED_OPERATIONS` emptied; K H N | FAILED-TO-REFUTE | `2 failed` |
| 10 | AC-1.7 | `GitHubAPIError` caught as refusal; K H N | FAILED-TO-REFUTE | `1 failed` |
| 11 | AC-2.2 | undocumented path names ignored; K H N | FAILED-TO-REFUTE | `2 failed` |
| 12 | AC-1.3 | `json_member` keeps text unparsed; K H N | FAILED-TO-REFUTE | `9 failed` |
| 13 | AC-1.4 | LINK items printed one by one; K H N | FAILED-TO-REFUTE | `5 failed` |
| 14 | AC-1.6 | non-JSON body decoded lossily; K H N | FAILED-TO-REFUTE | `2 failed` |
| 15 | AC-2.3 | missing path parameter not refused; K H N | FAILED-TO-REFUTE | `1 failed` |
| 16 | AC-1.1 every record | only first body member sent; N | FAILED-TO-REFUTE | `2 failed` |
| 17 | AC-1.5, AC-3.1, AC-3.2 | empty body prints `null`; `call_problems` drops method; `is_unreachable` drops family arm; K N | FAILED-TO-REFUTE | `3 failed` |
| 18 | UB-2.1, UB-2.2 | `--token` on `call`; `import pytest` in call.py; C V | FAILED-TO-REFUTE | `2 failed` |
| 19 | AC-5.3 | `_record_problems` compares path only; V | FAILED-TO-REFUTE | `1 failed` |
| 20 | AC-5.3 | pending ID absent from index accepted; V | FAILED-TO-REFUTE | `1 failed` |
| 21 | AC-4.1 | docstring loses `exit 2`; C + budget | FAILED-TO-REFUTE | `1 failed` |
| 22 | AC-4.2 | map bullet loses the `call` sentences | FAILED-TO-REFUTE (inspection) | mutant survives (`622 passed`); the oracle is inspection plus the cap test by design; sentences present |
| 23 | Parse refusals, D2 | `_split` accepts no `=` and an empty name; `-F` accepts NaN; `-F` usage error carries the value; wave-2 Run line | REFUTED AC-1.2, AC-1.3 | `592 passed`, exit 0 |
| 24 | Coverage | `--coverage` K R T H N | REFUTED AC-1.2, AC-1.3 | call.py missing `108, 110, 122, 131-132` |
| 25 | UB-3.1 (F.2) | gitlab wrapper, delivery test in the diff | FAILED-TO-REFUTE | no match; delivery tests pass |
| 26 | UB-1.1 (F.3) | `git diff --numstat` / `-U0` | FAILED-TO-REFUTE | 0 deletions in fixtures, C, V, R, T |
| 27 | Vacuity | skip/xfail/importorskip/deselect/no cover/`assert True` | FAILED-TO-REFUTE | none |
| 28 | Re-confirm green | K R T C delivery H N V P budget | FAILED-TO-REFUTE | `648 passed` |
| 29 | Inspection ACs | design D1/D8, D5, D6 | FAILED-TO-REFUTE | AC-1.1, AC-3.1, AC-5.1, AC-5.2 hold |

Secrets hygiene, by inspection: call.py holds no `environ`, `getenv` or `token`; its messages render names with
`json.dumps`; the token stays in `Transport`. The usage-error half had no test (row 23).

Refuted at b127712 (step 5): `_split` (no `=`, empty name), `_refuse_constant` and the non-JSON refusal of `json_member`
in `src/payload/scripts/github_api/commands/call.py` (design D2 "Parsing", AC-1.2, AC-1.3) ran in no test. Tree then:
seven mutated files restored, `sha256sum -c` OK, `git status --porcelain` empty.

Verdict: REFUTED AC-1.2 AC-1.3

## Re-verification — 2026-11-11, head cbb8c0c

Delta: cbb8c0c (DL-008) adds `test_a_malformed_argument_is_refused_without_its_value` (7 cases) to K and touches only K,
the decision log, `evidence/green/rework-1.txt` and this report. `git diff --stat b127712 cbb8c0c -- src/payload/scripts
docs` prints nothing: the production code is unchanged. Each mutant edited `call.py` alone; after every run
`git checkout --` restored it, and its sha256 `615a5fee...c79c` and the HEAD blob `c78fd36` matched each time.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| R1 | Suite green on cbb8c0c | `get-pr-checks 45` (main checkout) | FAILED-TO-REFUTE | `"head": "cbb8c0c15b7d..."` = HEAD; report, verify (types, security, tests, lint) `completed` `success`; `statuses: []` |
| R2 | AC-1.2, AC-1.3 | row 23's combined mutant; wave-2 Run line | FAILED-TO-REFUTE | `7 failed, 592 passed`, exit 1: the 7 new cases |
| R3 | AC-1.2 | `_split` accepts no `=`; K | FAILED-TO-REFUTE | `1 failed, 40 passed`: path-without-an-equals-sign, "standard error holds no usage: ''" |
| R4 | AC-1.2 | `_split` accepts an empty name; K | FAILED-TO-REFUTE | `2 failed, 39 passed`: query- and raw-field-with-an-empty-name, no usage |
| R5 | AC-1.3 | `json_member` without `parse_constant`; K | FAILED-TO-REFUTE | `3 failed, 38 passed`: nan, infinity, negative-infinity, "no route for PATCH .../issues/5" |
| R6 | AC-1.3, Security | `json_member` lets `ValueError` through to argparse; K | FAILED-TO-REFUTE | `4 failed, 37 passed`: `no usage error names "title": ["invalid json_member value: 'title=nope'"]` |
| R7 | Leak assert live | both refusal messages append the value; K | FAILED-TO-REFUTE | `6 failed, 35 passed`: "standard error holds the value ['secret']" and 5 more |
| R8 | Option assert live | `-F` spelling dropped from `register`; `-k` the new test | FAILED-TO-REFUTE | `4 failed, 3 passed`: "no usage error names the option -F/--field" |
| R9 | Coverage | `--coverage` K alone | FAILED-TO-REFUTE | `41 passed`; call.py `136 0 100%`: 108, 110, 122, 131-132 run |
| R10 | Vacuity | Grep K: skip, xfail, importorskip, deselect, no cover, `assert True`, health-check suppression, marks other than parametrize | FAILED-TO-REFUTE | one hit, the `rows_of` docstring of an existing `assert rows` guard; each of the new test's four asserts failed under R3-R8; no conftest, pyproject or workflow file in the delta |
| R11 | Re-confirm green | wave-2 Run line, restored tree, after R7 and again after R8 | FAILED-TO-REFUTE | `599 passed`, exit 0, both times |

R2 to R9 supersede rows 23 and 24 and close the usage-error gap of the secrets note: AC-1.2 and AC-1.3 hold. Tree:
`git status --porcelain` was empty after every restore and before this write; `tmp/` held nothing and was not used;
this report is the only file changed.

Verdict: VERIFIED
