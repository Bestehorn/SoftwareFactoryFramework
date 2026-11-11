# Standards review — issue #30 design, iteration 01

### C1 — `registry.variables` is shadowed inside `registry.graphql_call` by its own `variables` parameter
Severity: C
Location: design.md § D3 "Registry additions" (`variables`, `graphql_call`); § D8 `registry.py` row; § Acceptance Criteria Mapping AC-2.5
Defect: `graphql_call(transport, operation_id, *, variables)` must refuse an undeclared name, and its only source of the declared names is the module function `variables(*, operation)`. Inside `graphql_call`, though, the name `variables` refers to the caller's mapping, so following the text literally calls a `Mapping` (mypy rejects it; at run time it raises `TypeError`). The registry's existing naming, `path_parameters(*, operation)`, and the requirements' glossary term "Declared variables" both point to a name that does not collide.
Material-because: none of the five classes. This is a clarification that removes a name collision the implementer would otherwise have to resolve on their own.
Proposed-edit: in D3 "Registry additions", replace "`variables(*, operation) -> Tuple[str, ...]`" with "`declared_variables(*, operation) -> Tuple[str, ...]`". In D3 step 3, replace "`registry.variables(operation=...)`" with "`registry.declared_variables(operation=...)`". In D8's `registry.py` row, replace "`graphql_lookup`, `variables` and `graphql_call`" with "`graphql_lookup`, `declared_variables` and `graphql_call`". In the Acceptance Criteria Mapping AC-2.5 row, replace "`registry.variables`" with "`registry.declared_variables`". The R test name `test_variables_are_the_documents_definitions` stays.

### C2 — `call.py`'s docstring and the `GATED_OPERATIONS` comment would misdescribe the new `None` entry `graphql/transferIssue`
Severity: C
Location: design.md § D7 "Module docstrings" (first bullet); § D5
Defect: On the trunk D5 rebases onto (`origin/main` `src/payload/scripts/github_api/commands/call.py`), the `GATED_OPERATIONS` comment says "A record whose call commits to, creates, moves or renames a branch maps to ``None``", and the module docstring says the same for the "no subcommand sends it" refusal. D5 maps `graphql/transferIssue` to `None`, but that mutation moves an issue into another repository, not a branch. D7 edits `call.py`'s docstring only for "the GraphQL grammar and print forms", so both texts would be inaccurate after this change.
Material-because: none of the five classes. This is a stale-docstring correction in the ask's scope (AC-3.1 adds the entry), in the fix-now class of `issue-filing-discipline.md`.
Proposed-edit: replace D7's bullet "`commands/call.py`'s docstring adds the GraphQL grammar and print forms." with "`commands/call.py`'s docstring adds the GraphQL grammar and print forms. It and the `GATED_OPERATIONS` comment name, beside a record that commits to, creates, moves or renames a branch, a record that moves an issue into another repository (D5)."

Verdict: CLEAN
