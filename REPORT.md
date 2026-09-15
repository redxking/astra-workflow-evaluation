---
title: Astra Workflow Evaluation — Controlled Pilot
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
modified: 2026-09-15
revision: 3
status: Original pilot complete; expanded validation in preparation
---

# Astra Workflow Evaluation — Controlled Pilot

This is the single authoritative report for a 12-run exploratory evaluation of three Astra development configurations. All 12 scored runs completed without repairs or retries. The protocol and scoring code were frozen before scored model execution.

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
