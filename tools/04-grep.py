# The grep tool: search file contents recursively with a regular expression.

import fnmatch
import re
from pathlib import Path

from pi2 import ExtensionAPI, define_tool

MAX_MATCHES = 200


def resolve(ctx, path):
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()


def execute(params, ctx):
    pattern = params["pattern"]
    if not pattern:
        raise ValueError("pattern is empty.")

    requested = params.get("path") or "."
    root = resolve(ctx, requested)
    if not root.exists():
        raise ValueError(f"Path not found: {requested}")
    if not root.is_dir():
        raise ValueError(f"Not a directory: {requested}")

    try:
        regex = re.compile(pattern)
    except re.error as error:
        raise ValueError(f"Invalid regular expression: {error}") from error

    include = params.get("include") or "*"
    matches = []
    for file in sorted(root.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(root)
        if ".git" in relative.parts:
            continue
        if not fnmatch.fnmatch(file.name, include):
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                matches.append(f"{relative}:{number}:{line}")
                if len(matches) >= MAX_MATCHES:
                    matches.append(f"[stopped after {MAX_MATCHES} matches]")
                    return "\n".join(matches)

    if not matches:
        return "(no matches)"
    return "\n".join(matches)


grep_tool = define_tool(
    name="grep",
    label="grep",
    description=(
        "Search file contents recursively with a regular expression. Returns path:line:text for each "
        "matching line. Skips binary files and .git."
    ),
    prompt_snippet="Search file contents with a regular expression",
    prompt_guidelines=["Use grep to find where text or symbols appear; use find_files to locate files by name."],
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regular expression to search for"},
            "path": {
                "type": "string",
                "description": "Directory to search, relative to the working directory or absolute; defaults to the working directory",
            },
            "include": {
                "type": "string",
                "description": "Only search files whose name matches this glob, such as '*.py'; defaults to all files",
            },
        },
        "required": ["pattern"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(grep_tool)
