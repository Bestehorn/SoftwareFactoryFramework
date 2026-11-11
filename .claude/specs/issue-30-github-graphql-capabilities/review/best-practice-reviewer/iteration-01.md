# Best-practice review — issue #30, design iteration 01

Sources: `docs/api-reference/github/graphql/` (`conventions.md`, `mutations.md`, `objects-a-p.md`, `objects-p-w.md`,
`interfaces.md`), `docs/api-reference/github/rest/repos.md`, `src/payload/scripts/github_api/transport.py`, the trunk
at `f374b3d` (`git show origin/main:…/families/*.py`), and docs.github.com "Get a repository"
(https://docs.github.com/en/rest/repos/repos#get-a-repository, fetched 2026-11-11). No MCP documentation server covers
GitHub; the local reference and the web page above were used.

### B1 — D4 names a User-only source for an Organization `ownerId`
Severity: B
Location: design.md § D4, the `ownerId` row
Defect: `CreateProjectV2Input.ownerId` and `CopyProjectV2Input.ownerId` are "ID of: Organization, User"
(`mutations.md`), but the row's only source, `node_id` of `call users/get-authenticated` (`GET /user`), is the token
user's own ID, so an organization-owned project has no correct source in the design, and following the row creates
the project under the user instead of the organization.
Material-because: AC-1.1 requires `design.md` to record how a caller obtains the global node IDs a mutation's `input`
takes; for an Organization owner the recorded source is wrong (wrong-behaviour: the project gets the wrong owner).
`orgs/get` cannot be the fix: it is in `families/orgs.py` `PENDING` on the trunk. `repos/get` is a record on the
trunk, and its `full-repository` response has `owner` (`Simple User`) with `node_id` and `type` both required
(docs.github.com "Get a repository").
Proposed-edit: replace the row's second cell with: "`owner.node_id` of `call repos/get` (the repository's owner;
`owner.type` is `User` or `Organization`); the token's own user: `node_id` of `call users/get-authenticated`".

### C1 — A project this wrapper did not create has no `projectId` source
Severity: C
Location: design.md § D4, the `projectId` row; § Residuals
Defect: `updateProjectV2`, `deleteProjectV2`, `copyProjectV2` and `linkProjectV2ToRepository` take a `projectId`
that D4 sources only from `createProjectV2`/`copyProjectV2` output; `projects/get-for-org`, `projects/get-for-user`,
`projects/list-for-org` and `projects/list-for-user` are in `families/projects.py` `PENDING` on the trunk, so an
existing project's ID has no source among the records, exactly as D4's "Discussion comments" residual states for
comments.
Proposed-edit: add to design.md § Residuals: "**Existing Projects v2 projects.** A project this wrapper did not create
has no ID source among the records: the REST `projects/get-for-*` and `projects/list-for-*` records are pending, and
selecting `ProjectV2` connections is outside the rows' members."

### C2 — A mutation answered with `errors` and partial `data` may have applied
Severity: C
Location: design.md § D3 "Errors"; § Residuals
Defect: `conventions.md` "Errors" item 3 says `data` can come with `errors` (failed fields `null`, the rest filled
in), so a mutation's root field can have run while a payload field failed; AC-2.4 prints nothing to standard output
and logs only the `errors` array, and `conventions.md` "Mutations" says `clientMutationId` is not a de-duplication
key, so a caller that re-runs after exit 1 can repeat a create (`createDiscussion`, `addDiscussionComment`,
`createProjectV2`, `createSponsorship`). Changing what AC-2.4 prints is outside the frozen criteria.
Proposed-edit: add to design.md § Residuals: "**Partial mutation results.** A mutation answered with `errors` and
partial `data` exits 1 and prints only the `errors` (AC-2.4), though its effect may have applied (`conventions.md`
"Errors"); a caller checks the object's state before running it again."

Verdict: NOT-CLEAN (0 A, 1 B)
