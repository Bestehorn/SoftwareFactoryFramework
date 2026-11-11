# Test architect — design review, iteration 03 (delta)

Reviewed: `git diff 8fe5ae0 dfeae41` of `design.md` (`requirements.md` is unchanged in that range), the
iteration-02 fix sites, `src/payload/test/gitlab_wrapper_fixtures.py`, `test/test_gitlab_wrapper_contract.py`,
`test/test_gitlab_graphql_contract.py` and `docs/forLLMConsumption.md`.

## Iteration-02 findings

| ID | Status | Evidence |
|---|---|---|
| B3 | Resolved | AC-9.2's N `test_the_map_names_the_request_forms` now pins AC-9.1's five spellings: `--endpoint`, two `--path id=`, `--path format=`, `--header` and `override_params[container_expiration_policy_attributes]`. These are the same strings that C's and K's docstring tests pin. D11 names the same forms ("the repeated `--path` (two `--path id=`)", "the two-level member's full name"). The current `gitlab_api/` bullet holds `--path` and none of the five strings, so the test is red on the base. `_map_bullet` (`test_gitlab_graphql_contract.py`) joins the bullet's lines, so the check still matches a command that wraps onto the next line. |
| C6 | Resolved | The oracle now requires that the judged IDs include `plan#add-an-emoji-reaction-to-a-resource` and `verify#get-the-latest-release`. D8 gives each of them more than one record: the plan emoji-reaction "…a resource" row, and the verify row's `…/permalink/latest/downloads/bin/asset.exe` and `…/evidence` keys. Each ID has one record on the base, so the test is red there, and it can no longer pass by grouping no ID. |
| C7 | Resolved | The oracle now says the recorded requests are exactly those of the steps up to the failing one, its own included. This matches D4's step table: `bearer` is refused at step 1 before any request, and a project answer is refused "before step 3". `FakeOpener` in `gitlab_wrapper_fixtures.py` appends every request that urllib hands to the handler, whatever its host, so the extra request is observable. If a run skips the `@` rule, it records step 3's `/jwt/auth`, and the `user@registry.example.com/x` case fails. |
| D2 | Resolved | G's oracle now reads "the `/jwt/auth` request's `Authorization: Basic` decodes to `gitlab-ci-token:<token>`". `RecordedRequest.header(name=)` reads that header without regard to case. |

These delta checks raised no finding:
- D7's `IN_HEADER` sits beside the existing N string constants `IN_PATH`, `IN_QUERY`, `IN_BODY` and `IN_FORM`. Comparing `location.value` means N never reads `Location.HEADER`, which the base lacks, so its red run fails on the assertions and not on an `AttributeError`.
- D7's red-phase sentence now also names #43's restated `test_only_the_upload_module_path_holds_a_hyphenated_name`. D9's last bullet and D12's N row (`D7, D9`) name the same edit, so UB-1's "every existing test but D9's" still holds.
- The Security "What stays callable" edit (every D8 record but the S3 import) agrees with AC-7.1's lifted-gate test and K's S3 refusal under UB-3.
- The longer map spellings fit under the cap. `docs/forLLMConsumption.md` measures 7,358 B, against `post-activity.md`'s 40,000-byte cap that `test_llm_map_within_cap` enforces.

## New findings

None.

## Coverage

| Criterion | Tests | Status |
|---|---|---|
| AC-1.1 | V both; D9 pending literals | COVERED |
| AC-1.2 | N record test, N base-record test (red on the base); D9 typing | COVERED |
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
| AC-5.2 | F:package (with step-4 `404`); T both; G job token (`/jwt/auth` Basic); R send | COVERED |
| AC-5.3 | F:package no-token cases (exact per-step request list) | COVERED |
| AC-6.1 | N `header_problems` | COVERED |
| AC-6.2 | F:sscs, F:openapi_only; T; R | COVERED |
| AC-6.3 | K undeclared header | COVERED |
| AC-7.1 | F:gitlab_dedicated (gate lifted); K S3 refusal | COVERED |
| AC-7.2 | N two-level member | COVERED |
| AC-8.1 | N record, send, readings; N two-level for the gated S3 record | COVERED |
| AC-8.2 | N request header | COVERED |
| AC-8.3 | the main-run examples and refusals | COVERED |
| AC-9.1 | C and K docstring tests | COVERED |
| AC-9.2 | N map test (all five forms); `test_llm_map_within_cap` | COVERED |
| UB-1 | existing suites; D9 incl. #43 N; R NuGet repeat; R call fake `lookup` | COVERED |
| UB-2 | P stdlib; K no token option; C config; T; F:package | COVERED |
| UB-3 | K refusals; S3 gate | COVERED |
| UB-4 | GitHub suites in CI; diff | COVERED |

Counts: 0 A, 0 B, 0 C, 0 D; 30 COVERED, 0 GAP.

CLEAN

Verdict: READY
