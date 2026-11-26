# The session title says what the session is doing (Claude desktop app)

Installed at `.claude/docs/session-title.md`; read on demand. In the desktop app's sidebar every session otherwise
carries an auto-generated title, so the operator has to open a session to learn what it holds and where it stands.
Every MAIN session therefore keeps its own title equal to WHAT it works on and WHAT it is doing now.

## The rule

- **Form.** `<subject> · <activity>`: the subject, a middle dot between two spaces, then the activity in one to three
  lowercase words from "The forms" below. The subject comes first, so a title the sidebar cuts short still names it.
  A finished session reads `<subject> — done`. No `#`, no emoji, no words of your own beyond the forms'.
- **When.** Rename each time the subject or the activity changes — at each phase transition the run records (a new
  `Phase:` value), at the step of a command that starts a new activity, and in an interactive session when the
  operator starts a different task or the work moves to another of its activities — and at no other time: never
  within a phase, never per tool call, never to report progress.
- **How.** `mcp__ccd_session_mgmt__set_session_title` with `session_id: "self"`. The tool is deferred: load it once
  with `ToolSearch` `select:mcp__ccd_session_mgmt__set_session_title`. A command that tells the session to rename
  allowlists the tool in `allowed-tools`; an agent that does names it in its `tools` line.
- **Who.** Only the main session can rename itself: never delegate it. A subagent ignores this rule.
- **The end.** A flow's last rename, `<subject> — done`, comes before the close-out; no rename follows the SESSION
  verdict: on `SESSION: CAN CLOSE` the archive is the turn's last call.
- **A refused rename is not a blocker.** The app asks the operator before it replaces a title they typed, and
  declines where nobody can approve. A decline or an error changes nothing else: keep working, rename again at the
  next change, and never ask about the title.
- **Without the tool** — the CLI, and Kiro, which documents no rename an agent can call (kirodotdev/Kiro#7836 for the
  IDE, kirodotdev/Kiro#5471 for the CLI) — the session skips this rule; its state file and its issue notes still
  say where it stands.

## The forms

- **Issue work** — the orchestrator, `/work-issue`, `/auto-work`, `/issues-work`. Subject: the issue set, spelled as
  the orchestrator's "Session title" section says. Activities: `selecting`, `spec`, `spec review`, `implementing`,
  `verifying`, `CI`, `queued`, `merging`, and `needs you` while `AWAITING_USER` holds a reason. When the set holds
  more than one issue, the activity names the issue it concerns first. Examples: `Issue 77 · CI`,
  `Auto-Work 12, 15 · 15 implementing`.
- **Spec workflow** — `spec-conductor`, `/spec-new`, `/spec-review`, `/spec-tasks`, `/spec-implement`. Subject:
  `Spec <feature>`. Activities: `prompt`, `spec`, `spec review`, `tasks`, `implementing`, `verifying`, `report`,
  `needs you`. The review phases are `spec review`; SETUP is `prompt`; DONE is `Spec <feature> — done`. Example:
  `Spec deploy-guard · spec review`.
- **Close-out** — `/close-session` run on its own. Subject: the one the title already names. Activity:
  `closing out`, set at its first step. A flow whose last step runs the close-out checks (`/work-issue`, the
  orchestrator) keeps its `<subject> — done`. Example: `Issue 77 · closing out`.
- **Resume** — `/continue-work`. Subject and activity: the resumed run's, set once from its recorded state
  (`SESSION_ISSUES`, `MODE` or `CURRENT_SPEC`, and `Phase`); the resumed flow renames from then on. Example:
  `Auto-Work 12 · CI`.
- **Supervisor** — `/supervise`. Subject: `Supervisor`. Activities: `scanning`, `resuming`. Example:
  `Supervisor · resuming`.
- **Memory** — `/compile-memory`. Subject: `Memory`. Activities: `measuring`, `compiling`, `proving`, `committing`.
  Example: `Memory · compiling`.
- **An interactive session** — no agent, no command. Subject: the operator's current task in two to five words.
  Activities: `reading`, `changing`, `testing`, `CI`, `answering`, `needs you`. Example: `Deploy guard fix · CI`.
