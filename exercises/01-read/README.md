# Exercise 01: read

The first tool: the agent can look at files in the directory it works in.

## What you learn

- What a tool is: a name, a description and the JSON Schema of its arguments, plus one function.
- How pi2 offers the tool to the model, runs it, and sends back what it returns.
- How a failure becomes an error result the model can act on, instead of a crash.

## How it works

The model cannot touch your machine. It can only answer with text or with a tool call: a tool name and JSON arguments. pi2 runs the tool and sends the result back as the next message. A tool is therefore a contract: the description and schema tell the model what it may ask for, and the result tells it what happened.

1. pi2 starts, loads `starter.py` with `-e`, and calls its `extension(pi)`.
2. `pi.register_tool(read_tool)` adds `read`. The next request to the model lists it with its schema (step 2 in [the big picture](../../README.md#the-big-picture)).
3. The model answers with a call such as `read({"path": "math.js"})`.
4. pi2 checks the arguments against `parameters`, then calls `execute(params, ctx)` (steps 6 and 7).
5. The string `execute` returns, or the message of the exception it raises, becomes the tool result. pi2 sends it to the model, which answers or calls another tool (step 8).

## Steps

Follow EXERCISE 1 to 4 in [starter.py](starter.py). Add `from pathlib import Path` at the top.

1. Resolve `params["path"]` against `ctx.cwd`.

   ```python
   path = Path(ctx.cwd) / params["path"]
   ```

   `ctx.cwd` is the directory the agent works in. `/` joins it with a relative path; an absolute path replaces it, so both kinds work.

2. Read the file as UTF-8 text.

   ```python
   lines = path.read_text(encoding="utf-8").split("\n")
   ```

   Name the encoding: the default depends on the machine. Split into lines now, because step 3 counts lines.

3. Apply `offset` and `limit`, and say how to read on when lines are left.

   ```python
   offset = int(params.get("offset") or 1)
   end = len(lines)
   if params.get("limit") is not None:
       end = min(end, offset - 1 + int(params["limit"]))
   text = "\n".join(lines[offset - 1:end])
   if end < len(lines):
       text += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1} to continue.]"
   return text
   ```

   `offset` counts from 1, a Python list from 0, hence `offset - 1`. Without `limit`, read to the end; `min` stops at the end when `limit` reaches past it. `int()` because the schema type is `number`, so the model may send `3.0`. The model cannot see what was left out; the note tells it the next call to make.

4. Raise an exception for a missing file or an offset past the end.

   ```python
   if not path.is_file():                 # before read_text
       raise FileNotFoundError(f"File not found: {params['path']}")

   if offset > len(lines):                # after offset is known
       raise ValueError(f"Offset {offset} is beyond the end of the file ({len(lines)} lines).")
   ```

   pi2 turns the exception into an error result, and the model reads the message. Name the path the model sent, not the resolved one, so it recognizes its own call.

The whole run, with the line of the solution each step uses:

<p align="center"><img alt="The read starter, solved, with lines highlighted by step: define_tool's name, description and parameters (steps 2 and 6), execute (step 7), its return and raises (step 8), extension and register_tool (start). Right: what happens when you ask 'What is in package.json?', from loading the file to the tool result." src="../../assets/diagrams/exercise-01-read.svg" width="900"></p>

<details>
<summary>The whole function</summary>

```python
from pathlib import Path


def execute(params, ctx):
    path = Path(ctx.cwd) / params["path"]
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {params['path']}")
    lines = path.read_text(encoding="utf-8").split("\n")

    offset = int(params.get("offset") or 1)
    if offset > len(lines):
        raise ValueError(f"Offset {offset} is beyond the end of the file ({len(lines)} lines).")
    end = len(lines)
    if params.get("limit") is not None:
        end = min(end, offset - 1 + int(params["limit"]))
    text = "\n".join(lines[offset - 1:end])
    if end < len(lines):
        # Tell the model how to read on; it cannot see what was left out.
        text += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1} to continue.]"
    return text
```

</details>

## Check your tool

Before you try it with the model, check it without one:

```bash
python3 "$REPO/exercises/check.py" 01
```

Each step of the list above has checks that call your `execute()` directly. A check shows PASS, FAIL with what went wrong, or TODO while `execute()` still raises `NotImplementedError`. When all checks pass, the tool does what the steps ask. Whether the model uses the tool well is what the next section shows.

## Try it

Work in a copy of the playground, never in the repository (`REPO` is the path of your clone):

```bash
cp -R "$REPO/playground" ~/pi-workshop && cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/exercises/01-read/starter.py"
```

Ask: "What does math.js export?", then "Show me lines 5 to 7 of math.js.", then "Read missing.txt."

## Expected result

- The agent calls `read`. A tool box shows `read math.js` and the first lines of the file, and turns green.
- For part of a file, the call has `offset` and `limit`.
- For a missing file, the box turns red with your message, and the agent says the file does not exist instead of inventing its contents.

## Where to look

| File | What to look at |
|---|---|
| [pi2/extensions.py](../../pi2/extensions.py) | `define_tool`, `ExtensionAPI.register_tool` |
| [pi2/session.py](../../pi2/session.py) | `AgentSession.prompt`: the tools offered to the model |
| [pi2/agent_loop.py](../../pi2/agent_loop.py) | `execute_tool_call`: validation, execution, the result |

## In Pi

Pi's original `read` tool also reads images, streams large files and truncates long output: [tools/read.ts](https://github.com/windx987/pi-2/blob/cead615b4/packages/coding-agent/src/core/tools/read.ts) at the commit before the workshop removed it.
