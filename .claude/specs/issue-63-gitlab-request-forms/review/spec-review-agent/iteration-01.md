# spec-review-agent — design iteration 01 (issue #63, tier M)

Reviewed: `requirements.md`, `design.md`, `decisions/decision-log.md` DL-001..DL-004, against `origin/main` 252c21e
(`registry.py`, `transport.py`, `commands/call.py`, N, V, the family test modules, `gitlab_wrapper_fixtures.py`), #43's
approved design, and `docs/api-reference/gitlab/`.

### B1 — D1 hands `endpoint` to a `lookup` that an existing R test replaces with a one-argument fake
Severity: B
Location: design.md § D1 ("`send`, `call` and `pages` gain `endpoint=None` and pass it to `lookup`"); § D9
Defect: R `test_call_refuses_an_undeclared_value` monkeypatches `registry.lookup` with `def lookup(*, operation_id)`, so `registry.call` (and the `send` it calls) passing `endpoint=None` to it raises `TypeError`, not the `ValueError` the test asserts; D9 does not list the test.
Material-because: UB-1 (the existing tests of `src/payload/test/test_gitlab_*.py` continue to pass; this one pins nothing the change retires) — regression.
Proposed-edit: replace "`send`, `call` and `pages` gain `endpoint=None` and pass it to `lookup`." with "`send`, `call` and `pages` gain `endpoint=None`; each calls `lookup(operation_id=...)` when it is `None` and `lookup(operation_id=..., endpoint=...)` otherwise, so R `test_call_refuses_an_undeclared_value`, whose `lookup` takes `operation_id` alone, passes unedited."

### B2 — D3 and D4 change `placeholders` on two index rows that #43's N test pins
Severity: B
Location: design.md § D3 "The functions" (`placeholders` also names each suffix), § D4 "The base" (`placeholders` reads the rest; each `${NAME}` a path parameter), § D9; requirements.md § UB-1
Defect: #43's approved N `test_only_the_upload_module_path_holds_a_hyphenated_name` (#43 design.md Correctness Properties, UB-4) asserts that for every row of `operations-index.md` `registry.placeholders` equals what #40's pattern `[:*](?P<name>[A-Za-z_][A-Za-z0-9_]*)` finds; after D3 the `archive[.format]` row gives `("id", "format")` where the pattern finds `("id",)`, and after D4 the delete-by-reference row gives `("CI_REGISTRY_IMAGE", "CI_COMMIT_SHORT_SHA")` where it finds `()`. D9 does not list the test, and UB-1's exception names no such class.
Material-because: UB-1 — an existing N test fails, and editing it falls outside UB-1's exception; regression.
Proposed-edit: D9's last bullet becomes "#43's F `test_nothing_is_pending_but_the_kept_keys` and `test_a_two_endpoint_entry_maps_its_first_endpoint`, and #43's N `test_only_the_upload_module_path_holds_a_hyphenated_name`, whose rule gains two exceptions beside `package#upload-module`: the `archive[.format]` row gives `("id", "format")`, the delete-by-reference row `("CI_REGISTRY_IMAGE", "CI_COMMIT_SHORT_SHA")`"; UB-1's parenthetical becomes "(a key's pending state, one record per ID, a JSON-only body, a table without `Symbolchecksum`, a path's parameters read as `:name` and `*name` alone)".

### B3 — D9 omits gitlab_dedicated's `test_every_reference_has_its_record`
Severity: B
Location: design.md § D9, second bullet and "Every other existing test … passes unedited"
Defect: `test_gitlab_api_gitlab_dedicated.py` `test_every_reference_has_its_record` asserts `OPERATIONS` as `{id: (method, path)}` equals `RECORD_ENDPOINTS`, "every index row of the family but AC-2's four", the S3 import one of the four (`KEPT_PENDING`); D6's S3 record fails it, and D9 states it passes unedited.
Material-because: UB-1 — D9 is the design's enumeration of the assertions UB-1's exception lets this change restate, and it names this one unedited though AC-1.1 changes what it pins.
Proposed-edit: D9's second bullet: "`test_every_reference_has_its_record` of `developer_experience`, `fulfillment`, `tenant_scale` and `gitlab_dedicated` (its `RECORD_ENDPOINTS` gains the S3 import); `test_every_key_has_its_record` of …" (rest unchanged).

### C1 — AC-7.1 and AC-8.1 name a call the restated UB-3 refuses
Severity: C
Location: requirements.md § AC-7.1, § AC-8.1; design.md § D6 "The gate", § D7 closing paragraph
Defect: AC-7.1 ("WHEN a call of `gitlab-dedicated#import-a-project-from-an-aws-s3-bucket` gives … the body SHALL carry each") and AC-8.1 (every record passes `test_every_record_is_sent_as_its_section_documents`) describe a call that UB-3's gate refuses and a test that skips `GATED_OPERATIONS`; the design proves the body with the gate lifted.
Proposed-edit: AC-7.1 begins "WHEN the S3 import's record is called with `GATED_OPERATIONS` lifted (UB-3 refuses it otherwise) and given `override_params` members, …"; AC-8.1 adds "; a record `GATED_OPERATIONS` holds is sent by AC-7.2's test instead".

### C2 — D4's "never the answer's body" contradicts `_send` and Operability
Severity: C
Location: design.md § D4 "`_send(..., destination…)`" bullet; § Operability
Defect: step 3 is sent through `_send`, whose error-status refusal carries `error_text(body=response.text)` and `details=response.text`; D4 says step 3's errors never carry the answer's body, Operability says the exit carries GitLab's error text.
Proposed-edit: "step 3's errors name the URL, which holds the scope; an error status carries GitLab's error text as `_send` writes it, and a success answer without a usable `token` is refused without its body."

### C3 — K's "sent as `X-Gitlab-Nonce`" is not observable at the fake host
Severity: C
Location: design.md § Correctness Properties, AC-6.3 (K `test_an_undeclared_header_is_refused`)
Defect: `Request.add_header` stores a name `str.capitalize`d (the `transport.CREDENTIAL_HEADERS` comment: `Private-token`), so `FakeGitLab` records `X-gitlab-nonce` whatever spelling `encode` holds; the declared spelling is visible only in `EncodedRequest.headers`.
Proposed-edit: "`--header x-gitlab-nonce=n1` is accepted and the request carries `X-Gitlab-Nonce: n1` read with `RecordedRequest.header` (case-insensitive); R `test_a_header_param_is_encoded_as_a_header` holds `encode`'s pair for `x-gitlab-nonce` under `X-Gitlab-Nonce`."

### C4 — the external control's header `Param`s leave `required` unstated
Severity: C
Location: design.md § D8, the `software_supply_chain_security` F5 row; § D5 "The record"
Defect: D8 gives the NuGet downloads' header `required=True` but says only "with its headers" for the external control, whose `- Request headers:` line marks all three "(required)"; D9's `test_the_required_attributes_are_the_sections` literal depends on it.
Proposed-edit: the row's last cell ends "…`/status` key, with `Param(name=<name>, location=Location.HEADER, required=True)` for `X-Gitlab-Timestamp`, `X-Gitlab-Nonce` and `X-Gitlab-Hmac-Sha256` (each `(required)` on its `- Request headers:` line)".

### D1 — stale Residual
Severity: D
Location: design.md § Residuals, second bullet
Defect: "Requirements restatement owed: …" — DL-004 applied both; requirements UB-1 and UB-3 carry them.
Proposed-edit: delete that bullet.

### D2 — D12's `call.py` row omits symbols D5 changes
Severity: D
Location: design.md § D12, `commands/call.py` row
Defect: D5's case-insensitive header match changes `undocumented` and `_compared_name`, and header values reach `registry` through `call_values`; the row names none of them.
Proposed-edit: add `undocumented`, `_compared_name`, `call_values` to the row's list.

NOT-CLEAN (0 A, 3 B)
Verdict: NOT-READY
