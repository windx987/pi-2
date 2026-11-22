# The command tool: run a command in the working directory using the host shell.

import subprocess

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    result = subprocess.run(
        params["command"],
        shell=True,
        cwd=ctx.cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = result.stdout or "(no output)"
    if result.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {result.returncode}")
    return output


command_tool = define_tool(
    name="command",
    label="command",
    description="Run a command in the working directory using the host operating system's shell. Returns stdout and stderr combined.",
    prompt_snippet="Run commands for tests, git and other shell work",
    prompt_guidelines=["Use command for shell work; use lsdir, find_files and read to inspect files."],
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run in the host operating system's shell"},
        },
        "required": ["command"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(command_tool)
