# Evidence report — issue #38: GitLab wrapper rewrite, part 2 slice: the remaining 13 stage groups

Tier S (re-tiered from M; DL-001 moved deploy's three keys to #40), one wave. Branch `issue-38-gitlab-remaining-stage-records`, PR #60. It was rebased onto 5c55448 before the push.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every Reference of the 13 families has its record, an equality against F's literal table | F `test_every_reference_has_its_record` (×13); V | red/green wave-1 | green |
| AC-2 only DL-002/DL-005's 18 keys stay pending | F `test_only_the_kept_keys_are_pending` (×13); V | red/green wave-1 | green |
| AC-3, AC-6 names and locations as the section; every record sent as documented | N | green wave-1 | green |
| AC-4 kinds (FILE by "file upload" Notes), `required`, body JSON (FORM for `growth#force-a-variant-assignment`), no `fixed` | F `test_every_param_is_typed_as_its_row` | red/green wave-1 | green |
| AC-5 paging, DL-003's one-object lists NONE | F `test_only_the_list_records_are_paged` | red/green wave-1 | green |
| AC-7, AC-8 a paged record prints every page; a download is written unchanged | F | red/green wave-1 | green |
| UB the compatibility cases, the refusals (no kept id declared), stdlib only, the GitHub wrapper untouched; N's DL-004 edit | C, K, P, V; N; the PR diff | green wave-1 | green |

Red and green captures:
- Red: 124 failed. Every one is an `AssertionError` or an exit-2 refusal of an id no record declares, and N passes.
- Green: 317 passed.
- After the rebase, the GitLab suites gave 531 passed. Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- **Mutants:** 60 targeted mutants, at least one per module, were all killed. The whole-wave revert reproduced the red capture's 124 failures, and reverting N's DL-004 edit was killed too.
- **Reference check:** 47 sections were spot-checked across the 13 pages.
- **Lessons entry:** the five-line entry on this branch (a process lesson on decision-log timestamps) has no runtime effect. The verifier noted it and did not refute on it.

**Whole suite.** CI run 42997031572 success on b7424e9.

E2E: not applicable. The real-instance run is #11's. N and F run `call` through `main` up to the API boundary in CI job `verify`.
