# The lsdir tool: list the immediate contents of a directory.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/lsdir.py

from pathlib import Path

from pi2 import ExtensionAPI, define_tool

MAX_ENTRIES = 1000


def resolve_path(ctx, path):
    target = Path(path or ".").expanduser()
    if not target.is_absolute():
        target = Path(ctx.cwd) / target
    return target.resolve()


def execute_lsdir(params, ctx):
    requested = params.get("path") or "."
    target = resolve_path(ctx, requested)

    if not target.exists():
        raise ValueError(f"Path not found: {requested}")
    if not target.is_dir():
        raise ValueError(f"Not a directory: {requested}")

    include_hidden = params.get("include_hidden", False)
    try:
        children = list(target.iterdir())
    except OSError as error:
        raise ValueError(f"Cannot list {requested}: {error.strerror or error}") from error

    entries = []
    for child in children:
        if not include_hidden and child.name.startswith("."):
            continue
        entries.append(child.name + ("/" if child.is_dir() else ""))

    if not entries:
        return "(empty directory)" if not children else "(no visible entries)"

    entries.sort(key=str.casefold)
    if len(entries) > MAX_ENTRIES:
        remaining = len(entries) - MAX_ENTRIES
        entries = entries[:MAX_ENTRIES]
        entries.append(f"[{remaining} more entries not shown.]")
    return "\n".join(entries)


lsdir_tool = define_tool(
    name="lsdir",
    label="lsdir",
    description=(
        "List the immediate contents of a directory. Defaults to the working directory. "
        "Directories have a trailing slash."
    ),
    prompt_snippet="List directory contents",
    prompt_guidelines=["Use lsdir to inspect a directory before reading its files."],
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Directory path, relative to the working directory or absolute; "
                    "defaults to the working directory"
                ),
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include entries whose names start with a dot (default false)",
            },
        },
    },
    execute=execute_lsdir,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(lsdir_tool)
