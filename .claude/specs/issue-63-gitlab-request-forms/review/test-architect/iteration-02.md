# Test architect — design review, iteration 02 (delta)

## Iteration-01 findings

| ID | Status |
|---|---|
| B1 | Partly resolved. N `test_the_map_names_the_request_forms` is named, mapped and can fail, but the spellings it pins (the ones my iteration-01 edit proposed) cover three of AC-9.2's five forms. See B3. |
| B2 | Resolved. N `test_each_record_of_an_id_copies_its_base_record` compares each later record with the base on `params` (name, location, kind, required), `body`, `paging` and `fixed`. All four are `RestOperation` fields (`registry.py`), and the oracle restates D8 Rules. |
| C1 | Resolved. Exit 0, `RecordedRequest.header(name=)` (case-insensitive, `gitlab_wrapper_fixtures.py`), `call_values` (exists in `commands/call.py`). |
| C2 | Resolved. D9 names gitlab_dedicated's two tests. The ID-keyed literals keep their shape, so the `required`, `bodies` and `paged` dicts of developer_experience's `test_every_param_is_typed_as_its_row` and `test_only_the_list_records_are_paged` still hold unedited once F1 records copy their base. `OTHER_ENDPOINT_KEYS` exists in all three modules D9 names. |
| C3 | Resolved. |
| C4 | Resolved, and requirements AC-8.1 is restated to match. |
| C5 | Resolved. |
| D1 | Resolved. |

These delta checks raised no finding:
- D1 calls `lookup(operation_id=...)` when `endpoint` is `None`, so R `test_call_refuses_an_undeclared_value` (its fake `lookup(*, operation_id)`) passes unedited. No K test patches `lookup`.
- `transport.py` already imports `gitlab_api.registry` (`Paging, Pair`), so `check_header_value` adds no import cycle.
- D9's #43 N bullet matches #43 UB-4's oracle (`registry.placeholders` against #40's pattern). Its only new differences are the `[.format]` and `${NAME}` rows.
- G follows `testing.md` rule 3 and the test-time import pattern, and `run_tests.py` passes `--continue-on-collection-errors`.
- Each new T header name (`Host`, `Content-Length`) and AC-5.2's step-4 `404` case can fail.
- Each AC-5.3 step-2 case (`""`, `/group/project`, `registry.example.com#/x`, `user@registry.example.com/x`) breaks one of D4's step-2 rules.

## New findings

### B3 — The map test pins neither the two values of an F2 path nor a two-level member
Severity: B
Location: design.md § Correctness Properties AC-9.2
Defect: The bullet only has to hold `--endpoint`, `--path format=`, `--header` and `override_params[`. A bullet with no repeated `--path` passes, and so does one that names only `override_params[visibility]`, which is a one-level member.
Material-because: AC-9.2 says the map "SHALL name the same" as AC-9.1, which includes the two values of an F2 path and a two-level member, and no test checks those two forms.
Proposed-edit: replace "holds `--endpoint`, `--path format=`, `--header` and `override_params[`," with "holds AC-9.1's spellings: `--endpoint`, two `--path id=`, `--path format=`, `--header` and `override_params[container_expiration_policy_attributes]`,".

### C6 — The base-record test passes on the base, over no ID
Severity: C
Location: design.md § Correctness Properties AC-1.2
Defect: No ID has two records on the base, so `test_each_record_of_an_id_copies_its_base_record` is green in the wave's red run. After the change it would also pass if its grouping found no ID at all.
Proposed-edit: append "; the IDs it judges include `plan#add-an-emoji-reaction-to-a-resource` and `verify#get-the-latest-release`, so it is red on the base".

### C7 — AC-5.3's oracle does not pin "before step 3", and its `@` case can pass without the refusal
Severity: C
Location: design.md § Correctness Properties AC-5.3
Defect: The oracle "no recorded request on the registry's origin" still holds when a step-2 case sends `/jwt/auth`. Its docstring says `transport.origin` gives `https://user@registry.example.com/…` the host `user@registry.example.com`. So if a run skips the `@` rule, it sends the Bearer request, and the case still passes when the test compares origins as `transport.origin` does.
Proposed-edit: replace "no recorded request on the registry's origin" with "the recorded requests are exactly those of the steps before the failing one (none for `bearer`, step 1 for its `401`, steps 1 and 2 for a project answer, steps 1 to 3 for a `/jwt/auth` answer)".

### D2 — Which request G reads the login from
Severity: D
Location: design.md § Correctness Properties AC-5.2
Defect: "sends … the login `gitlab-ci-token`" does not say which request carries the login.
Proposed-edit: "a job token sends no `GET /user`, and the `/jwt/auth` request's `Authorization: Basic` decodes to `gitlab-ci-token:<token>`".

## Coverage

| Criterion | Tests | Status |
|---|---|---|
| AC-1.1 | V both; D9 pending literals | COVERED |
| AC-1.2 | N record test, N base-record test (C6); D9 typing | COVERED |
| AC-1.3 | D9 pending literals; V | COVERED |
| AC-1.4 | V both | COVERED |
| AC-2.1 | F:plan, F:sscs, K endpoint tests | COVERED |
| AC-2.2 | F:plan; R lookup | COVERED |
| AC-2.3 | F:developer_experience literals | COVERED |
| AC-2.4 | K refusals; P endpoint property; R lookup | COVERED |
| AC-3.1 | F:create, F:tenant_scale; P; R | COVERED |
| AC-3.2 | same | COVERED |
| AC-3.3 | K two-value refusal | COVERED |
| AC-4.1 | F:create formats; R suffix | COVERED |
| AC-4.2 | K format refusal; P (`sampled_from` + `text`) | COVERED |
| AC-5.1 | F:sscs token info; T host; R base | COVERED |
| AC-5.2 | F:package (with step-4 `404`); T both; G job token (D2); R send | COVERED |
| AC-5.3 | F:package no-token cases (C7) | COVERED |
| AC-6.1 | N `header_problems` | COVERED |
| AC-6.2 | F:sscs, F:openapi_only; T; R | COVERED |
| AC-6.3 | K undeclared header | COVERED |
| AC-7.1 | F:gitlab_dedicated (gate lifted); K S3 refusal | COVERED |
| AC-7.2 | N two-level member | COVERED |
| AC-8.1 | N record, send, readings; N two-level for the gated S3 record | COVERED |
| AC-8.2 | N request header | COVERED |
| AC-8.3 | the main-run examples and refusals | COVERED |
| AC-9.1 | C and K docstring tests | COVERED |
| AC-9.2 | N map test (three of five forms); `test_llm_map_within_cap` | GAP (B3) |
| UB-1 | existing suites; D9 incl. #43 N; R NuGet repeat; R call fake `lookup` | COVERED |
| UB-2 | P stdlib; K no token option; C config; T; F:package | COVERED |
| UB-3 | K refusals; S3 gate | COVERED |
| UB-4 | GitHub suites in CI; diff | COVERED |

Counts: 0 A, 1 B, 2 C, 1 D; 29 COVERED, 1 GAP.

Verdict: NOT-READY
