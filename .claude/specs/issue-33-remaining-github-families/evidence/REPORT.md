# Evidence report — issue #33: GitHub wrapper rewrite, part 2 slice: the remaining 31 families

Tier S (re-tiered from M, DL-001), one wave. Branch `issue-33-remaining-github-families`, PR #52. It merged the trunk twice: c59d491 resolved the `commands/call.py` conflict with #32 by keeping both sides, and 273d86b took #31.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending ID of the 31 families has one record, names as its section | F (31 modules); N | red/green wave-1 | green |
| AC-2 only `markdown/render-raw` and the Copilot content-exclusion record stay pending | F `test_only_the_residual_ids_are_pending`; V | red/green wave-1 | green |
| AC-3 paging (incl. `dependency-graph/diff-range`), `item_key`, `multi_segment` empty, default version and media type | F `test_the_records_follow_the_transcription_rules` | red/green wave-1 | green |
| AC-4 a paged record prints every page | F `test_a_paged_record_prints_every_page` | red/green wave-1 | green |
| AC-5 every record outside the gate is sent as documented; `billing/update-budget-org` declared once (DL-005) | N | green wave-1 | green |
| AC-6 the seven branch-writing or issue-creating records are refused, naming no subcommand | F `test_a_branch_writing_record_is_refused` | red/green wave-1 | green |
| UB the existing refusals (incl. #27's and #32's), compatibility, credential, GitLab untouched | K, C, P, V; repos, git and pulls suites; `test_wrapper_delivery.py` | green wave-1; after the merges | green |

Green captures:

- Wave 1: 771 passed.
- After the two trunk merges: 441 passed (merge check) and 362 passed (affected suites).

Product `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):

- **Targeted mutants:** 35, all killed. They covered names, `PENDING`, item keys, all eleven LINK↔NONE flips, each of the seven gate entries and their message, and the DL-005 revert.
- **Wave reverted to the merge base:** the same 132 failures as the red capture.
- **Merge resolution:** keeps all 17 gate entries and the three message forms.
- **Coverage:** `call.py` and every changed family module have 0 missed statements in CI.

**Whole suite.** CI run 42969041590 success on 273d86b.

E2E: the real-forge run is #10's. N runs every declared record through the product's `main` up to the API boundary,
in CI job `verify`.
