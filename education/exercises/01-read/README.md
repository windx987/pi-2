# 01: Read

## Learning objectives

- Define a tool: name, description, JSON Schema of its arguments.
- Register it with `pi.registerTool` and see Pi declare it to the model.
- Turn a request into a result, and a failure into an error result the model can act on.

## Concept

The model cannot touch your machine. It can only answer with text or with a tool call: a tool name and JSON arguments. Pi runs the tool and sends the result back as the next message. A tool is therefore a contract: the description and schema tell the model what it may ask for, and the result tells it what happened.

## Execution flow

1. Pi starts, loads `read.ts` with `-e`, and calls its default export with the extension API.
2. `pi.registerTool(readTool)` adds `read` to the session's tool registry. It is active, so the next request to the model lists it with its schema.
3. The model answers with `read({ "path": "package.json" })`.
4. Pi validates the arguments against `parameters`, then calls `execute(toolCallId, params, signal, onUpdate, ctx)`.
5. What `execute` returns, or the message of what it throws, becomes the tool result. Pi sends it to the model, which answers or calls another tool.

## Source code walkthrough

| File | What to look at |
|---|---|
| `packages/coding-agent/src/core/extensions/types.ts` | `ToolDefinition`, `defineTool` |
| `packages/coding-agent/src/core/agent-session.ts` | `_refreshToolRegistry()`: built-in and extension tools become one registry |
| `packages/agent/src/agent-loop.ts` | Tool calls from the model, execution, results back into the transcript |

## Hands-on exercise

Open `read.ts` and implement `execute()`, following EXERCISE 1 to 4 in its comments. Run it:

```bash
cd ~/pi-workshop
"$REPO/pi-test.sh" -e "$REPO/education/exercises/01-read/read.ts"
```

Ask: "What does math.js export?" and "Show me lines 5 to 7 of math.js."

## Expected result

- The agent calls `read`; the TUI shows the call as `read math.js` and the file contents under it.
- Asking for a missing file gives an error result, and the agent says the file does not exist instead of inventing contents.
- Asking for part of a file uses `offset` and `limit`.

## Further exploration

- The original tool: `git show cead615b4:packages/coding-agent/src/core/tools/read.ts`. It also reads images, streams large files and truncates output.
- Why the name matters: `packages/coding-agent/src/core/compaction/utils.ts` (`addFileOp`) and `src/core/system-prompt.ts` (skills need `read`).
