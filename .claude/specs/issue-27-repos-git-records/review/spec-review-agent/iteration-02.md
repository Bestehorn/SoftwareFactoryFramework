# spec-review-agent — iteration 02 (tier S, combined, delta)

No A, B, C or D findings. This pass checked the fix sites of iteration 01 and the text they changed.

## Fix sites

- B1 — closed. DL-002 records the split, its driver, the rejected re-tier and the evidence. AC-1 and the first
  Residuals bullet cite it. Comment 6786245265 on #27 (2026-11-11T03:35:20Z, after DL-002) records the deferral of
  "Both `PENDING` empty", gives the reason, and routes it to #46. #46 is open, with `Spawned-from: #27` and
  `Filing-rationale: DESIGN-OPTIONS`, and its work item "Map `repos/upload-release-asset` (left pending by #27)". That
  meets the deferral exception in `issue-tracking.md` "Closing", so #27 can be closed over that item.
- B2 — closed. `test_the_multi_segment_parameters_are_the_sections` fails in three cases: a missing name (the record
  drops out of the left-hand map), an extra name (the values differ), and a record that should hold no name (an extra
  key). It also covers the unchanged `git/delete-ref` and `repos/get-combined-status-for-ref`. Both already hold
  `multi_segment=frozenset({"ref"})`, and their sections' `ref` rows read "may contain `/` (multi-segment path)"
  (`rest/git.md` "Delete a reference", `rest/commits.md` "Get the combined status for a specific reference"). So the
  test passes on them without an edit, and UB-1 is untouched.
- C1 — applied (fourth Residuals bullet).
- C2 — applied (AC-7 test, "a literal tuple in F, never read from `GATED_OPERATIONS`").
- C3 — applied. Today `commands/call.py` `refuse_gated` refuses on `GATED_OPERATIONS.get(...) is not None`, and the
  Files row now replaces that with membership.
- C4 — applied. No task owns the ledger rows, and none needs to: `issue-work-orchestrator.md` puts "the ledger rows
  written with `memory_compile.py ledger add`" in the orchestrator's own pre-push commit.
- D1 — applied. `git/list-matching-refs` and `repos/list-public` get `item_key=None` from their `200` "array of".

## The Ask's "both `PENDING` emptied"

This is not a defect. The Ask records what #27 asked, and under `proportionality.md` "Scope freeze" only the person who
asked can change it. The deviation appears in every place it binds:

- AC-1's exception "per DL-002", which is the criterion F `test_only_the_upload_is_pending` and V
  `test_every_operation_is_covered_or_pending` test;
- the first Residuals bullet;
- the deferral comment on #27.

Rewriting the Ask as if the upload had never been asked for would misstate the issue. No edit is owed, and the change
has 6 bytes of headroom.

## New text

- The changed text introduces no new defect.
- AC-1's `repos.PENDING` set matches the scope of #27's deferral comment ("leaves `repos.PENDING` exactly
  `{repos/upload-release-asset}`; `git.PENDING` empty").
- AC-5 covers records only, so the pending upload is outside it. N fakes a success response, so the `307` of
  `repos/update` and `repos/delete` (still exit 1, #28 D4) does not contradict AC-5's exit 0.
- AC-4's new `None` arm agrees with the `Paging:` line of `repos/list-commit-statuses-for-ref` ("the response body is
  the array") and with the two `Link`-only records.

## Security lens on the delta

- The split removes the only `UPLOAD_ORIGIN` path from this change, so the credential reaches `API_ROOT` alone.
- Membership-based gating means an ID mapped to `None` is refused, not sent.
- The credential source is unchanged (UB-2).

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_only_the_upload_is_pending`, `test_nothing_is_pending`; V covered-or-pending, one-module | an ID other than the upload stays pending, the upload is mapped, or an ID has no record |
| AC-2 | N `test_every_record_matches_its_reference_section` | the method, the path or a name differs |
| AC-3 | F default version and media type; F `test_the_multi_segment_parameters_are_the_sections`; the `ref`-with-`/` cases | another version or media type; a `multi_segment` name is missing, extra or on the wrong record; a `/` is sent as `%2F` |
| AC-4 | F `test_every_list_record_has_a_case` + AC-6 cases | the LINK set or an `item_key` differs from F's transcription |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | a call exits non-0 or sends other names |
| AC-6 | F `test_a_list_record_prints_every_item` | either item is missing |
| AC-7 | F `test_a_branch_writing_record_is_refused` (literal tuple) | a listed ID is sent, exits other than 2, or is missing from `GATED_OPERATIONS` |
| UB-1 | C golden cases; P fork parity | a subcommand's output or exit code changes |
| UB-2 | C credential test; V stdlib test | `environ`/`getenv`, a token option, or a non-stdlib import |
| UB-3 | `test_wrapper_delivery.py`; the PR diff | the shared test fails or a file is touched |
| UB-4 | K gated cases; K json-or-empty (`git/delete-ref` 204) | a refusal loses its subcommand, or `delete-ref` is refused |
| E2E | N and F through `main` up to the API boundary (CI `verify`/`tests`); the real-forge check is #10's | — |

Verdict: READY
