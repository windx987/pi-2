# Exercise 05: extensions (Python only)

Exercises 01 to 04 each build one tool. An extension can do more than that. It can watch and block other tools' calls, or run a whole agent inside a tool. This exercise has two examples, one for each idea:

| Example | What it shows | Pi's version |
|---|---|---|
| [permission_gate.py](permission_gate.py) | A `tool_call` listener that blocks dangerous calls of any tool. It registers no tool itself | [permission-gate.ts](../../../packages/coding-agent/examples/extensions/permission-gate.ts) |
| [subagent.py](subagent.py) | A tool whose `execute()` runs a second agent with its own context | [subagent/](../../../packages/coding-agent/examples/extensions/subagent/) |

Do them in either order. Both follow the comments in the file.

## Permission gate

Step 6 has two halves: the arguments are validated, then extensions see the call. A listener added with `pi.on("tool_call", handler)` gets every call before the tool runs. If the handler returns a reason, the call is blocked. The tool never runs, and the model gets the reason as an error result:

```text
model: bash {"command": "rm -rf node_modules"}
gate:  "Dangerous command blocked: rm -rf"
model: sees the error, asks you or tries another way
```

The tool itself is unchanged. That is the point: one extension can put a rule on tools that other extensions registered.

## Subagent

Everything the agent reads stays in its messages and is sent with every later request. Say you ask "what does each file in this project do?":

- **Without a subagent:** the parent reads 10 files. Their full text stays in its context for the rest of the conversation.
- **With a subagent:** a second `AgentSession` with an empty conversation reads the 10 files in its own context and answers in one paragraph. The parent's context grows by that paragraph only.

The subagent does not see the conversation, so the task it gets must be complete. A tool reaches the running session through `ctx.session`, which gives it the model, the runtime and the other tools.

Pi has no built-in subagent either. Its example starts a separate `pi --mode json -p --no-session` process per task and reads its event stream. That gives it parallel tasks, streamed progress and roles defined in Markdown files. This version keeps the idea and runs the second agent in the same process.

## Try them

```bash
python -m pi2 -e exercises/01-read/starter.py -e exercises/05-extensions/subagent.py
```

Ask: "Use a subagent to find out what each file in this directory does." Compare the footer's context percentage with and without the subagent.

```bash
python -m pi2 -e exercises/01-read/starter.py -e exercises/04-bash/starter.py \
  -e exercises/05-extensions/permission_gate.py
```

Ask: "Delete the node_modules folder with rm -rf." The gate blocks the call, and the red tool box shows its reason.

Both need working tools from the earlier exercises. The subagent has only the tools you load, and the gate guards only the tools you load.

## More ideas

Pi's [examples/extensions/](../../../packages/coding-agent/examples/extensions/) has about 70 more. These map well onto pi2: `protected-paths.ts`, `dirty-repo-guard.ts` and `confirm-destructive.ts` (more gates), `todo.ts` (a tool with state), and `handoff.ts` (passing work to a fresh session).
