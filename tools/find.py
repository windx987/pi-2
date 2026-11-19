# The find tool: find files recursively by glob pattern.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/find.py

import os
from pathlib import Path

from pi2 import ExtensionAPI, define_tool

MAX_RESULTS = 1000


def resolve_path(ctx, path):
    target = Path(path or ".").expanduser()
    if not target.is_absolute():
        target = Path(ctx.cwd) / target
    return target.resolve()


def display_path(ctx, path):
    try:
        return str(path.relative_to(Path(ctx.cwd).resolve()))
    except ValueError:
        return str(path)


def matches_pattern(relative, pattern):
    """Match a relative path; let **/ also match zero directories."""
    if relative.match(pattern):
        return True
    relaxed = pattern.replace("**/", "")
    return relaxed != pattern and relative.match(relaxed)


def execute_find_files(params, ctx):
    requested = params.get("path") or "."
    pattern = params["pattern"]
    if not pattern:
        raise ValueError("pattern is empty.")

    target = resolve_path(ctx, requested)
    if not target.exists():
        raise ValueError(f"Path not found: {requested}")
    if not target.is_dir():
        raise ValueError(f"Not a directory: {requested}")

    include_hidden = params.get("include_hidden", False)
    results = []
    truncated = False

    def on_error(error):
        raise ValueError(f"Cannot search {requested}: {error.strerror or error}") from error

    for current, dirs, files in os.walk(target, topdown=True, followlinks=False, onerror=on_error):
        if not include_hidden:
            dirs[:] = [name for name in dirs if not name.startswith(".")]

        current_path = Path(current)
        for name in files:
            if not include_hidden and name.startswith("."):
                continue
            candidate = current_path / name
            if not matches_pattern(candidate.relative_to(target), pattern):
                continue
            results.append(candidate)
            if len(results) > MAX_RESULTS:
                truncated = True
                break
        if truncated:
            break

    if not results:
        return "(no matching files)"
    if truncated:
        results = results[:MAX_RESULTS]

    results.sort(key=lambda path: display_path(ctx, path).casefold())
    lines = [display_path(ctx, path) for path in results]
    if truncated:
        lines.append(f"[Results truncated to {MAX_RESULTS}. Use a narrower path or pattern.]")
    return "\n".join(lines)


find_files_tool = define_tool(
    name="find_files",
    label="find_files",
    description=(
        "Find files recursively by glob pattern under a directory. Defaults to the working directory. "
        "Returns relative paths, or absolute paths for results outside the working directory."
    ),
    prompt_snippet="Find files by glob pattern",
    prompt_guidelines=["Use find_files to locate files instead of shell find or recursive ls."],
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Directory to search, relative to the working directory or absolute; "
                    "defaults to the working directory"
                ),
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern such as '*.py' or 'test_*.py'",
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Search hidden files and directories (default false)",
            },
        },
        "required": ["pattern"],
    },
    execute=execute_find_files,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(find_files_tool)
