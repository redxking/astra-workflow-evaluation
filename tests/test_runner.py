"""Instrumentation checks. Author: Angelis Pseftis."""
import json
from pathlib import Path
import socket
import tempfile
import unittest
from scripts.execution_sandbox import run_python
from scripts.run_study import collect, sanitize


class InstrumentationTests(unittest.TestCase):
    def test_cumulative_usage_is_not_summed_repeatedly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sessions").mkdir()
            rows = [{"type": "session_meta", "payload": {"id": "parent", "source": "exec"}}]
            for count in [10, 10, 20]:
                rows.append({"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": count, "output_tokens": 2, "total_tokens": count + 2}}}})
            (root / "sessions/parent.jsonl").write_text("\n".join(map(json.dumps, rows)))
            events = root / "events.jsonl"
            events.write_text(json.dumps({"type": "thread.started", "thread_id": "parent"}) + "\n" + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 2}}))
            data, _ = collect(root, events)
            self.assertEqual(data["sessions"][0]["usage"]["total_tokens"], 22)

    def test_absent_usage_remains_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sessions").mkdir()
            (root / "sessions/child.jsonl").write_text(json.dumps({"type": "session_meta", "payload": {"id": "child"}}))
            data, _ = collect(root, root / "missing.jsonl")
            self.assertIsNone(data["sessions"][0]["usage"])

    def test_private_path_redaction(self):
        value = {"path": "/Users/example/run/workspace/file.py", "private": "/Users/example/other.txt"}
        result = sanitize(value, Path("/Users/example/run"), Path("/Users/example/run/runtime"), Path("/Users/example/run/workspace"))
        self.assertEqual(result["path"], "<WORKSPACE>/file.py")
        self.assertNotIn("/Users/", json.dumps(result))

    def test_grader_denies_network_and_private_reads(self):
        with tempfile.NamedTemporaryFile(dir=Path(__file__).resolve().parents[1], mode="w") as canary:
            canary.write("PRIVATE_NEGATIVE_CONTROL")
            canary.flush()
            code = '''import pathlib,socket,json
checks={}
try: pathlib.Path(%r).read_text(); checks['private_read_denied']=False
except PermissionError: checks['private_read_denied']=True
try: socket.create_connection(('127.0.0.1',80),timeout=0.2); checks['network_denied']=False
except PermissionError: checks['network_denied']=True
except OSError: checks['network_denied']=False
print(json.dumps(checks))
''' % canary.name
            result = run_python(code)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"private_read_denied": True, "network_denied": True})

    def test_grader_output_is_bounded(self):
        result = run_python('print("x" * 2_000_000)')
        self.assertLessEqual(len(result.stdout.encode()), 1_048_576)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
