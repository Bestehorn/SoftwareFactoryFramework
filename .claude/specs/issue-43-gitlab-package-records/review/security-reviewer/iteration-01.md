# Security review — issue #43 design, iteration 01 (security-reviewer)

### B1 — `package#change-the-visibility-of-the-container-registry` makes a branch-overwriting pull mirror callable ungated, while the design says no record of this change writes a branch
Severity: B
Location: design.md § Security Considerations "Gates" and "What stays callable"; requirements.md AC-1.3, AC-4.2, UB-4
Defect: The record is `PUT /projects/:id/`, the Projects API update endpoint. AC-1.4 gives it a `Param` for each of its
entry's rows, `import_url`, `mirror` and `mirror_overwrites_diverged_branches` among them (`rest/package.md` "Change the
visibility of the container registry"). GitLab documents that call as the way to configure pull mirroring: "use the API
to configure pull mirroring when creating or updating a project" (https://docs.gitlab.com/api/project_pull_mirroring/).
The mirror then pulls "Automatically, 30 minutes after a previous pull. This cannot be disabled", and "Overwrite
diverged branches" will "always update your local branches with remote versions, even if they have diverged"
(https://docs.gitlab.com/user/project/repository/mirror/pull/). So `call
package#change-the-visibility-of-the-container-registry -F mirror=true -f import_url=<any URL> -F
mirror_overwrites_diverged_branches=true` has GitLab rewrite the configured project's branches, the trunk included,
from a repository the caller names. No `id` is needed, because it defaults to the configured project (#41 AC-1.8). That
is the server-side form of the `git push --mirror` and `+main` that `src/hooks/gate_merge_steward.py` refuses (its
module docstring), and no gate covers it. The Gates bullet still says "no record of this change commits, merges or
creates an issue". #41 Residuals says that such a record "is gated by its slice", and `prompt.md` Goal adopts that
("the rule #41 records").
Material-because: security — a record this change adds lets any caller of `call` overwrite the trunk server-side,
bypassing the merge steward's rule that only it writes the trunk, and the design's gate analysis states the opposite.
Proposed-edit: keep the key pending, as DL-002 keeps the registry-host keys. Gating it instead would need a
`refuse_gated` message with no compatibility subcommand to name, and UB-4 freezes `GATED_OPERATIONS`. Keeping it
pending removes text and adds no mechanism.
- requirements.md AC-1.3 → "The keys whose path starts with `/http(s)://${CI_REGISTRY}`, and `("PUT", "/projects/:id/")`,
  SHALL stay in `package.PENDING`, with no record."
- requirements.md AC-4.2, second bullet: delete "and the `avatar` of "Change the visibility of the container registry"".
- requirements.md Residuals, append: "Project update (AC-1.3): `PUT /projects/:id/` is the Projects API update
  endpoint, whose `import_url`, `mirror` and `mirror_overwrites_diverged_branches` configure a pull mirror that
  overwrites the project's branches (https://docs.gitlab.com/api/project_pull_mirroring/). #41 Residuals gates such a
  record by its slice. It is mapped and gated together with tenant-scale's `PUT /projects/:id` ("Update a project"),
  whose entry carries the same rows."
- design.md D5: delete the `package#change-the-visibility-of-the-container-registry` (`avatar`) row. D6 "The kept
  keys": append "`("PUT", "/projects/:id/")` (AC-1.3)".
- design.md Security Considerations: delete the `package#change-the-visibility-of-the-container-registry` bullet of
  "What stays callable". Append to "Gates": "The project-update key `PUT /projects/:id/`, which can configure a pull
  mirror that overwrites the trunk, stays pending (AC-1.3)."
- design.md Residuals, last bullet → "The Conan tokens that `package#create-an-authentication-token` and `…-1` print
  are callable ungated (Security Considerations) → one findings-ledger row." The Correctness Properties literals for
  AC-1.1, AC-1.3 and AC-4.2 (F's `KEPT`, `OPERATION_IDS` and the `--file` cases) change to match.

### C1 — Upstream-registry passwords given in argv are not named
Severity: C
Location: design.md § Security Considerations "The credential"
Defect: The bullet covers only the configured token. The `password` body rows of the container and Maven
virtual-registry upstream records (create, update and the two "test connection" entries in `rest/package.md`) are
secrets that a caller gives with `-f`, so they show on the command line.
Proposed-edit: append to "The credential": "The upstream-registry `password` rows (container and Maven virtual
registries: create, update and test an upstream) are body values given with `-f`. They show in the command line, as
#41 Residuals "Secrets in arguments" records, and travel in the JSON body, never in the URL that an error quotes."

## Checked and found sound (no finding)
- `--route-prefix`: `registry.route` writes the record's own value, chosen by exact text, so caller text never becomes
  path text. Each `:id` of the value goes through `_segment` (`quote(safe="")`; `""`, `.` and `..` refused), and
  `_rest_url` plus `_send`'s origin check keep every request on the configured host. `expand` refuses an unrouted
  prefix path, and `pages` cannot send one.
- The hyphenated name only changes how a template's own name ends. A value is still one percent-encoded segment.
- Git Bash: I measured that `/packages/npm` arrives as `C:/Program Files/Git/packages/npm`, while the four values
  holding `:id` arrive unchanged. Matching by exact text turns the mangled value into a refusal, never a different
  route (Operability's claim holds).
- DL-002: the registry-host keys stay unreachable because `_send` refuses any other origin. No second origin and no
  `/jwt/auth` exchange is added.
- Raw bodies go through #40 D5's `request_raw`/`_send`. A PUT or POST is never redirected. The credential is read only
  from `config/gitlab.json`, and no option contains `token`. No dependency is added.

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
