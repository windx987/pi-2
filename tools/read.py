# The read tool: read a text file, with offset and limit.

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def resolve(ctx, path):
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (Path(ctx.cwd) / path).resolve()


def execute(params, ctx):
    target = resolve(ctx, params["path"])
    offset = max(1, int(params.get("offset", 1)))
    limit = max(1, int(params.get("limit", 2000)))

    lines = target.read_text(encoding="utf-8").splitlines()
    if lines and offset > len(lines):
        raise ValueError(f"offset {offset} is past the end of the file")

    start = offset - 1
    end = start + limit
    output = "\n".join(lines[start:end])
    if end < len(lines):
        output += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1}.]"
    return output


read_tool = define_tool(
    name="read",
    label="read",
    description="Read a text file. offset is the first line to read (starting at 1); limit is the maximum number of lines.",
    prompt_snippet="Read file contents",
    prompt_guidelines=["Use read to examine files instead of cat or sed."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "offset": {"type": "number", "description": "Line number to start reading from (1-indexed)"},
            "limit": {"type": "number", "description": "Maximum number of lines to read"},
        },
        "required": ["path"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(read_tool)
