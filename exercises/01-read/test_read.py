# Checks for exercise 01, one or more per step of README.md. Run: python3 exercises/check.py 01

import re

from check import Workspace, call, error_of, load_tool

LINES = "one\ntwo\nthree\nfour\nfive\n"


class ReadTest(Workspace):
    def setUp(self):
        super().setUp()
        self.read = load_tool("read")
        (self.cwd / "notes.txt").write_text(LINES, encoding="utf-8")

    def test_1_relative_path(self):
        """Step 1: a relative path is read from ctx.cwd, not from where pi2 started."""
        (self.cwd / "src").mkdir()
        (self.cwd / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
        self.assertIn("print('hi')", call(self.read, {"path": "src/app.py"}, self.cwd))

    def test_1_absolute_path(self):
        """Step 1: an absolute path is read as it is."""
        self.assertIn("three", call(self.read, {"path": str(self.cwd / "notes.txt")}, self.cwd))

    def test_2_whole_file(self):
        """Step 2: without offset and limit, the whole file comes back unchanged."""
        self.assertEqual(call(self.read, {"path": "notes.txt"}, self.cwd).rstrip("\n"), LINES.rstrip("\n"))

    def test_2_utf8(self):
        """Step 2: the file is read as UTF-8."""
        (self.cwd / "thai.txt").write_bytes("สวัสดี ✓ café\n".encode("utf-8"))
        self.assertIn("สวัสดี ✓ café", call(self.read, {"path": "thai.txt"}, self.cwd))

    def test_3_offset_and_limit(self):
        """Step 3: offset=2, limit=2 returns lines 2 and 3 only."""
        text = call(self.read, {"path": "notes.txt", "offset": 2, "limit": 2}, self.cwd)
        self.assertIn("two\nthree", text)
        for line in ("one", "four", "five"):
            self.assertNotIn(line, text, f"line {line!r} is outside offset=2, limit=2:\n{text}")

    def test_3_note_to_read_on(self):
        """Step 3: when lines remain, the text ends with a note naming the offset to continue at (4)."""
        text = call(self.read, {"path": "notes.txt", "offset": 2, "limit": 2}, self.cwd)
        note = text.split("three", 1)[-1]
        self.assertRegex(note, re.compile(r"offset\W{0,3}4\b", re.IGNORECASE), f"no note such as 'Use offset=4 to continue':\n{text}")

    def test_3_no_note_at_the_end(self):
        """Step 3: no note when the limit reaches the end of the file."""
        text = call(self.read, {"path": "notes.txt", "offset": 4, "limit": 10}, self.cwd)
        self.assertIn("four\nfive", text)
        self.assertNotIn("offset", text.lower(), f"nothing is left to read, so no note:\n{text}")

    def test_3_offset_alone(self):
        """Step 3: offset without limit reads to the end; numbers may arrive as 4.0."""
        text = call(self.read, {"path": "notes.txt", "offset": 4.0}, self.cwd)
        self.assertIn("four\nfive", text)
        self.assertNotIn("three", text)

    def test_4_missing_file(self):
        """Step 4: a missing file raises an exception that names the path."""
        error = error_of(self.read, {"path": "nope.txt"}, self.cwd)
        self.assertIn("nope.txt", str(error), f"the message should name the file: {error}")

    def test_4_offset_past_the_end(self):
        """Step 4: an offset past the end of the file raises an exception."""
        error_of(self.read, {"path": "notes.txt", "offset": 50}, self.cwd)
