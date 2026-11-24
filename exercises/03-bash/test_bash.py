# Checks for exercise 03, one or more per step of README.md. Run: python3 exercises/check.py 03
#
# The commands run with bash on this machine, in a temporary working directory, as they do in pi2
# (on Windows: in Git Bash).

import time

from check import Workspace, call, error_of, load_tool


class BashTest(Workspace):
    def setUp(self):
        super().setUp()
        self.bash = load_tool("bash")

    def test_1_runs_the_command(self):
        """Step 1: the command runs and its output comes back."""
        self.assertIn("hello", call(self.bash, {"command": "echo hello"}, self.cwd))

    def test_1_in_the_workspace(self):
        """Step 1: the command runs in ctx.cwd. Start it with command_args(params["command"], ctx.cwd)."""
        (self.cwd / "marker.txt").write_text("found me\n")
        text = call(self.bash, {"command": "cat marker.txt"}, self.cwd)
        self.assertIn("found me", text, f"the command did not run in ctx.cwd: {text.strip()[:200]}")

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

    def test_3_timeout_stops_everything(self):
        """Step 3: the timeout stops the command and what it started, with terminate()."""
        error = error_of(self.bash, {"command": "(sleep 3; touch late.txt) & wait", "timeout": 1}, self.cwd)
        self.assertRegex(str(error).lower(), "stop|time", f"say that the command was stopped: {error}")
        time.sleep(3)
        self.assertFalse((self.cwd / "late.txt").exists(), "a child of the command kept running after the "
                                                           "timeout: stop it with proc.terminate()")

    def test_3_no_timeout_given(self):
        """Step 3: without a timeout, a command runs to the end."""
        self.assertIn("done", call(self.bash, {"command": "sleep 1; echo done"}, self.cwd))
