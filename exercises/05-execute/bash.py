# Exercise 05: the bash tool. Lets the agent run commands in its working directory.
#
# Load it with read and edit so the agent can inspect and fix what it runs:
#   python3 -m pi2 --cwd playground/05-execute \
#     -e exercises/01-read/read.py -e exercises/03-edit/edit.py -e exercises/05-execute/bash.py
#
# Then ask: "Run the tests and fix what fails."
#
# LEARN:
# The model cannot run anything by itself. A tool call is the only way. Return the output even when
# the command fails, and raise for a non-zero exit: the message is the error result the model reads.

import subprocess

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # EXERCISE 1: run params["command"] with bash -c, in ctx.cwd. Capture stdout and stderr together,
    # as text.
    #
    # EXERCISE 2: keep the output. If it is empty, use "(no output)".
    #
    # EXERCISE 3: when the return code is not zero, raise RuntimeError with the output and the code,
    # so the model sees what failed instead of a silent success.
    #
    # EXERCISE 4: return the output.
    raise NotImplementedError("bash is not implemented yet.")


bash_tool = define_tool(
    name="bash",
    label="bash",
    description="Execute a bash command in the working directory. Returns stdout and stderr combined.",
    prompt_snippet="Execute bash commands for tests, git and other shell work",
    prompt_guidelines=["Use bash for commands that need a shell; use lsdir, find_files and read to inspect files."],
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Bash command to execute"},
        },
        "required": ["command"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(bash_tool)
