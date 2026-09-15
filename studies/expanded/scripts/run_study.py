#!/usr/bin/env python3
"""Reproducible local Codex study. Author: Angelis Pseftis.

Runtime homes and original logs stay outside this public repository. The native
Codex client reads its own login through a local symlink; this program never
reads, copies, prints, or publishes credential contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
ARMS = {"A": ("ultra", "ultra"), "B": ("medium", "medium"), "C": ("medium", "adaptive")}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def env_for(runtime):
    env = dict(os.environ)
    for name in list(env):
        if name.startswith(("OPENAI_", "CODEX_API_")):
            env.pop(name)
    # Intended, child-process-only configuration-home selection, not mutation
    # of the user's environment or global installation.
    env["CODEX_HOME"] = str(runtime)
    return env


def prepare(runtime, arm, auth_file):
    effort, policy = ARMS[arm]
    runtime.mkdir(parents=True, exist_ok=False)
    (runtime / "auth.json").symlink_to(auth_file)
    instructions = (REPO / "config/common.md").read_text() + "\n" + (REPO / f"config/{policy}.md").read_text()
    (runtime / "AGENTS.md").write_text(instructions)
    config = f'''model = "gpt-6-astra"
model_provider = "openai"
forced_login_method = "chatgpt"
model_reasoning_effort = "{effort}"
approval_policy = "never"
sandbox_mode = "read-only"
service_tier = "default"
web_search = "disabled"
project_doc_max_bytes = 0
[agents]
enabled = {str(arm != 'B').lower()}
max_concurrent_threads_per_session = 2
default_subagent_model = "gpt-6-astra"
default_subagent_reasoning_effort = "{effort}"
[features]
plugins = false
apps = false
memories = false
skip_host_skill_discovery = true
[memories]
use_memories = false
generate_memories = false
'''
    (runtime / "config.toml").write_text(config)
    if arm != "B":
        (runtime / "agents").mkdir()
        for source in sorted((REPO / "config/agents").glob("*.toml")):
            text = source.read_text()
            if arm == "A":
                text = re.sub(r'model_reasoning_effort = "[^"]+"', 'model_reasoning_effort = "ultra"', text)
                text = re.sub(r'description = "[^"]+"', 'description = "Fixed Astra Ultra specialist for this baseline."', text)
            (runtime / "agents" / source.name).write_text(text)
    return config, instructions


def inspect_prompt(cli, runtime, cwd, arm, output):
    cmd = [cli, "-C", str(cwd), "debug", "prompt-input", "CONFIGURATION_INSPECTION_ONLY"]
    r = subprocess.run(cmd, env=env_for(runtime), capture_output=True, text=True, timeout=60)
    output.write_text(r.stdout)
    if r.returncode:
        raise RuntimeError("Prompt assembly failed: " + r.stderr[-400:])
    data = json.loads(r.stdout)
    rendered = json.dumps(data)
    checks = {
        "personal_instructions_absent": "Standing Personalization Instructions" not in rendered,
        "personal_memory_absent": "MEMORY_SUMMARY" not in rendered,
        "common_contract_loaded": "Evaluation operating contract" in rendered,
        "candidate_policy_matches_arm": ("Adaptive Astra routing policy" in rendered) == (arm == "C"),
        "baseline_policy_matches_arm": ("Fixed Medium baseline" in rendered) == (arm == "B") and ("Fixed Ultra baseline" in rendered) == (arm == "A"),
    }
    if not all(checks.values()):
        raise RuntimeError("Instruction isolation failed: " + str(checks))
    return {"checks": checks, "prompt_assembly_sha256": digest(output), "serialized_characters": len(r.stdout)}


def read_jsonl(path):
    result = []
    if not path.exists():
        return result
    for line in path.read_text(errors="replace").splitlines():
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return result


def sanitize(value, private_root, runtime, workspace):
    if isinstance(value, dict):
        return {k: sanitize(v, private_root, runtime, workspace) for k, v in value.items() if k != "rate_limits"}
    if isinstance(value, list):
        return [sanitize(v, private_root, runtime, workspace) for v in value]
    if isinstance(value, str):
        for source, target in [(str(workspace), "<WORKSPACE>"), (str(runtime), "<RUNTIME>"), (str(private_root), "<PRIVATE_RUNS>"), (str(REPO), "<REPOSITORY>")]:
            value = value.replace(source, target)
        value = re.sub(r"/Users/[^/\s\"']+", "<USER_HOME>", value)
        value = re.sub(r"/var/folders/[^\s\"']+", "<TEMP_PATH>", value)
        return value
    return value


def collect(runtime, events_path):
    sessions = []
    for path in sorted((runtime / "sessions").rglob("*.jsonl")):
        rows = read_jsonl(path)
        metas = [x["payload"] for x in rows if x.get("type") == "session_meta"]
        contexts = [x["payload"] for x in rows if x.get("type") == "turn_context"]
        counts = [x["payload"] for x in rows if x.get("type") == "event_msg" and x.get("payload", {}).get("type") == "token_count"]
        usage = next((x.get("info", {}).get("total_token_usage") for x in reversed(counts) if isinstance(x.get("info"), dict) and x["info"].get("total_token_usage")), None)
        meta = metas[0] if metas else {}
        sessions.append({"id": meta.get("id"), "source": meta.get("source"), "rollout_sha256": digest(path), "model_effort": [{"turn_id": c.get("turn_id"), "model": c.get("model"), "effort": c.get("effort"), "sandbox": c.get("sandbox_policy")} for c in contexts], "usage": usage, "usage_event_count": len(counts), "usage_events": counts, "tool_events": [x["payload"] for x in rows if x.get("type") == "response_item" and x.get("payload", {}).get("type") in {"function_call", "function_call_output", "custom_tool_call", "custom_tool_call_output"}], "started_at": meta.get("timestamp"), "last_event_at": rows[-1].get("timestamp") if rows else None})
    events = read_jsonl(events_path)
    root_id = next((x.get("thread_id") for x in events if x.get("type") == "thread.started"), None)
    final_usages = [x.get("usage") for x in events if x.get("type") == "turn.completed"]
    public = []
    for event in events:
        if event.get("type", "").startswith("item.") and event.get("item", {}).get("type") in {"reasoning", "reasoning_summary"}:
            continue
        public.append(event)
    return {"root_id": root_id, "cli_completed_usage": final_usages, "sessions": sessions}, public


def run_one(cli, private_root, auth, run_id, task_id, arm, prompt_override=None, timeout=300):
    setup_clock = time.monotonic()
    root = private_root / run_id
    root.mkdir(parents=True, exist_ok=False)
    workspace = root / "workspace"
    if task_id:
        shutil.copytree(REPO / "fixtures" / task_id, workspace)
        task = json.loads((workspace / "task.json").read_text())
        prompt = task["prompt"]
    else:
        workspace.mkdir()
        prompt = prompt_override
    runtime = root / "runtime"
    input_before = {str(p.relative_to(workspace)): digest(p) for p in sorted(workspace.rglob("*")) if p.is_file()}
    config, instructions = prepare(runtime, arm, auth)
    inspection = inspect_prompt(cli, runtime, workspace, arm, root / "prompt-assembly.json")
    command = [cli, "exec", "--skip-git-repo-check", "--json", "--color", "never", "-C", str(workspace), "--output-schema", str(REPO / "config/response.schema.json"), "-o", str(root / "response.json"), "-"]
    setup_seconds = time.monotonic() - setup_clock
    started = stamp()
    start_clock = time.monotonic()
    timed_out = False
    with (root / "events.jsonl").open("w") as stdout, (root / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, env=env_for(runtime), stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    elapsed = time.monotonic() - start_clock
    accounting, events = collect(runtime, root / "events.jsonl")
    response = None
    parse_error = None
    try:
        response = json.loads((root / "response.json").read_text())
    except (OSError, ValueError) as exc:
        parse_error = str(exc)
    input_after = {str(p.relative_to(workspace)): digest(p) for p in sorted(workspace.rglob("*")) if p.is_file()}
    record = {"run_id": run_id, "task_id": task_id, "arm": arm, "started_at": started, "ended_at": stamp(), "elapsed_seconds": elapsed, "timeout_seconds": timeout, "timed_out": timed_out, "exit_code": process.returncode, "instruction_isolation": inspection, "config_sha256": digest(runtime / "config.toml"), "instructions_sha256": digest(runtime / "AGENTS.md"), "input_hashes": input_before, "input_hashes_after": input_after, "input_unchanged": input_before == input_after, "accounting": accounting, "response": response, "response_parse_error": parse_error, "human_intervention": False, "operational_status": "completed" if process.returncode == 0 and not timed_out and response is not None else "failed"}
    record["setup_seconds"] = setup_seconds
    write_json(root / "record.json", record)
    target = REPO / ("evidence/calibration" if task_id is None else "results") / run_id
    target.mkdir(parents=True, exist_ok=True)
    clean = lambda value: sanitize(value, private_root, runtime, workspace)
    write_json(target / "record.json", clean(record))
    (target / "events.jsonl").write_text("".join(json.dumps(clean(e)) + "\n" for e in events))
    (target / "stderr.log").write_text(clean((root / "stderr.log").read_text(errors="replace")))
    (target / "effective-config.toml").write_text(config)
    (target / "instructions.md").write_text(instructions)
    write_json(target / "original-evidence-hashes.json", {name: digest(root / name) for name in ["events.jsonl", "stderr.log", "prompt-assembly.json", "record.json"]})
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--auth-file", type=Path, required=True)
    parser.add_argument("--calibration", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--task")
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args()
    args.private_root = args.private_root.resolve()
    args.auth_file = args.auth_file.resolve()
    if REPO == args.private_root or REPO in args.private_root.parents:
        parser.error("Private runtime root must be outside the public repository")
    if not args.auth_file.is_file():
        parser.error("Native Codex auth unavailable; do not use an API fallback")
    if args.calibration:
        prompt = 'Calibration only, no fixture task. Spawn exactly one bounded default subagent using GPT-6 Astra at low reasoning with no inherited conversation. Ask it to return CHILD_OK, without tools. While it works, independently compute 2+2. Wait for its answer, then return {"answer":"CALIBRATION_OK; CHILD_OK; 4","code":""}. Do not do other work.'
        rec = run_one(args.cli, args.private_root, args.auth_file, "calibration-team", None, "C", prompt, 180)
    else:
        if not all([args.run_id, args.task, args.arm]):
            parser.error("run-id, task and arm are required")
        rec = run_one(args.cli, args.private_root, args.auth_file, args.run_id, args.task, args.arm)
    print(json.dumps({k: rec[k] for k in ["run_id", "operational_status", "elapsed_seconds", "exit_code"]}))


if __name__ == "__main__":
    main()
