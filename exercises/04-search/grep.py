# Exercise 04: the grep tool. Search file contents, not just file names.
#
# Load it with the existing find tool to compare the two:
#   python3 -m pi2 --cwd playground/04-search \
#     -e exercises/04-search/grep.py -e tools/find.py
#
# Then ask: "Search for TODO in the project."
#
# LEARN:
# find_files answers "which files are named like this?" from the directory tree alone. grep answers
# "where does this text appear?" and must open every candidate file. That is slower, can hit binary
# files, and can produce a lot of output, so the tool needs filters and a cap.

import fnmatch
import re
from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: resolve params["path"] against ctx.cwd (default "."). It must exist and be a
    # directory. Compile params["pattern"] with re.compile; turn re.error into ValueError.
    #
    # EXERCISE 2: walk the tree with root.rglob("*"). Keep files only. Skip anything under .git.
    # Keep only files whose name matches params["include"] (default "*") with fnmatch.
    #
    # EXERCISE 3: read each file as UTF-8. Skip files that raise UnicodeDecodeError or OSError:
    # those are binary or unreadable.
    #
    # EXERCISE 4: search every line with the regex. Add "relative/path:line:text" to the result.
    # Stop after 200 matches and add "[stopped after 200 matches]". Return "(no matches)" if none.
    raise NotImplementedError("grep is not implemented yet.")


grep_tool = define_tool(
    name="grep",
    label="grep",
    description=(
        "Search file contents recursively with a regular expression. Returns path:line:text for each "
        "matching line. Skips binary files and .git."
    ),
    prompt_snippet="Search file contents with a regular expression",
    prompt_guidelines=["Use grep to find where text or symbols appear; use find_files to locate files by name."],
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regular expression to search for"},
            "path": {
                "type": "string",
                "description": "Directory to search, relative to the working directory or absolute; defaults to the working directory",
            },
            "include": {
                "type": "string",
                "description": "Only search files whose name matches this glob, such as '*.py'; defaults to all files",
            },
        },
        "required": ["pattern"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(grep_tool)
