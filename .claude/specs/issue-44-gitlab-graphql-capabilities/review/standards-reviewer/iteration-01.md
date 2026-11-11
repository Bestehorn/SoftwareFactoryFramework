# Standards review — issue #44 design, iteration 01

Lane: standards-reviewer. Artefacts: `requirements.md`, `design.md`, `decisions/decision-log.md` at origin/main d30d022.

### B1 — D4 rebuilds the multipart body and Content-Type that `transport.request_body` already builds
Severity: B
Location: design.md § D4 "`transport.py`."
Defect: D4 has `Transport.graphql` call `multipart_body(form=..., files=..., boundary=...)` and compose
`multipart/form-data; boundary=<boundary>` itself. That repeats the files branch of `transport.request_body`, which
`Transport.request` already uses for a REST `--file` call: the `secrets.token_hex(nbytes=MULTIPART_BOUNDARY_BYTES)`
boundary, `multipart_body`, and `f"{CONTENT_TYPE_MULTIPART}; boundary={boundary}"`.
Material-because: unmaintainable-by-rule design-principles.md (§2 "reuse before adding new abstractions";
coding-standards.md §10 "reusable, testable units"). It leaves two copies of the boundary and Content-Type
construction, and D4 rejects `graphql_upload` on the same ground ("it would repeat `graphql`'s refusal, send and error
reading").
Proposed-edit: in D4 "`transport.py`", replace "With files the body is `multipart_body(form=..., files=...,
boundary=...)` and its `Content-Type` `multipart/form-data; boundary=<boundary>`:" with "With files, the body and its
`Content-Type` are what `request_body(form=..., json_body=None, files=...)` returns. That is the multipart branch a
REST `--file` call already takes: `multipart_body` under a fresh boundary, and `multipart/form-data;
boundary=<boundary>`:". DL-004 says "the existing `multipart_body`"; the conductor decides whether to supersede it.

### C1 — the docstrings say one record is one capability, which D1 ends
Severity: C
Location: design.md § D2 "`GraphQLOperation` is unchanged"; § D8 "Module docstrings"
Defect: `registry.py`'s module docstring says "A ``GraphQLOperation`` is a GraphQL-only capability …, named by the
first cell of the "Only in GraphQL" row it serves", and the class docstring says "One GraphQL-only capability: …".
Under D1, several records serve one capability. D8's `registry.py` bullet names only `upload_variables` and
`split_uploads`, so both docstrings stay stale in a file this change edits (post-activity.md §4).
Proposed-edit: D8 "Module docstrings", the `registry.py` bullet: "`registry.py` names `upload_variables` and
`split_uploads`. Its module docstring and `GraphQLOperation`'s say a record is one query or mutation of a capability,
and that several records may serve one capability (D1). `transport.py` names the multipart GraphQL request."

### D1 — a reference count in D1
Severity: D
Location: design.md § D1 "The rule."
Defect: "Row 1's five field members sit under five roots" counts the members of a reference row, and a regeneration
of the reference can change that count (proportionality.md "Specs state behaviour, not measurements").
Proposed-edit: "Row 1's field members sit under different roots (`workItem`, `workItemsByReference`, `project`,
`group`, `namespace`)".

### D2 — one parameter name and type, two meanings in `Transport`
Severity: D
Location: design.md § D4 "`transport.py`."; § D4 "`registry.py`." `split_uploads`
Defect: Both `Transport.request` and `Transport.graphql` would take `files: Sequence[Tuple[str, Path]]`. In
`request` the string is the part name; in `graphql` it is the operations path (`variables.files.0`), and D4 then names
the part `str(i)`.
Proposed-edit: in D4, "`Transport.graphql` gains `files: Sequence[Tuple[str, Path]] = ()`, each pair an operations path
and its file (not a part name, as in `request`)."

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
