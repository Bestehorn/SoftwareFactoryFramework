# Spec review, iteration 01, SPEC lane (issue #30, tier M)

### B1 — A paged record's `$after` is a declared variable that the design refuses
Severity: B
Location: requirements.md § Glossary "Declared variables", AC-2.1, AC-2.5; design.md § D3 `variables`, § Correctness Properties AC-2.5
Defect: The Glossary counts every `$name` definition of the document as a declared variable. So AC-2.1 requires
`call graphql/Repository.discussions -f owner=o -f name=r -f after=c` to be sent with `after: "c"`. D3 refuses that
call with exit 2, and G's third AC-2.5 case and R `test_variables_are_the_documents_definitions` give the declared
variables as `["owner", "name"]`.
Material-because: AC-2.1 is contradicted, and AC-2.5's "the record's declared variables" names a different set than
the test oracle. The design cannot honour the Glossary as written: `Transport.graphql_nodes` sends
`{**variables, FIELD_AFTER: after}` with `after = None` on the first page, which overwrites a caller's `after`. That
leaves the requirements text to restate, in line with DL-004.
Proposed-edit: in requirements.md § Glossary, replace the "Declared variables" bullet with: "- **Declared variables**
— the `$name` variable definitions of a record's `document`, except the `$after` of a record that pages a connection,
which `Transport.graphql_nodes` sets on every page."

### B2 — Q's method test demands one problem where D6's own rules give two or more
Severity: B
Location: design.md § Correctness Properties "Q's method" (`test_the_method_rejects_a_document_that_differs`); § D6 `document_problems`
Defect: The test says "Each case gives exactly one problem", but two of its cases break more than one of
`document_problems`' rules:
- `since:` in place of `after:` in `graphql/Repository.discussions` breaks two. `Repository.discussions` has no
  `since` argument (`objects-p-w.md` `Repository`, whose `discussions` arguments are `after`, `answered`, `before`,
  `categoryId`, `first`, `last`, `orderBy` and `states`), and the last connection field then lacks `after: $after`.
- `connection=("repository", "mergeQueue")` on `graphql/Repository.mergeQueue` breaks at least two. The last
  connection field, `mergeQueue(branch: $branch)`, has no `after: $after`, and its selection, `entries { … }`, has
  neither `nodes` nor `pageInfo`.
Material-because: AC-1.1 (the proof of Q's method). The test as specified cannot pass against the method as specified,
so the implementation has to depart from one of them.
Proposed-edit: in § Correctness Properties "Q's method", replace "Each case gives exactly one problem, naming what
differs:" with "Each case gives at least one problem, and one of them names what differs:".

### B3 — D4 gives no source for an Organization `ownerId`
Severity: B
Location: design.md § D4, row "`ownerId` (Organization, User)"
Defect: The row's only source is `node_id` of `call users/get-authenticated`, which returns the token's user. It never
returns an Organization's ID. So the row records no way to get the Organization `ownerId` that `createProjectV2` and
`copyProjectV2` take for an organisation-owned project (`mutations.md`: "ID of: Organization, User"). `orgs/get` is
not a source either: it sits on `families/orgs.py`'s `PENDING` on `origin/main`.
Material-because: AC-1.1 ("how a caller obtains the global node IDs a mutation's input takes") is not met for one of
the two types the row names. A caller who follows the row passes a User ID, and the project is created under the user.
Proposed-edit: replace the row's second cell with "`owner.node_id` of `call repos/get` (the repository's owner, an
Organization or a User); `node_id` of `call users/get-authenticated` (the token's user)". GitHub REST "Get a
repository" documents `owner` as a Simple User with a required `node_id`, and `repos/get` is declared on
`origin/main`.

### C1 — Q reads a type name that still carries list and non-null wrappers
Severity: C
Location: design.md § D6 `reference_schema`
Defect: D6 says "A type's name is the link text of its Type cell", but link texts carry wrappers: `` `[Discussion]` ``
(`DiscussionConnection.nodes`) and `` `PageInfo!` `` (`pageInfo`). Read literally, every `nodes` is an undefined name,
so it counts as a leaf, and a leaf with a selection is a problem. Also, `queries.md`'s signature line writes its return
type as a link (`` → [`Repository`](objects-p-w.md#repository) ``), not as the `` → `Type` `` that D6 shows; only
`mutations.md` writes a code span there.
Proposed-edit: replace "A type's name is the link text of its Type cell." with "A field's type is the link text of its
Type cell; the type the walk enters is that text with `[`, `]` and `!` removed. `queries.md`'s signature line gives
the return type as a link, `mutations.md`'s as a code span."

Verdict: NOT-READY (0 A, 3 B)
