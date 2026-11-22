# Checks for exercise 02, one or more per step of 02-write.md. Run: python3 exercises/check.py 02

from check import Workspace, call, error_of, load_tool


class WriteTest(Workspace):
    def setUp(self):
        super().setUp()
        self.write = load_tool("write")

    def test_1_relative_path(self):
        """Step 1: the path is resolved against ctx.cwd."""
        call(self.write, {"path": "todo.md", "content": "hello"}, self.cwd)
        self.assertEqual((self.cwd / "todo.md").read_text(encoding="utf-8"), "hello")

    def test_3_creates_parents(self):
        """Step 3: missing parent directories are created."""
        call(self.write, {"path": "a/b/c/file.txt", "content": "deep"}, self.cwd)
        self.assertTrue((self.cwd / "a/b/c/file.txt").is_file())

    def test_3_overwrites(self):
        """Step 3: an existing file is replaced whole."""
        target = self.cwd / "draft.md"
        target.write_text("old", encoding="utf-8")
        call(self.write, {"path": "draft.md", "content": "new"}, self.cwd)
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_3_utf8(self):
        """Step 3: the content is written as UTF-8."""
        call(self.write, {"path": "unicode.txt", "content": "café 東京 🚀"}, self.cwd)
        self.assertEqual((self.cwd / "unicode.txt").read_text(encoding="utf-8"), "café 東京 🚀")

    def test_2_outside_cwd(self):
        """Step 2: a relative path that escapes ctx.cwd is refused."""
        error_of(self.write, {"path": "../outside.txt", "content": "no"}, self.cwd)
        self.assertFalse((self.cwd.parent / "outside.txt").exists())

    def test_2_absolute_outside_cwd(self):
        """Step 2: an absolute path outside ctx.cwd is refused."""
        target = self.cwd.parent / "outside-absolute.txt"
        error_of(self.write, {"path": str(target), "content": "no"}, self.cwd)
        self.assertFalse(target.exists())

    def test_2_directory_target(self):
        """Step 2: writing to a directory is an error."""
        (self.cwd / "sub").mkdir()
        error_of(self.write, {"path": "sub", "content": "no"}, self.cwd)

    def test_4_confirmation(self):
        """Step 4: the result confirms what was written."""
        result = call(self.write, {"path": "plan.md", "content": "- one\n"}, self.cwd)
        self.assertIn("plan.md", result)
