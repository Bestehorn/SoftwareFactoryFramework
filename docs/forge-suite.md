# The forge suite and its test credential

The forge suite, `test/forge/`, tests the product wrapper `src/payload/scripts/github_wrapper.py` against github.com.
Each run creates one private repository, `sff-test-<run id>`, in the organization `bestehorn-sff-test`, runs every
forge test against it, and deletes it at the end. Before it creates its own, a run deletes every `sff-test-*`
repository of the organization that was created more than a day earlier: what an interrupted run left behind. The
default test collection never runs the suite; the `forge` CI job runs it on every push to `main`, every pull request
and every manual dispatch, and the pipeline fails when it fails.

## The test credential file

The suite reads its token from `credentials/github-sff-testing-pat.txt`: one line, the token. The file is git-ignored.
In a linked worktree, which has no git-ignored files, the suite uses the main working tree's copy. A file that is
empty, holds more than one token or still holds the placeholder fails the run before any request.

Only a machine that runs the forge suite locally needs the file; in CI, the `forge` job writes it from the secret.

## The token

A fine-grained personal access token (Settings, Developer settings, Personal access tokens, Fine-grained tokens,
Generate new token):

- Resource owner: `bestehorn-sff-test`.
- Repository access: "All repositories", because each run's repository is new.
- Repository permissions, named as docs.github.com "Permissions required for fine-grained personal access tokens"
  names them. GitHub's form offers write access as "Read and write".

| Permission | Access | Needed for |
|---|---|---|
| Administration | write | creating and deleting the run's repository and the leftovers |
| Contents | write | git fetch and push, the git commit and tree records, merging a pull request, the stargazers list |
| Metadata | read | getting and listing the repositories |
| Issues | write | labels, issues, comments and reactions |
| Pull requests | write | creating, getting and listing pull requests |
| Actions | read | listing the repository's workflow runs |
| Code scanning alerts | read | listing the code scanning alerts |
| Secret scanning alerts | read | listing the secret scanning alerts |
| Dependabot secrets | read | listing the repository's Dependabot secrets |

Not needed: Workflows (the suite pushes no workflow file), Dependabot alerts (not called) and Checks (GitHub gives
fine-grained tokens no access to the Checks API). A permission the token lacks fails the test that needs it with
GitHub's `403` "Resource not accessible by personal access token".

## The Actions secret

The repository Actions secret `SFF_TEST_TOKEN` holds the same token. The `forge` CI job hands it to one step,
`python test/forge/write_credential.py`, which writes the credential file into the job's checkout. An unset secret
fails the job before the suite runs; GitHub passes no secret to a pull request from a fork or from Dependabot.
A secret that is set but malformed (two pasted lines, the placeholder) is written to the runner's credential file, and
the run then fails with a message naming that file: in CI, replace the secret `SFF_TEST_TOKEN`, and locally the file.

When the token expires or is revoked, replace the secret and the file on every machine that has one.

## Running the suite locally

From the checkout's root, with the venv active:

```
python scripts/run_tests.py --workers 1 test/forge
```

`--workers 1` is required: the suite owns one repository per run and refuses a run spread over several workers. An
interrupted local run leaves its repository to a later run's sweep, and its workspace (the clone and the clone's
credential file) in the temporary directory.

## The GitLab forge suite

The GitLab forge suite, `test/forge_gitlab/`, tests the product wrapper `src/payload/scripts/gitlab_wrapper.py`
against gitlab.com. Each run creates one private project, `sff-test-<run id>`, in the gitlab.com group
`bestehorn-sff-test`, runs every GitLab forge test against it, and deletes it at the end. Before it creates its own, a
run deletes every `sff-test-*` project of the group that was created more than a day earlier: what an interrupted run
left behind. On gitlab.com a deletion only marks a project: it stays marked for deletion until gitlab.com removes it at
the end of its retention period, and the sweep skips a marked project. The default test collection never runs the
suite; the `forge-gitlab` CI job runs it on every push to `main`, every pull request and every manual dispatch, and the
pipeline fails when it fails.

### The GitLab test credential file

The suite reads its token from `credentials/gitlab-sff-testing-pat.txt`: one line, the token. The file is git-ignored.
In a linked worktree, which has no git-ignored files, the suite uses the main working tree's copy. A file that is
missing or empty, or still holds the placeholder, fails the run before any request.

Only a machine that runs the GitLab forge suite locally needs the file; in CI, the `forge-gitlab` job writes it from
the secret.

### The GitLab token

A personal access token of a group service account of `bestehorn-sff-test`, set up in the group on gitlab.com:

1. Settings > Service accounts > Add service account.
2. Manage > Members: invite the service account with the role Owner.
3. Settings > Service accounts, the account's vertical ellipsis > Manage access tokens > Add new token: the scope
   `api`, and an expiration date at most 365 days ahead, GitLab's default maximum
   (docs.gitlab.com/user/profile/service_accounts/).

What the scope and the role cover, in the words of the GitLab docs:

| Grant | Covers |
|---|---|
| Scope `api` | every request of the suite: "Grants complete read and write access to the API for the token's scope"; git fetch and push: "For a personal access token, `api` also grants complete read and write access to the registry and repository through Git-over-HTTP." (docs.gitlab.com/security/tokens/access_token_scopes/) |
| Owner of the test group | deleting a project: "You must be an administrator or have the Owner role for the project." (docs.gitlab.com/api/projects/#delete-a-project); "If you assign a service account the Owner role for a group, the service account's personal access tokens also have the Owner role for that group." (docs.gitlab.com/user/profile/service_accounts/) |

Not needed: `read_api`, `read_repository` and `write_repository` (`api` covers them).

### The GitLab Actions secret

The repository Actions secret `SFF_GITLAB_TEST_TOKEN` holds the same token. The `forge-gitlab` CI job hands it to one
step, `python test/forge_gitlab/write_credential.py`, which writes the credential file into the job's checkout. An
unset secret fails the job before the suite runs; GitHub passes no secret to a pull request from a fork or from
Dependabot.

When the token expires or is revoked, replace the secret and the file on every machine that has one.

### Running the GitLab suite locally

From the checkout's root, with the venv active:

```
python scripts/run_tests.py --workers 1 test/forge_gitlab
```

`--workers 1` is required: the suite owns one project per run and refuses a run spread over several workers. An
interrupted local run leaves its project to a later run's sweep, and its workspace (the clone and the clone's
credential files) in the temporary directory.
