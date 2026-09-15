---
title: Astra Workflow Evaluation — Controlled Pilot
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
modified: 2026-09-15
revision: 7
status: Both studies complete; controller prototype tested; broader validation pending
---

# Astra Workflow Evaluation — Controlled Pilot

This is the single authoritative report for the original 12-run exploratory evaluation, its completed 108-run expanded follow-up, and the subsequent controller prototype. The original study evaluated three Astra development configurations. All 12 scored runs completed without repairs or retries. The protocol and scoring code were frozen before scored model execution.

## Question and scope

Does a Medium-first Astra workflow with selective context and bounded delegation improve measured usage or elapsed time while satisfying the same task-specific acceptance criteria as fixed Ultra and fixed single-agent Medium?

The tasks are small, newly written synthetic fixtures inspired by a local security-workbench pilot. They do not contain private application source. The evaluation covers evidence extraction, a bounded Python implementation, security-boundary classification, and structured evidence synthesis. It does not establish whole-project productivity, open-ended writing quality, or Daybreak vulnerability-detection accuracy.

## Frozen method

See [protocol.json](protocol.json) for identities, exact randomized order, software versions, resource limits, and frozen file hashes. Each task is run once under each condition. All conditions share the task input, response schema, read-only model tool permissions, disabled web access, native ChatGPT authentication, and a two-child ceiling when delegation is enabled. Each execution has a 300-second deadline.

- **A:** fixed Astra Ultra for parent and any children.
- **B:** fixed Astra Medium, with delegation disabled.
- **C:** Astra Medium parent with the adaptive routing policy and Astra specialist roles.

Each run receives an isolated Codex configuration directory. The native client uses its existing authorized authentication through a local symlink; credential contents are never read or published by the study code. The live user configuration is not changed. Prompt assembly is inspected before every run to reject personal instructions, personal memory, and candidate-policy contamination in baseline conditions.

The primary usage metric sums each session's final cumulative input and output tokens. Cached input and reasoning output are reported separately as subsets. CLI root totals are not assumed to include children. Unknown usage prevents a complete efficiency claim. Timing includes measured run setup, model/tool execution, and deterministic grading, with study development and later reviewer effort recorded separately. Failures and timeouts remain in the results; scored outputs are not repaired or retried.

The deterministic evaluator checks task-specific facts, required structure, source references, and bounded implementation behavior. It does not automatically judge the semantic quality of prose rationales. Generated Python runs inside the tested macOS sandbox with CPU, output, open-file, and wall-time bounds. Private user-path reads and network access are negative-tested. This is not a general sandbox certification; no verified memory-cap claim is made.

## Calibration and provenance

The preceding Daybreak integration pilot was complete before this study began. A read-only evidence review confirmed a retained log of 18 passing tests and matched all 20 recorded implementation/test/fixture hashes. Recorded source preservation applies to two selected source files, not an entire repository. These observations are context for the synthetic fixtures, not comparative-study results or independent signed attestation.

An initial configuration probe demonstrated that ignoring the user config file alone still exposed global instructions. That approach was rejected before scoring. Isolated configuration homes removed those instructions. A controlled parent/child calibration returned the expected markers and exposed a Medium parent and Low child with separately recorded usage. Calibration is excluded from scored comparisons and its shareable records are in [evidence/calibration](evidence/calibration).

## Results

All three configurations passed all 71 checks across their four tasks. No run timed out, required human repair, or changed its input files. These checks are observations on this suite, not proof of equal general quality.

| Configuration | Accepted tasks | Checks | Sessions | Input + output tokens | Setup + execution + grading |
|---|---:|---:|---:|---:|---:|
| A — fixed Ultra | 4/4 | 71/71 | 6 | 272,582 | 227.15 s |
| B — single-agent Medium | 4/4 | 71/71 | 4 | 94,859 | 69.59 s |
| C — adaptive Medium | 4/4 | 71/71 | 4 | 155,547 | 130.05 s |

C used 42.9% fewer recorded tokens and 42.7% less measured elapsed time than A. Against B, however, C used 64.0% more tokens and 86.9% more time. Single-agent Medium was the most efficient condition on this suite. The data do not support claiming that the adaptive policy improved on Medium alone.

The adaptive condition stayed at Medium with no child agents in all four runs. The Ultra condition used one Ultra child on each of T02 and T03. Effective model/effort observations are retained in each record. The separate calibration demonstrated a Medium parent and Low child, but did not test whether the adaptive policy chooses or escalates specialists appropriately on difficult real work. That behavioral claim remains unvalidated.

The C coding execution took 84.48 seconds versus 23.17 seconds for B. One observation cannot separate policy effects, model variability, cache effects and provider contention. Task-specific data and cached/reasoning subsets are in [summary.csv](results/summary.csv) and [summary.json](results/summary.json).

## Accounting and evidence handling

A read-only review of the two scored forked-child logs checked inherited contexts against usage events. Parent turn context was inherited, but parent token-count events were not. Each child's first cumulative usage equaled its first last-call usage, and its three last-call usages summed to its final cumulative usage. Therefore the final parent and child totals can be added for these observed runs: 92,807 tokens for T03/A and 128,693 for T02/A. No copied parent baseline is subtracted. Cached input and reasoning output are already subsets and are never added again.

The separate team calibration consumed 53,060 recorded tokens, excluded from the table. Configuration probes, fixture creation, orchestration, reviewer work, report preparation and publication are not completely metered here. Consequently this study does not establish net lifecycle token savings. No dollar cost or subscription-allowance savings is inferred.

Public records retain synthetic task responses, tool events, acceptance results, runtime configuration, usage and original evidence hashes. Personal path prefixes are replaced with placeholders. Account quota/rate-limit metadata is removed from usage events. Reasoning-event items and original host prompt/session logs are withheld. Original private files are not changed. These redactions do not change task responses, token counts or checks. Hashes are provenance aids, not independent attestations. No private Daybreak source or authentication contents are included.

## Decision and next validation

Use single-agent Astra Medium as the normal starting point for tasks resembling these fixtures. Retain explicit higher-effort review for consequential work, but treat the adaptive routing policy as experimental. This study does not justify a universal claim that Medium preserves quality or that the policy finds the correct escalation point.

Before a stronger public performance claim, freeze a larger held-out suite containing genuinely difficult failures and required escalation decisions; repeat paired runs across randomized blocks; predefine quality noninferiority margins and effort/latency targets; assess rationale quality with blinded human review; and count repair, review and routing overhead. Include tasks on which Medium fails and measure whether escalation recovers them. Publish unsuccessful cases as well as successes. No significance test is used on these four heterogeneous single observations.


## Limitations and claim boundary

Four tasks and one run per task/condition do not justify a population-level claim of superiority or equivalence. Cached-prefix state and provider contention are not controlled. The task suite is deliberately small and mostly deterministic; a perfect score can be a ceiling effect. Each condition may make different tool or delegation decisions. Exact prompts, policies, evidence, and failures will be retained so those differences can be examined.

Observed reductions apply only to the measured runs and comparator named above; absence of quality loss outside these checks is not established. Subscription allowance and monetary cost cannot be inferred directly from token totals. A reproducible local release is not proof of successful reproduction by another user.

## Revision record

- Revision 1, 2026-09-15: recorded frozen method and preflight evidence before scored runs. Author and creator: Angelis Pseftis.

- Revision 2, 2026-09-15: integrated all 12 results, token-accounting review, privacy transformations and limitations in this same authoritative file. Git retains revision history. Reliable active editing-time telemetry was unavailable; no editing duration is invented. Author and creator: Angelis Pseftis.

## Expanded validation — prespecified follow-up

The user authorized a follow-up to address task coverage and unexercised escalation. The original 12 observations above remain unchanged. The follow-up uses 12 new synthetic tasks in four domains, three repetitions per task under the same three comparator families (108 scored runs). The adaptive policy is revised to specify an actionable review trigger: two separable substantive analyses combined with a consequential trust boundary, interacting failure modes, or conflicting authoritative evidence. This is a different candidate policy, not retroactive validation of the original one.

Separate forced conformance probes check actual Astra specialist effort and parent integration. They are excluded from natural routing rates and efficiency comparisons. Task-level review-opportunity labels and scoring oracles remain outside model-visible input folders. The protocol will freeze these labels, run order, policy, scoring and decision gates before any follow-up scored runs. No results are claimed here yet.

Repeated runs measure variability, while 12 task clusters remain the unit of breadth. Even zero observed task regressions among 12 tasks gives a one-sided 95% exact upper bound of about 22.1% under an independent-task sampling assumption; these purposively authored synthetic tasks do not justify population generalization. The 5% quality-regression margin can therefore remain inconclusive. A benchmark acceptance gate, mechanical routing conformance, and broader quality evidence will be reported separately. No amount of wording can remove an evidence limitation that the measurements do not resolve.

- Revision 3, 2026-09-15: added the authorized follow-up design before expanded scored execution. Original pilot findings preserved in this same authoritative report. Author and creator: Angelis Pseftis.

The exact-binomial bound follows [NIST’s one-sided confidence-limit method](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). This is a bound on regression-task incidence under stated sampling assumptions, not a confidence interval on the acceptance-rate difference.

The follow-up oracle is outside the model-visible fixture workspace and forbidden by the common task contract. The host read-only sandbox is not a per-file confidentiality boundary; retained parent/child tool traces require audit for unauthorized oracle or prior-result access before interpreting the scores.

## Validation needed for broader claims

The expanded study remains a synthetic engineering benchmark. More repetitions do not create more independent tasks, and no finite suite demonstrates superiority for all future projects. A defensible next claim must identify a target workload, model/client version, operating conditions, quality margin and measured benefit. The following is a proposed next-stage design, not a change to the running frozen protocol or a claim that the work has been performed.

### Workload sampling and quality

Define the target population first: for example, bounded repository changes and technical evidence reviews within named scope and complexity bands. Build an eligibility-based task inventory from multiple projects and independent contributors, sample across task type, difficulty and consequence, and record exclusions. Treat related tasks from a shared repository or template as clustered. Keep workflow tuning cases separate from an untouched confirmation set; do not use benchmark outcomes to select favorable confirmation cases.

Use the current pilot to inform plausible variability and paired disagreement rates, then conduct a prospective power/precision calculation for the chosen quality margin and minimum practical efficiency benefit. Freeze sample size, primary endpoints, multiplicity handling and stopping rules. A convenient count such as 60 or 100 tasks is not a substitute for that calculation. The zero-regression binomial example elsewhere in this report is not an acceptance-rate noninferiority power calculation.

Add real deliverables: multi-file bug repairs, hidden integration tests, incomplete/conflicting evidence, architecture alternatives with failure analysis, and technical documents requiring verified citations and rendered artifact inspection. Develop hard cases on a separate calibration set. Freeze scoring before confirmation, including critical-error vetoes and behaviorally anchored quality rubrics; preserve easy controls to expose unnecessary delegation. A high score is not itself a defective metric, but universal perfect scores cannot distinguish configurations well.

For open-ended outputs, use at least two blinded domain reviewers with predefined rubrics, measure agreement, and adjudicate disagreements without showing arm identity. Strip model/effort labels and randomize presentation order. Automated/model-assisted scoring may support triage, but is not independent human validation. Human task vetting and blinded expert comparisons are demonstrated practices in [OpenAI's GDPval methodology](https://openai.com/index/gdpval/); that work does not validate this study's fixtures or results.

### Environment, cache and causal attribution

For a later confirmation study, balance all six arm-order permutations across tasks, block runs by task and execution window, repeat across days, and hold client version, hardware, configured service tier, input snapshot and tool permissions constant where possible. Record cache-hit counts, tool time, setup time, execution timestamps and observed throttling. This follows [NIST's randomized-block design guidance](https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm). Provider-side contention remains unobservable without provider telemetry; randomization mitigates its influence but does not establish full control.

Do not call an isolated session a cold cache. Use warm/cold experimental conditions only if the execution surface supplies a documented control and telemetry confirms the intended state. Otherwise report observed cache behavior and descriptive sensitivity analyses. Cache reuse can itself be a workflow effect; adjusting it away is not automatically a valid causal estimate. Repeated prefix perturbations are not a verified cache-control mechanism.

Separate two questions. For whole-workflow effectiveness, differing tool/delegation choices are part of the treatment: charge all their time and usage. For mechanism attribution, run a separate preregistered ablation with a common tool policy to distinguish effort selection, context size, review and delegation effects. A frozen tool transcript may characterize reasoning under fixed evidence, but is not equivalent to live agent execution. Do not claim that specialist use caused a benefit merely because it co-occurred with it.

### Routing assurance, cost and reproduction

Treat role conformance, routing choice, completed specialist work, evidence integration and outcome benefit as separate gates. Audit observed decisions against hidden engineering labels and inspect unsupported claims of invocation. If the frozen policy misses its routing gate, preserve that failure and evaluate a new version on new confirmation cases. A future controller can enforce required launch settings and refuse completion when a required review receipt is absent; it still needs a separately validated decision rule for when review is required. Prompt wording alone does not guarantee enforcement, and mandatory delegation is not automatically efficient.

Report total input/output tokens, cache subsets, parent/child usage, failures, retries, setup, tools, grading, human repair time and maintenance overhead. Compare resources per accepted task while retaining failed-attempt expenditure and reporting success rates separately. With a flat subscription, token reductions do not establish bill reductions or a proportional change in allowance. A monetary claim requires an explicit cost model with attributable invoices or an authorized metered billing experiment; neither has been established here. Hypothetical API-rate calculations must be labelled estimates and cannot be substituted for observed subscription cost.

Publish a versioned release, environment specification, input hashes, immutable result bundles, analysis command and a replication submission template. An unrelated person or team must then execute it in its own environment and provide logs, configurations, hashes, deviations and results. A second local checkout or another agent operated by the same author establishes additional local reproduction only. Independent reproduction cannot be manufactured by automation; independent participants have not yet been recruited and no outreach is authorized by this plan.

### Publication gate

A broader claim requires a prespecified quality criterion to pass, no critical-error veto, practically meaningful efficiency improvement with an uncertainty interval supporting the claim, and replication evidence appropriate to the wording. Quality equivalence requires its own two-sided equivalence criterion; failure to detect a difference does not establish equivalence. If a gate is inconclusive or fails, report that result and limit the claim to the evidence actually obtained. The remaining qualifications should name the tested population and unresolved conditions rather than promise universal performance.

- Revision 4, 2026-09-15: added the prospective validation design in response to the user's methodology questions. No frozen expanded inputs, labels, policies, or criteria were altered. Author and creator: Angelis Pseftis.

## Stronger-validation implementation status

The following preparation is implemented and tested while the frozen expanded comparison continues:

- [Blinded-review exporter](validation/review/README.md): exports every completed response with randomized IDs and a private unblinding key; incomplete studies and unsafe key placement are rejected. Three tests pass. It also prepared a 12-response local demonstration from the original study. No human ratings were supplied, and prior public availability limits blinding of those demonstration outputs.
- [Independent-reproduction kit](reproducibility/README.md): verifies release and protocol hashes, captures minimal nonsensitive environment metadata, creates a blank external submission, and inspects referenced evidence. Twelve tests pass. It distinguishes self-report and byte consistency from substantive independence; it cannot certify independence from a form or matching hash.
- [Real-workload candidate inventory](validation/workloads/README.md): 500 SWE-bench Verified metadata rows across 12 repositories, pinned to source revision c104f840cc67f8b6eec6f759ebc8b2693d585d4a. Seven offline tests pass. The deterministic proposed split selects 55 tuning and 29 confirmation candidates from disjoint sets of eight and four repositories. This is a proposed sample, not a power-justified confirmation commitment. The public benchmark has unknown model-training exposure and covers Python issue repair, not the user's whole workload. Gold patches, test patches and issue prose are excluded from the published inventory. Dataset redistribution clearance and task execution readiness remain unresolved; the harness MIT license does not resolve underlying dataset/repository rights.
- [Sample-size sensitivity tool](validation/design/README.md): computes explicitly approximate paired-binary planning scenarios under hypothetical discordance and clustering assumptions. Four tests pass. It refuses zero-discordance planning rather than turning perfect pilot scores into a zero-sample recommendation. These calculations are not an exact noninferiority design or a frozen sample-size decision.

Docker Server 29.8.0 was reachable in a read-only environment check. No new benchmark images or real-task executions were started by this preparation. External reviewer recruitment, completed blinded reviews, independent reproduction, target-specific endpoint validation, confirmation power/simulation review and full live-harness qualification remain pending. The current 108-run protocol and its frozen inputs were not changed. All 26 tests above concern the new preparation tools; they are not 26 additional model-performance observations.

- Revision 5, 2026-09-15: recorded implemented and tested stronger-validation tooling, real-workload candidate provenance, and remaining external prerequisites. Author and creator: Angelis Pseftis.

## Research on provable routing — 2026-09-15

Primary-source research supports a more precise direction: a learned effort-selection rule, independently calibrated risk control, and enforced execution settings. This is an architectural recommendation, not an implemented or validated replacement for the frozen candidate.

| Work | Relevant evidence | Boundary |
|---|---|---|
| [Learn then Test](https://arxiv.org/pdf/2110.01052), Definition 1 and Theorem 1 | Uses valid hypothesis tests and family-wise error control to select policies satisfying a chosen risk bound with high probability over calibration sampling. | Requires the stated sampling/testing conditions and defined loss; does not guarantee every answer or any savings. |
| [Ares](https://arxiv.org/html/2603.07915v1), Tables 1–2 | Learns per-step effort selection. Table 2 reports 52.7% fewer reasoning tokens for the Retail experiment with improved task success against fixed High. | Empirical preprint result using gpt-oss-20b and a trained Qwen router; not an Astra result, total subscription-cost result or universal quality theorem. |
| [RouteLLM](https://arxiv.org/html/2406.18665) | Learns stronger/weaker model selection from preference data and reports favorable benchmark cost/quality tradeoffs. | Empirical evidence; its pretrained router is not calibrated for Astra effort levels or this workload. |
| [Conformal Thinking](https://arxiv.org/html/2602.03814v1), Sections 4.4 and Appendix B | Calibrates reasoning-stop thresholds against a specified risk. | Uses internal reasoning/uncertainty access not established in our Codex surface. Fixed-candidate bounds require correction when selecting across a grid; its combined-threshold discussion limits the resulting guarantee. |

The transferable design is to define a finite family of Astra effort policies before calibration, fit route predictors on tuning data, evaluate their task-level losses on independent representative calibration data, and retain only statistically admissible policies. A separate resource objective chooses among the retained policies; if no cheaper candidate qualifies, retain the reference policy. Per-step decisions must be evaluated through end-to-end task loss because errors can propagate through a trajectory. A statistical guarantee on a proxy grader is a guarantee about that proxy, not every aspect of real-world quality.

The runtime must apply the selected effort through supported call/turn controls and record actual execution. Fine-grained per-tool-call effort control and hidden-state/token-distribution access have not been established for our native Codex setup. We should not emulate an effort switch by silently adding a subagent and omitting its context/coordination costs. Ares's external router is incompatible with adopting its package unchanged under the Astra-only preference; a statistical decision rule or separately evaluated Astra-based selector would need its own overhead measurement.

Keep the learned rule and calibration set separate, preserve whole task/repository clusters, include model randomness in the evaluated procedure, and recalibrate after material distribution/model/harness changes. Evaluate quality and resource performance against both Medium and the chosen reference configuration. Higher effort is not assumed pointwise more accurate. These methods provide a path to conditional statistical assurance, not universal superiority, zero error, guaranteed speed, or dollar savings from subscription token counts.

- Revision 6, 2026-09-15: added primary-source routing research and its applicability boundary. Frozen experimental files and live execution were unchanged. Author and creator: Angelis Pseftis.

## Task-boundary controller implementation — revision 7

The experimental [controller](controller/README.md) now implements training-only finite effort policies, separate paired-risk calibration with multiplicity correction, and native Astra effort enforcement at task boundaries. It defaults to trusted Medium when no admissible certificate applies. It is not installed globally. The prototype handles read-only answer/code tasks; general project editing remains outside its implemented scope.

All 42 controller unit/integration tests passed, including mocked native processes, timeout handling, certificate tampering, missing accounting, explicit verifier checks and fallback retention. A separate statistical review found floating-point underflow and unbounded certificate-count computation; supported delta and sample-count limits plus regression tests address those findings. Unique cluster identifiers still do not establish independent or representative sampling.

Native conformance tests passed for a Medium reference execution and a deliberately forced Low-to-Medium fallback. The latter uses a clearly labeled synthetic certificate and intentionally rejects the first response; both model attempts pass the marker contract, and the verifier rejects the first solely to exercise fallback. These tests establish observed runtime mechanics, not savings or quality certification. [Retained evidence](controller/evidence/) includes sanitized execution summaries, exact marker prompt, verifier code and the synthetic certificate. A restricted-network attempt is also retained and is not a task-quality failure. No paid API fallback, model purchase or global configuration change was made.

The verifier consumes original private responses, while shareable summaries are sanitized. Unknown usage remains unknown. Certificates concern the frozen selector and paired loss; the complete verifier/fallback workflow still needs separate end-to-end evaluation. Representative calibration, held-out confirmation, general project integration and independent reproduction remain unfinished.

## Expanded study results — revision 7

All 108 prespecified runs completed, covering 12 synthetic tasks, three repetitions and three conditions. Each arm passed 36/36 runs and 270/270 deterministic checks. The 48 frozen fixture/analysis tests passed after execution; frozen file hashes and task inputs remained unchanged. [Analysis](studies/expanded/results/summary.json) and [final audit](studies/expanded/evidence/final-audit.json) retain the results and evidence boundaries.

| Condition | Accepted runs | Total tokens | Setup + execution + grading seconds | Child sessions |
|---|---:|---:|---:|---:|
| A: Ultra | 36/36 | 3,361,265 | 1,745.10 | 24 |
| B: Medium single-agent | 36/36 | 1,261,590 | 1,033.95 | 0 |
| C: adaptive Medium | 36/36 | 2,060,711 | 1,292.43 | 3 |

Adaptive used 38.7% fewer tokens and 25.9% less elapsed time than Ultra, but **63.3% more tokens and 25.0% more elapsed time than fixed Medium**. The descriptive task-cluster bootstrap ratio intervals were 0.483–0.792 for C/A tokens and 0.622–0.864 for C/A time; C/B intervals were 1.388–1.881 and 1.047–1.481 respectively. These describe resampling within the purposive synthetic suite, not population effects. Cache state and provider contention were not controlled, and tool/delegation choices differed by condition.

All 108 root usage records reconciled with CLI totals; retained hashes matched all 135 root/child rollout files. Final observed configurations were Ultra for all A roots and children, Medium for all B/C roots, and High for the three C children. Cached/reasoning counts are subsets. Development, review, controller smoke testing and failed infrastructure attempts are outside these scored totals; complete project lifecycle usage and subscription-dollar savings are not established.

**The routing invocation gate failed.** C invoked High reviewers in E01 repetitions 2 and 3, and E08 repetition 3. At the prespecified two-of-three task threshold this produces TP=1, FN=7, FP=0, TN=4, below the required six of eight opportunity tasks. E01 child results agree with the corresponding parent outputs; this does not establish causal benefit. The E08 child sent a message before its turn was interrupted; encrypted message content prevents independent semantic integration assessment from the retained readable record. Forced role-conformance probes remain separate evidence of invocation mechanics.

Observed acceptance and critical-check gates passed, but quality noninferiority remains inconclusive. Zero observed task regressions is compatible with a 22.1% upper one-sided bound on regression-task incidence under the binomial model; that quantity is not a confidence interval for acceptance-rate equivalence. The synthetic suite still has a ceiling effect and does not represent general project work.

**Decision:** retain fixed Medium as the practical baseline for this measured workload. The prompt-based adaptive policy has not earned default adoption. The new controller offers explicit execution, accounting and fail-closed calibration mechanics, but has not been evaluated for representative-workload superiority. Broader deployment requires eligible real tasks, frozen feature/labeling rules, independent calibration and held-out confirmation, followed by actual external reproduction. The public contributor tools are prepared; no external reviewer results are claimed.

- Revision 7, 2026-09-15: completed expanded analysis and audit, retained the negative routing finding, and added the tested controller prototype and native conformance evidence. Author and creator: Angelis Pseftis.
