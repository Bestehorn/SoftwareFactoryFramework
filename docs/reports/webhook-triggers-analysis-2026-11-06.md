# GitHub and GitLab webhooks: capabilities, local hookup, new-issue triggers (2026-11-06)

**Scope.** This document answers three questions:

- What webhooks do github.com and a self-managed GitLab (here: `gitlab.aws.dev`) offer?
- How can a client on a local machine without a public endpoint receive them?
- How is "a new issue was put on the backlog" recognised in a webhook, and turned into a signal that starts new work?

**Sources.**
- Vendor documentation (docs.github.com, docs.gitlab.com), fetched 2026-11-06.
- GitLab source code, where the docs are silent.
- Two unauthenticated probes against `gitlab.aws.dev`.

**Evidence marks.** Every claim carries one of these:

| Mark | Meaning |
|---|---|
| **[doc]** | Stated by vendor documentation |
| **[source]** | Read from vendor source code |
| **[measured]** | Observed today |
| **[inferred]** | My reasoning |
| **[unverified]** | Could not be confirmed |

## Summary

1. **Both platforms work the same way.**
   - A subscribed event sends an HTTP POST with a JSON body to a URL you configure.
   - The receiver must answer 2xx within **10 s** [doc].
   - **Neither platform retries a failed delivery automatically** [doc].
   - Failed deliveries can be re-sent by hand or through the API: GitHub within 3 days; GitLab 2 days in the UI and 7 days through the API.
2. **Each platform has an issue event that covers backlog changes.**
   - GitHub sends `issues` with actions such as `opened`, `labeled` and `assigned`.
   - GitLab sends `Issue Hook` with `open`/`update`/`close`/`reopen`, and shows label changes as a previous/current diff.
   - A board move appears as a label change on GitLab. On GitHub it appears as a `projects_v2_item` field change, but only for organization-owned projects.
3. **Authenticity differs.**
   - GitHub signs every delivery with HMAC-SHA256.
   - GitLab sends a plain shared secret header. It adds an HMAC signing token only from **19.0** (generally available in 19.1).
4. **A machine behind NAT or VPN cannot receive webhooks directly.** There are four workable hookups, compared in §4:
   - a forwarder or tunnel, which is for testing only;
   - a relay you own that queues events;
   - the platform's CI runner on the machine, which connects outbound;
   - polling instead of webhooks.
   - Because nothing is retried, any hookup that can be offline needs a reconciliation poll as well.
5. **Both platforms can start work from an issue event without a receiver of your own.**
   - GitHub Actions `on: issues` runs a workflow for issue events.
   - On GitLab, a webhook pointed at the pipeline-trigger URL starts a pipeline, and the job receives the payload as `TRIGGER_PAYLOAD`.
6. **What `gitlab.aws.dev` adds:**
   - Its version is unknown. The `User-Agent` of the first test delivery reveals it.
   - Unauthenticated API calls are redirected to corporate SSO [measured].
   - Its payloads are internal data, so public relays are unsuitable [inferred].

## 1. The common model

| Aspect | Both platforms |
|---|---|
| Transport | HTTPS POST, JSON body, one request per event |
| Acknowledgement | 2xx within 10 s. Answer first, then process asynchronously; GitHub explicitly recommends a queue [doc] |
| Retries | None automatic. Manual or API redelivery only [doc] |
| Duplicates | Possible after redelivery or timeouts. Deduplicate on the delivery id (GitHub `X-GitHub-Delivery`; GitLab `Idempotency-Key` or `webhook-id`) [doc] |
| Ordering | Not guaranteed. GitHub says deliveries can arrive out of order [doc]; GitLab documents nothing [unverified] |
| Trust | Verify the signature or secret on every request, then treat the payload as a hint and re-read the issue through the API before acting [inferred] |

## 2. GitHub (github.com)

### 2.1 Where webhooks can be configured

| Scope | Who can create it | Limit | Notes |
|---|---|---|---|
| Repository | Repo owner or admin | 20 hooks per event type | Events of that repo only |
| Organization | Org owners | 20 per event type | Org events plus all repos the org owns |
| GitHub App | App owner. One hook per app, created with the app | 1 | Starts with no events subscribed; can be deactivated, not deleted |
| Enterprise | Enterprise owners (Enterprise Cloud) | 20 per event type | Not relevant for small orgs |

- **There are no webhooks for personal accounts** [doc]: "You cannot create webhooks for individual user accounts". Repos under a user account need one hook per repo, or a GitHub App installed on them.

### 2.2 Events relevant to the backlog

**`issues`** [doc]
- **Actions:** `opened`, `edited`, `labeled`/`unlabeled`, `assigned`/`unassigned`, `milestoned`/`demilestoned`, `typed`/`untyped`, `transferred`, `closed`, `reopened`, `deleted`, `locked`/`unlocked`, `pinned`/`unpinned`, `field_added`/`field_removed`.
- **Payload:**
  - `issue`, including its `labels`, `assignees` and `author_association`.
  - `sender`: who performed the action.
  - For `labeled`, the `label` object.
  - For `edited`, `changes.title.from` and `changes.body.from`.

**Other events** [doc]
- **`issue_comment`:** `created`, `edited`, `deleted`. It also fires for comments on pull requests.
- **`sub_issues`:** parent and child added or removed.
- **`projects_v2_item`:** a card on a Projects (v2) board.
  - `edited` carries `changes.field_value` with the field name and from/to values, so a "Status: Todo → Ready" move is visible [doc].
  - **Available only for organization-owned projects** [doc]. User-owned projects get no webhooks [inferred from the org-only wording plus the no-user-webhooks rule].
  - Still in public preview.

### 2.3 Delivery

- **Timeout:** 10 s. GitHub "terminates the connection and considers the delivery a failure" [doc].
- **No automatic redelivery:** "GitHub does not automatically redeliver failed deliveries" [doc].
- **Manual redelivery:** in the UI or through the REST API (`GET …/hooks/{id}/deliveries`, `POST …/deliveries/{id}/attempts`) for the past 3 days. The deliveries log, with headers, payload and response, is also kept for 3 days [doc].
- **Scripted redelivery (GitHub's own example):**
  - A scheduled Actions workflow runs every 6 h and redelivers every GUID that has no successful attempt [doc].
  - It needs a personal access token, because `GITHUB_TOKEN` lacks the permission [doc].
- **Failing endpoints are not disabled.** No auto-disable for a failing endpoint is documented [doc].
- **Latency and throttling:** delivery "can take a few minutes", and under load GitHub may throttle deliveries [doc].
- **Payload cap:** 25 MB. Larger payloads are not delivered [doc].
- **Headers:**
  - `X-GitHub-Event`
  - `X-GitHub-Delivery` (a GUID, constant across redeliveries)
  - `X-GitHub-Hook-ID`
  - `X-GitHub-Hook-Installation-Target-Type` and `-ID`
  - `X-Hub-Signature-256`
  - `User-Agent: GitHub-Hookshot/…`
- **`ping`:** a `ping` event is sent when a hook is created [doc].

### 2.4 Security

- **Signature:** `X-Hub-Signature-256` is `sha256=` followed by the HMAC-SHA256 hex digest of the raw body, keyed with the hook's secret. Compare in constant time [doc].
  ```python
  expected = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
  ok = hmac.compare_digest(expected, request.headers["X-Hub-Signature-256"])
  ```
- **Source addresses:** the `hooks` ranges from `GET /meta`. GitHub says to query the API directly every time, because the ranges change [doc].
- **TLS:** certificate verification is on by default, and turning it off is "strongly" discouraged [doc].
- **Loopback URLs:** `localhost` and `127.0.0.1` are rejected as hook URLs [doc].
- **Private systems:** GitHub recommends a reverse proxy that accepts only HTTPS POST from the `hooks` ranges and validates signatures [doc].

### 2.5 Local development tooling

- **`gh webhook forward`** (the `cli/gh-webhook` extension) [doc][source]:
  - It creates a temporary hook on the repo or org, and GitHub streams its deliveries over a WebSocket to a local URL.
  - Only one forwarder per repository or organization can run at a time.
  - It is "not supported for use in production environments".
- **smee.io:** GitHub's documented relay for testing; "You should not use smee.io … in production" [doc].

### 2.6 Built-in alternative: GitHub Actions

- **`on: issues` with `types: [...]`** runs a workflow for issue events. The workflow file must be on the default branch [doc].
- **Trigger boundaries** [doc]:
  - `projects_v2_item` and `sub_issues` are **not** workflow triggers.
  - `repository_dispatch` and `workflow_dispatch` start a workflow from an API call.
- **Recursion guard:** events caused by `GITHUB_TOKEN` start no new workflow runs, except `workflow_dispatch` and `repository_dispatch` [doc].
  - Example: a label set by another workflow does **not** trigger `on: issues`.
  - The docs say nothing about whether webhooks still fire for such events [unverified].
- **Self-hosted runners** [doc]:
  - They need only outbound HTTPS on port 443.
  - A job no runner picks up is queued for at most 24 h, then fails.
  - GitHub warns that self-hosted runners "should almost never be used for public repositories".
- **Polling as a fallback** [doc]:
  - `GET /repos/{owner}/{repo}/issues?since=…` accepts `If-None-Match`, and a 304 "does not count against your primary rate limit".
  - The REST rate limit is 5,000 requests/h per user.

## 3. GitLab (self-managed)

### 3.1 Where webhooks can be configured

| Scope | Who can create it | Tier | Notes |
|---|---|---|---|
| Project | Maintainer or Owner | All tiers | Default limit 100 per project |
| Group | Owner | **Premium or Ultimate** | Fires for all projects in the group and its subgroups. Default limit 50 per group |
| System hook | Administrator | All tiers | **Carries no issue events.** Only group, user, project, membership, key events, plus optional push, tag and MR events |

If the same URL is configured on a group and on one of its projects, both fire [doc].

### 3.2 Events relevant to the backlog

**`Issue Hook`** [doc]
- **Object kinds:** issues send `object_kind: "issue"`. Tasks, epics and other work items send `object_kind: "work_item"`.
- **Actions:** `object_attributes.action` is `open`, `update`, `close` or `reopen`.
- **Who:** `user` is the person who triggered the event.
- **Changes:** each changed field appears as `{"previous": …, "current": …}`, e.g. `changes.labels.previous` and `changes.labels.current` (arrays of label objects).
- **Detecting "label `ready` added":**
  - For `update`: `ready` is in `changes.labels.current` and not in `changes.labels.previous`.
  - For `open`: `ready` is in the top-level `labels` array. An issue created with labels apparently carries no label diff [source, unverified].
- **Board moves:**
  - Moving between label lists removes one label and adds another, so it shows up as the same label diff [doc].
  - Status lists (Premium, 18.4+) add a `status` attribute that the docs don't describe [source].
- **Confidential issues:** these need the separate **Confidential issues events** trigger, sent as `Confidential Issue Hook` [doc][source].

**Other events** [doc]
- **`Note Hook`:** comments on issues, MRs, commits and snippets.
- **`Emoji Hook`:** reactions, generally available in 17.5.

### 3.3 Delivery

- **Timeout:** 10 s by default. Self-managed admins can raise it with `gitlab_rails['webhook_timeout']`; no maximum is documented [doc][source].
- **No automatic retry:** the docs only tell receivers to "prepare for duplicate events if a webhook times out". In the code, HTTP errors and timeouts are logged, not retried [doc][source].
- **Auto-disable of failing hooks:**
  - After 4 consecutive failures the hook is disabled temporarily, backing off from 1 min to 24 h.
  - After 40 failures it is disabled permanently (17.11+). A successful test request re-enables it.
  - **On self-managed this is off by default for project hooks** (feature flag `auto_disabling_web_hooks`) [doc][source].
- **Event log:** the **Recent events** UI covers 2 days, and **Resend Request** reuses the same `Idempotency-Key`. Through the API, `GET /projects/:id/hooks/:hook_id/events` covers 7 days (17.3+), and `POST …/resend` (17.4+) allows 5 per minute [doc].
- **Headers** [doc]:

| Header | Since | Carries |
|---|---|---|
| `X-Gitlab-Event` | — | `Issue Hook`, `Note Hook`, … |
| `X-Gitlab-Token` | — | The secret token, in plain text |
| `X-Gitlab-Event-UUID` | 14.8 | Event id |
| `X-Gitlab-Instance` | 15.5 | Instance hostname |
| `X-Gitlab-Webhook-UUID` | 16.2 | Hook id |
| `Idempotency-Key` | 17.4 | Constant across retries and resends |
| `webhook-id`, `webhook-timestamp`, `webhook-signature` | 19.0 (generally available 19.1) | Standard Webhooks signing |
| `User-Agent` | — | `GitLab/<version>`, which tells you the instance version |

### 3.4 Security

- **Secret token:** sent verbatim in `X-Gitlab-Token`. Compare in constant time. The docs now call this "not recommended" [doc].
- **Signing token (19.0+, generally available 19.1)** [doc]:
  - HMAC-SHA256 over `{webhook-id}.{webhook-timestamp}.{body}`, sent as `v1,<base64>`, with a `whsec_` key, following the Standard Webhooks specification.
  - The key is shown once only.
  - It can coexist with the secret token during a migration.
- **Other options** [doc]:
  - Custom headers: up to 20 per hook, 17.0+.
  - Custom payload templates: 17.0+. They cannot reach into arrays such as label lists.
  - URL masking for secrets in the URL: 15.7+.
  - Per-hook SSL verification.
  - One instance-wide mutual-TLS client certificate (self-managed only).

### 3.5 Admin restrictions on where webhooks can go

All of these are under **Admin > Settings > Network > Outbound requests** [doc]:
- **Local network:** blocked by default. This covers the instance's own address and private ranges (10/8, 172.16/12, 192.168/16, 127/8, …). "Allow requests to the local network from webhooks and integrations" lifts it.
- **Allow-list:** up to 1000 entries.
- **Filter mode:** "block all except the allow-list".
- **DNS rebinding protection:** on by default.
- **Cloud metadata endpoints:** always blocked from 19.5.
- **Rate limit:** off by default on self-managed (`web_hook_calls`) [doc].

### 3.6 Local development tooling

- **GitLab documents no equivalent of smee.io or `gh webhook forward`.**
- **`glab` has no webhook forwarding or event-streaming command.**
- **What the troubleshooting page suggests** [doc]:
  - public inspectors such as webhook.site, with a warning about sensitive data;
  - a local GitLab Development Kit;
  - a small local receiver, which needs the local-network setting.

### 3.7 Built-in alternative: webhook → pipeline

- **The pattern** [doc]:
  - Use the pipeline-trigger URL as the webhook URL: `https://<host>/api/v4/projects/<id>/ref/<branch>/trigger/pipeline?token=<trigger token>`. Creating the trigger token needs Maintainer.
  - GitLab starts a pipeline, and the job receives the webhook body as the file variable **`TRIGGER_PAYLOAD`** (13.9+).
  - `rules` can select such pipelines with `$CI_PIPELINE_SOURCE == "trigger"`.
- **Caveats:**
  - The docs show the pattern for push and tag events; issue events should work the same way [unverified].
  - If the instance's own hostname resolves to a private address, the local-network block in §3.5 may stop the hook from calling its own trigger URL [inferred].
  - Use URL masking for the token.
- **GitLab Runner:** it asks the instance for jobs (`POST /api/v4/jobs/request`), so a runner on a machine without a public endpoint needs only outbound access [doc].
- **Polling as a fallback** [doc]:
  - `GET /projects/:id/issues?updated_after=…&labels=…`.
  - Who added a label: `GET /projects/:id/issues/:iid/resource_label_events`.
  - No ETag support is documented for these endpoints.
  - API rate limits are off by default on self-managed.
- **Duo Agent Platform triggers** [doc]:
  - They can react to mention, assignment, and (from 19.1) "work item created".
  - They need Premium, and runners with Docker or Kubernetes executors.

### 3.8 What applies to `gitlab.aws.dev`

- **SSO in front of the API.** An unauthenticated `GET /api/v4/version` and `/api/v4/metadata` are redirected to `idp.federate.amazon.com` [measured].
  - Anything outside the instance that calls its API needs a token or SSO cookie that the proxy accepts. That includes a poller, a relay re-reading issues, and a runner.
- **Unknown version.** It decides HMAC signing (19.0+), `Idempotency-Key` (17.4+) and the hook events API (17.3+). Read it from the `User-Agent` of the first test delivery.
- **Internal payloads.** Third-party relays and inspectors (smee.io, webhook.site, ngrok's service) are unsuitable unless policy explicitly allows them [inferred].
- **Unknown egress.** Whether the instance may deliver to an endpoint outside the corporate network, such as your own AWS endpoint, is an admin question.

## 4. Hooking up a local client without a public endpoint

| Topology | How it works | Works after the machine was offline? | Cost and risk | Verdict |
|---|---|---|---|---|
| **A. Direct** | The platform POSTs straight to the machine | — | No reachable URL behind NAT or VPN | Not possible |
| **B. Forwarder or tunnel** | `gh webhook forward`, smee.io, ngrok, Cloudflare Tunnel or zrok relays the POST to a local port | **No.** Deliveries made while it is down are lost (§1). On GitLab, if auto-disable is on, repeated failures also disable the hook | Payloads pass through a third party; a local port is exposed. GitHub calls its own two tools dev-only | Testing only |
| **C. A relay you own** | A small HTTPS endpoint (e.g. a Lambda Function URL or API Gateway) verifies the signature or token, answers 2xx at once, and puts `{host, project, issue, action, delivery_id}` on a queue (e.g. SQS FIFO, deduplicated on delivery id). The local client long-polls the queue outbound | **Yes.** The queue keeps events (SQS up to 14 days) | One small cloud stack, the webhook secret stored there, and credentials on the machine to read the queue | Good for GitHub. For GitLab, only if the instance may reach the endpoint (§3.8) |
| **D. The platform's runner on the machine** | GitHub: `on: issues` workflow with `runs-on: [self-hosted, …]`. GitLab: webhook → pipeline trigger (§3.7) → a job for a runner on the machine. Both connect outbound only | **Partly.** GitHub queues a job up to 24 h; GitLab keeps it pending until a runner takes it | A persistent runner on the machine, registered per repo for user-owned GitHub repos. GitHub warns against it for public repos. Runner services run without a desktop session | Works with no extra infrastructure; operationally heavy |
| **E. Poll instead of webhooks** | Periodically list open issues updated since the last poll, filtered by label | **Yes.** It reads current state, not events | No infrastructure. GitHub conditional requests that return 304 are free; GitLab polls count, but self-managed limits are off by default | Simplest and most robust; latency equals the poll interval |

**Why a poll is needed in every topology**
- A webhook says "this changed", and a lost delivery loses the change. Neither platform retries.
- Any receiver that can be offline (a laptop that sleeps, reboots or leaves the VPN) should run a periodic reconciliation poll as well.
- With that poll in place, webhooks become a latency improvement, not the source of truth [inferred].

**What any receiver must do (topologies B–D)**
1. Answer 2xx immediately, and do the work afterwards.
2. Verify authenticity.
   - GitHub: the HMAC in §2.4.
   - GitLab before 19.0: a constant-time compare of `X-Gitlab-Token`.
   - GitLab 19.0+: the `webhook-signature` HMAC.
3. Drop duplicates by delivery id (§1).
4. Re-read the issue through the API before acting, because payloads can be stale or out of order.

## 5. Recognising "a new issue is on the backlog" and starting work

**Choose the signal**

| Signal | GitHub | GitLab |
|---|---|---|
| Issue created | `issues` + `opened` | `Issue Hook` + `action: open` |
| Issue marked ready (recommended) | `issues` + `labeled` with `label.name == "<ready>"`, or `opened` with the label already in `issue.labels` | `action: update` with the label in `changes.labels.current` and not in `.previous`, or `action: open` with the label in `labels` |
| Moved to a board column | `projects_v2_item` + `edited` with a Status change (org projects only; not an Actions trigger) | Same as the label signal, because board lists are label-based |

**Recommendations**
- **Trigger on an explicit "ready" label, not on `opened`.** A freshly opened issue is often unrefined. On public repositories anyone can open one, and the issue text would become the instruction for the work.
- **Check who applied the label:**
  - GitHub: the payload's `sender`, then `GET /repos/{o}/{r}/collaborators/{user}/permission`.
  - GitLab: the payload's `user`, then the member's access level.
  - Ignore events caused by your own automation's account.
- **Hand off, don't work in the receiver.** It enqueues `{host, project, issue_number, action, delivery_id}`, and whatever starts the work consumes the queue and re-reads the issue.

**Platform-native examples**

GitHub Actions. Use only safe fields such as the number in `run:`. Interpolating `issue.title` or `issue.body` into a shell is a script-injection risk [doc].
```yaml
on:
  issues:
    types: [opened, labeled]
jobs:
  start-work:
    if: >-
      (github.event.action == 'labeled' && github.event.label.name == 'ready') ||
      (github.event.action == 'opened' && contains(github.event.issue.labels.*.name, 'ready'))
    runs-on: ubuntu-latest
    steps:
      - run: echo "issue ${{ github.event.issue.number }} is ready"
```

GitLab, with the project webhook (Issue events) pointing at the pipeline-trigger URL from §3.7:
```yaml
start-work:
  rules:
    - if: $CI_PIPELINE_SOURCE == "trigger"
  script:
    - python3 scripts/on_issue_event.py "$TRIGGER_PAYLOAD"   # reads the JSON file, applies the label test above
```

## 6. Open points

1. **`gitlab.aws.dev`'s version, tier and outbound policy.** These decide which of §3.3–3.7 apply. One test hook answers the version; the egress and local-network settings need the instance admins.
2. **Whether GitHub webhooks fire for events caused by `GITHUB_TOKEN`.** Only the workflow-run guard is documented (§2.6).
3. **Whether a GitLab issue created with labels carries any label diff.** Source suggests not (§3.2); a test hook would confirm.
4. **Whether the webhook → pipeline-trigger bridge works for Issue events on `gitlab.aws.dev`.** The docs only show push and tag events (§3.7).

## Sources

**GitHub**
- https://docs.github.com/en/webhooks/types-of-webhooks
- https://docs.github.com/en/webhooks/webhook-events-and-payloads
- https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
- https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries
- https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks
- https://docs.github.com/en/webhooks/using-webhooks/automatically-redelivering-failed-deliveries-for-a-repository-webhook
- https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- https://docs.github.com/en/webhooks/using-webhooks/delivering-webhooks-to-private-systems
- https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks
- https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/testing-webhooks
- https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/using-the-github-cli-to-forward-webhooks-for-testing
- https://github.com/cli/gh-webhook
- https://docs.github.com/en/rest/repos/webhooks
- https://docs.github.com/en/rest/meta/meta
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://github.blog/changelog/2024-06-27-github-issues-projects-graphql-and-webhook-support-for-project-status-updates-and-more/

**GitLab**
- https://docs.gitlab.com/user/project/integrations/webhooks/
- https://docs.gitlab.com/user/project/integrations/webhook_events/
- https://docs.gitlab.com/user/project/integrations/webhooks_troubleshooting/
- https://docs.gitlab.com/administration/system_hooks/
- https://docs.gitlab.com/administration/instance_limits/
- https://docs.gitlab.com/security/webhooks/
- https://docs.gitlab.com/api/project_webhooks/
- https://docs.gitlab.com/ci/triggers/
- https://docs.gitlab.com/ci/jobs/job_rules/
- https://docs.gitlab.com/runner/
- https://docs.gitlab.com/api/issues/
- https://docs.gitlab.com/api/resource_label_events/
- https://docs.gitlab.com/administration/settings/user_and_ip_rate_limits/
- https://docs.gitlab.com/user/duo_agent_platform/triggers/
- https://gitlab.com/gitlab-org/gitlab/-/blob/master/app/workers/web_hook_worker.rb
- https://gitlab.com/gitlab-org/gitlab/-/blob/master/config/feature_flags/ops/auto_disabling_web_hooks.yml
- https://gitlab.com/gitlab-org/gitlab/-/blob/master/ee/lib/ee/gitlab/hook_data/issue_builder.rb
