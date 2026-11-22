# Exercise 04: search

## Goal
- Build `grep` to search file contents with a regular expression.
- Ask the agent to find Python files, search for `TODO`, and filter the search to `*.py`.

`find_files` searches filenames. `grep` searches text inside files.

## Requirements
- Required: `pattern`.
- Optional: `path` (directory, default `.`) and `include` (filename glob, default `*`).
- Resolve `path` from `ctx.cwd` and require a directory.
- Return `relative/path:line:text` for each match.
- Skip `.git` and files that are not UTF-8.
- Return `(no matches)` when empty and stop after 200 matches.

## Output

One line per match, with paths relative to the search root:

```text
src/app.py:2:# TODO: fix
```

Return `(no matches)` when nothing matches. Stop after 200 matches and add
`[stopped after 200 matches]` as the last line.

## Errors

Raise `ValueError` for an empty pattern, an invalid regular expression, a
missing path, or a path that is not a directory.

## Hints
- Use `re.compile`, `root.rglob("*")`, and `fnmatch`.
- Number lines from 1.
- Catch regex, file, and decoding errors as appropriate.

## Run
```bash
python3 -m pi2 --cwd playground/04-search \
  -e tools/04-grep.py -e tools/find.py
```

## Check
```bash
python3 exercises/check.py 04
```
