# Exercise 01: read

The first tool: the agent can look at files in the directory it works in.

## Goal

Build `read`, a tool that returns the text of a file, with optional `offset` and `limit` for long
files.

## What you learn

- What a tool is: a name, a description, the JSON Schema of its arguments, and one function.
- How pi2 offers the tool to the model, runs it, and sends back what it returns.
- How an exception becomes an error result the model can act on, instead of a crash.

## How it works

The model cannot touch your machine. It can only answer with text or a tool call: a tool name and
JSON arguments. pi2 runs the tool and sends the result back as the next message. A tool is therefore
a contract: the description and schema tell the model what it may ask for, and the result tells it
what happened.

1. pi2 starts, loads `read.py` with `-e`, and calls its `extension(pi)`.
2. `pi.register_tool(read_tool)` adds `read`. The next request to the model lists it with its schema.
3. The model answers with a call such as `read({"path": "todo.md"})`.
4. pi2 checks the arguments against `parameters`, then calls `execute(params, ctx)`.
5. The string `execute` returns, or the message of the exception it raises, becomes the tool result.
   pi2 sends it to the model, which answers or calls another tool.

## Setup

From the repository root:

```bash
python3 -m pi2 --cwd playground/01-read -e exercises/01-read/read.py
```

`--cwd` makes `playground/01-read` the agent's working directory. `-e` loads your tool from the
repository root.

## Steps

Follow the comments in [`01-read/read.py`](01-read/read.py). Add `from pathlib import Path` at the
top.

### 1. Resolve the path

```python
path = Path(params["path"]).expanduser()
target = path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()
```

`ctx.cwd` is the directory the agent works in. `/` joins it with a relative path; an absolute path
replaces it, so both kinds work.

### 2. Read the file as UTF-8

```python
lines = target.read_text(encoding="utf-8").splitlines()
```

Name the encoding: the default depends on the machine. Split into lines now, because the next step
counts lines. A missing file raises `FileNotFoundError`; pi2 turns that into an error result, and
the model reads the message.

### 3. Apply offset and limit

```python
offset = max(1, int(params.get("offset", 1)))
limit = max(1, int(params.get("limit", 2000)))
if lines and offset > len(lines):
    raise ValueError(f"offset {offset} is past the end of the file")
start = offset - 1
end = start + limit
```

`offset` counts from 1, a Python list from 0, hence `offset - 1`. An offset past the end is an error,
like a missing file. `int()` because the schema type is `number`, so the model may send `3.0`.
Without `limit`, read up to 2000 lines.

### 4. Join the lines and say how to read on

```python
output = "\n".join(lines[start:end])
if end < len(lines):
    output += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1}.]"
return output
```

The model cannot see what was left out. The note tells it the next call to make.

### 5. Register the tool

The starter already has this at the bottom:

```python
def extension(pi):
    pi.register_tool(read_tool)
```

## The whole tool

<details>
<summary>Show the complete <code>execute</code></summary>

```python
from pathlib import Path


def execute(params, ctx):
    path = Path(params["path"]).expanduser()
    target = path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()

    lines = target.read_text(encoding="utf-8").splitlines()
    offset = max(1, int(params.get("offset", 1)))
    limit = max(1, int(params.get("limit", 2000)))

    if lines and offset > len(lines):
        raise ValueError(f"offset {offset} is past the end of the file")

    start = offset - 1
    end = start + limit
    output = "\n".join(lines[start:end])
    if end < len(lines):
        output += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1}.]"
    return output
```

</details>

The reference implementation is [`tools/read.py`](../tools/read.py).

## Check your tool

Before you try it with the model, check it without one:

```bash
python3 exercises/check.py 01
```

Each check calls your `execute()` directly. It shows `PASS`, `FAIL` with what went wrong, or `TODO`
while `execute()` still raises `NotImplementedError`. When all checks pass, the tool does what the
steps ask.

## Try it

With the agent running from the setup command, ask:

1. **"Read `todo.md` and summarise the unfinished items."**
   The agent should call `read` with `{"path": "todo.md"}` and answer from the text.

2. **"Read lines 10 to 20 of `long.log`."**
   The agent should call `read` with `offset: 10, limit: 11` (or `limit: 10`; either is reasonable).
   You should see the two marker lines, `START OF INTERESTING WINDOW` and
   `END OF INTERESTING WINDOW`.

3. **"Read `unicode.txt`."**
   The text contains accents, CJK, emoji and Thai. The tool must return it unchanged.

4. **"Read `missing.txt`."**
   There is no such file. The tool raises, and the model receives an error result instead of a
   crash. It should tell you the file is missing.

## Expected result

- Tool calls show a `path`, and `offset`/`limit` when you ask for a range.
- A partial read ends with a note such as `[101 more lines. Use offset=21.]`.
- A missing file produces an error result, not a traceback in the terminal.
- `python3 exercises/check.py 01` ends with `10 of 10 checks pass.`

## Challenge

Add a `line_numbers` argument. When it is true, prefix each line with its number, starting from
`offset`. Keep the continuation note working.

## Where to look

| File | What to look at |
|---|---|
| [`pi2/extensions.py`](../pi2/extensions.py) | `Tool`, `define_tool`, `ToolContext`, `ExtensionAPI.register_tool` |
| [`pi2/schema.py`](../pi2/schema.py) | How the model's arguments are checked before `execute` |
| [`pi2/agent_loop.py`](../pi2/agent_loop.py) | `execute_tool_call`: how a result or an exception becomes a tool result |
