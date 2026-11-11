# Refutation report 2: issue #42 delta re-verification (head 041980e, PR #55)

Run 2026-11-11 in `.claude/worktrees/issue-42`. The head is the rework commit cd2227f (DL-009, five
`test_every_body_is_json_and_unfixed` tests) plus a merge of origin/main 25c91d3. Round 1
(`refutation-report.md`) was REFUTED on AC-3. Every capture below was regenerated; no prior evidence was trusted.
Mutants were applied by single-occurrence anchors through a disposable harness in the main checkout's `tmp/`, run
through `scripts/run_tests.py`, then each module was written back from its baseline bytes with its mtime, and the
sha256 compared to the pre-run value. The ten paired files: F x5, C, K, N, V, P (255 items: 250 + the 5 new tests).

## Procedure

| Step | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Suite green on the SHA | wrapper `get-run 42990143891`, `get-jobs`, `get-job-logs 130420733980` | FAILED-TO-REFUTE: head_sha = worktree HEAD 041980e; 5/5 jobs success; 3073 passed; five modules 6 stmts 0 miss | `full-suite-2.txt` |
| 2 | The AC-3 `body`/`fixed` clause has a killing test (round 1's gap) | harness group `body1`, `body2`, ten files per mutant | FAILED-TO-REFUTE: 10/10 KILLED (table below) | `mutant-rework-2a.txt`, `mutant-rework-2b.txt` |
| 2 | The new tests are not vacuous | harness group `empty`: `OPERATIONS = ()` inserted before `PENDING` in each module, its F run | FAILED-TO-REFUTE: in all five F, `test_every_body_is_json_and_unfixed` fails on its `assert records` guard (`...OPERATIONS declares no record, so no body or fixed is checked (AC-3)`) | `mutant-empty-2.txt` |
| 2 | First-round claims stand after the merge | harness group `spot`, one mutant per module, ten files | FAILED-TO-REFUTE: 5/5 KILLED (table below) | `mutant-spot-2.txt` |
| 2 | Restored tree green | harness group `green`, ten files | 255 passed, exit 0; ten watched files bytes and mtime equal to baseline | `green-after-restore-2.txt` |
| 3 | No vacuous test in the change | Grep of the five F files for `pytest.skip`, `xfail`, `skipif`, `importorskip`, commented `def test_`/`assert`; rework diff; pyproject `addopts` | FAILED-TO-REFUTE: no match; the rework diff adds one plain function per F, no mark; `addopts = "-ra --import-mode=importlib"`; the new test is collected and fails in every mutant run above | this file |
| 4 | Red for the right reason | Grep of the mutant captures | FAILED-TO-REFUTE: the rework is test-only against already-compliant records, so its red proof is the mutant runs; every failure of the new test is an `AssertionError` naming the offending record (`<id>: body <BodyFormat.FORM: 'form'>, fixed ()` or `fixed (('per_page', '100'),)`), no import or collection error | `mutant-rework-2a.txt`, `mutant-rework-2b.txt` |
| 5 | Changed lines exercised | CI `--cov` term-missing for the five F files | FAILED-TO-REFUTE: the missed lines (sys.path insert, fixture loader, the `ModuleNotFoundError` branch, the difference helpers) lie outside every `test_every_body_is_json_and_unfixed`; modules 100% | `full-suite-2.txt` |
| scope | Rework commit touches only F, the capture, verify evidence, decision log | `git show --name-status cd2227f` | FAILED-TO-REFUTE: five F files (M), `evidence/green/rework-1.txt` (A), `evidence/verify/{full-suite,green-after-restore,mutant-wave-1}.txt`, `refutation-report.md` (A), `decisions/decision-log.md` (M, DL-009 appended); no module, no other path | this file |
| scope | Merge changes no line of the five modules or their F | `git diff --stat cd2227f 041980e -- <the ten files>`; `git diff --name-only 25c91d3 041980e` vs `3beba95 cd2227f` | FAILED-TO-REFUTE: empty diff; the PR's net diff against its base is the same 25 paths as the pre-merge change (spec dir, ledger, five modules, five F); no UB-4 file | this file |

## Body and fixed mutants (all ten paired files run)

| Id | Module, mutation | Killed by | Result |
|---|---|---|---|
| B1 | factory, `body=BodyFormat.FORM` on `#update-the-secret_push_protection_enabled-setting` | F factory new test only (1 failed, 254 passed) | FAILED-TO-REFUTE |
| B3 | factory, `fixed=(("project", "x"),)` on `#retrieve-a-single-license-template` | F factory new test only | FAILED-TO-REFUTE |
| S1 | sscs, `body=BodyFormat.FORM` on `#create-a-user` (FILE `avatar`) | F sscs new test only | FAILED-TO-REFUTE |
| V1 | sscs near-variant, `body=BodyFormat.FORM` on part 1's `#as-a-regular-user` (`GET /users`, paged) | F sscs new test only | FAILED-TO-REFUTE |
| G1 | governance, `body=BodyFormat.FORM` on `#update-group-security-settings` | F governance new test only | FAILED-TO-REFUTE |
| V2 | platform near-variant, `fixed=(("per_page", "100"),)` on paged `#list-all-projects-in-a-cicd-job-token-allowlist` | F platform new test only; its AC-7 URL case passes, as the transport adds no `per_page` when the query holds one (`gitlab_api/transport.py`, the OFFSET `PARAM_PER_PAGE` clause) and N accepts a fixed name that is a query row | FAILED-TO-REFUTE |
| P2 | platform, `body=BodyFormat.FORM` on `#update-the-cicd-job-token-access-settings-for-a-project` | F platform new test only | FAILED-TO-REFUTE |
| R1 | risk, `body=BodyFormat.FORM` on `#create-an-organization-policy` (HASH, ARRAY rows) | F risk new test only | FAILED-TO-REFUTE |
| V3 | risk near-variant, `fixed=(("per_page", "100"),)` on paged `#list-all-group-policies` | F risk new test only; AC-7 case passes | FAILED-TO-REFUTE |
| G2 | governance, `fixed=(("secret_push_protection_enabled", "true"),)` | F governance new test; N `test_every_record_matches_its_reference_section`, `test_every_record_is_sent_as_its_section_documents` (a body row as fixed) | FAILED-TO-REFUTE |

## First-round spot checks after the merge (ten files)

| Id | Claim | Mutation | Killed by |
|---|---|---|---|
| X1 | AC-4 kind | factory `package_manager` ARRAY->SCALAR | F `test_every_kind_is_its_rows_type` |
| X2 | AC-5 | sscs `#list-all-token-associations` NONE->OFFSET | F `test_every_list_record_has_a_case` |
| X3 | AC-5, AC-7 | platform `#list-all-attestations` OFFSET->NONE | F `test_every_list_record_has_a_case`, `test_a_list_record_prints_every_item[list-all-attestations]` |
| X4 | AC-1, AC-6 | risk `#retry-failed-status-check-for-a-merge-request` POST->PUT | F `test_every_key_has_its_record`; N both record tests; V `test_every_declared_key_is_in_its_family`, `test_every_index_row_is_mapped_or_pending` |
| X5 | AC-4 required | governance `secret_push_protection_enabled` required true->false | F `test_the_required_attributes_are_the_sections` |

All five FAILED-TO-REFUTE. Round 1's AC-3 refutation is closed: B1 and B3, which survived round 1 with 250 passed,
now each fail exactly the new test.

## Tree

Each `# restored` line in the captures reads `equal to the baseline: True`; each capture ends with ten `# final ...
bytes and mtime equal to the baseline: True` lines. After the run `git diff --quiet HEAD` exits 0 and
`git status --porcelain` lists only the six new files of this round in `evidence/verify/` (`full-suite-2.txt`,
`mutant-rework-2a.txt`, `mutant-rework-2b.txt`, `mutant-empty-2.txt`, `mutant-spot-2.txt`,
`green-after-restore-2.txt`) and this report. The harness directory in the main checkout's `tmp/` is deleted. No
`git checkout` or `git stash` was used. Tree restored.

Verdict: VERIFIED
