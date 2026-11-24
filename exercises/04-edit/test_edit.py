# Checks for exercise 04, one or more per step of README.md. Run: python3 exercises/check.py 04

import re

from check import Workspace, call, error_of, load_tool

CALC = "def add(a, b):\n    return a + b\n\n\nprint(add(1, 2))\n"


class EditTest(Workspace):
    def setUp(self):
        super().setUp()
        self.edit = load_tool("edit")
        self.file = self.cwd / "calc.py"
        self.file.write_text(CALC, encoding="utf-8")

    def edits(self, *pairs, path="calc.py"):
        return {"path": path, "edits": [{"oldText": old, "newText": new} for old, new in pairs]}

    def assert_unchanged(self):
        self.assertEqual(self.file.read_text(encoding="utf-8"), CALC, "a failed edit must leave the file as it was")

    def test_1_relative_path(self):
        """Step 1: the file is found from ctx.cwd and changed."""
        call(self.edit, self.edits(("return a + b", "return a + b + 0")), self.cwd)
        self.assertIn("return a + b + 0", self.file.read_text(encoding="utf-8"))

    def test_1_missing_file(self):
        """Step 1: a missing file raises an exception."""
        error_of(self.edit, self.edits(("x", "y"), path="nope.py"), self.cwd)

    def test_2_not_found(self):
        """Step 2: an oldText that is not in the file raises, and the file stays as it was."""
        error = error_of(self.edit, self.edits(("def sub", "def minus")), self.cwd)
        self.assert_unchanged()
        self.assertTrue(str(error), "say which edit failed and why")

    def test_2_more_than_once(self):
        """Step 2: an oldText that occurs twice raises: the edit is ambiguous."""
        error_of(self.edit, self.edits(("add", "sum")), self.cwd)  # in the definition and in the call
        self.assert_unchanged()

    def test_2_names_the_failing_edit(self):
        """Step 2: the message names the edit that failed, such as edits[1]."""
        error = error_of(self.edit, self.edits(("return a + b", "return b + a"), ("missing", "x")), self.cwd)
        self.assertRegex(str(error), re.compile(r"edits?\W{0,2}1\b|edit\W{0,2}#?2\b|second", re.IGNORECASE),
                         f"say that edits[1] failed: {error}")
        self.assert_unchanged()

    def test_2_matches_the_original(self):
        """Step 2: each oldText is matched in the original file, not after the previous edit."""
        self.file.write_text("x = 1\ny = 2\n", encoding="utf-8")
        call(self.edit, self.edits(("1", "2"), ("2", "3")), self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "x = 2\ny = 3\n")

    def test_3_several_edits(self):
        """Step 3: several disjoint edits are all applied, in one call."""
        call(self.edit, self.edits(("def add", "def plus"), ("add(1, 2)", "plus(1, 2)")), self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), CALC.replace("add", "plus"))

    def test_3_edits_in_any_order(self):
        """Step 3: edits listed from the end of the file to the start work as well."""
        call(self.edit, self.edits(("add(1, 2)", "plus(1, 2)"), ("def add", "def plus")), self.cwd)
        self.assertEqual(self.file.read_text(encoding="utf-8"), CALC.replace("add", "plus"))

    def test_3_overlap(self):
        """Step 3: overlapping edits raise, and the file stays as it was."""
        error_of(self.edit, self.edits(("def add(a, b)", "def add(x, y)"), ("add(a, b):", "add(a, b, c):")), self.cwd)
        self.assert_unchanged()

    def test_4_written_and_confirmed(self):
        """Step 4: the new content is written as UTF-8 and the result confirms it."""
        result = call(self.edit, self.edits(("return a + b", "return a + b  # ✓ ผลรวม")), self.cwd)
        self.assertIn("# ✓ ผลรวม", self.file.read_text(encoding="utf-8"))
        self.assertTrue(result.strip(), "return a confirmation, so the model knows the edit worked")
