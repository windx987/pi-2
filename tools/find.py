# The find tool: find files recursively by glob pattern.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def resolve(ctx, path):
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()


def execute(params, ctx):
    requested = params.get("path") or "."
    pattern = params["pattern"]
    if not pattern:
        raise ValueError("pattern is empty.")

    root = resolve(ctx, requested)
    if not root.exists():
        raise ValueError(f"Path not found: {requested}")
    if not root.is_dir():
        raise ValueError(f"Not a directory: {requested}")

    files = [path for path in root.rglob(pattern) if path.is_file()]
    if not files:
        return "(no matching files)"
    return "\n".join(sorted(str(path.relative_to(root)) for path in files))


find_files_tool = define_tool(
    name="find_files",
    label="find_files",
    description="Find files recursively by glob pattern such as '*.py'. Paths are relative to the search directory.",
    prompt_snippet="Find files by glob pattern",
    prompt_guidelines=["Use find_files to locate files instead of shell find."],
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory to search, relative to the working directory or absolute; defaults to the working directory",
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern such as '*.py' or 'test_*.py'",
            },
        },
        "required": ["pattern"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(find_files_tool)
