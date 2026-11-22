# Checks for exercise 04, one or more per step of 04-search.md. Run: python3 exercises/check.py 04

from check import Workspace, call, error_of, load_tool


class GrepTest(Workspace):
    def setUp(self):
        super().setUp()
        self.grep = load_tool("grep")
        (self.cwd / "src/utils").mkdir(parents=True)
        (self.cwd / "src/app.py").write_text("first\n# TODO: fix\nlast\n", encoding="utf-8")
        (self.cwd / "src/utils/helpers.py").write_text("def helper():\n    return 1  # TODO: test\n", encoding="utf-8")
        (self.cwd / "docs").mkdir()
        (self.cwd / "docs/guide.md").write_text("TODO: write the guide\n", encoding="utf-8")
        (self.cwd / "legacy").mkdir()
        (self.cwd / "legacy/old.py").write_text("old\n", encoding="utf-8")
        (self.cwd / ".git").mkdir()
        (self.cwd / ".git/config").write_text("TODO: hidden\n", encoding="utf-8")
        (self.cwd / "assets").mkdir()
        (self.cwd / "assets/logo.bin").write_bytes(b"\x89PNG\x00TODO\xff")
        (self.cwd / "data").mkdir()
        (self.cwd / "data/users.json").write_text('{"note": "TODO"}\n', encoding="utf-8")

    def test_1_nested_matches(self):
        """Step 1: matches are found in nested files."""
        result = call(self.grep, {"pattern": "TODO"}, self.cwd)
        self.assertIn("src/app.py:2:# TODO: fix", result)
        self.assertIn("src/utils/helpers.py:2:", result)
        self.assertIn("docs/guide.md:1:", result)

    def test_1_relative_paths(self):
        """Step 1: result paths are relative to the search root."""
        result = call(self.grep, {"pattern": "TODO"}, self.cwd)
        self.assertNotIn(str(self.cwd), result)

    def test_2_include_filter(self):
        """Step 2: include keeps only matching file names."""
        result = call(self.grep, {"pattern": "TODO", "include": "*.py"}, self.cwd)
        self.assertIn("src/app.py", result)
        self.assertNotIn("docs/guide.md", result)
        self.assertNotIn("data/users.json", result)

    def test_2_path_filter(self):
        """Step 2: path limits the search root."""
        result = call(self.grep, {"pattern": "TODO", "path": "src"}, self.cwd)
        self.assertIn("app.py:2:", result)
        self.assertIn("utils/helpers.py:2:", result)
        self.assertNotIn("src/app.py", result)

    def test_2_git_skipped(self):
        """Step 2: .git is skipped."""
        result = call(self.grep, {"pattern": "TODO"}, self.cwd)
        self.assertNotIn(".git", result)

    def test_3_binary_skipped(self):
        """Step 3: binary files are skipped instead of crashing."""
        result = call(self.grep, {"pattern": "TODO"}, self.cwd)
        self.assertNotIn("logo.bin", result)

    def test_4_line_numbers(self):
        """Step 4: each match has its file, line number and text."""
        result = call(self.grep, {"pattern": "fix"}, self.cwd)
        self.assertIn("src/app.py:2:# TODO: fix", result)

    def test_4_no_matches(self):
        """Step 4: no matches returns a clear message."""
        self.assertEqual(call(self.grep, {"pattern": "NO_SUCH_TEXT"}, self.cwd), "(no matches)")

    def test_4_cap(self):
        """Step 4: output stops after 200 matches."""
        (self.cwd / "many").mkdir()
        (self.cwd / "many/lines.txt").write_text("\n".join("TODO" for _ in range(250)) + "\n", encoding="utf-8")
        result = call(self.grep, {"pattern": "TODO", "path": "many"}, self.cwd)
        self.assertEqual(len(result.splitlines()), 201)
        self.assertIn("[stopped after 200 matches]", result)

    def test_invalid_regex(self):
        """An invalid regular expression is an error."""
        error_of(self.grep, {"pattern": "["}, self.cwd)

    def test_empty_pattern(self):
        """An empty pattern is an error."""
        error_of(self.grep, {"pattern": ""}, self.cwd)

    def test_missing_path(self):
        """A missing path is an error."""
        error_of(self.grep, {"pattern": "TODO", "path": "nope"}, self.cwd)

    def test_not_a_directory(self):
        """A file path is an error: the search root must be a directory."""
        error_of(self.grep, {"pattern": "TODO", "path": "src/app.py"}, self.cwd)
