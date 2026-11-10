# Evidence report — issue #17: GitHub wrapper rewrite, part 1

Tier M, five waves plus one verification rework. Branch `issue-17-github-wrapper-foundation`, PR #26.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 records refuse an undocumented parameter; `.`/`..` segments refused | R `test_github_api_registry.py` | red/green wave-2 | green |
| AC-1.2, AC-1.3, AC-5.1–AC-5.3 one module per family, every operation covered or pending, a gap named | V `test/test_github_wrapper_coverage.py` | red/green wave-3 | green |
| AC-2.1–AC-2.4 API version on every request, `Link` paging incl. wrapped lists, uploads to `upload_url` | T `test_github_api_transport.py` | red/green wave-1 | green |
| AC-3.1–AC-3.4 cross-origin redirect drops the credential, rate limits waited and retried boundedly, error bodies | T; rework R3 (non-integer rate header) | wave-1; green/rework-1.txt | green |
| AC-4.1–AC-4.3 GraphQL query + variables, cursors, `errors` at 200 | T | wave-1 | green |
| UB-1.1 today's subcommands keep arguments, requests, stdout, exit codes | C `test_github_wrapper_compat.py` over 226 `CASES` rows; P fork parity (goldens are the installed wrapper's; parsers match option by option); rework R2 rows | red/green wave-4, wave-5; rework-1 | green |
| UB-1.2 delivery verbs reach the steward unchanged | `test_wrapper_delivery.py` unedited; C | wave-4, wave-5 | green |
| UB-1.3 the setup prompts copy `github_api/` with the entry script | S `test/test_setup_prompts_github_wrapper.py`; rework R1 (the copy instruction itself) | wave-5; rework-1 | green |
| UB-2.1, UB-2.2 credential only from the file; stdlib-only imports, no environment reads | C; V | wave-4, wave-3 | green |
| UB-3.1, UB-3.2 GitLab wrapper and delivery test untouched; the module loads without credential or network | F.2 diff check; C | verify | green |

Green captures: wave 5 809 passed; rework 618 passed. Local `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.** First pass REFUTED R1 (Part 5.3's copy clause deletable with the test green), R2 (`--limit <= 0` and a non-UTF-8 credential file never run), R3 (a non-integer rate header never sent); about 35 other mutants across the five waves were killed. The test side was reopened (DL-005); the re-verification killed every R1–R3 mutant and returned VERIFIED (`evidence/verify/refutation-report.md`).

**Whole suite.** CI run 42903402594 success on 95fc3b8; CI run 42911144152 success on faa6ceb (the rework head).

**Deferred.** The real-forge run on an `sff-test-*` repository moved to #10 (DL-006), which owns the fixture.
