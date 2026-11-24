# Exercise 03: the bash tool. Lets the agent run commands on your machine, in the working directory.
#
# Load it with the earlier tools, from the repository root:
#   python3 pi2.py --cwd playground -e exercises/01-read/read.py -e exercises/02-write/write.py \
#     -e exercises/03-bash/bash.py -e examples/permission_gate.py
# Then ask: "Run the tests and tell me what fails."
#
# LEARN:
# A command is a child process: output arrives on stdout and stderr, it ends with an exit code, and it
# may never end at all. The tool turns that into one result the model can read, and a non-zero exit
# code is an error result the model should react to.
#
# SAFETY:
# The model writes the commands, and they run as you: they can read and change your files and use your
# network, as Pi's own bash tool does. Work in the playground, keep examples/permission_gate.py loaded,
# and read each command the agent runs.

import os
import sys
import textwrap

from pi2 import ExtensionAPI, define_tool, windows

# A small Python process between pi2 and the command. It runs the command with bash in the workspace, in its
# own process group, and passes SIGTERM and ctrl+c on to all of it, so terminate() stops the command and
# everything it started.
RUNNER = textwrap.dedent("""
    import os, signal, subprocess, sys
    proc = subprocess.Popen(["bash", "-c", sys.argv[2]], cwd=sys.argv[1], start_new_session=True)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: os.killpg(proc.pid, signal.SIGTERM))
    sys.exit(proc.wait())
    """)


def command_args(command, workspace):
    """The command line that runs `command` with bash in `workspace`, through the runner."""
    if os.name == "nt":
        # Windows: terminate() ends one process and sends no signal; pi2/windows.py stops the rest.
        return windows.command_args(workspace, command)
    return [sys.executable, "-c", RUNNER, workspace, command]


def execute(params, ctx):
    # EXERCISE 1: Start the process: subprocess.Popen(command_args(params["command"], ctx.cwd),
    # stdout=subprocess.PIPE, text=True).
    #
    # EXERCISE 2: Collect output. Send stderr into stdout (stderr=subprocess.STDOUT) so both arrive in
    # one text, in order, the way a terminal shows them. proc.communicate(timeout=params.get("timeout"))
    # waits for the process and returns (output, None).
    #
    # EXERCISE 3: Stop runaway commands. Catch subprocess.TimeoutExpired, stop the process with
    # proc.terminate() and call communicate() again to wait for it. Say in the result that the command
    # was stopped. Do the same for KeyboardInterrupt (ctrl+c), then raise it again.
    # Use terminate() (SIGTERM), not kill() and not subprocess.run(timeout=...): the runner passes
    # SIGTERM on to the command and everything it started, but SIGKILL ends only the runner and leaves
    # them running. python3 exercises/check.py 03 checks that too.
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
        "Execute a bash command in the working directory. "
        "Returns stdout and stderr combined. Optionally provide a timeout in seconds."
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
