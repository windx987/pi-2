# pi/2 tool-building exercises

Six exercises that build the tools an agent needs, one capability at a time. pi/2 has no built-in
tools: every tool comes from an extension, and every extension is a Python file with one
`extension(pi)` function. You write the tool; pi/2 gives it to the model.

| # | Exercise | Tool to build | Playground | Format |
|---|---|---|---|---|
| 01 | [read](01-read.md) | `read` | `playground/01-read/` | walkthrough |
| 02 | [write](02-write.md) | `write` | `playground/02-write/` | walkthrough |
| 03 | [edit](03-edit.md) | `edit` | `playground/03-edit/` | build from scratch |
| 04 | [search](04-search.md) | `grep` | `playground/04-search/` | build from scratch |
| 05 | [execute](05-execute.md) | `bash` | `playground/05-execute/` | build from scratch |
| 06 | [subagents](06-subagents.md) | `subagent` | `playground/06-subagents/` | build from scratch |

The instructor walks through 01 and 02. In 03 to 06 you get the contract, hints and checks, but not
the full solution. Working reference implementations are in `tools/`, for the instructor and for
after you have tried the exercise yourself.

## Requirements

- Python 3.10 or newer, no packages.
- A settings file with an OpenAI-compatible endpoint. `settings.json` is in the repository root;
  `settings.local.json` is ignored by git and is a good place for your own key.

## Running an exercise

Run every command from the **repository root**. `python3 -m pi2` needs the repository root on
Python's import path, and `--cwd` tells the agent which directory to work in:

```bash
cd /path/to/pi-2
python3 -m pi2 --cwd playground/03-edit -e exercises/03-edit/edit.py
```

With private settings:

```bash
python3 -m pi2 --cwd playground/03-edit \
  --settings settings.local.json \
  -e exercises/03-edit/edit.py
```

`--cwd`, `-e` and `--settings` are resolved from the directory where you run the command, not from
each other. The default `settings.json` is still found in the repository root.

Because the agent starts inside `playground/NN-...`, the prompts stay short:

> Read `math.py` and fix the bug.
> Create `plan.md` with three items.

## Checking your tool

Each exercise has a `test_*.py` next to its starter. Run the checks without a model:

```bash
python3 exercises/check.py 03
```

Use `01` to `06`, or no number to run every exercise. A check shows:

- `PASS` — the tool did what the step asks.
- `FAIL` — it raised the wrong error, returned the wrong text, or changed the wrong file.
- `TODO` — `execute()` still raises `NotImplementedError`.

To check the reference implementation instead of your file:

```bash
python3 exercises/check.py 03 tools/edit.py
```

## Resetting the playground

The exercises change files in `playground/NN-...`. To put an exercise back as it was:

```bash
git restore playground/03-edit
```

## Resetting after a task

`--cwd` limits the default paths and the `write`/`edit` guard. It is not a sandbox: `read` and
`bash` can still reach outside it. Restore a changed playground with git:

```bash
git restore playground/03-edit
```

## What a tool is

A tool is a `define_tool(...)` value:

```python
tool = define_tool(
    name="read",                 # what the model calls
    label="read",
    description="...",           # what the model reads
    parameters={...},            # JSON Schema of the arguments
    prompt_snippet="...",        # one line for the system prompt
    prompt_guidelines=["..."],
    execute=execute,             # execute(params, ctx) -> str
)
```

`execute(params, ctx)` gets the validated arguments and a `ToolContext`:

- `ctx.cwd` is the working directory (`--cwd`, or the current directory).
- `ctx.session` is the running `AgentSession` (used by the subagent exercise).

Return a string: it becomes the tool result. Raise an exception: its message becomes an error result
the model can read. `pi2` validates the arguments against `parameters` before `execute` runs.
