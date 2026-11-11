# Evidence report — issue #32: GitHub wrapper rewrite, part 2 slice: issues, pulls, reactions, search, activity, gists

Tier S, one wave plus one verification rework. Branch `issue-32-issues-pulls-records`, PR #48, rebased onto #27's
merge f374b3d (DL-008).

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1 every pending ID but `pulls/update-branch` has one record, names as its section | F (six modules); N | red/green wave-1 | green |
| AC-2 `pulls.PENDING` is `{"pulls/update-branch"}`, the other five empty | F `test_only_the_residual_ids_are_pending`; V | red/green wave-1 | green |
| AC-3 paging, `item_key`, `multi_segment` empty, default version and media type | F `test_the_records_follow_the_transcription_rules` | red/green wave-1 | green |
| AC-4 a paged record prints both pages' items | F `test_a_paged_record_prints_every_page` | red/green wave-1 | green |
| AC-5 every record outside the gate is sent as documented | N `test_every_record_is_sent_as_its_section_documents` | green wave-1 | green |
| AC-6 `pulls/merge-async` refused naming `merge-pr`, without "which sends it" | K gated cases (rework DL-009) | red/green wave-1; green/rework-1 | green |
| AC-7 `call issues/create-issue-artifact` passes the filing gate | G `call-create-issue-artifact` | red/green wave-1 | green |
| UB-1 to UB-5 compatibility, refusals incl. #27's seven, credential, GitLab untouched, the filing gate's spellings | C, P, V, K, G (`quoted-create-word`), `test_wrapper_delivery.py` | green wave-1, rework-1 | green |

Green captures: wave 1 had 748 passed. After the rebase, 789 passed over the 15 affected files. Rework 1 had 118
passed. Product `run_checks.py --group lint --group types --group security`: 5 passed, 0 failed.

**Verifier.**
- First pass: REFUTED AC-6's wording (`evidence/verify/refutation-report.md`). Mutants M06 (the `GATED_NOT_SENT`
  condition inverted) and M06b (`GATED_NOT_SENT` emptied) survived, because K checked only the ID and the subcommand.
- Rework DL-009: K now asserts the ending of each message.
- The re-verification killed M06 (3 failures) and M06b (1 failure) and returned VERIFIED
  (`evidence/verify/refutation-report-2.md`).
- Every other first-pass mutant was killed: record fields, `pulls.PENDING`, the gate entry, the `refuse_gated`
  revert that #27's seven `None` refusals catch, and the `CREATE_RE` lookarounds.

**Whole suite.** CI run 42960788592 success on 234772e; CI run 42964842191 success on 8e80256 (the rework head).

E2E: the real-forge run is #10's. N and F run `call` through the product's `main` up to the API boundary in CI job
`verify`.
