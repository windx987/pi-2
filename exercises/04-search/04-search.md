# Exercise 04: search

Build `grep`, a tool that searches file contents with a regular expression. Compare it with the
existing `find_files` tool, which searches file names.

## Task

From the repository root:

```bash
python3 -m pi2 --cwd playground/04-search \
  -e tools/grep.py -e tools/find.py
```

Ask the agent to find Python files by name, search the project for `TODO`, and repeat with
`include: "*.py"`. The playground contains `app.py`, `helpers.py`, `test_app.py`, `guide.md`, and
`users.json`.

## Contract

Arguments are `pattern` (required regex), `path` (optional directory, default `.`), and `include`
(optional filename glob, default `*`). Return `path:line:text` for each matching line, relative to
the search root. Reject an empty pattern, invalid regexes, missing paths, and file roots. Skip `.git`
and files that are not UTF-8. Return `(no matches)` when there are none. Stop after 200 matches and
append `[stopped after 200 matches]`.

## Hints

Resolve the root against `ctx.cwd`; compile with `re.compile`; walk with `root.rglob("*")`; keep
files, skip `.git`, apply `fnmatch` to `file.name`, read UTF-8, and search each line.

## Check

```bash
python3 exercises/check.py 04
```

The reference implementation is [`tools/grep.py`](../../tools/grep.py). `find_files` is in
[`tools/find.py`](../../tools/find.py).
