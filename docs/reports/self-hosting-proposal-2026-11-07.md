# Self-hosting: developing the framework with the framework (2026-11-07)

**Status:** decided 2026-11-07 (§10); not implemented yet. **Builds on:** [directory-restructure-proposal-2026-11-07.md](directory-restructure-proposal-2026-11-07.md),
rule 5 ("sources are not installed copies").

## 1. The problem

This repository is about to use the framework it develops. The same files then play two roles:
- they are the **product**: what an issue changes, reviews and tests;
- they are the **tooling** that changes, reviews and tests the product.

Your example is the git wrapper: an issue about `github_wrapper.py` is filed, worked and merged *through*
`github_wrapper.py`. The same holds for the agent hooks (they gate the sessions that edit them), the rules
and agents (sessions follow them while changing them), the merge steward, and the CI workflow.

If the tooling ran straight from the files being developed, any defect would disable the means to fix it.
A wrapper that cannot open a PR cannot land its own fix. A gate that blocks every commit cannot be repaired
by a session that has to pass it. A rule edited mid-session would change behaviour mid-run.

## 2. Recommendation in brief

**The repository is its own consumer.** The usual way out of this is how a compiler is built: by its
previous release, never by itself.

| | Product (what is developed) | Toolchain (what development runs on) |
|---|---|---|
| Where | `prompts/`, `clients/`, `src/`, `templates/` | The paths every consumer project has: `CLAUDE.md`, `.claude/`, `.githooks/`, `scripts/`, `config/`, `.github/workflows/`, `docs/` (the installed docs) |
| Comes from | Commits on `main` | `prompts/update.txt`, run against this repository with **the framework = a release tag of this same repository**, exported with `git archive` (the update prompt already installs only from a pinned export, never from a working tree) |
| Changed by | Issues, PRs, CI | **Promotion only**: an update run to a newer release. Never by hand |
| Pinned in | — | `.claude/FRAMEWORK_COMMIT` (`<sha> <date>`, plus the tag) |

A merged product change does not affect development until it is **released** and **promoted**. So the
tooling in use is always a released version that already passed CI. The worst a bad change can do is
fail its own PR, or, if it gets released, be rolled back to the previous release.

## 3. One change through the scheme: the wrapper

1. **File the issue** with the installed wrapper (`python scripts/github_wrapper.py create-issue …`).
   The issue names the product file, `src/payload/scripts/github_wrapper.py`.
2. **Develop** in a worktree, in `src/payload/scripts/`. Unit tests (`src/payload/test/`, fake host) run
   locally and in CI.
3. **Integration-test against a real forge** with the *development* wrapper. The test creates its own
   **ephemeral repository** (§5), drives it, and deletes it, so it never touches this repository's
   backlog. This works without changing the wrapper: it targets the `origin` of the clone it runs in
   and reads that clone's `credentials/github-pat.txt`.
4. **Open the PR, wait for CI and merge** with the *installed* wrapper. It is unchanged, so it still works
   even when the change under review breaks the new one.
5. **Release:** tag `main` (§4). **Promote:** run `prompts/update.txt` against this repository, pinned
   to the tag. The update PR replaces `scripts/github_wrapper.py`, and every session uses the new wrapper
   from its next call. This is the first moment the change is "eaten".
6. **If the promoted wrapper turns out broken:** roll back (§4).

The same path applies to a gate (`src/hooks/` → `.claude/hooks/`), a rule or agent
(`clients/claude/…` → `.claude/…`), the steward, and the CI template (`templates/ci/` → `.github/workflows/`).

## 4. Releases, promotion, rollback

- **Release** = an annotated tag on a `main` commit whose CI is green, e.g. `v2026.11.07` (a `.N` suffix
  for a second one on the same day). It is cut when a merged change should take effect: for this
  repository's own development, and for consumers.
- **Releases help consumers too.** Today an update pins whatever HEAD is (the update prompt notes that
  five commits landed during one measured update). With tags, consumers can pin to a release.
  Switching `update.txt` from "pin HEAD" to "pin the latest release" is a one-paragraph follow-up.
- **Promotion** = `prompts/update.txt` run against this repository at the release tag. It installs the
  delta, keeps this repository's recorded deviations (§6) through its three-way merge, writes
  `FRAMEWORK_COMMIT`, and lands one PR. Promote right after each release, so this repository is
  always the first consumer of every release: it runs every release before any other project does.
- **Rollback** = promote the previous tag. When the broken piece is one the promotion itself needs (the
  wrapper that opens the PR), first restore that file from the previous tag's export. That is a local
  file copy, with no forge call:

  ```bash
  git show v<previous>:src/payload/scripts/github_wrapper.py > scripts/github_wrapper.py
  ```

  Then run the rollback promotion with the restored file. Because every release is a tag, a working
  toolchain is always one `git show` away.

## 5. Ephemeral repositories for forge-facing code (decided: S4)

The wrappers, the steward and the delivery CI talk to GitHub and GitLab. Fake-host unit tests cover the
logic. The real API behaviour (permissions, pagination, merge rules, events) can only be tested against a
real forge, and those tests create issues, PRs and merges. Nothing in this is manual: every run of the
forge tests provisions what it needs and removes it again.

- **One repository per test run, created by the test.** A session-scoped pytest fixture creates a
  private repository named `sff-test-<run id>` via the API (GitHub `POST /user/repos`; GitLab
  `POST /projects`). It pushes a seed commit and clones it into a temporary directory with its own
  `credentials/` file, so the wrapper under test targets it through `origin`. When the run ends, the
  fixture deletes the repository, whether the tests passed or failed.
- **They run on every PR**, as decided, next to the unit tests. They need network access and a token,
  so their CI job is the slowest; it runs in parallel with the rest.
- **Deletion is guarded.** The fixture deletes only a repository it created in this run, with a name
  matching `sff-test-<this run's id>`, and never anything else. A sweep at the start of each run removes
  leftovers of crashed runs: repositories matching `sff-test-*` older than a day, created by the same
  token. The development wrapper refuses to act on any `origin` that is not an `sff-test-*` repository
  while the test marker is set.
- **The one thing set up once is the credential.** The token must be allowed to create and delete
  repositories: GitHub classic `repo` + `delete_repo`, or a fine-grained token with Administration
  write; GitLab `api`. It lives as a CI secret and in a local, git-ignored credentials file. Creating a
  token is a sign-in step on the forge that no automation can take for you, so it is the only manual
  step, and it is needed once. It should be a dedicated token, not the one the toolchain wrapper uses
  for this repository's backlog.
- **Rate limits:** one repository per run, not per test, keeps a run to a handful of administrative calls.

## 6. Guards that keep the two halves apart

1. **Toolchain integrity check (CI, required).** Every installed toolchain file must equal its source at
   the commit `FRAMEWORK_COMMIT` names, unless it is listed in a short, reviewed
   `config/toolchain-deviations.json` with a reason (e.g. `scripts/run_tests.py` lists this repository's
   suites). A hand edit of `scripts/github_wrapper.py` then fails CI and names the product file to edit
   instead. Until the renderer exists (directory-restructure §5.3), the check covers the 1:1 copies, which
   are `src/payload/**`, `src/hooks/**`, and the client files installed unchanged. Once the renderer
   exists, it renders `FRAMEWORK_COMMIT` and diffs the whole tree.
2. **A project gate (decided: S5, ORDER > 100):** it refuses Edit/Write on a toolchain path and names
   the product path, so the mistake is stopped when it is made rather than at CI. The update run itself
   is exempt: it runs on a `framework-update-*` branch, which is how the gate tells it apart.
3. **Two lines in this repository's `CLAUDE.md` ("This project"):** "The rules, agents, hooks and scripts
   you run are the installed release named in `.claude/FRAMEWORK_COMMIT`. The files under `prompts/`,
   `clients/`, `src/` and `templates/` are the product you change. A product change takes effect for you
   only after release and promotion."

## 7. Specific points

- **Shipped tests are not installed a second time here.** In a consumer, `test/test_merge_steward.py`
  and the other shipped tests check the installed copy. Here, the product suite already tests the same
  code under `src/payload/test/` at every commit, and a release is only cut from green CI. Installing them
  again would run the 9-minute steward suite twice for nothing. Record them as deliberate deviations.
  The exception is `test_instruction_corpus_budget.py`: it checks *this* repository's `CLAUDE.md` and
  rules, so it is installed.
- **Merge mode `direct` to start.** One writer and low volume do not need the steward. It can be switched
  on later, at which point the ephemeral-repository tests (§5) are where it is proven first.
- **Hooks that gate their own development** are safe by construction: sessions run the installed
  release, while the product hooks' suite and `hooks.py selftest` run against `src/hooks/` in scratch
  projects.
- **Same file names in two places** (`scripts/github_wrapper.py` and `src/payload/scripts/github_wrapper.py`)
  follow from rule 3 of the layout and are intended. The integrity check and the `CLAUDE.md` lines are
  what keep them apart.
- **This repository's own tools** (`scripts/api_reference/`, `test/test_layout.py`) are project files,
  like any consumer's own scripts. They are not toolchain, so the integrity check ignores them.
- **Kiro:** start with the Claude toolchain only. A Kiro toolchain is a second promotion target and can
  follow once someone develops this repository with Kiro.

## 8. Alternatives considered

| Alternative | Why not |
|---|---|
| Run the tooling straight from the working tree (no pinning) | This is the chicken-and-egg itself: a broken change disables the tools needed to fix it, and a session's rules change under it mid-run. |
| Keep the toolchain outside the repository (a second repo, or a global install such as `~/.sff/`) | It works, but it is a second thing to version and keep in step per machine, while the in-repo pinned install is exactly what the framework already does for every consumer. Using the consumer path is also the point: this repository then dogfoods the update prompt itself. |
| Use a different tool for this repository's own forge work (`gh`, the web UI) | It avoids the recursion but gives up dogfooding the wrappers, which are a large part of the product. `gh` is not installed here. It remains a fine break-glass, but should not be the normal path. |

## 9. Bootstrap, and what it changes in the restructure plan

The first install is the one moment there is no toolchain to use. It goes:

1. Tag the current `main` (after the restructure, the rename and the API reference) as the first release,
   `v2026.11.07`. Choose a commit whose product suite has run green.
2. Run `prompts/setup-claude.txt` against this repository, with the framework = the export of that tag.
   It installs `CLAUDE.md`, `.claude/`, `scripts/github_wrapper.py` (plus the credentials stub),
   `pyproject.toml`, the CI workflow and the installed docs, records the deviations (§7) and writes
   `FRAMEWORK_COMMIT`. This bootstrap PR is opened and merged with the wrapper it has just installed. If
   that wrapper fails, the bootstrap stops before anything is merged.
3. Add the integrity check (§6.1), the project gate (§6.2) and the `CLAUDE.md` lines (§6.3). Provide the
   repository-create/delete token for the ephemeral forge tests (§5); that is the one step that is yours.
4. From then on: issues → product PRs → CI → merge; release → promote, whenever a change should take
   effect.

**Reordering the restructure's phase 2:** self-hosting moves to the front, ahead of the renderer and the
twin merge. Every later step then runs with issues, CI and the toolchain, instead of building them up to
the end. The forge-wrapper rewrite now under way (`docs/api-reference/`, commit `8e42ea2`) becomes the
first product change developed this way. It lands in `src/payload/scripts/`, is proven against
ephemeral repositories, and reaches the toolchain by promotion.

## 10. Decisions (2026-11-07)

| # | Question | Decision |
|---|---|---|
| S1 | Toolchain: in-repo pinned install, or an alternative (§8)? | In-repo install, pinned to a release tag of this repository. |
| S2 | Release tag scheme | Date tags `vYYYY.MM.DD[.N]`. |
| S3 | Promotion cadence | Right after every release. |
| S4 | Testing forge-facing code against a real forge | Ephemeral repositories, created and deleted by every test run, on every PR (§5). No manually created sandbox. The only one-time step is the create/delete token. |
| S5 | Keeping hand edits out of the toolchain | The CI integrity check AND the project gate (§6). |
| S6 | Order in phase 2 | Self-hosting first, ahead of the renderer and the twin merge (§9). |
