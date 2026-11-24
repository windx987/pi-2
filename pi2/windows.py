"""Windows support for the bash tool of exercise 03.

On macOS and Linux, proc.terminate() sends SIGTERM, and the runner in bash.py passes it on to the
command's process group. Windows has no such signal: terminate() ends one process at once, and the
commands Git Bash started would keep running.

So on Windows the command runs under a small runner, and a watchdog process waits for that runner to end.
If the command was still running then (a timeout, ctrl+c), the watchdog stops its process tree with
`taskkill /T`. Your execute() stays the same.
"""

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# Started by the runner, in its own hidden console, so ctrl+c and terminate() do not reach it.
WATCHDOG = textwrap.dedent("""
    import ctypes, subprocess, sys
    kernel32 = ctypes.WinDLL("kernel32")
    SYNCHRONIZE, INFINITE = 0x00100000, 0xFFFFFFFF
    runner = kernel32.OpenProcess(SYNCHRONIZE, False, int(sys.argv[1]))
    child = kernel32.OpenProcess(SYNCHRONIZE, False, int(sys.argv[2]))  # the open handle keeps its pid from reuse
    if runner:
        kernel32.WaitForSingleObject(runner, INFINITE)
    if child and kernel32.WaitForSingleObject(child, 0) != 0:  # the command still runs: the runner was stopped
        subprocess.run(["taskkill", "/F", "/T", "/PID", sys.argv[2]],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    """)

# Runs the command with the runner's stdout, starts the watchdog, and exits with the command's exit code.
RUNNER = textwrap.dedent("""
    import json, os, subprocess, sys
    job = json.loads(sys.argv[1])
    child = subprocess.Popen(job["argv"], cwd=job["cwd"])
    subprocess.Popen(
        [sys.executable, "-c", job["watchdog"], str(os.getpid()), str(child.pid)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    try:
        sys.exit(child.wait())
    except KeyboardInterrupt:
        sys.exit(130)
    """)


def git_bash():
    """Git for Windows' bash.exe. Not C:\\Windows\\System32\\bash.exe: that one runs WSL's Linux."""
    candidates = []
    git = shutil.which("git")
    if git:
        candidates.append(Path(git).resolve().parent.parent / "bin" / "bash.exe")  # Git\\cmd\\git.exe -> Git\\bin
    candidates.append(Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe")
    for path in candidates:
        if path.is_file():
            return str(path)
    raise RuntimeError("Git Bash is not installed. Install Git for Windows: winget install Git.Git")


def command_args(workspace, command):
    """The runner's command line, which runs `command` with Git Bash in `workspace`."""
    # In Git Bash, python and python3 often open the Microsoft Store instead: use the Python running pi2.
    python = Path(sys.executable).as_posix()
    prelude = f'python() {{ "{python}" "$@"; }}; python3() {{ "{python}" "$@"; }}; export -f python python3\n'
    job = {"argv": [git_bash(), "-c", prelude + command], "cwd": workspace, "watchdog": WATCHDOG}
    return [sys.executable, "-c", RUNNER, json.dumps(job)]
