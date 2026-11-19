# The read tool: read a UTF-8 text file, with offset and limit.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/read.py

from pathlib import Path

from pi2 import ExtensionAPI, define_tool

MAX_READ_LINES = 2000
INF = float("inf")
NEG_INF = float("-inf")


def is_finite(value):
    """True for a real number, false for NaN and infinities."""
    return value == value and value not in (INF, NEG_INF)


def resolve_read_path(ctx, path):
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = Path(ctx.cwd) / target
    return target.resolve()


def positive_int(value, name, default):
    if value is None:
        return default
    if isinstance(value, float) and not is_finite(value):
        raise ValueError(f"{name} must be a whole number.")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise ValueError(f"{name} must be a whole number.")
    number = int(value)
    if number < 1:
        raise ValueError(f"{name} must be 1 or greater.")
    return number


def execute_read(params, ctx):
    target = resolve_read_path(ctx, params["path"])
    offset = positive_int(params.get("offset"), "offset", 1)
    limit = min(positive_int(params.get("limit"), "limit", MAX_READ_LINES), MAX_READ_LINES)

    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ValueError(f"File not found: {params['path']}") from error
    except IsADirectoryError as error:
        raise ValueError(f"Not a file: {params['path']}") from error
    except UnicodeDecodeError as error:
        raise ValueError(f"File is not UTF-8 text: {params['path']}") from error

    if text == "":
        return ""

    lines = text.splitlines()
    start = offset - 1
    if start >= len(lines):
        raise ValueError(f"Offset {offset} is beyond the end of {params['path']} ({len(lines)} lines).")

    end = min(len(lines), start + limit)
    output = "\n".join(lines[start:end])
    if end < len(lines):
        output += f"\n\n[{len(lines) - end} more lines. Use offset={end + 1} to continue.]"
    return output


read_tool = define_tool(
    # The name is part of the contract: models are trained on tools called "read".
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
    execute=execute_read,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(read_tool)
