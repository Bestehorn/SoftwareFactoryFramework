---
description: Reconcile docs/ with the current implementation.
allowed-tools: Bash, Read, Edit, Grep, Glob
---
Synchronize documentation:
1. Read everything in docs/ and README.md.
2. Walk src/, scripts/, prompts/, clients/, templates/ to identify components, classes, entry points.
3. List discrepancies (docs missing components, docs describing removed components, outdated examples).
4. Update docs to match the current implementation.
5. Refresh `docs/forLLMConsumption.md` so it provides complete context for an AI assistant.
6. Report files updated and changes made.
