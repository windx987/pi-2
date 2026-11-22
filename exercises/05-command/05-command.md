# Exercise 05: command

## Goal
- Build a cross-platform tool that runs a shell command in the working directory.
- Ask the agent to run the tests and fix `subtract` in `calculator.py`.

## Requirements
- Required: `command`.
- Run it with the host operating system's shell and `cwd=ctx.cwd`.
- Combine stdout and stderr.
- Return `(no output)` when there is no output.
- Raise an error containing the output and exit code when it fails.

## Output

Return stdout and stderr together. When both are empty, return `(no output)`.

## Errors

Raise `RuntimeError` when the command exits non-zero. Include the output and
the code:

```text
bad
Command exited with code 3
```

A missing command is just exit code 127.

## Hints
- Use `subprocess.run(..., shell=True, cwd=ctx.cwd)`.
- Capture stdout and redirect stderr to stdout.
- Do not invoke `bash -c`; Windows may not have Bash.

## Run
```bash
python3 -m pi2 --cwd playground/05-command \
  -e tools/01-read.py -e tools/03-edit.py -e tools/05-command.py
```

## Check
```bash
python3 exercises/check.py 05
```
