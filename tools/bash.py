# The bash tool: run a command in the working directory.

import subprocess

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    result = subprocess.run(
        ["bash", "-c", params["command"]],
        cwd=ctx.cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = result.stdout or "(no output)"
    if result.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {result.returncode}")
    return output


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
