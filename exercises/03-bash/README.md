# Exercise 03: bash

The agent can run commands, each one in a new Docker container.

## What you learn

- Running a child process and collecting its output.
- Turning an exit code into a result the model reacts to.
- Bounding what a command can do: time limits, ctrl+c, isolation.

## How it works

With `bash` the agent can do anything a shell can, so where the shell runs matters. Every command runs in a new Docker container that is meant to see only the working directory (mounted at `/workspace`), to have no network, and to be removed when the command ends. `docker_args()` in [starter.py](starter.py) builds that command line for you; your job is the process handling around it.

The container reduces what a command can reach; it is not a proven sandbox. Run the [isolation checks](#isolation-checks) on your machine before relying on it.

A command result has three parts the model needs: the output (stdout and stderr in the order they arrived), the exit code, and whether it was stopped. A non-zero exit code is not a failure of the tool, but the model must notice it, so it is reported as an error result together with the output.

1. The model calls `bash({"command": "npm test"})`.
2. `execute` starts `docker run ... bash -c "npm test"` with the working directory mounted.
3. stdout and stderr arrive as one text, in order.
4. The process ends with an exit code. The tool returns the output, or raises an exception with it when the code is not 0.
5. A timeout stops the process with SIGTERM, and the result says the command was stopped. ctrl+c stops it too.

Why SIGTERM: `docker run` passes SIGTERM on to the container, whose init process stops the command. SIGKILL, which `proc.kill()` and `subprocess.run(timeout=...)` send, ends only the `docker` client, and the container keeps running.

## Steps

Follow EXERCISE 1 to 4 in [starter.py](starter.py). Add `import subprocess` at the top.

1. Start the process with `subprocess.Popen`; a missing Docker raises `FileNotFoundError`.

   ```python
   try:
       proc = subprocess.Popen(
           ["docker", *docker_args(params["command"], ctx.cwd)],
           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
       )
   except FileNotFoundError:
       raise RuntimeError("Docker is not installed or not on PATH.") from None
   ```

   `Popen` starts the process without waiting for it. The arguments are a list, so no shell runs on your machine: the model's command reaches `bash` only inside the container. `from None` keeps the error message short for the model.

2. Collect stdout and stderr as one text with `communicate()`.

   ```python
   output, _ = proc.communicate()
   ```

   `stderr=subprocess.STDOUT` in step 1 sends errors into the same pipe, so the output arrives in order, as a terminal shows it. `text=True` makes it a `str`. `communicate()` waits for the end and reads everything.

3. Return the output, or raise with `Command exited with code N`.

   ```python
   if proc.returncode != 0:
       raise RuntimeError(f"{output}\nCommand exited with code {proc.returncode}.")
   return output or "(no output)"
   ```

   A failing command becomes an error result that still has its output, so the model sees what failed. `"(no output)"` tells it an empty result is not a broken tool.

4. Pass the timeout to `communicate()`; on `TimeoutExpired`, call `terminate()` and `communicate()` again. This replaces the line from step 2:

   ```python
   try:
       output, _ = proc.communicate(timeout=params.get("timeout"))
   except subprocess.TimeoutExpired:
       proc.terminate()
       output, _ = proc.communicate()
       raise RuntimeError(f"{output}\nCommand stopped after {params['timeout']} seconds.") from None
   ```

   Without a timeout `params.get` gives `None`, and `communicate()` waits forever. `terminate()` sends SIGTERM, which stops the container (see "Why SIGTERM" above). The second `communicate()` waits until it has stopped and collects the output so far.

   ctrl+c needs the same treatment, or the container keeps running after you stop the agent. Add a second `except` to the same `try`:

   ```python
   except KeyboardInterrupt:
       proc.terminate()
       proc.communicate()
       raise
   ```

<details>
<summary>The whole function</summary>

```python
import subprocess


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
```

</details>

Then check the timeout:

```bash
python3 "$REPO/exercises/03-bash/check_timeout.py"
```

It runs `sleep 30` with a 2 second timeout and checks that the result is an error saying the command was stopped, and that no container is left running.

## Try it

Start Docker (Docker Desktop, or `colima start`) and pull the image once: `docker pull node:22-bookworm-slim`. Load it with your read and write tools, from your playground copy:

```bash
cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/exercises/01-read/starter.py" -e "$REPO/exercises/02-write/starter.py" \
  -e "$REPO/exercises/03-bash/starter.py"
```

Ask:

- "Run the tests." The result shows a failing test and exit code 1.
- "Why does the test fail?" The agent reads `math.js` and the test, and explains. Fixing it with a small change is exercise 04.
- "Run `sleep 30` with a 2 second timeout."
- "Run `getent hosts example.com`." It fails: the container has no network.

## Expected result

- The tool box shows `$ npm test` and the first lines of the output.
- Failing commands come back as red error results with their output and exit code, and the agent reacts to them.
- The timeout stops the command, and ctrl+c stops a running command. Afterwards `docker ps` shows no container.

## Isolation checks

Status: verified on 2026-11-19 with Colima (macOS, arm64) by running the Python solution directly against real containers. The same checks were verified for the TypeScript solution on 2026-11-18; `docker_args()` uses the same flags. Other runtimes, such as Docker Desktop or Linux, are not verified yet. Each check is also a command you can ask the agent to run.

| Check | Command | Expected |
|---|---|---|
| No network | `getent hosts example.com`, or `node -e "fetch('https://example.com')"` (the image has no `curl`) | Fails to resolve or connect |
| No host files outside the workspace | `ls /Users /home; cat /etc/hostname` | No host home directories; the hostname is the container's |
| Memory limit | `node -e "const a=[]; for(;;) a.push(Buffer.alloc(1e8, 1))"` | Killed (exit code 137) at about 1 GB |
| Process limit | `cat /sys/fs/cgroup/pids.max`, then start 400 processes | `256`; the shell cannot start them all and fails (exit code 254) |
| Timeout stops the container | `check_timeout.py`, or `sleep 300` with `timeout: 2`, then `docker ps` on the host | No container left running |
| Cleanup after errors | a failing command, then `docker ps -a` on the host | No leftover container (`--rm`) |
| No escape through symlinks | `ln -s / host-root && ls host-root/` | Lists the container's root, not the host's |

SAFETY: the symlink check covers commands. Your `read` and `write` tools, and later `edit`, run on the host: a symlink in the workspace that points outside it makes them reach the host. Resolve paths with `Path.resolve()` before the containment check if that matters for your setup.

SAFETY: the isolation depends on the mount. Mounting a home directory or the Docker socket gives the agent the host back.

## Where to look

| File | What to look at |
|---|---|
| [pi2/tui.py](../../pi2/tui.py) | `tool_title`: why a bash call shows as `$ command` |
| [pi2/agent_loop.py](../../pi2/agent_loop.py) | `execute_tool_call`: ctrl+c arrives in your tool as `KeyboardInterrupt` and ends the run as aborted |
| [examples/permission_gate.py](../../examples/permission_gate.py) | A rule that blocks dangerous commands before your tool runs |

## In Pi

Pi's original tool is [tools/bash.ts](https://github.com/windx987/pi-2/blob/cead615b4/packages/coding-agent/src/core/tools/bash.ts). It runs commands on the host, not in a container, streams output while the command runs, and truncates long output.
