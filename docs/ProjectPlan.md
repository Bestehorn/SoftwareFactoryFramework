# Project Plan

## Overall plan with milestones
1. **Layout restructure, phase 1** — done 2026-11-07: one kind of asset per top-level directory
   (`docs/reports/directory-restructure-proposal-2026-11-07.md`).
2. **Self-hosting** — the first release `v2026.11.09` is installed into this repository as its toolchain
   (`docs/reports/self-hosting-proposal-2026-11-07.md` §9). From here on, work goes through the backlog.
3. **Forge-wrapper rewrite** — from the complete API reference in `docs/api-reference/`; tested against
   ephemeral `sff-test-*` repositories; reaches the toolchain by promotion.
4. **Renderer** (`src/framework/render.py`) and the **twin merge** into `clients/common/` — one source per agent,
   command and rule, rendered per client (restructure proposal §5).
5. **Split the setup prompts** into shared and per-client parts with thin entry files (restructure proposal §9).

## TODOs and open issues
The live list is the GitHub issue backlog of `Bestehorn/SoftwareFactoryFramework`, read with
`python scripts/github_wrapper.py list-issues`. Known debt recorded at the self-install:
- the ephemeral-repository forge tests need their dedicated create/delete token.
