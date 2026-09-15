# Astra task-boundary controller

Author: Angelis Pseftis

Experimental controller: learn a finite family of effort rules from training rows, test those rules against a separate calibration set, then launch a task with an explicitly configured Astra effort. Without an admissible certificate, use the trusted reference effort (Medium by default). This is not installed as a global Codex default.

## Run locally

Requires Python 3.10+, a compatible native Codex CLI with ChatGPT authentication, and an existing task workspace. No API billing fallback is implemented. Compatibility was developed against Codex CLI 0.154.0-alpha.6.2; configuration mismatches fail closed.

```sh
python3 -m unittest discover -s controller/tests -v
python3 controller/cli.py calibrate --training train.json --calibration cal.json --output certificate.json --reference medium --candidate low --data-kind observed
python3 controller/cli.py run --cli /path/to/codex --workspace /path/to/task --prompt-file prompt.txt --features features.json --certificate certificate.json --private-run /path/outside/git/new-run --auth-file /path/to/native/auth.json --verifier-argv '["python3","verify.py"]'
```

The explicit trusted verifier receives the original response JSON path as its final argument. It must exit zero only when its acceptance criteria pass. The controller never executes generated code. A missing verifier yields `unverified`. A rejected candidate can trigger one reference-effort attempt; both attempts and their usage remain in the record. Execution failures stop and retain evidence. Verifier execution is trusted local code, not sandboxed by this controller.

Each row has task_id, cluster_id, numeric features, and paired outcomes for the two efforts. For example:

```json
{"task_id":"t1","cluster_id":"project1","features":{"size":20},"outcomes":{"low":{"passed":true,"tokens":100},"medium":{"passed":true,"tokens":200}}}
```

Training and calibration task/cluster IDs must be disjoint, and each calibration cluster appears once. Feature extraction must be available before running the task and frozen across training, calibration and deployment. Identifiers alone cannot prove independent sampling. Labels must come from a defensible acceptance process. `--data-kind synthetic_demo` certificates are disabled for execution unless `--allow-demonstration` is explicit. Provenance labels are user assertions, not independently authenticated facts.

## Statistical scope

Training generates at most 100 policies, including the reference. Calibration tests the one-sided paired loss: reference passes and selected candidate fails. Exact binomial lower-tail tests with Bonferroni correction admit policies under the stated independent, identically distributed sampling assumptions. Selection minimizes observed calibration tokens among admitted policies and the reference. This does not certify absolute accuracy, future cost savings, arbitrary workloads, or quality of the reference itself.

Supported delta is [1e-12,1); calibration is limited to 100,000 rows to bound numerical and validation work. Alpha zero admits no cheaper policy from finite data. Hashes detect inconsistent edits; they are not signatures and cannot authenticate data. Missing, inconsistent or out-of-range features return the externally configured reference. Deployment drift inside observed feature bounds remains possible.

The certificate concerns the frozen selector and measured paired loss. The verifier/fallback workflow requires its own end-to-end evaluation and calibration. Model version, prompts, tools, feature extractor, verifier and sampling changes can invalidate applicability.

## Runtime and evidence boundaries

Every attempt uses an isolated configuration home, existing native-auth symlink, Astra-only model, requested effort, read-only model sandbox, and disabled delegation, apps, plugins, memory and web. Preflight verifies native configuration and prompt isolation. Read-only restricts writes; permitted reading scope also relies on instructions and is not a filesystem confidentiality boundary. Routing occurs at task boundaries, not inside an active parent turn.

Private originals, configuration provenance, timings, verifier logs and reconciled root usage remain outside Git. Public summaries require privacy review; redaction is best effort. Cached input and reasoning output are subsets, never extra tokens. Any unresolved attempt makes corresponding aggregate usage unknown. Successful protocol execution is distinct from verifier acceptance and independent validation.

This prototype supports read-only answer/code tasks. General project editing, durable installation, representative calibration, held-out confirmation and independent reproduction remain release gates before broad adoption.
