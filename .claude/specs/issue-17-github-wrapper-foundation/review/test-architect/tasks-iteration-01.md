# Test architect - tasks review, iteration 01

## Findings

### TA-T-C1 - wave 4's golden values meet the fork oracle only in wave 5
Severity: C
Location: tasks.md § Wave 4 task 4.1; § Wave 5 task 5.2
Defect: `test_the_fork_produces_the_golden_case` checks that the `CASES` rows are the fork's own output (design § Correctness Properties UB-1.1, "The oracle is the fork"). It is written in 5.2, after IMPL 4.3 has been green-captured against the issues rows of 4.1. A wrong row would therefore first fail in wave 5, and fixing it means editing `commands/issues.py` and the 4.1 rows, files that no wave-5 task owns.
Material-because: this is a risk to the evidence order for UB-1.1, not an untested criterion. P still runs every row on the merged tree.
Proposed-edit: in 4.1, add `test/test_github_wrapper_fork_parity.py` to Files with `test_the_fork_produces_the_golden_case`, worded as in 5.2, and add that path to wave 4's `Run:` line. In 5.2, keep only `test_the_parsers_match_option_by_option`, and its Files entry stays `test/test_github_wrapper_fork_parity.py`.

### TA-T-D1 - coverage column header
Severity: D
Location: tasks.md § Coverage
Defect: the column is headed "TEST tasks", but the UB-3.1 row also lists F.2, which is a VERIFY task.
Proposed-edit: rename the header to "TEST / VERIFY tasks".

## Coverage (criterion -> TEST task -> status)

| Criterion | TEST task(s) | Status |
|---|---|---|
| AC-1.1 | 2.1 (R) + design inspection D1 | OK |
| AC-1.2 | 3.1 (V `test_discovery_follows_the_directory`) + inspection D2 | OK |
| AC-1.3 | 3.1 (V `test_one_module_per_family_holding_only_its_own_ids`) | OK |
| AC-2.1 | 1.1 (T) | OK |
| AC-2.2 | 1.1 (T) | OK |
| AC-2.3 | 1.1 (T) | OK |
| AC-2.4 | 1.1 (T) | OK |
| AC-3.1 | 1.1 (T) | OK |
| AC-3.2 | 1.1 (T) | OK |
| AC-3.3 | 1.1 (T) | OK |
| AC-3.4 | 1.1 (T) | OK |
| AC-4.1 | 1.1 (T) | OK |
| AC-4.2 | 1.1 (T) | OK |
| AC-4.3 | 1.1 (T) | OK |
| AC-5.1 | 3.1 (V) | OK |
| AC-5.2 | 3.1 (V) | OK |
| AC-5.3 | 3.1 (V) | OK |
| UB-1.1 | 4.1 (C, CASES), 5.1 (CASES), 5.2 (P) | OK |
| UB-1.2 | 4.1 (C) + `test_wrapper_delivery.py` in the wave 4/5 runs | OK |
| UB-1.3 | 4.1 (C `test_the_script_runs_by_path`), 5.3 (S) | OK |
| UB-2.1 | 4.1 (C) | OK |
| UB-2.2 | 3.1 (V) | OK |
| UB-3.1 | 4.1 (`test_wrapper_delivery.py` in the captures), F.2 | OK |
| UB-3.2 | 4.1 (C) | OK |

The tasks.md § Coverage table matches every `Validates:` line. In every wave the TEST tasks come before the IMPL tasks and need only code from earlier waves. Within each wave, the tasks own disjoint files. F.1 records E2E as not applicable, with its reason, and names the `verify` job, leg `tests`.

Verdict: CLEAN - TEST-READY (0 A, 0 B; 24 OK, 0 GAP)
