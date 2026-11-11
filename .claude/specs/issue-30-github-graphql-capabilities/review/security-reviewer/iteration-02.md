# Security review — design iteration 02 (delta) — issue #30

No findings.

- B1 applied: D6 `document_problems` reports a mutation whose `operation_id` is not `graphql/` plus its root field.
  The rule keys on the document's operation type, so a non-mutation ID carrying a mutation document is reported too.
  Correctness Properties `test_the_method_rejects_a_document_that_differs` carries the swapped
  `enablePullRequestAutoMerge` document case, which yields that one problem under Y1's "at least one" oracle. The
  AC-3.1 mapping row names Q `test_every_record_matches_the_reference`.
- C1 applied: the Output bullet gives `print_json`'s default `ensure_ascii=True` as the reason. `commands/_common.py`
  `print_json` calls `json.dumps(obj=value, indent=JSON_INDENT)` with no `ensure_ascii` argument. The Sources quote
  matches docs.python.org `json.dump` verbatim.
- The delta adds no new security defect. Y5's shared constant makes `test_a_refused_mutation_sends_nothing`, with
  AC-3.2's log check, fail on a missing gate entry. A refused ID that `graphql_lookup` cannot find does not pass that
  test, because its log lacks `merge-pr` and "no subcommand sends it". Y2's `owner.node_id` source and Y3's
  Glossary restatement touch no trust boundary.

Verdict: CLEAN
