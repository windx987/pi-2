# Exercise 03: bash

Let the agent run commands. Each one runs with bash on your machine, in the working folder, as Pi's own bash tool does.

## What you write

`execute(params, ctx)` in [bash.py](bash.py). `command_args()` is done for you: it builds the command line that runs bash in the working folder. Your part is the process around it.

| Name | Is |
|---|---|
| `params["command"]` | The bash command the model wants to run, such as `python3 -m unittest` |
| `params.get("timeout")` | Seconds before it is stopped (optional) |
| `ctx.cwd` | The working folder, where the command runs |

Return the output. When the command fails (exit code not 0), raise with the output and the code: the model must notice it.

## Steps

Follow EXERCISE 1 to 4 in [bash.py](bash.py). Add `import subprocess` at the top.

1. Start the command.

   ```python
   proc = subprocess.Popen(
       command_args(params["command"], ctx.cwd),
       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
   )
   ```

   `stderr=subprocess.STDOUT` puts errors in the same text as the output, in order, as a terminal shows them.

2. Wait for it, at most `timeout` seconds.

   ```python
   try:
       output, _ = proc.communicate(timeout=params.get("timeout"))
   ```

3. Stop it at the timeout, or when you press ctrl+c. These belong to the `try` of step 2:

   ```python
   except subprocess.TimeoutExpired:
       proc.terminate()
       output, _ = proc.communicate()
       raise RuntimeError(f"{output}\nCommand stopped after {params['timeout']} seconds.") from None
   except KeyboardInterrupt:
       proc.terminate()
       proc.communicate()
       raise
   ```

   Use `terminate()`, not `kill()`: the runner in `command_args()` passes it on and stops the command and everything it started. `kill()` stops only the runner, and the command keeps running.

4. Return the output, or raise when the command failed.

   ```python
   if proc.returncode != 0:
       raise RuntimeError(f"{output}\nCommand exited with code {proc.returncode}.")
   return output or "(no output)"
   ```

The four blocks, one under the other, are the whole function:

<p align="center"><img alt="The bash starter, solved, with lines highlighted by step; the runner and command_args are folded. Right: what happens when you ask 'Run the tests.': the model calls bash with python3 -m unittest, execute runs it with bash in the playground, one test fails with exit code 1, and the output goes back as an error result." src="../../assets/diagrams/exercise-03-bash.svg" width="900"></p>

<details>
<summary>The whole function</summary>

```python
import subprocess


def execute(params, ctx):
    proc = subprocess.Popen(
        command_args(params["command"], ctx.cwd),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        output, _ = proc.communicate(timeout=params.get("timeout"))
    except subprocess.TimeoutExpired:
        # SIGTERM, not kill(): the runner passes SIGTERM on to the command, SIGKILL leaves it running.
        proc.terminate()
        output, _ = proc.communicate()
        raise RuntimeError(f"{output}\nCommand stopped after {params['timeout']} seconds.") from None
    except KeyboardInterrupt:
        # ctrl+c in pi2: stop the command too, then let pi2 handle the interrupt.
        proc.terminate()
        proc.communicate()
        raise
    if proc.returncode != 0:
        raise RuntimeError(f"{output}\nCommand exited with code {proc.returncode}.")
    return output or "(no output)"
```

</details>

## Check

```bash
python3 exercises/check.py 03
```

The checks run real commands with bash in a temporary folder, including one that starts a child process and must be stopped at the timeout.

## Try it

```bash
python3 pi2.py --cwd playground -e exercises/01-read/read.py -e exercises/02-write/write.py \
  -e exercises/03-bash/bash.py -e examples/permission_gate.py
```

The commands run on your machine, as you: they can change your files and use your network. Keep the [permission gate](../../examples/permission_gate.py) loaded, work in the playground, and read each command the agent runs.

| Ask | You should see |
|---|---|
| Run the tests. | A red `$ python3 -m unittest` box: one failing test, exit code 1 |
| Why does the test fail? | The agent reads `calc.py` and the test, and explains. Fixing it is exercise 04 |
| Run `sleep 30` with a 2 second timeout. | Stopped after 2 seconds; `ps` in another terminal shows no `sleep 30` left |
| Delete the incidents folder with rm -rf. | Blocked by the permission gate before it runs; the folder stays |

<p align="center"><img alt="Try it for bash: Run the tests gives a red python3 -m unittest with one failing test and exit code 1; Why does the test fail? reads calc.py and test_calc.py; sleep 30 with a 2 second timeout is stopped and nothing is left running; rm -rf incidents is blocked by the permission gate. Hint: the commands run as you, so keep the gate loaded and run from the repository root with --cwd playground." src="../../assets/diagrams/exercise-03-try.svg" width="900"></p>

## Read more

- [examples/permission_gate.py](../../examples/permission_gate.py): a rule that blocks dangerous commands before your tool runs.
- [pi2/windows.py](../../pi2/windows.py): on Windows `terminate()` sends no signal, so a watchdog stops the commands, in Git Bash.
- [pi2/agent_loop.py](../../pi2/agent_loop.py): `execute_tool_call`, where ctrl+c reaches your tool as `KeyboardInterrupt`.
- Pi's own `bash` also runs on your machine, and streams output: [tools/bash.ts](https://github.com/windx987/pi-2/blob/cead615b4/packages/coding-agent/src/core/tools/bash.ts).
