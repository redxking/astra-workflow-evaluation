---
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
---
# Astra workflow evaluation

An exploratory, reproducible comparison of fixed Astra Ultra, single-agent Astra Medium, and a Medium-first adaptive Astra workflow. Read the [report](REPORT.md) before treating this as an optimization recommendation. The original 12-run pilot and expanded 108-run study are complete. Adaptive was more expensive and slower than fixed Medium in both. The synthetic studies cannot establish general superiority or unchanged quality.

## Evidence

- [Frozen protocol](protocol.json): task order, conditions, file hashes and environment.
- [Fixtures](fixtures): all redistributable task inputs.
- [Results](results): final answers, acceptance checks, sanitized execution events, configuration and usage evidence.
- [Calibration](evidence/calibration): excluded configuration/accounting probes.
- [Evaluator](evaluator.py) and [tests](tests): deterministic acceptance criteria and negative controls.
- [Analysis](scripts/analyze.py): regenerate summary tables from retained records.

The protocol commit predates scored execution. Original host prompt assemblies and session logs stay private because they can contain host metadata; retained SHA-256 hashes support provenance but do not independently prove their contents. No private Daybreak application source is included.

## Try the workflow

Requires a Codex version supporting Astra, its effort levels and custom agents. This pilot used the version recorded in the protocol; availability is account dependent. The installer does not verify model availability. Check it in your Codex installation before applying.

```sh
python3 scripts/install_workflow.py --help
python3 scripts/install_workflow.py
python3 scripts/install_workflow.py --apply
# Revert only if the managed files have not subsequently changed:
python3 scripts/install_workflow.py --rollback
```

Preview is the default. The installer preserves unrelated settings and stores a private rollback record in the selected configuration directory. Read the preview before applying. This is an experimental policy, not a deterministic effort router: a prompt cannot change the active parent's effort during a turn. Higher-effort specialists require actual delegation and runtime verification. This study reports what occurred rather than assuming policy text enforced an action.

## Reproduce

Python 3 and an authenticated native Codex CLI are required. Coding acceptance execution currently requires macOS `sandbox-exec`; unsupported environments fail closed. No paid API key is required by the runner. Live reproduction consumes your normal Codex allowance.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_study.py --help
python3 scripts/analyze.py
python3 scripts/verify_release.py
```

For each entry in `protocol.json`, run the runner with its exact task, arm and run ID, a new private runtime directory outside this repository, the native CLI path and your local authentication-file path. The runner accesses authentication through a symlink and does not copy its contents. Keep runtime folders private. Preserve existing evidence; use a separate checkout/output location for a replication. Grade the unmodified response using `evaluator.evaluate(task_id, response)` and retain the score. Original collection records require the privacy processing documented in the report before publication.

The recorded comparison includes setup, execution and grading. It excludes study development and release work; it is not a lifecycle cost study. Cached input is a subset of input, reasoning output is a subset of output, and token counts are not subscription charges.

MIT license. Author: Angelis Pseftis. No external reproduction or production-wide validation is claimed.

## Follow-up validation

The expanded 108-run study is complete. Its [protocol](studies/expanded/protocol.json), [fixtures and runner](studies/expanded), and [four passing forced conformance probes](studies/expanded/evidence/conformance-summary.json) are available. Results and limitations are reported below. Original pilot results are preserved.

## Stronger-validation tools

The [independent-reproduction kit](reproducibility/README.md), [blinded-review exporter](validation/review/README.md), [real-workload candidate inventory](validation/workloads/README.md), and [sample-size planning sensitivity](validation/design/README.md) are implemented and tested. They prepare future validation; no independent external result or real-workload performance claim is established by these tools.

## Experimental task-boundary controller

[Controller instructions](controller/README.md) cover training/calibration, explicit Astra effort, trusted verification and retained fallback attempts. Forty-two automated tests and native Medium / forced Low-to-Medium conformance checks passed. This is a read-only prototype with synthetic conformance evidence, not a globally deployed or representative-workload-certified optimizer. See the authoritative report for evidence boundaries.

## Completed expanded study

All 108 runs passed their deterministic task checks. Adaptive used **63.3% more tokens and 25.0% more elapsed time than fixed Medium**, despite improving on Ultra. Its natural routing gate failed (1/8 opportunity tasks met the required repeat threshold). [Read the report](REPORT.md#expanded-study-results--revision-7) and [retained analysis](studies/expanded/results/summary.json). These results support Medium as the measured baseline, not universal superiority or quality equivalence.
