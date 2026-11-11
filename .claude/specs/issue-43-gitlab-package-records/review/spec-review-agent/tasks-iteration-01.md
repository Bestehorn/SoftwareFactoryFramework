# Tasks review — iteration 01 — spec-review-agent

### C1 — `PreparedCall.prefix` is passed on but never set
Severity: C
Location: tasks.md § Wave 2, task 2.4
Defect: 2.4, like design D3, gives `PreparedCall` a `prefix` field that `send_call` passes to `registry.send`, but names
no step that sets it. Implemented literally, the field stays `None`, and `registry.send`'s `route` then raises
`ValueError` for every prefix call inside `send_call`. That is outside `call_operation`'s `except ValueError`, which
wraps only `prepare_call` (#40's `commands/call.py` `call_operation`, `send_call`), so the error escapes uncaught.
Material-because: wrong-behaviour. F's and N's prefix sends in the same wave catch it, so one restating sentence is
enough.
Proposed-edit: replace "`PreparedCall.prefix: Optional[str] = None`, which `send_call` passes to `registry.send` as
`prefix`" with "`PreparedCall.prefix: Optional[str] = None`, which `prepare_call` sets to `args.route_prefix` on the
`PreparedCall` of a `Paging.NONE` REST record and `send_call` passes to `registry.send` as `prefix`".

### C2 — 2.1's red sentence does not hold for two of F's calls
Severity: C
Location: tasks.md § Wave 2, task 2.1 (Red)
Defect: "each call exits 2 …, failing its exit-code or request assertion" is wrong for two calls:
- The `--file` refusal of `package#upload-a-package-file-3` (design § Correctness Properties, AC-4.2) expects exit 2
  with nothing sent. `registry.lookup`'s refusal gives exactly that, so written as its own parametrized case it passes
  on the red run.
- The glob record's call without `--path path` (AC-3.2) fails only on its log-record assertion.
Material-because: the red capture would contradict the task's own red statement and the intro's "add failing tests".
#40's task 2.2 named its one test that passes on both runs.
Proposed-edit: replace 2.1's Red sentence with "Red: `OPERATIONS` is empty and `PENDING` full, so each table test fails
its assertion, and each call exits 2 (`registry.lookup` refuses every `package#` ID, argparse `--route-prefix`),
failing its exit-code, request or log-record assertion; the `--file` refusal of `package#upload-a-package-file-3` is
asserted in that record's case, after its send, so it is red with it."

0 A, 0 B, 2 C, 0 D.

Verdict: READY
