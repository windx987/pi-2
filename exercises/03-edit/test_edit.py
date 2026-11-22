# Checks for exercise 03, one or more per step of 03-edit.md. Run: python3 exercises/check.py 03

from check import Workspace, call, error_of, load_tool


class EditTest(Workspace):
    def setUp(self):
        super().setUp()
        self.edit = load_tool("edit")
        self.file = self.cwd / "math.py"
        self.file.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    def test_1_relative_path(self):
        """Step 1: the file is found from ctx.cwd and changed."""
        call(self.edit, {"path": "math.py", "oldText": "a - b", "newText": "a + b"}, self.cwd)
        self.assertIn("return a + b", self.file.read_text(encoding="utf-8"))

    def test_1_missing_file(self):
        """Step 1: a missing file is an error."""
        error_of(self.edit, {"path": "missing.py", "oldText": "x", "newText": "y"}, self.cwd)

    def test_1_outside_cwd(self):
        """Step 1: a path outside ctx.cwd is refused."""
        target = self.cwd.parent / "outside.py"
        target.write_text("x\n", encoding="utf-8")
        error_of(self.edit, {"path": str(target), "oldText": "x", "newText": "y"}, self.cwd)
        self.assertEqual(target.read_text(encoding="utf-8"), "x\n")

    def test_2_empty_old_text(self):
        """Step 2: an empty oldText is an error."""
        error_of(self.edit, {"path": "math.py", "oldText": "", "newText": "x"}, self.cwd)

    def test_3_old_text_missing(self):
        """Step 3: an oldText that is not in the file is an error, and the file is unchanged."""
        error_of(self.edit, {"path": "math.py", "oldText": "def sub", "newText": "def minus"}, self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "def add(a, b):\n    return a - b\n")

    def test_3_old_text_twice(self):
        """Step 3: an oldText that occurs twice is ambiguous, and the file is unchanged."""
        self.file.write_text("x = 1\nx = 1\n", encoding="utf-8")
        error_of(self.edit, {"path": "math.py", "oldText": "x = 1", "newText": "x = 2"}, self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "x = 1\nx = 1\n")

    def test_4_replaces_once(self):
        """Step 4: exactly one replacement is applied."""
        self.file.write_text("add(1, 2)\nadd(3, 4)\n", encoding="utf-8")
        call(self.edit, {"path": "math.py", "oldText": "add(1, 2)", "newText": "sum(1, 2)"}, self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "sum(1, 2)\nadd(3, 4)\n")

    def test_4_delete(self):
        """Step 4: an empty newText deletes the old text."""
        self.file.write_text("keep\nremove me\n", encoding="utf-8")
        call(self.edit, {"path": "math.py", "oldText": "remove me\n", "newText": ""}, self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "keep\n")

    def test_4_utf8(self):
        """Step 4: the new content is written as UTF-8."""
        call(self.edit, {"path": "math.py", "oldText": "a - b", "newText": "a + b  # ✓"}, self.cwd)
        self.assertIn("a + b  # ✓", self.file.read_text(encoding="utf-8"))

    def test_4_confirmation(self):
        """Step 4: the result confirms the edit."""
        result = call(self.edit, {"path": "math.py", "oldText": "a - b", "newText": "a + b"}, self.cwd)
        self.assertIn("math.py", result)
