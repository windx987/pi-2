# Checks for exercise 02, one or more per step of README.md. Run: python3 exercises/check.py 02

from pathlib import Path

from check import Workspace, call, error_of, load_tool


class WriteTest(Workspace):
    def setUp(self):
        super().setUp()
        self.write = load_tool("write")

    def test_1_relative_path(self):
        """Step 1: a relative path is written under ctx.cwd, not where pi2 started."""
        call(self.write, {"path": "hello.txt", "content": "hi\n"}, self.cwd)
        self.assertEqual((self.cwd / "hello.txt").read_text(encoding="utf-8"), "hi\n")

    def test_2_parent_directory(self):
        """Step 2: ../ outside ctx.cwd is refused with an exception, and nothing is written."""
        outside = self.cwd.parent / f"{self.cwd.name}-escaped.txt"
        self.addCleanup(outside.unlink, missing_ok=True)
        error = error_of(self.write, {"path": f"../{outside.name}", "content": "x"}, self.cwd)
        self.assertFalse(outside.exists(), "the file was written outside the working directory")
        self.assertTrue(str(error), "say why the path was refused")

    def test_2_absolute_path_outside(self):
        """Step 2: an absolute path outside ctx.cwd is refused."""
        outside = Path(self.cwd.parent / f"{self.cwd.name}-outside.txt")
        self.addCleanup(outside.unlink, missing_ok=True)
        error_of(self.write, {"path": str(outside), "content": "x"}, self.cwd)
        self.assertFalse(outside.exists(), "the file was written outside the working directory")

    def test_2_inside_is_allowed(self):
        """Step 2: a path that stays inside, such as docs/../ok.txt or an absolute one, is written."""
        call(self.write, {"path": "docs/../ok.txt", "content": "ok"}, self.cwd)
        call(self.write, {"path": str(self.cwd / "abs.txt"), "content": "ok"}, self.cwd)
        self.assertTrue((self.cwd / "ok.txt").exists())
        self.assertTrue((self.cwd / "abs.txt").exists())

    def test_3_parent_directories(self):
        """Step 3: missing parent directories are created."""
        call(self.write, {"path": "notes/2026/todo.md", "content": "- one\n"}, self.cwd)
        self.assertEqual((self.cwd / "notes/2026/todo.md").read_text(encoding="utf-8"), "- one\n")

    def test_3_utf8(self):
        """Step 3: the content is written as UTF-8, exactly."""
        call(self.write, {"path": "thai.txt", "content": "สวัสดี ✓\n"}, self.cwd)
        self.assertEqual((self.cwd / "thai.txt").read_bytes(), "สวัสดี ✓\n".encode("utf-8"))

    def test_3_replaces_whole_file(self):
        """Step 3: an existing file is replaced, not appended to."""
        (self.cwd / "old.txt").write_text("a long old text\n", encoding="utf-8")
        call(self.write, {"path": "old.txt", "content": "new\n"}, self.cwd)
        self.assertEqual((self.cwd / "old.txt").read_text(encoding="utf-8"), "new\n")

    def test_4_confirmation(self):
        """Step 4: the result confirms what was written and names the file."""
        result = call(self.write, {"path": "notes/todo.md", "content": "- one\n"}, self.cwd)
        self.assertIn("todo.md", result, f"the confirmation should name the file: {result!r}")
