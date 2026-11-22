# Exercise 02: write

The agent can create files and replace them whole.

## Goal

Build `write`, a tool that creates a file with the given content, creating parent directories, and
refuses to write outside the working directory.

## What you learn

- What the schema already guarantees, and what `execute` must still check.
- Checking input where it enters your tool: here, where a file may be written.
- Reporting a side effect clearly, since the model does not see it otherwise.

## How it works

pi2 checks the model's arguments against `parameters` before `execute` runs. A missing `content`, or
a number instead of a string, never reaches your code: the model gets an error result instead. What
the schema cannot express is policy. "Only inside the working directory" is a rule about the value,
not its type, so that check belongs in `execute`, and its error message is an instruction to the
model.

1. The model calls `write({"path": "plan.md", "content": "..."})`.
2. pi2 checks the arguments ([`pi2/schema.py`](../pi2/schema.py)); invalid ones become an error result
   without calling `execute`.
3. `execute` resolves the path, checks it stays inside `ctx.cwd`, creates any missing folders, and
   writes the file.
4. The confirmation goes back to the model, which can now `read` the file or move on.

## Setup

From the repository root:

```bash
python3 -m pi2 --cwd playground/02-write -e tools/write.py
```

## Steps

Use the walkthrough below to create your own extension file. Add `from pathlib import Path` at
the top.

### 1. Resolve the path against the working directory

```python
cwd = Path(ctx.cwd).resolve()
target = (cwd / Path(params["path"]).expanduser()).resolve()
```

`resolve()` makes the path absolute and removes `..` and symlinks, so the next step compares real
locations.

### 2. Refuse paths outside the working directory

```python
if cwd not in target.parents:
    raise ValueError(f"Path is outside the working directory: {params['path']}")
```

`../outside.txt` looks harmless but resolves outside `cwd`. The message says why, so the model picks
another path instead of retrying the same one. A target equal to `cwd` is also rejected: it is a
directory, not a file.

### 3. Create the parent directories, then write the content

```python
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(params["content"], encoding="utf-8")
```

`parents=True` creates missing folders; `exist_ok=True` makes an existing folder no error. Name the
encoding so the result does not depend on the machine.

### 4. Return a short confirmation

```python
return f"Wrote {params['path']}"
```

The model does not see the file unless it reads it. The confirmation tells it the write happened.

## The whole tool

<details>
<summary>Show the complete <code>execute</code></summary>

```python
from pathlib import Path


def execute(params, ctx):
    cwd = Path(ctx.cwd).resolve()
    target = (cwd / Path(params["path"]).expanduser()).resolve()

    if cwd not in target.parents:
        raise ValueError(f"Path is outside the working directory: {params['path']}")

    if target.is_dir():
        raise ValueError(f"Not a file: {params['path']}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(params["content"], encoding="utf-8")
    return f"Wrote {params['path']}"
```

</details>

The reference implementation is [`tools/write.py`](../../tools/write.py).

## Check your tool

```bash
python3 exercises/check.py 02
```

The checks cover relative and absolute paths, nested directories, overwriting, UTF-8, and the
outside-the-working-directory refusal. They also make sure a failed write does not create a file.

## Try it

Ask:

1. **"Create `plan.md` with three bullets about the workshop."**
   The agent should call `write` with the path and content, then confirm.

2. **"Overwrite `draft.md` with a shorter draft."**
   `write` replaces the whole file. It does not append.

3. **"Write `../outside.txt` with hello."**
   The tool must refuse: the path escapes `playground/02-write`. The model should read the error and
   choose another path.

4. **"Read `plan.md` back to me."**
   Load your `read` tool too. The point is to verify what `write` actually wrote.

## Expected result

- `plan.md` exists with the requested content.
- `draft.md` is replaced, not appended to.
- `../outside.txt` is not created.
- The agent reports a clear error for the outside path.
- `python3 exercises/check.py 02` ends with `8 of 8 checks pass.`

## Challenge

Return the number of bytes written, such as `Wrote 42 bytes to plan.md`. Encode the content once,
use the encoded bytes for both the write and the count, and keep the same path checks.

## Where to look

| File | What to look at |
|---|---|
| [`pi2/schema.py`](../pi2/schema.py) | Argument validation before `execute` |
| [`pi2/extensions.py`](../pi2/extensions.py) | `ToolContext.cwd` and `define_tool` |
| [`tools/write.py`](../../tools/write.py) | The reference implementation |
