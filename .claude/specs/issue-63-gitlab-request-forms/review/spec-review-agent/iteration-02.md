# spec-review-agent — design iteration 02, delta (issue #63, tier M)

Reviewed: `git diff fb3b401 8fe5ae0` of `requirements.md` and `design.md`, the iteration-01 fix sites, against the
worktree's `src/payload/` and `test/`, `origin/main` 252c21e, #41's design D8, and `docs/api-reference/gitlab/conventions.md`.

## Iteration-01 findings

| ID | Status | Evidence |
|---|---|---|
| B1 | resolved | D1's paragraph now calls `lookup(operation_id=...)` when `endpoint` is `None`; R `test_call_refuses_an_undeclared_value` holds the only monkeypatched `lookup` under `src/payload/test/` and `test/` |
| B2 | resolved | D9's last bullet names #43's N `test_only_the_upload_module_path_holds_a_hyphenated_name` with both exceptions; UB-1's parenthetical adds "a path's parameters read as `:name` and `*name` alone" |
| B3 | resolved | D9's second bullet names gitlab_dedicated's `test_every_reference_has_its_record` and `test_only_the_list_records_are_paged`; the module's third `RECORD_ENDPOINTS` reader, `test_every_param_is_typed_as_its_row` (`expected_bodies`), is in D9's third bullet |
| C1 | resolved | AC-7.1 names the lifted gate; AC-8.1 routes a gated record to AC-7.2's test; the mapping row of AC-8.1 adds it |
| C2 | resolved | D4's `_send` bullet matches `transport.py` `_send` (`error_text(body=response.text)`, `details=response.text`) |
| C3 | resolved | `gitlab_wrapper_fixtures.py` `RecordedRequest.header` compares case-insensitively, as the restated K oracle reads it |
| C4 | resolved | D8's `software_supply_chain_security` row gives the three header `Param`s `required=True` |
| D1 | resolved | the stale Residual is deleted |
| D2 | resolved | D12's `commands/call.py` row lists `undocumented`, `_compared_name`, `call_values` |

Fix-site claims checked and holding: `transport.py` imports `gitlab_api.registry` (`Paging`, `Pair`) and `registry.py`
imports nothing of `transport` outside `TYPE_CHECKING`, so `_build_request` calling `registry.check_header_value` adds
no import cycle; `developer_experience`, `fulfillment` and `tenant_scale` test modules hold `OTHER_ENDPOINT_KEYS`; the
`commands/call.py` docstring holds "A path name, or an attribute given by `-f` or `-F`, given twice keeps its last
value"; #41 D8's exceptions row holds "a request form that part 1 does not build"; `test/test_gitlab_graphql_contract.py`
holds `test_the_map_names_the_graphql_call`; `conventions.md` "Which endpoints accept a CI/CD job token" lists no
Projects API endpoint; the eight archive formats match `conventions.md`; both Residuals sections are ten lines.

## New findings

### B1 — AC-9.2's new map test does not pin the F2 form
Severity: B
Location: design.md § Correctness Properties, AC-9.2 (N `test_the_map_names_the_request_forms`); § D11
Defect: AC-9.2 requires the map to "name the same" as AC-9.1, which includes "gives the two values of an F2 path"; the
new N test asserts only `--endpoint`, `--path format=`, `--header` and `override_params[`, so a map bullet without the
repeated `--path` passes it, while AC-9.1's test pins that form as "two `--path id=` in one line".
Material-because: AC-9.2 — one of the five forms it requires has no test that can fail.
Proposed-edit: AC-9.2's property reads "…the `src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md`
holds `--endpoint`, two `--path id=`, `--path format=`, `--header` and `override_params[`, as …"; in D11, "names
`--endpoint`, the repeated `--path`, …" becomes "names `--endpoint`, the repeated `--path` (two `--path id=`), …".

### C1 — "What stays callable" says every D8 record is ungated
Severity: C
Location: design.md § Security, "What stays callable"
Defect: "every record of D8, none gated" includes D8's `gitlab_dedicated` row, the S3 import, which D6, D12, the
next bullet ("Gates") and UB-3 put in `GATED_OPERATIONS`.
Proposed-edit: "every record of D8 but the S3 import (Gates), none gated (#41 Security "Destructive operations"): …".

### C2 — D7's red-phase claim omits D9's restated N test
Severity: C
Location: design.md § D7, opening paragraph ("on the base its existing tests fail only through `header_problems`")
Defect: on the base, #43's N `test_only_the_upload_module_path_holds_a_hyphenated_name`, restated by D9, also fails:
#40's pattern gives the `archive[.format]` row `("id",)` and the delete-by-reference row `()`.
Proposed-edit: "…so that on the base its existing tests fail only through `header_problems` and D9's restated
literals."

NOT-CLEAN (0 A, 1 B)
Verdict: NOT-READY
