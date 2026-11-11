# Standards review — issue #63, design iteration 02 (delta)

Lane: standards-reviewer. Delta: `git diff fb3b401 8fe5ae0` of `requirements.md` and `design.md`, and the fix sites.
Sizes on 8fe5ae0: `requirements.md` 18,295 B (cap 20,000), `design.md` 54,973 B (cap 60,000), both under cap.

## Iteration-01 findings

| ID | Sev | Status | Evidence on 8fe5ae0 |
|---|---|---|---|
| B1 | B | resolved | requirements.md § Residuals is ten lines: five bullets of two lines each. The S3 bullet is the proposed text, and the `bearer` sentence is gone. The `bearer` residual now appears once, in design.md § Residuals, so it makes one ledger row. design.md § Residuals is ten lines too. |
| C1 | C | resolved | design.md § Residuals no longer has the "Requirements restatement owed" bullet. |
| C2 | C | resolved | design.md § D12 opens with the proposed paragraph, word for word. |
| C3 | C | resolved | G = `test_gitlab_api_container_registry.py` (new) appears in the mapping legend, D10, D12's test row, the AC-5.2 example (`test_a_job_token_logs_in_as_gitlab_ci_token`) and the AC-5.2 mapping row. R keeps the case where a record is sent without `project`. |
| C4 | C | resolved | D5 "`encode`." sends the check through `registry.check_header_value(*, name, value)`, and `_build_request` calls it too. D12's `registry.py` row lists it. The design says `transport.py` "already imports `gitlab_api.registry`", which holds: `transport.py` has `from gitlab_api.registry import Paging, Pair`. |
| C5 | C | resolved | D11 states the `positional_names` exception to "A path name … given twice keeps its last value". |
| D1 | D | resolved | AC-1.1 F1 reads "the keys issue #63 lists under F1". `37 keys` appears nowhere in either file. |

Scope check on the delta: no acceptance-criterion id was added. AC-7.1, AC-8.1 and UB-1 were restated, which `proportionality.md` § Scope freeze allows. D4 step 2's origin refusals and D5's longer list of refused header names are design detail of AC-5.2 ("Where the registry's origin comes from … are `design.md`'s") and AC-6.2. D5's list now matches the names D7's `sent_call` row already listed. "#10" and "real-forge" appear nowhere in either file.

## New findings

### C1 — D12 does not list D9's edit of N
Severity: C
Location: design.md § D12, the `test/test_gitlab_wrapper_contract.py` row and the "D9, D10" row
Defect: D9 now edits #43's N `test_only_the_upload_module_path_holds_a_hyphenated_name` by adding two exceptions to its rule. D12's N row says "D7's readings, its tests, the docstring", and the "D9, D10" row names R, T, K, C, P, G and the family modules but not N. So no row of the change's file table lists that edit.
Proposed-edit: in D12's `test/test_gitlab_wrapper_contract.py` row, replace the Change cell "D7's readings, its tests, the docstring" with "D7's readings, its tests, D9's `test_only_the_upload_module_path_holds_a_hyphenated_name` rule, the docstring" and its D cell "D7" with "D7, D9".

### D1 — D7 writes N's header location as a literal
Severity: D
Location: design.md § D7, opening paragraph
Defect: N matches every location against its own constants (`IN_PATH`, `IN_QUERY`, `IN_BODY`, `IN_FORM`; `param_problems` compares `param.location.value` with a row's location). The new sentence instead spells the header test as `location.value == "header"`.
Proposed-edit: replace "recognises a header `Param` by `location.value == "header"`" with "recognises a header `Param` by `location.value == IN_HEADER` (a new N constant, `"header"`, beside `IN_PATH`)".

CLEAN

Verdict: READY
