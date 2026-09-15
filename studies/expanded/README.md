---
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
---
# Expanded validation

This follow-up preserves the original pilot and tests a revised adaptive policy on 12 new synthetic tasks with three repetitions per condition. See the single authoritative [report](../../REPORT.md) for current findings and limitations. The frozen protocol is the authority for run order, labels, criteria and source hashes.

Four separate forced conformance probes test Astra Low, Medium, High and Extra High specialist execution and integration. They are not evidence that the adaptive policy chooses delegation appropriately or saves tokens.

## Reproduction

Use a separate checkout for a replication and retain the published original evidence. Native Codex subscription authentication, a supported Astra client, and Python 3 are required. No paid API fallback is used. The private runtime location must be outside the study and public repository; never commit its authentication symlink or original host session logs.

```sh
python3 -m unittest discover -s studies/expanded/tests -v
python3 studies/expanded/scripts/execute.py --help
python3 studies/expanded/scripts/conformance.py --help
python3 studies/expanded/scripts/analyze.py
```

`execute.py` accepts `--cli`, `--private-root`, and `--auth-file`. It verifies frozen hashes before each run, executes the protocol order sequentially, grades unchanged responses and checkpoints to the private runtime. Completed scores are skipped on resume. Never launch duplicate controllers. An interrupted process may leave a controller lock; verify its recorded PID has stopped before removing a stale lock. To perform a fresh replication, remove published result folders only in the separate replication checkout and select a new private runtime path.

Model inputs contain only each task's prompt and fixture files. The oracle and routing-opportunity labels remain outside that workspace. Output correctness is judged against explicit structured contracts, including safety and evidence distinctions. This does not assess open-ended prose, real deployment behavior, or all development quality. The tasks were authored for this study, not randomly sampled from a workload population.

The analysis uses task clusters, preserving all repeats together. Cached tokens and reasoning tokens are subsets, not additional costs. Unknown session usage blocks complete token comparisons. Original logs can contain sensitive host metadata and are withheld; public records contain sanitized usage, responses and tool evidence plus provenance hashes. Source privacy scanning is required before each publication.
