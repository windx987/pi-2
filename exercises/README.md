# Exercises

| # | Tool | Instructions | Playground |
|---|---|---|---|
| 01 | `read` | [README](01-read/01-read.md) | `playground/01-read` |
| 02 | `write` | [README](02-write/02-write.md) | `playground/02-write` |
| 03 | `edit` | [README](03-edit/03-edit.md) | `playground/03-edit` |
| 04 | `grep` | [README](04-search/04-search.md) | `playground/04-search` |
| 05 | `command` | [README](05-command/05-command.md) | `playground/05-command` |
| 06 | `subagent` | [README](06-subagents/06-subagents.md) | `playground/06-subagents` |

## Run checks

Run checks from the repository root:

```bash
# Check one exercise:
python3 exercises/check.py 01

# Check every exercise:
python3 exercises/check.py
```

## Tool inputs

Every tool has this function:

```python
def execute(params, ctx):
```

`params` holds the values from the agent:

```python
path = params["path"]
offset = params.get("offset", 1)
limit = params.get("limit", 2000)
```

`ctx.cwd` is the playground path:

```python
target = Path(ctx.cwd) / path
```

If `ctx.cwd` is `/home/user/pi-2/playground/01-read` and `path` is `todo.md`,
the tool reads `/home/user/pi-2/playground/01-read/todo.md`.
