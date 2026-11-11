# Refutation report: issue #42, GitLab security records (head 2c4c872, PR #55)

Run 2026-11-11 in `.claude/worktrees/issue-42`. The change is `3beba95...HEAD` (3beba95 is the merge base with
origin/main; CI tested the PR merge onto d30d022). Every capture here was regenerated; prior `evidence/` was read
only for the red audit. Mutants were applied by single-occurrence anchors, the ten paired files (F x5, C, K, N, V, P)
run through `scripts/run_tests.py`, then bytes and mtime restored and sha256 checked against the pre-run baseline.

## Procedure

| Step | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Suite green on the SHA | wrapper `get-run 42980759363`, `get-jobs`, `get-job-logs 130390361960` | FAILED-TO-REFUTE: head_sha = worktree HEAD; 5/5 jobs success; 3001 passed; five modules 100% covered | `full-suite.txt` |
| 2 | Wave 1 tests need the wave (W0: five modules reverted to 3beba95) | `run_tests.py` ten files | FAILED-TO-REFUTE: 71 failed (every F test), 179 passed | `mutant-wave-1.txt` W0 |
| 2 | Restored tree green | `run_tests.py` ten files | 250 passed, exit 0; 46/46 restores equal baseline | `green-after-restore.txt` |
| 3 | No vacuous test | Grep of the five F files and the diff | FAILED-TO-REFUTE: no skip/xfail/mark beyond parametrize; parametrizations are literal non-empty tuples (2, 4, 9, 31 list cases); governance has none by design; no pytest config in the diff | this file |
| 4 | Red for the right reason | Grep of `evidence/red/wave-1.txt` | FAILED-TO-REFUTE: 71 failed, each an `AssertionError` on a table or on `call` exiting 2; no import or collection error; W0 reproduces the same 71 | `mutant-wave-1.txt` W0 |
| 5 | Changed lines exercised | CI `--cov` term-missing | FAILED-TO-REFUTE: each module 6 stmts, 0 miss; every record field a new line sets is asserted by F or N (mutants below) | `full-suite.txt` |

## Targeted mutants (all in `mutant-wave-1.txt`)

| Claim | Mutants | Result |
|---|---|---|
| AC-1 | W0; PE3 PE4 PE5 PE7 PE8 (mapped key put on PENDING, four modules); N7 method POST->PUT; N8 ID renamed; N9 path placeholder renamed | FAILED-TO-REFUTE: all KILLED (F `test_every_key_has_its_record` / `test_only_the_unmapped_keys_are_pending`, V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family`) |
| AC-2 | PE1 `PATCH /user/status`, PE2 `GET https://HOST/oauth/token/info`, PE6 `POST /pipelines/:id/dependency_list_exports` taken off PENDING | FAILED-TO-REFUTE: KILLED by F pending test and V |
| AC-3 names, In | N1 body `provider` dropped (sscs), N2 query `pipeline_id` dropped (srm), N3 body `operation` dropped (platform), N4 query `fullname` dropped (factory), N5 rename, N6 QUERY->BODY, N10 rename (governance) | FAILED-TO-REFUTE: KILLED by N `test_every_record_matches_its_reference_section` |
| AC-3 `body` JSON, no `fixed` | B1 `body=BodyFormat.FORM` on `security-factory#update-the-secret_push_protection_enabled-setting`; B3 `fixed=(("project", "x"),)` on `security-factory#retrieve-a-single-license-template` | **REFUTED**: both SURVIVED, 250 passed, exit 0. B2 (`fixed` on the paged `#list-all-license-templates`) died only on the AC-7 URL check. No test checks a family record's `body` or an empty `fixed`: N only requires a fixed name to be a query row (Grep `BodyFormat`, `.fixed` over every test tree). The shipped records comply (no `body=`, `fixed=` in the five modules); the clause has no test. |
| AC-4 Kind | K1 FILE->SCALAR `create-a-secure-file` `file`; K2 FILE->SCALAR `create-a-user` `avatar`; K3 ARRAY_OF_HASHES->SCALAR; K4, K6 ARRAY->SCALAR; K5 HASH->SCALAR; K7 SCALAR->ARRAY; K8 ARRAY->HASH | FAILED-TO-REFUTE: KILLED by each module's F `test_every_kind_is_its_rows_type` |
| AC-4 required | R1 R3 R5 R6 true->false; R2 R4 R7 false->true (R2, R7 on `conditional` rows) | FAILED-TO-REFUTE: KILLED by F `test_the_required_attributes_are_the_sections` |
| AC-5 | P1 P2 OFFSET->NONE (P2 = `#retrieve-project-external-status-check-services`); P3 P4 NONE->OFFSET (`#list-all-token-associations`, `#list-all-project-security-settings`); P5 OFFSET->KEYSET; P6 P7 NONE->OFFSET | FAILED-TO-REFUTE: KILLED by F `test_every_list_record_has_a_case` |
| AC-6 | N5 N6 N7 N8 N9 N10 | FAILED-TO-REFUTE: KILLED by N `test_every_record_is_sent_as_its_section_documents` |
| AC-7 | P1 P2 P5, W0 | FAILED-TO-REFUTE: KILLED by F `test_a_list_record_prints_every_item[...]` |
| UB-1 | U1 `#as-a-regular-user` drops `username`; U2 `#as-a-regular-user-1` path `/user/me`; diff hunks | FAILED-TO-REFUTE: KILLED by C `test_a_subcommand_form[issue-assign-user]`, `[issue-start]` and others; neither part 1 record lies in a diff hunk |
| UB-2 | K's `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`, `test_a_body_that_is_not_json_is_written_unchanged` in the green run; K not in the diff | FAILED-TO-REFUTE |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`, P `test_standard_library_only` in the green run; module imports: `__future__`, `typing`, `gitlab_api.registry` | FAILED-TO-REFUTE |
| UB-4 | `git diff --name-only 3beba95 HEAD` names no UB-4 file; CI suite green | FAILED-TO-REFUTE |

## Reference spot-check and ledger

63 sections read against their records (method, path, every query/body/form row, In, Type->Kind, Required): 30 on
`rest/software-supply-chain-security.md` (among them update-application-appearance's four "file upload" rows as FILE,
create-an-application `scopes` string SCALAR with `granular_scopes` ARRAY_OF_HASHES, create-a-user 34 rows with
`avatar` FILE, modify-a-user 32 rows, create-an-impersonation-token `conditional` not required,
list-all-token-associations, update-extern_uid with path rows only, revoke-a-token query `token`, set-your-user-status
PUT recorded and PATCH pending), all 5 of `security-factory.md`, the 1 of `security-governance.md`, 17 of
`security-platform.md` (create-a-secure-file `file` form FILE required) and 10 of `security-risk-management.md`
(create-a-dependency-list-export recording `/projects/:id/`, create-an-organization-policy `rules` ARRAY required and
`policy_scope` HASH, list-all-project-vulnerability-findings string arrays). Every one matches. Ledger: three rows
added, 227, 221 and 202 bytes, no CR, each within 240.

## Tree

The harness was a disposable script in the main checkout's `tmp/`, now deleted. After the run the module sha256 values
equal the baseline, `git diff --quiet HEAD` exits 0, and `git status --porcelain` lists only this directory
(`evidence/verify/`). Tree restored.

Verdict: REFUTED (AC-3)
