# Exercise 02: the write tool. Lets the agent create files and replace them whole.
#
# Load it from the repository root:
#   python3 -m pi2 --cwd playground/02-write -e exercises/02-write/write.py
#
# Then ask: "Create plan.md with three bullets."
#
# LEARN:
# The schema checks types, but it cannot express policy. "Only inside the working directory" is a
# rule about the value, so execute() must check it. The error message is an instruction to the model.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: resolve params["path"] against ctx.cwd. Resolve the result so ".." and symlinks
    # cannot escape.
    #
    # EXERCISE 2: refuse a path outside ctx.cwd. Name the path the model sent in the error.
    #
    # EXERCISE 3: create the parent directories, then write params["content"] as UTF-8.
    #
    # EXERCISE 4: return a short confirmation. The model cannot see the file unless it reads it.
    raise NotImplementedError("write is not implemented yet.")


write_tool = define_tool(
    name="write",
    label="write",
    description="Write content to a file inside the working directory. Creates parent directories.",
    prompt_snippet="Create or overwrite files",
    prompt_guidelines=["Use write only for new files or complete rewrites."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "content": {"type": "string", "description": "Content to write to the file"},
        },
        "required": ["path", "content"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(write_tool)
