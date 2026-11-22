# Security review — design iteration 01 (lane: security-reviewer)

No A or B finding. The token's paths, the helper reset and host scope, the project guard, both deletion guards, the
`forge-gitlab` secret step and the handling of listed project paths hold as designed. The three findings below are
restatements.

### C1 — "The guard's bound" names only `--path id=`, but GraphQL records and pathless records are unjudged too
Severity: C
Location: design.md § Security Considerations (The guard's bound); design.md § Residuals (the `--path id=` bullet)
Defect: `commands/call.py` `path_values` gives the configured project only to a record whose path is `/projects/:id`
  or lies under it (module docstring: "no other `:id` has a default"). A GraphQL record names its target only through
  its variables (`-f fullPath=...`, a global ID). So under the marker, with an `sff-test-*` configured project, the
  wrapper also sends every GraphQL record unjudged, F:graphql's `-f fullPath=P` among them. The same holds for every
  record with no project in its path (`POST /projects`, `/user`, `/personal_access_tokens/self`, a `/groups/:id`
  record). G's AC-8.7 check confines only `id=` strings and the two project records, so a wrong `fullPath` in a forge
  module would pass it. The token's reach (the test group) still bounds the impact, as the text already says.
Proposed-edit: in Security Considerations replace "and not an explicit `--path id=`, which reaches any project the
  token reaches." with "and not a target the call names itself: an explicit `--path id=`, a GraphQL record's
  variables (`fullPath`, a global ID), or a record whose path holds no `/projects/:id`. Each reaches whatever the token
  reaches. G confines `--path id=` and the creation and deletion records to the support module, and F:graphql's
  `fullPath` is the fixture's `full_path` (D6)." In Residuals replace "The guard does not judge an explicit
  `--path id=`" with "The guard does not judge a target the call names itself".

### C2 — The helper test does not say it checks the reset before it runs `git credential fill`
Severity: C
Location: design.md § Correctness Properties, AC-6.3 (`test_the_credential_helper_answers_git_with_the_clone_token`)
Defect: the row says `git credential fill`, run with D3's options and `host=gitlab.com`, answers the clone token. It
  does not say that the test first asserts the options open with `-c credential.helper=`, nor that it compares the
  password without printing it. #10's test does both (`test/test_forge_support.py`: it asserts
  `options[:3] == [CONFIG_OPTION, HELPER_RESET, CONFIG_OPTION]` before `_git`, then checks the boolean
  `answered_the_clone_token`). Suppose the GitLab test runs fill first and a regression drops the reset. git then asks
  the developer's configured helpers (Git Credential Manager) for a gitlab.com credential, and a failing equality
  prints their answer into the test report, which AC-6.3 forbids.
Proposed-edit: in the AC-6.3 row replace "Example, S `test_the_credential_helper_answers_git_with_the_clone_token`:
  `git credential fill` with D3's options and `protocol=https`, `host=gitlab.com` answers `username=sff-forge-suite`
  and the file's token; the helper string holds no token." with "Example, S
  `test_the_credential_helper_answers_git_with_the_clone_token`, as #10's. It first asserts that the options are
  exactly `-c credential.helper=` then `-c credential.https://gitlab.com.helper=!...` and hold no token. Then it runs
  `git credential fill` with them and `protocol=https`, `host=gitlab.com`, and checks `username=sff-forge-suite` and
  the file's token without printing the answer."

### C3 — A git command run without `authenticated` asks the operator's configured helpers
Severity: C
Location: design.md § D10 (`SubprocessGitRunner`); design.md § D3 (The clone)
Defect: #10's `SubprocessGitRunner.run` adds `credential_helper_arguments` only when `authenticated` is true, and it
  defaults to false (`test/forge/ephemeral.py`). Any remote git command the new code sends without
  `authenticated=True` therefore runs with the developer's helper list; the new `push_branch` push is one such command.
  Suppose the machine's Git Credential Manager holds the operator's own gitlab.com credential. The push then either
  succeeds as the operator (an Owner of the test group, with that account's whole reach) or opens an interactive
  sign-in. F still passes locally, so nothing shows the slip. As written, every remote command of D3 and D9 is
  authenticated; this tightens the default, not the design.
Proposed-edit: in D10 replace "`SubprocessGitRunner(*, clone)`: #10's, with D3's helper options when
  `authenticated`." with "`SubprocessGitRunner(*, clone)`: #10's, with D3's helper options when `authenticated`, and
  `-c credential.helper=` (`HELPER_RESET`) on every other command, so no git command of the suite asks a configured
  helper."

CLEAN
Verdict: READY — A 0, B 0, C 3, D 0
