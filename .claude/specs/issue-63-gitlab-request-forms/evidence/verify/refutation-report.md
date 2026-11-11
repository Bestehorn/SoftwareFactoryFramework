# Refutation report — issue #63 (tier M, PR #66, head 43ba0f1 on origin/main 6beeb77)

Method: whole suite from CI. Reverts and mutants ran in a detached worktree of 43ba0f1 (removed after), through
`scripts/run_tests.py` on named files: paired tests, then every GitLab suite (926 tests) for each survivor. Bytes
restored, sha256 `match=True` in all 81 restore lines. Captures: `evidence/verify/`.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the head | `wait-run`/`get-run`/`get-jobs` 43070929100: head_sha 43ba0f1; lint, types, security, tests, report success; 3663 passed, hook suite 1053 | FAILED-TO-REFUTE | full-suite.txt |
| 2 | Wave 1 tests need wave 1 | at ce555f6, registry.py and transport.py to 6beeb77, container_registry.py removed: 27 failed (R 6, T 16, P 3, G 1, N 1), the ids of red/wave-1 | FAILED-TO-REFUTE | mutant-wave-1.txt |
| 3 | Wave 2 tests need wave 2 | call.py, container_registry.py, transport.py, 11 families to ce555f6: 82 failed (K 16, F 61, N 5), the ids of red/wave-2 | FAILED-TO-REFUTE | mutant-wave-2.txt |
| 4 | Wave 3 tests need wave 3 | gitlab_wrapper.py, map, ledger to 8922465: 2 failed (C usage, N map) | FAILED-TO-REFUTE | mutant-wave-3.txt |
| 5 | Restored tree green | wave 3 Run line at 43ba0f1 after every mutant: 1030 passed | FAILED-TO-REFUTE | mutant-restored-green.txt |
| 6 | UB-2: configured token only to the configured origin; registry request carries only the registry token | 6 mutants (configured credential to the registry or /jwt/auth; origin check off or admitting the configured origin; registry token in URL or log): killed by T `test_a_registry_request_carries_only_the_registry_token`, `test_the_registry_token_is_asked_for_with_basic_credentials`, `test_next_url_on_another_origin_is_refused`, G, F:package | FAILED-TO-REFUTE | mutant-sec-*.txt |
| 7 | D5: `--header`/headers cannot be PRIVATE-TOKEN, JOB-TOKEN, Authorization, Host, Content-Length | 5 name mutants: killed by T `test_a_request_header_is_sent_beside_the_transport_headers` | FAILED-TO-REFUTE | mutant-sec-header-name*.txt |
| 8 | D5: CR, LF, NUL refused | CR, LF, NUL each dropped, and the check off: killed by the same T test | FAILED-TO-REFUTE | mutant-sec-header-value-*.txt |
| 9 | UB-3/D6: S3 import gated, `None` | entry removed; mapped to a subcommand: killed by K `test_the_s3_import_is_refused` | FAILED-TO-REFUTE | mutant-sec-s3-*.txt |
| 10 | D4 step 2 refuses `@`, `#`, empty | each dropped: killed by F:package `test_no_registry_token_sends_nothing_to_the_registry` [userinfo], [fragment], [without-a-host] | FAILED-TO-REFUTE | mutant-sec-step2-{at,fragment,empty}-allowed.txt |
| 11 | D4 step 2 refuses `?`, `\`, white space | each dropped: 926 passed | REFUTED RF-1 | mutant-sec-step2-{query,backslash,whitespace}-allowed[-full].txt |
| 12 | D4 step 1: `GET /user` without a username raises | `_answer_text` bypassed: 926 passed | REFUTED RF-2 | mutant-ac53-username-unchecked[-full].txt |
| 13 | D4 step 3: a refused /jwt/auth answer is never quoted, its body never kept | body put in the message; non-JSON branch re-raised with the body as details: 926 passed each; transport.py 289-291 unexecuted in CI | REFUTED RF-3 | mutant-sec-jwt-*[-full].txt |
| 14 | AC-5.2/5.3 rest | jwt token unchecked, bearer logs in, job looks up user, steps reordered, scope wrong, scope unwritten, no project: killed by F:package, G, T, R `test_send_fetches_the_registry_token_before_the_registry` | FAILED-TO-REFUTE | mutant-ac5*.txt, mutant-f4-*.txt |
| 15 | F1: `lookup(endpoint=)` exact; undeclared refused | default last, fall back, case-folded, trailing `/`, same-key twice, two families, send/call ignore endpoint, `endpoint_key` unchecked: killed by R `test_lookup_chooses_an_endpoint_of_a_reference`, `test_lookup_refuses_unknown_and_duplicate_ids`, P `test_only_a_declared_endpoint_is_chosen`, K `test_an_endpoint_*`, F:plan, F:sscs | FAILED-TO-REFUTE | mutant-f1-*.txt |
| 16 | F2: each place its own value; wrong counts refused | first value everywhere, reversed, extra accepted, surplus/missing/once in call, record field dropped: killed by R positional, P `test_each_place_takes_its_own_value`, F:create, F:tenant_scale, K `test_a_two_value_path_given_one_value_is_refused`, N | FAILED-TO-REFUTE | mutant-f2-*.txt |
| 17 | F3: only listed formats | expand any, call any, case-folded, left literal: killed by P `test_only_a_listed_format_reaches_the_path`, K `test_a_format_the_page_does_not_list_is_refused`, R, F:create | FAILED-TO-REFUTE | mutant-f3-*.txt |
| 18 | F5/AC-6.1 | not encoded, transport drops, case-sensitive, `-f` gives a header, Symbolchecksum dropped: killed by R, T, K, F:sscs, F:openapi_only, N `test_a_request_header_is_read_and_sent_as_written` | FAILED-TO-REFUTE | mutant-f5-*.txt, mutant-ac61-*.txt |
| 19 | F6: two-level names sent in full | name truncated; S3 body JSON: killed by F:gitlab_dedicated `test_the_s3_import_sends_every_member_at_its_name`, N `test_a_two_level_member_is_read_and_sent_as_written` | FAILED-TO-REFUTE | mutant-f6-*.txt |
| 20 | AC-1.1, AC-1.2, AC-2.3 records | `/version` record dropped, F1 copy loses a Param, literal path changed: killed by V, N `test_each_record_of_an_id_copies_its_base_record`, F:verify, F:developer_experience | FAILED-TO-REFUTE | mutant-ac1*.txt, mutant-ac23-*.txt |
| 21 | UB-2: standard library, no environment | third-party import; `os.environ` read: killed by P `test_standard_library_only` | FAILED-TO-REFUTE | mutant-ub2-*.txt |
| 22 | D4/D5: `pages` refuses a non-REST base and request headers | each check off: 926 passed; registry.py 935, 945 unexecuted | REFUTED RF-4 | mutant-f4-pages-any-base[-full].txt, mutant-f5-pages-headers-accepted[-full].txt |
| 23 | DL-009: registry record refuses body/file/header/bytes | check off: 926 passed; registry.py 805 unexecuted | REFUTED RF-5 | mutant-dl009-*[-full].txt |
| 24 | Coverage of new lines | CI coverage of 43ba0f1: registry.py 484, 499 (D2 `_described`, `_place_values`), 774, 779 (D4 `_scope`) unexecuted | REFUTED RF-6 | full-suite.txt |
| 25 | Vacuity | AST scan, 202 test functions of the 18 changed test files: 0 without assert/raises; no skip, xfail, importorskip; no pyproject/conftest change | FAILED-TO-REFUTE | — |
| 26 | Red for the right reason | red/wave-1..3 and the regenerated captures: AssertionError, or TypeError/AttributeError raised in test bodies; no import or collection error | FAILED-TO-REFUTE | red/*.txt, mutant-wave-*.txt |
| 27 | F.2 | `git diff --name-only origin/main...HEAD` names no GitHub file; test_github_api_*, test_wrapper_delivery ran green in run 43070929100 | FAILED-TO-REFUTE | full-suite.txt |
| 28 | F.3 | outside the spec: only D12's files; no Not-edited file; removed assertions only in D9's tests and N's send loop; GATED_OPERATIONS +1 line, the S3 import | FAILED-TO-REFUTE | diff |

## Refutations

- RF-1 AC-5.3 / D4 step 2: no test pins the refusal of `?`, `\` or white space in the registry host.
- RF-2 AC-5.3 / D4 step 1: no test pins the refusal of a `GET /user` answer without a username.
- RF-3 AC-5.3, UB-2 / D4 step 3: no test pins "never quoting its body": both mutants pass; the non-JSON branch is unexecuted.
- RF-4 AC-5.1, AC-6.3 / D4, D5: `pages`' base and header refusals are unexecuted; a mutant disabling either passes.
- RF-5 UB-3 / DL-009: the container-registry body/file/header/bytes refusal is unexecuted (DL-009 records that no test reaches it).
- RF-6 AC-3.3, AC-5.2 / D2, D4: four new refusal lines that no test executes.

Every other claim survived: 61 of 70 mutants killed, the 9 survivors above.

## Tree

Temporary worktree removed and pruned; `tmp/` empty; `git status --porcelain` lists only `evidence/verify/`; HEAD
43ba0f1. A placeholder written by mistake into the main checkout's `.claude/specs/` was removed with the directories
it created; that checkout's status matches its start. Nothing committed.

Refuted: RF-1 RF-2 RF-3 RF-4 RF-5 RF-6
Verdict: REFUTED
