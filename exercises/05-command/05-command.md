# Exercise 05: command

Build `command`, a tool that lets the agent run shell commands in its working directory.

## Task

From the repository root:

```bash
python3 -m pi2 --cwd playground/05-command \
  -e tools/01-read.py -e tools/03-edit.py \
  -e tools/05-command.py
```

Ask the agent to run the tests, fix `subtract` in `calculator.py`, and run the tests again.

## Contract

- Run `params["command"]` with the host operating system's shell and `cwd=ctx.cwd`.
- Capture stdout and stderr together as text.
- Return the output; if empty, return `(no output)`.
- For a non-zero exit, raise an error containing the output and exit code.

## Hints

Use `subprocess.run` with `shell=True`, `cwd=ctx.cwd`, `text=True`, captured stdout, and stderr
redirected to stdout. Check `returncode` before returning. On Unix this uses the default Unix shell; on
Windows it uses the default Windows shell, so shell syntax may differ between platforms.

## Check

```bash
python3 exercises/check.py 05
```

The starter template is [`tools/05-command.py`](../../tools/05-command.py).
