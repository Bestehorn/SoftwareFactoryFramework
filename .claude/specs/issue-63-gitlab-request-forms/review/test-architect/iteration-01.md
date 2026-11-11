# Test architect — design review, iteration 01

### B1 — AC-9.2's "name the same" clause has no test
Severity: B
Location: design.md § Correctness Properties AC-9.2; § Acceptance Criteria Mapping AC-9.2
Defect: Only `test_llm_map_within_cap` is named. Nothing checks that the map's `gitlab_api/` bullet holds the spellings, so a bullet that names no form passes.
Material-because: AC-9.2 ("`docs/forLLMConsumption.md` SHALL name the same") has no test.
Proposed-edit: AC-9.2 → "Example, N `test_the_map_names_the_request_forms`: the `src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md` holds `--endpoint`, `--path format=`, `--header` and `override_params[`, as `test/test_gitlab_graphql_contract.py` pins the GraphQL bullet (#44 AC-5.2); `test_llm_map_within_cap` passes." The mapping row AC-9.2 gains "N `test_the_map_names_the_request_forms`".

### B2 — The typing checks see only one record per ID, so other F1 records go unchecked
Severity: B
Location: design.md § Correctness Properties AC-1.2; § D9
Defect: The typing tests key their result by operation ID: `required_params`/`non_scalar_params` of verify, create's `typed_params`, and the `required` dicts of developer_experience and fulfillment, where the last record wins; plan uses `(operation_id, name)` sets, where all records merge. N's `record_problems` compares neither `kind` nor `required`. An ID with three records (`verify#get-the-latest-release` with its required `suffix_path`, the plan emoji "…a resource" References with their required rows) therefore has records whose `kind` or `required` can be mis-transcribed with no test failing.
Material-because: AC-1.2 (each record of this change transcribed by its family's rules) is untested for those records.
Proposed-edit: AC-1.2 gains "Structural, N `test_each_record_of_an_id_copies_its_base_record`: for every ID that several REST records of one family declare, each record after the first declares the first's `Param`s (name, location, kind, required) less those naming a placeholder of its own path, and the first's `body`, `paging` and `fixed` (D8 Rules)". The mapping row AC-1.2 gains the same test.

### C1 — "sent as `X-Gitlab-Nonce`" cannot be observed at the fake host
Severity: C
Location: design.md § Correctness Properties AC-6.3
Defect: `urllib.request.Request.add_header` capitalizes every name. Measured: adding `X-Gitlab-Nonce` and then `x-gitlab-nonce` records a single header, `('X-gitlab-nonce', 'n2')`. A case-sensitive assertion therefore never passes, and `RecordedRequest.header` cannot tell the two spellings apart.
Proposed-edit: replace "is accepted and sent as `X-Gitlab-Nonce`" with "is accepted: exit 0, and the recorded request's `header(name="X-Gitlab-Nonce")` is `n1`".

### C2 — D9 misses two tests, and a by-ID literal cannot hold the extra keys
Severity: C
Location: design.md § D9
Defect: `gitlab_dedicated`'s `test_every_reference_has_its_record` and `test_only_the_list_records_are_paged` compare against `RECORD_ENDPOINTS`, which has to gain the S3 import, yet D9 counts them among the tests that pass unedited. Separately, a `{id: (method, path)}` literal (`RECORD_ENDPOINTS`, tenant_scale `RECORDS`) cannot "gain" a second record under the same ID. Changing its shape would also force edits to tests D9 does not list: the typed and paged tests and `list_params` of developer_experience and fulfillment, which read it as one key per ID.
Proposed-edit: D9's third bullet gains "`test_every_reference_has_its_record` and `test_only_the_list_records_are_paged` of `gitlab_dedicated` (their `RECORD_ENDPOINTS` gains the S3 import)". The lead sentence gains "a `{id: (method, path)}` literal keeps its shape and the base record's key; an F1 Reference's other keys are asserted from a literal of their own (developer_experience and fulfillment already hold `OTHER_ENDPOINT_KEYS`)".

### C3 — The format property almost never draws a listed format
Severity: C
Location: design.md § Correctness Properties AC-4.2
Defect: Drawing from `st.text()` practically never produces one of the eight formats, so P exercises only its refusal half.
Proposed-edit: "over `st.one_of(st.sampled_from(<the eight formats>), st.text())`, a listed value gives `.value`; any other raises `ValueError`".

### C4 — The S3 record's send proof is not named under AC-8.1
Severity: C
Location: design.md § Acceptance Criteria Mapping AC-8.1
Defect: `test_every_record_is_sent_as_its_section_documents` skips `GATED_OPERATIONS`, so it never sends the S3 record of this change. That record is sent by `test_a_two_level_member_is_read_and_sent_as_written`, which the row does not name.
Proposed-edit: the AC-8.1 row gains "N `test_a_two_level_member_is_read_and_sent_as_written` (the S3 record, gate lifted)".

### C5 — The red run must keep N's existing checks green on the base
Severity: C
Location: design.md § D7
Defect: N's new readings use `positional_names`, `suffix_values`, `token_scope` and `Location.HEADER`, and the base has none of them. Read unguarded, the red run crashes the existing send and record tests on every record (AttributeError) instead of failing only on the NuGet records' missing `Symbolchecksum`.
Proposed-edit: D7 gains "N reads a field the base lacks with its default (`getattr(record, "positional_names", ())`) and recognises a header `Param` by `location.value == "header"`, so that on the base its existing tests fail only through `header_problems`".

### D1 — Stale residual
Severity: D
Location: design.md § Residuals
Defect: The design still says a requirements restatement is owed ("Requirements restatement owed: UB-1's …, UB-3's …"), but `requirements.md` UB-1 and UB-3 already carry it (DL-004).
Proposed-edit: delete that bullet.

UB-1 check: every test D9 restates pins retired state: a pending key, one record per ID, a JSON-only body, or a table without `Symbolchecksum`. No D9 edit weakens an assertion of unchanged behaviour. Test-first: every new test goes red on the base because the feature is missing (unknown kwarg, unknown ID or literal mismatch), provided C5 is applied. Imports happen at test time, so there are no collection errors.

## Coverage

| Criterion | Tests | Status |
|---|---|---|
| AC-1.1 | V both; D9 pending literals | COVERED |
| AC-1.2 | N record test; D9 typing | GAP (B2) |
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
| AC-4.2 | K format refusal; P (C3) | COVERED |
| AC-5.1 | F:sscs token info; T host; R base | COVERED |
| AC-5.2 | F:package registry; T both; R send | COVERED |
| AC-5.3 | F:package no-token cases | COVERED |
| AC-6.1 | N `header_problems` | COVERED |
| AC-6.2 | F:sscs, F:openapi_only; T; R | COVERED |
| AC-6.3 | K undeclared header (C1) | COVERED |
| AC-7.1 | F:gitlab_dedicated; K S3 refusal | COVERED |
| AC-7.2 | N two-level member | COVERED |
| AC-8.1 | N record, send, readings (C4) | COVERED |
| AC-8.2 | N request header | COVERED |
| AC-8.3 | the main-run examples and refusals | COVERED |
| AC-9.1 | C and K docstring tests | COVERED |
| AC-9.2 | `test_llm_map_within_cap` only | GAP (B1) |
| UB-1 | existing suites; D9; R NuGet repeat | COVERED |
| UB-2 | P stdlib (rglob); K no token option; C config; T; F:package | COVERED |
| UB-3 | K refusals; S3 gate; diff | COVERED |
| UB-4 | GitHub suites in CI; diff | COVERED |

Counts: 0 A, 2 B, 5 C, 1 D; 28 COVERED, 2 GAP.

Verdict: NOT-READY
