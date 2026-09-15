#!/usr/bin/env python3
"""Preview/apply a minimal workflow overlay; Author: Angelis Pseftis."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tomllib

REPO = Path(__file__).resolve().parents[1]
START, END = "<!-- astra-workflow:start -->", "<!-- astra-workflow:end -->"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def set_key(text, section, key, value):
    lines = text.splitlines(keepends=True)
    begin, end = 0, len(lines)
    if section:
        candidates = [i for i, line in enumerate(lines) if line.strip() == f"[{section}]"]
        if not candidates:
            return text.rstrip() + f"\n\n[{section}]\n{key} = {value}\n"
        begin = candidates[0] + 1
    for i in range(begin, len(lines)):
        if lines[i].lstrip().startswith("["):
            end = i
            break
    for i in range(begin, end):
        if re.match(r"^\s*" + re.escape(key) + r"\s*=", lines[i]):
            lines[i] = f"{key} = {value}\n"
            return "".join(lines)
    lines.insert(end, f"{key} = {value}\n")
    return "".join(lines)


def proposed(home):
    config_path = home / "config.toml"
    old = config_path.read_text() if config_path.exists() else ""
    before = tomllib.loads(old)
    updated = old
    for key, value in [("model", '"gpt-6-astra"'), ("model_reasoning_effort", '"medium"'), ("plan_mode_reasoning_effort", '"medium"')]:
        updated = set_key(updated, "", key, value)
    for key, value in [("enabled", "true"), ("default_subagent_model", '"gpt-6-astra"'), ("default_subagent_reasoning_effort", '"medium"'), ("max_concurrent_threads_per_session", "2")]:
        updated = set_key(updated, "agents", key, value)
    after = tomllib.loads(updated)  # Complex unsupported TOML representations fail before writes.
    expected = dict(before)
    expected.update(model="gpt-6-astra", model_reasoning_effort="medium", plan_mode_reasoning_effort="medium")
    expected["agents"] = dict(before.get("agents", {}), enabled=True, default_subagent_model="gpt-6-astra", default_subagent_reasoning_effort="medium", max_concurrent_threads_per_session=2)
    if after != expected:
        raise ValueError("Unexpected nonrouting configuration change")
    instructions_path = home / "AGENTS.md"
    original = instructions_path.read_text() if instructions_path.exists() else ""
    body = (REPO / "config/adaptive.md").read_text().split("\n", 1)[1].strip()
    block = START + "\n## Adaptive Model, Reasoning, and Work Routing\n\n" + body + "\n" + END
    if START in original or END in original:
        if original.count(START) != 1 or original.count(END) != 1:
            raise ValueError("Ambiguous managed instruction markers")
        revised = original[:original.index(START)] + block + original[original.index(END) + len(END):]
    elif "## Adaptive Model, Reasoning, and Work Routing" in original:
        begin = original.index("## Adaptive Model, Reasoning, and Work Routing")
        next_section = re.search(r"^## ", original[begin + 3:], flags=re.M)
        end = begin + 3 + next_section.start() if next_section else len(original)
        revised = original[:begin] + block + "\n\n" + original[end:]
    else:
        revised = original.rstrip() + ("\n\n" if original.strip() else "") + block + "\n"
    outputs = {"config.toml": updated, "AGENTS.md": revised}
    for path in (REPO / "config/agents").glob("*.toml"):
        outputs["agents/" + path.name] = path.read_text()
    return outputs


def install(home, apply=False):
    outputs = proposed(home)
    changes = []
    for name, new in outputs.items():
        path = home / name
        existed = path.exists()
        old = path.read_text() if existed else ""
        if old == new:
            continue
        reverse_edits = [{"start": j1, "end": j2, "text": old[i1:i2]} for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes() if tag != "equal"]
        changes.append({"name": name, "existed": existed, "before_sha256": sha(old), "after_sha256": sha(new), "reverse_edits": reverse_edits})
    summary = {"mode": "apply" if apply else "dry-run", "files": [x["name"] for x in changes], "permissions_changed": False}
    if apply and changes:
        home.mkdir(parents=True, exist_ok=True)
        rollback = home / "astra-workflow.rollback.json"
        if rollback.exists():
            raise ValueError("Existing rollback record must be resolved before another changed installation")
        rollback.write_text(json.dumps({"author": "Angelis Pseftis", "changes": changes}, indent=2) + "\n")
        rollback.chmod(0o600)
        for change in changes:
            path = home / change["name"]
            current = path.read_text() if path.exists() else ""
            if sha(current) != change["before_sha256"]:
                raise ValueError("Concurrent change; stop and inspect rollback record")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(outputs[change["name"]])
    return summary


def rollback(home):
    record_path = home / "astra-workflow.rollback.json"
    record = json.loads(record_path.read_text())
    restored = {}
    allowed = {"config.toml", "AGENTS.md"} | {"agents/" + p.name for p in (REPO / "config/agents").glob("*.toml")}
    for change in record["changes"]:
        if change["name"] not in allowed:
            raise ValueError("Unexpected rollback target")
        path = home / change["name"]
        new = path.read_text() if path.exists() else ""
        if sha(new) == change["before_sha256"]:
            continue
        if sha(new) != change["after_sha256"]:
            raise ValueError("Refusing to overwrite post-install edits")
        for edit in reversed(change["reverse_edits"]):
            new = new[:edit["start"]] + edit["text"] + new[edit["end"]:]
        if sha(new) != change["before_sha256"]:
            raise ValueError("Rollback identity mismatch")
        restored[path] = new if change["existed"] else None
    for path, old in restored.items():
        if old is None:
            path.unlink()
        else:
            path.write_text(old)
    record_path.unlink()
    return {"mode": "rollback", "restored_files": len(restored)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    print(json.dumps(rollback(args.home) if args.rollback else install(args.home, args.apply), indent=2))


if __name__ == "__main__":
    main()
