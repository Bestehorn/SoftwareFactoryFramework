# Review latest — issue #30 design

## Iteration 01 (consolidated by the conductor)

Lanes:

- devops CLEAN (1 C, 1 D);
- standards CLEAN (2 C);
- best-practice NOT-CLEAN (0 A, 1 B, 2 C);
- security NOT-CLEAN (0 A, 1 B, 1 C);
- test-architect NOT-CLEAN (1 A, 2 B, 6 C, 1 D; 19/21 COVERED);
- spec-review NOT-READY (0 A, 3 B, 1 C).

### Root causes (A/B): 8 findings → 6 causes

- **Y1: Q's self-test cannot pass.** `test_the_method_rejects_a_document_that_differs` demands exactly one problem per
  case, but the `since:` and `connection=("repository", "mergeQueue")` cases each break several D6 rules. Fix: the
  `after`/`pageInfo` checks run only on a path that matches the connection. The oracle reads "at least one problem,
  and one names what differs". [TA-A1, SR-B2]
- **Y2: an organisation's `ownerId` has no source.** `users/get-authenticated` returns only the token's user. Fix:
  D4 sources `ownerId` from `owner.node_id` of `call repos/get` and keeps `users/get-authenticated` for the token's
  own user. [BP-B1, SR-B3]
- **Y3: a paging record's `$after`.** The requirements' Glossary counts it as a declared variable, so AC-2.1 says it
  is sent, while D3 refuses it. Fix: restate the Glossary entry to exclude a paging record's `$after`. This is a
  restatement, not new scope. [SR-B1]
- **Y4: a refused ID is not tied to the mutation it sends.** Fix: Q's `document_problems` also reports a mutation
  whose `operation_id` is not `graphql/` plus its root field. Add one rejection case (a swapped document) and add Q
  to AC-3.1's mapping row. [SEC-B1]
- **Y5: the call-through-`main` test skips `GATED_OPERATIONS`, the table under test, and passes on an empty
  `OPERATIONS`.** Fix: a test constant of AC-3.1's four refused IDs, shared with
  `test_a_refused_mutation_sends_nothing`, and the test fails when it calls no record. [TA-B1]
- **Y6: the docstring test's strings already exist** (`JSON array`, `exit 2`, `merge-pr` are on the trunk). Fix:
  assert within the `call graphql/` usage entry only. [TA-B2]

### C/D: apply in the same pass, no new round

- TA-C1: compare variable values by JSON kind.
- TA-C2: pin `selected_members` with an example.
- TA-C3: the `variables` unit test uses a body that uses its variables.
- TA-C4: the `-f after=c` case tests D3's refusal (DL-004).
- TA-C5: the reference test fails on an empty `OPERATIONS`.
- TA-C6: AC-4.2's map clause is checked by inspection.
- TA-D1: the wording of the AC-2.5 oracle.
- ST-C1: rename `registry.variables` to `declared_variables`; the parameter shadows it.
- ST-C2: D7 names the issue-moving `None` case beside branch writes.
- BP-C1: residual: a project not created here has no `projectId` source.
- BP-C2: residual: `errors` with partial `data` means the effect may have applied.
- SEC-C1: the Output bullet's reason is `ensure_ascii` escaping.
- SR-C1: the type-name reader strips `[...]` and `!`.
- DV-C1: "once its fixture exists".
- DV-D1: the Operability reason.

Next: one author pass over Y1–Y6 and every C/D above, then a delta review in iteration 02 (cap 4).

## Iterations 02–03 (delta)

Iteration 02: test-architect CLEAN (21/21 COVERED), best-practice CLEAN, security CLEAN, spec-review NOT-READY (1 B: D7's docstring line break split "JSON array" out of the narrowed AC-4.1 test). The conductor applied the reviewer's one-line edit. Iteration 03: spec-review READY. Approved (DL-006).
