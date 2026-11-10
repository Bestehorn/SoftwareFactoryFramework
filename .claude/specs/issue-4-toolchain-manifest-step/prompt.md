# Prompt — issue #4: promotion does not maintain config/toolchain.json

Tier: S — one repository tool and its test, plus a one-sentence manifest step in the promotion procedure; no
shipped interface changes.

Kind: BUGFIX (an unreproducible promotion step).

## Goal

This repository runs on an installed release of itself. `config/toolchain.json` (`release_tag`, `installed`,
`files`, `deviations`, `not_installed`) is what `test/test_toolchain_integrity.py` and the `toolchain-paths` gate
(`.claude/hooks/gate_toolchain_paths.py` `_manifest`) read. The promotion procedure, `prompts/update.txt`, never
mentions the manifest: its step 7 ("Write the marker") writes only `.claude/FRAMEWORK_COMMIT`. The first
promotion (release v2026.11.09, PR #1) built the manifest with a one-off script that was never committed.
Correct: a promotion that follows the committed procedure leaves a manifest that names the promoted release and
lists every installed file, reproducibly.

## Scope (the ask)

Decided (DL-001), the issue's first open question — the route is a committed REPOSITORY tool, not product
behaviour every project runs:

- `scripts/toolchain_manifest.py` — a tool of this repository (like `scripts/api_reference/`: a project file,
  not toolchain, never listed in `files`). `python scripts/toolchain_manifest.py --release <tag>` reads the
  release's tree with git (`git ls-tree -r --name-only <tag>` — never a working tree), maps every product file
  under the installable trees to its install path by the layout the setup prompts install
  (`clients/claude/<dir>/<f>` → `.claude/<dir>/<f>` for agents, commands, docs, rules; `clients/common/docs/<f>`
  → `.claude/docs/<f>`; `clients/common/phases/<f>` → `.claude/specs/_workflow/phases/<f>`; `src/hooks/<f>` →
  `.claude/hooks/<f>`; `src/payload/<f>` → `<f>`; `templates/githooks/<f>` → `.githooks/<f>`;
  `templates/docs/<f>` → `docs/<f>`; `templates/setup-hooks.sh.template` → `scripts/setup-hooks.sh`), drops every source the current
  manifest's `not_installed` names (exact path or `fnmatch` pattern), and writes `config/toolchain.json` with
  `release_tag` = the tag, `installed` = the `--installed` date (default today), `files` = the derived map, and
  `deviations` / `not_installed` carried forward. Decided (DL-001), the issue's second open question: `files` is
  derived from the release itself, so a file the release adds is listed (or must be named in `not_installed`
  with a reason) and a file it removes disappears.
- A carried `deviations` or `not_installed` entry whose path the release no longer contains is dropped and
  reported (UB-2: entries survive unless the release removes their cause); the tool prints the added and removed
  `files` entries relative to the previous manifest, so the promoter sees the delta.
- `config/toolchain.json` `not_installed` gains the release sources the first promotion left out without a
  recorded reason, each with one: `clients/claude/README.md`, `templates/README.md`, `templates/docs/README.md`
  (descriptions of the product trees, not installed files), `src/hooks/ruff.toml` (the root `ruff.toml` extends
  it in place), `templates/pre-commit-config.yaml.template` (this repository keeps its own
  `.pre-commit-config.yaml`) — so the derived `files` equals the committed one for the committed release (AC-4).
- `prompts/update.txt` `## Task` step 7 gains one sentence: a project that keeps a toolchain manifest regenerates
  it in the same commit as the marker, with the command its `docs/forLLMConsumption.md` names. Harmless for
  every other project; it makes the committed procedure (AC-1, AC-3) reach the tool.
- `docs/forLLMConsumption.md` section `## Two halves (read this first)` names the command.
- A test `test/test_toolchain_manifest.py`: regenerating for the committed manifest's own `release_tag` with its
  own `installed` date yields the committed manifest exactly (AC-4); a `not_installed` pattern drops its
  sources; a carried entry whose path the release lacks is dropped and reported.

## Out of scope

- `.claude/FRAMEWORK_COMMIT` (still written by update.txt step 7), the integrity test and the gate (UB-1: they
  keep reading `config/toolchain.json` as their single list).
- Running a promotion (that is the release this run cuts after the fixes land).

## Tests

Every acceptance criterion and unchanged-behaviour clause is pinned by a test. The tests need git and the
release tag (CI checks out with `fetch-depth: 0`).
E2E: not applicable — a repository maintenance tool; no runtime behaviour of a deployed system changes. CI's
`tests` group runs the new test.
