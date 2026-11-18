# Exercise 04: the bash tool. Lets the agent run commands, inside a Docker container.
#
# Needs Docker running and the image pulled once:  docker pull node:22-bookworm-slim
# Load it with the earlier tools, from a playground copy under your home directory:
#   "$REPO/pi2.sh" -e .../01-read/starter.py -e .../02-write/starter.py -e .../03-edit/starter.py \
#     -e .../04-bash/starter.py
# Then ask: "Run the tests and fix what fails."
#
# LEARN:
# A command is a child process: output arrives on stdout and stderr, it ends with an exit code, and it
# may never end at all. The tool turns that into one result the model can read, and a non-zero exit
# code is an error result the model should react to.
#
# SAFETY:
# The model writes the commands. They run in a throwaway container (--rm) meant to see only the
# working directory, mounted at /workspace, with no network. docker_args() below builds that command
# line; change the isolation only on purpose. It is not a proven sandbox: see "Isolation checks" in
# education/exercises/04-bash/README.md.

import os

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
    # EXERCISE 1: Start the process: subprocess.Popen(["docker", *docker_args(params["command"], ctx.cwd)],
    # stdout=subprocess.PIPE, text=True). It raises FileNotFoundError when Docker is not installed;
    # raise an exception that says so.
    #
    # EXERCISE 2: Collect output. Send stderr into stdout (stderr=subprocess.STDOUT) so both arrive in
    # one text, in order, the way a terminal shows them. proc.communicate() waits for the process and
    # returns (output, None).
    #
    # EXERCISE 3: Return the output; when proc.returncode is not 0, raise an exception with the output
    # and "Command exited with code N", so the model gets an error result.
    #
    # EXERCISE 4: Stop runaway commands. Pass timeout=params.get("timeout") to communicate() and catch
    # subprocess.TimeoutExpired. Then stop the process with proc.terminate() and call communicate()
    # again to wait for it. Say in the result that the command was stopped.
    # Use terminate() (SIGTERM), not kill() and not subprocess.run(timeout=...): docker run passes
    # SIGTERM on to the container, but SIGKILL ends only the docker client and leaves the container
    # running. Check your tool with:  python3 python/exercises/04-bash/check_timeout.py
    #
    # CHALLENGE: Long output. Keep the last 2000 lines for the model and say how much was left out.
    raise NotImplementedError(f"bash is not implemented yet (asked to run {params['command']} in {ctx.cwd}).")


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
