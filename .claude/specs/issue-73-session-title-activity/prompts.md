# Prompts — issue #73

## 2026-11-26 — operator

"Did the new mechanism get integrated into the agents? Give me an overview of the new flow. Generally, the session
title should always reflect what the agent is doing. As we recently tested, agents have the ability to change their
session label (at least in Claude Code. What about Kiro?)"

## 2026-11-26 — response

The tip-only deploy guard shipped in v2026.11.26 and needed no agent change. Session titles today name only the
claimed issue set, and only the orchestrator and its three commands rename. Kiro documents no way to rename a session
(kirodotdev/Kiro#7836, #6091). Proposed: `<subject> · <activity>` for every main session from one shared doc, renamed
at each phase transition, plus the missing delivery.md refusal row in the same PR.

## 2026-11-26 — operator

"I agree to the point about session titles. We should implement this as an issue, i.e., file an issue and then we
can execute this."

## 2026-11-26 — response

Filed issue #73 through issue intake (which found #6091 closed as a duplicate of the open #5471), claimed it, and
started this spec.
