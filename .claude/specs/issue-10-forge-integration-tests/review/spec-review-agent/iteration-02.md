# Design review — spec-review-agent — iteration 02 (delta)

Lens: implementability and internal consistency of the delta (fb1beaa to the current revision); cited symbols as
described.

## Iteration-01 findings

- A1 — resolved. D9 step 3 creates `<workspace>/clone` with `Path.mkdir` before `git init`, and D3 reads "`git init`
  in the created `<clone>`", so `SubprocessGitRunner`'s `-C <clone>` names an existing directory from the first command.
- B1 — resolved. `requirements.md` AC-6.1 now carries the proposed text (DL-002); D8 "Lookup" and S
  `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree` match it. `--path-format=absolute` comes before
  `--git-common-dir`, which is where git applies it.
- C1 — resolved. Step 1 binds `run_id` and `name` before the `try`, the `finally` covers steps 2 to 6 and the yield,
  and D8 "Reading" cites step 2.
- C2 — resolved. `Path.write_bytes` with `\n`.
- C3 — resolved (applied as review B2). `swept_at` is in the `EphemeralRepository` field list, step 4 passes it, and
  the D6 row judges with `now=swept_at`.
- D1 — resolved.

The delta's new claims hold where I checked them. `ci.yml` `on:` is exactly `push` (`branches: [main]`),
`pull_request` and `workflow_dispatch`. `config/toolchain.json` `files` lists no workflow, `not_installed`
`templates/ci/*` names `ci.yml` as the project's own, `templates/ci/` holds no `ci.yml` source, and
`gate_toolchain_paths` judges only the manifest's `files`. `run_checks.py` has `e2e_argv` and `ON_REQUEST_GROUPS`
`("e2e",)`. `GITHUB_REPOSITORY_PATTERN` reads `https://github.com:<sentinel>@example.com/repo` as owner
`<sentinel>@example.com` and repo `repo`, so D2's `shown` and the new AC-4.1 example agree. `run_tests.py`
`build_command` adds nothing that overrides `log_cli`. The URL-scoped helper `credential.https://github.com.helper`
comes after the empty `credential.helper=` reset on the command line, so the reset still empties the list first. No
fix added a criterion or a mechanism beyond the consolidated list.

## Findings

### D1 — The AC-6.2 mapping row still cites the old step number
Severity: D
Location: design.md § Acceptance Criteria Mapping, row AC-6.2
Defect: the row names "D9 step 1" for the credential read. After the C1 reorder, step 1 binds the run id and step 2
reads the token, and D8 "Reading" already says "D9 step 2".
Proposed-edit: "| AC-6.2 | D8 `read_test_token`; D9 step 2 | ..."

### D2 — D2's `shown` restates a separator the wrapper already defines
Severity: D
Location: design.md § D2, `_refuse_unless_ephemeral`
Defect: `owner.rpartition("@")[2]` spells out the literal. `github_wrapper.py` already has `USERINFO_SEPARATOR = "@"`,
and `_without_userinfo` uses it for the same stripping.
Proposed-edit: "`shown` is the owner after its last `USERINFO_SEPARATOR` (`owner.rpartition(USERINFO_SEPARATOR)[2]`, as
`_without_userinfo` strips a URL's userinfo)".

CLEAN
