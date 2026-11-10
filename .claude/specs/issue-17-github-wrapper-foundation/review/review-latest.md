# Review — design iteration 01 (issue #17), aggregated by the conductor

Combined A+B = 14 (A 2, B 12) across six lanes; all A/B pass the materiality gate (each names a criterion or failure class and carries an edit). Lane files: `review/<lane>/iteration-01.md`.

## Surviving A/B (apply each lane's Proposed-edit unless a decision below overrides it)

| Id | Lane | Subject |
|---|---|---|
| TA-A1 | test-architect | UB-2.2 import check cannot fail (site-packages under platstdlib) → see X1 |
| TA-A2 | test-architect | fork parity runs the `--token-stdin` case against the fork (stdin read under capture) → product only |
| TA-B1 | test-architect | UB-1.1 parser parity option by option + the `--label` prefix case |
| TA-B2 | test-architect | ordered fake-host responses + expected write requests (start-issue) |
| TA-B3 | test-architect | retry-after vs x-ratelimit-reset precedence case |
| TA-B4 | test-architect | API-version header on `Transport.download` |
| TA-B5 | test-architect | AC-5.1 independent row count (index heading total); several graphql_only rows |
| TA-B6 | test-architect | AC-5.2 capability-gap example |
| SR-B1 | spec-review | UB-1.1 carve-out for redirected / rate-limited responses; same-origin follow is D3's decision |
| ST-B1 | standards | rename `GitHubRateLimitError`, `GitHubGraphQLResponseError` |
| ST-B2 | standards | breaking change for new projects (copy step) → see X3 |
| SE-B1 | security | server-supplied URLs (Link next, upload_url) only on the exact configured origin |
| SE-B2 | security | `_detect_repo` error strips `user:password@` from the remote URL |
| DO-B1 | devops | promotion residual restated → see X4 |

C/D findings of every lane are applied in the same pass (restate, never add).

## Cross-wrapper decisions (orchestrator, shared with #13)

- X1 The standard-library import check (UB-2.2) and any Hypothesis property test live in `test/` (framework-only, never installed into projects, runs on CI's Python 3.10) and use `sys.stdlib_module_names`. Shipped suites under `src/payload/test/` stay pytest-only and Python 3.9.
- X2 Exceptions live in `github_api/errors.py` (`GitHubAPIError` base with `details=None`, subclasses named with the base prefix) — the same module name as #13, so part-2 families never edit `transport.py` for an error type.
- X3 This change edits the setup prompts' wrapper copy steps (`prompts/setup-claude.txt` Part 5.3, `prompts/setup-kiro.txt` Part 6.2 and their shipped-Python lists) to copy `github_api/` with the entry script, so a project set up from the next release gets a working wrapper (`design-principles.md` 3). Few lines, no new criterion; a test pins the copy step names the package.
- X4 Promotion residual: the next promotion of this repository records `src/payload/scripts/github_api/*` and the new `src/payload/test/` GitHub files under `not_installed` (the fork stays installed) until the new wrapper replaces the fork; one findings-ledger row records it.
- X5 Origin = scheme + lower-cased host + port (443 when absent), computed for every URL the transport opens, from the same parse urllib connects with.
