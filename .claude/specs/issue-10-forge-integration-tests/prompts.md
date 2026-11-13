# Prompts — issue #10 (forge integration tests)

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run, 2026-11-10: the question on issue #10 asked for the create/delete token (comment 6772287815).
3. User, 2026-11-12: "For github: Does this need a PAT or a classic token? If PAT, should this allow for general
   account access? Will the testing make sure that we cleanup created test repos? Do I need to create a separate
   github account for this or can I use my existing one?"
   Answer: a fine-grained token owned by a free test organization, All repositories, Administration write and
   Contents write; cleanup is AC-1 to AC-3; no separate account (issue #10 comment 6820424075).
4. User, 2026-11-12: "How many organizations can I create with a free account?"
   Answer: GitHub documents no limit; one organization is all the tests need.
5. User, 2026-11-12: "Where do I store the github PAT?"
   Answer: a git-ignored file under `credentials/` and the repository Actions secret `SFF_TEST_TOKEN`.
6. User, 2026-11-12: "I created the file and put the PAT into github-sff-testing-pat.txt in the credentials folder. Do
   I need to copy this file to all machines that run/work for this project?"
   Answer: only to a machine that runs the forge tests locally; CI uses the secret (issue #10 comment 6820621970).
7. User, 2026-11-12: "the org is called "bestehorn-sff-test"" (issue #10 comment 6828747536). The run resumed #10.
8. User, 2026-11-12: "How do I need to create the SFF_TEST_TOKEN Actions secret on github?"
   Answer: Settings, Secrets and variables, Actions, New repository secret, name `SFF_TEST_TOKEN`, the token as value.
