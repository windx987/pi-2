# Exercise 02: write

Let the agent create files, and replace them whole.

## What you write

`execute(params, ctx)` in [write.py](write.py).

| Name | Is |
|---|---|
| `params["path"]` | The file to write, relative to the working folder or absolute |
| `params["content"]` | The whole new content of the file |
| `ctx.cwd` | The working folder |

pi2 checks the arguments against the schema first: a missing `content` never reaches your code. What the schema cannot check is where the file goes. That rule is yours: only inside `ctx.cwd`.

## Steps

Follow EXERCISE 1 to 4 in [write.py](write.py). Add `from pathlib import Path` at the top.

1. Find the real location of the file.

   ```python
   cwd = Path(ctx.cwd).resolve()
   path = (cwd / params["path"]).resolve()
   ```

   `resolve()` removes `..` and symlinks, so step 2 compares real locations.

2. Refuse a path outside the working folder.

   ```python
   if not path.is_relative_to(cwd):
       raise PermissionError(f"Refusing to write outside the working directory: {params['path']}")
   ```

   `notes/../../.bashrc` looks harmless but lands outside. The message tells the model why, so it picks another path.

3. Create the folders, then write the file.

   ```python
   path.parent.mkdir(parents=True, exist_ok=True)
   data = params["content"].encode("utf-8")
   path.write_bytes(data)
   ```

4. Say what happened.

   ```python
   return f"Wrote {len(data)} bytes to {params['path']}"
   ```

   The model does not see the file unless it reads it: this line is all it gets.

The four blocks, one under the other, are the whole function:

<p align="center"><img alt="The write starter, solved, with lines highlighted by step. Right: what happens when you ask 'Create notes/todo.md with three items.': the model calls write, pi2 checks the arguments, execute resolves the path inside the working directory, creates notes/ and writes the file, and the confirmation goes back to the model." src="../../assets/diagrams/exercise-02-write.svg" width="900"></p>

<details>
<summary>The whole function</summary>

```python
from pathlib import Path


def execute(params, ctx):
    cwd = Path(ctx.cwd).resolve()
    path = (cwd / params["path"]).resolve()
    if not path.is_relative_to(cwd):
        raise PermissionError(f"Refusing to write outside the working directory: {params['path']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = params["content"].encode("utf-8")
    path.write_bytes(data)
    # The model does not see the file unless it reads it, so say what happened.
    return f"Wrote {len(data)} bytes to {params['path']}"
```

</details>

## Check

```bash
python3 ~/pi-2/exercises/check.py 02
```

## Try it

Load it with your read tool, from the playground copy:

```bash
cd ~/pi-workshop
python3 ~/pi-2/pi2.py -e ~/pi-2/exercises/01-read/read.py -e ~/pi-2/exercises/02-write/write.py
```

| Ask | You should see |
|---|---|
| Create notes/todo.md with three workshop goals, then read it back. | A green `write notes/todo.md` box with your confirmation, then a `read` of it. `cat notes/todo.md` shows the same |
| Write a file to /tmp/outside.txt. | A red box with your message; no file is written, and the agent says it was refused |

<p align="center"><img alt="Try it for write: you ask to create notes/todo.md and read it back, and the agent calls write then read, both green; you ask to write /tmp/outside.txt and the write turns red: refused outside the working directory. Hint: the model sees only your confirmation, not the file." src="../../assets/diagrams/exercise-02-try.svg" width="900"></p>

## Read more

- [pi2/schema.py](../../pi2/schema.py): `validate_tool_arguments`, what the schema checks before `execute`.
- Pi's own `write` is [tools/write.ts](https://github.com/windx987/pi-2/blob/cead615b4/packages/coding-agent/src/core/tools/write.ts). Pi runs tool calls at the same time, so writes to one file wait in a queue; pi2 runs them one after another.
