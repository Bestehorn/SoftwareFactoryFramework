# spec-review-agent — tasks.md, iteration 01 (issue #40, tier M)

Checked and found sound:
- **Traceability.** Every `Validates:` id exists in `requirements.md`, and every AC and UB row of the Coverage table is
  correct.
- **Files and waves.** Each wave's `Files:` match D7 and are disjoint, and every D7 file has a task.
- **Wave order.** 2.4 to 2.6 read only what 1.5 and 1.6 add.
- **Run lines.** Every named suite exists, and so do the regression tests F.3 names.
- **F.1** is honest: N's `test_every_record_is_sent_as_its_section_documents` runs through `fixtures.run_main`.
- **Cap and figures.** tasks.md is 14,952 B against a cap of 15,000, and it carries no line number.
- **3.3** is acceptable as written. D7 lists `docs/findings-ledger.md`. `issue-filing-discipline.md` requires the rows
  in the change they come from, and F.3 admits only D7's files. It is not work beyond the design.

### C1 — 2.2's green-by-design test names no mutant
Severity: C
Location: tasks.md § Wave 2, task 2.2
Defect: `test_no_record_declares_an_openapi_only_model_id` passes on both runs. Under the verifier's wave-2 mutant
(2.4 and 2.5 reverted) it stays green, and the task names no mutant that turns it red. #46's tasks name one for each
such test, and so did #41's tasks review, C1.
Material-because: not gating. `registry.lookup` raises `ValueError` for the ID today and after wave 2, so the verifier
cannot show the test can fail.
Proposed-edit: in 2.2, "pins an absence and passes on both runs." becomes "pins an absence and passes on both runs,
its mutant an `openapi_only.OPERATIONS` record with the ID `openapi-only#download-an-ml_model-package-file`."

### C2 — 1.4's red reason for the deploy case is not what runs
Severity: C
Location: tasks.md § Wave 1, task 1.4, the "Red:" sentence
Defect: 1.4 makes `record_problems` read the section through `documented_raw_body` (design D5 "N"). That function reads
`record.content_type`, and `RestOperation` has no such field until 1.5. So the
`deploy#download-a-machine-learning-model-package-file` case raises `AttributeError` before `endpoint_problems` can
name the `path` row. The stated "(assertion)" never occurs. The call_problems cases exercise only N's helpers, which
1.4 itself edits, so they pass in red.
Material-because: not gating. The test is red, and the header accepts an `AttributeError`, but the verifier's red audit
would be checked against a reason the capture does not show.
Proposed-edit: replace "Red: the new test's `deploy#download-a-machine-learning-model-package-file` case names the
`path` row, which `registry.placeholders` does not read yet (assertion), and its raw-body record raises `TypeError` on
`content_type`; N's existing record tests raise `AttributeError` on `content_type` inside `documented_raw_body` until
1.5." with "Red: until 1.5, the new test's raw-body record raises `TypeError` on `content_type`, and its other
`record_problems` cases and N's existing record tests raise `AttributeError` on `content_type` inside
`documented_raw_body`."

### D1 — the header's "only inside a test body" excludes 1.4's helper
Severity: D
Location: tasks.md § preamble ("appears only inside a test body")
Defect: 1.4's `documented_raw_body` is an N helper, not a test function, and it reads `content_type`.
Proposed-edit: "appears only inside a test body" becomes "appears only inside a function body".

Byte balance: C2's restatement is 109 bytes shorter than the text it replaces. C1 adds 109 bytes and D1 adds 4, before
re-wrapping. The file stays inside its 48 bytes of headroom.

CLEAN

Verdict: READY
