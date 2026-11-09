# credentials/ — git host tokens (never committed)

Everything here except this README and `*.template` files is git-ignored.

| File | Used by | Content |
|---|---|---|
| `github-pat.txt` | `scripts/github_wrapper.py` (run from the repository root) | One line: a GitHub token for `Bestehorn/SoftwareFactoryFramework` with Issues, Pull requests, Contents and Actions access. Copy `github-pat.txt.template` and replace its line. |

The forge integration tests use their OWN token, kept apart from this one: they create and delete ephemeral
`sff-test-*` repositories, so that token needs repository create and delete rights
(`docs/reports/self-hosting-proposal-2026-11-07.md` §5). Never put either token in a shell environment variable.
