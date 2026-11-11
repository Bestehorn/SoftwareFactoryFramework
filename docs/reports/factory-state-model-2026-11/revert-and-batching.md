# Revert-first without the red hour: restore the environment fast, revert on trunk, attribute the batch (2026-11-09)

> Record from the factory state-model design discussion (2026-11-09 to 2026-11-11), copied from the working notes. Paths to working files were rewritten to this folder; the text is otherwise as written. Where it differs from `docs/design/factory-state-model/decisions.md`, that file wins.

Scope: research for the state model. It extends `docs/reports/red-pipeline-analysis-2026-11-02.md` (F1 to F6, the OSS
revert-first survey) and does not repeat that survey. The question: with revert-first as the default after a red
deploy or a red smoke check, how do we keep (a) the time the shared dev environment is non-functional and (b) the
time trunk is blocked well below "redeploy the last good commit, about an hour"?

Read for this report: `src/payload/scripts/merge_steward.py` (header, `verdict`), `clients/common/docs/delivery.md`
§4, `templates/ci/github-deploy.yml.template`, the state-model discussion, and, read-only, chess's
`.github/workflows/deploy-dev.yml` and `cdk/deploy.py`. Nothing outside this file was changed.

Markers: **[F]** established fact, with its source. **[I]** my inference or design proposal. **[M]** measured or
read in this repository or in chess.

---

## 0. The answer in brief

1. **Treat it as three clocks, not one.** *Non-functional time* (NFT): dev cannot serve. *Verification-blocked time*
   (VBT): no deploy that contains the culprit can go green, so no innocent issue gets verified. *Trunk-blocked time*
   (TBT): landings are paused. Chess's "50 hours red" was mostly VBT: CloudFormation had rolled `ChessEngine-Dev`
   back, so dev was probably still serving the old version for most of that time [I, from the report's §1].
2. **Split the revert into two tracks with different owners.**
   - **Track E, the environment restore**, belongs to the deploy job. It needs no attribution: put back the last
     green version of exactly the stacks that changed, from a cached build. Typical cost is minutes, not a
     rebuild [I].
   - **Track T, the trunk revert**, belongs to the steward. It does need attribution: revert the culprit's merge
     at the head of the next batch. The next normal deploy carries the innocent landings to verification
     without re-landing them.
3. **The restore is also the "passes without" test.** Last-good green on the same environment and same smoke
   check means the window caused the red. Last-good red too means infra, flake or drift, and nobody is blamed [I].
4. **Attribution can be mostly deterministic for deploy failures.** Diff the failing stack's synthesized template
   step by step over the landing window. The steward's train branches already hold the cumulative states, so
   the first step that changes the failing resource or export is the culprit [I]. Smoke failures need
   heuristics. A wrong guess costs one deploy, never a broken trunk.
5. **Near-zero NFT needs project infrastructure, offered as tiers.**
   - **Minimum:** cached artifact plus restore.
   - **Better:** smoke tests run as pre-traffic hooks, so traffic never reaches the broken version, and stateful
     stacks are split from stateless ones.
   - **Best:** blue/green or alias traffic shifting with bake time, and feature flags. Rollback is then a pointer
     flip in seconds. [F, sources in §3]
6. **The current code has two hazards that revert-first would trigger** (§6.6).
   - Verification by ancestry would close a reverted issue: the original landing commit stays an ancestor of
     every later trunk commit.
   - A rework branch re-merged after `git revert -m 1` brings back nothing unless the revert is reverted first.

---

## 1. What "red" costs today, and where the hour comes from

- **Measured:** chess's `Deploy dev` job had a median of 94 min (n = 20), followed by 9–21 min of harnesses
  [M: `docs/reports/wait-time-analysis-2026-10-25.md`]. That job runs everything in one go:
  - engine WASM ports and gates;
  - the release build;
  - then the deploy, stack by stack. `cdk/deploy.py` runs one
    `cdk deploy <stack> --exclusively --app "<python> app.py"` per stack, about 15 stacks in a fixed plan
    order, so the app is synthesized again for every stack [M: chess `cdk/deploy.py` docstring,
    `deploy-dev.yml` lines 207–356].
- **A naive revert** (git revert, then the normal deploy) pays all of that again: build, every synth, every stack.
  Track T then adds attribution and the revert's train CI (the steward docstring cites a 55-minute CI).
- **Rough totals [I]:**
  - NFT ≈ detection + attribution + revert CI + full deploy, about 2.5–3 h.
  - VBT is about the same.
- **Most of that hour is not needed to restore the environment.** Restoring needs only:
  - the CloudFormation updates of the stacks whose deployed template differs from last-good;
  - assets that already exist. CDK assets are content-addressed in the bootstrap bucket and ECR. They stay
    there unless garbage-collected, and `cdk gc --rollback-buffer-days` exists to keep them for exactly this
    case [F: CDK gc docs].

---

## 2. Failure-mode taxonomy (CDK / CloudFormation deploy + post-deploy smoke)

| # | Failure mode | What CloudFormation / CDK does | Is dev non-functional? For how long | Fastest restore | Effect on trunk / verification | Sources |
|---|---|---|---|---|---|---|
| T1 | **Deploy fails in one stack**, CloudFormation rolls it back (`UPDATE_ROLLBACK_COMPLETE`) | Undoes the stack's changes. A replaced resource is created first and the old one is deleted only afterwards, so rolling back just re-points to the old one [F] | That stack ends on the old version. Resources updated before the failure ran the new config for the update-plus-rollback window, usually minutes. Often NFT ≈ 0 [I] | Nothing for that stack: CloudFormation already restored it. Other stacks: see T3 | Every later deploy containing the culprit fails at the same place. VBT runs until the revert deploys. This was chess #566 | [CDK deploy `--rollback`](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html), [update behaviours](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html) |
| T2 | **The rollback itself fails** (`UPDATE_ROLLBACK_FAILED`) | The stack cannot be updated until `continue-update-rollback` succeeds. You can retry, list `--resources-to-skip`, or use `--force-rollback`. Skipped resources become inconsistent, and further updates may leave the stack impossible to recover [F] | Possibly non-functional, in a mixed state, until resolved: minutes to hours | Retry `continue-update-rollback` once automatically. Skipping resources is a human decision | All deploys of that stack are blocked. This is an infra-class event with the operator as owner | [Continue rolling back](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html) |
| T2b | **A slow failure: stabilization never completes** | An ECS service whose tasks keep failing can hold the stack `UPDATE_IN_PROGRESS` for several hours before rollback, and the rollback can then fail too [F]. A custom resource that never answers waits the default 1 h. `ServiceTimeout` (since June 2024) shortens that [F] | If new tasks replaced old ones, for the whole window [I] | ECS deployment circuit breaker with rollback, which returns to the last COMPLETED deployment [F]. `ServiceTimeout` on custom resources [F] | Deploy runs much longer and the next deploy queues behind it | [KC: ECS stuck](https://aws.amazon.com/premiumsupport/knowledge-center/ecs-service-stuck-update-status/), [custom resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html), [circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html) |
| T3 | **Multi-stack app: stack A updated, B failed, C never ran** | Rollback is per stack. There is no cross-stack transaction, so A stays on the new version [I, consistent with the per-stack wording of the CDK rollback docs]. Nested stacks are the exception: rolling back the parent also rolls back its children [F] | Non-functional only if new A does not work with old B or C. Unknown without a smoke check [I] | Redeploy A, and only A, from the last-good cloud assembly, consumers before producers [I] | C's own defects stay hidden until B passes. This is R3, serial masking, from the red-pipeline report | [CDK deploy](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html), [nested-stack note](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html), chess `cdk/deploy.py` [M] |
| T4 | **Deploy succeeds, smoke/E2E fails** | Nothing. The new version is live and CloudFormation has finished | Yes, from the moment traffic hit the new version until the restore passes its smoke. Naive: smoke time plus a full redeploy (more than 1.5 h). With a cached-artifact restore: smoke time plus a redeploy of the changed stacks (est. 5–30 min [I]). With traffic shifting: seconds [F, §3] | Minimum: redeploy last-good templates of the changed stacks. Better: run the smoke as a pre-traffic hook, so the failure aborts before traffic shifts and CloudFormation rolls back, which turns T4 into T1 with NFT ≈ 0. Best: flip the alias or target group, or turn the flag off | VBT until the revert deploys | [CodeDeploy hooks](http://docs.aws.amazon.com/lambda/latest/dg/automating-updates-to-serverless-apps.html), [ECS B/G](https://aws.amazon.com/blogs/aws/accelerate-safe-software-releases-with-new-built-in-blue-green-deployments-in-amazon-ecs) |
| T5 | **Flaky smoke, environment drift, or an outage of a dependency** | Not a change failure | Maybe, but not because of the window | Retry once. If the last-good restore also fails smoke, it is not the change: no revert, infra class [I] | No blame. Report it on the delivery-status issue | Red-pipeline report §3.3 ("fails with, passes without") |
| T6 | **Schema/data migration (irreversible)** | CloudFormation does not undo data. A restore puts old code on new data | Old code may not read the new schema, so a code restore can make things worse. NFT lasts until a forward fix unless the change was expand–contract | With expand–contract or two-phase changes, a code rollback is safe by construction. Without them, only a forward fix works, and revert-first must not auto-revert a contract step [F/I] | Escalate, do not revert blindly | [Builders' Library: rollback safety](https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments), [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) |
| T7 | **The deploy role or caller lacks a permission** (chess #1494: `cloudformation:GetTemplate`) | Fails at the first call that needs it. Inside CloudFormation with "preserve successfully provisioned resources" you can **Retry** after fixing IAM, without a rollback [F] | If it fails before any change, which is the case for a pre-flight check, NFT = 0. Mid-plan it behaves like T1 or T3 | Grant the permission (a human approval), then retry. Or revert the PR that introduced the new call | Every deploy fails until the grant or the revert. Classification: an action first used by a PR in the window is a change (revert, plus a request for the grant). An action that used to work is infra (no revert, escalate) [I] | [Stack failure options](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-failure-options.html) |
| T8 | **A stateful resource is replaced or deleted** (DynamoDB key schema, RDS port, a renamed bucket) | Creates the new resource, re-points, then deletes or retains the old one at cleanup [F] | From cutover: the new resource is empty, so data looks lost. A rollback before cleanup gets the old resource back. After completion, a "restore deploy" would replace the resource again rather than restore the data [I] | Restore from snapshot or PITR, which takes hours. In practice only prevention works: a stack policy that denies `Update:Replace`/`Update:Delete`, RETAIN policies, and a diff check | Treat as a human incident | [Update behaviours](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html), [stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html) |
| T9 | **A cross-stack export is removed while still imported** (chess #566) | The producer's update fails with "Cannot delete export … in use by …" and is rolled back [F] | As T1. Dev stays functional | Nothing needed. The fix is either the revert or the two-step `exportValue()` pattern [F] | Blocks every deploy until reverted | [re:Post](https://www.repost.aws/articles/ARrtwG71pqTYi3bGme27_3bg/remediating-cannot-delete-update-export-export-name-as-it-is-in-use-by-importing-stack-and-migrating-to-ssm-parameters-for-dynamic-updates), [two-step](https://www.codewithyou.com/blog/aws-cdk-removing-automatic-crossstack-references) |
| T10 | **Template property or name errors** | Since June 2026, CloudFormation's pre-deployment validation hard-fails property-syntax and name-conflict errors on CreateStack/UpdateStack, before anything is provisioned [F] | No | Nothing to restore | As T1 for the trunk | [CFN pre-deployment validation, 2026](https://aws.amazon.com/blogs/devops/ship-infrastructure-faster-with-cloudformation-and-cdk-pre-deployment-validation-on-every-stack-operation/) |

What follows from the table [I]:

- In T1, T7, T9 and T10, dev usually stays functional, so the whole cost is VBT. The cure there is a fast,
  correct revert. Restoring the environment is not the problem.
- In T3 and T4, dev may really be down. The cure is the Track E restore, which needs no attribution at all.
- T2, T6 and T8 cannot be fixed by reverting faster. They need prevention (§5) and a human owner.

---

## 3. Techniques that shrink non-functional time

| Technique | Applies to | Typical restore time | Project effort | Source |
|---|---|---|---|---|
| Keep CloudFormation's automatic rollback. Never use `--no-rollback`, hotswap, or express mode without rollback on a shared environment | Every stack | Rollback re-applies the old config to the resources the update touched: minutes, but hours for ECS without a circuit breaker [F/I] | None | [CDK deploy](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html). With `--no-rollback`, deploys that replace a resource always fail [F] |
| **Restore from a cached, immutable cloud assembly, changed stacks only.** `cdk deploy --app <cdk.out dir>` skips synthesis [F]. `cdk deploy` skips stacks with no change [F]. `cdk gc --rollback-buffer-days` keeps old assets [F] | Any CDK app | About the sum of the CloudFormation update times of the changed stacks. Skips the build, the synths and asset builds (for chess: the engine ports and the release build). Estimate 5–30 min against a 94-min job [I] | Low: persist `cdk.out` per deployed SHA, and give the deploy script a `--restore-from` path | [CodeCatalyst CDK action](https://docs.aws.amazon.com/codecatalyst/latest/userguide/cdk-dep-action-ref.html), [cdk gc](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-gc.html), [gc blog](https://aws.amazon.com/blogs/devops/announcing-cdk-garbage-collection/) |
| CodePipeline **stage rollback**, manual or automatic on failure (April 2024, V2 pipelines, not PARALLEL mode) | CodePipeline projects | Re-runs the stage with an earlier successful execution's artifacts and variables. No rebuild [F] | Low, for CodePipeline users | [Stage rollback](https://docs.aws.amazon.com/codepipeline/latest/userguide/stage-rollback.html), [auto rollback](https://docs.aws.amazon.com/codepipeline/latest/userguide/stage-rollback-auto.html) |
| GitLab environment rollback, or re-running an old GitHub deploy job | GitLab / GitHub | GitLab re-runs only the deploy jobs for the earlier commit [F]. A GitHub re-run uses the original SHA, within 30 days [F]. Either way it rebuilds unless the deploy job consumes stored artifacts | Low | [GitLab deployments](https://docs.gitlab.com/ci/environments/deployments/), [GitHub re-run](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs) |
| **CloudFormation rollback triggers** plus monitoring time. Up to 5 alarms, 0–180 min. They persist for later updates unless replaced. CDK flags: `--rollback-trigger-alarm-arns`, `--monitoring-time-minutes` [F] | Any stack, whenever an alarm reflects user-visible health. Smoke results can be published as a metric, or a synthetic canary used | CloudFormation rolls back the whole stack operation, in minutes, instead of a full redeploy [F/I] | Low to medium. **Caveat:** the monitoring time adds to every stack update. Chess deploys about 15 stacks one after another, so use triggers only on the edge and API stacks [I] | [Rollback triggers](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-rollback-triggers.html), [RollbackConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_RollbackConfiguration.html) |
| **Smoke tests before traffic shifts.** CodeDeploy `BeforeAllowTraffic` hook for Lambda; ECS lifecycle hooks with a test listener | Lambda, ECS/Fargate | NFT ≈ 0. A hook failure aborts the deployment before traffic moves, and CloudFormation rolls back [F] | Medium | [SAM gradual deployments](http://docs.aws.amazon.com/lambda/latest/dg/automating-updates-to-serverless-apps.html), [ECS B/G](https://aws.amazon.com/blogs/aws/accelerate-safe-software-releases-with-new-built-in-blue-green-deployments-in-amazon-ecs) |
| Lambda versions + alias + CodeDeploy (AllAtOnce, canary 10 % for 5–30 min, linear 10 % every 1–10 min) | Lambda | Re-pointing the alias is one API call, seconds [I]. On an alarm, CodeDeploy points the alias back automatically [F] | Medium (`AutoPublishAlias` / `LambdaDeploymentGroup`) | [CodeDeploy configs](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html), [CDK LambdaDeploymentGroup](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html) |
| **ECS built-in blue/green** (July 2025), plus linear and canary (October 2025): bake time, lifecycle hooks, alarm rollback | ECS behind ALB, NLB or Service Connect | Rollback is near-instant while blue still runs, during the bake [F] | Medium | [What's New](https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-ecs-built-in-blue-green-deployments), [aws-samples summary](https://aws-samples.github.io/sample-apex-skills/docs/skills/ecs/ecs-operation-review/references/services-deployment) |
| ECS deployment circuit breaker with rollback | ECS rolling deployments | Minutes. It caps the hours-long stuck update of T2b [F/I] | Trivial | [Circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html) |
| CloudFormation ECS blue/green through the CodeDeploy transform | ECS | Traffic shift with automatic rollback. **Caveat:** cannot be combined with other resource updates in the same stack update [F] | Medium | [CFN B/G](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/about-blue-green-deployments.html) |
| ALB weighted target groups | Anything behind an ALB | A weight change, with no DNS TTL wait [F] | Medium | [AWS blog 2019](https://aws.amazon.com/it/blogs/aws/new-application-load-balancer-simplifies-deployment-with-weighted-target-groups/) |
| Spinnaker-style red/black: keep the old fleet disabled but alive | EC2/ASG | Re-enable the old group [F] | Medium | [Spinnaker blog](https://blog.spinnaker.io/can-i-push-that-building-safer-low-risk-deployments-with-spinnaker-a27290847ac4) |
| Step Functions versions + alias. `DeploymentPreference` with alarms, or explicit weights | Step Functions | Alias re-point. Immediate rollback on an alarm [F] | Low to medium | [CFN alias](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-stepfunctions-statemachinealias.html), [compute blog](https://aws.amazon.com/blogs/compute/deploying-state-machines-incrementally-with-versions-and-aliases-in-aws-step-functions/) |
| API Gateway canary stage, 0–100 % traffic, then promote or turn off | REST APIs | Turning off the canary leaves the base deployment serving [F]. Seconds [I] | Medium | [Canary release](https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html) |
| Static frontend: versioned prefixes plus a CloudFront KeyValueStore pointer | S3 + CloudFront | KVS updates reach every edge within seconds [F]. The alternative, changing distribution config, waited 5–10 min for propagation in AWS's own example [F]. CloudFront continuous deployment covers CDN config only, at most 15 % weight, no HTTP/3 [F] | Medium | [KVS launch](https://aws.amazon.com/blogs/aws/introducing-amazon-cloudfront-keyvaluestore-a-low-latency-datastore-for-cloudfront-functions), [CF CD quotas](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html), [express what's new](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-cloudformation-cdk/) |
| **Feature flags / kill switch (AWS AppConfig)**: deploy dark, release by flag | Behaviour changes in any compute | About one poll interval (Lambda extension default 45 s). AppConfig rolls config back automatically on an alarm [F] | Medium, plus code discipline | [AppConfig rollback](https://docs.aws.amazon.com/appconfig/latest/userguide/monitoring-deployments.html), [Lambda ext. blog](https://aws.amazon.com/blogs/compute/implementing-dynamic-feature-flags-with-aws-appconfig-on-aws-lambda/) |
| **Expand–contract / two-phase** (prepare, then activate) | Schemas, data formats, cross-stack exports, APIs | Makes a code rollback safe. Either phase can be rolled back on its own, but not both together [F] | A rule for each change, enforced in review | [Builders' Library](https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments), [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) |
| Split stateful from stateless stacks, and put a stack policy on the stateful ones | All | A restore touches only the fast stateless stacks. Replacement of data resources is refused [F/I] | Medium, one-time | [Deployment time](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-deployment-time.html) (AWS: group resources by how often they change), [stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html) |
| Nested stacks, for atomic rollback across tightly coupled stacks | Coupled stacks | One rollback restores all the children [F] | Medium. You lose per-stack deploys | [Nested-stack note](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html) |
| Bake time | All | Detection, not restore. Amazon: at least 1 h after one-box, 12 h after the first regional wave [F] | Low | [Hands-off deployments](https://builder.aws.com/content/3ErTKQOTKc5NIw031UePBPxTQ6I/automating-safe-hands-off-deployments) |
| Rollback drills (upgrade-downgrade testing) | All | Makes rollback trustworthy. Amazon deploys N+1 to half the fleet, then all of it, then rolls back to N. Google rolls back periodically even when nothing is wrong [F] | Low | [Builders' Library](https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments), [Google CRE](https://cloud.google.com/blog/products/gcp/reliable-releases-and-rollbacks-cre-life-lessons) |
| CloudFormation express mode (June 2026) for the **restore only** (an option) | CloudFormation | Up to 4× faster because it skips stabilization waits. Rollback is off by default. AWS does not recommend it for production; `rollback-stack` supports it too [F] | Low, but risky: the restore smoke then has to retry until resources are ready [I] | [Express mode](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-express-mode.html), [launch](https://aws.amazon.com/blogs/aws/accelerate-your-infrastructure-deployments-by-up-to-4x-with-aws-cloudformation-express-mode/) |

Pipeline behaviour worth knowing:

- **CodePipeline batches by default** [F]. SUPERSEDED mode lets a newer execution overtake one waiting at a
  locked stage, so whatever piles up during an hour-long deploy goes out as one batch. QUEUED mode runs
  executions one by one. AWS describes PARALLEL mode as being for "targets that are not shared by other users".
  That is the shared-environment assumption of this framework, stated by AWS
  ([executions](https://docs.aws.amazon.com/codepipeline/latest/userguide/concepts-how-it-works.html)).
- **CDK Pipelines adds pre and post steps to each stage** ([CDK Pipelines](https://docs.aws.amazon.com/cdk/v2/guide/cdk-pipeline.html)).
  A failing post step fails the execution but does not undo the stacks, unless the CodePipeline stage is set to
  roll back [I: no other rollback is documented].
- **Traffic shifting needs traffic.** In a shared dev account with little traffic, canary percentages and
  error-rate alarms mean little [I]. The checks that work in dev are pre-traffic hooks and synthetic canaries.
  Amazon runs synthetic tests at least every minute
  ([going faster](https://builder.aws.com/content/3F08Mhh186qOa4VhG19egs06NJa/going-faster-with-continuous-delivery)).
- **Rollback is a swap, not a rebuild.** At Amazon a rollback switches back to the previously deployed container
  image, Lambda package or deployment package [F]. That is Track E.

---

## 4. Batching to a shared environment: how others do it

| Who | Changes per deploy | On a red batch | Attribution | Source |
|---|---|---|---|---|
| Amazon | Ideally one change at a time, which makes regressions easier to identify. Sets of changes are promoted wave to wave so bundles do not build up | Automatic rollback to the previously deployed package, triggered by an alarm. Often already in progress when the on-call engineer starts | Per change where possible | [Going faster](https://builder.aws.com/content/3F08Mhh186qOa4VhG19egs06NJa/going-faster-with-continuous-delivery), [hands-off](https://builder.aws.com/content/3ErTKQOTKc5NIw031UePBPxTQ6I/automating-safe-hands-off-deployments) |
| AWS CodePipeline | Everything waiting at a locked stage (SUPERSEDED) | Stage rollback of the whole batch to the last successful execution's artifacts | None built in | [Docs](https://docs.aws.amazon.com/codepipeline/latest/userguide/concepts-how-it-works.html) |
| Meta | Dozens to hundreds of diffs per push, every few hours; employees, then 2 %, then 100 % | Gatekeeper switches the feature off; an emergency stop halts the release | Push-blocking alerts at the employee tier | [Rapid release](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) |
| Shopify | 8 PRs per deploy (Shipit `max_commits` default 8); about 40 deploys and about 400 commits a day | Roll back to an earlier build with a separate rollback script. The queue locks during incidents. No merges with too many undeployed PRs | Humans | [Merging 1000+ devs](https://shopify.engineering/successfully-merging-work-1000-developers), [Shipit](https://github.com/Shopify/shipit-engine) |
| Slack | About 12 scheduled deploys a day from one release branch; dogfood, canary at 2 %, then 10 to 100 % | If production is already affected, roll back to the previous build first. Then identify the PR, revert it, and cherry-pick the revert into a new build | The deploy commander, from dashboards | [Deploys at Slack](https://slack.engineering/deploys-at-slack/) |
| GitHub | Old trains carried up to 15 PRs and a derailed train blocked everyone. Merge-queue deploy groups now take 30 or more | Canary at 2 %, then 20 %, then 100 %, with 5-minute gates. A quick rollback from the deploy UI | Humans, with the group as context | [Merge queue](https://github.blog/engineering/engineering-principles/how-github-uses-merge-queue-to-ship-hundreds-of-changes-every-day/), [deploys](https://github.blog/engineering/infrastructure/improving-how-we-deploy-github/) |
| Etsy | Push trains, up to 50 deploys a day | The train's members check their own changes and fix | Each train member for their own change | [How Etsy ships apps](https://www.etsy.com/codeascraft/how-etsy-ships-apps) |
| Google | n/a | Rollback is routine: roll back first, investigate second | Culprit finder (red-pipeline report) | [CRE life lessons](https://cloud.google.com/blog/products/gcp/reliable-releases-and-rollbacks-cre-life-lessons) |
| Microsoft Azure (Gandalf) | Many concurrent rollouts | Stops the rollout | Matches failure signatures against rollout events in space and time, then vote-veto and ranking. 92.4 % precision (data plane), 94.87 % (control plane) | [NSDI '20](https://www.usenix.org/conference/nsdi20/presentation/li) |
| Mozilla | Jobs coalesced across pushes when load is high | Backfill: run the job on earlier pushes (5 by default) until one push is to blame | Bisection on separate CI workers | [Retrigger/backfill](https://wiki.mozilla.org/Sheriffing/How_To/Retrigger_Jobs), [perf sheriffing](https://firefox-source-docs.mozilla.org/testing/perfdocs/perf-sheriffing.html) |

**Patterns across them:**

1. **Restore the whole batch first, without attribution** [F]. Slack, Amazon, CodePipeline, Shipit and GitHub do
   this.
2. **Then ship "the batch minus the suspect"** [F]. Slack cherry-picks the revert. Chromium and LLVM revert, as
   the earlier report covers. The innocent changes ship in the next build without being re-landed.
3. **Attribution after the restore is done by people or by data correlation, not by bisection on the shared
   environment** [I]. I found no organization that describes deploy-level bisection on a shared environment as
   routine. Mozilla bisects, but on parallel CI workers, not on one environment.
4. **Keep batches small, and throttle merges by the undeployed backlog** [F]: Shopify's 8 per deploy and its
   backlog rule, Amazon's one change at a time.

**What bisection costs when one probe is one deploy** [I, arithmetic]. With one shared environment, the probes run
one after another. Binary bisection over *n* suspects needs ⌈log₂ n⌉ deploys. Relanding one at a time needs up to
*n*.

| Suspects *n* | Binary bisection (deploys) | at 60 min / deploy | at 94 min / deploy (chess median) | One-at-a-time, worst case |
|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 0 |
| 2 | 1 | 1 h | 1.6 h | 2 deploys |
| 4 | 2 | 2 h | 3.1 h | 4 |
| 8 | 3 | 3 h | 4.7 h | 8 |
| 16 | 4 | 4 h | 6.3 h | 16 |

- **A first guess cuts the expected cost** [I]. If an attribution heuristic is right with probability *p*, the
  expected number of deploys is about 1 + (1 − *p*)·⌈log₂ n⌉. At a Gandalf-like *p* ≈ 0.9 and *n* = 8, that is
  about 1.3 deploys.
- **Chess windows are small** [I, from M]. About 24 landings a day against deploys of roughly 94 min gives 1–2
  landings per window on average and 4 or more at peaks. Bisection is the rare fallback. Track E is what makes
  even that bearable: between probes, dev stays on the restored last-good version.

---

## 5. Prevention: keep deploy-breaking changes out of the shared deploy (pre-merge, in the train)

| Check | Catches | Cost | Source |
|---|---|---|---|
| CloudFormation pre-deployment validation through a change set (`cdk deploy --method=prepare-change-set`, or the June 2026 `cdk validate`). Catches property syntax, name conflicts, S3 emptiness, service quotas, ECR delete readiness | T10, parts of T2 | Seconds. Needs `CreateChangeSet` on dev, **never** `ExecuteChangeSet` [I: least privilege] | [Validate deployments](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/validate-stack-deployments.html), [2026 blog](https://aws.amazon.com/blogs/devops/ship-infrastructure-faster-with-cloudformation-and-cdk-pre-deployment-validation-on-every-stack-operation/) |
| `cdk diff` or change-set review rule: Replace or Remove on a stateful type (DynamoDB, RDS, S3, Cognito user pool, KMS…) blocks unless the PR carries a `stateful-change` label | T8 | Seconds | Diff [F]; the rule [I] |
| **Export-in-use check.** Compare the deployed exports and their importers (`ListExports`, `ListImports`) with the synthesized outputs. Removing or changing an imported export blocks, and the PR must use the two-step `exportValue()` | T9 (#566) | Seconds | Error and two-step [F]; the check [I] |
| **IAM simulation** (`SimulatePrincipalPolicy`) of the deploy-caller role over a committed *action manifest* listing what the deploy scripts and migrations call. Access Analyzer custom checks for changes to policies | T7 (#1494) | Seconds. AWS warns simulator results can differ from live behaviour [F] | [IAM simulator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html); the manifest [I] |
| cfn-lint, cfn-guard and cdk-nag with project rules: every ECS service has a circuit breaker, every custom resource a `ServiceTimeout`, stateful resources are RETAIN | T2b, T8 | Seconds | [cfn-lint](https://github.com/aws-cloudformation/cfn-lint), [cfn-guard](https://github.com/aws-cloudformation/cloudformation-guard), [cdk-nag](https://github.com/cdklabs/cdk-nag); the rules [I] |
| A stack policy on stateful stacks that denies `Update:Replace`/`Update:Delete` (a runtime guard) | T8 | One-time | [Stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html) |
| Migration lint: additive (expand) only, unless a `contract` label is present and the expand has already deployed green | T6 | Seconds | [Two-phase](https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments) [F]; the lint [I] |
| **Revert-safety check**: synthesize the PR's revert at train time and run the same checks on it. Would the revert itself deploy cleanly? | Reverts that would fail (H5) | One extra synth per PR | Static version of Amazon's upgrade-downgrade test [I] |
| `cdk deploy --hotswap` | Not a check. **Never use it on a shared environment**: it introduces drift on purpose and is for development only [F] | n/a | [CDK deploy](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html) |

Security note [I]: train CI synthesizes PR code, which is untrusted, so any AWS credential it holds must be
read-only, plus at most `CreateChangeSet`/`DescribeChangeSet`/`DeleteChangeSet` on dev. The CDK lookup role is the
model for this.

---

## 6. Recommendation

### 6.1 Principles

- **P1. Two tracks.**
  - Track E restores the environment. It belongs to the deploy job, needs no attribution, and takes minutes.
  - Track T reverts on trunk. It belongs to the steward, needs attribution, and costs one CI plus one deploy.
- **P2. The restore is the "passes without" test.** The last-good version passing smoke on the same environment
  proves the window is the cause.
- **P3. Revert the culprit alone when attribution is confident**, and the whole suspect set only when it is not.
  Innocent landings never need rework.
- **P4. Infra and grant failures are not change failures.** A PR is reverted only if it introduced the need.
- **P5. Bound every wait**: stabilization timeouts, one automatic rollback retry, an escalation clock.

### 6.2 Track E: the deploy job (framework template; the project supplies the restore hook)

1. **E0 Pre-flight**, seconds, before anything changes: action-manifest IAM simulation, export-in-use check,
   change-set validation. A failure here leaves dev untouched and is reported as a red verdict with stage
   `pre-flight`.
2. **E1 Deploy**, as today, but record a result for every stack: status, first FAILED logical ID, reason.
   Where stacks are independent, keep going after a failure (F4 of the earlier report), so one deploy surfaces
   more than one defect.
3. **E2 Smoke / E2E**, retried once.
4. **E3 Auto-restore**, on failure in E1 or E2:
   1. Fetch the last-green SHA's cloud assembly, stored per deployed SHA as a workflow artifact or in an S3
      bucket in the dev account (open decision D-R4).
   2. List the stacks whose deployed template differs from last-green's.
   3. Redeploy each one with `cdk deploy --app <dir> <stack> --exclusively`, in reverse plan order (consumers
      before producers, so a restore never removes an export that a still-new consumer imports) [I].
   4. Run the smoke again.

   The restore runs **inside the failed run**, in the same concurrency slot. A separately dispatched restore could
   be superseded by a pending trunk deploy, because the template keeps only the newest pending run (H4).
5. **E4 Verdict payload**: stage (pre-flight, deploy or smoke), per-stack results, failing checks, restore result
   (`restored-green` or `restore-red`), and the SHA now serving.
6. **E5 Rollback still fails?** For `UPDATE_ROLLBACK_FAILED`, retry `continue-update-rollback` once, never with
   skips. Then go infra class: the delivery-status issue records `red (environment)` and the operator gets a
   NEEDS YOU.

Expected effect, with the Minimum tier only [I]:

- **T1/T9 deploy failures:** NFT ≈ CloudFormation's own rollback window (minutes), plus the restore of any
  earlier, now mixed-version stacks when the smoke shows they do not work together.
- **T4 smoke failures:** NFT ≈ smoke time plus a restore of the changed stacks, against about 1.5–3 h today.

### 6.3 Track T: the steward

1. **T0 Classify first.** These are **infra** and blame nobody:
   - credentials, throttling, quota, runner loss;
   - `AccessDenied` on an action that no PR in the window newly uses;
   - `restore-red` (last-good fails too);
   - `UPDATE_ROLLBACK_FAILED`.

   For infra: retry once, record `red (infra: <reason>)` on the delivery-status issue, and NEEDS YOU after the
   clock. This is R4/F3 of the earlier report.
2. **T1 Attribute** with the algorithm in §6.4.
3. **T2 Revert.**
   - The steward creates a revert PR, `git revert -m 1 <the PR's merge commit>`. Trunk has one `--no-ff` merge
     per PR, so this is exact. It is labelled `revert` and placed as **train 1 of the next batch**, so landings
     never pause.
   - The revert-first clock is zero: the revert is opened as soon as attribution is confident. This is the
     user's decision. An optional `revert_hold_minutes` (default 0) lets an operator hold it with a label.
   - Clean-revert fast lane (option D-R1): no later landing touched the culprit's files, and the revert passes
     the deploy-safety checks. Then land after a reduced check instead of the full train CI.
   - Chromium already exempts clean reverts from code review, though OWNERS approval still applies
     ([code_review_owners.md](https://github.com/chromium/chromium/blob/main/docs/code_review_owners.md)).
4. **T3 Landings while red.** Do not pause. Keep the window small instead: while `red-since` is set, a batch is
   the revert plus at most *k* PRs (for example 2). Add Shopify's rule: no landings while more than *M* landings
   are undeployed [F: Shipit; values I].
5. **T4 The next deploy** is the trunk tip, which contains the revert and the innocents.
   - **Green:** confirms the attribution, verifies the innocents by ancestry, ends the red streak.
   - **Red with the same signature:** the attribution was wrong. Revert the next suspect, which means bisection
     (§4 table).
6. **T5 Escalation.** NEEDS YOU on the delivery-status issue when either holds:
   - two wrong attributions in a row;
   - the red streak is longer than X h (suggest 4 h, roughly two deploys plus a CI).

### 6.4 Attribution, in order (stop at the first conclusive step)

1. **A1. Window.** W = the first-parent landings in (last-green, red], minus reverted ones.
2. **A2. One suspect.** |W| = 1 means that PR is the culprit.
3. **A3. Deploy-stage failure** (T1, T3, T9). Take the failing stack S, its first FAILED logical ID R and the
   reason.
   - For k = 1..|W|, synthesize the cumulative state "last-green plus the first k landings". The steward's
     trains already are those states for its own batches.
   - The first k whose step changes R, or removes the export or permission the reason names, is the culprit.
     Confidence: high.
   - CDK's `aws:cdk:path` metadata, on by default [F: CDK CLI global options], maps R to a construct and so to
     source files.
   - All of this runs on CI workers and touches no environment.
4. **A4. Pre-flight failure.** The check names the item itself: "export X removed at step k", or "action Y is
   first called at step k".
5. **A5. Smoke failure.**
   - Drop the provably inert PRs. A PR is inert if its step produces an **identical cloud assembly** (templates
     and asset hashes) **and** it touches none of the declared deploy footprint (deploy scripts, migrations,
     post-deploy checks).
   - Rank the rest by overlap between their changed paths and the failing checks' declared paths.
   - A single top candidate is the culprit, with medium confidence.
6. **A6. Still ambiguous.** Revert all remaining suspects in one revert. They come back through the relanding in
   §6.5.

Every revert comment records the method and the confidence. A wrong attribution costs one deploy and one reland,
never a broken trunk [I]. The data needed for A3 to A5 is exactly what §6.2 E4 adds to the verdict.

### 6.5 How the issue state machine reacts

| Role in the red window | Stage change | Machine record | Next actor |
|---|---|---|---|
| **Culprit** (A2 to A5) | LANDED → **REWORK-REQUIRED** | `merge-steward: reverted <landing> in <revert-sha> (deploy <env> red at <sha>; stage <s>; <stack/resource/check>; attribution <method>/<confidence>)`. Plus `needs-rework`. `awaiting-verification` and `verification-failed` are removed and the claim released | An implementer, pulled first. The rework branch starts from a **revert of the revert** plus the fix (H2) |
| **Culprit whose fix needs a grant** (T7) | LANDED → REWORK-REQUIRED, plus the `needs-input` flag (kind: approval) | As above, naming the IAM action and the role | The human approves the grant through `/get-guidance`. Then the rework relands |
| **Innocent in the window**, not reverted | Stays **LANDED** (`awaiting-verification`) | One comment: the red was attributed to #X and reverted in S, and this issue is not a suspect | Watcher: the next green deploy that contains it verifies it. No re-landing, no rework |
| **Reverted but not blamed** (A6, ambiguous) | LANDED → **TEST-READY** automatically: no claim, no worker, no rework | `merge-steward: reverted … (suspect set)`, then `merge-steward: queued PR #<reland>` | The steward opens a reland PR (revert of the revert) for each, in bisection order, half the set per deploy. A reland whose deploy goes red with the same signature, after a green one without it, turns its issue into the culprit |
| **Landed after the red began** | Unchanged (existing red-streak rule) | The existing streak comment | Watcher |
| **Infra / environment red** | No issue changes | The delivery-status issue: `red (infra: <reason>)`, and NEEDS YOU after the clock | Operator |
| **Culprit's rework PR** | REWORK-REQUIRED → TEST-READY → LANDED | The usual queued and landed lines. The landing line now supersedes the `reverted` line | Steward, then watcher |

### 6.6 Hazards in the current mechanism that revert-first would trigger

- **H1. Ancestry verification would verify and close a reverted issue.**
  - **What happens:** `verdict` (`merge_steward.py`, about lines 1764–1787) takes issues labelled
    `awaiting-verification` or `verification-failed`. It verifies them when their *last landing line* names an
    ancestor of the deployed commit. After a revert, the original landing commit is still an ancestor of every
    later trunk commit. The first green deploy after the revert would therefore close the culprit's issue,
    whose code is gone [M: code read].
  - **Fix:** a `merge-steward: reverted <landing> in <sha>` line supersedes the landing, so `last_landing`
    returns None until a newer landing line appears. `needs-rework` issues are no longer candidates.
- **H2. Re-merging a branch after its merge was reverted brings nothing back.** Git's own guidance is to revert
  the revert first ([revert-a-faulty-merge](https://raw.githubusercontent.com/git/git/master/Documentation/howto/revert-a-faulty-merge.adoc)) [F].
  The wrapper should therefore create rework and reland branches with the revert-of-revert commit already on
  them.
- **H3. A restore must not count as a trunk verdict.**
  - **What happens:** deploying last-green is "green". Today's code would refresh `last-green`, keep
    `red-since` (good), and verify nothing new (harmless) [M].
  - **Fix:** mark restore runs and record `<env> serving <sha> (restored)`, so the delivery-status issue shows
    the difference between "dev works" and "trunk deploys".
- **H4. Supersession races.** In the deploy template, a newer pending run replaces an older pending one [M]. A
  restore dispatched separately could be dropped. Keep it inside the failing run (E3).
- **H5. A revert can itself be undeployable.**
  - **Examples:** a later landing now imports the export the revert removes; the revert deletes a stateful
    resource; the revert undoes a migration.
  - **Fix:** run the deploy-safety checks on the revert PR. Revert the dependency closure (the later dependents
    too), or escalate.
- **H6. Serial masking (R3) blinds A3.** Record a result for every stack and keep deploying independent stacks.

### 6.7 What each project must provide: tiers

| Tier | The project provides | The framework provides | NFT, deploy failure | NFT, smoke failure | Trunk / verification |
|---|---|---|---|---|---|
| **Minimum** | <ul><li>`cdk.out` cached per deployed SHA, with `cdk gc --rollback-buffer-days` ≥ the retention</li><li>A deploy script that can redeploy named stacks from a given assembly (`--restore-from`)</li><li>A per-stack result file</li><li>CloudFormation auto-rollback on; no hotswap, `--no-rollback` or express mode on dev</li><li>ECS circuit breaker with rollback; `ServiceTimeout` on custom resources</li><li>An IAM action manifest</li><li>A smoke check that runs standalone</li></ul> | E0 to E5, the T0 to T5 steward logic, attribution A1 to A6, the state-machine records, the H1 to H6 fixes | CloudFormation's rollback window (minutes), plus a restore of mixed stacks if needed | Smoke time plus a restore of the changed stacks (est. 5–30 min) [I] | VBT ≈ revert CI plus one deploy (≈ 2.5 h for chess), TBT ≈ 0 |
| **Better** | <ul><li>Stateful stacks split from stateless ones, with stack policies</li><li>The smoke for user-facing entry points runs as **pre-traffic hooks** (CodeDeploy for Lambda, ECS lifecycle hooks)</li><li>A synthetic-canary alarm as a CloudFormation rollback trigger on the edge and API stacks</li><li>Expand–contract for migrations and exports</li><li>`--concurrency` for independent stateless stacks</li></ul> | Pre-merge checks of §5 (export, IAM, stateful-replace, migration lint, revert safety) | ≈ 0 for hooked components | ≈ 0 for hooked components (traffic never shifts); a restore for the rest | Fewer red deploys; same VBT when one happens |
| **Best** | <ul><li>Blue/green with bake time for all compute: Lambda alias + CodeDeploy, ECS built-in B/G, Step Functions alias, API Gateway canary, static site through version prefix + KVS</li><li>AppConfig flags for behaviour changes</li><li>A quarterly rollback drill (N+1, then back to N)</li></ul> | Calls a project `rollback-traffic` hook in place of E3 | Seconds | Seconds (a flag: about 45 s) | Same, but with less pressure, because users never see the break |

### 6.8 The chess incidents under this design [I]

- **#566 (the export removed).**
  - The export-in-use check would have refused it at the train: 0 h red.
  - Without the check: the deploy goes red at `ChessEngine-Dev`, and CloudFormation rolls it back, so dev keeps
    serving. A3 finds #566 as the step that removed the outputs named in the error. Its revert becomes train 1
    of the next batch, and the next deploy is green.
  - Total about 1 train CI plus 1 deploy, roughly 2.5 h after the red, against about 44 h after the cause was
    known.
- **#1494 (`cloudformation:GetTemplate`).** E0's IAM simulation fails in seconds, before any change, and names
  the action that #1494 is the first to call. Under T7 rules the steward reverts #1494 and files a grant approval
  for the human, or the train refuses it pre-merge. The defects that #566 had masked (R3) surface in the same
  deploy once per-stack continuation exists.

### 6.9 What to measure (on the delivery-status issue, per red event)

- Timestamps: `t_red`, `t_restored`, `t_revert_landed`, `t_green`.
- The clocks they give: NFT = `t_restored` − first failing step; VBT = `t_green` − `t_red`; TBT = paused minutes.
- The attribution method, its confidence, and whether the next deploy confirmed it.

This is the same "measure before tuning" discipline as the earlier reports.

### 6.10 Open decisions

- **D-R1.** Clean-revert fast lane (a reduced check) or the full train CI for reverts.
- **D-R2.** While red: cap the batch size (recommended) or pause landings until the revert lands.
- **D-R3.** Ambiguous windows: revert the whole suspect set and reland by bisection (recommended), or bisect
  without a revert. Without a revert, every trunk deploy stays red, so VBT grows.
- **D-R4.** Where cached assemblies live (Actions artifacts or S3 in the dev account), and for how long.
- **D-R5.** Smoke retry count before red (1 recommended, as with `retry_culprit_once`).
- **D-R6.** Whether the Minimum tier becomes a setup-prompt requirement for every AWS project. That would mean
  the deploy-script restore hook plus the artifact cache.

---

## 7. Sources

Internal: `docs/reports/red-pipeline-analysis-2026-11-02.md`; `docs/reports/wait-time-analysis-2026-10-25.md`;
`src/payload/scripts/merge_steward.py`; `clients/common/docs/delivery.md` §4;
`templates/ci/github-deploy.yml.template`; chess `.github/workflows/deploy-dev.yml` and `cdk/deploy.py`
(read-only).

AWS: [Builders' Library: rollback safety](https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments) ·
[hands-off deployments](https://builder.aws.com/content/3ErTKQOTKc5NIw031UePBPxTQ6I/automating-safe-hands-off-deployments) ·
[going faster with CD](https://builder.aws.com/content/3F08Mhh186qOa4VhG19egs06NJa/going-faster-with-continuous-delivery) ·
[CFN rollback triggers](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-rollback-triggers.html) ·
[RollbackConfiguration API](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_RollbackConfiguration.html) ·
[continue update rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html) ·
[stack failure options](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-failure-options.html) ·
[update behaviours](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html) ·
[stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html) ·
[stack deployment time](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-deployment-time.html) ·
[express mode](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-express-mode.html) and
[launch post](https://aws.amazon.com/blogs/aws/accelerate-your-infrastructure-deployments-by-up-to-4x-with-aws-cloudformation-express-mode/) ·
[pre-deployment validation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/validate-stack-deployments.html) and
[2026 post](https://aws.amazon.com/blogs/devops/ship-infrastructure-faster-with-cloudformation-and-cdk-pre-deployment-validation-on-every-stack-operation/) ·
[custom resources (timeout)](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) and
[ServiceTimeout launch](https://aws.amazon.com/about-aws/whats-new/2024/06/aws-cloudformation-dev-test-cycle-timeouts-custom-resources/) ·
[CFN ECS blue/green](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/about-blue-green-deployments.html) ·
[CDK deploy](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html) ·
[cdk gc](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-gc.html) and [blog](https://aws.amazon.com/blogs/devops/announcing-cdk-garbage-collection/) ·
[CDK Pipelines](https://docs.aws.amazon.com/cdk/v2/guide/cdk-pipeline.html) ·
[CodeCatalyst CDK action (pre-synthesized assembly)](https://docs.aws.amazon.com/codecatalyst/latest/userguide/cdk-dep-action-ref.html) ·
[CodePipeline executions](https://docs.aws.amazon.com/codepipeline/latest/userguide/concepts-how-it-works.html) ·
[stage rollback](https://docs.aws.amazon.com/codepipeline/latest/userguide/stage-rollback.html) and
[automatic](https://docs.aws.amazon.com/codepipeline/latest/userguide/stage-rollback-auto.html) ·
[CodeDeploy configurations](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html) ·
[SAM gradual deployments](http://docs.aws.amazon.com/lambda/latest/dg/automating-updates-to-serverless-apps.html) ·
[ECS built-in B/G (What's New)](https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-ecs-built-in-blue-green-deployments) and
[blog](https://aws.amazon.com/blogs/aws/accelerate-safe-software-releases-with-new-built-in-blue-green-deployments-in-amazon-ecs) ·
[ECS circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html) ·
[KC: ECS stuck updates](https://aws.amazon.com/premiumsupport/knowledge-center/ecs-service-stuck-update-status/) ·
[ALB weighted target groups](https://aws.amazon.com/it/blogs/aws/new-application-load-balancer-simplifies-deployment-with-weighted-target-groups/) ·
[Step Functions alias](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-stepfunctions-statemachinealias.html) ·
[API Gateway canary](https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html) ·
[CloudFront CD quotas](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html) ·
[CloudFront KVS](https://aws.amazon.com/blogs/aws/introducing-amazon-cloudfront-keyvaluestore-a-low-latency-datastore-for-cloudfront-functions) ·
[AppConfig auto-rollback](https://docs.aws.amazon.com/appconfig/latest/userguide/monitoring-deployments.html) ·
[AppConfig on Lambda](https://aws.amazon.com/blogs/compute/implementing-dynamic-feature-flags-with-aws-appconfig-on-aws-lambda/) ·
[IAM policy simulator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html) ·
[export-in-use remediation](https://www.repost.aws/articles/ARrtwG71pqTYi3bGme27_3bg/remediating-cannot-delete-update-export-export-name-as-it-is-in-use-by-importing-stack-and-migrating-to-ssm-parameters-for-dynamic-updates).

Others: [Google CRE: releases and rollbacks](https://cloud.google.com/blog/products/gcp/reliable-releases-and-rollbacks-cre-life-lessons) ·
[Meta rapid release](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) ·
[Slack deploys](https://slack.engineering/deploys-at-slack/) ·
[GitHub merge queue](https://github.blog/engineering/engineering-principles/how-github-uses-merge-queue-to-ship-hundreds-of-changes-every-day/) ·
[GitHub deploys](https://github.blog/engineering/infrastructure/improving-how-we-deploy-github/) ·
[Shopify merge queue](https://shopify.engineering/successfully-merging-work-1000-developers) ·
[Shipit](https://github.com/Shopify/shipit-engine) ·
[Etsy ships apps](https://www.etsy.com/codeascraft/how-etsy-ships-apps) ·
[Gandalf, NSDI '20](https://www.usenix.org/conference/nsdi20/presentation/li) ·
[Mozilla retrigger/backfill](https://wiki.mozilla.org/Sheriffing/How_To/Retrigger_Jobs) ·
[Spinnaker safe deployments](https://blog.spinnaker.io/can-i-push-that-building-safer-low-risk-deployments-with-spinnaker-a27290847ac4) ·
[GitLab deployments](https://docs.gitlab.com/ci/environments/deployments/) and [deployment safety](https://docs.gitlab.com/ci/environments/deployment_safety/) ·
[GitHub re-run](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs) ·
[git: revert a faulty merge](https://raw.githubusercontent.com/git/git/master/Documentation/howto/revert-a-faulty-merge.adoc) ·
[Fowler: ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) ·
[DORA metrics](https://dora.dev/guides/dora-metrics/) ·
[Chromium code review owners (clean reverts)](https://github.com/chromium/chromium/blob/main/docs/code_review_owners.md) ·
[cfn-lint](https://github.com/aws-cloudformation/cfn-lint) · [cfn-guard](https://github.com/aws-cloudformation/cloudformation-guard) ·
[cdk-nag](https://github.com/cdklabs/cdk-nag).
