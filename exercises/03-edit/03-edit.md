# Exercise 03: edit

## Goal
- Build a tool that makes one exact text replacement in a file.
- Ask the agent to fix `math.py`, then edit the timeout in `config.ini` with enough context.

## Requirements
- Required: `path`, `oldText`, and `newText`.
- Keep the target inside `ctx.cwd`.
- `oldText` must be non-empty and occur exactly once.
- Leave the file unchanged on failure.
- Write UTF-8 and return a confirmation.

## Output

Return one short line that includes the path:

```text
Edited math.py
```

## Errors

Raise `ValueError` when the file is missing or outside `ctx.cwd`, when `oldText`
is empty, or when `oldText` does not occur exactly once. Leave the file
unchanged.

## Hints
- Read the file before changing it.
- Check `text.count(oldText)` before calling `replace`.
- Use `text.replace(oldText, newText, 1)`.

## Run
```bash
python3 -m pi2 --cwd playground/03-edit \
  -e tools/01-read.py -e tools/03-edit.py
```

## Check
```bash
python3 exercises/check.py 03
```
