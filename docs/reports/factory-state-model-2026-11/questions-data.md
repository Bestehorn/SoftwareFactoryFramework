# How questions to the operator spread over an issue's life (2026-11-10)

> Record from the factory state-model design discussion. Aggregates only: the question texts themselves are not
> reproduced, because they contain personal and customer details.

## Source and method

- **Population.** Claude Code transcripts of one workstation, four projects (chess, AWSBedrockGateway, Insights
  Analyzer, ccet), sessions since 2026-10-01: 133 issues worked, of which 51 asked the operator something.
- **What counts as a question:** an `AskUserQuestion` call (archive prompts excluded), or an `AWAITING_USER` write in
  the run state.
- **Attribution:** to the issue current at that moment.
- **Episode:** questions less than one hour apart form one episode.
- **Answer time:**
  - a blocking `AskUserQuestion` is timed to its tool result (the answer);
  - an `AWAITING_USER` write is timed to the next human message in the same session.
- **Caveat.** Many of these sessions were interactive, with the operator present, which invites questions an
  unattended worker would settle with the recommended option. The figures are an upper bound for an unattended
  factory.

## Measurements

| Measure | Value |
|---|---|
| Asking issues with more than one question episode | 55 % (only 45 % asked in a single episode) |
| Episodes per asking issue | p50 2, p75 2, p90 4, p95 8, max 21 |
| Hours between consecutive episodes of one issue (n = 77 gaps) | p50 10.2, p75 17.8, p90 31.5, p95 59.9, max 88.8 |
| Hours from the first to the last episode of an issue | p50 1.8, p75 19.1, p90 54.9, p95 80.1, max 411.8 |
| Asking issues with a further episode ≥ 4 h / ≥ 8 h / ≥ 24 h after the first | 45 % / 37 % / 23.5 % |
| Blocking `AskUserQuestion`: hours until the answer (n = 109) | p50 2.1, p75 7.3, p90 15.0, p95 18.3, max 44.7; 24 % took ≥ 8 h |
| `AWAITING_USER`: hours until the next human message in that session | p50 7.0, p75 14.1, p90 18.2; 13 of 96 never got one in that session |
| Share of an asking issue's transcript span spent waiting for an answer | p50 28 %, p75 58 %, p90 94 % |

## What the late questions were

These are the 95 questions asked ≥ 8 h after the issue's first question. The classification is mine, made row by
row from the question texts.

| Kind | Count | Where it belongs in the design |
|---|---|---|
| One human review task asked item by item (one issue: 107 sentences to judge, over about 400 h) | 38 | one review sheet (design §12.6) |
| Environment health: security findings blocking deploys, quotas, refused CI runners, wedged host test slots, a desktop MCP policy, test data | 23 | the environment owner and `delivery-status`, one record per root cause (§12.4) |
| Dependency on another issue, merge contention | 8 | `blocked-by`, the merge steward (§12.4) |
| Expired credentials | 7 | the environment owner (§12.4) |
| Standing permissions: dispatch the prod deploy, merge another issue's PR, change IAM in the shared dev account, cut a release | 6 | policy, asked once per project (§12.5) |
| Release risk sign-off | 5 | a genuine human decision; the optional approval setting (§12.8) |
| Inputs that belonged in the first batch (accounts, data folders) | 3 | the decision inventory (§12.2) |
| Genuine late design decisions (how to re-land after a revert) | 3 | legitimate late questions |
| Review cap reached | 2 | automatic approval with residuals (§13) |

One environment root cause, the same security finding, was asked about from four different issues.
