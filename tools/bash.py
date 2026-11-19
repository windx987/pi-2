# The bash tool: run a command on the host, in the working directory.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/bash.py

import subprocess

from pi2 import ExtensionAPI, define_tool


def execute_bash(params, ctx):
    """Run the command on the host, in the working directory."""
    # Commands run as your user, on your machine. There is no sandbox here: the model can do
    # anything you can. Work in a copy of the playground, not in the repository.
    try:
        result = subprocess.run(
            ["bash", "-c", params["command"]],
            cwd=ctx.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=params.get("timeout"),
        )
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        message = "Command stopped after the timeout."
        raise RuntimeError(f"{output}\n{message}" if output else message) from error

    output = result.stdout or "(no output)"
    if result.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {result.returncode}")
    return output


bash_tool = define_tool(
    name="bash",
    label="bash",
    description=(
        "Execute a bash command in the working directory. Returns stdout and stderr combined. "
        "Optionally provide a timeout in seconds."
    ),
    prompt_snippet="Execute bash commands (ls, grep, find, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Bash command to execute"},
            "timeout": {"type": "number", "description": "Timeout in seconds (optional, no default timeout)"},
        },
        "required": ["command"],
    },
    execute=execute_bash,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(bash_tool)
