# Checks for exercise 01, one or more per step of 01-read.md. Run: python3 exercises/check.py 01

from check import Workspace, call, error_of, load_tool


class ReadTest(Workspace):
    def setUp(self):
        super().setUp()
        self.read = load_tool("read")

    def test_1_relative_path(self):
        """Step 1: a relative path is resolved against ctx.cwd."""
        (self.cwd / "notes.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
        result = call(self.read, {"path": "notes.txt"}, self.cwd)
        self.assertEqual(result, "one\ntwo\nthree")

    def test_1_absolute_path(self):
        """Step 1: an absolute path replaces ctx.cwd."""
        target = self.cwd / "absolute.txt"
        target.write_text("absolute content", encoding="utf-8")
        self.assertEqual(call(self.read, {"path": str(target)}, self.cwd), "absolute content")

    def test_2_utf8(self):
        """Step 2: the file is read as UTF-8."""
        (self.cwd / "unicode.txt").write_text("café 東京 🚀", encoding="utf-8")
        self.assertEqual(call(self.read, {"path": "unicode.txt"}, self.cwd), "café 東京 🚀")

    def test_3_offset_and_limit(self):
        """Step 3: offset starts at 1 and limit caps the number of lines."""
        (self.cwd / "lines.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
        result = call(self.read, {"path": "lines.txt", "offset": 2, "limit": 2}, self.cwd)
        self.assertEqual(result, "two\nthree")

    def test_3_default_limit(self):
        """Step 3: without limit, read up to 2000 lines and say how to continue."""
        lines = [f"line {number}" for number in range(1, 2006)]
        (self.cwd / "long.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = call(self.read, {"path": "long.txt"}, self.cwd)
        self.assertIn("line 2000", result)
        self.assertNotIn("line 2001", result)
        self.assertIn("5 more lines", result)
        self.assertIn("offset=2001", result)

    def test_3_offset_past_end(self):
        """Step 3: an offset past the end is an error."""
        (self.cwd / "short.txt").write_text("one\ntwo\n", encoding="utf-8")
        error_of(self.read, {"path": "short.txt", "offset": 10}, self.cwd)

    def test_3_empty_file(self):
        """Step 3: an empty file returns an empty string."""
        (self.cwd / "empty.txt").write_text("", encoding="utf-8")
        self.assertEqual(call(self.read, {"path": "empty.txt"}, self.cwd), "")

    def test_4_continuation_note(self):
        """Step 4: lines left over produce a note with the next offset."""
        (self.cwd / "lines.txt").write_text("one\ntwo\nthree\nfour\nfive\n", encoding="utf-8")
        result = call(self.read, {"path": "lines.txt", "offset": 2, "limit": 2}, self.cwd)
        self.assertIn("2 more lines", result)
        self.assertIn("offset=4", result)

    def test_4_no_note_at_end(self):
        """Step 4: no note when the read reaches the end of the file."""
        (self.cwd / "lines.txt").write_text("one\ntwo\n", encoding="utf-8")
        result = call(self.read, {"path": "lines.txt"}, self.cwd)
        self.assertNotIn("more lines", result)

    def test_missing_file(self):
        """A missing file is an error the model can read."""
        error_of(self.read, {"path": "missing.txt"}, self.cwd)
