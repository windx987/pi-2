# Exercise 02: write

## Goal
- Build a tool that creates or replaces a UTF-8 file.
- Ask the agent to create `plan.md`, replace `draft.md`, and try `../outside.txt`.

## Requirements
- Required: `path` and `content`.
- Resolve paths from `ctx.cwd`.
- Refuse paths outside `ctx.cwd`.
- Create missing parent directories.
- Replace the complete file contents.
- Return a short confirmation.

## Hints
- Resolve both `cwd` and the target before checking containment.
- Use `target.parent.mkdir(parents=True, exist_ok=True)`.
- Use `target.write_text(..., encoding="utf-8")`.

## Run
```bash
python3 -m pi2 --cwd playground/02-write -e tools/02-write.py
```

## Check
```bash
python3 exercises/check.py 02
```
