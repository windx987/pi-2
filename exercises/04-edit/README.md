# Exercise 04: edit

The agent can change part of a file without rewriting all of it.

## What you learn

- Designing a tool the model can use reliably: exact text instead of line numbers.
- Refusing ambiguous or stale requests instead of guessing.
- Returning a result that shows the model what changed.

## How it works

Line numbers go stale: after one edit, every line below it moves. So the model names the text to replace (`oldText`) and its replacement (`newText`). This is safe only if `oldText` occurs exactly once in the file. Zero matches mean the model's copy of the file is out of date; two matches mean the edit is ambiguous. Both are errors that tell the model to read the file again or include more context.

Several edits in one call are all matched against the original file, not one after another, so the model can describe every change from one read.

1. The model calls `edit({"path": "math.js", "edits": [{"oldText": "...", "newText": "..."}]})`.
2. `execute` reads the file and finds each `oldText` exactly once.
3. It rejects overlapping edits, applies the replacements from the end of the file to the start, and writes the file.
4. It returns a confirmation, best with a diff, so the model sees the result without reading the file again.

## Steps

Follow EXERCISE 1 to 4 in [starter.py](starter.py):

1. Resolve the path and read the file.
2. Find each `oldText` once in the original content (`str.count`); name the failing edit (`edits[0]`, `edits[1]`, ...) in the error.
3. Reject overlaps, then apply the replacements from the end of the file to the start.
4. Write the file and return a confirmation; `difflib.unified_diff` gives the diff.

## Check your tool

Before you try it with the model, check it without one:

```bash
python3 "$REPO/exercises/check.py" 04
```

Each step of the list above has checks that call your `execute()` directly. A check shows PASS, FAIL with what went wrong, or TODO while `execute()` still raises `NotImplementedError`. When all checks pass, the tool does what the steps ask. Whether the model uses the tool well is what the next section shows.

## Try it

Start Docker as in exercise 03, and load it with your read, write and bash tools, from your playground copy:

```bash
cd ~/pi-workshop
"$REPO/pi2.sh" -e "$REPO/exercises/01-read/starter.py" -e "$REPO/exercises/02-write/starter.py" \
  -e "$REPO/exercises/03-bash/starter.py" -e "$REPO/exercises/04-edit/starter.py"
```

Ask: "Fix the failing test." The agent reads `math.js`, edits it, and runs the tests again: all four tools in one task. Then ask: "Rename add to sum in math.js and update its callers." Then copy the line `return a + b;` once more into `math.js` yourself and ask: "In math.js, replace `return a + b;` with `return a - b;`."

## Expected result

- `npm test` fails, then a green `edit math.js` box, then `npm test` passes.
- A green `edit math.js` box with your confirmation and the start of the diff. `grep -n sum math.js` shows the renamed function and its caller.
- The ambiguous edit turns red with your message naming the edit. The agent reads the file and retries with more context, or asks you which one you mean.
- The file on disk has exactly the requested changes.

## Where to look

| File | What to look at |
|---|---|
| [pi2/tui.py](../../pi2/tui.py) | `tool_title` and `on_event`: how the tool box shows the call and the first lines of the result |
| [pi2/agent_loop.py](../../pi2/agent_loop.py) | `execute_tool_call`: an exception becomes an error result |

## In Pi

Pi's original tool is [tools/edit.ts](https://github.com/windx987/pi-2/blob/cead615b4/packages/coding-agent/src/core/tools/edit.ts). Its matching ([edit-diff.ts](https://github.com/windx987/pi-2/blob/main/packages/coding-agent/src/core/tools/edit-diff.ts)) also handles line endings and near matches, and its renderer shows the diff in a box while the call streams.
