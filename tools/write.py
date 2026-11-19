# The write tool: create or overwrite a file inside the working directory.
#
# Load all tools:  python3 -m pi2 -e tools
# Load only this:   python3 -m pi2 -e tools/write.py

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def resolve_inside_cwd(ctx, path, action):
    cwd = Path(ctx.cwd).resolve()
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = cwd / target
    target = target.resolve()
    try:
        target.relative_to(cwd)
    except ValueError as error:
        raise ValueError(
            f"Refusing to {action} {path}: only files inside the working directory may be changed."
        ) from error
    return target


def execute_write(params, ctx):
    target = resolve_inside_cwd(ctx, params["path"], "write")
    if target.exists() and target.is_dir():
        raise ValueError(f"Not a file: {params['path']}")

    content = params["content"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content.encode('utf-8'))} bytes to {params['path']}"


write_tool = define_tool(
    name="write",
    label="write",
    description=(
        "Write content to a file. Creates the file if it does not exist, overwrites it if it does, "
        "and creates parent directories."
    ),
    prompt_snippet="Create or overwrite files",
    prompt_guidelines=["Use write only for new files or complete rewrites."],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file, relative to the working directory or absolute"},
            "content": {"type": "string", "description": "Content to write to the file"},
        },
        "required": ["path", "content"],
    },
    execute=execute_write,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(write_tool)
