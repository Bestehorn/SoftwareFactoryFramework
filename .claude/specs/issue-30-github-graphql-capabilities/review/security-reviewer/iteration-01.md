# Security review — design iteration 01 — issue #30

### B1 — The gate refuses an ID string; nothing proves the ID names the mutation its document runs
Severity: B
Location: design.md § D6 (Q `document_problems`), § Correctness Properties (AC-3.1, AC-3.3); requirements.md AC-3.1
Defect: `refuse_gated` matches `operation_id` exactly (origin/main `commands/call.py` `refuse_gated`) while
`Transport.graphql` sends `document`, and no test of D6 checks D2's rule that a mutation record's ID is `graphql/`
plus its root field: Q compares the document with the schema, V compares IDs with each other and with the index, and
G posts `record.document` and compares it with itself. So a record whose document runs `createCommitOnBranch` or
`enablePullRequestAutoMerge` under an ungated ID passes Q, V and G and is sent; for example the two documents swapped
between `graphql/enablePullRequestAutoMerge` and `graphql/disablePullRequestAutoMerge` keep every row member selected
(AC-1.3), keep every input type and selection valid, and leave `graphql/disablePullRequestAutoMerge` sending the
enable mutation.
Material-because: security — AC-3.1 is stated for the mutation a call "would run", and the design proves the refusal
only for four ID strings, whereas for REST `test/test_github_wrapper_contract.py` `record_problems` ties every gated
ID to its reference method and path.
Proposed-edit: in D6, replace the Q bullet "for a mutation: more than one root field, or an `input` argument that is
not `$input`." with "for a mutation: more than one root field, an `input` argument that is not `$input`, or an
`operation_id` other than `graphql/` followed by that root field's name (D2), so the ID `GATED_OPERATIONS` refuses is
the mutation the document runs (AC-3.1)."; in Correctness Properties, `test_the_method_rejects_a_document_that_differs`,
add the case "the document of `graphql/enablePullRequestAutoMerge` in `graphql/disablePullRequestAutoMerge`"; in the
Acceptance Criteria Mapping row AC-3.1, add "Q `test_every_record_matches_the_reference`".

### C1 — The "Output" bullet names the wrong reason a result cannot write a terminal escape
Severity: C
Location: design.md § Security Considerations, "Output"
Defect: RFC 8259 §7 obliges escaping U+0000 to U+001F only, so a C1 control such as U+009B (a one-character CSI)
survives it; the result is escaped because `print_json` calls `json.dumps` with its default `ensure_ascii=True`
(`commands/_common.py` `print_json`; Python docs, `json.dump`: "If ensure_ascii is true (the default), the output is
guaranteed to have all incoming non-ASCII characters escaped").
Material-because: n/a (C) — the conclusion holds today; the stated reason would stay "true" if the default changed.
Proposed-edit: replace "JSON strings escape control characters (RFC 8259 §7), so" with "`print_json`'s `json.dumps`
keeps its default `ensure_ascii=True`, which escapes every character outside ASCII, and RFC 8259 §7 escapes U+0000 to
U+001F, so".

Verdict: NOT-CLEAN (0 A, 1 B)
