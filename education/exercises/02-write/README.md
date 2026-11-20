# 02: Write

## Learning objectives

- Know what the schema already guarantees and what `execute` must still check.
- Validate input at the tool boundary: here, where a file may be written.
- Report a side effect clearly, since the model does not see it otherwise.

## Concept

Pi validates the model's arguments against `parameters` before `execute` runs. A missing `content` or a number instead of a string never reaches your code. What the schema cannot express is policy: "only inside the working directory" is a rule about the value, not its type. That check belongs in `execute`, and its error message is an instruction to the model.

## Execution flow

1. The model calls `write({ "path": "notes/todo.md", "content": "..." })`.
2. Pi validates the arguments; invalid ones become an error result without calling `execute`.
3. `execute` resolves the path, checks it stays inside `ctx.cwd`, creates `notes/`, writes the file.
4. The confirmation goes back to the model, which can now `read` the file or move on.

## Source code walkthrough

| File | What to look at |
|---|---|
| `packages/agent/src/agent-loop.ts` | Argument validation before execution |
| `packages/coding-agent/src/core/tools/file-mutation-queue.ts` | Why concurrent writes to one file need a queue |
| `packages/coding-agent/src/core/tools/renderers/write.ts` | How the TUI previews `content` while the call streams |

## Hands-on exercise

Implement `execute()` in `write.ts` (EXERCISE 1 to 4). Load it together with your read tool:

```bash
"$REPO/pi-test.sh" -e "$REPO/education/exercises/01-read/read.ts" -e "$REPO/education/exercises/02-write/write.ts"
```

Ask: "Create notes/todo.md with three workshop goals, then read it back." Then: "Write a file to /tmp/outside.txt."

## Expected result

- `notes/todo.md` exists with the content, and the TUI shows a syntax-highlighted preview of the write.
- The write outside the working directory fails with your error message, and the agent explains it was refused.

## Further exploration

- The original tool: `git show cead615b4:packages/coding-agent/src/core/tools/write.ts`.
- CHALLENGE in `write.ts`: `withFileMutationQueue`.
