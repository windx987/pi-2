# Checks for exercise 05, one or more per step of 05-execute.md. Run: python3 exercises/check.py 05

from check import Workspace, call, error_of, load_tool


class BashTest(Workspace):
    def setUp(self):
        super().setUp()
        self.bash = load_tool("bash")

    def test_1_runs_in_cwd(self):
        """Step 1: the command runs in ctx.cwd."""
        result = call(self.bash, {"command": "pwd"}, self.cwd)
        self.assertEqual(result.strip(), str(self.cwd))

    def test_1_reads_workspace_file(self):
        """Step 1: the command sees files in ctx.cwd."""
        (self.cwd / "hello.txt").write_text("hi\n", encoding="utf-8")
        self.assertEqual(call(self.bash, {"command": "cat hello.txt"}, self.cwd), "hi\n")

    def test_2_stdout(self):
        """Step 2: stdout is returned."""
        self.assertEqual(call(self.bash, {"command": "printf hi"}, self.cwd), "hi")

    def test_2_stderr_combined(self):
        """Step 2: stderr is combined with stdout."""
        self.assertEqual(call(self.bash, {"command": "echo err >&2"}, self.cwd), "err\n")

    def test_2_shell_features(self):
        """Step 2: bash features such as pipes work."""
        result = call(self.bash, {"command": "printf 'a\\nb\\n' | wc -l"}, self.cwd)
        self.assertEqual(result.strip(), "2")

    def test_2_quotes(self):
        """Step 2: quoted arguments are passed through."""
        self.assertEqual(call(self.bash, {"command": "printf '%s' \"hello world\""}, self.cwd), "hello world")

    def test_2_no_output(self):
        """Step 2: an empty result is reported clearly."""
        self.assertEqual(call(self.bash, {"command": "true"}, self.cwd), "(no output)")

    def test_3_nonzero_raises(self):
        """Step 3: a non-zero exit raises with the output and the code."""
        error = error_of(self.bash, {"command": "echo bad; exit 3"}, self.cwd)
        self.assertIn("bad", str(error))
        self.assertIn("3", str(error))

    def test_3_command_not_found(self):
        """Step 3: a missing command is an error, not a silent success."""
        error = error_of(self.bash, {"command": "definitely-not-a-command"}, self.cwd)
        self.assertIn("127", str(error))
