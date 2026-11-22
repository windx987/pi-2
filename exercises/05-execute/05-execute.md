# Exercise 05: execute

Build `bash`, a tool that lets the agent run shell commands in its working directory.

## Task

From the repository root:

```bash
python3 -m pi2 --cwd playground/05-execute \
  -e tools/read.py -e tools/edit.py \
  -e tools/bash.py
```

Ask the agent to run the tests, fix `subtract` in `calculator.py`, and run the tests again.

## Contract

- Run `params["command"]` with `bash -c` and `cwd=ctx.cwd`.
- Capture stdout and stderr together as text.
- Return the output; if empty, return `(no output)`.
- For a non-zero exit, raise an error containing the output and exit code.

## Hints

Use `subprocess.run` with `cwd=ctx.cwd`, `text=True`, captured stdout, and stderr redirected to
stdout. Check `returncode` before returning.

## Check

```bash
python3 exercises/check.py 05
```

The reference implementation is [`tools/bash.py`](../../tools/bash.py).
