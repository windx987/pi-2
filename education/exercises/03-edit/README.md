# 03: Edit

## Learning objectives

- Design a tool the model can use reliably: exact text instead of line numbers.
- Refuse ambiguous or stale requests instead of guessing.
- Return structured `details` that the UI renders, separate from the text the model reads.

## Concept

Line numbers go stale: after one edit, every line below it moves. So the model names the text to replace (`oldText`) and its replacement (`newText`). This is safe only if `oldText` occurs exactly once in the file. Zero matches mean the model's copy of the file is out of date; two matches mean the edit is ambiguous. Both are errors that tell the model to read the file again or include more context.

Several edits in one call are matched against the original file, not one after another, so the model can describe all changes from one read.

## Execution flow

1. While the model streams `edit({ "path": "math.js", "edits": [...] })`, Pi's edit renderer previews the diff from the arguments.
2. `execute` reads the file, finds each `oldText` once, rejects overlaps, applies the replacements, writes the file.
3. It returns text for the model and `details: { diff, patch, firstChangedLine }` for the renderer.
4. The TUI shows the final diff in the edit frame (`renderShell: "self"`).

## Source code walkthrough

| File | What to look at |
|---|---|
| `packages/coding-agent/src/core/tools/renderers/edit.ts` | The preview and result rendering your `details` feed |
| `packages/coding-agent/src/core/tools/edit-diff.ts` | Pi's matching, including fuzzy matching and line endings |
| `packages/coding-agent/src/core/tools/edit.ts` | The argument and `details` types the renderer expects |

## Hands-on exercise

Implement `execute()` in `starter.ts` (EXERCISE 1 to 4). Load it with your read and write tools and ask:

- "Rename add to sum in math.js and update its callers."
- "In math.js, replace `return a + b;` with `return a - b;`" after you copied that line twice into the file: the edit must fail as ambiguous.

## Expected result

- The edit is shown as a boxed diff: removed lines in red, added lines in green, with line numbers.
- An `oldText` that does not occur, or occurs twice, gives an error naming the edit; the agent reads the file and retries with a unique match.
- The file on disk has exactly the requested changes.

## Further exploration

- The original tool: `git show cead615b4:packages/coding-agent/src/core/tools/edit.ts`, and its tests: `git show cead615b4:packages/coding-agent/test/tools.test.ts` (section "edit tool").
- CHALLENGE in `starter.ts`: CRLF files.
