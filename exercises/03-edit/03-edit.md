# Exercise 03: edit

The agent can change part of a file without rewriting all of it.

## Goal

Build `edit`, a tool that replaces one exact piece of text in a file, and refuses when the text is
missing or appears more than once.

## What you learn

- Why the model names text instead of line numbers.
- Why an edit must match exactly once: zero means the file is stale, two means the edit is ambiguous.
- Why a failed edit must leave the file unchanged.

## The contract

| Argument | Type | Meaning |
|---|---|---|
| `path` | string, required | File to edit, relative to the working directory or absolute |
| `oldText` | string, required | Exact text to replace; must occur exactly once |
| `newText` | string, required | Replacement text; may be empty to delete |

Return a short confirmation such as `Edited math.py`.

Rules:

- The path must stay inside `ctx.cwd`.
- A missing file is an error.
- An empty `oldText` is an error.
- `oldText` occurring zero times is an error.
- `oldText` occurring more than once is an error.
- A failed edit must not change the file.
- Write the result as UTF-8.

## Setup

Load your `read` tool as well, so you can inspect the file before editing:

```bash
python3 -m pi2 --cwd playground/03-edit \
  -e tools/read.py \
  -e tools/edit.py
```

## Steps

Create your own extension file and implement the contract below.

### 1. Resolve the path and guard the working directory

Reuse the pattern from `write`: resolve `ctx.cwd`, join `params["path"]`, resolve the result, and
refuse a target that is not strictly inside `ctx.cwd`. Raise with the path the model sent, not the
resolved one.

### 2. Read the file

Read it as UTF-8 text. Raise if `params["oldText"]` is empty: an empty search string is not a useful
edit and `str.count("")` would be misleading.

### 3. Require exactly one match

Use `text.count(oldText)`. If the count is not 1, raise a `ValueError` that says what happened:

- `0` — the text is not in the file; the model's view may be stale.
- `2` or more — the edit is ambiguous; the model needs more surrounding text.

Do not guess which occurrence to replace.

### 4. Replace, write, and confirm

Use `text.replace(oldText, newText, 1)`, write the result back as UTF-8, and return a confirmation.
Because the count check runs first, a failed edit never reaches the write.

## Check your tool

```bash
python3 exercises/check.py 03
```

The checks cover a successful edit, a missing file, a path outside the working directory, an empty
`oldText`, zero matches, two matches, deletion with an empty `newText`, UTF-8, and the confirmation.
They also verify that a failed edit leaves the file unchanged.

## Try it

Ask:

1. **"Read `math.py`, then fix the bug."**
   The bug is `return a - b`; it should become `return a + b`. Run the file to confirm:
   `python3 math.py` prints `ok`.

2. **"Change the server timeout in `config.ini` to 60."**
   `config.ini` contains `timeout = 30` twice, once under `[server]` and once under `[worker]`. The
   first attempt should fail because the text is ambiguous. That is the lesson, not a bug.

3. **"Change only the `[server]` timeout to 60. Use enough context to make the old text unique."**
   The model should include the section or the nearby `port` line, for example:

   ```ini
   port = 8080
   timeout = 30
   ```

   After the edit, `[server]` has `timeout = 60` and `[worker]` still has `timeout = 30`.

4. **"Change `timeout = 30` to `timeout = 60`."** without more context. The tool must refuse and
   leave the file unchanged.

## Expected result

- `math.py` returns `a + b` and `python3 math.py` prints `ok`.
- The first `config.ini` edit fails with an ambiguity error.
- The second edit changes only the `[server]` timeout.
- `python3 exercises/check.py 03` ends with `10 of 10 checks pass.`

## Challenge

Support several edits in one call: change the schema to `edits`, an array of `{oldText, newText}`.
Match every `oldText` against the **original** text, reject overlapping matches, then apply the
replacements from the end of the file to the start so earlier positions stay valid. Update the tests
if you do.

## Where to look

| File | What to look at |
|---|---|
| [`tools/edit.py`](../../tools/edit.py) | The reference implementation |
| [`tools/write.py`](../../tools/write.py) | The same working-directory guard |
| [`pi2/schema.py`](../pi2/schema.py) | How the arguments are validated |
