# Checks for exercise 03, one or more per step of README.md. Run: python3 exercises/check.py 03
#
# They need no Docker: a stand-in `docker` on PATH runs the command with bash in the mounted workspace.
# That checks your process handling, not the container. test_docker.py checks the real container and
# its timeout when Docker is running.

import os
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path

from check import Workspace, call, error_of, load_tool

FAKE_DOCKER = f"""#!{sys.executable}
# Stand-in for `docker run --init ... --volume <workspace>:/workspace ... bash -c <command>`.
import os, signal, subprocess, sys
args = sys.argv[1:]
workspace = args[args.index("--volume") + 1].rsplit(":/workspace", 1)[0]
# Like --init: the command gets its own process group, and SIGTERM stops all of it.
proc = subprocess.Popen(args[-3:], cwd=workspace, start_new_session=True)
signal.signal(signal.SIGTERM, lambda *_: os.killpg(proc.pid, signal.SIGTERM))
sys.exit(proc.wait())
"""


class BashTest(Workspace):
    def setUp(self):
        super().setUp()
        self.bash = load_tool("bash")
        bin_dir = Path(tempfile.mkdtemp(prefix="pi2-fake-docker-"))
        self.addCleanup(shutil.rmtree, bin_dir, ignore_errors=True)
        docker = bin_dir / "docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(docker.stat().st_mode | stat.S_IEXEC)
        self.path = os.environ["PATH"]
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{self.path}"
        self.addCleanup(os.environ.__setitem__, "PATH", self.path)

    def test_1_runs_the_command(self):
        """Step 1: the command runs and its output comes back."""
        self.assertIn("hello", call(self.bash, {"command": "echo hello"}, self.cwd))

    def test_1_in_the_workspace(self):
        """Step 1: the command runs in ctx.cwd, mounted as the workspace."""
        (self.cwd / "marker.txt").write_text("found me\n")
        self.assertIn("found me", call(self.bash, {"command": "cat marker.txt"}, self.cwd))

    def test_1_no_docker(self):
        """Step 1: without Docker, the exception says that Docker is missing."""
        os.environ["PATH"] = tempfile.gettempdir()  # no docker here
        error = error_of(self.bash, {"command": "echo hi"}, self.cwd)
        message = str(error)
        self.assertIn("docker", message.lower(), f"say that Docker is missing: {message}")
        self.assertFalse(message.startswith("[Errno"), f"write the message for the model, not the raw OSError: {message}")

    def test_2_stdout_and_stderr(self):
        """Step 2: stdout and stderr arrive in one text, in order."""
        text = call(self.bash, {"command": "echo first; echo second >&2; echo third"}, self.cwd)
        for word in ("first", "second", "third"):
            self.assertIn(word, text, f"{word!r} is missing; is stderr sent into stdout?")
        self.assertLess(text.index("first"), text.index("second"))
        self.assertLess(text.index("second"), text.index("third"))

    def test_4_exit_code(self):
        """Step 4: a non-zero exit code raises an exception with the output and the code."""
        error = error_of(self.bash, {"command": "echo broken; exit 3"}, self.cwd)
        self.assertIn("broken", str(error), f"include the output: {error}")
        self.assertIn("3", str(error), f"include the exit code: {error}")

    def test_4_success_is_not_an_error(self):
        """Step 4: exit code 0 returns the output, with no error."""
        self.assertIn("ok", call(self.bash, {"command": "echo ok; exit 0"}, self.cwd))

    def test_3_timeout(self):
        """Step 3: a command over its timeout is stopped soon after, as an error that says so."""
        started = time.monotonic()
        error = error_of(self.bash, {"command": "echo started; sleep 30", "timeout": 1}, self.cwd)
        seconds = time.monotonic() - started
        self.assertLess(seconds, 8, f"the tool returned after {seconds:.0f} s; stop the process at the timeout")
        self.assertRegex(str(error).lower(), "stop|time", f"say that the command was stopped: {error}")

    def test_3_no_timeout_given(self):
        """Step 3: without a timeout, a command runs to the end."""
        self.assertIn("done", call(self.bash, {"command": "sleep 1; echo done"}, self.cwd))
