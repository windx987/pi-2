# Checks for exercise 05, one or more per step of 05-command.md. Run: python3 exercises/check.py 05

import os
import shlex
import subprocess
import sys

from check import Workspace, call, error_of, load_tool


def python_command(*args):
    """Build a command line that works with the host shell on Unix and Windows."""
    parts = [sys.executable, *args]
    if os.name == "nt":
        return subprocess.list2cmdline(parts)
    return shlex.join(parts)


class CommandTest(Workspace):
    def setUp(self):
        super().setUp()
        self.command = load_tool("command")

    def test_1_runs_in_cwd(self):
        """Step 1: the command runs in ctx.cwd."""
        result = call(self.command, {"command": python_command("-c", "import os; print(os.getcwd())")}, self.cwd)
        self.assertEqual(result.strip(), str(self.cwd))

    def test_1_reads_workspace_file(self):
        """Step 1: the command sees files in ctx.cwd."""
        (self.cwd / "hello.txt").write_text("hi\n", encoding="utf-8")
        code = "print(open('hello.txt', encoding='utf-8').read(), end='')"
        self.assertEqual(call(self.command, {"command": python_command("-c", code)}, self.cwd), "hi\n")

    def test_2_stdout(self):
        """Step 2: stdout is returned."""
        self.assertEqual(call(self.command, {"command": python_command("-c", "print('hi', end='')")}, self.cwd), "hi")

    def test_2_stderr_combined(self):
        """Step 2: stderr is combined with stdout."""
        code = "import sys; print('err', file=sys.stderr)"
        self.assertEqual(call(self.command, {"command": python_command("-c", code)}, self.cwd), "err\n")

    def test_2_shell_features(self):
        """Step 2: the host shell supports pipes."""
        producer = python_command("-c", "print('a'); print('b')")
        consumer = python_command("-c", "import sys; print(sum(1 for _ in sys.stdin))")
        result = call(self.command, {"command": f"{producer} | {consumer}"}, self.cwd)
        self.assertEqual(result.strip(), "2")

    def test_2_quotes(self):
        """Step 2: quoted arguments are passed through."""
        self.assertEqual(
            call(self.command, {"command": python_command("-c", "print('hello world', end='')")}, self.cwd),
            "hello world",
        )

    def test_2_no_output(self):
        """Step 2: an empty result is reported clearly."""
        self.assertEqual(call(self.command, {"command": python_command("-c", "pass")}, self.cwd), "(no output)")

    def test_3_nonzero_raises(self):
        """Step 3: a non-zero exit raises with the output and the code."""
        code = "print('bad'); raise SystemExit(3)"
        error = error_of(self.command, {"command": python_command("-c", code)}, self.cwd)
        self.assertIn("bad", str(error))
        self.assertIn("3", str(error))

    def test_3_command_not_found(self):
        """Step 3: a missing command is an error, not a silent success."""
        error = error_of(self.command, {"command": "definitely-not-a-command"}, self.cwd)
        self.assertRegex(str(error), r"code [0-9]+")
