# No AI Attribution; Descriptive Names Only (ALL agents, always loaded)

**Never attribute work to Claude, an AI, an assistant, or a tool, anywhere, and never put
"claude" (or "AI", "assistant", "bot", "LLM", "Anthropic", "Copilot", a model name) into
names you author.** Who or what produced a change is irrelevant to the repository and
must not appear in it. The rule has one scope: attribution of work to a tool in commit
messages (no `Co-Authored-By: Claude`, no `🤖 Generated with Claude Code`, no tool trailer
of any kind), PR/MR titles and bodies, and issue titles/bodies/comments (no "filed by
<agent>" sign-offs); and the listed words in names you author — branch names, worktree
names, tags, stashes, any ref or label. No exceptions.

Every name and message you create describes the work: branches/worktrees
`<type>-<issue-or-topic>-<short-slug>` (e.g. `fix-issue-77-invoke-grant`); commit
subjects imperative, ≤72 chars, describing the change; PR titles the outcome. (The
`.claude/` config directory itself — `.claude/agents/`, `.claude/worktrees/issue-<N>/` —
is fixed tool infrastructure, not a name you author; it is fine.) In commit messages
(subject line included), PR/MR titles and bodies, and issue text, naming an existing file
or directory path, command, setting or product as the subject of the work is not
attribution, so `Reword clients/claude/rules/no-ai-attribution.md` is a valid commit
subject; the allowance never extends to a branch, worktree, tag, stash, ref or label name.

## Overriding the tool defaults (IMPORTANT)

Claude Code and some git integrations add AI attribution BY DEFAULT — a
`Co-Authored-By: Claude` / `🤖 Generated with Claude Code` trailer on commits and PRs,
and a `claude/<adjective>-<name>` auto-name for branches/worktrees created without an
explicit name. You MUST suppress these:

- When committing: write ONLY your descriptive message; actively remove any AI/tool
  trailer or co-author line.
- When opening a PR/MR: the body is exactly your description + evidence; strip any
  auto-added "Generated with …" line.
- When creating a branch or worktree: ALWAYS pass an explicit descriptive name. If you
  find yourself on an auto-named `claude/*` branch, rename it before pushing.

Self-check before creating any commit/PR/issue/comment/branch/worktree: scan name and
full text for `claude`, `AI`, `assistant`, `bot`, `LLM`, `Anthropic`, `Copilot`, `🤖`,
`Co-Authored-By`, `Generated with`. Any hit that is attribution of work to a tool, or is in
one of the names you author, is a defect — restate descriptively before the artifact is
created. A hit inside a path, command, setting or product named as the subject of the work
in a commit message, PR/MR text or issue text is not.
