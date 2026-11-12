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

When the token expires or is revoked, replace the secret and the file on every machine that has one.

## Running the suite locally

From the checkout's root, with the venv active:

```
python scripts/run_tests.py --workers 1 test/forge
```

`--workers 1` is required: the suite owns one repository per run and refuses a run spread over several workers. An
interrupted local run leaves its repository to a later run's sweep, and its workspace (the clone and the clone's
credential file) in the temporary directory.
