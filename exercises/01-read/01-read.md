# Exercise 01: read

## Goal
- Build a tool that reads a UTF-8 text file.
- Ask the agent to read `todo.md`, lines from `long.log`, and `unicode.txt`.

## Requirements
- The tool receives a `path`.
- `offset` is optional and starts at line 1.
- `limit` is optional and defaults to 2000 lines.
- Relative paths start from `ctx.cwd`.
- Return the selected file text.
- If more lines remain, tell the agent the next offset.
- Show an error when the file is missing or the offset is invalid.

## Hints
- Use `Path(ctx.cwd)` and `Path.read_text(encoding="utf-8")`.
- Convert the one-based offset to a zero-based slice.
- Use `NotImplementedError` until your implementation is ready.

## Run
```bash
python3 -m pi2 --cwd playground/01-read -e tools/01-read.py
```

## Check
```bash
python3 exercises/check.py 01
```
