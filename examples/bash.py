# A solution to exercise 03: the bash tool, each command in a new Docker container.
#
# Needs Docker running and the image pulled once:  docker pull node:22-bookworm-slim
# Load it with the other examples, from a playground copy under your home directory:
#   "$REPO/pi2.sh" -e "$REPO/examples/read.py" -e "$REPO/examples/write.py" -e "$REPO/examples/bash.py"
# Then ask: "Run the tests and tell me what fails."
#
# It is not a proven sandbox: see "Isolation checks" in exercises/03-bash/README.md.

import os
import subprocess

from pi2 import ExtensionAPI, define_tool

# Image the commands run in. It must have bash.
WORKSHOP_IMAGE = "node:22-bookworm-slim"


def docker_args(command, workspace):
    """Arguments for `docker` that run `command` in a disposable container with only `workspace` mounted."""
    # Run as the host user, so files the command creates in the workspace stay editable on the host.
    user = ["--user", f"{os.getuid()}:{os.getgid()}"] if hasattr(os, "getuid") else []
    return [
        "run", "--rm",
        # An init process forwards the stop signal to the command, so SIGTERM to `docker run` stops it.
        "--init",
        "--network", "none",
        "--memory", "1g",
        "--pids-limit", "256",
        *user,
        "--env", "HOME=/tmp",
        "--volume", f"{workspace}:/workspace",
        "--workdir", "/workspace",
        WORKSHOP_IMAGE,
        "bash", "-c", command,
    ]


def execute(params, ctx):
    try:
        proc = subprocess.Popen(
            ["docker", *docker_args(params["command"], ctx.cwd)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("Docker is not installed or not on PATH.") from None
    try:
        output, _ = proc.communicate(timeout=params.get("timeout"))
    except subprocess.TimeoutExpired:
        # SIGTERM, not kill(): docker run passes SIGTERM on to the container, SIGKILL leaves it running.
        proc.terminate()
        output, _ = proc.communicate()
        raise RuntimeError(f"{output}\nCommand stopped after {params['timeout']} seconds.") from None
    except KeyboardInterrupt:
        # ctrl+c in pi2: stop the container too, then let pi2 handle the interrupt.
        proc.terminate()
        proc.communicate()
        raise
    if proc.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {proc.returncode}.")
    return output or "(no output)"


bash_tool = define_tool(
    name="bash",
    label="bash",
    description=(
        "Execute a bash command in the working directory, inside a container without network. Returns "
        "stdout and stderr combined. Optionally provide a timeout in seconds."
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
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(bash_tool)
