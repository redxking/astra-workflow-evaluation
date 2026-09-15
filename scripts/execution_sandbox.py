"""Bounded macOS execution for synthetic grading. Author: Angelis Pseftis."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile


def run_python(script: str, stdin_text: str = "", timeout: float = 5):
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        raise RuntimeError("This release requires the tested macOS sandbox; execution is unavailable on this platform")
    with tempfile.TemporaryDirectory(prefix="astra-grader-") as temporary:
        root = Path(temporary).resolve()
        path = root / "grade.py"
        path.write_text(script)
        profile = '''(version 1)(deny default)(allow process*)(allow sysctl-read)(allow mach-lookup)
(allow file-read* (require-all (require-not (subpath "/Users")) (require-not (subpath "/Volumes")) (require-not (subpath "/private/tmp")) (require-not (subpath "/tmp")) (require-not (subpath "/private/var/folders")) (require-not (subpath "/var/folders"))))
(allow file-read* file-write* (subpath %s))''' % json.dumps(str(root))

        def limits():
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            # macOS rejects lowering RLIMIT_DATA on the tested Python runtime.
            # No memory-isolation claim is made; these are small synthetic tests.

        command = ["/usr/bin/sandbox-exec", "-p", profile, sys.executable, "-I", str(path)]
        stdout_path, stderr_path = root / "stdout.txt", root / "stderr.txt"
        with stdout_path.open("w") as out, stderr_path.open("w") as err:
            process = subprocess.Popen(command, cwd=root, env={"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8", "TMPDIR": str(root)}, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True, start_new_session=True, preexec_fn=limits)
            try:
                process.communicate(stdin_text, timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                raise
        stdout, stderr = stdout_path.read_text(errors="replace"), stderr_path.read_text(errors="replace")
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
