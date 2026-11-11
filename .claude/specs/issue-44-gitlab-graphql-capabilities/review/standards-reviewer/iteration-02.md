# Standards review — issue #44 design, iteration 02 (delta)

Lane: standards-reviewer. Delta: design.md D1, D2, D4, D8, D9 and iteration 01's C/D edits; DL-006. Checked against
`src/payload/scripts/gitlab_api/transport.py` (`request_body`, `multipart_body`, `_file_part`, `Transport.graphql`) and
`src/payload/scripts/gitlab_api/registry.py` (`Pair`).

## Iteration-01 findings

- B1: closed. D4 "`transport.py`" now takes the body and `Content-Type` from
  `request_body(form=..., json_body=None, files=...)`. The call matches the code. `request_body` is keyword-only and
  needs all three parameters. `form` is `Sequence[Pair]` with `Pair = Tuple[str, str]`, and D4's `operations` and `map`
  values are `json.dumps` strings. `files` is `Sequence[Tuple[str, Path]]` keyed by part name, and D4's `str(i)`
  provides that name. With files and `json_body=None`, `request_body` takes its multipart branch: a
  `secrets.token_hex(nbytes=MULTIPART_BOUNDARY_BYTES)` boundary, then `multipart_body`, then
  `f"{CONTENT_TYPE_MULTIPART}; boundary={boundary}"`. `multipart_body` writes the form parts before the file parts, which
  is the order D4 quotes. `_file_part`'s `GitLabAPIError` comes from inside `request_body`, before `_send`, as D4 says.
  The boundary and Content-Type are now built in one place only. DL-006 supersedes only DL-004's body-construction
  clause, by appending, as `agent-state-convention.md` §2 rule 1 requires.
- C1: closed. D8's `registry.py` bullet and D9's `registry.py` row now name the module docstring and the
  `GraphQLOperation` docstring.
- D1: closed. D1 now lists the roots without a count.
- D2: closed. D4 now says that each `files` pair in `Transport.graphql` is an operations path and its file, not a part
  name as in `request`.

## New in the delta

No project-standard violation. Checked:
- D6's `GATED_OPERATIONS` comment wording.
- The Security Considerations sentence on `pipelineCreate`.
  `ci_pipeline_variables_minimum_override_role` appears in `docs/api-reference/gitlab/conventions.md`.
- The Operability citation. `config/toolchain.json` `not_installed` holds `src/payload/scripts/gitlab_wrapper.py`.
- The AC-5.1 and AC-5.2 test edits.
- D1's `workItemExport` deprecation note.
- The two new Residuals bullets.

None of these adds a dependency, an environment read, a measurement or a line number.

### D1 — In Security Considerations, `conventions.md` means the REST file; everywhere else it means the GraphQL one
Severity: D
Location: design.md § Security Considerations "Destructive or costly operations."
Defect: "`conventions.md` names the projects attribute" points to `docs/api-reference/gitlab/conventions.md`, at its
`restrict_user_defined_variables` (projects) row. Everywhere else in the design, a bare `conventions.md` is
`docs/api-reference/gitlab/graphql/conventions.md` (§ Sources).
Proposed-edit: replace "`conventions.md` names the projects attribute" with "the REST
`docs/api-reference/gitlab/conventions.md` names the projects attribute".

CLEAN

Verdict: READY
