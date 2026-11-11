# Best-practice review — issue #30, design iteration 02 (delta)

Sources: `docs/api-reference/github/graphql/` (`mutations.md` `copyProjectV2`, `createProjectV2`; `interfaces.md`
`RepositoryOwner`; `conventions.md` "Global node IDs"), `docs/api-reference/github/rest/repos.md` "Get a repository",
the trunk at `f374b3d` (`git grep` over `origin/main:src/payload/scripts/github_api/families/`), and docs.github.com
"Get a repository" (https://docs.github.com/en/rest/repos/repos#get-a-repository, fetched 2026-11-11). No MCP
documentation server covers GitHub; the local reference and the web page above were used.

Fix sites checked:

- BP-B1 (Y2), design.md § D4, the `ownerId` row: applied. The row sources `ownerId` from `owner.node_id` of
  `call repos/get` and keeps `node_id` of `call users/get-authenticated` for the token's user. This agrees with the
  documentation. `CopyProjectV2Input.ownerId` and `CreateProjectV2Input.ownerId` are "ID of: Organization, User"
  (`mutations.md`). `Repository.owner` is `RepositoryOwner!`, which `Organization` and `User` implement
  (`interfaces.md`). A REST `node_id` is the object's GraphQL `id` (`conventions.md` "Global node IDs"). The
  `full-repository` `owner` is a Simple User with `node_id` and `type` required (docs.github.com). `repos/get` is
  an `operation_id=` record in `families/repos.py` on the trunk, and `orgs/get` is still a `PENDING` string in
  `families/orgs.py`, so D4's "Every REST record named here is declared" still holds. The new § Sources entry
  ("`owner` is a Simple User whose `node_id` is required") matches the fetched page.
- BP-C1, design.md § Residuals "Objects this wrapper did not create": applied. It is merged with the earlier
  discussion-comment residual. `projects/get-for-org`, `projects/get-for-user`, `projects/list-for-org` and
  `projects/list-for-user` are `PENDING` strings in `families/projects.py` on the trunk, as the residual states.
- BP-C2, design.md § Residuals "Partial mutation results": applied as proposed (its last clause is shortened). It adds
  no acceptance criterion or mechanism.

The edits added no deprecated API, documented anti-pattern or contradiction of GitHub's documentation.

Verdict: CLEAN
