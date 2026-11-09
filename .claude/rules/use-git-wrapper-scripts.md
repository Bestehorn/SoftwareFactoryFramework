# Repo Operations: Wrapper Scripts Only (CRITICAL)

ALL operations against this repository's GitHub remote — CI/CD inspection, issue/PR/label
management, any other API call — go through the wrapper, `scripts/github_wrapper.py`.

## Forbidden

- `gh` CLI (any subcommand)
- raw `curl` or `wget` against `api.github.com`
- direct `requests` / `urllib` calls to the GitHub API from anywhere outside the wrapper
- any other tool that bypasses the wrapper's credential loading

These tools fail unpredictably here because they rely on their own token stores (often via
environment variables) and produce inconsistent output formats.

## Allowed

- Local-only `git` commands (`git status`, `git log`, `git diff`, `git add`, `git commit`,
  `git push`, `git fetch`, `git rebase`). These don't hit the host API.
- Any subcommand the wrapper exposes.
- Adding new subcommands when needed — extend, do not bypass. The extension goes into the PRODUCT
  wrapper, `src/payload/scripts/github_wrapper.py`; the installed `scripts/github_wrapper.py`
  changes only by promotion (`project-specific.md`).

## Credentials

- GitHub PAT: `credentials/github-pat.txt` (one line, gitignored). Templates with `*.template` are
  checked in.
- If the wrapper reports a placeholder is still present, STOP and ask the user to paste a real
  token. Do not proceed.
- NEVER echo credential contents into chat, logs, or commit messages.

## Integration

- `no-environment-vars.md`: the wrapper reads from project files, never from `GITHUB_TOKEN`. Do not
  add env-var fallbacks.
- `no-guessing.md`: when reporting CI/issue status, run the wrapper and quote its output.
- `coding-standards.md`: new subcommands use string constants for JSON fields, absolute imports,
  `pathlib.Path`, named parameters.
