# Evidence report — issue #13: GitLab wrapper rewrite, part 1

Tier M, five waves (wave 5 in two parts, DL-005), one absorbed fix (DL-006) and one verification rework (DL-007).
Branch `issue-13-gitlab-wrapper-foundation`, PR #34.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 records, lookup by id, undeclared value refused | R `test_gitlab_api_registry.py` | red/green wave-1, wave-2 | green |
| AC-1.2, AC-5.1, AC-5.2 a family module discovered alone; the checker names each unlisted row | V `test/test_gitlab_wrapper_coverage.py` | wave-1 | green |
| AC-1.3, UB-3 no GitHub wrapper file, delivery test untouched | F.2 diff check; `test_wrapper_delivery.py` | verify | green |
| AC-2.1 one credential header per token type | T `test_gitlab_api_transport.py` | wave-2 | green |
| AC-2.2, AC-2.3 one-segment path values; array, hash and array-of-hash pairs in query and form | R; P `test/test_gitlab_api_properties.py`; rework T form body | wave-1, wave-2; green/rework-1.txt | green |
| AC-2.4–AC-2.6, AC-3.1–AC-3.5, AC-4.1–AC-4.3 multipart, paging, origin, redirects, 429, error shapes, GraphQL | T | wave-2 | green |
| AC-5.3, AC-5.4 every index row mapped or pending | V over the real index | wave-3 | green |
| UB-1 today's subcommands, exit codes, `pipeline wait`, the template | C `test_gitlab_wrapper_compat.py`; S `test/test_setup_prompts_gitlab_wrapper.py` | wave-3, 4, 5a, 5b | green |
| UB-2 config-only credential, stdlib-only, no environment reads | C; P (rework: AST check) | wave-3, 4; rework-1 | green |
| DL-006 file-list checks batched under the Windows cap | RC `test_run_checks.py` (rework: console-script head, exit 127) | red/green run-checks-batching; rework-1 | green |

Green captures: wave 5b 351 passed; rework 253 passed. Local `run_checks.py --group lint --group types --group security`
(product copy): 5 passed, 0 failed, detect-secrets as 2 commands.

**Verifier.** First pass: 61 mutants, 54 killed; REFUTED AC-2.3 (the form-body branch never ran) with observations O1
(environment guard missed from-imports) and O2 (two batching paths untested). Rework DL-007 added the tests; the
re-verification killed 2q, x1, 2p, z1, w1 and returned VERIFIED (`evidence/verify/refutation-report.md`). O4 — a
string-named `getattr(os, "environ")` is not caught by the name scan; no shipped file holds such a construct.

**Whole suite.** CI run 42918925603 success on c3efdcb; CI run 42924782796 success on 9e78001 (the rework head).
