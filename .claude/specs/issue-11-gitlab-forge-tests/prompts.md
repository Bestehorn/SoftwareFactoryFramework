# Prompts — issue #11 (real-GitLab integration tests)

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run, 2026-11-11: the question on issue #11 asked for a GitLab test target and token (comment 6808250293).
3. User, 2026-11-13: "The token is updated. COntinue using it. We will deal with gitlab once github works."
4. User, 2026-11-16: "Let's set up the GitLab test target for #11; walk me through the exact steps I need to perform
   on gitlab."
   Answer: a private gitlab.com group, a group service account invited as Owner, its token with scope `api`, stored as
   the Actions secret `SFF_GITLAB_TEST_TOKEN` and in `credentials/gitlab-sff-testing-pat.txt` (comment 6923784402).
5. User, 2026-11-21: "There is no "Service Accounts" submenu in the settings of the group"
   Answer: the page shows for a top-level group's Owner on gitlab.com; on a self-managed or Dedicated instance only for
   an administrator, or when the administrator lets group owners create service accounts; corrected steps per host
   (comment 7061531929).
6. User, 2026-11-22: "The group URL is https://gitlab.aws.dev/bestehorn-sff-test" (comment 7077139116).
   Answer: every request to gitlab.aws.dev, token or not, is redirected by its load balancer to the corporate
   sign-in, so it cannot be the target; options gitlab.com, a GitLab inside the CI job, or the administrators
   (comment 7077150394).
7. User, 2026-11-22: "Use gitlab.com"
   Answer: the gitlab.com steps of comment 6923784402 stand; the suite is built now, its real run waits for the token.
8. User, 2026-11-24: "I have created a new gitlab account on gitlab.com. Provide me with the steps to create the secret."
   Answer: the gitlab.com group, service account, Owner membership and `api` token steps, then the GitHub Actions
   secret `SFF_GITLAB_TEST_TOKEN` (issue #11).
