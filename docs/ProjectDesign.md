# Project Design

## Main design principles
- **The prompt drives, files carry the content.** An operator pastes a prompt; the agent installs files from a
  pinned export of the framework and merges them into the project without overwriting project-specific content.
- **One kind of asset per directory; installable trees mirror their destination** (restructure proposal §3).
- **Nothing is written twice:** content more than one client uses lives in `clients/common/`.
- **Mechanical enforcement over instruction:** rules state the norm; hooks (`src/hooks/`), tests and CI enforce it.
- **The repository is its own first consumer:** it runs on its own last release, never on its working tree
  (`docs/reports/self-hosting-proposal-2026-11-07.md`).

## Overall architecture
- `prompts/` — the setup and update procedures (specification and entry point).
- `clients/` — natural-language assets installed into `.claude/` and `.kiro/`.
- `src/hooks/` — the hook runtime: one dispatcher per event (`hooks.py`), the shared identity/state library
  (`hooklib.py`), gates discovered by file (`gate_*.py`, framework ORDER 10–90, project gates above 100).
- `src/payload/` — scripts installed into a project's `scripts/` and `test/`: the forge wrappers, the test and
  check runners, the suite semaphore, the merge steward, the memory compiler, the temp reaper.
- `templates/` — skeletons with placeholders and verbatim documents.

## Component interactions
- A session's harness calls the launcher registered in `.claude/settings.json`, which runs `hooks.py <event>`;
  the dispatcher runs that event's gates in order against the payload.
- Agents and commands read the rules (`.claude/rules/`), the on-demand docs (`.claude/docs/`) and the phase
  fragments (`.claude/specs/_workflow/phases/`); every remote operation goes through the forge wrapper.
- `scripts/run_checks.py` is the one pipeline definition, run by CI and locally; it calls `scripts/run_tests.py`.
- A promotion: release tag → `prompts/update.txt` against this repository → `config/toolchain.json` and
  `.claude/FRAMEWORK_COMMIT` rewritten → one PR.
