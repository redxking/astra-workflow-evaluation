---
title: Astra Workflow Evaluation — Controlled Pilot
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
modified: 2026-09-15
revision: 1
status: Frozen protocol; scored runs pending
---

# Astra Workflow Evaluation — Controlled Pilot

This is the single authoritative report for a 12-run exploratory evaluation of three Astra development configurations. Results are pending. The protocol and scoring code were frozen before scored model execution.

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

Pending completion of all frozen runs.

## Limitations and claim boundary

Four tasks and one run per task/condition do not justify a population-level claim of superiority or equivalence. Cached-prefix state and provider contention are not controlled. The task suite is deliberately small and mostly deterministic; a perfect score can be a ceiling effect. Each condition may make different tool or delegation decisions. Exact prompts, policies, evidence, and failures will be retained so those differences can be examined.

No savings, speed improvement, or absence of quality loss is asserted before results are available. Subscription allowance and monetary cost cannot be inferred directly from token totals. A reproducible local release is not proof of successful reproduction by another user.

## Revision record

- Revision 1, 2026-09-15: recorded frozen method and preflight evidence before scored runs. Author and creator: Angelis Pseftis.
