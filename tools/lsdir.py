# The lsdir tool: list the immediate contents of a directory.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def resolve(ctx, path):
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()


def execute(params, ctx):
    requested = params.get("path") or "."
    target = resolve(ctx, requested)
    if not target.exists():
        raise ValueError(f"Path not found: {requested}")
    if not target.is_dir():
        raise ValueError(f"Not a directory: {requested}")

    entries = [child.name + ("/" if child.is_dir() else "") for child in target.iterdir()]
    if not entries:
        return "(empty directory)"
    return "\n".join(sorted(entries, key=str.casefold))


lsdir_tool = define_tool(
    name="lsdir",
    label="lsdir",
    description="List the immediate contents of a directory. Directories end with a slash.",
    prompt_snippet="List directory contents",
    prompt_guidelines=["Use lsdir to inspect a directory before reading its files."],
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path, relative to the working directory or absolute; defaults to the working directory",
            },
        },
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(lsdir_tool)
