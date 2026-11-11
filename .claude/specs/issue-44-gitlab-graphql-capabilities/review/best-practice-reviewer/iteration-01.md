# Best-practice review — issue #44, design iteration 01

No documentation MCP server covers GitLab or GraphQL in this session; the local reference
(`docs/api-reference/gitlab/graphql/`, snapshot of GitLab 19.6) and the official web pages below were read on
2026-11-11. The multipart request of D4 (part order `operations`, `map`, files; `null` in place of each file; `map`
values as arrays of operations paths; part names `0`, `1`, …) matches the multipart request specification and
`conventions.md` "File uploads". The GraphQL-spec claims of D1 and D7 (§6.2.2 serial mutation execution, §6.4.1
`CoerceArgumentValues`, the §3.10 Input Coercion row `{ a: $var, b: 123 }` with `{}` giving `{ b: 123 }`) match the
October 2021 text. Every root field, argument, input field and payload field the D1 tables name is in the reference
with the type the design gives it, and `workItemDelete` selects `namespace` instead of the `project` payload field that
was deprecated in 16.9. D5's global-ID handling and D3's forward paging follow `conventions.md`.

### C1 — `graphql#workItemExport` runs a mutation the reference marks deprecated, and the design does not say so
Severity: C
Location: design.md § D1 (Mutation records table); design.md § Residuals
Defect: `mutations-j-w.md` `workItemExport` carries "Notes: **deprecated** in 18.0", and the same reference documents
`workItemsCsvExport` (experiment) with the same input fields and the same `errors` and `message` payload. Of the
deprecated features, the design records only design management (Sources, Residuals).
Material-because: not A or B. The frozen AC-1.3 names `workItemExport` as a row member, the 19.6 snapshot still serves
it, and D1's comment rule already marks the record. When GitLab removes it at a later major release (`conventions.md`
"Deprecation, experiment and beta markers" § Process), the call will exit 1 by AC-2.4, and a regeneration of the
reference will fail Q.
Proposed-edit: in D1's mutation table, change the first cell `graphql#workItemExport` to "`graphql#workItemExport`
(deprecated in 18.0; the reference also documents `workItemsCsvExport` with the same input)". In design.md § Residuals,
add one bullet: "**`workItemExport` is deprecated in 18.0.** A regeneration that drops it fails Q, as for design
management."

### Sources
- `docs/api-reference/gitlab/graphql/conventions.md`: "Endpoint and request shape", "Global IDs and other
  identifiers", "Connections and cursor pagination", "Errors and partial data", "Deprecation, experiment and beta
  markers", "Mutations", "File uploads".
- `docs/api-reference/gitlab/graphql/mutations-j-w.md` (`workItemExport`, `workItemsCsvExport`, `workItemDelete`,
  `pipelineCreate`, `workItemsCsvImport`), `mutations-a-j.md` (`branchRule*`, `designManagementUpload`), `queries.md`,
  `objects-*.md`.
- https://github.com/jaydenseric/graphql-multipart-request-spec: "the fields are ordered: 1. `operations` … with files
  replaced with `null`. 2. `map` … 3. File fields"; "the key is the file multipart form field name and the value is an
  array of operations paths".
- https://spec.graphql.org/October2021/: §6.2.2 "This selection set should be executed serially"; §6.4.1 "Let hasValue
  be true if variableValues provides a value for the name variableName"; §3.10 Input Coercion table.
- https://docs.gitlab.com/user/project/issues/design_management/: "deprecated in GitLab 18.6 and is planned for removal
  in 20.0", the design's cited fact, confirmed.

CLEAN

Verdict: READY
