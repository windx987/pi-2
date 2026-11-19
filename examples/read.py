# A solution to exercise 01: the read tool, with offset and limit.
#
# Load it:  ./pi2.sh -e examples/read.py
# Then ask: "What is in package.json?"

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    path = Path(ctx.cwd) / params["path"]
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {params['path']}")
    lines = path.read_text(encoding="utf-8").split("\n")

    offset = int(params.get("offset") or 1)
    if offset > len(lines):
        raise ValueError(f"Offset {offset} is beyond the end of the file ({len(lines)} lines).")
    end = len(lines) if params.get("limit") is None else min(len(lines), offset - 1 + int(params["limit"]))
    text = "\n".join(lines[offset - 1:end])
    if end < len(lines):
        # Tell the model how to read on; it cannot see what was left out.
        text += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1} to continue.]"
    return text


read_tool = define_tool(
    name="read",
    label="read",
    description=(
        "Read the contents of a text file. Use offset and limit to read part of a large file; "
        "offset is the first line to read, starting at 1."
    ),
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
