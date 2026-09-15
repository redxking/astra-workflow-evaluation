---
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
---
# Astra workflow evaluation

An exploratory, reproducible comparison of fixed Astra Ultra, single-agent Astra Medium, and a Medium-first adaptive Astra workflow. Read the [report](REPORT.md) before treating this as an optimization recommendation. Four synthetic tasks, one run per task and condition, cannot establish general superiority or unchanged quality.

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
