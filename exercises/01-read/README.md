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

Follow EXERCISE 1 to 4 in [starter.py](starter.py):

1. Resolve `params["path"]` against `ctx.cwd`.
2. Read the file as UTF-8 text.
3. Apply `offset` and `limit`, and say how to read on when lines are left.
4. Raise an exception for a missing file or an offset past the end.

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
