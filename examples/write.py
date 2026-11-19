# A solution to exercise 02: the write tool, limited to the working directory.
#
# Load it with the read tool:  ./pi2.sh -e examples/read.py -e examples/write.py
# Then ask: "Create notes/todo.md with three items."

from pathlib import Path

from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    cwd = Path(ctx.cwd).resolve()
    path = (cwd / params["path"]).resolve()
    if not path.is_relative_to(cwd):
        raise PermissionError(f"Refusing to write outside the working directory: {params['path']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = params["content"].encode("utf-8")
    path.write_bytes(data)
    # The model does not see the file unless it reads it, so say what happened.
    return f"Wrote {len(data)} bytes to {params['path']}"


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
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(write_tool)
