# Exercises

| # | Tool | Edit this file | Instructions | Playground |
|---|---|---|---|---|
| 01 | `read` | `tools/01-read.py` | [README](01-read/01-read.md) | `playground/01-read` |
| 02 | `write` | `tools/02-write.py` | [README](02-write/02-write.md) | `playground/02-write` |
| 03 | `edit` | `tools/03-edit.py` | [README](03-edit/03-edit.md) | `playground/03-edit` |
| 04 | `grep` | `tools/04-grep.py` | [README](04-search/04-search.md) | `playground/04-search` |
| 05 | `command` | `tools/05-command.py` | [README](05-command/05-command.md) | `playground/05-command` |
| 06 | `subagent` | `tools/06-subagent.py` | [README](06-subagents/06-subagents.md) | `playground/06-subagents` |

Each starter in `tools/` already registers its tool and raises
`NotImplementedError`; fill in that file's `execute`.

## Run checks

Run checks from the repository root:

```bash
# Check one exercise:
python3 exercises/check.py 01

# Check every exercise:
python3 exercises/check.py
```

The checks read `tools/<NN>-<name>.py` unless you pass another file:
`python3 exercises/check.py 06 tools/06-subagent.py`.

## How a tool works

Every tool has this function:

```python
def execute(params, ctx):
```

### Input

`params` holds the values from the agent:

```python
path = params["path"]
offset = params.get("offset", 1)
limit = params.get("limit", 2000)
```

`ctx.cwd` is the playground path. Join relative paths with it:

```python
target = Path(ctx.cwd) / path
```

If `ctx.cwd` is `/home/user/pi-2/playground/01-read` and `path` is `todo.md`,
the tool reads `/home/user/pi-2/playground/01-read/todo.md`.

The agent may also send an absolute path. That same line handles it: an
absolute right side replaces the left side.

`ctx.session` is the running session, for a tool that needs more than a
directory. Exercise 06 uses it to start a child session.

### Output

`execute` returns a string. pi2 shows that text to the model, so write it for a
reader: the file text, the result of the command, or a short line saying what
changed.

Return text only. Do not return a dict or list: pi2 would show the model its
Python repr instead of a result.

### Errors

When something is wrong, raise an exception:

```python
if not target.exists():
    raise ValueError(f"File not found: {params['path']}")
```

pi2 turns the message into an error result the model can read. Do not return
`"error: ..."` — the model would treat it as normal output.

Say what is wrong and, when you can, what to do next. `NotImplementedError` is
special: the checks show it as TODO, not FAIL.
