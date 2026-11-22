# Exercise 01: the read tool. Lets the agent look at files in its working directory.
#
# Load it from the repository root:
#   python3 -m pi2 --cwd playground/01-read -e exercises/01-read/read.py
#
# Then ask: "Read todo.md and summarise it."
#
# LEARN:
# A tool is a name, a description, the JSON Schema of its arguments, and one execute() function.
# The model calls it with JSON; pi2 checks the arguments and sends the returned string back as the
# tool result. An exception becomes an error result the model can act on.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: resolve params["path"] against ctx.cwd. An absolute path replaces ctx.cwd.
    #
    # EXERCISE 2: read the file as UTF-8 text and split it into lines.
    #
    # EXERCISE 3: apply offset (first line, starting at 1) and limit (maximum lines, default 2000).
    #
    # EXERCISE 4: join the selected lines. If lines are left, add a note that says how to read on,
    # such as "[12 more lines. Use offset=113.]".
    raise NotImplementedError("read is not implemented yet.")


read_tool = define_tool(
    name="read",
    label="read",
    description="Read a text file. offset is the first line to read (starting at 1); limit is the maximum number of lines.",
    prompt_snippet="Read file contents",
    prompt_guidelines=["Use read to examine files instead of cat or sed."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "offset": {"type": "number", "description": "Line number to start reading from (1-indexed)"},
            "limit": {"type": "number", "description": "Maximum number of lines to read"},
        },
        "required": ["path"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(read_tool)
