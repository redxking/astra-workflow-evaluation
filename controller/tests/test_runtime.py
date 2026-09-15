"""Offline native adapter tests. Author: Angelis Pseftis."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("controller_runtime", Path(__file__).parents[1] / "runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()
        self.auth = self.base / "auth.json"
        self.auth.write_text("AUTH_CONTENT_MUST_NOT_BE_READ")
        self.native = {"config": {"model": "gpt-6-astra", "model_reasoning_effort": "medium",
                                  "sandbox_mode": "read-only", "approval_policy": "never",
                                  "forced_login_method": "chatgpt", "agents": {"enabled": False},
                                  "features": {"plugins": False, "apps": False, "memories": False,
                                               "skip_host_skill_discovery": True},
                                  "memories": {"use_memories": False, "generate_memories": False},
                                  "project_doc_max_bytes": 0, "web_search": "disabled"},
                       "origins": {"model": {"name": {"type": "user", "file": str(self.base / "runtime/config.toml")},
                                              "version": "test"}}}

    def invoke(self, mode="ok", **overrides):
        def command(command, **kw):
            kw["stderr_path"].write_text("")
            if "debug" in command:
                kw["stdout_path"].write_text(json.dumps([{"text": "Evaluation operating contract" +
                    (" MEMORY_SUMMARY" if mode == "memory" else "")}]))
                return {"exit_code": 0, "timed_out": False}
            root = kw["stdout_path"].parent
            home = root / "runtime"
            self.assertTrue((home / "auth.json").is_symlink())
            self.assertNotIn("OPENAI_API_KEY", kw["env"])
            self.assertNotIn("CODEX_API_TEST", kw["env"])
            usage = {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 4}
            rows = [{"type": "thread.started", "thread_id": "root"}]
            if mode != "missing_usage":
                rows.append({"type": "turn.completed", "usage": usage})
            kw["stdout_path"].write_text("\n".join(map(json.dumps, rows)))
            response = {"answer": "ok", "code": "raise Exception('must never execute')"}
            if mode == "hostile_schema":
                response["extra"] = "no"
            if mode == "wrong_type":
                response["code"] = ["bad"]
            (root / "response.json").write_text("{" if mode == "bad_json" else json.dumps(response))
            session = home / "sessions"
            session.mkdir()
            rollout = [{"type": "session_meta", "payload": {"id": "root"}},
                       {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "low"}},
                       {"type": "turn_context", "payload": {"model": "gpt-6-astra",
                                      "effort": "ultra" if mode == "mismatch" else "medium"}}]
            if mode != "missing_usage":
                rollout.append({"type": "event_msg", "payload": {"type": "token_count", "info": {
                    "total_token_usage": dict(usage, input_tokens=99 if mode == "usage_mismatch" else 10)}}})
            (session / "rollout.jsonl").write_text("\n".join(map(json.dumps, rollout)))
            return {"exit_code": -15 if mode == "timeout" else 0, "timed_out": mode == "timeout"}

        args = dict(cli="fake", workspace=self.workspace, prompt="bounded task", effort="medium",
                    private_run=self.base / "attempt", auth_file=self.auth)
        args.update(overrides)
        with patch.object(runtime, "_native_config", return_value=self.native), \
                patch.object(runtime, "_command", side_effect=command), \
                patch.dict(os.environ, {"OPENAI_API_KEY": "not-used", "CODEX_API_TEST": "not-used"}):
            return runtime.run_task(**args)

    def test_success_last_root_turn_and_usage(self):
        result = self.invoke()
        self.assertEqual(result["operational_status"], "completed")
        self.assertEqual(result["observed_effort"], "medium")
        self.assertEqual(result["usage"]["reconciliation"], "matched")
        self.assertEqual(result["usage"]["reconciled"]["input_tokens"], 10)
        self.assertFalse(result["scope"]["code_executed"])
        self.assertIn("record.json", result["original_hashes"])
        self.assertEqual(self.auth.read_text(), "AUTH_CONTENT_MUST_NOT_BE_READ")

    def test_effort_mismatch_fails(self):
        result = self.invoke("mismatch")
        self.assertEqual(result["operational_status"], "failed")
        self.assertIn("observed_model_effort_mismatch_or_missing", result["failure_reasons"])

    def test_missing_usage_is_unknown(self):
        result = self.invoke("missing_usage")
        self.assertIsNone(result["usage"]["reconciled"])
        self.assertEqual(result["usage"]["reconciliation"], "usage-unresolved")
        self.assertEqual(result["operational_status"], "completed")

    def test_usage_mismatch_is_not_zero(self):
        result = self.invoke("usage_mismatch")
        self.assertIsNone(result["usage"]["reconciled"])
        self.assertEqual(result["usage"]["reconciliation"], "mismatch")

    def test_timeout_fails(self):
        result = self.invoke("timeout")
        self.assertEqual(result["operational_status"], "failed")
        self.assertIn("execution_timeout", result["failure_reasons"])

    def test_existing_private_refused(self):
        (self.base / "attempt").mkdir()
        with self.assertRaises(FileExistsError):
            self.invoke()

    def test_private_in_git_refused(self):
        (self.base / ".git").mkdir()
        with self.assertRaises(ValueError):
            self.invoke()

    def test_bad_effort(self):
        with self.assertRaises(ValueError):
            self.invoke(effort="maximum")

    def test_native_model_mismatch_prevents_execution(self):
        self.native["config"]["model"] = "other"
        result = self.invoke()
        self.assertEqual(result["operational_status"], "failed")
        self.assertFalse((self.base / "attempt/events.jsonl").exists())

    def test_memory_contamination_prevents_execution(self):
        result = self.invoke("memory")
        self.assertEqual(result["operational_status"], "failed")
        self.assertFalse((self.base / "attempt/events.jsonl").exists())

    def test_native_agents_enabled_prevents_execution(self):
        self.native["config"]["agents"]["enabled"] = True
        result = self.invoke()
        self.assertEqual(result["operational_status"], "failed")
        self.assertFalse((self.base / "attempt/events.jsonl").exists())

    def test_duplicate_response_keys_rejected(self):
        with self.assertRaises(ValueError):
            runtime._response_json('{"answer":"a","answer":"b","code":""}')

    def test_schema_failures_are_not_repaired(self):
        for mode in ["hostile_schema", "wrong_type", "bad_json"]:
            with self.subTest(mode=mode):
                result = self.invoke(mode, private_run=self.base / mode)
                self.assertEqual(result["operational_status"], "failed")
                self.assertIsNone(result["response"])

    def test_sanitizer_paths_keys_tokens(self):
        source = {str(self.auth): {"text": str(self.workspace) + " /Users/alice/secret.txt "
                  "sk-abcdefghijklmnopqrst Bearer abcdefg access_token=secret123 "
                  "eyJabcdefghijklmnop.qwertyuiop.asdfghjkl", "access_token": "private-token-value"}}
        clean = runtime.sanitize(source, private_run=self.base / "attempt", runtime=self.base / "runtime",
                                 workspace=self.workspace, auth_file=self.auth)
        text = json.dumps(clean)
        for secret in [str(self.auth), "/Users/alice", "sk-abcdef", "abcdefg", "secret123", "eyJ", "private-token-value"]:
            self.assertNotIn(secret, text)

    def test_real_process_timeout(self):
        result = runtime._command(["/bin/sleep", "30"], env=dict(os.environ), cwd=self.workspace,
                                  stdin=None, stdout_path=self.base / "stdout", stderr_path=self.base / "stderr",
                                  timeout=0.05)
        self.assertTrue(result["timed_out"])
        self.assertNotEqual(result["exit_code"], 0)

    def test_native_config_fake_executable_no_model_call(self):
        executable = self.base / "fake-codex"
        executable.write_text('''#!/usr/bin/env python3
import sys,json
for line in sys.stdin:
    row=json.loads(line)
    if row.get('method')=='initialize':
        print(json.dumps({'id':1,'result':{}}),flush=True)
    elif row.get('method')=='config/read':
        print(json.dumps({'id':2,'result':{'config':{'model':'gpt-6-astra'},'origins':{}}}),flush=True)
''')
        executable.chmod(0o700)
        home = self.base / "home"
        home.mkdir()
        result = runtime._native_config(str(executable), home, self.workspace, self.base, 3)
        self.assertEqual(result["config"]["model"], "gpt-6-astra")
        self.assertTrue((self.base / "config-read.stdout.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
