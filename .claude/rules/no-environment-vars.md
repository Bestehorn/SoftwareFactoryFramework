# No Environment Variables (CRITICAL)

This system runs multiple projects on shared hardware. Setting shell environment variables leaks
state between projects.

1. Never `set`, `setx`, `export`, or `$env:VAR=...` for ANY variable, including `GITHUB_TOKEN`,
   `GITLAB_TOKEN` and any custom config variable.
2. Instead:
   - Git hosts: credentials are read from `credentials/` and `config/` by the project's wrapper
     scripts (`use-git-wrapper-scripts.md`).
   - Application config: load from config files at startup.

CLARIFICATION: the `env` block inside `.claude/settings.json` / `.claude/settings.local.json` and
the `terminal.integrated.env.*` block inside editor settings are NOT shell environment variables.
They are scoped configuration consumed by Claude Code or by one specific subprocess, and do not
pollute global state. Leave them alone.

CLARIFICATION 2 — the scoped TEMP DIRECTORY is permitted, and is the one case where NOT setting a
variable is the leak. `TMPDIR` / `TEMP` / `TMP` may point at this tree's ABSOLUTE `tmp/os-temp`
through scoped configuration — the `env` block of `.claude/settings.local.json` (the
`scoped-temp-init` SessionStart hook writes it), or a per-command prefix on the one invocation that
needs it. What stays forbidden is the global form: no `setx`, no `export` in a shell profile, no
`$env:TMPDIR=` that outlives the command. This serves rule 1: by default every project writes into
one global temp directory, so their residue is indistinguishable and nobody can safely clean it.
Scoping temp per tree makes every artifact attributable to the tree that made it, which is what lets
`scripts/reap_agent_temp.py` and `/close-session` clean it up.
