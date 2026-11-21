# Exercise 03: the bash tool. Lets the agent run commands, inside a Docker container.
#
# Needs Docker running and the image pulled once:  docker pull node:22-bookworm-slim
# No Docker? Start pi2 with PI2_NO_DOCKER=1 to run the commands on this machine instead (see command_args).
# Load it with the earlier tools, from a playground copy under your home directory:
#   "$REPO/pi2.sh" -e .../01-read/read.py -e .../02-write/write.py -e .../03-bash/bash.py
# Then ask: "Run the tests and tell me what fails."
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
# README.md next to this file.

import os
import sys
import textwrap

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


# Without Docker: a small Python process in the place of `docker run --init`. It runs the command with bash in
# the workspace, in its own process group, and passes SIGTERM and ctrl+c on to all of it, so terminate() stops
# the command and everything it started, as with the container.
LOCAL_RUNNER = textwrap.dedent("""
    import os, signal, subprocess, sys
    proc = subprocess.Popen(["bash", "-c", sys.argv[2]], cwd=sys.argv[1], start_new_session=True)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: os.killpg(proc.pid, signal.SIGTERM))
    sys.exit(proc.wait())
    """)


def no_docker():
    return os.environ.get("PI2_NO_DOCKER") == "1"


def command_args(command, workspace):
    """The command line that runs `command`: docker run ..., or with PI2_NO_DOCKER=1 bash on this machine."""
    if no_docker():
        # SAFETY: no container. The command sees your files, your network and your user's rights.
        return [sys.executable, "-c", LOCAL_RUNNER, workspace, command]
    return ["docker", *docker_args(command, workspace)]


def execute(params, ctx):
    # EXERCISE 1: Start the process: subprocess.Popen(command_args(params["command"], ctx.cwd),
    # stdout=subprocess.PIPE, text=True). It raises FileNotFoundError when Docker is not installed;
    # raise an exception that says so.
    #
    # EXERCISE 2: Collect output. Send stderr into stdout (stderr=subprocess.STDOUT) so both arrive in
    # one text, in order, the way a terminal shows them. proc.communicate(timeout=params.get("timeout"))
    # waits for the process and returns (output, None).
    #
    # EXERCISE 3: Stop runaway commands. Catch subprocess.TimeoutExpired, stop the process with
    # proc.terminate() and call communicate() again to wait for it. Say in the result that the command
    # was stopped. Do the same for KeyboardInterrupt (ctrl+c), then raise it again.
    # Use terminate() (SIGTERM), not kill() and not subprocess.run(timeout=...): docker run passes
    # SIGTERM on to the container, but SIGKILL ends only the docker client and leaves the container
    # running. With Docker running, python3 exercises/check.py 03 checks that too.
    #
    # EXERCISE 4: Return the output; when proc.returncode is not 0, raise an exception with the output
    # and "Command exited with code N", so the model gets an error result.
    #
    # CHALLENGE: Long output. Keep the last 2000 lines for the model and say how much was left out.
    raise NotImplementedError(f"bash is not implemented yet (asked to run {params['command']} in {ctx.cwd}).")


bash_tool = define_tool(
    name="bash",
    label="bash",
    description=(
        "Execute a bash command in the working directory"
        + ("" if no_docker() else ", inside a container without network")
        + ". Returns stdout and stderr combined. Optionally provide a timeout in seconds."
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
