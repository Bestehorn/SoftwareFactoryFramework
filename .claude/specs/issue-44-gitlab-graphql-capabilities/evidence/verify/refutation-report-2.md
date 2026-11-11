# Refutation report, round 2 (delta): issue #44 (PR #61, head 82aa3d9)

This round grades rework 6675399 (DL-009: five tests, no product change) and merge 82aa3d9 (origin/main 7c5b8b9). Every
mutant was an exact-once byte edit in the file's own CRLF bytes, made by a harness in the main checkout's
`tmp/verify-issue-44-r2/` (deleted after use). Before each edit the harness checked the file's sha256 against the
pre-run baseline. It wrote the original bytes and timestamps back in a `finally` block, and every restore printed
`identical=True`. P is G, R, T, Q, V and K (228 items), run through `scripts/run_tests.py --color=no` in the worktree.
P was green (228 passed) before the first mutant and after the last mutant of each of the three groups. Letters are as
in `tasks.md`.

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Suite green on the pushed SHA | wrapper `get-run`, `get-jobs` 43004808641; `get-job-logs` 130469520833 | FAILED-TO-REFUTE: completed/success; `head_sha` = worktree HEAD 82aa3d9; 5 of 5 jobs success; 3314 + 1053 passed on PR merge 6480038 (82aa3d9 into 7c5b8b9, an ancestor of 82aa3d9); no FAILED, SKIPPED or XFAIL line | full-suite-2.txt |
| M2j | Every paging record pages (AC-2.2) | P, round 1's 2j | FAILED-TO-REFUTE: killed, 1 failed (`test_every_paging_record_names_its_designed_connection`) | mutant-delta-2.txt |
| M2k | D1's `$input` mutation shape is held (AC-1.1) | P, round 1's 2k | FAILED-TO-REFUTE: killed, 1 failed (`test_every_mutation_document_has_the_designed_shape`) | mutant-delta-2.txt |
| M2r | A `--file` replaces a `-f`/`-F` value of the same name (AC-3.1) | P, round 1's 2r | FAILED-TO-REFUTE: killed, 2 failed (both rows of `test_a_file_replaces_a_field_of_the_same_name`) | mutant-delta-2.txt |
| M3f | The usage says which mutations are refused (AC-5.1) | P, round 1's 3f | FAILED-TO-REFUTE: killed, 1 failed (`test_the_usage_says_which_mutations_are_refused`) | mutant-delta-2.txt |
| COV | registry.py's untyped-definition branch is exercised (AC-3.1) | P, round 1's 1o; CI `--cov=src`; `git diff -U0 origin/main...HEAD` | FAILED-TO-REFUTE: 1o killed, 1 failed (`test_upload_variables_leave_out_a_definition_without_a_type`). CI's registry.py now misses only 224, 456 and 460. call.py and graphql_only.py are at 100%. No miss of registry.py, transport.py or gitlab_wrapper.py lies in an added hunk | mutant-delta-2.txt; full-suite-2.txt |
| V2j | Near variants of M2j | P: 2j-a Query.vulnerabilities' and 2j-b workItemsByReference's connection removed; 2j-c branchRules paged at `(branchRules,)`; 2j-d Query.vulnerability given a connection | FAILED-TO-REFUTE: all 4 killed by the connection test (2j-c and 2j-d also by Q) | mutant-variants-2.txt |
| V2k | Near variants of M2k | P: 2k-a workItemExport inline; 2k-b branchRuleCreate's `$in`; 2k-c pipelineCreate as `$input` (no `async: true`); 2k-d a second root field in branchRuleUpdate; 2k-e workItemDelete's `$input` nullable | FAILED-TO-REFUTE: all 5 killed by the shape test. 2k-a and 2k-b only by it; 2k-c to 2k-e also by Q | mutant-variants-2.txt |
| V2r | `--file` precedence for a list Upload | P: 2r-a a `-f`/`-F` value wins only over a list Upload's files; 2r-b a `-F` JSON list joined with the `--file` list | FAILED-TO-REFUTE: 2r-a kills both rows. 2r-b kills the JSON row; the `-f` text row passes, as it must, because 2r-b leaves text values alone | mutant-variants-2.txt |
| V3f | The refusal sentence reworded | P: 3f-a drops workItemsCsvImport; 3f-b drops workItemCreate; 3f-c says `exit 1` | FAILED-TO-REFUTE: all 3 killed by the refusal test (3f-c also by `test_the_usage_names_every_graphql_record`) | mutant-variants-2.txt |
| V1o | The untyped-definition branch, either side of it | P: 1o-a `continue` as `break`; 1o-b guard removed; 1o-c the untyped name as a non-list Upload; 1o-d `uploads.clear()` | FAILED-TO-REFUTE: all 4 killed by the R test. The test has an Upload before `$broken:` and one after it, so 1o-a loses the later one and 1o-d the earlier one. 1o-b raises `AttributeError` inside the product call | mutant-variants-2.txt |
| SPOT | Round 1's kills still die | P: 1a list flag inverted (wave 1, registry); 1m files dropped (wave 1, transport); 2b `errors` cut from `$input` (wave 2); 3a an ID dropped from the usage (wave 3) | FAILED-TO-REFUTE: 1a 9 failed, 1m 7, 2b 3 (now including the shape test), 3a 1 | spot-check-2.txt |
| VAC | The five new tests are not vacuous | the diff of 6675399; the captures above | FAILED-TO-REFUTE: one `@pytest.mark.parametrize` (2 constant rows) and no skip, xfail, deselect or commented test. The connection and shape tests assert a non-empty record set first. The oracles are the file's own constants, and `DESIGNED_CONNECTIONS` equals D1's query table. Each test fails under at least one mutant, and each failure-branch line CI lists as missed in G (698, 763, 774, 778, 784, 786) printed its message under a mutant | mutant-delta-2.txt, mutant-variants-2.txt |
| RED | The kills are assertion failures | the captures | FAILED-TO-REFUTE: the 33 failures are 32 `AssertionError` and one product `AttributeError` (1o-b), all in test bodies; no collection error | mutant-delta-2.txt, mutant-variants-2.txt |
| F-R | 6675399 is test-only | `git show --numstat 6675399` | FAILED-TO-REFUTE: 9 files, 4075 additions and 0 deletions: G, R, green/rework-1.txt, the round-1 verify captures and report, and the decision log | none |
| F-M | The merge leaves this change alone | `git diff --stat 6675399 82aa3d9`; `git diff --stat 5c55448 7c5b8b9` on the change's files | FAILED-TO-REFUTE: no gitlab graphql_only.py, commands/call.py, registry.py, transport.py, gitlab_wrapper.py, G, R, T or Q path. main changed only docs/forLLMConsumption.md among them, in one hunk inside the `github_api/` bullet. The `gitlab_api/` bullet is unchanged | none |

## Refuted

None. All five claims round 1 refuted now fail on the test DL-009 added for each. All 18 near variants and all 4
spot-checked round-1 mutants are killed. One variant was not built: "the last option on the command line wins". The
parsed `argparse` namespace keeps no order across `-f`, `-F` and `--file`, so `call_values` cannot express it as a
mutant. The test pins both orders, and both rows fail under 2r and 2r-a.

## Tree

After the last restore the harness printed `identical=True` for graphql_only.py, commands/call.py, registry.py,
transport.py and gitlab_wrapper.py. Their sha256 and the map's equal the pre-run values. HEAD is 82aa3d9, and
`git diff --stat HEAD` is empty. `git status --porcelain` lists only this report and the four captures
(full-suite-2.txt, mutant-delta-2.txt, mutant-variants-2.txt, spot-check-2.txt). The `!!` lines of `--ignored` equal
the pre-run listing. The captures are LF only. The mutant captures hold no 40-hex string, and every 40-hex SHA in
full-suite-2.txt carries the allowlist pragma. The harness, the saved job log and the listings are deleted.

Verdict: VERIFIED
