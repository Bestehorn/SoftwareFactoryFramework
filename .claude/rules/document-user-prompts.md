# Document User Prompts in Spec Sessions

For spec sessions (any directory under `.claude/specs/`), preserve the conversation:

1. `requirements.md` and `design.md` (`change.md` for a tier-S spec) each have a "User Prompts"
   section that captures the verbatim prompts that drove the current state of the document —
   including the first prompt that initiated the spec.
2. `prompts.md` in the same spec directory captures the full chronological conversation: every user
   message and every assistant response.
3. When the user asks for updates, append the new prompts to "User Prompts" in those documents, and
   to `prompts.md`.
